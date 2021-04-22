#!/bin/bash

if [ -z "$1" ]
  then
    # Check for tag
    echo "Please provide the tag number, eg 0.0.1"
    exit
fi


cp -r ../../Application/Substructure/htmls ./htmls
cp ../../Application/Substructure/Substructure.* ./
cp ../../Application/Substructure/*.tsv ./


docker build -t glyomics/substructure:$1 -t glyomics/substructure:latest ./
# docker run -p 10983:10983 glyomics/substructure:latest

docker push glyomics/substructure:$1
docker push glyomics/substructure:latest


rm -rf htmls
rm Substructure.*
rm *.tsv


