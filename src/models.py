#!/usr/bin/env python

import os
import sys

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

class Novel(object):
    title = None
    author = None
    config = {}
    
    plotlines = []
    chapters = []
    versions = []
    drafts = []
    parts = []
    
    def __init__(self, title, author=None, config={}):
        self.title = title
        self.author = author
        self.config = config
                
    def get_config(self, key):
        if key in self.config:
            return DEFAULTS['key'].value

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

class Plotline(Taggable, Commentable, Novelable):
    
    def __init__(self, tag, novel, comment=None):
        super(Taggable, self).__init__(tag)
        super(Commentable, self).__init__(comment)
        super(Novelable, self).__init__(novel)
        
    def get_directory(self):
        os.path.join(os.path.abspath('.'), self.tag)
    
    def create_directory(self):
        os.makedirs(self.get_directory())

class Chapter(Taggable):
    
    title = None
    plotline = None
    path = None
    novel = None
    
    def __init__(self, tag, plotline, novel, title=None):
        super(Taggable, self).__init__(tag)
        super(Commentable, self).__init__(comment)
        super(Novelable, self).__init__(novel)
        self.plotline = plotline
        self.path = os.path.join(
            self.plotline.get_directory(),
            '%s.%s' % self.title,
            novel.get_config('chapter.format'))
        self.title = title

class Version(Taggable, Commentable, Novelable):
    
    label=None
    novel=None
    
    def __init__(self, label, git_hash, tag, novel, comment=None):
        self.label = label
        self.get_hash = git_hash
        super(Taggable, self).__init__(tag)
        super(Novelable, self).__init__(novel)
        super(Commentable, self).__init__(comment)

class Draft(Taggable, Commentable):
    
    def __init__(self, stage, tag, novel, comment=None):
        self.stage = stage
        super(Taggable, self).__init__(tag)
        super(Commentable, self).__init__(comment)
        super(Novelable, self).__init__(novel)
