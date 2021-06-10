#!/bin/bash

if [ -z "$1" ]
  then
    # Check for tag
    echo "Please provide the tag number, eg 0.1.1"
    exit
fi


cp -r ../../Application/GlycanConverter/htmls ./htmls
cp ../../Application/GlycanConverter/GlycanConverter.* ./


docker build -t glyomics/glycanconverter:$1 -t glyomics/glycanconverter:latest ./
# docker run -p 10986:10986 glyomics/glycanconverter:latest

docker push glyomics/glycanconverter:$1
docker push glyomics/glycanconverter:latest


rm -rf htmls
rm GlycanConverter.*


