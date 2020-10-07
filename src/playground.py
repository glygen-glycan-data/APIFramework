
import os
import sys
import time, datetime
import json
import flask
import atexit
import hashlib
import ConfigParser
import multiprocessing, Queue


def workerfunction():
    # raise NotImplemented
    print "ok"
    time.sleep(1)
    print "done"


deamon_process_pool = []
for i in range(10):
    p = multiprocessing.Process(target=workerfunction)
    deamon_process_pool.append(p)



for p in deamon_process_pool:
    p.start()




