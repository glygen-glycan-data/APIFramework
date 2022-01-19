#!/bin/bash

python link.py
find image -type d -exec chmod a+rwx {} \;
