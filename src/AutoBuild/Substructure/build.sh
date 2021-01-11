#!/bin/bash

if [ -z "$1" ]
  then
    # Check for tag
    echo "Please provide the tag number, eg 0.0.1"
    exit
fi


cp -r ../../Application/Substructure/htmls ./htmls
cp ../../Application/Substructure/Substructure.* ./


docker build -t glyomics/substructure:$1 -t glyomics/substructure:latest ./

:'
docker run \
  --env WEBSERVICE_BASIC_HOST=0.0.0.0 \
  --env WEBSERVICE_BASIC_PORT=10982 \
  --env WEBSERVICE_BASIC_CPU_CORE=1 \
  -p 10982:10982 \
  glyomics/motifmatch:$1

# Additional Options:
# --mount type=bind,source=/.../.../.../ConfigFileFolder,target=/root/appconfig
'

docker push glyomics/substructure:$1
docker push glyomics/substructure:latest


rm -rf htmls
rm Substructure.*



