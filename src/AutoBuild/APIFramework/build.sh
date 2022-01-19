#!/bin/bash

tag=$1
if [ -z "$1" ]; then
    echo "No tag is provided, NOT going to push to docker hub."
    tag="TEST"
fi


# COMMIT="master"
# COMMIT="512ee883e848d0aa0eeb02ec3acd2ec8fe7ae9f5"
# COMMIT="5716c270f441bb08b77009b838e08f7e67ad74bf"
COMMIT="957e634483c5189b5f1907dee5c1df7dccfd8187"
wget https://github.com/glygen-glycan-data/PyGly/archive/${COMMIT}.zip -O PyGly.zip
unzip PyGly.zip
mv ./PyGly-$COMMIT/pygly ./pygly
mv ./PyGly-$COMMIT/scripts ./pygly-scripts
rm -rf PyGly-$COMMIT
rm PyGly.zip

cp ../../APIFramework.py ./APIFramework.py

docker build -t glyomics/apiframework:$tag -t glyomics/apiframework:latest ./

if [ "$tag" != "TEST" ]; then
    docker push glyomics/apiframework:$tag
    docker push glyomics/apiframework:latest
fi


rm -rf pygly pygly-scripts
rm APIFramework.py



