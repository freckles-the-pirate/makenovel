#!/usr/bin/env python

import os
import sys
import csv

DATADIR = '.novel'
NOVELFILE = os.path.join(DATADIR, 'novel')
PARTSFILE = os.path.join(DATADIR, 'parts.csv')
CHAPTERSFILE = os.path.join(DATADIR, 'chapters.csv')
PLOTLINESFILE = os.path.join(DATADIR, 'plotlines.csv')
VERSIONSFILE = os.path.join(DATADIR, 'versions.csv')
DRAFTSFILE = os.path.join(DATADIR, 'drafts.csv')

def machine_str(s):
    s2 = s.lower().replace( ' ', '_' )
    for i in ('!', '.', "'", '"', ','):
        s2 = s2.replace(i, '')
    return s2

class Config(object):
    doc=None
    default_value=None
    value=None
    
    def __init__(self, doc=None, default_value=None):
        self.doc = doc
        self.default_value = default_value

class Author(object):
    first_name=None
    last_name=None
    middle_name=None
    email_address=None
    phone_number=None
    street_address=None
    city=None
    state=None
    
    def __init__(self, first_name, last_name, middle_name=None,
        email_address=None, phone_number=None, street_address=None,
        city=None, state=None):
            
        self.first_name = first_name
        self.last_name = last_name
        self.middle_name = middle_name
        self.email_address = email_address
        self.phone_number = phone_number
        self.street_address = street_address
        self.city = city
        self.state = state
    
    def __repr__(self):
        return "%s %s" % (self.first_name, self.last_name)


class NovelEnvironment(object):
    
    last_edit = None
    projdir = None
    
    def __init__(self, last_edit=None, projdir=None):
        self.last_edit = last_edit
        self.projdir = projdir

class Novel(object):
    title = None
    author = None
    config = {}
    env = None
    
    plotlines = []
    chapters = []
    versions = []
    drafts = []
    parts = []
    
    def __init__(self, title=None, author=None, config={}, env=None):
        self.title = title
        self.author = author
        self.config = config
        self.env = env
                
    def get_config(self, key):
        if key in self.config:
            return DEFAULTS['key'].value
    
    def word_count(self):
        count = 0
        for c in self.chapters:
            count = count + c.word_count()
        return count
    
    def find_plotline(self, tag):
        for p in self.plotlines:
            if p.tag == tag:
                return p
        return None
    
    def find_part(self, tag):
        for p in self.parts:
            if p.tag == tag:
                return p
        return None
    
    def find_chapter(self, tag):
        for p in self.chapters:
            if p.tag == tag:
                return p
        return None
    
    def _write_csv(self, obj_set, path):
        p = os.path.join(self.env.projdir, path)
        with open(path, 'w') as csv_file:
            csv_writer = csv.writer(csv_file)
            for obj in obj_set:
                obj.write_row(csv_writer)
            csv_file.close()
    
    def write_plotlines(self):
        self._write_csv(self.plotlines, PLOTLINESFILE)
    
    def write_parts(self):
        self._write_csv(self.parts, PARTSFILE)
    
    def write_chapters(self):
        self._write_csv(self.chapters, CHAPTERSFILE)
    
    def __repr__(self):
        return "%s by %s" % (self.title, self.author)

class Novelable(object):
    novel = None
    
    def __init__(self, novel):
        self.novel = novel


class Taggable(object):
    tag = None
    
    def __init__(self, tag):
        self.tag = tag


class Commentable(object):
    comment=None
    
    def __init__(self, comment=None):
        self.comment = comment

class Plotline(Novelable, Commentable, Taggable):
    
    def __init__(self, tag, novel, comment=None):
        self.tag = tag
        self.novel = novel
        self.comment = comment
        
    def get_directory(self):
        os.path.join(os.path.abspath('.'), self.tag)
    
    def create_directory(self):
        os.makedirs(self.get_directory())
    
    def __repr__(self):
        return "<Plotline (tag=\"%s\", novel=\"%s\", comment=\"%s\")>" % (
            self.tag, self.novel, self.comment)
    
    @classmethod
    def from_file(Klass, novel, path):
        with open(path) as plf:
            pl_reader = csv.reader(plf)
            for row in pl_reader:
                p = Plotline(row[0], novel, row[1])
                novel.plotlines.append(p)
    
    def write_row(self, writer):
        writer.writerow([self.tag, self.comment])

