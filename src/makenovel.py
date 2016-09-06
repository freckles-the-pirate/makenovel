#!/usr/bin/env python3

import sys
import os
import argparse
import csv
import subprocess
import textwrap

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

subparsers = parser.add_subparsers()

parser_config = subparsers.add_parser('config')
parser_config.add_argument('-l', '--list', const=True, nargs='?')
parser_config.add_argument('-k', '--key')
parser_config.add_argument('-s', '--set')
parser_config.add_argument('-g', '--get', const=True, nargs='?')
parser_config.add_argument('-d', '--set-default', action='store_true')
parser_config.set_defaults(which='config')

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
parser_add_part.add_argument('-t', '--title',
                             help="Formal title, e.g. 'Part 1'")
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

### EDIT and UPDATE ###
parser_update = subparsers.add_parser('update')
subparsers_update = parser_update.add_subparsers()

# "update part" subparser
parser_update_part = subparsers_update.add_parser('part')
parser_update_part.add_argument('-t', '--title')
parser_update_part.add_argument('tag')
part_update_order = parser_update_part.add_mutually_exclusive_group()
part_update_order.add_argument('-b', '--before',
    metavar='PART_TAG',
    help='Add this part before `PART_TAG`')
part_update_order.add_argument('-p', '--parent',
    metavar='PARENT',
    help='Add this part below `PART_TAG`')
part_update_order.add_argument('-a', '--after',
    metavar='part_tag',
    help='Add this part after `PART_TAG`')

### "update plotline" subparser ###
parser_update_plotline = subparsers_update.add_parser('plotline')
parser_update_plotline.add_argument('tag')
parser_update_plotline.add_argument('-t', '--new-tag')
parser_update_plotline.add_argument('-d', '--description',
    help="What happens in this plotline?")
parser_update_plotline.set_defaults(which='update_plotline')

### "update chapter" subparser ###
parser_update_chapter = subparsers_update.add_parser('chapter')
parser_update_chapter.add_argument('tag')
parser_update_chapter.add_argument('-t', '--title')
parser_update_chapter.add_argument('-p', '--plotline',
    help='Plotline associated with the chapter',
    required=True)
parser_update_chapter.add_argument('-P', '--part',
    help='Place this chapter in a part')
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

### "edit chapter" ###
parser_edit = subparsers.add_parser('edit')
parser_edit.add_argument('-e', '--editor',
    help='Full path to an alternative editor', type=str)
parser_edit_chapter_continue = parser_edit.add_mutually_exclusive_group(
    required=True)
parser_edit_chapter_continue.add_argument('--tag', type=str,
    help='Chapter tag to edit.')
parser_edit_chapter_continue.add_argument('-c', '--continue',
    help='Continue editing where you last left off',
    action='store_true')
parser_edit.set_defaults(which='edit_chapter')

### "delete" subparser ###
parser_delete = subparsers.add_parser('delete')
parser_delete.add_argument('object', choices=[
    'plotline', 'part', 'chapter', 'version', 'draft'])
parser_delete.add_argument('tag')
parser_delete.add_argument('-f', '--force',
    help="Force deletion of the object",
    action='store_true')
parser_delete.set_defaults(which='delete')

### "bind" subparser
parser_bind = subparsers.add_parser('bind')
parser_bind.add_argument('-s', '--stage', type=str,
                         help="If you're creating a draft, what type of draft?")
parser_bind.add_argument('-c', '--comment', type=str,
                         help="A long description of this version.")
parser_bind.set_defaults(which='bind')

### "import" subparser
parser_import = subparsers.add_parser("import")
parser_import.set_defaults(which='import')

### IMPORT CHAPTER
subparsers_import = parser_import.add_subparsers()
parser_import_chapter = subparsers_import.add_parser('chapter')
parser_import_chapter.add_argument("-o", "--path",
                                   help="Path of the original chapter file.",
                                   required=True)
parser_import_chapter.add_argument("-P", "--plotline",
                                   help="Plotline tag",
                                   required=True)
parser_import_chapter.add_argument("-t", "--title",
                                   help="Title of the chapter"
                                   )
parser_import_chapter.add_argument("-p", "--part",
                                   help="Add the chapter to this part tag"
                                   )
