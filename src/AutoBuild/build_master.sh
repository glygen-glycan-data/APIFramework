#!/bin/bash

if [ -z "$1" ]
  then
    # Check for tag
    echo "Please provide the tag number, eg 0.0.1"
    exit
fi

if [[ ! ("$(pwd)" =~ "/AutoBuild") ]]; then
  # Check for executing folder
  exit
fi


cd ./APIFramework
echo "BUILDING: APIFramework Base"
./build.sh $1
cd ..

for d in $(find ./ -maxdepth 1 -type d)
do
  if [ $d = "./" ]; then
    # Current folder
    continue
  fi

  if [ $d = ".//APIFramework" ]; then
    # Build base docker image before everything else
    continue
  fi

  echo "BUILDING:" $d

  cd $d
  # pwd
  ./build.sh $1
  cd ..

done

