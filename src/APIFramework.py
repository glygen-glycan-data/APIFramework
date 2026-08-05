
from __future__ import print_function

import os
import re
import sys
import copy
import time
import json
import math
import flask
import werkzeug
import atexit
import hashlib
import urllib.request
import random
import string
import datetime
import glob
import multiprocessing
import multiprocessing.queues


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



# For MacOS/Unix only...
class SharedCounter(object):

    def __init__(self, n=0):
        self.count = multiprocessing.Value('i', n)

    def increment(self, n=1):
        with self.count.get_lock():
            self.count.value += n

    @property
    def value(self):
        return self.count.value

class MacOSQueue(multiprocessing.queues.Queue):

    def __init__(self, *args, **kwargs):
        super(MacOSQueue, self).__init__(*args, **kwargs)
        self.size = SharedCounter(0)

    def put(self, *args, **kwargs):
        super(MacOSQueue, self).put(*args, **kwargs)
        self.size.increment(1)

    def get(self, *args, **kwargs):
        res = super(MacOSQueue, self).get(*args, **kwargs)
        self.size.increment(-1)
        return res

    def qsize(self):
        return self.size.value

    def empty(self):
        return not self.qsize()

    def clear(self):
        while not self.empty():
            self.get()

# Hmmm not the best implementation..
try:
    q = multiprocessing.Queue()
    q.qsize()
except NotImplementedError:
    multiprocessing.Queue = MacOSQueue


