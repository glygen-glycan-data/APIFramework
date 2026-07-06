#!/bin/env python3.12 

import os
import sys
import time
import multiprocessing
from collections import defaultdict
from APIFramework import APIFramework, APIFrameworkWithFrontEnd, queue

import pygly.alignment
from pygly.GlycanMultiParser import GlycanMultiParser, GlycanParseError

import pygly.GlycanResource.GlyGen
import pygly.GlycanResource.GlyTouCan



class Substructure(APIFrameworkWithFrontEnd):

    task_params = {'seq':   None, # No default
                   'align': 'substructure'}

    def worker(self, pid):
        self.start_worker(pid)

        glycan_list = self.get_param("glycan_set","glytoucan") + "_glycan_list"
        structure_list_file_path = self.get_filename_param(glycan_list)
        max_motif_size = int(self.get_param("max_motif_size"))

        gp = GlycanMultiParser()

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
            try:
                acc, s, mw = line.split()
            except ValueError:
                acc, s = line.split()
                mw = "-"
            g = gp.toGlycan(s)
            glycans[acc] = g
            if mw != "-":
                glycanmw[mw][acc] = g

        self.worker_output("Total structures: %d"%(len(glycans),))
        self.worker_ready()

        while True:
            task_detail = self.get_task()

            try:
                seq = str(task_detail["seq"])
                align = str(task_detail["align"])
            except (TypeError,ValueError,AttributeError,KeyError):
                self.put_error("Required parameters are missing")
                continue

            result = {}
            if align in ('all','substructure'):
                result['substructure'] = []
            if align in ('all','core'):
                result['core'] = []
            if align in ('all','nonreducingend'):
                result['nonreducingend'] = []
            if align in ('all','wholeglycan'):
                result['wholeglycan'] = []

            try:
                motif = gp.toGlycan(seq)
            except (GlycanParseError,TypeError,RuntimeError):
                self.put_error("Unable to parse")
                continue

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

            if not motif.has_root():
                self.put_error("Input glycan is a composition")
                continue

            motif_node_num = len(list(motif.all_nodes()))
            if motif_node_num > max_motif_size and motifmw is None:
                self.put_error("Motif is too big")

            for acc, glycan in glyiter:

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

            self.put_result(result)


    def pre_start(self, worker_para):

        data_file_path1 = self.autopath(worker_para["glygen_glycan_list"])
        data_file_path2 = self.autopath(worker_para["glytoucan_glycan_list"])

        glygen_set = set()
        gg = pygly.GlycanResource.GlyGen()
        for acc in gg.allglycans():
            glygen_set.add(acc.strip())

        gp = GlycanMultiParser()
        gtc = pygly.GlycanResource.GlyTouCanNoCache()

        f1 = open(self.autopath("tmp1.txt", newfile=True), "w")
        f2 = open(self.autopath("tmp2.txt", newfile=True), "w")

        for acc, f, s in gtc.allseq(format="wurcs"):

            try:
                g = gp.toGlycan(s)
            except:
                continue

            g = gp.toGlycan(s)
            if not g.has_root():
                continue

            mw = "-"
            try:
                mw = str(round(g.underivitized_molecular_weight(),2))
            except (KeyError,ValueError,TypeError):
                pass

            if acc in glygen_set:
                f1.write("%s\t%s\t%s\n" % (acc, s, mw))
            f2.write("%s\t%s\t%s\n" % (acc, s, mw))

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










