#!/bin/env python3.12

import os
import sys
import time
import re
import traceback
from collections import defaultdict
import multiprocessing
from APIFramework import APIFramework, APIFrameworkWithFrontEnd, queue

import pygly.alignment
from pygly.GlycanResource.GlyTouCan import GlyTouCanNoCache, GlyTouCan
from pygly.GlycanResource.GlyGen import GlyGen
from pygly.GlycanMultiParser import GlycanMultiParser, GlycanParseError
from pygly.Glycan import RepeatGlycanError

def round2str(n):
    return str(round(n, 2))

class GlyLookup(APIFrameworkWithFrontEnd):
    task_params = dict(seq=None)

    def worker(self, pid):

        self.start_worker(pid)

        glycan_file_path = self.get_filename_param("glycan_file_path")

        gmp = GlycanMultiParser()
        gie = pygly.alignment.GlycanEqual()

        wurcss = {}
        otherseq = defaultdict(list)
        member = defaultdict(list)
        glycan_by_mass = defaultdict(list)

        hash2acc = defaultdict(set)

        for line in open(glycan_file_path):

            try:
                acc, mass, wseq, gseq, glygen, xxx = line.strip().split("\t")
            except ValueError:
                acc, mass, wseq, gseq, xxx = line.strip().split("\t")
                glygen = ""

            gseq = gseq.replace("\\n", "\n")

            for s in [wseq, gseq]:
                if s != "":
                    h = self.str2hash(s)
                    if acc not in hash2acc[h]:
                        hash2acc[h].add(acc)

            wurcss[acc] = wseq
            for s in [gseq,]:
                if s != "":
                    otherseq[acc].append(dict(seq=s,hash=self.str2hash(s),format='GlycoCT',source='GlyTouCan:'+acc))

            if glygen == "true":
                member[acc].append("GlyGen:"+acc)

            if mass == "":
                continue

            glycan_by_mass[mass].append(acc)

        self.worker_ready()
        
        while True:
            task_detail = self.get_task()

            try:
                seq = str(task_detail["seq"])
            except (TypeError,ValueError,AttributeError,KeyError):
                self.put_error("Required parameters are missing")
                continue
                
            wurcsfromgtcacc = False
            if re.search(r'^G[0-9]{5}[A-Z]{2}$',seq):
                if seq in wurcss:
                    seq = wurcss[seq]
                    wurcsfromgtcacc = True
                else:
                    self.put_error("Unexpected GlyTouCan accession")
                    continue
                
            result = []

            if seq != None:
                seqh = self.str2hash(seq)
                for acc in sorted(hash2acc[seqh]):
                    result.append(acc)

            if len(result) == 0 and seq != None:
                try:
                    query_glycan = gmp.toGlycan(seq)
                except (GlycanParseError, RuntimeError,TypeError):
                    self.put_error("Unable to parse")
                    continue

                try:
                    query_glycan_mass = round2str(query_glycan.underivitized_molecular_weight())
                except (LookupError,RepeatGlycanError):
                    self.put_error("Error in calculating mass")
                    continue

                potential_accs = glycan_by_mass.get(query_glycan_mass,[])

                for acc in sorted(potential_accs):
                    glycan = gmp.toGlycan(wurcss[acc])
                    if gie.eq(query_glycan, glycan):
                        result.append(acc)
                        hash2acc[seqh].add(acc)

            elif len(result) > 0 and seq != None:
                self.worker_output("Multiple accessions match by sequence hash: %s."%(", ".join(sorted(result))))
                try:
                    query_glycan = gmp.toGlycan(seq)
                except GlycanParseError:
                    self.put_error("Unable to parse")
                    continue

                result1 = []
                for acc in result:
                    try:
                        glycan = gmp.toGlycan(wurcss[acc])
                    except GlycanParseError:
                        continue
                    if gie.eq(query_glycan, glycan):
                         result1.append(acc)
                if len(result1) > 0:
                    result = result1
                    if len(result1) > 1:
                        self.worker_output("Multiple sequence hash accessions are equal to the query: %s."%(", ".join(sorted(result))))
                else:
                    self.worker_output("No sequence hash accessions are equal to the query.")

            result1 = []
            for acc in result:
                r = dict(accession=acc,
                         sequences=[dict(seq=wurcss[acc],hash=self.str2hash(wurcss[acc]),format='WURCS',source='GlyTouCan:'+acc)]+otherseq[acc],
                         membership=['GlyTouCan:'+acc]+member[acc])
                if seq.startswith('RES'):
                    r['sequences'].append(dict(seq=seq,hash=seqh,format='GlycoCT',source='UserInput'))
                elif not wurcsfromgtcacc and seq.startswith('WURCS'):
                    r['sequences'].append(dict(seq=seq,hash=seqh,format='WURCS',source='UserInput'))
                result1.append(r)
            
            self.put_result(result1)

    def pre_start(self, para):

        ggacc = set(GlyGen().allglycans())
        gtc = GlyTouCanNoCache()
        gmp = GlycanMultiParser()

        file_path = self.autopath(para["glycan_file_path"])

        data = {}
        for acc, f, s in gtc.allseq():

            if f not in ["wurcs", "glycoct"]:
                continue

            s = s.strip()
            if " " in s:
                # Issue with some sequence...
                continue

            s = s.replace("\n", "\\n")
            if "\r" in s:
                # Issue with some sequence...
                # print acc
                continue

            if acc not in data:
                data[acc] = ["", "", "", "" ]

            if acc in ggacc:
                data[acc][3] = 'true'

            if f == "glycoct":
                data[acc][2] = s
            elif f == "wurcs":
                data[acc][1] = s

                try:
                    g = gmp.toGlycan(s)
                    mass = round2str(g.underivitized_molecular_weight())
                    data[acc][0] = mass
                except (GlycanParseError,LookupError,RepeatGlycanError):
                    continue

        f1 = open(self.autopath("tmp.txt", newfile=True), "w")
        for acc, d in data.items():
            line = "\t".join([acc] + d + ["END"])
            f1.write("%s\n" % (line))
        f1.close()

        if os.path.exists(file_path):
            os.remove(file_path)
        os.rename(self.autopath("tmp.txt", newfile=True), file_path)

if __name__ == '__main__':
    multiprocessing.freeze_support()

    glylookup_app = GlyLookup()
    glylookup_app.find_config("GlyLookup.ini")
    glylookup_app.start()

