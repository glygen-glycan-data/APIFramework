#!/bin/bash

chmod 0777 ./
mkdir /data
chmod 0777 /data

mkdir /data/config

python fixenv.py
apt-get update && apt-get install -y openjdk-11-jre-headless && apt-get clean;


