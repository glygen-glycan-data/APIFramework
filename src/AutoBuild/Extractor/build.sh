#!/bin/bash

tag=$1
if [ -z "$1" ]
  then
    echo "No tag is provided, NOT going to push to docker hub."
    tag="TEST"
fi


# switch to the latest commit
# COMMIT="b2342b83ab84ac3d0607c6cbe9c8962995eaf62e"
# COMMIT="94a9f575a5fa3b6320e4e1759537d87f05a2bc89"
# COMMIT="c936f09fc48ec44c0cf73c2b28f82f013edab65f"
# COMMIT="0b5de59b244798d8eb86e0e15e173e9087c9cd0f"
# COMMIT="57cfc0e413ec1917a09616f41c664e9fbe62008b"
# COMMIT="9e3d58b2da819cf7d782fa6cb401150bbf3af1b5"
# COMMIT="60b4a0e12f1f4dd4bdfb7ae32f8026eeaa715da9"
# COMMIT="d2c91a6a9390a48d1df39ff806d40830224a6638"
# COMMIT="a39630631ac399ddd95e236b16f68c23360aad2b"
# COMMIT="63158b9a9103da2ef25c655dd89ef1e7f7489a20"
# COMMIT="e985f36b6fceef63760372a365f0621372d4e806"
# COMMIT="273ca52f8dd3fa2e3eb2944b89ab50ecdd7ccedc"
# COMMIT="28f9552072ebb741a93bddaf41639c2e43a9f1c4"
COMMIT="8e9b1ebd57b95f560a99545a6b3d189f8e56b941"

wget https://github.com/glygen-glycan-data/GlycanImageExtract2/archive/${COMMIT}.zip -O ImgExtractor.zip
unzip -o ImgExtractor.zip

ImageExtract_DIR="./GlycanImageExtract2-${COMMIT}"

# Move only specific folders and files to current directory
mv ${ImageExtract_DIR}/BKGlycanExtractor ./
mv ${ImageExtract_DIR}/WebApplication ./
mv ${ImageExtract_DIR}/requirements.txt ./
mkdir -p ./static/files ./static/examples
if [ -d ${ImageExtract_DIR}/static/examples ]; then
  mv ${ImageExtract_DIR}/static/examples/* ./static/examples
fi

# Run the Python script to pull from Drive
python3 ./BKGlycanExtractor/config/getfromgdrive.py ./BKGlycanExtractor/config/

# docker build -t glyomics/extractor:$tag -t glyomics/extractor:latest ./
# $(date +%s) is the Unix timestamp
docker build --no-cache \
  --build-arg CACHEBUST=$(date +%s) \
  -t glyomics/extractor:$tag \
  -t glyomics/extractor:latest ./ 

# docker run -it -p 10981:10981 glyomics/extractor:latest

if [ "$tag" != "TEST" ];
  then
    docker push glyomics/extractor:$tag
    docker push glyomics/extractor:latest
fi


# Delete the directory and zip file
rm -rf ./GlycanImageExtract2-${COMMIT}
rm -rf ImgExtractor.zip
rm -rf WebApplication BKGlycanExtractor static requirements.txt 

