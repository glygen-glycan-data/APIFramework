
import os
import re
import sys
import time
import json
import copy
import base64
import urllib
import hashlib
import multiprocessing
from APIFramework import APIFramework

import pygly.alignment
import pygly.GNOme
import pygly.GlycanImage
import pygly.GlycanResource.GlyTouCan
from pygly.GlycanFormatter import WURCS20Format, GlycoCTFormat

def round2str(n):
    return str(round(n, 2))


class GNOmeLevelComputing(pygly.GNOme.SubsumptionGraph):

    def __init__(self, resource=None, format=None):
        pass

gnome = GNOmeLevelComputing()

class Subsumption(APIFramework):


    def form_task(self, p):
        res = {}
        p["seqs"] = p["seqs"].strip()
        task_str = json.dumps(p["seqs"], sort_keys=True).encode("utf-8")
        list_id = hashlib.md5(task_str).hexdigest()

        res["id"] = list_id
        res["seqs"] = p["seqs"]

        return res

    @staticmethod
    def worker(pid, task_queue, result_queue, params):
        print(pid, "Start")

        glycan_file_path = params["glycan_file_path"]

        gp = GlycoCTFormat()
        wp = WURCS20Format()

        ge = pygly.GlycanImage.GlycanImage()
        ge.notation("snfg")

        gie = pygly.alignment.GlycanEqual()
        gsc = pygly.alignment.GlycanSubsumption()

        wurcss = {}
        glycan_by_mass = {}
        subsumption_levels = {}

        for line in open(glycan_file_path):
            acc, mass, sl, s = line.strip().split()

            if mass not in glycan_by_mass:
                glycan_by_mass[mass] = []

            subsumption_levels[acc] = sl

            glycan_by_mass[mass].append(acc)
            wurcss[acc] = s

        glycan_by_mass[None] = []


        while True:
            task_detail = task_queue.get(block=True)
            print(task_detail)

            error = []
            calculation_start_time = time.time()


            list_id = task_detail["id"]
            seqs = task_detail["seqs"]
            query_glycans = {}
            masses = set()


            # Parsing sequences
            for name, seq in seqs.items():
                try:
                    if "RES" in seq:
                        query_glycan = gp.toGlycan(seq)
                    elif "WURCS" in seq:
                        query_glycan = wp.toGlycan(seq)
                    else:
                        raise RuntimeError
                    query_glycans[name] = query_glycan
                except:
                    error.append("Unable to parse %s: %s" % (name, seq))

            # Calculating MW
            for name, qg in query_glycans.items():
                try:
                    query_glycan_mass = round2str(qg.underivitized_molecular_weight())
                    masses.add(query_glycan_mass)
                except:
                    error.append("Error in calculating mass for " + name)

            query_glycan_mass = None
            if len(masses) == 1:
                query_glycan_mass = list(masses)[0]
            elif len(masses) > 1:
                error.append("Query glycans are not in the same mass cluster...")

            if len(error) == 0:
                if query_glycan_mass not in glycan_by_mass:
                    error.append("The mass is not supported")


            # Try to find GlyTouCan accession for submitted query sequences
            equivalents = {}
            if len(error) == 0:
                potential_accs = glycan_by_mass[query_glycan_mass]
                glycans = {}
                for acc in potential_accs:
                    glycan = wp.toGlycan(wurcss[acc])
                    glycans[acc] = glycan

                    for name, qg in query_glycans.items():
                        if gie.eq(qg, glycan):
                            equivalents[name] = acc


                for name, qg in query_glycans.items():
                    glycans[name] = qg
                    try:
                        del glycans[equivalents[name]]
                    except:
                        continue


                potential_accs = glycans.keys()
                relationship = {}
                for acc in potential_accs:
                    relationship[acc] = []

                    for acc2 in potential_accs:
                        if acc == acc2:
                            continue

                        if gsc.leq(glycans[acc2], glycans[acc]):
                            relationship[acc].append(acc2)

                # Eliminate short-cuts
                while True:
                    found = False
                    for acc, children in relationship.items():

                        descendants = set()
                        todo = children[:]
                        seen = set()
                        while len(todo) > 0:
                            c = todo.pop()
                            if c not in seen:
                                seen.add(c)
                            else:
                                continue
                            grandchildren = relationship[c]
                            for gc in grandchildren:
                                todo.append(gc)

                                descendants.add(gc)


                        for c in children:

                            for d in descendants:

                                if d in children:
                                    children.remove(d)
                                    found = True
                                    break

                    if not found:
                        break


            # Generating images for glycans not in GlyTouCan
            images = {}
            for name, s in seqs.items():

                if name in equivalents:
                    continue

                try:
                    tmp = hashlib.sha256(s).hexdigest()
                    ge.writeImage(s, tmp)
                    b64image = base64.b64encode(open(tmp, "rb").read())
                    images[name] = b64image

                except:
                    error.append("Could not generate images for " + name)


            # Computing subsumption level
            subsumption_levels_calc = {}
            for name, query_glycan in query_glycans.items():
                subsumption_level_calc = None
                subsumption_level_gnome = None


                if gnome.any_anomer(query_glycan) or gnome.any_parent_pos(query_glycan):
                    subsumption_level_calc = 'saccharide'

                if gnome.any_links(query_glycan) or (gnome.mono_count(query_glycan) == 1 and self.any_ring(query_glycan)):
                    if not subsumption_level_calc:
                        subsumption_level_calc = 'topology'

                #if gnome.any_ring(query_glycan):
                #    error.append("%s has no linkages but does have ring values" % (name) )

                if gnome.any_stem(query_glycan):
                    if not subsumption_level_calc:
                        subsumption_level_calc = 'composition'

                if not subsumption_level_calc:
                    subsumption_level_calc = 'basecomposition'

                if name in equivalents and equivalents[name] in subsumption_levels:
                    subsumption_level_gnome = subsumption_levels[equivalents[name]]

                if subsumption_level_gnome != None and subsumption_level_gnome != subsumption_level_calc:
                    error.append("%s subsumption level calculation is not the same as GNOme" % (name))


                # print name, subsumption_level_calc, subsumption_level_gnome
                subsumption_levels_calc[name] = subsumption_level_calc


            # Computing buttons
            ButtonConfigs = {}
            for name, query_glycan in query_glycans.items():
                ButtonConfigs[name] = query_glycan.iupac_composition(floating_substituents=False,aggregate_basecomposition=True)


            calculation_end_time = time.time()
            calculation_time_cost = calculation_end_time - calculation_start_time

            combined_result = {
                "relationship": relationship,
                "equivalent": equivalents,
                "image": images,
                "subsumption_level": subsumption_levels_calc,
                "buttonconfig": ButtonConfigs
            }
            res = {
                "id": list_id,
                "start time": calculation_start_time,
                "end time": calculation_end_time,
                "runtime": calculation_time_cost,
                "error": error,
                "result": combined_result
            }
            result_queue.put(res)

    def pre_start(self, worker_para):

        data_file_path = self.abspath(worker_para["glycan_file_path"])
        output_file = open(data_file_path, "w")

        gtc_acc_pattern = re.compile(r"^G\d{5}\w{2}$")

        mass_lut = {}
        header = True
        for line in urllib.urlopen(
                "https://raw.githubusercontent.com/glygen-glycan-data/GNOme/master/data/mass_lookup_2decimal"):
            l = line.strip()
            if header:
                header = False
                continue

            mid, mass = l.split()
            mass_lut[mid] = mass

        all_wurcs = {}

        wp = WURCS20Format()
        gtc = pygly.GlycanResource.GlyTouCanNoCache()
        for acc, f, s in gtc.allseq(format="wurcs"):
            try:
                wp.toGlycan(s)
            except:
                continue

            all_wurcs[acc] = s

        lines = []

        gnome = pygly.GNOme.GNOme()
        accs = set()
        for acc in gnome.nodes():
            if acc == "00000001":
                continue

            if gtc_acc_pattern.findall(acc):
                accs.add(acc)
            else:
                assert acc in mass_lut

                for gacc in gnome.descendants(acc):
                    if gacc not in all_wurcs:
                        print gacc, "wurcs issue!"
                        continue

                    lvl = gnome.level(gacc)
                    # print gacc, lvl
                    assert lvl

                    lines.append("%s\t%s\t%s\t%s\n" % (gacc, mass_lut[acc], lvl, all_wurcs[gacc]))

        for l in sorted(lines):
            output_file.write(l)

        print "Preparation finished"


if __name__ == '__main__':
    multiprocessing.freeze_support()

    subsumption_app = Subsumption()
    subsumption_app.find_config("Subsumption.ini")
    subsumption_app.start()










