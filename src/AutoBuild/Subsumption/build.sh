#!/bin/bash

tag=$1
if [ -z "$1" ]
  then
    echo "No tag is provided, NOT going to push to docker hub."
    tag="TEST"
fi


cp -r ../../Application/Subsumption/htmls ./htmls
cp ../../Application/Subsumption/Subsumption.* ./
cp ../../Application/Subsumption/glycans.tsv ./


docker build -t glyomics/subsumption:$tag -t glyomics/subsumption:latest ./
# docker run -p 10984:10984 glyomics/subsumption:latest

if [ "$tag" != "TEST" ];
  then
    docker push glyomics/subsumption:$tag
    docker push glyomics/subsumption:latest
fi



rm -rf htmls
rm Subsumption.*
rm glycans.tsv

