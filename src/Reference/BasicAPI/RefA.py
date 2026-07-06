

import time
import hashlib
import multiprocessing
from APIFramework import APIFramework

class ReferenceAPIBasic(APIFramework):
    task_params = dict(num=None)

    @staticmethod
    def worker(pid):
        self.start_worker(pid)
        # any setup tasks

        self.worker_ready()
        while True:
            task_detail = self.get_task()

            result = []

            try:
                n = int(task_detail["num"])
            except (ValueError,TypeError):
                # indicate error and loop for next task
                self.put_error("Bad number")
                continue

            # create result in whatever format makes sense...
            result.append(n*n)
            # send result back
            self.put_result(result)

if __name__ == '__main__':
    multiprocessing.freeze_support()

    fb_api = ReferenceAPIBasic()
    fb_api.parse_config("RefA.ini")
    fb_api.start()










