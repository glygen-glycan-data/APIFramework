#!/bin/bash

tag=$1
if [ -z "$1" ]
  then
    echo "No tag is provided, NOT going to push to docker hub."
    tag="TEST"
fi


cp -r -L ../../Application/GlyLookup/htmls ./htmls
cp ../../Application/GlyLookup/GlyLookup.* ./
cp ../../Application/GlyLookup/glycans.tsv ./


docker build -t glyomics/glylookup:$tag -t glyomics/glylookup:latest ./
# docker run -p 10981:10981 glyomics/glylookup:latest

if [ "$tag" != "TEST" ];
  then
    docker push glyomics/glylookup:$tag
    docker push glyomics/glylookup:latest
fi



rm -rf htmls
rm GlyLookup.*
rm glycans.tsv


