#!/bin/bash

if [ -z "$1" ]
  then
    # Check for tag
    echo "Please provide the tag number, eg 0.0.1"
    exit
fi


wget https://github.com/glygen-glycan-data/PyGly/archive/master.zip -O PyGly.zip
unzip PyGly.zip
mv ./PyGly-master/pygly ./pygly
rm -rf PyGly-master
rm PyGly.zip

cp ../../APIFramework.py ./APIFramework.py

docker build -t glyomics/apiframework:$1 -t glyomics/apiframework:latest ./


# Test Run
# docker run glyomics/apiframework:$1

# Addtional Options
# --env WEBSERVICE_BASIC_HOST=0.0.0.0
# --env WEBSERVICE_BASIC_PORT=10999
# --env WEBSERVICE_BASIC_CPU_CORE=1
# --mount type=bind,source=/PATH/TO/CONFIG/FOLDER,target=/root/appconfig

docker push glyomics/apiframework:$1
docker push glyomics/apiframework:latest

rm -rf pygly
rm APIFramework.py



