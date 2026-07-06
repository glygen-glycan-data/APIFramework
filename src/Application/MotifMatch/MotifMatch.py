#!/bin/env python3.12

import os
import sys
import time
import flask
import multiprocessing
from APIFramework import APIFramework, APIFrameworkWithFrontEnd, queue

import pygly.alignment
from pygly.GlycanFormatter import WURCS20Format, GlycoCTFormat
from pygly.GlycanMultiParser import GlycanMultiParser, GlycanParseError

import pygly.GlycanResource.GlycoMotif

class MotifMatch(APIFrameworkWithFrontEnd):
    task_params = dict(seq=None,
                       collection="GM")

    def worker(self, pid):
        self.start_worker(pid)

        motif_file_path = self.get_filename_param("motif_set")

        gmp = GlycanMultiParser()

        motif_match_connected_nodes_cache = pygly.alignment.ConnectedNodesCache()

        loose_matcher = pygly.alignment.MotifInclusive(connected_nodes_cache=motif_match_connected_nodes_cache)
        loose_nred_matcher = pygly.alignment.NonReducingEndMotifInclusive(connected_nodes_cache=motif_match_connected_nodes_cache)

        strict_matcher = pygly.alignment.MotifStrict(connected_nodes_cache=motif_match_connected_nodes_cache)
        strict_nred_matcher = pygly.alignment.NonReducingEndMotifStrict(connected_nodes_cache=motif_match_connected_nodes_cache)

        motifs = {}
        GlycoMotifPages = []
        for line in open(motif_file_path):
            # acc, name, s =
            collection, pageacc, acc, name, s = line.strip().split("\t")

            motifs[acc] = gmp.toGlycan(s)
            GlycoMotifPages.append([collection, pageacc, acc, name])

        self.worker_ready()    

        while True:
            task_detail = self.get_task()

            result = []

            try:
                seq = str(task_detail["seq"])
                selected_collection = str(task_detail["collection"])
            except (TypeError,ValueError,AttributeError,KeyError):
                self.put_error("Required parameters are missing")
                continue

            try:
                glycan = gmp.toGlycan(seq)
            except GlycanParseError:
                self.put_error("Unable to parse")
                continue

            selected_pages = []
            for page in GlycoMotifPages:
                collection, pageacc, acc, name = page

                if collection != selected_collection:
                    continue

                selected_pages.append(page)



            for collection, pageacc, acc, name in selected_pages:

                motif = motifs[acc]

                core_loose, core_strict, sub_loose, sub_strict, whole_loose, whole_strict, nred_loose, nred_strict = [False] * 8
                core_loose =  loose_matcher.leq(motif, glycan, rootOnly=True, anywhereExceptRoot=False, underterminedLinkage=True)
                if core_loose:
                    core_strict = strict_matcher.leq(motif, glycan, rootOnly=True, anywhereExceptRoot=False, underterminedLinkage=False)
                    result.append([collection, pageacc, acc, name, "Core", core_strict])


                sub_partial_loose, sub_partial_strict = [False] * 2
                if not core_strict:
                    sub_partial_loose = loose_matcher.leq(motif, glycan, rootOnly=False, anywhereExceptRoot=True, underterminedLinkage=True)
                    if sub_partial_loose:
                        sub_partial_strict = strict_matcher.leq(motif, glycan, rootOnly=False, anywhereExceptRoot=True, underterminedLinkage=False)

                sub_loose = core_loose or sub_partial_loose
                sub_strict = core_strict or sub_partial_strict

                if sub_loose:
                    result.append([collection, pageacc, acc, name, "Substructure", sub_strict])

                if core_loose:
                    if len(list(motif.all_nodes())) == len(list(glycan.all_nodes())):
                        result.append([collection, pageacc, acc, name, "Whole", core_strict])


                nred_loose = loose_nred_matcher.leq(motif, glycan, underterminedLinkage=True)
                if nred_loose:
                    nred_strict = strict_nred_matcher.leq(motif, glycan, underterminedLinkage=False)
                    result.append([collection, pageacc, acc, name, "Non-Reducing", nred_strict])

            self.put_result(result)

    def pre_start(self, worker_para):

        data_file_path = self.autopath(worker_para["motif_set"])

        site = ""
        if "glycomotif_version" in worker_para:
            site = worker_para["glycomotif_version"]
        assert site in ["", "dev", "test"]

        if site == "dev":
            gm = pygly.GlycanResource.GlycoMotifDev(usecache=False)
        else:
            gm = pygly.GlycanResource.GlycoMotif(usecache=False)

        gmp = GlycanMultiParser()

        q2 = """
        PREFIX glycomotif: <http://glyomics.org/glycomotif#>
        
        SELECT ?collectionid ?accession ?gtcacc ?preferred_name ?wurcs ?glycoct
        WHERE {
            ?collection a glycomotif:Collection .
            ?collection glycomotif:id ?collectionid .
            
            ?motif a glycomotif:Motif .
            ?motif glycomotif:accession ?accession .
            ?motif glycomotif:incollection ?collection . 
            ?motif glycomotif:glytoucan ?gtcacc . 
            
            OPTIONAL { ?motif glycomotif:preferred_name ?preferred_name }
            OPTIONAL { ?motif glycomotif:wurcs ?wurcs }
            OPTIONAL { ?motif glycomotif:glycoct ?glycoct }
        }
        ORDER BY ?collectionid ?accession ?gtcacc ?preferred_name
        """

        data_file_handle = open(self.autopath("tmp.txt", newfile=True), "w")
        for i in gm.queryts(q2):
            res = list(i[:])

            res[0] = str(res[0]).split("/")[-1]

            res[1] = str(res[1])
            res[2] = str(res[2])

            # print(i)

            if res[3] != None:
                try:
                    res[3] = str(res[3])
                except:
                    # print res[3]
                    # Contains UTF-8 char...
                    res[3] = ""

            else:
                res[3] = ""

            res[4] = str(res[4])

            del res[5]


            l = "\t".join(res)

            try:
                gmp.toGlycan(res[4])
            except:
                continue

            data_file_handle.write(l+"\n")

        if os.path.exists(data_file_path):
            os.remove(data_file_path)
        os.rename(self.autopath("tmp.txt"), data_file_path)


if __name__ == '__main__':
    multiprocessing.freeze_support()

    motifmatch_app = MotifMatch()
    motifmatch_app.find_config("MotifMatch.ini")
    motifmatch_app.start()



