#!/usr/bin/env python3

import sys
import os
import argparse
import csv
import subprocess
from models import *

PROJDIR = os.path.abspath('.')
DATADIR = os.path.join(PROJDIR, '.novel')
NOVELFILE = os.path.join(DATADIR, 'novel')
PARTSFILE = os.path.join(DATADIR, 'parts.csv')
CHAPTERSFILE = os.path.join(DATADIR, 'chapters.csv')
PLOTLINESFILE = os.path.join(DATADIR, 'plotlines.csv')
VERSIONSFILE = os.path.join(DATADIR, 'versions.csv')
DRAFTSFILE = os.path.join(DATADIR, 'drafts.csv')

GIT = '/usr/bin/git'

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
parser_list.set_defaults(which='list')

### "show" subparser ###
parser_show = subparsers.add_parser('show')
parser_show.add_argument('object',
    help="Type of object to show",
    choices=('novel', 'plotline', 'part', 'chapter', 'version', 'draft',)
)
parser_show.add_argument('-tag', '--tag',
    help="Tag to show (not required for `show novel`)", 
    required=False)
parser_show.set_defaults(which='show')


### "Add" subparser ###
parser_add = subparsers.add_parser('add')
subparsers_add = parser_add.add_subparsers()

### "Add plotline" subparser ###
parser_add_plotline = subparsers_add.add_parser('plotline')
parser_add_plotline.add_argument('-t', '--tag', help=TAG_HELP,
    required=True)
parser_add_plotline.add_argument('-d', '--description',
    help="What happens in this plotline?")
parser_add_plotline.set_defaults(which='add_plotline')

### "Add parts" subparser ###
parser_add_part = subparsers_add.add_parser('part')
parser_add_part.add_argument('-t', '--tag', help=TAG_HELP,
    required=True)
parser_add_part.add_argument('title', help="Formal title, e.g. 'Part 1'")
part_order = parser_add_part.add_mutually_exclusive_group()
part_order.add_argument('-b', '--before',
    metavar='PART_TAG',
    help='Add this part before `PART_TAG`')
part_order.add_argument('-p', '--parent',
    metavar='PARENT',
    help='Add this part below `PART_TAG`')
part_order.add_argument('-a', '--after',
    metavar='part_tag',
    help='Add this part after `PART_TAG`')
parser_add_part.set_defaults(which='add_part')

### "Add chapter" subparser ###
parser_add_chapter = subparsers_add.add_parser('chapter')
parser_add_chapter.add_argument('-t', '--title')
parser_add_chapter.add_argument('-p', '--plotline',
    help='Plotline associated with the chapter',
    required=True)
parser_add_chapter.add_argument('-P', '--part',
    help='Novel part')
chapter_order = parser_add_chapter.add_mutually_exclusive_group()
chapter_order.add_argument('-b', '--before', nargs=1,
    metavar='chapter_tag',
    help='Add this chapter before `chapter_tag`')
chapter_order.add_argument('-a', '--after', nargs=1,
    metavar='chapter_tag',
    help='Add this chapter after `chapter_tag`')
parser_add_chapter.set_defaults(which='add_chapter')

### "add version" subparser ###
parser_add_version = subparsers_add.add_parser('version')
parser_add_version.add_argument('-t', '--tag')
parser_add_version.add_argument('-c', '--comment')
parser_add_version.set_defaults(which='add_version')

### "add draft" subparser ###
parser_add_draft = subparsers_add.add_parser('draft')
parser_add_draft.add_argument('-t', '--tag')
parser_add_draft.add_argument('-c', '--comment')
parser_add_draft.set_defaults(which='add_draft')

### EDIT and UPDATE ###
parser_edit = subparsers.add_parser('edit')
subparsers_edit = parser_edit.add_subparsers()
parser_update = subparsers.add_parser('update')
subparsers_update = parser_update.add_subparsers()

### "update plotline" subparser ###
parser_update_plotline = subparsers_update.add_parser('plotline')
parser_update_plotline.add_argument('-t', '--tag', help=TAG_HELP,
    required=True)
parser_update_plotline.add_argument('-d', '--description',
    help="What happens in this plotline?")
parser_update_plotline.set_defaults(which='update_plotline')

