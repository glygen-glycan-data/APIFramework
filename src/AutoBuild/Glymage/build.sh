#!/bin/bash

tag=$1
if [ -z "$1" ]
  then
    echo "No tag is provided, NOT going to push to docker hub."
    tag="TEST"
fi


cp ../../Application/Glymage/Glymage.* ./
mkdir -p ./image ./htmls
cp  ../../Application/Glymage/htmls/*.html ./htmls
cp  ../../Application/Glymage/image/image.tgz ./image

docker build -t glyomics/glymage:$tag -t glyomics/glymage:latest ./
# docker run -p 10986:10986 glyomics/glymage:latest

if [ "$tag" != "TEST" ];
  then
    docker push glyomics/glymage:$tag
    docker push glyomics/glymage:latest
fi

rm Glymage.*
rm -rf htmls
rm -rf image
