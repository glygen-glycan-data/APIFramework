import os
import sys
import json
from pygly.GlycanResource.GlyCosmos import GlyCosmos
from pygly.GlycanFormatter import WURCS20Format

def round2str(n):
    return str(round(n, 2))


gtc = GlyCosmos()
wp = WURCS20Format()
f1 = open("glycans_all.tsv", "w")
for acc,f,s in gtc.allseq():

    if f != "wurcs":
        continue

    try:
        g = wp.toGlycan(s)
        mass = round2str(g.underivitized_molecular_weight())
        # g.underivitized_molecular_weight()
    except:
        continue

    f1.write("%s\t%s\t%s\n" % (acc, mass, s))

f1.close()


