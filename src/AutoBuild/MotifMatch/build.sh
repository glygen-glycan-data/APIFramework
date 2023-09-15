#!/bin/bash

tag=$1
if [ -z "$1" ]
  then
    echo "No tag is provided, NOT going to push to docker hub."
    tag="TEST"
fi


cp -r -L ../../Application/MotifMatch/htmls ./htmls
cp ../../Application/MotifMatch/MotifMatch.* ./
cp ../../Application/MotifMatch/motif.tsv ./


docker build -t glyomics/motifmatch:$tag -t glyomics/motifmatch:latest ./

if [ "$tag" != "TEST" ];
  then
    docker push glyomics/motifmatch:$tag
    docker push glyomics/motifmatch:latest
fi



rm -rf htmls
rm MotifMatch.*
rm motif.tsv


