import sys
import time
import flask
import hashlib
import multiprocessing
from APIFramework import APIFramework

import pygly.alignment
from pygly.GlycanFormatter import WURCS20Format, GlycoCTFormat



class MotifMatch(APIFramework):

    def form_task(self, p):
        res = {}
        task_str = p["seq"]
        task_str.encode("utf-8")
        list_id = hashlib.sha256(task_str).hexdigest()

        res["id"] = list_id
        res["seq"] = p["seq"]

        return res

    @staticmethod
    def worker(pid, task_queue, result_queue, params):
        print(pid, "Start")

        motif_file_path = params["motif_set"]


        gp = GlycoCTFormat()
        wp = WURCS20Format()

        motif_match_connected_nodes_cache = pygly.alignment.ConnectedNodesCache()

        normal_motif_matcher = pygly.alignment.GlyTouCanMotif(connected_nodes_cache=motif_match_connected_nodes_cache)
        nonred_motif_matcher = pygly.alignment.GlyTouCanMotif(connected_nodes_cache=motif_match_connected_nodes_cache)
        gtc_motif_matcher = pygly.alignment.GlyTouCanMotif(connected_nodes_cache=motif_match_connected_nodes_cache)


        motifs = {}
        names = {}
        for line in open(motif_file_path):
            acc, name, s = line.strip().split("\t")
            motifs[acc] = wp.toGlycan(s)
            names[acc] = name

        while True:
            task_detail = task_queue.get(block=True)

            result = []
            error = []
            calculation_start_time = time.time()


            list_id = task_detail["id"]
            seq = task_detail["seq"]


            try:
                if "RES" in seq:
                    glycan = gp.toGlycan(seq)
                elif "WURCS" in seq:
                    glycan = wp.toGlycan(seq)
                else:
                    raise RuntimeError
            except:
                error.append("Unable to parse")


            for acc, motif in motifs.items():

                if len(error) != 0:
                    for e in error:
                        print("Processor-%s: Issues (%s) is found with task %s" % (pid, e, task_detail["id"]))
                    break

                # if fullstructure:
                #    if motif_node_num != len(list(glycan.all_nodes())):
                #        continue

                if normal_motif_matcher.leq(motif, glycan, rootOnly=True, anywhereExceptRoot=False):
                    # result.append(acc)
                    result.append([acc, names[acc], "Core"])

                if normal_motif_matcher.leq(motif, glycan, rootOnly=False, anywhereExceptRoot=True):
                    # result.append(acc)
                    result.append([acc, names[acc], "Substructure"])

                if nonred_motif_matcher.leq(motif, glycan):
                    # result.append(acc)
                    result.append([acc, names[acc], "Non-Reducing"])

                if len(list(motif.all_nodes())) == len(list(glycan.all_nodes())):
                    if gtc_motif_matcher.leq(motif, glycan, rootOnly=True, anywhereExceptRoot=False):
                        # result.append(acc)
                        result.append([acc, names[acc], "Whole"])



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




if __name__ == '__main__':
    multiprocessing.freeze_support()

    motifmatch_app = MotifMatch()
    motifmatch_app.find_config("MotifMatch.ini")
    motifmatch_app.start()