### "edit chapter" ###
parser_edit_chapter = subparsers_edit.add_parser('chapter')
parser_edit_chapter.add_argument('-e', '--editor',
    help='Full path to an alternative editor', type=str)
parser_edit_chapter_continue = parser_edit_chapter.add_mutually_exclusive_group(required=True)
parser_edit_chapter_continue.add_argument('-t', '--tag', type=str,
    help='Chapter tag to edit.')
parser_edit_chapter_continue.add_argument('-c', '--continue',
    help='Continue editing where you last left off',
    action='store_true')
parser_edit_chapter.set_defaults(which='edit_chapter')

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
parser_update_chapter.set_defaults(which='update_chapter')
chapter_order = parser_update_chapter.add_mutually_exclusive_group()
chapter_order.add_argument('-b', '--before', nargs=1,
    metavar='chapter_tag',
    help='update this chapter before `chapter_tag`')
chapter_order.add_argument('-a', '--after', nargs=1,
    metavar='chapter_tag',
    help='update this chapter after `chapter_tag`')

### "update version" subparser ###
parser_update_version = subparsers_update.add_parser('version')
parser_update_version.add_argument('-t', '--tag')
parser_update_version.add_argument('-c', '--comment')
parser_update_version.add_argument('tag', help='version tag')
parser_update_version.set_defaults(which='update_version')

### "update draft" subparser ###
parser_update_draft = subparsers_update.add_parser('draft')
parser_update_draft.add_argument('-t', '--tag')
parser_update_draft.add_argument('-c', '--comment')
parser_update_draft.add_argument('tag', help='draft tag')
parser_update_draft.set_defaults(which='update_draft')

### "delete" subparser ###
parser_delete = subparsers.add_parser('delete')
parser_delete.add_argument('object', choices=[
    'plotline', 'part', 'chapter', 'version', 'draft'])
parser_delete.add_argument('tag')
parser_delete.add_argument('-f', '--force',
    help="Force deletion of the object",
    action='store_true')
parser_delete.set_defaults(which='delete')

parser_bind = subparsers.add_parser('bind')
parser_bind.add_argument('-d', '--draft',
    help="Tag of the draft to use. If omitted, latest draft will be used.")
parser_bind.set_defaults(which='bind')

def get_novel(config={}):
    
    if not os.path.exists(DATADIR):
        print("Directory %s does not exist. Creating..." % DATADIR)
        os.makedirs(DATADIR)
    for datafile in [NOVELFILE, PARTSFILE, CHAPTERSFILE, PLOTLINESFILE,
        VERSIONSFILE, DRAFTSFILE]:
            if not os.path.exists(datafile):
                print("    creating %s" % datafile)
                open(datafile).close()
    
    with open(NOVELFILE) as novelfile:
        lines = novelfile.readlines()
        novelfile.close()
    
    data = {}
    for line in lines:
        if (line[0] != '#'):
            l = line.strip().split('=')
            data.update({l[0]: l[1]})
            #print("data: %s" % data)
    
    title = data.get('title')
    author = Author(config.get('first_name'),
        config.get('last_name'),
        config.get('middle_name'),
        config.get('email_address'),
        config.get('phone_number'),
        config.get('street_address'),
        config.get('city'),
        config.get('state'))
    
    env = NovelEnvironment(projdir=PROJDIR)
    
    novel = Novel(title, author, config, env=env)
    chapters=[]
    plotlines=[]
    
    Plotline.from_file(novel, PLOTLINESFILE)
    Part.from_file(novel, PARTSFILE)
    Chapter.from_file(novel, CHAPTERSFILE)
    
    # Parse the versions
    
    with open(VERSIONSFILE) as versionsfile:
        v_reader = csv.reader(versionsfile)
        for row in v_reader:
            versions.append(Version(row[0], row[1], row[2], novel,
                row[3]))
    
    return novel

# list

def list_plotlines(novel):
    print("Plotlines")
    print("%20s%20s" % ("tag", "description"))
    print("%s+%s" % ("=" * 20, "=" * 20))
    for plotline in novel.plotlines:
        print ("%20s%20s" % (plotline.tag, plotline.comment))

def list_parts(novel):
    print("Parts")
    print("%5s%10s%10s%5s" % (" ", "tag", " ", "title"))
    print("%s+%s" % ("=" * 20, "=" * 20))
    for part in novel.parts:
        print("%10s%20s" % (part.tag, part.title))

