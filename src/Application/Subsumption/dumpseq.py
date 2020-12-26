
import os
import re
import sys
import urllib

import pygly.GNOme
import pygly.GlycanFormatter
import pygly.GlycanResource.GlyTouCan


output_file = open("glycans.tsv", "w")

gtc_acc_pattern = re.compile(r"^G\d{5}\w{2}$")

mass_lut = {}
header = True
for line in urllib.urlopen("https://raw.githubusercontent.com/glygen-glycan-data/GNOme/master/data/mass_lookup_2decimal"):
    l = line.strip()
    if header:
        header = False
        continue

    mid, mass = l.split()
    mass_lut[mid] = mass





all_wurcs = {}

wp = pygly.GlycanFormatter.WURCS20Format()
gtc = pygly.GlycanResource.GlyTouCan()
for acc, f, s in gtc.allseq(format="wurcs"):
    try:
        wp.toGlycan(s)
    except:
        continue

    all_wurcs[acc] = s



lines = []


gnome = pygly.GNOme.GNOme()
accs = set()
for acc in gnome.nodes():
    if acc == "00000001":
        continue

    if gtc_acc_pattern.findall(acc):
        accs.add(acc)
    else:
        assert acc in mass_lut

        for gacc in gnome.descendants(acc):
            if gacc not in all_wurcs:
                print gacc, "wurcs issue!"
                continue

            lvl = gnome.level(gacc)
            # print gacc, lvl
            assert lvl

            lines.append("%s\t%s\t%s\t%s\n" % (gacc, mass_lut[acc], lvl, all_wurcs[gacc]))


for l in sorted(lines):
    output_file.write(l)



print len(accs)

