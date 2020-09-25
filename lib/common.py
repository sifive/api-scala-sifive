
import os
import argparse

def is_existing_dir(arg):
    if not os.path.isdir(arg):
        msg = "Directory {} does not exist!".format(arg)
        raise argparse.ArgumentTypeError(msg)
    else:
        return arg


def is_existing_file(arg):
    if not os.path.isfile(arg):
        msg = "File {} does not exist!".format(arg)
        raise argparse.ArgumentTypeError(msg)
    else:
        return arg