def _print_tree_parts(part, level=0):
    sys.stdout.write('  '*level)
    sys.stdout.write('+- [%s] %s\n' % (part.tag, part.title))
    if part.chapters and len(part.chapters) > 0:
        for chapter in part.chapters:
            sys.stdout.write('  '*(level+1))
            sys.stdout.write('+- %s\n' % chapter)
    if part.children and len(part.children) > 0:
        for child in part.children:
            _print_tree_parts(child, level+1)

def list_chapters(novel):
    for part in novel.parts:
        _print_tree_parts(part)
    
    orphaned = []
    for chapter in novel.chapters:
        if chapter.part is None:
            orphaned.append(chapter)
    
    if len(orphaned) > 0:
        print("Orphaned Chapters (without a part):")
        for i in orphaned:
            print("- %s" % i)

def list_versions(novel):
    pass

def list_drafts(novel):
    pass

# show

def show_novel(novel):
    print("Title: %s" % novel.title)
    print("Author: %s" % novel.author)
    print("Chapters: %s" % len(novel.chapters))
    print("Words: %s" % novel.word_count())
    print()
    print("Keep up the good work!")

def show_parts(novel):
    pass

def show_chapters(novel):
    pass

def show_versions(novel):
    pass

def show_drafts(novel):
    pass

# add

def git_add_files_and_commit(paths=[], message=None):
    if isinstance(paths, list) or isinstance(paths, tuple):
        paths = ' '.join(paths)
    if paths and len(paths) > 0:
        CMD=[GIT, 'add', paths]
        print("[shell] %s" % (" ".join(CMD)))
        subprocess.call(CMD)
    if message:
        CMD=[GIT, 'commit', '-am', '"%s"' % message]
    else:
        CMD=[GIT, 'commit', '-a']
    print("[shell] %s" % (" ".join(CMD)))
    return subprocess.call(CMD)

def add_plotline(novel, tag, description):
    plotline_dir = os.path.join(PROJDIR, tag)
    if not os.path.exists(plotline_dir):
        os.makedirs(plotline_dir)
    with open(PLOTLINESFILE, 'a') as plf:
        wr = csv.writer(plf)
        wr.writerow([tag, description])
        plf.close()
        
    git_add_files_and_commit(message='add plotline %s' % tag)

def add_part(novel, tag, title, before, after, parent):
    # First check if the tags are valid:
    part_tags = [p.tag for p in novel.parts]
    for i in [before, after, parent]:
        if i not in part_tags:
            print("%s: invalid part tag" % i)
            sys.exit(1)
                
    with open(PARTSFILE, 'a') as partsfile:
        partswriter = csv.writer(partsfile)
        partswriter.writerow([tag, title, parent])
        partsfile.close()
    
    git_add_files_and_commit(message='add part %s' % tag)

def add_chapter(novel, plotline_tag, title, part_tag):
    
    plotline = novel.find_plotline(plotline_tag)
    if plotline is None:
        print("%s: plotline not found" % plotline_tag)
    part = novel.find_part(part_tag)
    if part is None:
        print("%s: part not found" % part_tag)
    
    i = len(novel.chapters)+1
    c = Chapter(plotline=plotline, novel=novel, title=title, part=part, 
        number=i)
    with open(CHAPTERSFILE, 'a') as chaptersfile:
        ch_writer = csv.writer()
        c.write_row(ch_writer)
        chatpersfile.close()

def edit_chapter(novel, cont, tag, editor):
    
    chapter = None
    
    if cont:
        if len(novel.chapters) == 0:
            print("No chapters found. Please add some chapters.")
            sys.exit(1)
        if len(novel.chapters) == 1:
            chapter = novel.chapters[0]
        chapter = novel.env.last_edit
        if chapter is None:
            chapter = novel.chapters[-1]
            novel.env.last_edit = chapter
    
    else:
        chapter = None
        for c in novel.chapters:
            if c.tag == tag:
                chapter = c
        
        if chapter is None:
            print("%s: Invalid chapter tag." % tag)
            sys.exit(1)
    
    CMD = ['/usr/bin/vim', chapter.path]
    print("[shell] %s" % ' '.join(CMD))
    subprocess.call(CMD)
    
    git_add_files_and_commit(chapter.path, "Edit %s" % chapter)

