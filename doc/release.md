# APIFramework Release Process

## Pre-requisite
1. wget
2. Docker
3. PyGly Package

## How to build
### Run build script
Execute [master build script](https://github.com/glygen-glycan-data/APIFramework/blob/main/src/AutoBuild/build_master.sh) in the terminal by:
```
# Provide the tag number in the following format
./build_master.sh 0.1.15
```
The script builds the base docker image first, and then build every other application automatically by going into subfolder and invoking the build.sh.

## Explanation

### Basics
Every container is tagged by both "latest" and your specified tag number.

### APIFramework base docker container
This is the base docker container for all the other applications, which derived from official python 2.7 container.
1. It installs required python packages like flask and rdflib.
2. It Embedded the PyGly/pygly into the environment
3. It fixes a few things in linux environments.
4. It installs the openjdk 11 (primarily for Glymage)

Note that the script will download the entire package as zip file from github. If new vital updates are pushed to PyGly, please wait several minutes before building the base container. GitHub usually need a few minutes to reflect the updates into zip file.


### Other simple applications
All other applications are built from base APIFramework container. Usually all it need to do is to add the app.py file, configuration file and related data files into the container.

### Glymage
Glymage requires [all images](https://github.com/glygen-glycan-data/APIFramework/releases/tag/V0.1.1-images) as critical dependency.
Because it contains so many small files, the copy operation from local hard drive into docker container and making hard links from accession and sequence hash takes tremendous amount of time. Usually 20~40 minutes.

#### Release steps:
1. Download all images into [this folder](https://github.com/glygen-glycan-data/APIFramework/tree/main/src/Application/Glymage/image), unzip it and delete it.
2. Execute build script in terminal
```
# Provide the tag number in the following format
./build.sh 0.1.15
```
3. Wait for it.


















