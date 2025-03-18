
import os
import re
import sys
import time
import datetime
import json
import copy
import flask
import base64
import requests
import urllib
import hashlib
import multiprocessing
import traceback
import subprocess
import glob
import shutil
from collections import defaultdict
from APIFramework import APIFramework, queue


import pygly.GlycanImage
import pygly.GlycanResource
import pygly.GlycanFormatter
import pygly.CompositionFormatter
import pygly.GlycanFormatterExceptions
import pygly.GlycanBuilderSVGParser
import pygly.alignment

class Glymage(APIFramework):

    allowed_display  = []
    allowed_notation = []


    def form_task(self, p):
        res = {}

        if "seq" in p:
            res["seq"] = p["seq"].strip()
        else:
            res["seq"] = None

        if "acc" in p:
            res["acc"] = p["acc"].strip()

            now = datetime.datetime.now()
            res["timestamp"] = now.strftime("%Y.%m.%d.%H")

        else:
            res["acc"] = None

        stdopts = True

        scale = 1.0
        if "scale" in p:
            scale = float(p["scale"])
            if scale != 1.0:
                stdopts = False

        notation = "snfg"
        if "notation" in p:
            notation = p["notation"].lower()
            if notation not in ["cfg", "snfg", "cfgbw", "cfglink", "uoxf", "text", "uoxfcol"]:
                raise RuntimeError
            if notation != "snfg":
                stdopts = False

        display = "extended"
        if "display" in p:
            display = p["display"].lower()
            if display not in ["normalinfo", "normal", "compact", "extended"]:
                raise RuntimeError
            if display not in ("extended","compact"):
                stdopts = False

        orientation = "RL"
        if "orientation" in p:
            orientation = p["orientation"].upper()
            if orientation not in ["RL", "LR", "BT", "TB"]:
                raise RuntimeError
            if orientation != "RL":
                stdopts = False

        redend = True
        if "redend" in p:
            tmp = p["redend"].lower()
            if tmp in ["y", "yes", "t", "true", "1"]:
                redend = True
            elif tmp in ["n", "no", "f", "false", "0"]:
                redend = False
            else:
                raise RuntimeError
            if redend != True:
                stdopts = False

        opaque = True
        if "opaque" in p:
            tmp = p["opaque"].lower()
            if tmp in ["y", "yes", "t", "true", "1"]:
                opaque = False
            elif tmp in ["n", "no", "f", "false", "0"]:
                opaque = True
            else:
                raise RuntimeError
            if opaque != True:
                stdopts = False

        image_format = "png"
        if "image_format" in p:
            image_format = p["image_format"].lower()
            if image_format not in ["png", "jpg", "jpeg", "svg"]:
                raise RuntimeError

        res["scale"] = scale
        res["notation"] = notation
        res["display"] = display
        res["orientation"] = orientation
        res["redend"] = redend
        res["opaque"] = opaque
        res["image_format"] = image_format

        task_str = ""
        for k in sorted(res.keys()):
            task_str += "_%s:%s"%(k,res[k])
        list_id = self.str2hash(task_str)
        res["id"] = list_id

        option_str = ""
        for k in sorted(res.keys()):
            if k in ("timestamp","image_format","id"):
                continue
            option_str += "_%s:%s"%(k,res[k])
        option_hash = self.str2hash(option_str)
        res["optionhash"] = option_hash

        res["stdopts"] = p.get("stdopts",stdopts)

        return res


    def worker(self, pid, task_queue, result_queue, suicide_queue_pair, params):

        self.output(2, "Worker-%s is starting up" % (pid))

        # TODO
        self.data_folder = self._static_folder
        # print self.data_folder

        tmp_image_folder = "tmp"
        try:
            os.mkdir(tmp_image_folder)
        except:
            pass

        cannonseq = dict()
        for l in open(os.path.join(self._static_folder,"cannonseq.tsv")):
            acc,seq = l.split('\t')
            cannonseq[acc.strip()] = seq.strip()

        gtc = pygly.GlycanResource.GlyTouCanNoPrefetch()
        self.output(2, "Worker-%s is ready to take job" % (pid))

        while True:
            task_detail = self.task_queue_get(task_queue, pid, suicide_queue_pair)

            self.output(2, "Worker-%s is computing task: %s" % (pid, task_detail))

            error = []
            calculation_start_time = time.time()


            list_id = task_detail["id"]
            acc = task_detail["acc"]
            if task_detail.get("seq"):
                seq = task_detail["seq"]
            else:
                seq = ""
            scale = task_detail["scale"]
            notation = task_detail["notation"]
            display = task_detail["display"]
            orientation = task_detail["orientation"]
            redend = task_detail["redend"]
            opaque = task_detail["opaque"]
            image_format = task_detail["image_format"]

            displayjava = display
            if display == "extended":
                displayjava = "normalinfo"

            ge = pygly.GlycanImage.GlycanImage()
            ge.scale(scale)
            ge.notation(notation)
            ge.display(displayjava)
            ge.orientation(orientation)
            ge.opaque(opaque)
            ge.reducing_end(redend)
            ge.format(image_format)
            ge.verbose(True)

            seq_hashes = []

            wurcs = None
            if acc:
                if task_detail["stdopts"]:
                    seq_hashes.append(("stdopts",acc))

                if acc in cannonseq:
                    wurcs = cannonseq[acc]
                else:
                    wurcs = gtc.getseq(acc, format="wurcs")

                if wurcs == None:
                    error.append("GlyTouCan Accession (%s) is not present in triple store" % acc)
                else:
                    seq = wurcs
                    if task_detail["stdopts"]:
                        seq_hashes.append(("stdopts",self.str2hash(wurcs)))
                    if acc not in cannonseq:
                        cannonseq[acc] = wurcs

            elif seq:
                if task_detail["stdopts"]:
                    seq_hashes.append(("stdopts",self.str2hash(seq)))
                if not (seq.startswith('RES') or seq.startswith('WURCS')):
                    newseq = None
                    if not newseq:
                        try:
                            newseq = self.cp.toSequence(seq)
                            ge.reducing_end(True)
                        except pygly.GlycanFormatter.GlycanParseError:
                            pass
                    if not newseq:
                        try:
                            gly = self.ip.toGlycan(seq)
                            newseq = gly.glycoct()
                        except pygly.GlycanFormatter.GlycanParseError:
                            pass
                    if not newseq:
                        try:
                            gly = self.ip1.toGlycan(seq)
                            newseq = gly.glycoct()
                        except pygly.GlycanFormatter.GlycanParseError:
                            pass
                    if newseq:
                        seq = newseq
            else:
                error.append("No accession or sequence provided.")

            seq_hashes.append(("anyopts",task_detail['optionhash']))
                
            str_image = ""
            image_md5_hash = ""

            tmpfilebase = list_id
            if acc:
                tmpfilebase += (":"+acc)

            if len(error) == 0:

                tmp_image_file_name = "./%s/%s.%s" % (tmp_image_folder, tmpfilebase, image_format)
                print("Sequence:",seq,file=sys.stderr)
                ge.writeImage(seq, tmp_image_file_name)

                try:
                    str_image = open(tmp_image_file_name,'rb').read()

                    image_md5_hash = self.bytes2hash(str_image)
                    img_actual_path = self.data_folder + "/hash/%s.%s" % (image_md5_hash, image_format)
                    shutil.copy(tmp_image_file_name, img_actual_path)

                    json_actual_path = None

                    if seq.startswith('WURCS=') and image_format == 'svg':

                        tmp_image_file_name = "./%s/%s.%s" % (tmp_image_folder, tmpfilebase, 'txt')
                        with open(tmp_image_file_name,'w') as wh:
                             wh.write(seq)

                        # tmp_image_file_name = "./%s/%s.%s" % (tmp_image_folder, tmpfilebase, 'svg')
                        # with open(tmp_image_file_name,'wb') as wh:
                        #      wh.write(str_image)

                        cmd="python3 pygly-scripts/resmap_tojson.py %s %s %s %s"%(tmp_image_folder,tmp_image_folder,tmp_image_folder,tmpfilebase)
                        subprocess.run(cmd,shell=True)

                        tmp_json_file_name = "./%s/%s.%s" % (tmp_image_folder, tmpfilebase, 'json')
                        if os.path.exists(tmp_json_file_name):
                            str_json = open(tmp_image_file_name,'rb').read()
                            json_md5_hash = self.bytes2hash(str_json)
                            json_actual_path = self.data_folder + "/hash/%s.%s" % (json_md5_hash, 'json')
                            shutil.copy(tmp_json_file_name, json_actual_path)

                except:
                    error.append("Could not generate image...\n%s"%( traceback.format_exc(),))

            for fn in glob.glob("./%s/%s.*"%(tmp_image_folder, tmpfilebase)):
                os.unlink(fn)

            resultvalue = ""
            if len(error) == 0:

                for thetype,accorseq in seq_hashes:
                    try:
                        if thetype == "stdopts":
                            image_sym_path = os.path.join(self.data_folder, notation, display, accorseq + "." + image_format)
                            if not resultvalue:
                                resultvalue = image_sym_path
                        else:
                            image_sym_path = os.path.join(self.data_folder, "hash", accorseq + "." + image_format)                            
                            if not resultvalue:
                                resultvalue = image_sym_path
                        if not os.path.exists(image_sym_path):
                            os.link(os.path.abspath(img_actual_path), os.path.abspath(image_sym_path))
                            print("%s -> %s"%(image_sym_path,img_actual_path))

                    except:
                        error.append("Issue in make symbolic link (%s)\n%s" % (image_sym_path, traceback.format_exc()))

                    try:
                        if json_actual_path:
                            if thetype == "stdopts":
                                json_sym_path = os.path.join(self.data_folder, notation, display, accorseq + "." + 'json')
                            else:
                                json_sym_path = os.path.join(self.data_folder, "hash", accorseq + "." + 'json')
                            if not os.path.exists(json_sym_path):
                                os.link(os.path.abspath(json_actual_path), os.path.abspath(json_sym_path))
                                print("%s -> %s"%(json_sym_path,json_actual_path))
                    except:
                        error.append("Issue in make symbolic link (%s)\n%s" % (json_sym_path, traceback.format_exc()))

            calculation_end_time = time.time()
            calculation_time_cost = calculation_end_time - calculation_start_time

            self.output(2, "Worker-%s finished computing job (%s)" % (pid, list_id))

            res = {
                "id": list_id,
                "start time": calculation_start_time,
                "end time": calculation_end_time,
                "runtime": calculation_time_cost,
                "error": error,
                "result": resultvalue,
            }
            self.output(2, "Job (%s): %s" % (list_id, res))
            if len(res['error']) > 0:
                for err in res['error']:
                    self.output(2, "Error:\n%s" % (err,))
            result_queue.put(res)

    def error_image(self,force_error=False):
        try:
            if force_error:
                raise RuntimeError
            notfoundurl = str(flask.request.url)
            content = notfoundurl.split("/")
            imageword = content[3]
            notation = content[4]
            display = content[5]
            filename = content[6]

            acc, image_format = filename.split(".")
            if image_format not in ["png","svg","jpg","jpeg"]:
                raise RuntimeError

            if imageword != "image":
                raise RuntimeError

            if notation not in ["snfg"]:
                raise RuntimeError

            if display not in ["compact", "extended"]:
                raise RuntimeError

            acc = acc.upper()
            if not self.glytoucan_accession_detection(acc):
                raise RuntimeError

            option = {
                "notation": notation,
                "display": display,
                "image_format": image_format,
            }
            return self.image_generation(acc,"accession",**option)

        except:
            fp = self.abspath(os.path.join(self._static_folder, "error.png"))
            image_format = (flask.request.url).split(".")[-1]
            if image_format == "json":
                fp = self.abspath(os.path.join(self._static_folder, "error.json"))
                return flask.send_file(fp, mimetype='application/json')
            return flask.send_file(fp, mimetype='image/png'), 404

    def glytoucan_accession_detection(self, s):
        gtcp = re.compile(r"^G\d{5}\w{2}$")
        return gtcp.search(s)

    def image_generation_submit(self, option):
        imagegenerationwebservicebaseurl = "http://%s:%s/" % (self.host(), self.port()) + "submit"

        req = requests.post(
            imagegenerationwebservicebaseurl,
            data={
                "task": json.dumps(option),
                "developer_email": "GlymageBackEnd@glyomics.org"
            })

        jobid = json.loads(req.text)[0]["id"]

        return jobid

    @staticmethod
    def mimetype(image_format):
        if image_format in ('png','jpg','jpeg'):
            return "image/"+image_format
        elif image_format == 'svg':
            return "image/svg+xml"
        elif image_format == 'json':
            return "application/json"

    def image_generation(self, query, query_type, notation='snfg', display='extended', image_format=None):

        result_path = ""

        imagegenerationwebservicebaseurl = "http://%s:%s/" % (self.host(), self.port())

        assert query_type in ["sequence", "accession", "task"]
        query = query.strip()

        if query_type in ("task","accession") and '.' in query and query.rsplit('.',1)[1] in ('svg','png','jpg','jpeg','json'):
            query,image_format=query.rsplit('.',1)

        option = {}
        option["notation"] = notation
        option["display"] = display
        option["image_format"] = image_format

        if query_type == "accession":
            option["acc"] = query
        elif query_type == "sequence":
            option["seq"] = query

        task_id = ""
        if query_type == "task":
            task_id = query
        else:
            # See if the image already exists
            locater = ""
            if query_type == "accession":
                locater = query
            elif query_type == "sequence":
                locater = self.str2hash(query)
            result_path = os.path.join(self.data_folder, notation, display, locater + "." + image_format)

            if os.path.exists(result_path):
                return flask.send_file(result_path, mimetype=self.mimetype(image_format))

            # Nope, submit the task
            task_id = self.image_generation_submit(option)

        time.sleep(1)
        errors = ["Time out..."]
        for i in range(10):
            retrieveurl = imagegenerationwebservicebaseurl + "retrieve?task_id="
            retrieveurl += task_id

            response = urllib.request.urlopen(retrieveurl)
            response_obj = json.loads(response.read())[0]

            if len(response_obj.get("error",[]))>0:
                errors = response_obj.get("error",[])
                break
            if response_obj["finished"]:
                result_path = response_obj["result"]
                errors = response_obj.get("error",[])
                if image_format == None:
                    # force image format from task
                    image_format = response_obj["task"]["image_format"]
                result_path = result_path.rsplit('.',1)[0] + "." + image_format
                break

            time.sleep(2)

        if len(errors) == 0 and os.path.exists(result_path):
            return flask.send_file(result_path, mimetype=self.mimetype(image_format))
        return self.error_image(force_error=True)

    ip = pygly.GlycanFormatter.IUPACLinearFormat()
    ip1 = pygly.GlycanFormatter.IUPACParserExtended1()
    cp = pygly.CompositionFormatter.CompositionFormat()
    def load_additional_route(self, app):
        # TODO
        self.data_folder = self._static_folder

        self.cannonseq = dict()
        for l in open(os.path.join(self._static_folder,"cannonseq.tsv")):
            acc,seq = l.split('\t')
            self.cannonseq[acc.strip()] = seq.strip()

        @app.errorhandler(404)
        def error_handling(e):
            return self.error_image()

        @app.route('/js/<path:path>')
        def serve_js(path):
            return flask.send_from_directory('js', path)

        @app.route('/css/<path:path>')
        def serve_css(path):
            return flask.send_from_directory('css', path)

        @app.route('/demo/<path:path>')
        def serve_demo(path):
            return flask.send_from_directory('demo', path)

        @app.route('/getimage', methods=["GET", "POST"])
        @app.route('/getimage/<query>', methods=["GET"])
        def getimage(query=""):
            para = {}
            if flask.request.method == "GET":
                para = flask.request.args
            elif flask.request.method == "POST":
                para = flask.request.form
            else:
                return self.error_image(force_error=True)

            p = {}
            for k in dict(para).keys():
                v = para.get(k)
                if v:
                    p[k] = str(v)

            query_type = ""
            if "seq" in p:
                query = p["seq"].strip()
                query_type = "sequence"
                if not (query.startswith('RES') or query.startswith('WURCS')):
                    newquery = None
                    if not newquery:
                        try:
                            newquery = self.cp.toSequence(query)
                        except pygly.GlycanFormatter.GlycanParseError:
                            pass
                    if not newquery:
                        try:
                            gly = self.ip.toGlycan(query)
                            newquery = gly.glycoct()
                        except pygly.GlycanFormatter.GlycanParseError:
                            pass
                    if not newquery:
                        try:
                            gly = self.ip1.toGlycan(query)
                            newquery = gly.glycoct()
                        except pygly.GlycanFormatter.GlycanParseError:
                            pass
                    if not newquery:
                        return self.error_image(force_error=True)
                    query = newquery

            if "acc" in p:
                query = p["acc"].strip()
                query_type = "accession"

            if "list_id" in p:
                # TODO should be removed in the future version
                query = p["list_id"].strip()
                query_type = "task"

            if "task_id" in p:
                query = p["task_id"].strip()
                query_type = "task"

            if not query_type and query:
                query=query.strip()
                if self.glytoucan_accession_detection(query.split('.')[0]):
                    query_type = "accession"
                elif re.search(r'^[0-9a-f]{32}$',query.split('.')[0]):
                    query_type = "accession" # actually sequence hash
                elif re.search(r'^[0-9a-f]{52}$',query.split('.')[0]):
                    query_type = "task"

            if query == "" or query_type == "":
                return self.error_image(force_error=True)

            p["notation"] = p.get("notation","snfg").lower()
            if p["notation"] not in ("snfg",):
                return self.error_image(force_error=True)

            p["display"] = p.get("display","extended").lower()
            if p["display"] not in ("extended","compact"):
                return self.error_image(force_error=True)

            if "image_format" in p or query_type != 'task':
                p["image_format"] = p.get("image_format","png").lower()
                if p["image_format"] not in ("png","jpg","jpeg","svg"):
                    return self.error_image(force_error=True)

            for k in ("task_id","list_id","seq","acc"):
                if k in p:
                    del p[k]

            # print >>sys.stderr, query, query_type, p

            return self.image_generation(query, query_type, **p)


if __name__ == '__main__':
    multiprocessing.freeze_support()

    glymage_app = Glymage()
    glymage_app.find_config("Glymage.ini")
    glymage_app.start()











