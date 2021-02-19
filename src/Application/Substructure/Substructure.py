import os
import sys
import time
import hashlib
import multiprocessing
from APIFramework import APIFramework, queue

import pygly.alignment
from pygly.GlycanFormatter import WURCS20Format, GlycoCTFormat

import pygly.GlycanResource.GlyGen
import pygly.GlycanResource.GlyTouCan



class Substructure(APIFramework):

    def form_task(self, p):
        res = {}
        task_str = p["seq"].strip()
        task_str.encode("utf-8")
        list_id = hashlib.md5(task_str).hexdigest()

        res["id"] = list_id
        res["seq"] = p["seq"]

        return res


    def worker(self, pid, task_queue, result_queue, params):

        self.output(2, "Worker-%s is starting up" % (pid))

        structure_list_file_path = params["glycan_list"]
        max_motif_size = int(params["max_motif_size"])


        gp = GlycoCTFormat()
        wp = WURCS20Format()

        motif_match_connected_nodes_cache = pygly.alignment.ConnectedNodesCache()
        loose_motif_matcher = pygly.alignment.MotifInclusive(connected_nodes_cache=motif_match_connected_nodes_cache)
        strict_motif_matcher = pygly.alignment.MotifStrict(connected_nodes_cache=motif_match_connected_nodes_cache)

        glycans = {}
        for line in open(structure_list_file_path):
            acc, s = line.strip().split()
            glycans[acc] = wp.toGlycan(s)

        self.output(2, "Worker-%s is ready to take job" % (pid))

        while True:
            try:
                task_detail = task_queue.get_nowait()
            except queue.Empty:
                time.sleep(1)
                continue

            self.output(1, "Worker-%s is computing task: %s" % (pid, task_detail))

            result = []
            error = []
            calculation_start_time = time.time()


            list_id = task_detail["id"]
            seq = task_detail["seq"]


            try:
                if "RES" in seq:
                    motif = gp.toGlycan(seq)
                elif "WURCS" in seq:
                    motif = wp.toGlycan(seq)
                else:
                    raise RuntimeError
            except:
                error.append("Unable to parse")

            if len(error) == 0:
                motif_node_num = len(list(motif.all_nodes()))
                if motif_node_num > max_motif_size:
                    error.append("Motif is too big")

            for acc, glycan in glycans.items():

                if len(error) != 0:
                    for e in error:
                        print("Processor-%s: Issues (%s) is found with task %s" % (pid, e, task_detail["id"]))
                    break

                strict = False
                loose = loose_motif_matcher.leq(motif, glycan, underterminedLinkage=True)
                if loose:
                    strict = strict_motif_matcher.leq(motif, glycan, underterminedLinkage=False)
                    result.append([acc, strict])



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


    def pre_start(self, worker_para):

        data_file_path = self.abspath(worker_para["glycan_list"])

        glygen = False
        if "glycan_set" in worker_para and worker_para["glycan_set"] == "glygen":
            glygen = True

        glygen_set = set()

        if glygen:
            gg = pygly.GlycanResource.GlyGen()
            for acc in gg.allglycans():
                glygen_set.add(acc.strip())


        wp = WURCS20Format()
        gtc = pygly.GlycanResource.GlyTouCanNoCache()

        f1 = open("tmp.txt", "w")

        for acc, f, s in gtc.allseq(format="wurcs"):

            try:
                g = wp.toGlycan(s)
            except:
                continue

            if glygen and acc in glygen_set:
                f1.write("%s\t%s\n" % (acc, s))

            elif not glygen:
                f1.write("%s\t%s\n" % (acc, s))


        f1.close()

        if os.path.exists(data_file_path):
            os.remove(data_file_path)
        os.rename("tmp.txt", data_file_path)



if __name__ == '__main__':
    multiprocessing.freeze_support()

    substructure_app = Substructure()
    substructure_app.find_config("Substructure.ini")
    substructure_app.start()










