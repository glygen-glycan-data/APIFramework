#!/bin/bash

if [ -z "$1" ]
  then
    # Check for tag
    echo "Please provide the tag number, eg 0.1.1"
    exit
fi


cp -r ../../Application/Converter/htmls ./htmls
cp ../../Application/Converter/Converter.* ./


docker build -t glyomics/converter:$1 -t glyomics/converter:latest ./
# docker run -p 10986:10986 glyomics/converter:latest

docker push glyomics/converter:$1
docker push glyomics/converter:latest


rm -rf htmls
rm Converter.*


