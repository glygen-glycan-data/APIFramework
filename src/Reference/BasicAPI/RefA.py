

import time
import hashlib
import multiprocessing
from APIFramework import APIFramework

class ReferenceAPIBasic(APIFramework):

    def form_task(self, p):
        res = {}
        task_str = p["num"].encode("utf-8")
        list_id = hashlib.sha256(task_str).hexdigest()

        res["id"] = list_id
        res["num"] = p["num"]

        return res

    @staticmethod
    def worker(pid, task_queue, result_queue, params):
        print(pid, "Start")

        while True:
            task_detail = task_queue.get(block=True)

            error = []
            calculation_start_time = time.time()


            list_id = task_detail["id"]
            result = []

            n = int(task_detail["num"])
            result.append(n*n)
            time.sleep(2.3)



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




if __name__ == '__main__':
    multiprocessing.freeze_support()

    fb_api = ReferenceAPIBasic()
    fb_api.parse_config("RefA.ini")
    fb_api.start()










