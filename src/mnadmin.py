#!/usr/bin/env python3

import argparse
import sys
import os
import subprocess
import shutil

DFLT_CONFIG_FILE=os.path.abspath(
    os.path.expanduser('~/.makenovel/config'))
CURRDIR = os.path.abspath('.')
MAKENOVEL_DIR=os.path.abspath(os.path.dirname(__file__))
NOVELFILE = os.path.join(MAKENOVEL_DIR, 'novel')
PARTSFILE = os.path.join(MAKENOVEL_DIR, 'parts.csv')
CHAPTERSFILE = os.path.join(MAKENOVEL_DIR, 'chapters.csv')
PLOTLINESFILE = os.path.join(MAKENOVEL_DIR, 'plotlines.csv')
VERSIONSFILE = os.path.join(MAKENOVEL_DIR, 'versions.csv')
DRAFTSFILE = os.path.join(MAKENOVEL_DIR, 'drafts.csv')

GIT='/usr/bin/git'

parser = argparse.ArgumentParser(description="MakeNovel admin command line utility")

parser.add_argument("name",
    help="What the directory will be named. Lower-case, no spaces is recommended." )
parser.add_argument("-t", "--title", required=True)
parser.add_argument("-c", "--config",
    help="makenovel configuration file. Default is %s" % DFLT_CONFIG_FILE,
    default=DFLT_CONFIG_FILE)
parser.add_argument("-p", "--path",
    help="Alternative location for this project",
    default=CURRDIR)
parser.add_argument("-b", "--branch",
    help="Name of this specific git branch")

def create_project(name, title, branch):
    projdir=os.path.join(CURRDIR, name)
    dest_data_dir=os.path.join(projdir, '.novel')
    if not os.path.exists(dest_data_dir):
        os.makedirs(dest_data_dir)
    
    for f in ("novel", "chapters.csv", "parts.csv", "plotlines.csv", "versions.csv",
        "drafts.csv"):
            tf = os.path.join(dest_data_dir, f)
            if not os.path.exists(tf):
                os.close(os.open(tf, os.O_CREAT))
    
    with open(os.path.join(dest_data_dir, "novel"), 'w') as nf:
        nf.write('title=%s' % title)
        nf.close()
        
    currdir = os.path.abspath('.')
        
    os.chdir(projdir)
    subprocess.call([GIT, "init", "."])
    print("[shell] %s %s %s" % (GIT, "init", "."))
    if branch:
        subprocess.call([GIT, 'checkout', '-b', branch])
        print("[shell] %s checkout -b %s" % (GIT, branch))
    subprocess.call([GIT, "add", dest_data_dir])
    print("[shell] %s %s %s" % (GIT, "add", dest_data_dir))
    subprocess.call([GIT, "commit", "-am", "makenovel - create project `%s'" % title])
    print("[shell] %s commit -am \"makenovel - create project `%s'\"" % (GIT, title))
    
    os.chdir(currdir)
    
def main():
    args = parser.parse_args(sys.argv[1:])
    create_project(args.name, args.title, args.branch)

if __name__=="__main__":
    main()
