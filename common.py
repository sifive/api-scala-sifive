
import os
import sys
import time
import subprocess

def directory():
    return os.path.dirname(os.path.realpath(__file__))

def pid_file():
    return "{}/.bloop_timeout.pid".format(directory())

# FIXME - use actual install
def bloop_executable():
    return "{}/../scala/bloop".format(directory())

# FIXME - use actual install
def bloop_launcher():
    return "{}/../scala/blp-server".format(directory())

# TODO, can we get this directly from bloop_timeout itself?
def timeout_executable():
    return "{}/bloop_timeout".format(directory())

