
import os
import sys
import flask
import pygly.alignment
import APIFramework



print "APIFramework base Docker Image build test complete"

# TEST env pick up
for k in ["WEBSERVICE_BASIC_HOST", "WEBSERVICE_BASIC_PORT", "WEBSERVICE_BASIC_CPU_CORE"]:
    if k in os.environ:
        print k, os.environ[k]


# TEST mount
if os.path.exists("/root/appconfig"):
    print os.listdir("/root/appconfig")
else:
    print "/root/appconfig doesn't exist"