## Delete methods ##

def delete_plotline(novel, tag, force):
    pass

def delete_part(novel, tag, force):
    pass

def delete_chapter(novel, tag, force):
    chapter = None
    for c in novel.chapters:
        if c.tag() == tag:
            chapter = c
    if not chapter:
        print("%s: Invalid chapter tag" % tag)
        sys.exit(1)
        
    if not force:
        f = ''
        while f.lower() not in ('y', 'n'):
            f = input("Are you sure you want to delete '%s' (y/n)? " % chapter)
            if f == 'y':
                delete_chapter(novel, tag, True)
            else:
                print("%s not deleted." % chapter)
                return
    
    ch_entries = []
    with open(CHAPTERSFILE) as chaptersfile:
        ch_reader = csv.reader(chaptersfile)
        chh_entries = [r for r in ch_reader]
        chaptersfile.close()
    
    with open(CHAPTERSFILE, 'w') as chaptersfile:
        ch_writer = csv.writer(chaptersfile)
        ch_writer.writerows(ch_entries[:chapter.num-1])
        ch_writer.writerows(ch_entries[chapter.num+1:])
        chaptersfile.close()
    
    os.remove(chapter.path())
    print("Removed %s" % chapter.path())
    
    git_add_files_and_commit([], message="Delete %s" % chapter)
    

def delete_version(novel, tag, force):
    pass

def delete_draft(novel, tag, force):
    pass

def main(argv):
    if not os.path.exists(DATADIR):
        print("This is not a makenovel project. \
Use `mnadmin' to create the novel project. Thank you.")
        sys.exit(1)
        
    args = parser.parse_args(argv[1:])
    
    novel = get_novel()
    
    if getattr(args, 'which', '') == 'list':
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
    
    elif getattr(args, 'which', '') == 'show':
        obj = getattr(parser_show.parse_args(argv[2:]), 'object')
        tag = getattr(parser_show.parse_args(argv[2:]), 'tag')
        if obj == 'novel':
            show_novel(novel)
        elif tag is None:
            print("Error: tag [-t, --tag] required!")
            sys.exit(1)
        elif obj == 'plotline':
            show_plotline(novel, tag)
        elif obj == 'part':
            show_part(novel, tag)
        elif obj == 'chapter':
            show_chapter(novel, tag)
        elif obj == 'version':
            show_version(novel, tag)
        elif obj == 'draft':
            show_draft(novel, tag)
    
    elif getattr(args, 'which', '').startswith('add_'):
        parsed = parser_add.parse_args(argv[2:])
        tag = getattr(parsed, 'tag', None)
        description = getattr(parsed, 'description', None)
        title = getattr(parsed, 'title', None)
        before = getattr(parsed, 'before', None)
        parent = getattr(parsed, 'parent', None)
        after = getattr(parsed, 'after', None)
        plotline = getattr(parsed, 'plotline', None)
        part = getattr(parsed, 'part', None)

        if args.which == 'add_plotline':
            add_plotline(novel, tag, description)
        elif args.which == 'add_part':
            add_part(novel, tag, title, parent, before, after)
        elif args.which == 'add_chapter':
            add_chapter(novel, plotline, title, part)
        elif args.which == 'add_version':
            add_version(novel, parsed.tag)
        elif args.which == 'add_draft':
            add_draft(novel, parsed.tag)
    
    elif getattr(args, 'which', '') == 'edit_chapter':
        parsed = parser_edit.parse_args(argv[2:])
        cont = getattr(parsed, 'continue', False)
        tag = getattr(parsed, 'tag', None)
        editor = getattr(parsed, 'editor',
            novel.config.get('chapter.editor',
            '/usr/bin/vim'))
        edit_chapter(novel, cont, tag, editor)
    
    elif getattr(args, 'which', '') == 'delete':
        parsed = parser_delete.parse_args(argv[2:])
        force = getattr(parsed, 'force', False)
        obj = getattr(parsed, 'object')
        tag = getattr(parsed, 'tag')
        
        callbacks = {
            'plotline': delete_plotline,
            'part': delete_part,
            'chapter': delete_chapter,
            'version': delete_version,
            'draft': delete_draft,
        }
        
        callbacks[obj](novel, tag, force)
        

if __name__=="__main__":
    main(sys.argv)