parser_import_chapter.set_defaults(which='import_chapter')
chapter_import_order = parser_import_chapter.add_mutually_exclusive_group()
chapter_import_order.add_argument('-b', '--before', nargs=1,
    metavar='CHAPTER',
    help='update this chapter before `CHAPTER`')
chapter_import_order.add_argument('-a', '--after', nargs=1,
    metavar='CHAPTER',
    help='update this chapter after `CHAPTER`')

def ask_to_delete(obj, force=False):
    if not force:
        f = ''
        while f.lower() not in ('y', 'n'):
            f = input("Are you sure you want to delete '%s' (y/n)? " % obj)
            if f == 'y':
                return True
            else:
                print("%s not deleted." % obj)
                sys.exit(0)
    return True

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
        print("%10s%20s" % (part.tag, part.title or ''))

def _print_tree_parts(part, level=0):
    sys.stdout.write('  '*level)
    sys.stdout.write('+- [%s] %s\n' % (part.tag, part.title or ''))
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
    if len(novel.versions) == 0:
        print("No versions found.")
        sys.exit(0)
    for v in novel.versions:
        print("%-5d%20s%50s" % (v.number, v.timestamp, os.path.abspath(v.path)))

def list_drafts(novel):
    if len(novel.drafts) == 0:
        print("No drafts found.")
        sys.exit(0)
    for d in novel.drafts:
        print("[%-5d]%-10s%20s%50s" % (d.number, d.stage, d.timestamp,
                                       os.path.abspath(d.path)))

# show

def show_novel(novel):
    print("Title: %s" % novel.title)
    print("Author: %s" % novel.author)
    print("Chapters: %s" % len(novel.chapters))
    print("Words: %s" % novel.word_count())
    print()
    print("Keep up the good work!")

def show_part(novel, part_tag):
    part = novel.find_part(part_tag)
    if part is None:
        tags = ', '.join(["'%s'" % p.tag for p in novel.parts])
        raise RuntimeError("%s: Part not found in [%s]" % (part_tag, tags))
    wc = 0
    for ch in part.chapters:
        wc += ch.word_count()
    print("part #: %d" % part.number)
    print("tag: %s" % part.tag)
    print("title: %s" % part.title)
    print("chapters: %d" % len(part.chapters))
    print("%d words" % wc)

def show_plotline(novel, plotline_tag):
    plotline = novel.find_plotline(plotline_tag)
    if not plotline:
        print("%s: plotline not found" % plotline_tag)
    
    print("tag: %s" % plotline.tag)
    print("description: %s" % plotline.comment)
    print("%d chapters follow this plotline" % len(plotline.chapters))

def show_chapter(novel, chapter_tag):
    chapter = novel.find_chapter(chapter_tag)
    if chapter is None:
        print("No chapter with tag %s" % chapter_tag)
        sys.exit(1)
    print("Chapter #: %d" % chapter.number)
    print("Tag: %s" % chapter.tag)
    if chapter.title:
        print("Title: %s" % chapter.title)
    print("Word Count: %s" % chapter.word_count())

def show_version(novel):
    pass

def show_draft(novel):
    pass

# add

def add_plotline(novel, tag, description):
    if novel.find_plotline(tag) is not None:
        raise RuntimeError("%s: plotline tag already exists\n" % tag)
    novel.plotlines.append(Plotline(novel, tag, description))
    novel.write_plotlines()

def add_part(novel, title=None, before_tag=None, after_tag=None, parent_tag=None):
    # First check if the tags are valid
    (before, after, parent) = (None, None, None)
    if before_tag is not None:
        before = novel.find_part(before_tag)
        if before is None:
            raise RuntimeError("'%s': part not found")
    if after_tag is not None:
        after = novel.find_part(after_tag)
        if after is None:
            raise RuntimeError("'%s': part not found")
    if parent_tag is not None:
        parent = novel.find_part(parent_tag)
        if parent is None:
            raise RuntimeError("'%s': part not found")
    
    part = Part(novel, title, parent)
    
    if before:
        novel.parts.insert(novel.parts.index(before), part)
    elif after:
        novel.parts.insert(novel.parts.index(after)+1, part)
    else:
        novel.parts.append(part)
        
    novel.write_parts()
    novel.git_commit_data(novel.env.parts_path)

