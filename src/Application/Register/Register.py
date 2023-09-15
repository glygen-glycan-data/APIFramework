
import re
import os
import sys
import time
import hashlib
import multiprocessing
import traceback
from APIFramework import APIFramework, APIFrameworkWithFrontEnd, queue

import pygly.alignment
from pygly.GlycanResource.GlyTouCan import GlyTouCanNoCache, GlyTouCan
from pygly.GlycanFormatter import WURCS20Format, GlycoCTFormat, IUPACLinearFormat, GlycanParseError
from pygly.CompositionFormatter import CompositionFormat


class Register(APIFrameworkWithFrontEnd):

    def form_task(self, p):
        res = {}

        p["seq"] = p["seq"].strip()
        task_str = p["seq"].encode("utf-8") + "_" + str(int(time.time()/600))
        task_id = self.str2hash(task_str)

        res["id"] = task_id
        res["seq"] = p["seq"]

        return res


    def worker(self, pid, task_queue, result_queue, suicide_queue_pair, params):

        self.output(2, "Worker-%s is starting up" % (pid))

        glytoucan_userid = params["userid"].strip()
        glytoucan_apikey = params["apikey"].strip()

        gtc = GlyTouCan(verbose=True, prefetch=False, user=glytoucan_userid, apikey=glytoucan_apikey)
        gp = GlycoCTFormat()
        cp = CompositionFormat()
        ip = IUPACLinearFormat()

        self.output(2, "Worker-%s is ready to take job" % (pid))

        while True:
            task_detail = self.task_queue_get(task_queue, pid, suicide_queue_pair)

            self.output(2, "Worker-%s is computing task: %s" % (pid, task_detail))

            error = []
            calculation_start_time = time.time()

            task_id = task_detail["id"]

            # TODO seq conversions?
            seq = str(task_detail["seq"]).strip()
            result = {
                "status": "",
                "submitted_sequence": seq
            }

            inputerror = False
            if seq.startswith('WURCS'):
                pass
            elif seq.startswith('RES'):
                pass
            else:
                newseq = None
                if not newseq:
                    # see if it parses as a composition
                    try:
                        gly = cp.toGlycan(seq)
                        newseq = cp.toSequence(seq)
                        result["submitted_sequence"] = newseq
                    except GlycanParseError:
                        pass
                if not newseq:
                    # see if it parses as IUPAC
                    try:
                        gly = ip.toGlycan(seq)
                        newseq = gp.toStr(gly)
                        result["submitted_sequence"] = newseq
                    except GlycanParseError:
                        traceback.print_exc()
                        pass
                if newseq:
                    seq = newseq.strip()
                else:
                    inputerror = True

            if not inputerror:

                glytoucan_seq_hash, acc, e = gtc.gethashedseq(seq=seq.strip())
    
                if not glytoucan_seq_hash:
                    # Never submitted to GlyTouCan
                    hsh = gtc.register(seq)
                    if hsh and re.search(r'^[0-9a-f]{64}$',hsh):
                        result["status"] = "Submitted"
                        result["seqhash"] = hsh
		    else:
                        result["status"] = "Error"
                        error.append("Submission failed.")
		        if hsh:
                            error.append(hsh)

                elif not acc:
                    # Submitted, but no accession
                    if e:
                        result["status"] = "Error"
                        result["seqhash"] = glytoucan_seq_hash
                        error.append(e)
		    else:
                        result["status"] = "Processing"
                        result["seqhash"] = glytoucan_seq_hash
        
                else:
                    result["status"] = "Registered"
                    result["seqhash"] = glytoucan_seq_hash
                    result["accession"] = acc
            else:
                result["status"] = "Error"
                error.append("Can't parse supplied composition or IUPAC sequence")

            calculation_end_time = time.time()
            calculation_time_cost = calculation_end_time - calculation_start_time

            self.output(2, "Worker-%s finished computing job (%s)" % (pid, task_id))

            res = {
                "id": task_id,
                "start time": calculation_start_time,
                "end time": calculation_end_time,
                "runtime": calculation_time_cost,
                "error": error,
                "result": result
            }

            self.output(2, "Job (%s): %s" % (task_id, res))

            result_queue.put(res)




if __name__ == '__main__':
    multiprocessing.freeze_support()

    register_app = Register()
    register_app.find_config("Register.ini")
    register_app.start()










