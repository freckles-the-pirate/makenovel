#!/usr/bin/env python

import os
import sys
import csv
import shutil

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
    parts = []
    chapters = []
    versions = []
    drafts = []
    
    def __init__(self, title=None, author=None, config={}, env=None):
        self.title = title
        self.author = author
        self.config = config
        self.env = env
    
    def add_plotlines(self, *plotlines):
        for plotline in plotlines:
            plotline.novel = self
            self.plotlines.append(plotline)
    
    def add_parts(self, *parts):
        for part in parts:
            part.novel = self
            self.parts.append(part)
    
    def set_config(self, key, value, create=False):
        if create and key not in self.config:
            self.config.update({key: Config("[user]", None)})
        self.config[key].value = value
                
    def get_config(self, key):
        return self.config[key].value or self.config[key].default
    
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
        
    @classmethod
    def parse(Klass, env):
        novel_path = os.path.join(env.projdir, NOVELFILE)
        chapt_path = os.path.join(env.projdir, CHAPTERSFILE)
        parts_path = os.path.join(env.projdir, PARTSFILE)
        plotline_path = os.path.join(env.projdir, PLOTLINESFILE)
        versions_path = os.path.join(env.projdir, VERSIONSFILE)
        draft_path = os.path.join(env.projdir, DRAFTSFILE)
        
        # Novel Overview
        with open(novel_path) as novel_file:
            for line in novel_file:
                l = line.strip()
                if not l.startswith('#'):
                    cfg = line.split('=')
        
        novel = Novel(title, author, config, env)
        
        Part.from_file(novel, parts_path)
        Plotline.from_file(novel, plotline_path)
    
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
    path = None
    
    def __init__(self, novel, tag, comment=None):
        self.novel = novel
        self.tag = tag
        self.comment = comment
        os.path.join(self.novel.env.projdir, self.tag)
    
    def create_directory(self):
        os.makedirs(self.path)
    
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
    
    def _is_ch(self, x):
        return x.plotline == self
    
    @property
    def chapters(self):
        return filter(self._is_ch, self.novel.chapters)

class Part(Novelable, Taggable):
    
    novel=None
    title=None
    parent=None
    children=[]
    chapters=[]
    
    def __init__(self, novel, title=None, parent=None):
        self.novel = novel
        self.title = title
        self.parent = parent
        
        if self.parent:
            self.parent.children.append(self)
    
    @property
    def number(self):
        if self.parent:
            return len(self.parent.children)+1
        else:
            return len(self.novel.parts)+1
    
    @property
    def tag(self):
        if self.title is None:
            return '%d' % self.number
        else:
            return '%d__%s' % (self.number, machine_str(self.title))
        
    @classmethod
    def from_file(Klass, novel, path):
        with open(path) as partsfile:
            p_reader = csv.reader(partsfile)
            for row in p_reader:
                (tag, title, parent) = row
                
                parent = novel.find_part(parent)
                part = Part(novel, title, parent=parent)
                
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
        
        if self.number==0:
            self.number = len(novel.chapters)+1
        
        if self.tag is None or len(self.tag) == 0:
            self.reset_tag_and_path()
    
    def reset_tag_and_path(self):
        old_tag = self.tag
        old_path = self.path
        
        if self.title is None or len(self.title) == 0:
            self.tag = '%d' % self.number
        else:
            # Replace all machine-unfriendly chars.
            ttl = machine_str(self.title)
            self.tag = '%d__%s' % (self.number, ttl)
                
        if self.path is None or old_tag != self.tag:
            filename = '%s.%s' % (self.tag,
                                  self.novel.config.get(
                                      'chapter.ext', 'rst'))
            if self.plotline is not None:
                pre = os.path.join(self.novel.env.projdir, self.plotline.tag)
            else:
                pre = os.path.join(self.novel.env.projdir)
            self.path = os.path.join(pre, filename)
        
        if self.path != old_path and None not in (self.path, old_path):
            shutil.copy(old_path, self.path)
            print("[shell] cp %s %s" % (old_path, self.path))
    
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
