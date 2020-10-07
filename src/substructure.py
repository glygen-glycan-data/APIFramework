

import os
import urllib, urllib2, urllib3
from framework import *


import pygly.alignment
from pygly.GlycanFormatter import WURCS20Format, GlycoCTFormat


class SubstAPI(APIFrameWork):

    def workerfunction(self, PPID):
        self.output(1, "Computing Processor%s is starting" % PPID)

        task_queue = self.taskqueue
        result_queue = self.resultqueue

        max_motif_size = int(self._worker_para["max_motif_size"])
        structure_list_file_path = self._worker_para["glycan_set"]

        gp = GlycoCTFormat()
        wp = WURCS20Format()

        motif_match_connected_nodes_cache = pygly.alignment.ConnectedNodesCache()
        mm1 = pygly.alignment.GlyTouCanMotif(connected_nodes_cache=motif_match_connected_nodes_cache)
        # mm2 = pygly.alignment.MotifAllowOptionalSub(connected_nodes_cache=motif_match_connected_nodes_cache)

        glycans = {}
        for line in open(structure_list_file_path):
            acc, s = line.strip().split()
            glycans[acc] = wp.toGlycan(s)
        self.output(1, "Processor-%s: finishes loading %s glycans" % (PPID, len(glycans)))

        while True:
            task_detail = task_queue.get(block=True)

            self.output(1, "Processor-%s: Job %s received." % (PPID, task_detail["id"]))

            seq = task_detail["seq"]
            jobid = task_detail["id"]

            # loose_root_match = task_detail["loose_root_match"]
            # additional_subst = task_detail["additional_subst"]

            motif_match_position = task_detail["motif_match_position"]

            motif_matcher = mm1
            """
            if loose_root_match:
                motif_matcher = mm3

            """

            # fullstructure = False
            rootOnly = False
            anywhereExceptRoot = False
            if motif_match_position == "anywhere":
                pass
            elif motif_match_position == "reo":
                rootOnly = True
            else:
                pass
            """
            elif motif_match_position == "notre":
                anywhereExceptRoot = True
            elif motif_match_position == "fullstructure":
                rootOnly = True
                fullstructure = True
            """

            matches = []
            error = []
            calculation_start_time = time.time()

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
                        self.output(1,  "Processor-%s: Issues (%s) is found with task %s" %
                                    (PPID, e, task_detail["id"]))
                    break

                # if fullstructure:
                #    if motif_node_num != len(list(glycan.all_nodes())):
                #        continue

                if motif_matcher.leq(motif, glycan, rootOnly=rootOnly, anywhereExceptRoot=anywhereExceptRoot):
                    matches.append(acc)

            calculation_end_time = time.time()
            calculation_time_cost = calculation_end_time - calculation_start_time

            res = {
                "id": jobid,
                "start time": calculation_start_time,
                "end time": calculation_end_time,
                "alignment calculation time": calculation_time_cost,
                "matches": matches,
                "error": error
            }
            self.output(1, "Processor-%s: Job %s finished within %ss" %
                        (PPID, task_detail["id"], calculation_time_cost))
            result_queue.put(res)


    def formtask(self, raw_task):
        res = {}

        res["seq"] = raw_task["seq"]
        res["motif_match_position"] = raw_task["seq"]
        res["id"] = hashlib.sha256(res["seq"] + "_" + res["motif_match_position"]).hexdigest()

        return res

    def home(self):
        return open("general.html").read()


if __name__ == "__main__":
    multiprocessing.freeze_support()

    ss = SubstAPI()
    ss.autoconfigparsing("substructure.ini")
    ss.start()

