#!/bin/env python2

import os
import sys
import shutil
import hashlib
# import pygly.GlycanImage
# import pygly.GlycanResource.GlyTouCan
# from pygly.GlycanFormatter import GlycoCTFormat, WURCS20Format

image_home = "./image/"

# wp = WURCS20Format()
# gp = GlycoCTFormat()


seqhashtable = open(image_home + "shash2acc.tsv")
imagetable   = open(image_home + "imageinfo.tsv")


shash2acc = {}
for l in seqhashtable.read().strip().split("\n"):
    shash, acc = l.strip().split()
    if shash not in shash2acc:
        shash2acc[shash] = []
    shash2acc[shash].append(acc)



for notation in ["snfg"]:
    p = os.path.join(image_home, notation)
    if not os.path.exists(p):
        os.mkdir(p)

    for display in ["extended", "compact"]:
        p = os.path.join(image_home, notation, display)
        if not os.path.exists(p):
            os.mkdir(p)

i = 0
for l in imagetable.read().strip().split("\n"):
    shash, notation, display, extn, ihash = l.strip().split()

    if display == "normalinfo":
        display = "extended"

    src = os.path.join(image_home, "hash", ihash + "." + extn)
    src_abs = os.path.abspath(src)
    # i+=1
    # if i > 1000:
    #     break

    destination = [shash, ihash]
    try:
        destination += shash2acc[shash]
    except:
        pass


    for t in destination:
        dst = os.path.join(image_home, notation, display, t + "." + extn)
        dst_abs = os.path.abspath(dst)

        try:
            os.link(src_abs, dst_abs)
            # os.symlink(src, dst)
        except:
            continue

            print src_abs
            print dst_abs
            print


    # print shash, notation, display
    # print src
    # print dst1, dst2, dst3

# shutil.rmtree(os.path.join(image_home, "hash"))








