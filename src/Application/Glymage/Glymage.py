
import os
import re
import sys
import time
import json
import copy
import flask
import base64
import urllib, urllib2
import hashlib
import multiprocessing
from APIFramework import APIFramework, queue


import pygly.GlycanImage
import pygly.GlycanResource


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
        else:
            res["acc"] = None

        scale = 1.0
        if "scale" in p:
            scale = float(p["scale"])

        notation = "snfg"
        if "notation" in p:
            notation = p["notation"].lower()
            if notation not in ["cfg", "snfg", "cfgbw", "cfglink", "uoxf", "text", "uoxfcol"]:
                raise RuntimeError

        display = "extended"
        if "display" in p:
            display = p["display"].lower()
            if display not in ["normalinfo", "normal", "compact", "extended"]:
                raise RuntimeError


        orientation = "RL"
        if "orientation" in p:
            orientation = p["orientation"].upper()
            if orientation not in ["RL", "LR", "BT", "TB"]:
                raise RuntimeError

        redend = True
        if "redend" in p:
            tmp = p["redend"].lower()
            if tmp in ["y", "yes", "t", "true", "1"]:
                redend = True
            elif tmp in ["n", "no", "f", "false", "0"]:
                redend = False
            else:
                raise RuntimeError

        opaque = False
        if "opaque" in p:
            tmp = p["opaque"].lower()
            if tmp in ["y", "yes", "t", "true", "1"]:
                opaque = False
            elif tmp in ["n", "no", "f", "false", "0"]:
                opaque = True
            else:
                raise RuntimeError

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
            task_str += "_%s" % res[k]

        list_id = self.str2hash(task_str)
        res["id"] = list_id

        return res


    def worker(self, pid, task_queue, result_queue, suicide_queue_pair, params):

        self.output(2, "Worker-%s is starting up" % (pid))

        # TODO
        self.data_folder = self._static_folder
        print self.data_folder

        tmp_image_folder = "tmp"
        try:
            os.mkdir(tmp_image_folder)
        except:
            pass

        gtc = pygly.GlycanResource.GlyTouCanNoPrefetch()
        self.output(2, "Worker-%s is ready to take job" % (pid))

        while True:
            task_detail = self.task_queue_get(task_queue, pid, suicide_queue_pair)

            self.output(2, "Worker-%s is computing task: %s" % (pid, task_detail))

            error = []
            calculation_start_time = time.time()


            list_id = task_detail["id"]
            acc = task_detail["acc"]
            seq = task_detail["seq"]
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

            seq_hashs = []

            glycoct = None
            wurcs = None
            if acc != None:
                seq_hashs.append(acc)

                wurcs   = gtc.getseq(acc, format="wurcs")
                glycoct = gtc.getseq(acc, format="glycoct")

                if wurcs == None:
                    error.append("GlyTouCan Accession (%s) is not present" % acc)
                else:
                    seq = wurcs
                    seq_hashs.append(self.str2hash(wurcs))

                if glycoct != None:
                    seq_hashs.append(self.str2hash(glycoct))

            else:
                seq_hashs.append(self.str2hash(seq))


            str_image = ""
            image_md5_hash = ""

            if len(error) == 0:
                try:
                    tmp_image_file_name = "./%s/%s.%s" % (tmp_image_folder, list_id, image_format)
                    ge.writeImage(seq, tmp_image_file_name)

                    str_image = open(tmp_image_file_name).read()
                    image_md5_hash = self.str2hash(str_image)

                    img_actual_path = self.data_folder + "/hash/%s.%s" % (image_md5_hash, image_format)

                    os.rename(tmp_image_file_name, img_actual_path)
                    img_actual_path = self.data_folder + "/hash/%s.%s" % (image_md5_hash, image_format)
                    for accorseq in seq_hashs:
                        image_sym_path = os.path.join(self.data_folder, notation, display, accorseq + "." + image_format)
                        print image_sym_path
                        os.link(os.path.abspath(img_actual_path), os.path.abspath(image_sym_path))

                except:
                    error.append("Could not generate image...")

            calculation_end_time = time.time()
            calculation_time_cost = calculation_end_time - calculation_start_time

            self.output(2, "Worker-%s finished computing job (%s)" % (pid, list_id))

            res = {
                "id": list_id,
                "start time": calculation_start_time,
                "end time": calculation_end_time,
                "runtime": calculation_time_cost,
                "error": error,
                "result": image_md5_hash
            }
            self.output(2, "Job (%s): %s" % (list_id, res))
            result_queue.put(res)



    def error_image(self):
        fp = self.abspath(os.path.join(self._static_folder, "error.png"))

        try:
            notfoundurl = str(flask.request.url)
            content = notfoundurl.split("/")
            imageword = content[3]
            notation = content[4]
            display = content[5]
            filename = content[6]

            if imageword != "image":
                raise RuntimeError

            if notation not in ["snfg"]:
                raise RuntimeError

            if display not in ["compact", "extended"]:
                raise RuntimeError

            acc, image_format = filename.split(".")
            if image_format not in ["png"]:
                raise RuntimeError

            acc = acc.upper()
            if not self.glytoucan_accession_detection(acc):
                raise RuntimeError

            option = {
                "acc": acc,
                "notation": notation,
                "display": display,
                "image_format": image_format,
            }
            self.image_generation_submit(option)

        except:
            pass

        return flask.send_file(fp, mimetype='image/png')

    def glytoucan_accession_detection(self, s):
        gtcp = re.compile(r"^G\d{5}\w{2}$")
        return len(gtcp.findall(s)) > 0


    def image_generation_submit(self, option):
        imagegenerationwebservicebaseurl = "http://%s:%s/" % (self.host(), self.port())

        submiturl = imagegenerationwebservicebaseurl + "submit?"
        submiturl += "tasks=" + urllib.quote_plus(json.dumps([option]))

        response = urllib2.urlopen(submiturl)
        jobid = json.loads(response.read())[0]["id"]

        return jobid


    def image_generation(self, acc, seq, notation, display, image_format):

        seq = seq.strip()
        seq_hash = self.str2hash(seq)

        option = {}

        if acc != None:
            option["acc"] = acc

        if seq != None:
            option["seq"] = seq

        option["notation"] = notation
        option["display"] = display

        option["image_format"] = image_format

        image_sym_path_seq = os.path.join(self.data_folder, notation, display, seq_hash + "." + image_format)

        mimetype = image_format
        if image_format == "svg":
            mimetype = "svg+xml"

        if os.path.exists(image_sym_path_seq):
            pass
        else:

            imagegenerationwebservicebaseurl = "http://%s:%s/" % (self.host(), self.port())

            jobid = self.image_generation_submit(option)

            b64imagecomputed = ["", ""]
            errors = ["Time out..."]
            for i in range(10):
                retrieveurl = imagegenerationwebservicebaseurl + "retrieve?list_id="
                retrieveurl += jobid

                response = urllib2.urlopen(retrieveurl)
                response_obj = json.loads(response.read())[0]

                if response_obj["finished"]:
                    b64imagecomputed = response_obj
                    errors = b64imagecomputed["error"]
                    break

                time.sleep(2)

            if len(errors) > 0:
                return self.error_image(), 404

        return flask.send_file(image_sym_path_seq, mimetype='image/%s' % mimetype)


    def load_additional_route(self, app):
        # TODO
        self.data_folder = self._static_folder

        @app.errorhandler(404)
        def error_handling(e):
            return self.error_image(), 404

        @app.route('/getimage')
        def getimage():
            para = {}
            if flask.request.method == "GET":
                para = flask.request.args
            elif flask.request.method == "POST":
                para = flask.request.form
            else:
                raise RuntimeError

            p = {}
            for k in dict(para).keys():
                v = para.get(k)
                p[k] = str(v)

            seq = p["seq"].strip()

            notation = "snfg"
            if "notation" in p:
                notation = p["notation"].lower()
                if notation not in ["snfg"]:
                    return self.error_image(), 404

            display = "extended"
            if "display" in p:
                display = p["display"].lower()
                if display not in ["compact", "extended"]:
                    return self.error_image(), 404

            image_format = "png"
            if "image_format" in p:
                image_format = p["image_format"].lower()
                if image_format not in ["png", "svg"]:
                    return self.error_image(), 404

            return self.image_generation(None, seq, notation, display, image_format)


if __name__ == '__main__':
    multiprocessing.freeze_support()

    glymage_app = Glymage()
    glymage_app.find_config("Glymage.ini")
    glymage_app.start()










