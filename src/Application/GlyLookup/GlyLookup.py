
import os
import sys
import time
import hashlib
import multiprocessing
from APIFramework import APIFramework

import pygly.alignment
from pygly.GlycanResource.GlyTouCan import GlyTouCanNoCache, GlyTouCan
from pygly.GlycanFormatter import WURCS20Format, GlycoCTFormat

def round2str(n):
    return str(round(n, 2))


class GlyLookup(APIFramework):

    def form_task(self, p):
        res = {}

        p["seq"] = p["seq"].strip()
        task_str = p["seq"].encode("utf-8")
        list_id = hashlib.md5(task_str).hexdigest()

        res["id"] = list_id
        res["seq"] = p["seq"]

        return res

    @staticmethod
    def worker(pid, task_queue, result_queue, params):
        print(pid, "Start")

        glycan_file_path = params["glycan_file_path"]

        gp = GlycoCTFormat()
        wp = WURCS20Format()

        gie = pygly.alignment.GlycanEqual()

        wurcss = {}
        glycan_by_mass = {}

        hash2seq = {}


        for line in open(glycan_file_path):
            acc, s = line.strip().split()
            s = s.replace("\\n", "\n")

            h = hashlib.md5(s).hexdigest()
            hash2seq[h] = (acc, s)

            try:
                g = wp.toGlycan(s)
                mass = round2str(g.underivitized_molecular_weight())
            except:
                continue

            if mass not in glycan_by_mass:
                glycan_by_mass[mass] = []

            glycan_by_mass[mass].append(acc)
            wurcss[acc] = s

        glycan_by_mass[None] = []


        while True:
            task_detail = task_queue.get(block=True)
            print(task_detail)

            error = []
            calculation_start_time = time.time()


            list_id = task_detail["id"]
            seq = str(task_detail["seq"])
            result = []

            h = hashlib.md5(seq).hexdigest()
            if h in hash2seq:
                acc = hash2seq[h][0]
                result.append(acc)

            if len(result) == 0:
                query_glycan = None
                try:
                    if "RES" in seq:
                        query_glycan = gp.toGlycan(seq)
                    elif "WURCS" in seq:
                        query_glycan = wp.toGlycan(seq)
                    else:
                        raise RuntimeError
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
                    if query_glycan_mass not in glycan_by_mass:
                        error.append("The mass is not supported")

                if len(error) == 0:
                    potential_accs = glycan_by_mass[query_glycan_mass]

                    for acc in potential_accs:
                        glycan = wp.toGlycan(wurcss[acc])
                        if gie.eq(query_glycan, glycan):
                            result.append(acc)



            calculation_end_time = time.time()
            calculation_time_cost = calculation_end_time - calculation_start_time

            res = {
                "id": list_id,
                "start time": calculation_start_time,
                "end time": calculation_end_time,
                "runtime": calculation_time_cost,
                "error": error,
                "result": result
            }
            result_queue.put(res)


    def pre_start(self, para):

        gtc = GlyTouCanNoCache()
        wp = WURCS20Format()

        file_path = self.abspath(para["glycan_file_path"])
        f1 = open(file_path, "w")
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

            f1.write("%s\t%s\n" % (acc, s))

        f1.close()




if __name__ == '__main__':
    multiprocessing.freeze_support()

    glylookup_app = GlyLookup()
    glylookup_app.find_config("GlyLookup.ini")
    glylookup_app.start()










