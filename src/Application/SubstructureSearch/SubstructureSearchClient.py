
from __future__ import print_function

import sys
import json
from APIFramework import APIUnfinishedError, APIFrameworkClient


class SubstructureSearchClient(APIFrameworkClient):

    def submit(self, seq, red_only=False):
        if red_only == True:
            red_only = "reo"
        else:
            red_only = "anywhere"

        param = {"task": json.dumps({
            "seq": seq,
            "motif_match_position": red_only
        })}
        res1 = self.request("submit", param)

        list_id = res1.json()[0][u"id"]
        return list_id


    def retrieve_once(self, list_id):
        param = {"list_id": json.dumps(list_id)}

        try:
            res2 = self.request("retrieve", param)
            res2json = res2.json()[0]
        except:
            raise RuntimeError

        if not res2json[u"finished"]:
            raise APIUnfinishedError("The task %s is not finished yet" % list_id)

        return res2json




if __name__ == '__main__':
    substructure_search_client = SubstructureSearchClient()
    substructure_search_client.parse_config("SubstructureSearch.ini")

    red_only = False
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        arg = arg.strip()

        if arg.startswith("WURCS") or arg.startswith("RES"):
            seq = arg
        else:
            seq = open(arg).read().strip()

    else:
        sys.exit(1)

    if len(sys.argv) > 2:
        if sys.argv[2].lower() in ["y", "yes", "true", "t"]:
            red_only = True

    try:
        res = substructure_search_client.get(seq, red_only=red_only)
    except APIUnfinishedError:
        print("It is not finished yet, please try again later...")
        sys.exit(1)

    for r in sorted(res[u"result"]):
        print(r)




