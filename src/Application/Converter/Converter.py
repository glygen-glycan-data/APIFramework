
import os
import sys
import time
import multiprocessing
from APIFramework import APIFramework, APIFrameworkWithFrontEnd, queue

import pygly.alignment
from pygly.GlycanResource.GlyTouCan import GlyTouCanNoCache, GlyTouCan
from pygly.GlycanFormatter import WURCS20Format, GlycoCTFormat, IUPACGlycamFormat

def round2str(n):
    return str(round(n, 2))


class Converter(APIFrameworkWithFrontEnd):

    def form_task(self, p):
        res = {}

        p["seq"] = p["seq"].strip()
        p["format"] = p["format"].strip()
        task_str = p["seq"].encode("utf-8") +"_"+ p["format"].encode("utf-8")
        list_id = self.str2hash(task_str)

        res["id"] = list_id
        res["seq"] = p["seq"]
        res["format"] = p["format"]

        return res


    def worker(self, pid, task_queue, result_queue, suicide_queue_pair, params):

        self.output(2, "Worker-%s is starting up" % (pid))


        gp = GlycoCTFormat()
        wp = WURCS20Format()
        glycam_parser = IUPACGlycamFormat()

        self.output(2, "Worker-%s is ready to take job" % (pid))

        while True:
            task_detail = self.task_queue_get(task_queue, pid, suicide_queue_pair)

            self.output(2, "Worker-%s is computing task: %s" % (pid, task_detail))

            error = []
            calculation_start_time = time.time()

            list_id = task_detail["id"]
            seq = str(task_detail["seq"])
            request_format = str(task_detail["format"]).lower()
            result = ""

            query_glycan = None
            try:
                if "RES" in seq:
                    query_glycan = gp.toGlycan(seq)
                elif "WURCS" in seq:
                    query_glycan = wp.toGlycan(seq)
                else:
                    raise RuntimeError
            except:
                error.append("Unable to parse your sequence")


            if len(error) == 0:
                try:
                    if request_format == "iupac":
                        result = glycam_parser.toStr(query_glycan)
                    elif request_format == "glycoct":
                        result = gp.toStr(query_glycan)
                    else:
                        error.append("Format %s is not supported" % request_format)
                except:
                    error.append("Critical error during conversion")

            result = result.strip()

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

    converter_app = Converter()
    converter_app.find_config("Converter.ini")
    converter_app.start()