class Part(Novelable, Taggable):
    
    tag=None
    novel=None
    number=0
    title=None
    parent=None
    children=[]
    chapters=[]
    
    def __init__(self, novel, title, number, tag=None, parent=None, children=[]):
        self.tag = tag
        self.novel = novel
        self.title = title
        self.parent = parent
        self.children = children
        self.number = number
        if self.tag is None or len(self.tag) == 0:
            if self.title is None:
                self.tag = '%d' % self.number
            else:
                self.tag = '%d__%s' % (self.number, machine_str(self.title))
        
    @classmethod
    def from_file(Klass, novel, path):
        n=0
        with open(path) as partsfile:
            p_reader = csv.reader(partsfile)
            for row in p_reader:
                (title, parent) = row
                
                parent = novel.find_part(parent)
                n += 1
                part = Part(novel=novel, title=title, parent=parent, number=n)
                if parent:
                    parent.children.append(part)
                
                novel.parts.append(part)
            partsfile.close()
    
    def write_row(self, writer):
        parent_tag = None
        if self.parent:
            parent_tag = self.parent.tag
        writer.writerow([self.tag, self.title, parent_tag])

class Chapter(Taggable):
    
    path = None
    title = None
    plotline = None
    novel = None
    part = None
    number = 0
    
    def __init__(self, plotline, novel, title=None, part=None,
                 number=0, tag=None, path=None):

        self.tag = tag
        self.novel = novel
        self.plotline = plotline
        self.title = title
        self.part = part
        self.number = number
        self.path = path
        
        # Configure the chapter tag and path
        if self.tag is None or len(tag) == 0:
            if title is None or len(title) == 0:
                self.tag = '%d' % number
            else:
                # Replace all machine-unfriendly chars.
                ttl = machine_str(title)
                self.tag = '%d__%s' % (number, ttl)
        #print("tag=%s" % self.tag)
                
        if self.path is None:
            filename = '%s.%s' % (tag, novel.config.get('chapter.ext', 'rst'))
            if plotline is not None:
                pre = os.path.join(novel.env.projdir, plotline.tag)
            else:
                pre = os.path.join(novel.env.projdir)
            self.path = os.path.join(pre, filename)
    
    def word_count(self):
        count = 0
        with open(self.path, 'r') as f:
            count += len(f.read().split(' '))
            f.close()
        return count
    
    def __repr__(self):
        if self.title:
            return "[%s] Chapter %d: %s" % (self.tag, self.number, self.title)
        return "[%s] Chapter %d" % (self.tag, self.number)
    
    def write_row(self, csvwriter):
        csvwriter.writerow([self.tag,
                             self.path,
                             self.plotline.tag, 
                             self.part.tag,
                             self.title,
                             ])
    
    @classmethod
    def from_file(self, novel, chapters_path):
        
        n = 0
        
        with open(chapters_path) as chaptersfile:
            ch_reader = csv.reader(chaptersfile)
            for row in ch_reader:
                (tag, path, plotline_tag, part_tag, title) = row
                
                part = None
                if part_tag is not None:
                    for p in novel.parts:
                        if part_tag == p.tag:
                            part = p
                            
                plotline = None
                if plotline_tag is not None:
                    for pl in novel.plotlines:
                        if pl.tag == plotline_tag:
                            plotline = pl
                
                n += 1
                            
                chapter = Chapter(plotline=plotline,
                                  novel=novel,
                                  title=title,
                                  part=part,
                                  number=n,
                                  tag=tag,
                                  path=path)
                novel.chapters.append(chapter)
                if part is not None:
                    part.chapters.append(chapter)
            chaptersfile.close()

class Version(Taggable, Commentable, Novelable):
    
    label=None
    novel=None
    timestamp=None
    
    def __init__(self, label, git_hash, tag, novel, comment=None,
        timestamp=None):
        self.label = label
        self.get_hash = git_hash
        self.tag = tag
        self.novel = novel
        self.comment = comment
        self.timestamp = timestamp

class Draft(Taggable, Commentable):
    
    timestamp = None
    
    def __init__(self, stage, tag, novel, comment=None, timestamp=None):
        self.stage = stage
        super(Taggable, self).__init__(tag)
        super(Commentable, self).__init__(comment)
        super(Novelable, self).__init__(novel)
        self.timestamp = timestamp
