#!/bin/bash
# This script is located inside the Extractor folder, but it sets permissions
# for the WebApplication subdirectory which will be pulled via the github commit.

# Set full permissions for the WebApplication folder
chmod -R 0777 /code/WebApplication

# Ensure input folder exists and set permissions
mkdir -p /code/WebApplication/input
chmod -R 0777 /code/WebApplication/input

# Ensure static/files folder exists and set permissions
mkdir -p /code/WebApplication/static/files
chmod -R 0777 /code/WebApplication/static/files