def add_chapter(novel, plotline_tag, title, part_tag):
    
    plotline = novel.find_plotline(plotline_tag)
    if plotline is None:
        print("%s: plotline not found" % plotline_tag)
        sys.exit(1)
    part = novel.find_part(part_tag)
    if part is None:
        print("%s: part not found" % part_tag)
        sys.exit(1)
    
    i = len(novel.chapters)+1
    c = Chapter(plotline=plotline, novel=novel, title=title, part=part, number=i)
    novel.chapters.append(c)
    if part:
        part.chapters.append(c)
    
    # First create the plotline directory if it doesn't exist.
    if not os.path.exists(os.path.dirname(c.path)):
        os.makedirs(os.path.dirname(c.path))
    if not os.path.exists(c.path):
        open(c.path, 'w+').close()
    novel.write_chapters()
    
    novel.git_commit_files([c.path])
    novel.git_commit_data(novel.env.chapters_path, "Add %s" % c)

# update

def update_part(novel, tag, title, before_tag, after_tag, parent_tag):
    part = novel.find_part(tag)
    if part is None:
        print("%s: part not found" % tag)
        sys.exit(1)
        
    if title:
        part.title = title
    
    if parent_tag:
        old_parent = part.parent
        parent = novel.find_part(parent)
        part.parent = parent
        old_parent.children.remove(part)
        parent.children.append(part)
    
    if before_tag:
        before = novel.find_part(before_tag)
        if before is None:
            print("%s: part not found" % tag)
            sys.exit(1)
        i1 = novel.parts.index(part)
        i2 = novel.parts.index(before)
        novel.parts.insert(novel.parts.pop(i1), i2)
        
    if after_tag:
        after = novel.find_part(after_tag)
        if after is None:
            print("%s: part not found" % tag)
            sys.exit(1)
        i1 = novel.parts.index(part)
        i2 = novel.parts.index(before)+1
        novel.parts.insert(novel.parts.pop(i1), i2)
    
    with open(PARTSFILE, 'w') as partsfile:
        writer = csv.writer(partsfile)
        for p in novel.parts:
            p.write_row(writer)
        partsfile.close()
    
    novel.write_parts()
    novel.git_commit_data(Novel.PARTSFILE, "Update part %s" % part)

def update_plotline(novel, tag, new_tag, description):
    plotline = novel.find_plotline(tag)
    
    if not plotline:
        print("%s: plotline not found" % tag)
        sys.exit(1)
    
    if new_tag:
        plotline.tag = new_tag
    
    if description:
        plotline.comment = description
    
    novel.write_plotlines()
    novel.git_commit_data(Novel.PARTSFILE, "Update plotline %s" % plotline)

def update_chapter(novel, tag, plotline_tag, title, part_tag,
                   before_tag, after_tag):
    (plotline, part, before, after) = (None, )*4
    
    chapter = novel.find_chapter(tag)
    if chapter is None:
        print("%s: chapter not found" % tag)
        sys.exit(1)
    
    # The tag will be overwritten, so save it, just in case.
    old_tag = chapter.tag
    
    if title:
        chapter.title = title
    
    if plotline_tag:
        plotline = novel.find_plotline(plotline_tag)
        if plotline is None:
            print("%s: plotline not found" % plotline_tag)
            sys.exit(1)
        old_plotline = chapter.plotline
        chapter.plotline = plotline
        plotline.chapters.append(
            old_plotline.chapters.pop(
                old_plotline.chapters.index(chapter)
            )
        )
    
    if part_tag:
        part = novel.find_part(part_tag)
        if part is None:
            print("%s: part not found" % part_tag)
            sys.exit(1)
        old_part = chapter.part
        chapter.part = part
        part.chapters.append(
            old_part.pop(
                old_part.index(chapter)
            )
        )
    
    if before_tag:
        before = novel.find_chapter(before_tag)
        if before is None:
            print("%s: chapter not found" % before)
            sys.exit(1)
        
        novel.chapters.insert(
            novel.chapters.index(chapter),
            novel.chapters.pop(chapter)
            )
    
    elif after_tag:
        after = novel.find_chapter(after_tag)
        if after is None:
            print("%s: chapter not found" % after)
            sys.exit(1)
        
        novel.chapters.insert(
            novel.chapters.index(chapter)+1,
            novel.chapters.pop(chapter)
            )
    
    novel.write_chapters()
    novel.git_add_files([novel.env.data_dir, chapter.path])
    novel.git_commit_files([chapter.path, novel.env.chapters_path],
                           "Update %s" % chapter)
        

