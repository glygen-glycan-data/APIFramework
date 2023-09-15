#!/bin/bash

set -x

tag=$1
if [ -z "$1" ]; then
    echo "No tag is provided, NOT going to push to docker hub."
    tag="TEST"
fi


# COMMIT="master"
# COMMIT="512ee883e848d0aa0eeb02ec3acd2ec8fe7ae9f5"
# COMMIT="5716c270f441bb08b77009b838e08f7e67ad74bf"
# COMMIT="957e634483c5189b5f1907dee5c1df7dccfd8187"
# COMMIT="3c5c9642b77bd0dba67bee707464f0c716ef716a"
# COMMIT="bc58d18ba8e80b569b33021480fb26d9a4b9327a"
# COMMIT="193eac123a73881e5a6b7e05e6bda78f26070d89"
# COMMIT="da382923418a0dec3fdc1b33ed9385502069704f"
# COMMIT="31f6e7e1c386b072686a7011a2f036e3268c670c"
# COMMIT="486a587ff6b6e8abbf947f01acf2448aafd1c0b2"
# COMMIT="d8cf33040dfd1ca6ab32a25bed55316ba7168feb"
# COMMIT="cc0250fbedbfbe453b78a659ec11a91e02f07585"
# COMMIT="88b7cfcdbed7e73bf1e85d1ec30dc14ff59c0b68"
# COMMIT="568ccaea8298ae964f716f769b6dc07eb5b0d57a"
# COMMIT="9bdb4af834c217be07261f62d66110da88f85f3c"
# COMMIT="9a73cd8a3a1c279defb57ce047e135a52bff68cc"
COMMIT="81591fff9b03b25036f018bbf1e23c024ffb629b"

wget https://github.com/glygen-glycan-data/PyGly/archive/${COMMIT}.zip -O PyGly.zip
unzip PyGly.zip
mv ./PyGly-$COMMIT/pygly ./pygly
mv ./PyGly-$COMMIT/scripts ./pygly-scripts
rm -rf PyGly-$COMMIT
rm PyGly.zip

cp ../../APIFramework.py ./APIFramework.py

if [ "$tag" != "TEST" ]; then
    docker build -t glyomics/apiframework:$tag -t glyomics/apiframework:latest ./
    docker push glyomics/apiframework:$tag
    docker push glyomics/apiframework:latest
else
    docker build -t glyomics/apiframework:latest ./
fi

rm -rf pygly pygly-scripts
rm APIFramework.py



