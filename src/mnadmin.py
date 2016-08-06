#!/usr/bin/env python3

import argparse
import sys
import os
import subprocess

DFLT_CONFIG_FILE=os.path.abspath(
    os.path.expanduser('~/.makenovel/config'))
CURRDIR=os.path.abspath(".")

parser = argparse.ArgumentParser(description="MakeNovel admin command line utility")

parser.add_argument("name", nargs=1)
parser.add_argument("-t", "--title", nargs=1)
parser.add_argument("-c", "--config", nargs=1,
    help="makenovel configuration file. Default is %s" % DFLT_CONFIG_fILE,
    default=DFLT_CONFIG_FILE)
parser.add_argument("-p", "--path", nargs=1,
    help="Alternative location for this project",
    default = CURRDIR)

def create_project(name, title):
    projdir=os.path.join(CURRDIR, name)
    os.makedirs(projdir)
    os.mkdirs(os.path.join(projdir, '.novel'))
    

def main():
    args = parser.parse_args(sys.argv[1:])
    create_project(
    )

if __name__=="__main__":
    main()
