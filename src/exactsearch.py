

import os
import urllib, urllib2, urllib3
from framework import *


import pygly.alignment
from pygly.GlycanFormatter import WURCS20Format, GlycoCTFormat


class ExactSearchAPI(APIFrameWork):

    def workerfunction(self, PPID):
        self.output(1, "Computing Processor%s is starting" % PPID)
        task_queue = self.taskqueue
        result_queue = self.resultqueue

        topology_file_path = self._worker_para["topologyset"]
        other_file_path = self._worker_para["otherset"]

        gp = GlycoCTFormat()
        wp = WURCS20Format()

        # motif_match_connected_nodes_cache = pygly.alignment.ConnectedNodesCache()
        gie = pygly.alignment.GlycanEqual()

        topologies = {}
        saccharides = {}

        for line in open(topology_file_path):
            acc, s = line.strip().split()
            g = wp.toGlycan(s)
            l = len(list(g.all_nodes()))
            if l not in topologies:
                topologies[l] = {}
            topologies[l][acc] = g

        for line in open(other_file_path):
            acc, s = line.strip().split()
            g = wp.toGlycan(s)
            l = len(list(g.all_nodes()))
            if l not in saccharides:
                saccharides[l] = {}
            saccharides[l][acc] = g

        self.output(1, "Processor-%s: finishes loading topologies (%s) and saccharides (%s)" %
                    (PPID, len(topologies), len(saccharides)))

        while True:
            task_detail = task_queue.get(block=True)

            self.output(1, "Processor-%s: Job %s received." % (PPID, task_detail["id"]))

            seq = task_detail["seq"]
            jobid = task_detail["id"]

            hits = []
            error = []
            calculation_start_time = time.time()

            query_glycan = None
            try:
                if "RES" in seq:
                    query_glycan = gp.toGlycan(seq)
                elif "WURCS" in seq:
                    query_glycan = wp.toGlycan(seq)
                else:
                    raise RuntimeError
            except:
                error.append("Unable to parse")

            if len(error) != 0:
                for e in error:
                    self.output(1, "Processor-%s: Issues (%s) is found with task %s" % (PPID, e, task_detail["id"]))

            else:

                l = len(list(query_glycan.all_nodes()))

                if l in topologies:
                    for acc, glycan in topologies[l].items():
                        if gie.eq(query_glycan, glycan):
                            hits.append(acc)

                if len(hits) == 0 and l in saccharides:

                    for acc, glycan in saccharides[l].items():
                        if gie.eq(query_glycan, glycan):
                            hits.append(acc)

            calculation_end_time = time.time()
            calculation_time_cost = calculation_end_time - calculation_start_time

            res = {
                "id": jobid,
                "start time": calculation_start_time,
                "end time": calculation_end_time,
                "alignment calculation time": calculation_time_cost,
                "matches": hits,
                "error": error
            }
            self.output(1,  "Processor-%s: Job %s finished within %ss" % (PPID, task_detail["id"], calculation_time_cost))
            result_queue.put(res)


    def formtask(self, raw_task):
        res = {}

        res["seq"] = raw_task["seq"]
        res["id"] = hashlib.sha256(raw_task["seq"]).hexdigest()

        return res

    def home(self):
        return open("general.html").read()


if __name__ == "__main__":
    multiprocessing.freeze_support()

    es = ExactSearchAPI()

    # test cases G00028MO
    wurcs1 = "WURCS=2.0/4,7,6/[u2122h_2*NCC/3=O][a2122h-1b_1-5_2*NCC/3=O][a1122h-1b_1-5][a1122h-1a_1-5]/1-2-3-4-4-4-4/a4-b1_b4-c1_c3-d1_c6-e1_e3-f1_e6-g1"
    glycoct1 = """RES
    1b:x-dglc-HEX-x:x
    2s:n-acetyl
    3b:b-dglc-HEX-1:5
    4s:n-acetyl
    5b:b-dman-HEX-1:5
    6b:a-dman-HEX-1:5
    7b:a-dman-HEX-1:5
    8b:a-dman-HEX-1:5
    9b:a-dman-HEX-1:5
    LIN
    1:1d(2+1)2n
    2:1o(4+1)3d
    3:3d(2+1)4n
    4:3o(4+1)5d
    5:5o(3+1)6d
    6:5o(6+1)7d
    7:7o(3+1)8d
    8:7o(6+1)9d"""

    submit_url = "http://%s:%s/submit?tasks=%s" % (
        es.host(), es.port(), urllib.quote_plus(json.dumps([{"seq": wurcs1}, {"seq": glycoct1}]))
    )
    print submit_url
    retrive_url = "http://%s:%s/retrieve?list_ids=%s" % (
        es.host(), es.port(), urllib.quote_plus(json.dumps(
            ['b2cc5aab3b2d9b8e79d76ce9be868aa0cab07bcb92d424f18c66ff30272df0fb',
             '88c1bfe3ac41196ce80f5ba80aeec5748f7af5d6343de9bdc468037e4279da89']))
    )
    print retrive_url

    # End test cases


    es.autoconfigparsing("exactsearch.ini")
    es.start()



