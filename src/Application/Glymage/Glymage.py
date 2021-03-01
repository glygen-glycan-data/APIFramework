
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


class Glymage(APIFramework):


    def form_task(self, p):
        res = {}
        seq = p["seq"].strip()

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
                opaque = True
            elif tmp in ["n", "no", "f", "false", "0"]:
                opaque = False
            else:
                raise RuntimeError

        image_format = "png"
        if "image_format" in p:
            image_format = p["image_format"].lower()
            if image_format not in ["png", "jpg", "jpeg", "svg"]:
                raise RuntimeError

        res["seq"] = seq
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

        list_id = hashlib.md5(task_str).hexdigest()

        res["id"] = list_id


        return res


    def worker(self, pid, task_queue, result_queue, params):

        self.output(2, "Worker-%s is starting up" % (pid))

        tmp_image_folder = "tmp"
        try:
            os.mkdir(tmp_image_folder)
        except:
            pass

        self.output(2, "Worker-%s is ready to take job" % (pid))

        while True:
            try:
                task_detail = task_queue.get_nowait()
            except queue.Empty:
                time.sleep(1)
                continue
            self.output(2, "Worker-%s is computing task: %s" % (pid, task_detail))

            error = []
            calculation_start_time = time.time()


            list_id = task_detail["id"]
            seq = task_detail["seq"]
            scale = task_detail["scale"]
            notation = task_detail["notation"]
            display = task_detail["display"]
            orientation = task_detail["orientation"]
            redend = task_detail["redend"]
            opaque = task_detail["opaque"]
            image_format = task_detail["image_format"]

            if display == "extended":
                display = "normalinfo"

            ge = pygly.GlycanImage.GlycanImage()
            ge.scale(scale)
            ge.notation(notation)
            ge.display(display)
            ge.orientation(orientation)
            ge.opaque(opaque)
            ge.reducing_end(redend)
            ge.format(image_format)

            # print scale, notation, display, orientation, opaque, redend, image_format

            str_image = ""
            image_md5_hash = ""
            try:
                tmp_image_file_name = "./%s/%s.%s" % (tmp_image_folder, list_id, image_format)
                ge.writeImage(seq, tmp_image_file_name)

                if image_format == "svg":
                    f = open(tmp_image_file_name)
                    str_image = f.read()
                    f.close()
                    image_md5_hash = hashlib.md5(str_image).hexdigest()
                else:
                    str_image = base64.b64encode(open(tmp_image_file_name, "rb").read())
                    image_md5_hash = hashlib.md5(open(tmp_image_file_name).read()).hexdigest()
                os.remove(tmp_image_file_name)

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
                "result": [image_md5_hash, str_image]
            }
            self.output(2, "Job (%s): %s" % (list_id, res))
            result_queue.put(res)

    @staticmethod
    def str2hash(s):
        return hashlib.md5(s).hexdigest()

    def error_image(self):
        fp = self.abspath(os.path.join(self._static_folder, "error.png"))
        return flask.send_file(fp, mimetype='image/png')

    def load_additional_route(self, app):
        self.data_folder = "./image"

        @app.errorhandler(404)
        def error_handling(e):
            return self.error_image(), 404

        @app.route('/test')
        def x():
            return open("./htmls/ig.html").read()

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

            option = {}

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

            seq = p["seq"]
            seq = seq.strip()
            seq_hash = self.str2hash(seq)

            option["seq"] = seq

            option["notation"] = notation
            option["display"] = display

            option["image_format"] = image_format

            """
            option["scale"] = scale
            option["orientation"] = orientation
            option["redend"] = redend
            option["opaque"] = opaque
            """

            image_sym_path_seq = os.path.join(self.data_folder, notation, display, seq_hash + "." + image_format)

            mimetype = image_format
            if os.path.exists(image_sym_path_seq):
                pass
            else:

                imagegenerationwebservicebaseurl = "http://%s:%s/" % (self.host(), self.port())

                submiturl = imagegenerationwebservicebaseurl + "submit?"

                submiturl += "tasks=" + urllib.quote_plus(json.dumps([option]))
                response = urllib2.urlopen(submiturl)
                jobid = json.loads(response.read())[0]["id"]

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

                ihash, image_str = b64imagecomputed["result"]

                img_actual_path = self.data_folder + "/hash/%s.%s" % (ihash, image_format)

                if image_format == "svg":
                    imgf = open(img_actual_path, "w")
                    imgf.write(image_str)
                    imgf.close()
                    mimetype = "svg+xml"
                else:
                    imgf = open(img_actual_path, "wb")
                    imgf.write(base64.b64decode(image_str))
                    imgf.close()

                os.link(os.path.abspath(img_actual_path), os.path.abspath(image_sym_path_seq))

            return flask.send_file(image_sym_path_seq, mimetype='image/%s' % mimetype)


if __name__ == '__main__':
    multiprocessing.freeze_support()

    glymage_app = Glymage()
    glymage_app.find_config("Glymage.ini")
    glymage_app.start()











