#!/bin/bash

tag=$1
if [ -z "$1" ]
  then
    echo "No tag is provided, NOT going to push to docker hub."
    tag="TEST"
fi


cp -r -L ../../Application/Converter/htmls ./htmls
cp ../../Application/Converter/Converter.* ./


docker build -t glyomics/converter:$tag -t glyomics/converter:latest ./
# docker run -p 10986:10986 glyomics/converter:latest

if [ "$tag" != "TEST" ];
  then
    docker push glyomics/converter:$tag
    docker push glyomics/converter:latest
fi



rm -rf htmls
rm Converter.*


