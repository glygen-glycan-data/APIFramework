#!/bin/bash

set -x

tag=$1
if [ -z "$1" ]; then
    echo "No tag is provided, NOT going to push to docker hub."
    tag="TEST"
fi


# COMMIT="master"
# COMMIT="512ee883e848d0aa0eeb02ec3acd2ec8fe7ae9f5"
# COMMIT="5716c270f441bb08b77009b838e08f7e67ad74bf"
# COMMIT="957e634483c5189b5f1907dee5c1df7dccfd8187"
# COMMIT="3c5c9642b77bd0dba67bee707464f0c716ef716a"
# COMMIT="bc58d18ba8e80b569b33021480fb26d9a4b9327a"
COMMIT="193eac123a73881e5a6b7e05e6bda78f26070d89"

wget https://github.com/glygen-glycan-data/PyGly/archive/${COMMIT}.zip -O PyGly.zip
unzip PyGly.zip
mv ./PyGly-$COMMIT/pygly ./pygly
mv ./PyGly-$COMMIT/scripts ./pygly-scripts
rm -rf PyGly-$COMMIT
rm PyGly.zip

cp ../../APIFramework.py ./APIFramework.py

if [ "$tag" != "TEST" ]; then
    docker build -t glyomics/apiframework:$tag -t glyomics/apiframework:latest ./
    docker push glyomics/apiframework:$tag
    docker push glyomics/apiframework:latest
else
    docker build -t glyomics/apiframework:latest ./
fi

rm -rf pygly pygly-scripts
rm APIFramework.py



