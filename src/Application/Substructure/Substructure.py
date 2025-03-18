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

        glycan_list = params["glycan_set"] + "_glycan_list"
        structure_list_file_path = self.autopath(params[glycan_list])
        max_motif_size = int(params["max_motif_size"])


        gp = GlycoCTFormat()
        wp = WURCS20Format()

        nodes_cache = pygly.alignment.ConnectedNodesCache()

        loose_matcher = pygly.alignment.MotifInclusive(connected_nodes_cache=nodes_cache)
        loose_nred_matcher = pygly.alignment.NonReducingEndMotifInclusive(connected_nodes_cache=nodes_cache)
        loose_whole_matcher = pygly.alignment.WholeGlycanEqualMotifInclusive()

        strict_matcher = pygly.alignment.MotifStrict(connected_nodes_cache=nodes_cache)
        strict_nred_matcher = pygly.alignment.NonReducingEndMotifStrict(connected_nodes_cache=nodes_cache)
        strict_whole_matcher = pygly.alignment.WholeGlycanEqualMotifStrict()

        glycans = {}
        glycanmw = defaultdict(dict)
        for line in open(structure_list_file_path):
            acc, s = line.strip().split()
            g = wp.toGlycan(s)
            if not g.has_root():
                continue
            glycans[acc] = g
            try:
                mw = str(round(g.underivitized_molecular_weight(),2))
                glycanmw[mw][acc] = g
            except (KeyError,ValueError,TypeError):
                pass

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

            glyiter = glycans.items()
            motifmw = None
            if align == 'wholeglycan':
                try:
                    motifmw = str(round(motif.underivitized_molecular_weight(),2))
                except (KeyError,ValueError,TypeError):
                    pass
                # print(motifmw)
                if motifmw is not None:
                    glyiter = glycanmw[motifmw].items()

            if len(error) == 0:
                if not motif.has_root():
                    error.append("Motif is not a structure")

            if len(error) == 0:
                motif_node_num = len(list(motif.all_nodes()))
                if motif_node_num > max_motif_size and motifmw is None:
                    error.append("Motif is too big")

            for acc, glycan in glyiter:

                if len(error) != 0:
                    for e in error:
                        print("Processor-%s: Issues (%s) is found with task %s" % (pid, e, task_detail["id"]))
                    break
                
                # print(acc)

                # Loose match first
                idmaps_loose_core = []
                loose_core = (motifmw is None) and loose_matcher.leq(motif, glycan, rootOnly=True, anywhereExceptRoot=False, underterminedLinkage=True, idmaps=idmaps_loose_core)
                idmaps_loose_core = loose_matcher.idmaps_toids(idmaps_loose_core)

                loose_substructure_noncore = False
                idmaps_loose_noncore = []
                if align in ('substructure','nonreducingend','all'):
                    loose_substructure_noncore = loose_matcher.leq(motif, glycan, rootOnly=False, anywhereExceptRoot=True, underterminedLinkage=True,idmaps=idmaps_loose_noncore)
                    idmaps_loose_noncore =  loose_matcher.idmaps_toids(idmaps_loose_noncore)

                loose_substructure = loose_core or loose_substructure_noncore
                idmaps_loose_substructure = list(idmaps_loose_core) + list(idmaps_loose_noncore)

                loose_whole = False
                idmaps_loose_whole = []
                if (motifmw is None) and loose_core and loose_matcher.whole_glycan_match_check(motif, glycan):
                    loose_whole = True
                    idmaps_loose_whole = list(idmaps_loose_core)
                elif (motifmw is not None) and loose_whole_matcher.leq(motif,glycan,idmap=idmaps_loose_whole):
                    loose_whole = True
                    idmaps_loose_whole = loose_matcher.idmaps_toids([idmaps_loose_whole])

                loose_nred = False
                idmaps_loose_nred = []
                if not motif.repeated() and not glycan.repeated() and loose_substructure:
                    loose_nred = loose_nred_matcher.leq(motif, glycan, underterminedLinkage=True,idmaps=idmaps_loose_nred)
                    idmaps_loose_nred = loose_nred_matcher.idmaps_toids(idmaps_loose_nred)

                # if inclusive, then try to match strict
                strict_core, strict_substructure_noncore, strict_whole, strict_nred = False, False, False, False
                idmaps_strict_core = []
                idmaps_strict_noncore = []
                idmaps_strict_whole = []
                idmaps_strict_nred = []

                if loose_core:
                    strict_core = strict_matcher.leq(motif, glycan, rootOnly=True, anywhereExceptRoot=False, underterminedLinkage=False,idmaps=idmaps_strict_core)
                    idmaps_strict_core = strict_matcher.idmaps_toids(idmaps_strict_core)

                if loose_substructure_noncore:
                    if align in ('substructure','nonreducingend','all'):
                        strict_substructure_noncore = strict_matcher.leq(motif, glycan, rootOnly=False, anywhereExceptRoot=True, underterminedLinkage=False,idmaps=idmaps_strict_noncore)
                        idmaps_strict_noncore = strict_matcher.idmaps_toids(idmaps_strict_noncore)

                strict_substructure = strict_core or strict_substructure_noncore
                idmaps_strict_substructure = list(idmaps_strict_core) + list(idmaps_strict_noncore)

                if (motifmw is None) and strict_core and strict_matcher.whole_glycan_match_check(motif, glycan):
                    strict_whole = True
                    idmaps_strict_whole = list(idmaps_strict_core)
                elif (motifmw is not None) and strict_whole_matcher.leq(motif,glycan,idmap=idmaps_strict_whole):
                    strict_whole = True
                    idmaps_strict_whole = strict_matcher.idmaps_toids([idmaps_strict_whole])

                if loose_nred and strict_substructure:
                    strict_nred = strict_nred_matcher.leq(motif, glycan, underterminedLinkage=False,idmaps=idmaps_strict_nred)
                    idmaps_strict_nred = strict_nred_matcher.idmaps_toids(idmaps_strict_nred)

                glyres = [loose_core, loose_substructure, loose_whole, loose_nred,
                          strict_core, strict_substructure, strict_whole, strict_nred]

                # if loose_whole:
                #     print(acc,strict_whole)
                #     print(idmaps_loose_whole)
                #     print(idmaps_strict_whole)

                ids_loose_core = loose_matcher.matched_ids(idmaps_loose_core,glycan)
                ids_loose_substructure = loose_matcher.matched_ids(idmaps_loose_substructure,glycan)
                ids_loose_whole = loose_matcher.matched_ids(idmaps_loose_whole,glycan)
                ids_loose_nred = loose_nred_matcher.matched_ids(idmaps_loose_nred,glycan)

                ids_strict_core = strict_matcher.matched_ids(idmaps_strict_core,glycan)
                ids_strict_substructure = strict_matcher.matched_ids(idmaps_strict_substructure,glycan)
                ids_strict_whole = strict_matcher.matched_ids(idmaps_strict_whole,glycan)
                ids_strict_nred = strict_nred_matcher.matched_ids(idmaps_strict_nred,glycan)

                # if loose_substructure is False, no others can be True
                # assert loose_substructure or True not in glyres

                if loose_substructure and align in ('all','substructure'):
                    row = [acc, strict_substructure]
                    if strict_substructure:
                        row.extend([ sorted(l) for l in ids_strict_substructure ])
                    else:
                        row.extend([ sorted(l) for l in ids_loose_substructure ])
                    result['substructure'].append(row)
                if loose_core and align in ('all','core'):
                    row = [acc, strict_core]
                    if strict_core:
                        row.extend([ sorted(l) for l in ids_strict_core ])
                    else:
                        row.extend([ sorted(l) for l in ids_loose_core ])
                    result['core'].append(row)
                if loose_nred and align in ('all','nonreducingend'):
                    row = [acc, strict_nred]
                    if strict_nred:
                        row.extend([ sorted(l) for l in ids_strict_nred ])
                    else:
                        row.extend([ sorted(l) for l in ids_loose_nred ])
                    result['nonreducingend'].append(row)
                if loose_whole and align in ('all','wholeglycan'):
                    row = [acc, strict_whole]
                    if strict_whole:
                        row.extend([ sorted(l) for l in ids_strict_whole ])
                    else:
                        row.extend([ sorted(l) for l in ids_loose_whole ])
                    result['wholeglycan'].append(row)

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

        data_file_path1 = self.autopath(worker_para["glygen_glycan_list"])
        data_file_path2 = self.autopath(worker_para["glytoucan_glycan_list"])

        glygen_set = set()
        gg = pygly.GlycanResource.GlyGen()
        for acc in gg.allglycans():
            glygen_set.add(acc.strip())

        wp = WURCS20Format()
        gtc = pygly.GlycanResource.GlyTouCanNoCache()

        f1 = open(self.autopath("tmp1.txt", newfile=True), "w")
        f2 = open(self.autopath("tmp2.txt", newfile=True), "w")

        for acc, f, s in gtc.allseq(format="wurcs"):

            try:
                g = wp.toGlycan(s)
            except:
                continue

            if acc in glygen_set:
                f1.write("%s\t%s\n" % (acc, s))
            f2.write("%s\t%s\n" % (acc, s))

        f1.close()
        f2.close()

        if os.path.exists(data_file_path1):
            os.remove(data_file_path1)
        if os.path.exists(data_file_path2):
            os.remove(data_file_path2)
        os.rename(self.autopath("tmp1.txt", newfile=True), data_file_path1)
        os.rename(self.autopath("tmp2.txt", newfile=True), data_file_path2)



if __name__ == '__main__':
    multiprocessing.freeze_support()

    substructure_app = Substructure()
    substructure_app.find_config("Substructure.ini")
    substructure_app.start()










