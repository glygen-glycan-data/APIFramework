import os
import sys
import time
import multiprocessing
from collections import defaultdict
from APIFramework import APIFramework, APIFrameworkWithFrontEnd, queue

import pygly.alignment
from pygly.GlycanFormatter import WURCS20Format, GlycoCTFormat

import pygly.GlycanResource.GlyGen
import pygly.GlycanResource.GlyTouCan



class Substructure(APIFrameworkWithFrontEnd):

    task_params = {'seq':   None, # No default
                   'align': 'substructure'}

    def worker(self, pid, task_queue, result_queue, suicide_queue_pair, params):

        self.output(2, "Worker-%s is starting up" % (pid))

        structure_list_file_path = self.autopath(params["glycan_list"])
        max_motif_size = int(params["max_motif_size"])


        gp = GlycoCTFormat()
        wp = WURCS20Format()

        nodes_cache = pygly.alignment.ConnectedNodesCache()

        loose_matcher = pygly.alignment.MotifInclusive(connected_nodes_cache=nodes_cache)
        loose_nred_matcher = pygly.alignment.NonReducingEndMotifInclusive(connected_nodes_cache=nodes_cache)

        strict_matcher = pygly.alignment.MotifStrict(connected_nodes_cache=nodes_cache)
        strict_nred_matcher = pygly.alignment.NonReducingEndMotifStrict(connected_nodes_cache=nodes_cache)

        glycans = {}
        for line in open(structure_list_file_path):
            acc, s = line.strip().split()
            glycans[acc] = wp.toGlycan(s)

        self.output(2, "Worker-%s is ready to take job" % (pid))

        while True:
            task_detail = self.task_queue_get(task_queue, pid, suicide_queue_pair)

            self.output(2, "Worker-%s is computing task: %s" % (pid, task_detail))

            list_id = task_detail["id"]
            seq = task_detail["seq"]
            align = task_detail["align"]

            result = {}
            if align in ('all','substructure'):
                result['substructure'] = []
            if align in ('all','core'):
                result['core'] = []
            if align in ('all','nonreducingend'):
                result['nonreducingend'] = []
            if align in ('all','wholeglycan'):
                result['wholeglycan'] = []

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

            for acc, glycan in glycans.items():

                if len(error) != 0:
                    for e in error:
                        print("Processor-%s: Issues (%s) is found with task %s" % (pid, e, task_detail["id"]))
                    break

                # Loose match first
                loose_core = loose_matcher.leq(motif, glycan, rootOnly=True, anywhereExceptRoot=False, underterminedLinkage=True)
                loose_substructure_partial = False
                if not loose_core and align in ('substructure','nonreducingend','all'):
                    loose_substructure_partial = loose_matcher.leq(motif, glycan, rootOnly=False, anywhereExceptRoot=True, underterminedLinkage=True)
                loose_substructure = loose_core or loose_substructure_partial

                loose_whole = False
                if loose_core and loose_matcher.whole_glycan_match_check(motif, glycan):
                    loose_whole = True

                loose_nred = False
                if not motif.repeated() and not glycan.repeated() and loose_substructure:
                    loose_nred = loose_nred_matcher.leq(motif, glycan, underterminedLinkage=True)

                # if inclusive, then try to match strict
                strict_core, strict_substructure_partial, strict_whole, strict_nred = False, False, False, False
                if loose_core:
                    strict_core = strict_matcher.leq(motif, glycan, rootOnly=True, anywhereExceptRoot=False, underterminedLinkage=False)

                if loose_substructure_partial:
                    if not strict_core and align in ('substructure','nonreducingend','all'):
                        strict_substructure_partial = strict_matcher.leq(motif, glycan, rootOnly=False, anywhereExceptRoot=True, underterminedLinkage=False)

                strict_substructure = strict_core or strict_substructure_partial

                if strict_core and strict_matcher.whole_glycan_match_check(motif, glycan):
                    strict_whole = True

                if loose_nred and strict_substructure:
                    strict_nred = strict_nred_matcher.leq(motif, glycan, underterminedLinkage=False)

                glyres = [loose_core, loose_substructure, loose_whole, loose_nred,
                          strict_core, strict_substructure, strict_whole, strict_nred]

                # if loose_substructure is False, no others can be True
                # assert loose_substructure or True not in glyres

                if loose_substructure and align in ('all','substructure'):
                    result['substructure'].append([acc, strict_substructure])
                if loose_core and align in ('all','core'):
                    result['core'].append([acc, strict_core])
                if loose_nred and align in ('all','nonreducingend'):
                    result['nonreducingend'].append([acc, strict_nred])
                if loose_whole and align in ('all','wholeglycan'):
                    result['wholeglycan'].append([acc,strict_whole])

            calculation_end_time = time.time()
            calculation_time_cost = calculation_end_time - calculation_start_time

            self.output(2, "Worker-%s finished computing job (%s)" % (pid, list_id))

            res = {
                "id": list_id,
                "start time": calculation_start_time,
                "end time": calculation_end_time,
                "runtime": calculation_time_cost,
                "error": error,
                "result": result,
            }

            self.output(2, "Job (%s): %s" % (list_id, res))

            result_queue.put(res)


    def pre_start(self, worker_para):

        data_file_path = self.autopath(worker_para["glycan_list"])

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

        f1 = open(self.autopath("tmp.txt", newfile=True), "w")

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
        os.rename(self.autopath("tmp.txt", newfile=True), data_file_path)



if __name__ == '__main__':
    multiprocessing.freeze_support()

    substructure_app = Substructure()
    substructure_app.find_config("Substructure.ini")
    substructure_app.start()










