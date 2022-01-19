#!/bin/sh

set -x
Xvfb :1 &
XSCR=$!
export DISPLAY=localhost:1.0

DOCKER="docker run --rm -it -u `id -u`:`id -g` -v `pwd`/work:/work glyomics/apiframework:latest"
PYSCR="$DOCKER python2 pygly-scripts"
SHSCR="$DOCKER pygly-scripts"
DUMPSEQ="$PYSCR/dumpgtcseq.py"
ALLIMG="$SHSCR/allimg.sh"

mkdir -p work/wurcs work/glycoct work/genglycoct
$DUMPSEQ /work/wurcs
$ALLIMG -N 20 -P 2 -n snfg -d normalinfo -f png -o /work/snfg/extended /work/wurcs
$ALLIMG -N 20 -P 2 -n snfg -d compact -f png -o /work/snfg/compact /work/wurcs
$DUMPSEQ /work/glycoct
$ALLIMG -N 20 -P 2 -n snfg -d normalinfo -f png -o /work/snfg/extended /work/glycoct
$ALLIMG -N 20 -P 2 -n snfg -d compact -f png -o /work/snfg/compact /work/glycoct
$DUMPSEQ /work/genglycoct
$ALLIMG -N 20 -P 2 -n snfg -d normalinfo -f png -o /work/snfg/extended /work/genglycoct
$ALLIMG -N 20 -P 2 -n snfg -d compact -f png -o /work/snfg/compact /work/genglycoct

kill $XSCR

CURDIR=`pwd`
rm -rf image/hash
( cd work; python2 $CURDIR/image2hash.py ../image/hash )
rm -rf image/snfg
python2 $CURDIR/link.py
( cd image; tar czf image.tgz hash snfg error.png imageinfo.tsv shash2acc.tsv )
