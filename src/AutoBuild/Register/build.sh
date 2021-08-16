#!/bin/bash

tag=$1
if [ -z "$1" ]
  then
    echo "No tag is provided, NOT going to push to docker hub."
    tag="TEST"
fi


cp -r ../../Application/Register/htmls ./htmls
cp ../../Application/Register/Register.* ./


docker build -t glyomics/register:$tag -t glyomics/register:latest ./
# docker run -p 10987:10987 glyomics/register:latest

if [ "$tag" != "TEST" ];
  then
    docker push glyomics/register:$tag
    docker push glyomics/register:latest
fi



rm -rf htmls
rm Register.*

