
import os
import sys
import time
import multiprocessing
from APIFramework import APIFramework, APIFrameworkWithFrontEnd, queue

import pygly.alignment
from pygly.GlycanResource.GlyTouCan import GlyTouCanNoCache, GlyTouCan
from pygly.GlycanFormatter import WURCS20Format, GlycoCTFormat


class Register(APIFrameworkWithFrontEnd):

    def form_task(self, p):
        res = {}

        p["seq"] = p["seq"].strip()
        task_str = p["seq"].encode("utf-8") + "_" + str(int(time.time()/600))
        list_id = self.str2hash(task_str)

        res["id"] = list_id
        res["seq"] = p["seq"]

        return res


    def worker(self, pid, task_queue, result_queue, suicide_queue_pair, params):

        self.output(2, "Worker-%s is starting up" % (pid))

        # TODO get hash in batch
        glytoucan_userid = params["userid"]
        glytoucan_apikey = params["apikey"]

        gtc = GlyTouCan(prefetch=False)
        gtc.setup(user=glytoucan_userid, apikey=glytoucan_apikey)

        self.output(2, "Worker-%s is ready to take job" % (pid))

        while True:
            task_detail = self.task_queue_get(task_queue, pid, suicide_queue_pair)

            self.output(2, "Worker-%s is computing task: %s" % (pid, task_detail))

            error = []
            calculation_start_time = time.time()


            list_id = task_detail["id"]
            seq = str(task_detail["seq"])
            result = {
                "accession": "",
                "status": "",
            }

            glytoucan_seq_hash, acc = gtc.gethashedseq(seq=seq)

            if not glytoucan_seq_hash:
                # Never registered to GlyTouCan
                hsh = gtc.register(seq)
                result["status"] = "register sent"
                if not hsh:
                    error.append("Your sequence is rejected by GlyTouCan")
            elif not acc:
                # Registered, but no accession yet
                result["status"] = "registered, but no accession yet"
            else:
                result["accession"] = acc
                result["status"] = "accession found"


            calculation_end_time = time.time()
            calculation_time_cost = calculation_end_time - calculation_start_time

            self.output(2, "Worker-%s finished computing job (%s)" % (pid, list_id))

            res = {
                "id": list_id,
                "start time": calculation_start_time,
                "end time": calculation_end_time,
                "runtime": calculation_time_cost,
                "error": error,
                "result": result
            }

            self.output(2, "Job (%s): %s" % (list_id, res))

            result_queue.put(res)




if __name__ == '__main__':
    multiprocessing.freeze_support()

    register_app = Register()
    register_app.find_config("Register.ini")
    register_app.start()










