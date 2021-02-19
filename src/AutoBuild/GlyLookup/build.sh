#!/bin/bash

if [ -z "$1" ]
  then
    # Check for tag
    echo "Please provide the tag number, eg 0.1.1"
    exit
fi


cp -r ../../Application/GlyLookup/htmls ./htmls
cp ../../Application/GlyLookup/GlyLookup.* ./
cp ../../Application/GlyLookup/glycans.tsv ./


docker build -t glyomics/glylookup:$1 -t glyomics/glylookup:latest ./
docker run -p 10984:10984 glyomics/subsumption:latest

:'
docker run \
  --env WEBSERVICE_BASIC_HOST=0.0.0.0 \
  --env WEBSERVICE_BASIC_PORT=10981 \
  --env WEBSERVICE_BASIC_CPU_CORE=1 \
  -p 10981:10981 \
  glyomics/glylookup:$1

# Additional Options:
# --mount type=bind,source=/.../.../.../ConfigFileFolder,target=/root/appconfig
'

docker push glyomics/glylookup:$1
docker push glyomics/glylookup:latest


rm -rf htmls
rm GlyLookup.*



