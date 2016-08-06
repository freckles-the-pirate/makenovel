#!/usr/bin/env python3

import sys
import os
import argparse
import csv
from models import *

PROJDIR = os.path.abspath('.')
DATADIR = os.path.join(PROJDIR, '.novel')
NOVELFILE = os.path.join(DATADIR, 'novel')
CHAPTERSFILE = os.path.join(DATADIR, 'chapters.csv')
PLOTLINESFILE = os.path.join(DATADIR, 'plotlines.csv')
VERSIONSFILE = os.path.join(DATADIR, 'versions.csv')
DRAFTSFILE = os.path.join(DATADIR, 'drafts.csv')

""" Construct the parsers
"""

TAG_HELP="Simple (machine-readable) name."

parser = argparse.ArgumentParser(description=
                                 'Command line novel management')
                                 
""" Add a subparser
"""
subparsers = parser.add_subparsers()

parser_list = subparsers.add_parser('list')
parser_list.add_argument('object', choices=[
    'plotlines', 'parts', 'chapters', 'versions', 'drafts'])

### "Show" subparser ###
parser_show = subparsers.add_parser('show')
parser_show.add_argument('type',
    help="Type of object desired to be shown", choices=[ 'novel', 
    'plotline', 'chapter', 'version', 'draft'])
parser_show.add_argument('tag', type=str,
    help="Tag of the object to be shown, e.g. 'ch1'")


### "Add" subparser ###
parser_add = subparsers.add_parser('add')
subparsers_add = parser_add.add_subparsers()

### "Add plotline" subparser ###
parser_add_plotline = subparsers_add.add_parser('plotline')
parser_add_plotline.add_argument('-t', '--tag', help=TAG_HELP,
    required=True)
parser_add_plotline.add_argument('-d', '--description',
    help="What happens in this plotline?")

### "Add parts" subparser ###
parser_add_part = subparsers_add.add_parser('part')
parser_add_part.add_argument('-t', '--tag', help=TAG_HELP,
    required=True)
parser_add_part.add_argument('title', help="Formal title, e.g. 'Part 1'")
part_order = parser_add_part.add_mutually_exclusive_group()
part_order.add_argument('-b', '--before', nargs=1,
    metavar='PART_TAG',
    help='Add this part before `PART_TAG`')
part_order.add_argument('-p', '--parent', nargs=1,
    metavar='PARENT',
    help='Add this part below `PART_TAG`')
part_order.add_argument('-a', '--after', nargs=1,
    metavar='part_tag',
    help='Add this part after `PART_TAG`')

### "Add chapter" subparser ###
parser_add_chapter = subparsers_add.add_parser('chapter')
parser_add_chapter.add_argument('-p', '--plotline',
    help='Plotline associated with the chapter',
    required=True)
chapter_order = parser_add_chapter.add_mutually_exclusive_group()
chapter_order.add_argument('-b', '--before', nargs=1,
    metavar='chapter_tag',
    help='Add this chapter before `chapter_tag`')
chapter_order.add_argument('-a', '--after', nargs=1,
    metavar='chapter_tag',
    help='Add this chapter after `chapter_tag`')

### "add version" subparser ###
parser_add_version = subparsers_add.add_parser('version')
parser_add_version.add_argument('-t', '--tag')
parser_add_version.add_argument('-c', '--comment')

### "add draft" subparser ###
parser_add_draft = subparsers_add.add_parser('draft')
parser_add_draft.add_argument('-t', '--tag')
parser_add_draft.add_argument('-c', '--comment')

### EDIT ###
parser_edit = subparsers.add_parser('edit')
subparsers_edit = parser_edit.add_subparsers()
parser_update = subparsers.add_parser('update')
subparsers_update = parser_update.add_subparsers()

### "edit plotline" subparser ###
parser_edit_plotline = subparsers_edit.add_parser('plotline')
parser_edit_plotline.add_argument('-t', '--tag', help=TAG_HELP,
    required=True)
parser_edit_plotline.add_argument('-d', '--description',
    help="What happens in this plotline?")

### "edit chapter" ###
parser_edit_chapter = subparsers_edit.add_parser('chapter')
parser_edit_chapter.add_argument('chapter_tag', type=str,
    help='Chapter tag to edit.')

