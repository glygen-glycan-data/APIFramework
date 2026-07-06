#!/bin/bash

tag=$1
if [ -z "$1" ]
  then
    echo "No tag is provided, NOT going to push to docker hub."
    tag="TEST"
fi

cp -r -L ../../Application/Substructure/htmls ./htmls
cp ../../Application/Substructure/Substructure.* ./
cp ../../Application/Substructure/*.tsv ./


docker build --build-arg CACHEBUSTER=`date +%s` -t glyomics/substructure:$tag -t glyomics/substructure:latest ./

if [ "$tag" != "TEST" ];
  then
    docker push glyomics/substructure:$tag
    docker push glyomics/substructure:latest
fi

rm -rf htmls
rm Substructure.*
rm *.tsv


