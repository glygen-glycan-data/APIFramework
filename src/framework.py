
import os
import sys
import copy
import time, datetime
import json
import flask
import atexit
import hashlib
import ConfigParser
import multiprocessing, Queue



class APIErrorBase(RuntimeError):

    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg


class APIParameterError(APIErrorBase):
    pass



class APIFrameWork:

    def __init__(self):

        self._verboselevel = 100

        self._host = "localhost"
        self._port = 10980

        self._workernum = 2

        self._app_name = "testing"
        self._flask_app = flask.Flask(self._app_name)

        self._worker_para = {}

        self.taskqueue = multiprocessing.Queue()
        self.resultqueue = multiprocessing.Queue()

        self.result_cache = {}


    def host(self):
        return self._host

    def sethost(self, h):
        self._host = h

    def port(self):
        return self._port

    def setport(self, p):
        self._port = p

    def worknum(self):
        return self._workernum

    def setworknum(self, w):
        self._workernum = w

    def verboselevel(self):
        return self._verboselevel

    def setverboselevel(self, v):
        assert isinstance(v, int)
        assert v >= 0 and v <= 100
        self._verboselevel = v

    def setappname(self, an):
        self._app_name = an
        self._flask_app = flask.Flask(self._app_name)

    def output(self, lvl, msg):
        if lvl <= self.verboselevel():
            print >> sys.stderr, msg

    def autoconfigparsing(self, configfilename):
        currentdir = os.path.dirname(sys.argv[0])
        currentdirabs = os.path.abspath(currentdir)

        configpath = os.path.join(currentdirabs, configfilename)

        config = ConfigParser.SafeConfigParser()
        config.readfp(open(configpath))

        res = {}
        for each_section in config.sections():
            res[each_section] = {}
            for (each_key, each_val) in config.items(each_section):
                res[each_section][each_key] = each_val


        if "basic" in res:

            if "host" in res["basic"]:
                self.sethost(res["basic"]["host"])

            if "port" in res["basic"]:
                self.setport(int(res["basic"]["port"]))

            if "cpu_core" in res["basic"]:
                self.setworknum(int(res["basic"]["cpu_core"]))

            if "app_name" in res["basic"]:
                self.setappname(res["basic"]["app_name"])

                if res["basic"]["app_name"] in res:
                    self._worker_para = res[res["basic"]["app_name"]]


    # Daemon processor init function
    def workerfunction(self, PPID):
        """
        para = self._worker_para
        self.output(1, "Computing Processor%s is starting" % PPID)
        time.sleep(10)
        """
        raise NotImplemented



    # FLASK related functions start here
    def flaskfunction(self):

        # self._flask_app.config["DEBUG"] = True
        @self._flask_app.route('/', methods=['GET', 'POST'])
        def home():
            return self.home()

        @self._flask_app.route('/date', methods=['GET', 'POST'])
        def getdate():
            # Used for checking whether FLASK is alive
            return flask.jsonify(datetime.datetime.now())

        @self._flask_app.route('/queue', methods=['GET', 'POST'])
        def getqueuelength():
            self.update_results(getall=True)
            n = len(filter(lambda x: not x["finished"], self.result_cache.values()))
            return flask.jsonify(n)

        @self._flask_app.route('/submit', methods=['GET', 'POST'])
        def submit():
            if flask.request.method in ['GET', 'POST']:
                p = self.api_para()
            else:
                return flask.jsonify("METHOD %s is not suppoted" % flask.request.method)

            if "tasks" not in p:
                return flask.jsonify("Please submit with actual tasks")

            # Suppose to be a list
            raw_tasks = json.loads(p["tasks"])
            res = []
            for raw_task in raw_tasks:
                task_detail = self.formtask(raw_task)
                if "id" not in task_detail:
                    raise APIParameterError("No id provided for your job(%s), probably check the formtask method" % task_detail)

                res.append(copy.deepcopy(task_detail))
                list_id = task_detail["id"]
                status = {
                    "id": list_id,
                    "submission_detail": task_detail,
                    "finished": False,
                    "result": {}
                }

                if list_id in self.result_cache:
                    pass
                else:
                    self.taskqueue.put(task_detail)
                    self.result_cache[list_id] = status
                self.output(1, "Job received by API: %s" % (task_detail))

            return flask.jsonify(res)

        @self._flask_app.route('/retrieve', methods=['GET', 'POST'])
        def retrieve():
            if flask.request.method in ['GET', 'POST']:
                p = self.api_para()
            else:
                return flask.jsonify("METHOD %s is not suppoted" % flask.request.method)

            if "list_ids" not in p:
                return flask.jsonify("Please provide with list_id(s)")

            self.update_results(getall=True)

            # Suppose to be a list
            list_ids = json.loads(p["list_ids"])
            res = []
            for list_id in list_ids:
                thing = {"Error": "list_id (%s) not found" % list_id}
                if list_id in self.result_cache:
                    thing = self.result_cache[list_id]
                res.append(thing)

            return flask.jsonify(res)

        flask_API_host = self.host()
        flask_API_port = self.port()
        self.output(1, "Running FLASK at http://%s:%s" % (flask_API_host, flask_API_port))
        self._flask_app.run(host=flask_API_host, port=flask_API_port, threaded=False)

    def update_results(self, getall=False):

        i = 0
        while True:

            if not getall and i >= 5:
                break

            i += 1

            try:
                res = self.resultqueue.get_nowait()
                self.result_cache[res["id"]]['finished'] = True
                self.result_cache[res["id"]]["result"] = res
            except Queue.Empty:
                break
            except KeyError:
                self.output(1, "Job ID %s is not present" % res["id"])


    def home(self):
        return flask.jsonify("Hello!")

    @staticmethod
    def api_para():
        if flask.request.method == "GET":
            return flask.request.args
        elif flask.request.method == "POST":
            return flask.request.form
        else:
            raise APIErrorBase

    def formtask(self, p):
        """
        task = {
            "id": list_id,
            "something": something...
        }
        return task
        """
        raise NotImplemented


    def declareprocess(self):
        self._front_end_process = multiprocessing.Process(target=self.flaskfunction)

        self._deamon_process_pool = []
        for i in range(self._workernum):
            p = multiprocessing.Process(target=self.workerfunction, args=(i, ))
            self._deamon_process_pool.append(p)


    def start(self):
        self.declareprocess()

        self._front_end_process.start()
        for p in self._deamon_process_pool:
            p.start()
        self.cleanup()

    def terminateall(self):
        for p in self._deamon_process_pool:
            p.terminate()
        self._front_end_process.terminate()

    def cleanup(self):
        atexit.register(self.terminateall)
        while True:
            goodbye = not self._front_end_process.is_alive()
            for p in self._deamon_process_pool:
                if not p.is_alive():
                    goodbye = True

            if goodbye:
                self.terminateall()
                break
            time.sleep(1)



if __name__ == "__main__":
    multiprocessing.freeze_support()