### "update chapter" subparser ###
parser_update_chapter = subparsers_update.add_parser('chapter')
parser_update_chapter.add_argument('-p', '--plotline',
    help='Plotline associated with the chapter',
    nargs=1,
    required=True)
parser_update_chapter.add_argument('-P', '--part',
    help='Place this chapter in a part',
    nargs=1,
    metavar='PART_TAG')
chapter_order = parser_update_chapter.add_mutually_exclusive_group()
chapter_order.add_argument('-b', '--before', nargs=1,
    metavar='chapter_tag',
    help='update this chapter before `chapter_tag`')
chapter_order.add_argument('-a', '--after', nargs=1,
    metavar='chapter_tag',
    help='update this chapter after `chapter_tag`')

### "edit version" subparser ###
parser_edit_version = subparsers_edit.add_parser('version')
parser_edit_version.add_argument('-t', '--tag')
parser_edit_version.add_argument('-c', '--comment')
parser_edit_version.add_argument('tag', help='version tag')

### "edit draft" subparser ###
parser_edit_draft = subparsers_edit.add_parser('draft')
parser_edit_draft.add_argument('-t', '--tag')
parser_edit_draft.add_argument('-c', '--comment')
parser_edit_draft.add_argument('tag', help='draft tag')

### "remove" subparser ###
parser_remove = subparsers.add_parser('delete',
    help='remove')
parser_remove.add_argument('object', choices=[
    'plotline', 'chapter', 'version', 'draft'])
parser_remove.add_argument('-f', '--force',
    help="Force deletion of the object",
    type=bool,
    nargs='?',
    const=True)

parser_bind = subparsers.add_parser('bind')
parser_bind.add_argument('-d', '--draft',
    help="Tag of the draft to use. If omitted, latest draft will be used.")

def get_novel(config={}):
    
    if not os.path.exists(DATADIR):
        print("Directory %s does not exist. Creating..." % DATADIR)
        os.makedirs(DATADIR)
    for datafile in [NOVELFILE, CHAPTERSFILE, PLOTLINESFILE,
        VERSIONSFILE, DRAFTSFILE]:
            if not os.path.exists(datafile):
                print("    creating %s" % datafile)
                open(datafile, 'x').close()
    
    with open(NOVELFILE) as novelfile:
        lines = novelfile.readlines()
        novelfile.close()
    
    data = {}
    for line in lines:
        if (line[0] != '#'):
            l = line.strip().split('=')
            data.update({l[0]: l[1]})
            print("data: %s" % data)
    
    title = data.get('title')
    author = Author(config.get('first_name'),
        config.get('last_name'),
        config.get('middle_name'),
        config.get('email_address'),
        config.get('phone_number'),
        config.get('street_address'),
        config.get('city'),
        config.get('state'))
    
    novel = Novel(title, author, config)
    chapters=[]

    # Parse the chapters
    
    with open(CHAPTERSFILE) as chaptersfile:
        ch_reader = csv.reader(chaptersfile)
        for row in ch_reader:
            chapters.append(Chapter(row[0], row[1], novel, row[2]))
        chaptersfile.close()
    
    novel.chapters = chapters
    
    # Parse the versions
    
    with open(VERSIONSFILE) as versionsfile:
        v_reader = csv.reader(versionsfile)
        for row in v_reader:
            versions.append(Version(row[0], row[1], row[2], novel,
                row[3]))
    
    return novel

def list_plotlines(novel):
    print("Plotlines")
    print("%20s%20s" % ("tag", "description"))
    print("%s+%s" % ("=" * 20, "=" * 20))
    for plotline in novel.plotlines:
        print ("%20s%20s" % (plotline.tag, plotline.description))

def list_parts(novel):
    pass

def list_chapters(novel):
    pass

def list_versions(novel):
    pass

def list_drafts(novel):
    pass

def main(argv):
    args = parser.parse_args(argv[1:])
    
    novel = get_novel()
    
    if parser_list:
        obj = parser_list.parse_args(argv[2:]).object
        if obj == 'plotlines':
            list_plotlines(novel)        
        elif obj == 'parts':
            list_parts(novel)
        elif obj == 'chapters':
            list_chapters(novel)
        elif obj == 'versions':
            list_versions(novel)
        elif obj == 'drafts':
            list_drafts(novel)

if __name__=="__main__":
    main(sys.argv)
