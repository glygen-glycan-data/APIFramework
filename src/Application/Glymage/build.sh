#!/bin/bash

docker pull glyomics/apiframework:latest
# docker build -t glyomics/glymage:$1 -t glyomics/glymage:latest ./

# docker push glyomics/glymage:$1
# docker push glyomics/glymage:latest

# docker run -p 10989:10989 --user 1000:1000 glyomics/glymage:latest

docker build -t glymage_testing ./
docker run -p 10989:10985 --user 1000:1000 glymage_testing


