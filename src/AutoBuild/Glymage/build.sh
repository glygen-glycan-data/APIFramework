#!/bin/bash

tag=$1
if [ -z "$1" ]
  then
    echo "No tag is provided, NOT going to push to docker hub."
    tag="TEST"
fi


cp ../../Application/Glymage/Glymage.* ./
cp -r -L ../../Application/Glymage/htmls ./htmls
mkdir -p ./js ./css ./demo ./image
cp ../../Application/Glymage/css/*.js ./js
cp ../../Application/Glymage/css/*.css ./css
cp ../../Application/Glymage/demo/*.html ./demo
cp ../../Application/Glymage/image/image.tgz ./image

docker build -t glyomics/glymage:$tag -t glyomics/glymage:latest ./
# docker run -p 10986:10986 glyomics/glymage:latest

if [ "$tag" != "TEST" ];
  then
    docker push glyomics/glymage:$tag
    docker push glyomics/glymage:latest
fi

rm Glymage.*
rm -rf htmls css js demo image
