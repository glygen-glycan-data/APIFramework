
from __future__ import print_function

import os
import sys
import copy
import time
import json
import flask
import werkzeug
import atexit
import hashlib
import random
import string
import multiprocessing

try:
    # Python3 import
    import queue
except ImportError:
    # Python2 import
    import Queue as queue

try:
    import configparser
except ImportError:
    import ConfigParser as configparser



class APIErrorBase(RuntimeError):

    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg


class APIParameterError(APIErrorBase):
    pass


class APIUnfinishedError(APIErrorBase):
    pass


class APIFramework(object):

    def __init__(self):

        self._verbose_level = 100

        self._host = "localhost"
        self._port = 10980

        self._worker_num = 1
        self._clean_start = True
        self._file_based_job = False

        self._app_name = "testing"
        self._flask_app = flask.Flask(self._app_name)

        self._input_file_folder  = self.abspath("input")
        # self._output_file_folder = self.abspath("output")

        self._allowed_file_ext = ["txt", "doc", "docx", "pdf", "jpg", "png"]
        self._allow_cors = False

        self._worker_para = {}

        self.result_cache = {}
        self.task_queue   = multiprocessing.Queue()
        self.result_queue = multiprocessing.Queue()

        self._template_folder = None
        self._home_html = None
        self._file_upload_finished_html = None

        self._status_saving_location = None


    # Proper APIs for changing config
    def host(self):
        return self._host

    def set_host(self, h):
        self._host = h

    def port(self):
        return self._port

    def set_port(self, p):
        if isinstance(p, int):
            self._port = p
        else:
            raise APIParameterError("Port number requires integer, %s is not acceptable")

    def worker_num(self):
        return self._worker_num

    def set_worker_num(self, w):
        self._worker_num = w

    def verbose_level(self):
        return self._verbose_level

    def set_verbose_level(self, v):
        assert isinstance(v, int)
        assert 0 <= v <= 100
        self._verbose_level = v

    def set_app_name(self, an):
        self._app_name = an
        if self._template_folder is None:
            self._flask_app = flask.Flask(self._app_name)
        else:
            self._flask_app = flask.Flask(self._app_name, template_folder=self.abspath(self._template_folder))

    def input_file_folder(self):
        return self._input_file_folder

    def set_input_file_folder(self, fp):
        self._input_file_folder = self.abspath(fp)

    # set_status_saving_location

    # def output_file_folder(self):
    #     return self._output_file_folder

    # def set_output_file_folder(self, fp):
    #     self._output_file_folder = self.abspath(fp)

    def status_saving_location(self):
        return self._status_saving_location

    def set_status_saving_location(self, fp):
        self._status_saving_location = self.abspath(fp)

    def allowed_file_ext(self):
        return self._allowed_file_ext

    def clear_allowed_file_ext(self):
        self._allowed_file_ext = []

    def add_allowed_file_ext(self, ext):
        ext = ext.lower()
        if ext not in self._allowed_file_ext:
            self._allowed_file_ext.append(ext)

    def rm_allowed_file_ext(self, ext):
        ext = ext.lower()
        if ext in self._allowed_file_ext:
            self._allowed_file_ext.remove(ext)

    def output(self, lvl, msg):
        if lvl <= self.verbose_level():
            print(msg, file=sys.stderr)


    def abspath(self, fp):
        base = os.path.dirname(os.path.abspath(sys.argv[0]))
        res = os.path.join(base, fp)
        return res

    def bool(self, s):
        if s.lower() in ["y","yes","true",]:
            return True
        else:
            return False

    def inside_docker(self):
        inside_docker = False
        try:
            inside_docker = "docker" in open("/proc/self/cgroup").read()
        except:
            pass
        return inside_docker


    def find_config(self, config_file_name):

        inside_docker = self.inside_docker()

        config_current_path = self.abspath(config_file_name)
        config_docker_path  = "/root/appconfig" + config_file_name

        if inside_docker:
            if os.path.exists(config_docker_path):
                self.parse_config(config_docker_path)
            else:
                self.parse_config(config_current_path)

            self.environmental_variable()
        else:
            self.parse_config(config_current_path)

    def parse_config(self, config_file_name):

        config = configparser.ConfigParser()
        config.read_file(open(config_file_name))

        res = {}
        for each_section in config.sections():
            res[each_section] = {}
            for (each_key, each_val) in config.items(each_section):
                if each_val != "":
                    res[each_section][each_key] = each_val


        if "basic" in res:

            #for k,v in res["basic"].items():
            #    print("%s: |%s|" % (k,v))

            if "host" in res["basic"]:
                self.set_host(res["basic"]["host"])

            if "port" in res["basic"]:
                self.set_port(int(res["basic"]["port"]))

            if "cpu_core" in res["basic"]:
                self.set_worker_num(int(res["basic"]["cpu_core"]))

            if "clean_start" in res["basic"]:
                self._clean_start = self.bool(res["basic"]["clean_start"])

            if "file_based_job" in res["basic"]:
                self._file_based_job = self.bool(res["basic"]["file_based_job"])

            if "input_file_folder" in res["basic"]:
                self.set_input_file_folder(res["basic"]["input_file_folder"])

            # if "output_file_folder" in res["basic"]:
            #     self.set_output_file_folder(res["basic"]["output_file_folder"])

            if "status_saving_location" in res["basic"]:
                self.set_status_saving_location(res["basic"]["status_saving_location"])

            if "template_folder" in res["basic"]:
                self._template_folder = res["basic"]["template_folder"]

            if "home_page" in res["basic"]:
                self._home_html = res["basic"]["home_page"]

            if "file_upload_finished_page" in res["basic"]:
                self._file_upload_finished_html = res["basic"]["file_upload_finished_page"]

            if "allowed_file_ext" in res["basic"]:
                allowed_file_ext = res["basic"]["allowed_file_ext"].split(",")
                self.clear_allowed_file_ext()
                for ext in allowed_file_ext:
                    ext = ext.strip()
                    self.add_allowed_file_ext(ext)

            if "allow_cors" in res["basic"]:
                self._allow_cors = self.bool(res["basic"]["allow_cors"])


            if "app_name" in res["basic"]:
                self.set_app_name(res["basic"]["app_name"])

                if res["basic"]["app_name"] in res:
                    self._worker_para = res[res["basic"]["app_name"]]


            #if "" in res["docker"]:
            #    self._xxxxx = res["docker"][""]

    def environmental_variable(self):

        if "WEBSERVICE_BASIC_HOST" in os.environ:
            self.set_host(os.environ["WEBSERVICE_BASIC_HOST"])

        if "WEBSERVICE_BASIC_PORT" in os.environ:
            self.set_port(int(os.environ["WEBSERVICE_BASIC_PORT"]))

        if "WEBSERVICE_BASIC_CPU_CORE" in os.environ:
            self.set_worker_num(int(os.environ["WEBSERVICE_BASIC_CPU_CORE"]))

        for k, v in os.environ.items():
            if k.startswith("WEBSERVICE_APP_"):
                newk = k[15:].lower()

                self._worker_para[newk] = v


        return


    # Worker function
    @staticmethod
    def worker(pid, task_queue, result_queue, params):
        # Params are key value pairs from configuration file, section app_name
        raise NotImplemented

    @staticmethod
    def unavailable_status(name, host, port):
        app = flask.Flask(name)

        @app.route("/")
        def home():
            return "Service temporarily unavailable, please come back in 10 minutes", 503

        @app.route("/status")
        def somefunction():
            return flask.jsonify(False)

        app.run(host, port)

    # FLASK related functions starts here

    # FLASK handlers, need to be overwrite for your own app
    def home(self, **kwargs):
        if self._home_html is None:
            return flask.jsonify("Hello from %s:%s" % (self.host(), self.port()))
        else:
            return flask.render_template(self._home_html, **kwargs)

    def file_upload_finished_page(self, **kwargs):

        if self._file_upload_finished_html is None:
            return flask.jsonify("Not Implemented")
        else:
            return flask.render_template(self._file_upload_finished_html, **kwargs)

    def get_unfinished_job_count(self):
        self.update_results(getall=True)
        n = len(list(filter(lambda x: not x["finished"], self.result_cache.values())))

        response = flask.jsonify(n)
        if self._allow_cors:
            response.headers.add("Access-Control-Allow-Origin", "*")
        return response

    @staticmethod
    def random_str():
        return ''.join(random.choice(string.ascii_lowercase + string.digits) for i in range(20))

    def submit(self):
        if flask.request.method in ['GET', 'POST']:
            p = self.api_para()
        else:
            response = flask.jsonify("METHOD %s is not suppoted" % flask.request.method)
            if self._allow_cors:
                response.headers.add("Access-Control-Allow-Origin", "*")

            return response

        if "tasks" not in p and "task" not in p and "q" not in p:
            response = flask.jsonify("Please submit with actual tasks")

            if self._allow_cors:
                response.headers.add("Access-Control-Allow-Origin", "*")

            return response

        if "tasks" in p:
            raw_tasks = json.loads(p["tasks"])
        elif "task" in p:
            raw_tasks = [json.loads(p["task"])]
        elif "q" in p:
            raw_tasks = json.loads(p["q"])

        res = []
        userid = self.random_str()
        for raw_task in raw_tasks:
            task_detail = self.form_task(raw_task)

            if "id" not in task_detail:
                raise APIParameterError(
                    "No id provided for your job(%s), probably check the form_task method"
                    % task_detail)

            res.append(copy.deepcopy(task_detail))
            list_id = task_detail["id"]
            status = {
                "id": list_id,
                "initial_user_id": userid,
                "submission_original": raw_task,
                "submission_detail": task_detail,
                "finished": False,
                "stat": {},
                "result": {}
            }

            if list_id in self.result_cache:
                pass
            else:
                self.task_queue.put(task_detail)
                self.result_cache[list_id] = status
            self.output(1, "Job received by API: %s" % (task_detail))

        for r in res:
            r["id"] = r["id"] + userid

        response = flask.jsonify(res)
        if self._allow_cors:
            response.headers.add("Access-Control-Allow-Origin", "*")

        return response


    def retrieve(self):
        if flask.request.method in ['GET', 'POST']:
            p = self.api_para()
        else:
            response = flask.jsonify("METHOD %s is not suppoted" % flask.request.method)
            if self._allow_cors:
                response.headers.add("Access-Control-Allow-Origin", "*")

            return response

        if "list_ids" not in p and "list_id" not in p and "q" not in p:
            return flask.jsonify("Please provide with list_id(s)")

        self.update_results(getall=True)

        if "list_ids" in p:
            list_ids = json.loads(p["list_ids"])
        elif "list_id" in p:
            list_ids = [str(p["list_id"])]
        elif "q" in p:
            list_ids = json.loads(p["q"])

        res = []
        for tmp in list_ids:
            # Assume MD5
            list_id = tmp[:32]
            user_id = tmp[32:]

            if list_id in self.result_cache:
                r = copy.deepcopy(self.result_cache[list_id])
            else:
                res.append({"Error": "list_id (%s) not found" % list_id})
                continue

            cached = True
            if r["initial_user_id"] == user_id:
                cached = False
            r["stat"]["cached"] = cached

            r["task"] = r["submission_detail"]

            del r["submission_original"]
            del r["submission_detail"]
            del r["initial_user_id"]

            r["id"] = tmp
            r["task"]["id"] = tmp

            try:
                del r["stat"]["start time"]
                del r["stat"]["end time"]
            except:
                pass

            res.append(r)

        response = flask.jsonify(res)
        if self._allow_cors:
            response.headers.add("Access-Control-Allow-Origin", "*")
        return response


    def upload_file(self):
        if flask.request.method == 'POST':

            if 'file' not in flask.request.files:
                return flask.abort(400)

            file = flask.request.files['file']
            filename = werkzeug.utils.secure_filename(file.filename)

            if file.filename == '':
                response = flask.jsonify('No selected file')
                if self._allow_cors:
                    response.headers.add("Access-Control-Allow-Origin", "*")

                return response

            task_detail = self.form_task({"original_file_name": file.filename})
            list_id = task_detail["id"]

            if file and self.allow_file_ext(file.filename):
                file.save(os.path.join(self.input_file_folder(), list_id))
            else:
                response = flask.jsonify('File extension is not supported')
                if self._allow_cors:
                    response.headers.add("Access-Control-Allow-Origin", "*")

                return response

            status = {
                "id": list_id,
                "submission_original": {},
                "submission_detail": task_detail,
                "finished": False,
                "stat": {},
                "result": {}
            }

            if list_id in self.result_cache:
                pass
            else:
                self.task_queue.put(task_detail)
                self.result_cache[list_id] = status
            self.output(1, "Job received by API: %s" % (task_detail))

        return self.file_upload_finished_page(list_id=list_id)


    def download_file(self):
        if flask.request.method in ['GET', 'POST']:
            p = self.api_para()
        else:
            response = flask.jsonify("METHOD %s is not suppoted" % flask.request.method)
            if self._allow_cors:
                response.headers.add("Access-Control-Allow-Origin", "*")

            return response


        if "list_id" not in p:
            response = flask.jsonify("Please provide with list_id(s)")
            if self._allow_cors:
                response.headers.add("Access-Control-Allow-Origin", "*")

            return response

        list_id = p["list_id"]

        if not self.result_cache[list_id]["finished"]:
            response = flask.jsonify("The computation haven't finished yet")
            if self._allow_cors:
                response.headers.add("Access-Control-Allow-Origin", "*")

            return response

        target_file_path = self.result_cache[list_id]["result"]["output_file_abs_path"]

        download_file_name = target_file_path
        if "rename" in self.result_cache[list_id]["result"]:
            download_file_name = self.result_cache[list_id]["result"]["rename"]

        download_option = {}
        if "flask_download_option" in self.result_cache[list_id]["result"]:
            download_option = self.result_cache[list_id]["result"]["flask_download_option"]

        try:
            return flask.send_file(target_file_path,
                                   attachment_filename=download_file_name,
                                   **download_option)
        except:
            flask.abort(404)


    # FLASK helper functions
    def form_task(self, p):
        #
        """
        task = {
            "id": list_id,
            "key": value...
        }
        return task
        """
        raise NotImplemented

    @staticmethod
    def api_para():
        if flask.request.method == "GET":
            return flask.request.args
        elif flask.request.method == "POST":
            return flask.request.form
        else:
            raise APIErrorBase

    def update_results(self, getall=False):

        i = 0
        while True:

            if not getall and i >= 5:
                break

            i += 1

            try:
                res = self.result_queue.get_nowait()

                self.result_cache[res["id"]]["stat"] = {
                    "start time": res["start time"],
                    "end time": res["end time"],
                    "runtime": res["runtime"]
                }

                self.result_cache[res["id"]]["error"] = res["error"]
                self.result_cache[res["id"]]["result"] = res["result"]

                self.result_cache[res["id"]]['finished'] = True
            except queue.Empty:
                break
            except KeyError:
                self.output(1, "Job ID %s is not present" % res["id"])


    def allow_file_ext(self, filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in self.allowed_file_ext()

    def status(self):
        response = flask.jsonify(True)
        if self._allow_cors:
            response.headers.add("Access-Control-Allow-Origin", "*")

        return response


    # Load route and handler to flask app
    def load_route(self):

        self._flask_app.add_url_rule("/", "home", self.home, methods=["GET", "POST"])
        self._flask_app.add_url_rule("/status", "status", self.status, methods=["GET", "POST"])
        self._flask_app.add_url_rule("/retrieve", "retrieve", self.retrieve, methods=["GET", "POST"])
        if self._file_based_job:
            self._flask_app.add_url_rule("/file_upload", "upload_file", self.upload_file, methods=["GET", "POST"])
            self._flask_app.add_url_rule("/file_download", "download_file", self.download_file, methods=["GET", "POST"])
        else:
            self._flask_app.add_url_rule("/submit", "submit", self.submit, methods=["GET", "POST"])



    def manipulate_dirs(self):
        if self._file_based_job:
            if not os.path.exists(self.input_file_folder()):
                os.makedirs(self.input_file_folder())
            """
            if not os.path.exists(self.output_file_folder()):
                os.makedirs(self.output_file_folder())
    
            if self._clean_start:
                for folder in [self.input_file_folder(), self.output_file_folder()]:
                    for fn in os.listdir(folder):
                        # Clean up the input and output folder
                        fp = os.path.join(folder, fn)
                        os.remove(fp)
            """
        return


    def pre_start(self, worker_para):
        # Function for downloading necessary data and others.
        # Execute before everything else starts
        return None


    def start(self):

        # Temporary webservice...
        webservice_process_tmp = multiprocessing.Process(target=self.unavailable_status, args=(self._app_name, self.host(), self.port() ))
        webservice_process_tmp.start()

        self.pre_start(self._worker_para)
        self.load_route()
        self.manipulate_dirs()

        if not self._clean_start and self.status_saving_location() != None:
            if os.path.exists(self.status_saving_location()):
                self.result_cache = json.load(open(self.status_saving_location()))

        self._deamon_process_pool = []
        for i in range(self._worker_num):
            p = multiprocessing.Process(target=self.worker, args=(i, self.task_queue, self.result_queue, self._worker_para ))
            self._deamon_process_pool.append(p)

        for p in self._deamon_process_pool:
            p.start()

        self.cleanup()

        webservice_process_tmp.terminate()
        self._flask_app.run(self.host(), self.port(), False)

    def cleanup(self):
        atexit.register(self.terminate_all)
        atexit.register(self.dump_status)


    def terminate_all(self):
        for p in self._deamon_process_pool:
            p.terminate()

    def dump_status(self):
        if self.status_saving_location() != None:
            useful_result = {}
            for list_id, task in self.result_cache.items():
                if task["finished"]:
                    useful_result[list_id] = task

            json.dump(
                useful_result,
                open(self.status_saving_location(), "w"),
                indent=2
            )



if __name__ == '__main__':
    multiprocessing.freeze_support()



