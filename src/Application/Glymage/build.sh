#!/bin/bash

if [ -z "$1" ]
  then
    # Check for tag
    echo "Please provide the tag number, eg 0.0.1"
    exit
fi


docker build -t glyomics/glymage:$1 -t glyomics/glymage:latest ./

docker push glyomics/glymage:$1
docker push glyomics/glymage:latest

# docker run -p 10985:10985 --user 1000:1000 glyomics/glymage:latest

# docker build -t wenjin27/test:$1 ./
# docker run -p 10985:10985 --user 1000:1000 wenjin27/test:$1


