#!/bin/sh

set -x
# Xvfb :1 &
# XSCR=$!
# export DISPLAY=localhost:1.0

DOCKER="docker run -d --rm -u `id -u`:`id -g` -v `pwd`/work:/work glyomics/apiframework:latest"
function dockerrun() {
  CID=`$DOCKER $@`
  docker logs -f $CID
  # docker wait $CID
}

PYSCR="python2 pygly-scripts"
SHSCR="pygly-scripts"
DUMPSEQ="$PYSCR/dumpgtcseq.py"
ALLIMG="$SHSCR/allimg.sh"
CREJSON="$PYSCR/resmap_tojson.py"
JSONMOTIF="$PYSCR/resmap_motifaligntojson.py"
JSONENZ="$PYSCR/resmap_sandboxtojson.py"

docker pull glyomics/apiframework:latest
mkdir -p work/wurcs work/glycoct work/genglycoct

if [ "$1" != "json" ]; then
  dockerrun $DUMPSEQ /work/wurcs
  dockerrun $ALLIMG -N 20 -P 2 -n snfg -d normalinfo -f png -o /work/snfg/extended /work/wurcs
  dockerrun $ALLIMG -N 20 -P 2 -n snfg -d compact -f png -o /work/snfg/compact /work/wurcs
  dockerrun $ALLIMG -N 20 -P 2 -n snfg -d normalinfo -f svg -o /work/snfg/extended /work/wurcs
  dockerrun $ALLIMG -N 20 -P 2 -n snfg -d compact -f svg -o /work/snfg/compact /work/wurcs
  dockerrun $DUMPSEQ /work/glycoct
  dockerrun $ALLIMG -N 20 -P 2 -n snfg -d normalinfo -f png -o /work/snfg/extended /work/glycoct
  dockerrun $ALLIMG -N 20 -P 2 -n snfg -d compact -f png -o /work/snfg/compact /work/glycoct
  dockerrun $ALLIMG -N 20 -P 2 -n snfg -d normalinfo -f svg -o /work/snfg/extended /work/glycoct
  dockerrun $ALLIMG -N 20 -P 2 -n snfg -d compact -f svg -o /work/snfg/compact /work/glycoct
  dockerrun $DUMPSEQ /work/genglycoct
  dockerrun $ALLIMG -N 20 -P 2 -n snfg -d normalinfo -f png -o /work/snfg/extended /work/genglycoct
  dockerrun $ALLIMG -N 20 -P 2 -n snfg -d compact -f png -o /work/snfg/compact /work/genglycoct
  dockerrun $ALLIMG -N 20 -P 2 -n snfg -d normalinfo -f svg -o /work/snfg/extended /work/genglycoct
  dockerrun $ALLIMG -N 20 -P 2 -n snfg -d compact -f svg -o /work/snfg/compact /work/genglycoct
fi

# kill $XSCR

dockerrun $CREJSON /work/wurcs /work/snfg/extended /work/snfg/extended
dockerrun $CREJSON /work/wurcs /work/snfg/compact /work/snfg/compact
dockerrun $JSONENZ /work/snfg/extended
dockerrun $JSONENZ /work/snfg/compact
dockerrun $JSONMOTIF /work/snfg/extended
dockerrun $JSONMOTIF /work/snfg/compact

CURDIR=`pwd`
rm -rf image/hash
( cd work; python2 $CURDIR/image2hash.py ../image/hash )
rm -rf image/snfg
python2 $CURDIR/link.py
( cd image; tar czf image.tgz hash snfg error.png error.json imageinfo.tsv shash2acc.tsv cannonseq.tsv )
