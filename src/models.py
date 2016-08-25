#!/usr/bin/env python

import os
import sys
import csv
import shutil

def machine_str(s):
    s2 = s.lower().replace( ' ', '_' )
    for i in ('!', '.', "'", '"', ','):
        s2 = s2.replace(i, '')
    return s2

def parse_cfg(path):
    cfg = {}
    with open(path, 'r') as cfg_file:
        for line in cfg_file:
            if not line[0] != '#':
                (x,y) = line.strip().split('=')
                cfg.update({x: y,})
        cfg_file.close()
    return cfg

def load_csv(path, mode='r'):
    rows = []
    with open(path, mode) as csvfile:
        reader = csv.reader(csvfile)
        rows = [r for r in reader]
        csvfile.close()
    return rows

class Config(object):
    doc=None
    default_value=None
    value=None
    thetype=None
    
    def __init__(self, doc=None, default_value=None, thetype=str):
        self.doc = doc
        self.default_value = default_value
        self.thetype=thetype
    
    def get_value(self):
        v = self.default_value
        if self.value:
            v = self.value
        return self.thetype(v)
    
    @classmethod
    def get_ref(Klass):
        configs = {}
        config_ref = os.path.join(
            os.path.abspath(
                os.path.dirname(__file__)),
            'config.csv')
        with open(config_ref) as configsfile:
            reader = csv.reader(configsfile)
            for row in reader:
                c = Klass(row[1], row[2])
                configs.update({row[0]: c,})
            configsfile.close()
        return configs
    
    
    @classmethod
    def get_user(Klass, config_path=None):
        
        if config_path == '':
            config_path = None
        
        config = Klass.get_ref()
        
        if config_path is None:
            config_dir = os.path.expanduser( '~/.makenovel')
            config_path = os.path.join(config_dir, 'makenovel.cfg')
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)
            if not os.path.exists(config_path):
                print("[makenovel] creating config file '%s'" % config_path)
                with open(config_path, 'w') as cfg_file:
                    for (k,v) in config.items():
                        cfg_file.write('%s=%s\n' % (k, v.get_value()))
                    cfg_file.close()
        return config

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
    
    @classmethod
    def from_config(Klass, config):
        return Author(
            config.get('author.first_name'),
            config.get('author.last_name'),
            config.get('author.middle_name'),
            config.get('author.email_address'),
            config.get('author.phone_number'),
            config.get('author.street_address'),
            config.get('author.city'),
            config.get('author.state')
            )


