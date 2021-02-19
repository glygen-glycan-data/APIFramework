#!/bin/bash

if [ -z "$1" ]
  then
    # Check for tag
    echo "Please provide the tag number, eg 0.0.1"
    exit
fi


cp -r ../../Application/Subsumption/htmls ./htmls
cp ../../Application/Subsumption/Subsumption.* ./
cp ../../Application/Subsumption/glycans.tsv ./


docker build -t glyomics/subsumption:$1 -t glyomics/subsumption:latest ./

:'
docker run \
  --env WEBSERVICE_BASIC_HOST=0.0.0.0 \
  --env WEBSERVICE_BASIC_PORT=10984 \
  --env WEBSERVICE_BASIC_CPU_CORE=1 \
  -p 10984:10984 \
  glyomics/subsumption:$1

# Additional Options:
# --mount type=bind,source=/.../.../.../ConfigFileFolder,target=/root/appconfig
'

docker push glyomics/subsumption:$1
docker push glyomics/subsumption:latest


rm -rf htmls
rm Subsumption.*
# TODO delete glycans.tsv



