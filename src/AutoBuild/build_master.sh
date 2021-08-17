#!/bin/bash

tag=$1
if [ -z "$1" ]
  then
    echo "No tag is provided, NOT going to push to docker hub."
    tag="TEST"
fi

if [[ ! ("$(pwd)" =~ "/AutoBuild") ]]; then
  # Check for executing folder
  exit
fi


cd ./APIFramework
echo "BUILDING: APIFramework Base"
./build.sh $tag
cd ..

for d in $(find . -maxdepth 1 -type d)
do
  if [ $d = "." ]; then
    # Current folder
    continue
  fi

  if [ $d = "./APIFramework" ]; then
    # Build base docker image before everything else
    continue
  fi

  echo "BUILDING:" $d

  cd $d
  # pwd
  ./build.sh $tag
  cd ..

done

