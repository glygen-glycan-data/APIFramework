#!/bin/env python3.12

import os
import sys
import time
import multiprocessing
import traceback

from APIFramework import APIFramework, APIFrameworkWithFrontEnd, queue

import pygly.alignment
from pygly.GlycanResource.GlyTouCan import GlyTouCanNoCache, GlyTouCan

from pygly.GlycanFormatter import IUPACGlycamFormat, GlycoCTFormat, IUPACLinearFormat
from pygly.CompositionFormatter import CompositionFormat
from pygly.GlycanMultiParser import GlycanMultiParser, GlycanParseError

def round2str(n):
    return str(round(n, 2))


class Converter(APIFrameworkWithFrontEnd):

    task_params = dict(seq=None,format=None)

    def worker(self, pid):

        self.start_worker(pid)

        gmp = GlycanMultiParser()
        gp = GlycoCTFormat()
        cp = CompositionFormat()
        iupac_parser = IUPACLinearFormat()
        glycam_parser = IUPACGlycamFormat()

        self.worker_ready()

        while True:
            task_detail = self.get_task()

            try:
                seq = str(task_detail["seq"])
                request_format = str(task_detail["format"]).lower()
            except (TypeError,ValueError,AttributeError,KeyError):
                self.put_error("Required parameters are missing")
                continue
                
            result = ""

            try:
                query_glycan = gmp.toGlycan(seq)
            except (GlycanParseError,RuntimeError,TypeError):
                self.put_error("Unable to parse")
                continue

            try:
                if request_format == "glycam":
                    if not query_glycan.has_root():
                        self.put_error("Cannot make Glycam sequence from composition")
                        continue
                    else:
                        result = glycam_parser.toStr(query_glycan)
                elif request_format == "iupac":
                    if not query_glycan.has_root():
                        self.put_error("Cannot make IUPAC sequence from composition")
                        continue
                    else:
                        result = iupac_parser.toStr(query_glycan)
                elif request_format == "composition":
                    comp = query_glycan.iupac_composition(floating_substituents=True, 
                                                          aggregate_basecomposition=False)
                    compstr = ""
                    for k,v in sorted(comp.items()):
                        if v > 0 and k != "Count":
                            compstr += "%s(%d)"%(k,v)
                    result = compstr
                elif request_format == "glycoct":
                    result = gp.toStr(query_glycan)
                else:
                    self.put_error("Format %s is not supported" % request_format)
                    continue
            except:
                traceback.print_exc()
                self.put_error("Unexpected error during conversion")
                continue

            result = result.strip()
            self.put_result(result)

if __name__ == '__main__':
    multiprocessing.freeze_support()

    converter_app = Converter()
    converter_app.find_config("Converter.ini")
    converter_app.start()






