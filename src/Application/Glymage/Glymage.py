
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

        opaque = True
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

            seq_hashs = []

            wurcs = None
            if acc:
                seq_hashs.append(acc)

                if acc in cannonseq:
                    wurcs = cannonseq[acc]
                else:
                    wurcs = gtc.getseq(acc, format="wurcs")

                if wurcs == None:
                    error.append("GlyTouCan Accession (%s) is not present in triple store" % acc)
                else:
                    seq = wurcs
                    seq_hashs.append(self.str2hash(wurcs))

            elif seq:
                seq_hashs.append(self.str2hash(seq))
                if not (seq.startswith('RES') or seq.startswith('WURCS')):
                    newseq = None
                    if not newseq:
                        try:
                            gly = self.cp.toGlycan(seq)
                            newseq = gly.glycoct()
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

            str_image = ""
            image_md5_hash = ""

            if len(error) == 0:

                tmp_image_file_name = "./%s/%s.%s" % (tmp_image_folder, list_id, image_format)
                ge.writeImage(seq, tmp_image_file_name)

                try:
                    str_image = open(tmp_image_file_name,'rb').read()

                    image_md5_hash = self.bytes2hash(str_image)
                    img_actual_path = self.data_folder + "/hash/%s.%s" % (image_md5_hash, image_format)
                    os.rename(tmp_image_file_name, img_actual_path)
                except:
                    error.append("Could not generate image...\n%s"%( traceback.format_exc(),))


            if len(error) == 0:

                for accorseq in seq_hashs:
                    try:
                        image_sym_path = os.path.join(self.data_folder, notation, display, accorseq + "." + image_format)
                        if not os.path.exists(image_sym_path):
                            os.link(os.path.abspath(img_actual_path), os.path.abspath(image_sym_path))
                    except:
                        error.append("Issue in make symbolic link (%s)\n%s" % (image_sym_path, traceback.format_exc()))


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
            if len(res['error']) > 0:
                for err in res['error']:
                    self.output(2, "Error:\n%s" % (err,))
            result_queue.put(res)



    def error_image(self):
        try:
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
                "acc": acc,
                "notation": notation,
                "display": display,
                "image_format": image_format,
            }
            self.image_generation_submit(option)

        except:
            pass

        fp = self.abspath(os.path.join(self._static_folder, "error.png"))
        image_format = (flask.request.url).split(".")[-1]
        if image_format == "json":
            fp = self.abspath(os.path.join(self._static_folder, "error.json"))
            return flask.send_file(fp, mimetype='application/json')
        return flask.send_file(fp, mimetype='image/png')

    def glytoucan_accession_detection(self, s):
        gtcp = re.compile(r"^G\d{5}\w{2}$")
        return len(gtcp.findall(s)) > 0

    highlight_css_expand = """
                .glycanimage:hover .highlight_mono {
                       fill:white;
                       text-rendering: optimizeSpeed;
                       stroke:white;
                       transform: scale(1.3);
                       transform-origin: center;
                       transform-box: fill-box;
                }
    """

    # This is the default...
    highlight_css_outline = """
                .glycanimage:hover .highlight_mono * {
                       stroke: rgb(247, 71, 62) !important; 
                       stroke-width: 4;
                } 
                .glycanimage:hover .highlight_link * {
                       stroke: rgb(247, 71, 62) !important; 
                       stroke-width: 4;
                } 
    """
    gbsp = pygly.GlycanBuilderSVGParser.GlycanBuilderSVG()
    gctp = pygly.GlycanFormatter.GlycoCTFormat()
    wp   = pygly.GlycanFormatter.WURCS20Format()
    glyeq  = pygly.alignment.GlycanImageEqual()
    gtc  = pygly.GlycanResource.GlyTouCanNoPrefetch()
    def highlightsvg(self, svgfile, glyseq, highlight, style='outline'):
        svg = open(svgfile).read()
        try:
            gly1 = self.gbsp.toGlycan(svg)
        except pygly.GlycanFormatterExceptions.GlycanParseError:
            gly1 = None
        except:
            traceback.print_exc(file=sys.stderr)
            gly1 = None
        if gly1 == None:
            self.output(2,"Highlight SVG: Can't parse the SVG image")
            return StringIO.StringIO(svg)
        # print(self.gctp.toStr(gly1))
        gly0 = None
        if glyseq.strip().startswith('RES'):
            try:
                gly0 = self.gctp.toGlycan(glyseq)
            except pygly.GlycanFormatterExceptions.GlycanParseError:
                gly0 = None
            except:
                traceback.print_exc(file=sys.stderr)
                gly0 = None
        elif glyseq.strip().startswith('WURCS'):
            try:
                gly0 = self.wp.toGlycan(glyseq)
            except pygly.GlycanFormatterExceptions.GlycanParseError:
                gly0 = None
            except:
                traceback.print_exc(file=sys.stderr)
                gly0 = None
        if gly0 == None:
            self.output(2,"Highlight SVG: Can't parse the provided sequence")
            return StringIO.StringIO(svg)
        # print(self.gctp.toStr(gly0))
        idmap = []
        if not self.glyeq.eq(gly0,gly1,idmap=idmap):
            self.output(2,"Highlight SVG: SVG and provided structures cannot be aligned")
            return StringIO.StringIO(svg)
        svgidmap = defaultdict(list)
        for f,t in idmap:
            svgidmap[f.id()].extend(t.external_descriptor_id().split(';'))
        for l in gly0.all_links():
            for parent_svgid in svgidmap[l.parent().id()]:
                for child_svgid in svgidmap[l.child().id()]:
                    svgidbase,parent_svgid1 = parent_svgid.rsplit(':',1)
                    svgidbase = svgidbase.split('-',1)[1]
                    child_svgid1 = child_svgid.rsplit(':',1)[1]
                    svgidmap[(l.parent().id(),l.child().id())].append('l-%s:%s,%s'%(svgidbase,parent_svgid1,child_svgid1))
        svg = svg.replace('<!--Generated by the Batik Graphics2D SVG Generator-->',"""
           <defs id="highlightcss">
              <style type="text/css"><![CDATA[
              %s
              ]]></style>
           </defs>
        """%(getattr(self,"highlight_css_"+style),))
        svg = svg.replace('<g>','<g class="glycanimage">')
        ids = map(int,filter(lambda id: '-' not in id, highlight.split(',')))
        linkids = filter(lambda id: '-' in id, highlight.split(','))
        if linkids != ['*-*']:
            linkids = map(lambda id: tuple(map(int,id.split('-'))),linkids)
        highlighted = set()
        for id in ids:
            for svgid in svgidmap[id]:
                # svgid = "r-1:%d"%(id,)
                if svgid not in highlighted:
                    svg = svg.replace(' ID="%s" '%(svgid,),' ID="%s" class="highlight highlight_mono" '%(svgid,))
                    highlighted.add(svgid)
                break # first "id" only...
            for id1 in ids:
                if linkids == ["*-*"] or (id,id1) in linkids:
                  for svgid in svgidmap[(id,id1)]:
                    if svgid not in highlighted:
                        svg = svg.replace(' ID="%s" '%(svgid,),' ID="%s" class="highlight highlight_link" '%(svgid,))
                        highlighted.add(svgid)
                    break # first "id" only...
        return StringIO.StringIO(svg)

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


    def image_generation(self, query, query_type, **option):

        result_path = ""

        imagegenerationwebservicebaseurl = "http://%s:%s/" % (self.host(), self.port())

        assert query_type in ["sequence", "accession", "task"]
        query = query.strip()

        # option = {}
        # option["notation"] = notation
        # option["display"] = display
        # option["image_format"] = image_format
        notation = option["notation"]
        display = option["display"]
        image_format = option["image_format"]

        if query_type == "accession":
            option["acc"] = query
        elif query_type == "sequence":
            option["seq"] = query


        mimetype = image_format
        if image_format == "svg":
            mimetype = "svg+xml"


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
                if image_format == "svg" and option.get("highlight"):
                    query_seq = query
                    if query_type == "accession":
                        if query not in self.cannonseq:
                            query_seq = self.gtc.getseq(query,format="wurcs")
                            self.cannonseq[query] = query_seq
                        else:
                            query_seq =  self.cannonseq[query]
                    try:
                        return flask.send_file(self.highlightsvg(result_path, query_seq,
                                                                 option.get('highlight'), 
                                                                 option.get('highlight_style','outline')), 
                                               mimetype='image/%s' % mimetype)
                    except:
                        traceback.print_exc(file=sys.stderr)
                        print >>sys.stderr, "Exception in highlightsvg..."
                        return flask.send_file(result_path, mimetype='image/%s' % mimetype)
                else:
                    return flask.send_file(result_path, mimetype='image/%s' % mimetype)

            # Nope, submit the task
            task_id = self.image_generation_submit(option)


        errors = ["Time out..."]
        for i in range(10):
            retrieveurl = imagegenerationwebservicebaseurl + "retrieve?task_id="
            retrieveurl += task_id

            response = urllib.request.urlopen(retrieveurl)
            response_obj = json.loads(response.read())[0]

            if response_obj["finished"]:
                errors = response_obj["error"]
                image_hash = response_obj["result"]
                image_format = response_obj["task"]["image_format"]
                query_acc = response_obj["task"].get("acc")
                query_seq = response_obj["task"].get("seq")
                result_path = os.path.join(self.data_folder, "hash", image_hash + "." + image_format)

                mimetype = image_format
                if image_format == "svg":
                    mimetype = "svg+xml"
                break

            time.sleep(2)


        if os.path.exists(result_path):
            if image_format == "svg" and option.get("highlight"):
                if query_acc:
                    if query_acc not in self.cannonseq:
                        query_seq = self.gtc.getseq(query_acc,format="wurcs")
                        self.cannonseq[query_acc] = query_seq
                    else:
                        query_seq = self.cannonseq[query_acc]
                try:
                    return flask.send_file(self.highlightsvg(result_path, query_seq, option.get('highlight'), 
                                                             option.get('highlight_style','outline')),
                                           mimetype='image/%s' % mimetype)
                except:
                    traceback.print_exc(file=sys.stderr)
                    print >>sys.stderr, "Exception in highlightsvg..."
                    return flask.send_file(result_path, mimetype='image/%s' % mimetype)
            else:
                return flask.send_file(result_path, mimetype='image/%s' % mimetype)
        else:
            return self.error_image(), 404

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
            return self.error_image(), 404

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
        def getimage():
            para = {}
            if flask.request.method == "GET":
                para = flask.request.args
            elif flask.request.method == "POST":
                para = flask.request.form
            else:
                return self.error_image(), 404

            p = {}
            for k in dict(para).keys():
                v = para.get(k)
                if v:
                    p[k] = str(v)

            query, query_type = "", ""
            if "seq" in p:
                query = p["seq"].strip()
                query_type = "sequence"
                if not (query.startswith('RES') or query.startswith('WURCS')):
                    newquery = None
                    if not newquery:
                        try:
                            gly = self.cp.toGlycan(query)
                            newquery = gly.glycoct()
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
                        return self.error_image(), 404
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

            if query == "" or query_type == "":
                return self.error_image(), 404

            p["notation"] = p.get("notation","snfg").lower()
            if p["notation"] not in ("snfg",):
                return self.error_image(), 404

            p["display"] = p.get("display","extended").lower()
            if p["display"] not in ("extended","compact"):
                return self.error_image(), 404

            p["image_format"] = p.get("image_format","png").lower()
            if p["image_format"] not in ("png","jpg","jpeg","svg"):
                return self.error_image(), 404

            for k in ("task_id","list_id","seq","acc"):
                if p.get(k) == None and k in p:
                    del p[k]

            # print >>sys.stderr, query, query_type, p

            return self.image_generation(query, query_type, **p)


if __name__ == '__main__':
    multiprocessing.freeze_support()

    glymage_app = Glymage()
    glymage_app.find_config("Glymage.ini")
    glymage_app.start()











