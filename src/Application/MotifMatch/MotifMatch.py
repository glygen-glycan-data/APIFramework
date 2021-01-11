import sys
import time
import flask
import hashlib
import multiprocessing
from APIFramework import APIFramework

import pygly.alignment
from pygly.GlycanFormatter import WURCS20Format, GlycoCTFormat

import pygly.GlycanResource.GlycoMotif



class MotifMatch(APIFramework):

    def form_task(self, p):
        res = {}

        seq = p["seq"]
        collection = "GM"
        if "collection" in p:
            collection = p["collection"]

        task_str = seq + "_" + collection
        task_str.encode("utf-8")
        list_id = hashlib.sha256(task_str).hexdigest()

        res["id"] = list_id
        res["seq"] = seq
        res["collection"] = collection

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
        GlycoMotifPages = []
        for line in open(motif_file_path):
            # acc, name, s =
            collection, pageacc, acc, name, s = line.strip().split("\t")

            motifs[acc] = wp.toGlycan(s)
            GlycoMotifPages.append([collection, pageacc, acc, name])


        while True:
            task_detail = task_queue.get(block=True)

            result = []
            error = []
            calculation_start_time = time.time()


            list_id = task_detail["id"]
            seq = task_detail["seq"]
            selected_collection = task_detail["collection"]


            try:
                if "RES" in seq:
                    glycan = gp.toGlycan(seq)
                elif "WURCS" in seq:
                    glycan = wp.toGlycan(seq)
                else:
                    raise RuntimeError
            except:
                error.append("Unable to parse")


            selected_pages = []
            for page in GlycoMotifPages:
                collection, pageacc, acc, name = page

                if collection != selected_collection:
                    continue

                selected_pages.append(page)



            for collection, pageacc, acc, name in selected_pages:

                motif = motifs[acc]

                if len(error) != 0:
                    for e in error:
                        print("Processor-%s: Issues (%s) is found with task %s" % (pid, e, task_detail["id"]))
                    break


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



    def pre_start(self, worker_para):

        data_file_path = self.abspath(worker_para["motif_set"])

        site = ""
        if "glycomotif_version" in worker_para:
            site = worker_para["glycomotif_version"]
        assert site in ["", "dev", "test"]

        gm = pygly.GlycanResource.GlycoMotif()
        gm.endpt = "https://edwardslab.bmcb.georgetown.edu/sparql/glycomotif"+site+"/query"

        wp = WURCS20Format()

        q2 = """
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX glycomotif: <http://glycandata.glygen.org/glycomotif#>

        SELECT ?collection ?accession ?gtcacc (group_concat(?aname;SEPARATOR="//") as ?name) ?wurcs ?glycoct
        WHERE {
            ?motif rdf:type glycomotif:Motif .
            ?motif glycomotif:accession ?accession .
            ?motif glycomotif:incollection ?collection . 
            ?motif glycomotif:glytoucan ?gtcacc . 
            ?collection rdf:type glycomotif:Collection .
            OPTIONAL { ?motif glycomotif:name ?aname }
            OPTIONAL { ?motif glycomotif:wurcs ?wurcs }
            OPTIONAL { ?motif glycomotif:glycoct ?glycoct }
        }
        GROUP BY ?collection ?accession ?gtcacc ?wurcs ?glycoct
        ORDER BY ?collection ?accession
        """

        data_file_handle = open(data_file_path, "w")
        for i in gm.queryts(q2):
            res = list(i[:])

            res[0] = str(res[0]).split("/")[-1]

            res[1] = str(res[1])
            res[2] = str(res[2])

            if res[3] != None:
                try:
                    res[3] = str(res[3])
                except:
                    print res[3]
                    res[3] = ""

            else:
                res[3] = ""

            res[4] = str(res[4])

            del res[5]


            l = "\t".join(res)

            try:
                wp.toGlycan(res[4])
            except:
                continue

            data_file_handle.write(l+"\n")


if __name__ == '__main__':
    multiprocessing.freeze_support()

    motifmatch_app = MotifMatch()
    motifmatch_app.find_config("MotifMatch.ini")
    motifmatch_app.start()