class APIFramework(object):

    def __init__(self):

        self._verbose_level = 100

        self._host = "0.0.0.0"
        self._port = None
        self._debug = False

        self._max_worker_num = 1
        self._min_worker_num = 1
        self._file_based_job = False

        self._app_name = "APIFramework"
        # self._flask_app = flask.Flask(self._app_name)

        self._input_file_folder  = self.autopath("input")
        # self._output_file_folder = self.abspath("output")

        self._allowed_file_ext = ["txt", "doc", "docx", "pdf", "jpg", "png"]
        self._allow_cors = True

        self._worker_para = {}

        self.result_cache = {} # only updated in flask process
        self.task_queue   = multiprocessing.Queue()
        self.result_queue = multiprocessing.Queue()
        self.request_suicide_queue = multiprocessing.Queue()
        self.approve_suicide_queue = multiprocessing.Queue()

        self._static_folder = 'static'
        self._static_url = '/static'

        self._template_folder = "htmls"
        self._home_html = "index.html"
        self._file_upload_finished_html = None

        self._worker_started = False
        self._last_worker_process_id = 0

        self._google_analytics_tag_id = ""

        self._glymage_base_url = "https://glymage.glyomics.org"
        self._glymage_dev_email = ""
        self._frontend_dev_email = ""
        self._taskidlength = 11
        self._useridlength = 5

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

    def debug(self):
        return self._debug

    def set_debug(self, h):
        self._debug = h

    def max_worker_num(self):
        return self._max_worker_num

    def set_max_worker_num(self, w):
        self._max_worker_num = w

    def min_worker_num(self):
        return self._min_worker_num

    def set_min_worker_num(self, w):
        self._min_worker_num = w

    def verbose_level(self):
        return self._verbose_level

    def set_verbose_level(self, v):
        assert isinstance(v, int)
        assert 0 <= v <= 100
        self._verbose_level = v

    def set_app_name(self, an):
        self._app_name = an
        self.set_frontend_dev_email(self._app_name+"FrontEnd@glyomics.org")

    def google_analytics_tag_id(self):
        return self._google_analytics_tag_id

    def glymage_base_url(self):
        return self._glymage_base_url
    
    def set_glymage_dev_email(self, email):
        self._glymage_dev_email = email

    def set_frontend_dev_email(self, email):
        self._frontend_dev_email = email

    def glymage_dev_email(self):
        return self._glymage_dev_email
    
    def frontend_dev_email(self):
        return self._frontend_dev_email

    def set_google_analytics_tag_id(self, tag):
        assert type(tag) == str
        self._google_analytics_tag_id = tag

    def set_glymage_base_url(self, url):
        assert type(url) == str
        if url.endswith('/'):
            url = url.strip('/')
        self._glymage_base_url = url

    def input_file_folder(self):
        return self._input_file_folder

    def set_input_file_folder(self, fp):
        self._input_file_folder = self.autopath(fp)

    # set_status_saving_location

    # def output_file_folder(self):
    #     return self._output_file_folder

    # def set_output_file_folder(self, fp):
    #     self._output_file_folder = self.abspath(fp)

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
            t = datetime.datetime.now()
            print("[%s %s %s] %s" % (t.strftime("%x"), t.strftime("%X"), lvl, msg), file=sys.stderr)


    def abspath(self, fp):
        # Getting things from current folder
        base = os.path.dirname(os.path.abspath(sys.argv[0]))
        res = os.path.join(base, fp)
        return res

    def autopath(self, fp, newfile=False):
        res = self.abspath(fp)
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
        config_docker_path  = "/data/" + config_file_name

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
        self.output(1, "Reading config: "+config_file_name)
        if hasattr(config,"read_file"):
            config.read_file(open(config_file_name))
        else:
            config.readfp(open(config_file_name))
        
        assert config_file_name.endswith('.ini')
        base = config_file_name.rsplit('.',1)[0]
        for fn in glob.glob(os.path.split(base)[0]+"/*-local.ini"):
            if fn != config_file_name:
                self.output(1, "Reading config: "+fn)
                config.read_file(open(fn))
        
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

            if "debug" in res["basic"]:
                self.set_debug(res["basic"]["debug"])

            if "max_cpu_core" in res["basic"]:
                self.set_max_worker_num(int(res["basic"]["max_cpu_core"]))

            if "min_cpu_core" in res["basic"]:
                self.set_min_worker_num(int(res["basic"]["min_cpu_core"]))

            if "file_based_job" in res["basic"]:
                self._file_based_job = self.bool(res["basic"]["file_based_job"])

            if "input_file_folder" in res["basic"]:
                self.set_input_file_folder(res["basic"]["input_file_folder"])

            # if "output_file_folder" in res["basic"]:
            #     self.set_output_file_folder(res["basic"]["output_file_folder"])

            if "template_folder" in res["basic"]:
                self._template_folder = res["basic"]["template_folder"]

            if "static_folder" in res["basic"]:
                self._static_folder = res["basic"]["static_folder"]

            if "static_url" in res["basic"]:
                self._static_url = res["basic"]["static_url"]

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

            if "google_analytics_tag_id" in res["basic"]:
                self.set_google_analytics_tag_id(res["basic"]["google_analytics_tag_id"])

            if "glymage_base_url" in res["basic"]:
                self.set_glymage_base_url(res["basic"]["glymage_base_url"])

            if "app_name" in res["basic"]:
                self.set_app_name(res["basic"]["app_name"])

                if res["basic"]["app_name"] in res:
                    self._worker_para = res[res["basic"]["app_name"]]

            if "glymage_dev_email" in res["basic"]:
                self.set_glymage_dev_email(res["basic"]["glymage_dev_email"])

            if "frontend_dev_email" in res["basic"]:
                self.set_frontend_dev_email(res["basic"]["frontend_dev_email"])

            #if "" in res["docker"]:
            #    self._xxxxx = res["docker"][""]

    def environmental_variable(self):

        if "WEBSERVICE_BASIC_HOST" in os.environ:
            self.set_host(os.environ["WEBSERVICE_BASIC_HOST"])

        if "WEBSERVICE_BASIC_PORT" in os.environ:
            self.set_port(int(os.environ["WEBSERVICE_BASIC_PORT"]))

        if "WEBSERVICE_BASIC_DEBUG" in os.environ:
            self.set_debug(int(os.environ["WEBSERVICE_BASIC_DEBUG"]))

        if "WEBSERVICE_BASIC_CPU_CORE" in os.environ:
            self.output(0, "Environment variable (WEBSERVICE_BASIC_CPU_CORE) is deprecated!")
            self.set_max_worker_num(int(os.environ["WEBSERVICE_BASIC_CPU_CORE"]))

        if "WEBSERVICE_BASIC_MAX_CPU_CORE" in os.environ:
            self.set_max_worker_num(int(os.environ["WEBSERVICE_BASIC_MAX_CPU_CORE"]))

        if "WEBSERVICE_BASIC_MIN_CPU_CORE" in os.environ:
            self.set_min_worker_num(int(os.environ["WEBSERVICE_BASIC_MIN_CPU_CORE"]))

        if "WEBSERVICE_BASIC_GOOGLE_ANALYTICS_TAG_ID" in os.environ:
            self.set_google_analytics_tag_id(os.environ["WEBSERVICE_BASIC_GOOGLE_ANALYTICS_TAG_ID"])

        if "WEBSERVICE_BASIC_GLYMAGE_BASE_URL" in os.environ:
            self.set_glymage_base_url(os.environ["WEBSERVICE_BASIC_GLYMAGE_BASE_URL"])

        if "WEBSERVICE_BASIC_GLYMAGE_DEV_EMAIL" in os.environ:
            self.set_glymage_dev_email(os.environ["WEBSERVICE_BASIC_GLYMAGE_DEV_EMAIL"])

        if "WEBSERVICE_BASIC_FRONTEND_DEV_EMAIL" in os.environ:
            self.set_frontend_dev_email(os.environ["WEBSERVICE_BASIC_FRONTEND_DEV_EMAIL"])

        for k, v in os.environ.items():
            if k.startswith("WEBSERVICE_APP_"):
                newk = k[15:].lower()
                self._worker_para[newk] = v
        return


    # Worker function
    def worker(pid, task_queue, result_queue, params):
        # Params are key value pairs from configuration file, section app_name
        raise NotImplemented

    def flask_start(self, pid, task_queue, result_queue, params):
        self.output(1, "FLASK service started at %s:%s" % (self.host(), self.port()) )

        if self._template_folder is None:
            tf = None
        else:
            tf = self.autopath(self._template_folder)

        if self._static_folder is None:
            sf = None
        else:
            sf = self.autopath(self._static_folder)


        flask_app = flask.Flask(self._app_name,
                                template_folder = tf,
                                static_folder   = sf,
                                static_url_path = self._static_url)

        self.load_route(flask_app)

        assert self.port(), "Port not set!"
        flask_app.run(self.host(), self.port(),  self.debug())


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

    def queue_length(self):
        self.update_results(getall=True)
        n = len(list(filter(lambda x: not x["finished"], self.result_cache.values())))

        response = flask.jsonify(n)
        return response

    @staticmethod
    def random_str(l=20):
        return ''.join(random.choice(string.ascii_lowercase + string.digits) for i in range(l))

    @staticmethod
    def bytes2hash(s,digits=32):
        return hashlib.md5(s).hexdigest()[:digits]

    @staticmethod
    def str2hash(s,digits=32):
        return hashlib.md5(s.encode('utf8')).hexdigest()[:digits]

    def submit(self):
        if flask.request.method in ['GET', 'POST']:
            p = self.api_para()
        else:
            response = flask.jsonify("METHOD %s is not suppoted" % flask.request.method)
            return response

        if "tasks" not in p and "task" not in p and "q" not in p:
            response = flask.jsonify("Please submit with actual tasks")
            return response

        try:
            if "tasks" in p:
                raw_tasks = json.loads(p["tasks"])
            elif "task" in p:
                raw_tasks = [json.loads(p["task"])]
            elif "q" in p:
                raw_tasks = json.loads(p["q"])
        except json.decoder.JSONDecodeError:
            response = flask.jsonify("Bad JSON format for task(s)")
            return response
        
        if not isinstance(raw_tasks,list):
            return flask.jsonify("Bad format for task(s)")

        developer_email = ""
        developer_email_valid = False
        if "developer_email" in p:
            developer_email = p["developer_email"].strip()
            email_valid = re.compile(r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$')
            developer_email_valid = bool(email_valid.match(developer_email))
        else:
            self.output(1, "No developer email address is provided with task(s): %s" % raw_tasks)
            response = flask.jsonify("Please provide your E-mail address. Use developer_email field.")
            return response

        if not developer_email_valid:
            self.output(1, "Invalid developer email (%s) for task(s): %s" % (developer_email, raw_tasks))
            response = flask.jsonify("Please provide valid E-mail address.")
            return response

        userid = self.str2hash(developer_email)
        
        nocache = (p.get('nocache') == 'true')

        res = []
        for raw_task in raw_tasks:
            try:
                task_detail = self.form_task(raw_task)
            except (AttributeError, TypeError, ValueError):
                raise APIParameterError(
                    "Bad job parmeters (%s)"
                    % task_detail)

            if "id" not in task_detail:
                raise APIParameterError(
                    "No id provided for your job(%s), probably check the form_task method"
                    % task_detail)

            if nocache:
                self.set_task_id(task_detail,random=True)

            returned_task_detail = copy.deepcopy(task_detail)

            res.append(returned_task_detail)

            if "error" in returned_task_detail:
                del returned_task_detail["id"]
                continue
            else:
                self.set_task_id(returned_task_detail,user=developer_email)

            task_id = task_detail["id"]
            status = {
                "id": task_id,
                "submission_original": raw_task,
                "submission_detail": task_detail,
                "finished": False,
                "stat": {},
                "result": {}
            }

            retcached = False
            queuejob = False
            if task_id not in self.result_cache:
                queuejob = True
            else:
                result = self.result_cache[task_id]
                if result['finished']:
                    if result.get('expires',1e+20) < time.time():
                        queuejob = True
                    else:
                        retcached = True
                else:
                    # do nothing
                    pass
            
            assert not retcached or not queuejob 
            
            if queuejob:
                self.task_queue.put(task_detail)
                self.result_cache[task_id] = status
            elif retcached:
                result = self.result_cache[task_id]
                result['stat']['cached'] = True
                res[-1]['incache'] = True
            else:
                # do nothing
                pass
            
            self.output(1, "Job received by API: %s (developer_email: %s)" % (task_detail,developer_email))

        response = flask.jsonify(res)
        return response

    def retrieve(self):
        if flask.request.method in ['GET', 'POST']:
            p = self.api_para()
        else:
            response = flask.jsonify("METHOD %s is not supported" % flask.request.method)
            return response

        if "list_ids" not in p and \
                "task_ids" not in p and \
                "list_id" not in p and \
                "task_id" not in p:
            return flask.jsonify("Please provide with list_id(s)")

        if "list_ids" in p:
            task_ids = json.loads(p["list_ids"])
        elif "list_id" in p:
            task_ids = [str(p["list_id"])]

        elif "task_ids" in p:
            task_ids = json.loads(p["task_ids"])
        elif "task_id" in p:
            task_ids = [str(p["task_id"])]


        timeout = 0
        if "timeout" in p:
            try:
                timeout = float(p["timeout"])
                if timeout < 0:
                    timeout = 0
                if timeout > 10:
                    timeout = 10
            except:
                pass

        res = []
        query_start_timestamp = time.time()
        delay = 0.2
        for query_round in range(int(math.ceil(timeout/delay))+1):
            res = []
            got_all = True
            self.update_results(getall=True)

            for tmp in task_ids:
                # Assume MD5
                task_id = self.get_task_id(tmp)

                if task_id in self.result_cache:
                    r = copy.deepcopy(self.result_cache[task_id])
                else:
                    res.append({"id": tmp, "finished": True, "status": "ERROR", "result": [], "error": ["task_id %s not found" % tmp]})
                    continue

                # cached = True
                # if r["initial_user_id"] == user_id:
                #     cached = False
                # if r["finished"]:
                #     r["stat"]["cached"] = cached

                if not r["finished"]:
                    got_all = False

                r["task"] = r["submission_detail"]

                del r["submission_original"]
                del r["submission_detail"]
                # del r["initial_user_id"]

                r["id"] = tmp
                # r["task"]["id"] = tmp
                 
                try:
                   del r["task"]["id"]
                except:
                   pass

                try:
                    del r["stat"]["starttime"]
                    del r["stat"]["endtime"]
                except:
                    pass

                res.append(r)


            if timeout == 0 or (time.time() - query_start_timestamp) > timeout:
                break
            if got_all:
                break
            time.sleep(delay)


        response = flask.jsonify(res)
        self.output(1, "Retrieve json: %s" % res)
        return response


    def upload_file(self):
        if flask.request.method == 'POST':

            if 'file' not in flask.request.files:
                return flask.abort(400)

            file = flask.request.files['file']
            filename = werkzeug.utils.secure_filename(file.filename)

            if file.filename == '':
                response = flask.jsonify('No selected file')

                return response

            task_detail = self.form_task({"original_file_name": file.filename})
            task_id = task_detail["id"]

            if file and self.allow_file_ext(file.filename):
                file.save(os.path.join(self.input_file_folder(), task_id))
            else:
                response = flask.jsonify('File extension is not supported')

                return response

            status = {
                "id": task_id,
                "submission_original": {},
                "submission_detail": task_detail,
                "finished": False,
                "stat": {},
                "result": {}
            }

            if task_id in self.result_cache:
                if self.result_cache[task_id]['finished']:
                    if "stat" in self.result_cache[task_id]:
                        self.result_cache[task_id]["stat"]["cached"] = True
                    self.result_cache[task_id]["incache"] = True
            else:
                self.task_queue.put(task_detail)
                self.result_cache[task_id] = status
            self.output(1, "Job received by API: %s" % (task_detail))

        return self.file_upload_finished_page(list_id=task_id)


    def download_file(self):
        if flask.request.method in ['GET', 'POST']:
            p = self.api_para()
        else:
            response = flask.jsonify("METHOD %s is not suppoted" % flask.request.method)

            return response


        if "list_id" not in p:
            response = flask.jsonify("Please provide with list_id(s)")

            return response

        list_id = p["list_id"]

        if not self.result_cache[list_id]["finished"]:
            response = flask.jsonify("The computation haven't finished yet")

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
    def form_task(self, params):
        if not isinstance(params,dict):
            raise ValueError("No parameter dictionary provided")
        
        task = {}
        for par in self.task_params:
            if par in params:
                try:
                    task[par] = params[par].strip()
                except (AttributeError,TypeError,ValueError):
                    task[par] = params[par]
            elif self.task_params[par] != None:
                try:
                    task[par] = self.task_params[par].strip()
                except (AttributeError,TypeError,ValueError):
                    task[par] = self.task_params[par]
        self.set_task_id(task)
        return task
    
    def set_task_id(self,task,random=False,user=None):
        if not random and not user:
            assert "id" not in task
            task_str = json.dumps(task, sort_keys=True)
            task["id"] = self.str2hash("; ".join(task_str),self._taskidlength)
        elif user:
            userid = self.str2hash(user,self._useridlength)
            task["id"] = task["id"]+userid
        elif random:
            task["id"] = self.str2hash(self.random_str(32),self._taskidlength)
    
    def get_task_id(self,retrieve_id):
        return retrieve_id[:self._taskidlength]

    # @staticmethod
    def api_para(self):
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
                    "starttime": res["starttime"],
                    "endtime": res["endtime"],
                    "runtime": res["runtime"],
                    "cached": False
                }

                self.result_cache[res["id"]]["error"] = res["error"]
                self.result_cache[res["id"]]["result"] = res["result"]
                self.result_cache[res["id"]]["status"] = res["status"]

                self.result_cache[res["id"]]['finished'] = True
            except queue.Empty:
                break
            except KeyError:
                self.output(1, "Job ID %s is not present" % res["id"])


    def allow_file_ext(self, filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in self.allowed_file_ext()

    def status(self):
        response = flask.jsonify(True)
        return response


    # Load route and handler to flask app
    def load_route(self, app):

        app.add_url_rule("/status", "status", self.status, methods=["GET", "POST"])
        # app.add_url_rule("/queue_length", "queue_length", self.queue_length, methods=["GET", "POST"])
        app.add_url_rule("/retrieve", "retrieve", self.retrieve, methods=["GET", "POST"])
        if self._file_based_job:
            app.add_url_rule("/file_upload", "upload_file", self.upload_file, methods=["GET", "POST"])
            app.add_url_rule("/file_download", "download_file", self.download_file, methods=["GET", "POST"])
        else:
            app.add_url_rule("/submit", "submit", self.submit, methods=["GET", "POST"])

        if self._allow_cors:
            @app.after_request
            def cors(response):
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response

        self.load_modular_front_end(app)
        self.load_additional_route(app)


    def load_modular_front_end(self, app):
        app.add_url_rule("/", "home", self.home, methods=["GET", "POST"])
        return

    def load_additional_route(self, app):
        return

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

        self.output(0, "Host: %s" % self._host)
        self.output(0, "Port: %s" % self._port)
        self.output(0, "Min_Worker_Num: %s" % self._min_worker_num)
        self.output(0, "Max_Worker_Num: %s" % self._max_worker_num)

        for k,v in self._worker_para.items():
            self.output(0, "%s(worker para): %s" % (k,v))

        flask_process = multiprocessing.Process(target=self.flask_start, args=(0, self.task_queue, self.result_queue, self._worker_para))
        flask_process.start()

        self._worker_started = True
        self.manipulate_dirs()

        self.output(0, "Starting workers")
        self._deamon_process_pool = self.new_worker_processes()


        self.output(0, "Downloading necessary data... please wait")
        self.pre_start(self._worker_para)
        self.output(0, "Download phase finished")


        self.output(0, "Terminating previous workers with outdated data")
        self.terminate_all()

        self.output(0, "Starting workers with updated data")
        self._deamon_process_pool = self.new_worker_processes()

        self.monitor()

    def new_worker_process(self):

        self._last_worker_process_id += 1
        pid = self._last_worker_process_id

        suicide_queue = [
            self.request_suicide_queue,
            self.approve_suicide_queue
        ]

        proc = multiprocessing.Process(
            target=self.worker,
            args=(pid,)
        )

        proc.start()

        self.output(0, "Worker-%s: Created" % (pid))

        return pid, proc

    def new_worker_processes(self):

        process_pool = {}
        for i in range(self._min_worker_num):
            pid, proc = self.new_worker_process()
            process_pool[pid] = proc

        return process_pool

    def start_worker(self,pid):
        self._pid_ = pid
        self.worker_output("Starting up")

    def worker_output(self,message,level=2):
        self.output(level, "Worker-%s: %s" % (self._pid_,message))

    def worker_ready(self):
        self.worker_output("Ready to take job")

    def get_param(self,key,default=None):
        return self._worker_para.get(key,default) 

    def get_filename_param(self,key,default=None):
        fn = self.get_param(key,default)
        if not fn:
            raise LookupError(f"Filename parameter {key} must be specified.")
        return self.autopath(fn)

    def get_task(self):

        i = 0
        counter = 0
        next_report = 600
        while True:
            counter += 1
            i += 1

            try:
                task_detail = self.task_queue.get_nowait()
                self.worker_output("Computing task: %s" % (task_detail,))
                self._task_ = (task_detail['id'],time.time())            
                return task_detail
            except queue.Empty:
                time.sleep(1)

            if counter > 599:
                i = 0

                time_str = ""
                hours = int(counter / 3600)
                minutes = int(counter % 3600 / 60)

                if hours > 0:
                    time_str += "%sh " % hours
                time_str += "%sm " % minutes

                if counter == next_report:
                    if counter < 3600:
                        next_report += 600
                    else:
                        next_report += 3600

                    self.output(2, "Worker-%s has been idling for %s" % (self._pid_, time_str))
                self.request_suicide_queue.put(self._pid_)

            try:
                approval = self.approve_suicide_queue.get_nowait()
                if approval:
                    self.output(2, "Worker-%s received KILL-SIGNAL, Bye." % self._pid_)
                    sys.exit()
            except queue.Empty:
                continue

    def put_result(self,result,expires=None):
        calculation_end_time = time.time()
        self.worker_output("Finished computing job (%s)" % (self._task_[0],))
        calculation_time_cost = calculation_end_time - self._task_[1]
        res = {
            "id": self._task_[0],
            "starttime": self._task_[1],
            "endtime": calculation_end_time,
            "runtime": calculation_time_cost,
            "error": [],
            "result": result,
            "status": "OK"
            }
        if expires:
            res["expires"] = (time.time()+expires)
        self.worker_output("Job (%s) Complete: %s" % (self._task_[0], res))
        self.result_queue.put(res)

    def put_error(self,error,expires=None):
        calculation_end_time = time.time()
        self.worker_output("Finished computing job (%s)" % (self._task_[0],))
        calculation_time_cost = calculation_end_time - self._task_[1]
        res = {
            "id": self._task_[0],
            "starttime": self._task_[1],
            "endtime": calculation_end_time,
            "runtime": calculation_time_cost,
            "error": [error],
            "result": [],
            "status": "ERROR"
            }
        if expires:
            res["expires"] = (time.time()+expires)
        self.worker_output("Job (%s) Failed: %s" % (self._task_[0], res))
        self.result_queue.put(res)

    def get_queue_length(self):
        url = "http://%s:%s/queue_length" % (self.host(), self.port())

        req = urllib.request.urlopen(url)
        x = req.read()

        return int(x)

    def deamon_process_pool_update(self):

        for pid, proc in list(self._deamon_process_pool.items()):

            if not proc.is_alive():
                self.output(0, "Worker-%s was terminated for some reasons... Please check the log for more info" % (pid))
                del self._deamon_process_pool[pid]

        return

    def monitor(self):
        self.cleanup()

        while True:
            time.sleep(60)

            unfinished_job_count = self.task_queue.qsize()

            self.deamon_process_pool_update()

            require_new_worker = False
            if unfinished_job_count > 10 or len(self._deamon_process_pool) < self.min_worker_num():
                require_new_worker = True
            if len(self._deamon_process_pool) >= self.max_worker_num():
                require_new_worker = False

            if require_new_worker:

                self.output(0, "Need more workers...")
                new_pid, new_proc = self.new_worker_process()
                self._deamon_process_pool[new_pid] = new_proc

            if unfinished_job_count >= len(self._deamon_process_pool):
                while True:
                    try:
                        pid = self.request_suicide_queue.get_nowait()
                    except queue.Empty:
                        break
                continue

            try:
                pid = self.request_suicide_queue.get_nowait()

                self.deamon_process_pool_update()

                if len(self._deamon_process_pool) > self.min_worker_num():
                    self.approve_suicide_queue.put(True)
                    self.output(0, "Sending KILL-SIGNAL to worker")
                self.deamon_process_pool_update()

            except queue.Empty:
                pass

    def cleanup(self):
        atexit.register(self.terminate_all)

    def terminate_all(self):
        for i, p in list(self._deamon_process_pool.items()):
            self.output(0, "Worker-%s is terminated" % (i))
            p.terminate()
            del self._deamon_process_pool[i]

class APIFrameworkWithFrontEnd(APIFramework):

    def load_modular_front_end(self, app):

        google_tracking_js = ""
        if self.google_analytics_tag_id() not in [None, ""]:
            google_tracking_js = self.google_analytics_script()

        kwarg = {
            "app_name": self._app_name,
            "app_name_lower": self._app_name.lower(),
            "google_analytics_html": google_tracking_js,
            "glymage_base_url": self.glymage_base_url(),
            "glymage_dev_email": self.glymage_dev_email(),
            "frontend_dev_email": self.frontend_dev_email()
        }

        @app.route('/')
        def home():
            return flask.render_template(self._home_html, **kwarg)

        @app.route('/header')
        def header():
            return flask.render_template("./header.html", **kwarg)

        @app.route('/footer')
        def footer():
            return flask.render_template("./footer.html", **kwarg)

        @app.route('/help')
        def help():
            return flask.send_from_directory('htmls', 'help.html', max_age=86400)
            
        @app.route('/example')
        def example():
            return flask.send_from_directory('htmls', 'example.html', max_age=86400)

        @app.route('/submitoption')
        def submitoption():
            return flask.send_from_directory('htmls', 'submitoption.html', max_age=86400)

        @app.route('/about')
        def about():
            return flask.render_template("./about.html", **kwarg)
        
        @app.route('/glycoapi.js')
        def glycoapijs():
            return flask.send_from_directory('htmls', 'glycoapi.js', max_age=86400)

        @app.route('/renderresult.js')
        def renderresult():
            return flask.send_from_directory('htmls', 'renderresult.js', max_age=86400)

        @app.route('/renderer.js')
        def renderer():
            return flask.send_from_directory('htmls', 'renderer.js', max_age=86400)

        @app.route('/head.js')
        def head():
            content = flask.render_template("./head.js", **kwarg)
            response = flask.make_response(content)
            response.mimetype = 'application/javascript'
            return response

        @app.route('/robots.txt')
        def robots():
            return flask.send_from_directory('htmls', 'robots.txt', max_age=86400)

    def google_analytics_script(self):
        tag = self.google_analytics_tag_id()
        res = """
<script async src="https://www.googletagmanager.com/gtag/js?id=%s"></script>
<script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){dataLayer.push(arguments);}
    gtag('js', new Date());

    gtag('config', '%s');
</script>""" % (tag, tag)
        return res


if __name__ == '__main__':
    multiprocessing.freeze_support()