class NovelEnvironment(object):
    
    last_edit = None
    
    proj_path = None
    
    # data paths
    data_dir = None
    novel_path = None
    parts_path = None
    plotlines_path = None
    chapters_path = None
    versions_path = None
    drafts_path = None
    
    config_path = None
    title = None
    
    def __init__(self, projdir=None, config_path=None, last_edit=None, title=None):
        self.last_edit = last_edit
        self.proj_path = projdir
        self.config_path = config_path
        
        self._datafiles = [self.parts_path, self.plotlines_path,
                           self.chapters_path, self.versions_path,
                           self.drafts_path]
        dataparts = ('parts', 'plotlines', 'chapters', 'versions', 'drafts')
        
        self.data_dir = os.path.join(self.proj_path, '.novel')
        
        self.novel_path = os.path.join(self.data_dir, 'novel')
        self.parts_path = os.path.join(self.data_dir, 'parts.csv')
        self.plotlines_path = os.path.join(self.data_dir, 'plotlines.csv')
        self.chapters_path = os.path.join(self.data_dir, 'chapters.csv')
        self.versions_path = os.path.join(self.data_dir, 'versions.csv')
        self.drafts_path = os.path.join(self.data_dir, 'drafts.csv')
        
        self.title = title
    
    @classmethod
    def load(Klass, path=None):
        if not path:
            path = os.path.dirname('.')
        cfg_path = os.path.join(path, '.novel', 'novel')
        if not os.path.exists(cfg_path):
            raise RuntimeError(str("%s: not a makenovel project. " +
                                   "Please run `mnadmin.py` to create the" +
                                   " makenovel project."))
        
        envdict = parse_cfg(cfg_path)
        return NovelEnvironment( path, cfg_path, envdict.get('last_edit'),
                                envdict.get('title'))

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
    
    def set_config(self, key, value, create=False):
        if create and key not in self.config:
            self.config.update({key: Config("[user]", None)})
        self.config[key].value = value
                
    def get_config(self, key):
        if key is None:
            raise ValueError("%s not found in %s" % (
                key, list(self.config.keys())))
        c = self.config[key]
        v = c.value or c.default_value
        if v is None:
            return v
        return c.thetype(v)
    
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
        p = os.path.join(self.env.proj_path, path)
        with open(path, 'w') as csv_file:
            csv_writer = csv.writer(csv_file)
            for obj in obj_set:
                obj.write_row(csv_writer)
            csv_file.close()
    
    def _get_data_path(self, p):
        return os.path.join(self.env.projdir, p)
    
    def write_plotlines(self):
        self._write_csv(self.plotlines, self.env.plotlines_path)
    
    def write_parts(self):
        self._write_csv(self.parts, self.env.parts_path)
    
    def write_chapters(self):
        self._write_csv(self.chapters, self.env.chapters_path)
    
    def write_config(self):
        with open(self.env.config_path, 'w') as config_file:
            for (k, v) in self.config.items():
                config_file.write('%s=%s\n' % (k, v.get_value()))
            config_file.close()
    
    def git_add_files(self, paths=[]):
        import subprocess
        if not issubclass(paths, list):
            raise TypeError("`paths` must be a list.")
        for i in paths:
            if not os.path.exists(i):
                raise RuntimeError("%s: path not found\n" % i)
            
        git_cmd = self.get_config('git.path')
        CMD=[git_cmd, 'add', " ".join('"%s"' % p for p in paths)]
        print("[shell] %s" % (" ".join(CMD)))
        return subprocess.call(CMD)
        
    def git_commit_files(self, paths=[], message=None):
        import subprocess
        for p in paths:
            if not os.path.exists(p):
                raise RuntimeError("%s: path not found" % p)
        
        git_cmd = self.get_config('git.path')
        CMD=[git_cmd, 'commit']
        if message:
            CMD.extend(['-m', '"%s"' % message])
        print("[shell] %s" % (" ".join(CMD)))
        return subprocess.call(CMD)
    
    def git_commit_data(self, datafile, message=None):
        self.git_commit_files([datafile,], message)
        
    @classmethod
    def load(Klass, path=None):
        """
        @brief Given a project's path, load the novel from that path.
        
        :param path: Project's path. If None, use the shell's current working
            directory.
        :type path: str
        
        :returns: A new Novel
        """
        
        env = NovelEnvironment.load(path)
        cfg = Config.get_user()
        
        author = Author.from_config(cfg)
        
        novel = Novel(env.title, author, cfg, env)
        
        Part.from_file(novel)
        Plotline.from_file(novel)
        Chapter.from_file(novel)
        
        return novel
    
    def __repr__(self):
        return "%s by %s" % (self.title, self.author)


class Novelable(object):
    novel = None
    
    def __init__(self, novel):
        self.novel = novel
    
    def write_row(self):
        raise NotImplementedError()


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
    
    def create_directory(self):
        os.makedirs(self.path)
    
    def __repr__(self):
        return "<Plotline (tag=\"%s\", novel=\"%s\", comment=\"%s\")>" % (
            self.tag, self.novel, self.comment)
    
    @classmethod
    def from_file(Klass, novel):
        with open(novel.env.plotlines_path) as plf:
            pl_reader = csv.reader(plf)
            for row in pl_reader:
                p = Plotline(novel, row[0], row[1])
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
    number=0
    
    def __init__(self, novel, title=None, parent=None):
        self.novel = novel
        self.title = title
        self.parent = parent
        
        if self.parent:
            self.number = len(self.parent.children)+1
        else:
            self.number = len(self.novel.parts)+1
        
        if self.parent:
            self.parent.children.append(self)
    
    @property
    def tag(self):
        if self.title is None:
            return '%d' % self.number
        else:
            return '%d__%s' % (self.number, machine_str(self.title))
        
    @classmethod
    def from_file(Klass, novel):
        with open(novel.env.parts_path) as partsfile:
            p_reader = csv.reader(partsfile)
            for row in p_reader:
                (title, parent) = row
                
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
    def from_file(self, novel):
        
        n = 0
        
        with open(novel.env.chapters_path) as chaptersfile:
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
