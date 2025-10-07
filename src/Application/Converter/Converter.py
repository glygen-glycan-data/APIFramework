#!/bin/env python3.12

import os
import sys
import time
import multiprocessing
import traceback

from APIFramework import APIFramework, APIFrameworkWithFrontEnd, queue

import pygly.alignment
from pygly.GlycanResource.GlyTouCan import GlyTouCanNoCache, GlyTouCan

from pygly.GlycanFormatter import IUPACGlycamFormat, GlycoCTFormat, IUPACLinearFormat
from pygly.CompositionFormatter import CompositionFormat
from pygly.GlycanMultiParser import GlycanMultiParser, GlycanParseError

def round2str(n):
    return str(round(n, 2))


class Converter(APIFrameworkWithFrontEnd):

    def form_task(self, p):
        res = {}

        p["seq"] = p["seq"].strip()
        p["format"] = p["format"].strip()
        task_str = p["seq"] +"_"+ p["format"]
        list_id = self.str2hash(task_str)

        res["id"] = list_id
        res["seq"] = p["seq"]
        res["format"] = p["format"]

        return res


    def worker(self, pid, task_queue, result_queue, suicide_queue_pair, params):

        self.output(2, "Worker-%s is starting up" % (pid))


        gmp = GlycanMultiParser()
        gp = GlycoCTFormat()
        cp = CompositionFormat()
        iupac_parser = IUPACLinearFormat()
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

            try:
                query_glycan = gmp.toGlycan(seq)
            except GlycanParseError:
                error.append("Unable to parse your sequence")

            if len(error) == 0:
                try:
                    if request_format == "glycam":
                        if not query_glycan.has_root():
                            error.append("Cannot make Glycam sequence from composition")
                        else:
                            result = glycam_parser.toStr(query_glycan)
                    elif request_format == "iupac":
                        if not query_glycan.has_root():
                            error.append("Cannot make IUPAC sequence from composition")
                        else:
                            result = iupac_parser.toStr(query_glycan)
                    elif request_format == "composition":
                        comp = query_glycan.iupac_composition(floating_substituents=True, 
                                                              aggregate_basecomposition=False)
                        compstr = ""
                        for k,v in sorted(comp.items()):
                            if v > 0 and k != "Count":
                                compstr += "%s(%d)"%(k,v)
                        result = compstr
                    elif request_format == "glycoct":
                        result = gp.toStr(query_glycan)
                    else:
                        error.append("Format %s is not supported" % request_format)
                except:
                    traceback.print_exc()
                    error.append("Unexpected error during conversion")

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






