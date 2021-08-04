#!/bin/bash

tag=$1
if [ -z "$1" ]
  then
    echo "No tag is provided, NOT going to push to docker hub."
    tag="TEST"
fi


wget https://github.com/glygen-glycan-data/PyGly/archive/master.zip -O PyGly.zip
unzip PyGly.zip
mv ./PyGly-master/pygly ./pygly
rm -rf PyGly-master
rm PyGly.zip

cp ../../APIFramework.py ./APIFramework.py

docker build -t glyomics/apiframework:$tag -t glyomics/apiframework:latest ./

if [ "$tag" != "TEST" ];
  then
    docker push glyomics/apiframework:$tag
    docker push glyomics/apiframework:latest
fi


rm -rf pygly
rm APIFramework.py



