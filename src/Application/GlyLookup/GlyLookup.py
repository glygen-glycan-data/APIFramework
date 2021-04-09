
import os
import sys
import time
import multiprocessing
from APIFramework import APIFramework, APIFrameworkWithFrontEnd, queue

import pygly.alignment
from pygly.GlycanResource.GlyTouCan import GlyTouCanNoCache, GlyTouCan
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
        glycan_by_mass = {}

        hash2seq = {}


        for line in open(glycan_file_path):

            acc, mass, wseq, gseq, xxx = line.strip().split("\t")
            gseq = gseq.replace("\\n", "\n")

            for s in [wseq, gseq]:
                if s != "":
                    h = self.str2hash(s)
                    hash2seq[h] = acc

            if mass == "":
                continue
            elif mass not in glycan_by_mass:
                glycan_by_mass[mass] = []

            glycan_by_mass[mass].append(acc)
            wurcss[acc] = wseq

        glycan_by_mass[None] = []

        self.output(2, "Worker-%s is ready to take job" % (pid))

        while True:
            task_detail = self.task_queue_get(task_queue, pid, suicide_queue_pair)

            self.output(2, "Worker-%s is computing task: %s" % (pid, task_detail))

            error = []
            calculation_start_time = time.time()


            list_id = task_detail["id"]
            seq = str(task_detail["seq"])
            result = []

            h = self.str2hash(seq)
            if h in hash2seq:
                acc = hash2seq[h]
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

            self.output(2, "Worker-%s finished computing job (%s)" % (pid, list_id))

            res = {
                "id": list_id,
                "start time": calculation_start_time,
                "end time": calculation_end_time,
                "runtime": calculation_time_cost,
                "error": error,
                "result": result
            }

            self.output(2, "Job (%s): %s" % (list_id, res))

            result_queue.put(res)


    def pre_start(self, para):

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
                data[acc] = ["", "", ""]

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










