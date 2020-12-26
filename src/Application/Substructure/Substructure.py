import sys
import time
import hashlib
import multiprocessing
from APIFramework import APIFramework

import pygly.alignment
from pygly.GlycanFormatter import WURCS20Format, GlycoCTFormat



class Substructure(APIFramework):

    def form_task(self, p):
        res = {}
        task_str = p["seq"] + "_" + p["motif_match_position"]
        task_str.encode("utf-8")
        list_id = hashlib.sha256(task_str).hexdigest()

        res["id"] = list_id
        res["seq"] = p["seq"]
        res["motif_match_position"] = p["motif_match_position"]

        return res

    @staticmethod
    def worker(pid, task_queue, result_queue, params):
        print(pid, "Start")

        structure_list_file_path = params["glycan_set"]
        max_motif_size = int(params["max_motif_size"])


        gp = GlycoCTFormat()
        wp = WURCS20Format()

        motif_match_connected_nodes_cache = pygly.alignment.ConnectedNodesCache()
        motif_matcher = pygly.alignment.GlyTouCanMotif(connected_nodes_cache=motif_match_connected_nodes_cache)

        glycans = {}
        for line in open(structure_list_file_path):
            acc, s = line.strip().split()
            glycans[acc] = wp.toGlycan(s)

        while True:
            task_detail = task_queue.get(block=True)

            result = []
            error = []
            calculation_start_time = time.time()


            list_id = task_detail["id"]
            seq = task_detail["seq"]

            motif_match_position = task_detail["motif_match_position"]

            rootOnly = False
            anywhereExceptRoot = False
            if motif_match_position == "anywhere":
                pass
            elif motif_match_position == "reo":
                rootOnly = True
            else:
                pass

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

            # TODO time out mechanism to avoid running for too long
            for acc, glycan in glycans.items():

                if len(error) != 0:
                    for e in error:
                        print("Processor-%s: Issues (%s) is found with task %s" % (pid, e, task_detail["id"]))
                    break

                # if fullstructure:
                #    if motif_node_num != len(list(glycan.all_nodes())):
                #        continue

                if motif_matcher.leq(motif, glycan, rootOnly=rootOnly, anywhereExceptRoot=anywhereExceptRoot):
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




if __name__ == '__main__':
    multiprocessing.freeze_support()

    substructure_app = Substructure()
    substructure_app.find_config("Substructure.ini")
    substructure_app.start()










