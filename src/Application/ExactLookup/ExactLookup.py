
import sys
import time
import hashlib
import multiprocessing
from APIFramework import APIFramework

import pygly.alignment
from pygly.GlycanFormatter import WURCS20Format, GlycoCTFormat

def round2str(n):
    return str(round(n, 2))


class ExactLookup(APIFramework):

    def form_task(self, p):
        res = {}
        task_str = p["seq"].encode("utf-8")
        list_id = hashlib.sha256(task_str).hexdigest()

        res["id"] = list_id
        res["seq"] = p["seq"]

        return res

    @staticmethod
    def worker(pid, task_queue, result_queue, params):
        print(pid, "Start")

        glycan_file_path = params["glycan_file_path"]

        gp = GlycoCTFormat()
        wp = WURCS20Format()

        gie = pygly.alignment.GlycanEqual()

        glycans = {}
        glycan_by_mass = {}


        for line in open(glycan_file_path):
            acc, s = line.strip().split()
            g = wp.toGlycan(s)

            try:
                mass = round2str(g.underivitized_molecular_weight())
            except:
                mass = None

            if mass not in glycan_by_mass:
                glycan_by_mass[mass] = []

            glycan_by_mass[mass].append(acc)
            glycans[acc] = g


        while True:
            task_detail = task_queue.get(block=True)

            error = []
            calculation_start_time = time.time()


            list_id = task_detail["id"]
            seq = task_detail["seq"]
            result = []

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
                    pass

            else:
                try:
                    query_glycan_mass = round2str(query_glycan.underivitized_molecular_weight())
                except:
                    query_glycan_mass = None

                potential_accs = glycan_by_mass[None]
                if query_glycan_mass in glycan_by_mass:
                    potential_accs = list(set(potential_accs + glycan_by_mass[query_glycan_mass]))

                for acc in potential_accs:
                    glycan = glycans[acc]
                    if gie.eq(query_glycan, glycan):
                        result.append(acc)



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

    exact_lookup_app = ExactLookup()
    exact_lookup_app.parse_config("ExactLookup.ini")
    exact_lookup_app.start()