def update_version(novel, tag, rename_tag, comment):
    pass

def update_draft(novel, tag, rename_tag, comment):
    pass

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
    
    novel.git_add_files([chapter.path, novel.env.chapters_path])
    novel.git_commit_files([chapter.path, novel.env.chapters_path],
                           "Edit %s" % chapter)

## Delete methods ##

def delete_plotline(novel, tag, force):
    pass

def delete_part(novel, tag, force):
    
    part = novel.find_part(tag)
    if not part:
        print("%s: part not found" % tag)
        sys.exit(1)
    
    if not ask_to_delete(part, force):
        return
    
    removed_title = str(part)
    
    removed = novel.parts.pop(novel.parts.index(part))
    novel.write_parts()
    novel.git_commit_files([novel.env.parts_path,], "Remove tag %s" % removed)

def delete_chapter(novel, tag, force):
    chapter = novel.find_chapter(tag)
    if not chapter:
        print("%s: Invalid chapter tag" % tag)
        sys.exit(1)
        
    if not ask_to_delete(chapter, force):
        return
    
    os.remove(chapter.path)
    novel.chapters.remove(chapter)
    
    with open(CHAPTERSFILE, 'w') as chaptersfile:
        writer = csv.writer(chaptersfile)
        for chapter in novel.chapters:
            chapter.write_row(writer)
        chaptersfile.close()

def delete_version(novel, tag, force):
    version = novel.find_version(tag)
    if not version:
        raise RuntimeError("%s: version not found" % tag)
    
    if not ask_to_delete(version):
        return
    
    novel.versions.remove(version)
    novel.write_versions()
    novel.git_commit_files([novel.env.versions_path,], "Remove %s" % version)

def delete_draft(novel, tag, force):
    pass

def import_chapter(novel, origin, plotline_tag, title, part_tag, before_tag, 
                    after_tag):
    
    (plotline, part, before, after) = (None,)*4
    if plotline_tag:
        plotline = novel.find_plotline(plotline_tag)
        if not plotline:
            print("%s: plotline not found" % plotline_tag)
            sys.exit(1)
    
    if part_tag:
        part = novel.find_part(part_tag)
        if not part:
            print("%s: part not found" % part_tag)
            sys.exit(1)
    
    if before_tag:
        before = novel.find_before(before_tag)
        if not before:
            print("%s: chapter not found" % before_tag)
            sys.exit(1)
    
    elif after_tag:
        after = novel.find_after(after_tag)
        if not after:
            print("%s: chapter not found" % after_tag)
            sys.exit(1)
    
    if not os.path.exists(origin):
        print("%s: Origin path does not exist." % origin)
        sys.exit(1)
        
    chapter = Chapter(plotline, novel, title, part)
    if not os.path.exists(os.path.dirname(chapter.path)):
        os.makedirs(os.path.dirname(chapter.path))
    if not os.path.exists(chapter.path):
        open(chapter.path, 'a+').close()
    
    novel.chapters.append(chapter)
    
    with open(origin, 'r') as originfile:
        with open(chapter.path, 'w') as destfile:
            destfile.write(originfile.read())
        destfile.close()
        originfile.close()
    
    plotline_dir = None
    if chapter.plotline:
        plotline_dir = chapter.plotline.path
    
    files = [CHAPTERSFILE, chapter.path]
    if plotline_dir:
        files.append(plotline_dir)
    novel.write_chapters()
    novel.git_add_files([chapter.path])
    novel.git_commit_files([chapter.path, novel.env.chapters_path],
                           "Import %s" % chapter)

def bind_novel(novel, comment, stage):
    version = novel.bind(comment, stage)
    print("New %s created: %s" % (type(version).__name__, version.path))

