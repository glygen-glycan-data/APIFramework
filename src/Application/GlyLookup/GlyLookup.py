
import os
import sys
import time
import re
from collections import defaultdict
import multiprocessing
from APIFramework import APIFramework, APIFrameworkWithFrontEnd, queue

import pygly.alignment
from pygly.GlycanResource.GlyTouCan import GlyTouCanNoCache, GlyTouCan
from pygly.GlycanResource.GlyGen import GlyGen
from pygly.GlycanFormatter import WURCS20Format, GlycoCTFormat

def round2str(n):
    return str(round(n, 2))


class GlyLookup(APIFrameworkWithFrontEnd):

    def form_task(self, p):
        res = {}

        p["seq"] = p["seq"].strip()
        task_str = p["seq"].encode("utf-8")
        list_id = self.str2hash(task_str)

        res["id"] = list_id
        res["seq"] = p["seq"]

        return res


    def worker(self, pid, task_queue, result_queue, suicide_queue_pair, params):

        self.output(2, "Worker-%s is starting up" % (pid))

        glycan_file_path = self.autopath(params["glycan_file_path"])

        gp = GlycoCTFormat()
        wp = WURCS20Format()

        gie = pygly.alignment.GlycanEqual()

        wurcss = {}
        otherseq = defaultdict(list)
        member = defaultdict(list)
        glycan_by_mass = defaultdict(list)

        hash2acc = defaultdict(set)

        for line in open(glycan_file_path):

            try:
                acc, mass, wseq, gseq, glygen, xxx = line.strip().split("\t")
            except ValueError:
                acc, mass, wseq, gseq, xxx = line.strip().split("\t")
                glygen = ""

            gseq = gseq.replace("\\n", "\n")

            for s in [wseq, gseq]:
                if s != "":
                    h = self.str2hash(s)
                    if acc not in hash2acc[h]:
                        hash2acc[h].add(acc)

            wurcss[acc] = wseq
            for s in [gseq,]:
                if s != "":
                    otherseq[acc].append(dict(seq=s,hash=self.str2hash(s),format='GlycoCT',source='GlyTouCan:'+acc))

            if glygen == "true":
                member[acc].append("GlyGen:"+acc)

            if mass == "":
                continue

            glycan_by_mass[mass].append(acc)

        self.output(2, "Worker-%s is ready to take job" % (pid))

        while True:
            task_detail = self.task_queue_get(task_queue, pid, suicide_queue_pair)

            self.output(2, "Worker-%s is computing task: %s" % (pid, task_detail))

            error = []
            calculation_start_time = time.time()


            list_id = task_detail["id"]
            seq = str(task_detail["seq"])
            wurcsfromgtcacc = False
            if re.search(r'^G[0-9]{5}[A-Z]{2}$',seq):
                if seq in wurcss:
                    seq = wurcss[seq]
                    wurcsfromgtcacc = True
                else:
                    seq = None
                    error.append("Unexpected GlyTouCan accession")
                
            result = []

            if seq != None:
                seqh = self.str2hash(seq)
                for acc in sorted(hash2acc[seqh]):
                    result.append(acc)

            if len(result) == 0 and seq != None:
                query_glycan = None
                try:
                    if seq.startswith("RES"):
                        query_glycan = gp.toGlycan(seq)
                    elif seq.startswith("WURCS"):
                        query_glycan = wp.toGlycan(seq)
                    else:
                        error.append("Unable to parse")
                except:
                    error.append("Unable to parse")

                if len(error) != 0:
                    for e in error:
                        pass

                if len(error) == 0:
                    try:
                        query_glycan_mass = round2str(query_glycan.underivitized_molecular_weight())
                    except:
                        error.append("Error in calculating mass")

                if len(error) == 0:
                    potential_accs = glycan_by_mass.get(query_glycan_mass,[])

                    for acc in sorted(potential_accs):
                        glycan = wp.toGlycan(wurcss[acc])
                        if gie.eq(query_glycan, glycan):
                            result.append(acc)
                            hash2acc[seqh].add(acc)

            result1 = []
            for acc in result:
                r = dict(accession=acc,
                         sequences=[dict(seq=wurcss[acc],hash=self.str2hash(wurcss[acc]),format='WURCS',source='GlyTouCan:'+acc)]+otherseq[acc],
                         membership=['GlyTouCan:'+acc]+member[acc])
                if seq.startswith('RES'):
                    r['sequences'].append(dict(seq=seq,hash=seqh,format='GlycoCT',source='UserInput'))
                elif not wurcsfromgtcacc and seq.startswith('WURCS'):
                    r['sequences'].append(dict(seq=seq,hash=seqh,format='WURCS',source='UserInput'))
                result1.append(r)

            calculation_end_time = time.time()
            calculation_time_cost = calculation_end_time - calculation_start_time

            self.output(2, "Worker-%s finished computing job (%s)" % (pid, list_id))

            res = {
                "id": list_id,
                "start time": calculation_start_time,
                "end time": calculation_end_time,
                "runtime": calculation_time_cost,
                "error": error,
                "result": result1
            }

            self.output(2, "Job (%s): %s" % (list_id, res))

            result_queue.put(res)


    def pre_start(self, para):

        ggacc = set(GlyGen().allglycans())
        gtc = GlyTouCanNoCache()
        wp = WURCS20Format()

        file_path = self.autopath(para["glycan_file_path"])

        data = {}
        for acc, f, s in gtc.allseq():

            if f not in ["wurcs", "glycoct"]:
                continue

            s = s.strip()
            if " " in s:
                # Issue with some sequence...
                continue

            s = s.replace("\n", "\\n")
            if "\r" in s:
                # Issue with some sequence...
                # print acc
                continue

            if acc not in data:
                data[acc] = ["", "", "", "" ]

            if acc in ggacc:
                data[acc][3] = 'true'

            if f == "glycoct":
                data[acc][2] = s
            elif f == "wurcs":
                data[acc][1] = s

                try:
                    g = wp.toGlycan(s)
                    mass = round2str(g.underivitized_molecular_weight())
                    data[acc][0] = mass
                except:
                    continue

        f1 = open(self.autopath("tmp.txt", newfile=True), "w")
        for acc, d in data.items():
            line = "\t".join([acc] + d + ["END"])
            f1.write("%s\n" % (line))
        f1.close()

        if os.path.exists(file_path):
            os.remove(file_path)
        os.rename(self.autopath("tmp.txt", newfile=True), file_path)




if __name__ == '__main__':
    multiprocessing.freeze_support()

    glylookup_app = GlyLookup()
    glylookup_app.find_config("GlyLookup.ini")
    glylookup_app.start()

