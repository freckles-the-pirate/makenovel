#!/usr/bin/env python

import os
import sys

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
    
    def __init__(self, title, author=None):
        self.title = title
        self.author = author

class TaggableObject(object):
    tag = None
    
    def __init__(self, tag):
        self.tag = tag

class CommentableObject(object):
    comment=None
    
    def __init__(self, comment=None):
        self.comment = comment

class Plotline(TaggableObject, CommentableObject):
    
    def __init__(self, tag, comment=None):
        super(self, TaggableObject).__init__(tag)
        super(self, CommentableObject).__init__(comment)
        
    def get_directory(self):
        os.path.join(os.path.abspath('.'), self.tag)
    
    def create_directory(self):
        os.makedirs(self.get_directory())

class Chapter(TaggableObject):
    
    title = None
    plotline = None
    path = None
    novel = None
    
    def __init__(self, tag, plotline, novel, title=None):
        super(TaggableObject, self).__init__(tag)
        self.plotline = plotline
        self.path = os.path.join(
            self.plotline.get_directory(),
            '%s.%s' % self.title,
            novel.get_config('chapter.format'))
        self.title = title