def main(argv):
    if not os.path.exists(DATADIR):
        print("This is not a makenovel project. \
Use `mnadmin' to create the novel project. Thank you.")
        sys.exit(1)
    
    if len(argv) == 1:
        parser.print_help()
        sys.exit(1)
        
    args = parser.parse_args(argv[1:])
    
    novel = Novel.load()
    
    if getattr(args, 'which', '') == 'config':
        parsed = parser_config.parse_args(argv[2:])
        value = getattr(parsed, 'set', None)
        get = getattr(parsed, 'get', None)
        dflt = getattr(parsed, 'default', False)
        key = getattr(parsed, 'key', None)
        lst = getattr(parsed, 'list', False)
        
        if key is not None and key not in novel.config:
            raise ValueError("'%s' not in %s" % (key, list(novel.config.keys())))
        
        if lst:
            for c in novel.config.keys():
                print(c)
        elif value is not None:
            novel.set_config(key, value)
            novel.write_config()
        elif dflt:
            dflt = novel.config[parsed.key].default
            print(novel.set_config(parsed.key, dflt))
        elif get or key:
            print(novel.get_config(key))
        else:
            for k in list(novel.config.keys()):
                dv = novel.config[k].default_value
                cv = getattr(novel.config[k], 'value', None)
                doc = textwrap.indent(
                        '\n'.join(
                            textwrap.wrap(
                                "%s" % novel.config[k].doc,
                            )
                        ), '  | '
                    )
                print("* %s" % k)
                print(doc)
                if dv:
                    print("    Default Value: %s" % str(dv))
                if cv and dv != cv:
                    print("    Current value: %s" % str(cv))
                print()
    
    elif getattr(args, 'which', '') == 'list':
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
        obj = getattr(parser_show.parse_args(argv[2:]), 'object', None)
        tag = getattr(parser_show.parse_args(argv[2:]), 'tag', None)
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
    
    elif getattr(args, 'which', '').startswith('add'):
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
            add_part(novel, title, before, after, parent)
        elif args.which == 'add_chapter':
            add_chapter(novel, plotline, title, part)
        elif args.which == 'add_version':
            add_version(novel, parsed.tag)
        elif args.which == 'add_draft':
            add_draft(novel, parsed.tag)
    
    elif getattr(args, 'which', '').startswith('update'):
        parsed = parser_update.parse_args(argv[2:])
        tag = getattr(parsed, 'tag', None)
        new_tag = getattr(parsed, 'new_tag', None)
        description = getattr(parsed, 'description', None)
        title = getattr(parsed, 'title', None)
        before = getattr(parsed, 'before', None)
        parent = getattr(parsed, 'parent', None)
        after = getattr(parsed, 'after', None)
        plotline = getattr(parsed, 'plotline', None)
        part = getattr(parsed, 'part', None)
        
        if args.which == 'update_plotline':
            update_plotline(novel, tag, new_tag, description)
        elif args.which == 'update_part':
            update_part(novel, tag, title, before, after, parent)
        elif args.which == 'update_chapter':
            update_chapter(novel, tag, plotline, title, part, before, after)
        elif args.which == 'update_version':
            update_version(novel, parsed.tag)
        elif args.which == 'update_draft':
            update_draft(novel, parsed.tag)
        elif args.which == 'update':
            parser_update.print_help()
            sys.exit(1)
    
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
    
    elif getattr(args, 'which', '').startswith('import'):
        parsed = parser_import.parse_args(argv[2:])
        origin = getattr(parsed, 'path', None)
        plotline = getattr(parsed, 'plotline', None)
        title = getattr(parsed, 'title', None)
        part = getattr(parsed, 'part', None)
        before = getattr(parsed, 'before', None)
        after = getattr(parsed, 'after', None)
        
        if args.which == 'import_chapter':
            import_chapter(novel, origin, plotline, title, part, before, after)
        
        if args.which == 'import':
            parser_import.print_usage()
    
    elif getattr(args, 'which', '') == 'bind':
        parsed = parser_import.parse_args(argv[2:])
        comment = getattr(parsed, 'comment', None)
        stage = getattr(parsed, 'stage', None)
        
        bind_novel(novel, comment, stage)

if __name__=="__main__":
    main(sys.argv)
