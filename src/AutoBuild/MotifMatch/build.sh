#!/bin/bash

if [ -z "$1" ]
  then
    # Check for tag
    echo "Please provide the tag number, eg 0.0.1"
    exit
fi


cp -r ../../Application/MotifMatch/htmls ./htmls
cp ../../Application/MotifMatch/MotifMatch.* ./
cp ../../Application/MotifMatch/motif.tsv ./


docker build -t glyomics/motifmatch:$1 -t glyomics/motifmatch:latest ./

docker push glyomics/motifmatch:$1
docker push glyomics/motifmatch:latest


rm -rf htmls
rm MotifMatch.*
rm motif.tsv


