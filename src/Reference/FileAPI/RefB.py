
from APIFramework import APIFrameWork

import os
import sys
import time
import random
import hashlib
import multiprocessing


class ReferenceAPIParaBased(APIFrameWork):
    pass


import subprocess
class ReferenceAPIFileBased(APIFrameWork):

    def form_task(self, p):
        res = {}

        # Prevent name collision
        task_str = p["original_file_name"] + str(random.randint(10000, 99999))
        task_str = task_str.encode("utf-8")
        list_id = hashlib.sha256(task_str).hexdigest()

        res["id"] = list_id
        res["original_file_name"] = p["original_file_name"]

        return res

    @staticmethod
    def worker(pid, task_queue, result_queue, params):
        print(pid, "Start")

        while True:
            task_detail = task_queue.get(block=True)

            error = []
            calculation_start_time = time.time()

            original_file_name = task_detail["original_file_name"]


            list_id = task_detail["id"]
            # the input_file is just file path.
            input_file = os.path.join("input" , task_detail["id"])
            output_file_abs_path = os.path.abspath(os.path.join("./output", list_id + ".out"))

            subprocess.call(["cp", input_file, output_file_abs_path])

            time.sleep(0.5)



            calculation_end_time = time.time()
            calculation_time_cost = calculation_end_time - calculation_start_time

            # option = {"as_attachment": True}
            option = {"as_attachment": False, "mimetype": 'application/pdf'}

            res = {
                "id": list_id,
                "start time": calculation_start_time,
                "end time": calculation_end_time,
                "runtime": calculation_time_cost,
                "error": error,

                "rename": "your_result.pdf",
                "output_file_abs_path": output_file_abs_path,
                "flask_download_option": option
            }
            result_queue.put(res)




if __name__ == '__main__':
    multiprocessing.freeze_support()

    fb_api = ReferenceAPIFileBased()
    fb_api.parse_config("RefB.ini")
    fb_api.start()










