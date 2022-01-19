
import os
import sys
import shutil
import hashlib
import re
# import pygly.GlycanResource.GlyTouCan
# from pygly.GlycanFormatter import GlycoCTFormat, WURCS20Format


# wp = WURCS20Format()
# gp = GlycoCTFormat()
# gtc = pygly.GlycanResource.GlyTouCan()


def s2h(s):
    return hashlib.md5(s).hexdigest()


seq_hash_to_acc = {}
acc_to_seq_hash = {}

# Key: sequence hash + image options -> Value: images hash
seqhash_to_imagehash = {}

for seqtype in ("wurcs","glycoct"):
    for dirpath, dirnames, filenames in os.walk("./"+seqtype):
	for f in filenames:
            acc,extn = f.rsplit('.',1)
	    if extn != 'txt':
		continue
            if not re.search(r'^G[0-9]{5}[A-Z]{2}$',acc):
		continue
            s = open(os.path.join(dirpath,f)).read()
            h = s2h(s)
            seq_hash_to_acc[h] = acc
            if acc not in acc_to_seq_hash:
                acc_to_seq_hash[acc] = []
            acc_to_seq_hash[acc].append(h)

try:
    os.mkdir(sys.argv[1])
except:
    pass



for dirpath, dirnames, filenames in os.walk("./snfg/"):

    display = dirpath.split("/")[-1]
    if "hash" in dirpath:
        continue

    for fn in filenames:

        if not fn.endswith(".png"):
            continue

        acc = fn.split('.',1)[0]

        fp = os.path.join(dirpath, fn)

        imgstr = open(fp).read()
        imgh = s2h(imgstr)


        fph = sys.argv[1] + "/%s.png"%imgh
        if not os.path.exists(fph):
            shutil.copyfile(fp, fph)

        if acc not in acc_to_seq_hash:
            continue

        for sh in acc_to_seq_hash[acc]:
            seqhash_to_imagehash[(sh, "snfg", display)] = imgh


seqhashtable = open(sys.argv[1] + "/shash2acc.tsv", "w")
for acc, shs in acc_to_seq_hash.items():
    for sh in shs:
        seqhashtable.write("%s\t%s\n" % (sh, acc))
seqhashtable.close()


imagetable = open(sys.argv[1] + "/imageinfo.tsv", "w")
for key, ih in seqhash_to_imagehash.items():
    imagetable.write("%s\t%s\n" % ("\t".join(key), ih))
imagetable.close()




