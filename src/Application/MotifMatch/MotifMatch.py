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

        loose_matcher = pygly.alignment.MotifInclusive(connected_nodes_cache=motif_match_connected_nodes_cache)
        loose_nred_matcher = pygly.alignment.NonReducingEndMotifInclusive(connected_nodes_cache=motif_match_connected_nodes_cache)

        strict_matcher = pygly.alignment.MotifStrict(connected_nodes_cache=motif_match_connected_nodes_cache)
        strict_nred_matcher = pygly.alignment.NonReducingEndMotifStrict(connected_nodes_cache=motif_match_connected_nodes_cache)

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

                for mode in ["Inclusive", "Strict"]:

                    if mode == "Inclusive":
                        matcher = loose_matcher
                        nred_matcher = loose_nred_matcher
                        und_link = True

                    else:
                        matcher = strict_matcher
                        nred_matcher = strict_nred_matcher
                        und_link = False

                    if matcher.leq(motif, glycan, rootOnly=True, anywhereExceptRoot=False, underterminedLinkage=und_link):
                        # result.append(acc)
                        result.append([acc, names[acc], mode, "Core"])

                    if matcher.leq(motif, glycan, rootOnly=False, anywhereExceptRoot=True, underterminedLinkage=und_link):
                        # result.append(acc)
                        result.append([acc, names[acc], mode, "Substructure"])

                    if nred_matcher.leq(motif, glycan):
                        # result.append(acc)
                        result.append([acc, names[acc], mode, "Non-Reducing"])

                    if len(list(motif.all_nodes())) == len(list(glycan.all_nodes())):
                        if matcher.leq(motif, glycan, rootOnly=True, anywhereExceptRoot=False, underterminedLinkage=und_link):
                            # result.append(acc)
                            result.append([acc, names[acc], mode, "Whole"])


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










