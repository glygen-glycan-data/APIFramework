
from __future__ import print_function

import sys
import json
from APIFramework import APIUnfinishedError, APIFrameworkClient


class ExactLookupClient(APIFrameworkClient):

    def submit(self, seq):

        param = {"task": json.dumps({"seq": seq})}
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
    exact_lookup_client = ExactLookupClient()
    exact_lookup_client.parse_config("ExactLookup.ini")

    if len(sys.argv) > 1:
        arg = sys.argv[1]
        arg = arg.strip()

        if arg.startswith("WURCS") or arg.startswith("RES"):
            seq = arg
        else:
            seq = open(arg).read().strip()
    else:
        print("Please provide a sequence")
        sys.exit(1)


    try:
        res = exact_lookup_client.get(seq)
    except APIUnfinishedError:
        print("It is not finished yet, please try again later...")
        sys.exit(1)

    for r in sorted(res[u"result"]):
        print(r)




