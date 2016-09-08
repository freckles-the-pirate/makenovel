#!/usr/bin/env python

import os
import sys
import csv
import shutil
import datetime

UNIX_DATE_FORMAT="%Y-%m-%d %H:%M:%S %z"

def machine_str(s):
    s2 = s.lower().replace( ' ', '_' )
    for i in ('!', '.', "'", '"', ','):
        s2 = s2.replace(i, '')
    return s2

def parse_cfg(path):
    cfg = {}
    with open(path, 'r') as cfg_file:
        for line in cfg_file:
            if line[0] != '#':
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
    def merge_changes(Klass, template_config, config_path):
        orig_user_config = parse_cfg(config_path)
        user_config = {}
        changes = False
        for (k, v) in orig_user_config.items():
            if k in template_config:
                user_config.update({k: v})
            else:
                print("[makenovel] config - removed <%s=%s>" % (k,v))
                changes = True
        for (k, v) in template_config.items():
            if k not in user_config:
                user_config.update({k: str(v.thetype(v.value)) or ''})
                changes = True
        
        if not changes:
            return
        
        # first make a backup
        n = 0
        dirname = os.path.dirname(config_path)
        new_cfg_path = os.path.join(dirname, 'makenovel.cfg.%d.old' % n)
        while os.path.exists(new_cfg_path):
            n += 1
            new_cfg_path = os.path.join(dirname, 'makenovel.cfg.%d.old' % n)
        print("[shell] current config backed up as '%s'" % new_cfg_path)
        shutil.copy(config_path, new_cfg_path)
        
        # Now overwrite the new changes.
        with open(config_path, 'w+') as config_file:
            for (k, v) in user_config.items():
                config_file.write("%s=%s\n" % (k, v))
    
    @classmethod
    def get_user(Klass, config_path=None):
        
        if config_path == '':
            config_path = None
        
        config = Klass.get_ref()
        
        if config_path is None or not os.path.exists(config_path):
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
                    
        # Now read the config.
        Klass.merge_changes(config, config_path)
        raw_cfg = parse_cfg(config_path)
        for (k,v) in raw_cfg.items():
            config[k].value = v
        
        return config
    
    def __repr__(self):
        return "Config(%s, %s)" % (self.thetype.__name__,
                                   str(self.thetype(self.value)))

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
        mapping = (
            'first_name',  'email_address', 'last_name', 'middle_name',
            'phone_number', 'street_address', 'city', 'state',
            )
        values = {}
        for m in mapping:
            v = config.get('author.%s' % m)
            if v:
                values[m] = v.value
        return Author(**values)


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
        self.proj_path = os.path.abspath(projdir)
        self.config_path = os.path.abspath(config_path)
        
        self._datafiles = [self.parts_path, self.plotlines_path,
                           self.chapters_path, self.versions_path,
                           self.drafts_path]
        dataparts = ('parts', 'plotlines', 'chapters', 'versions', 'drafts')
        
        self.data_dir = os.path.abspath(os.path.join(self.proj_path, '.novel'))
        
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
            path = os.path.abspath(os.path.dirname('.'))
        novel_path = os.path.abspath(os.path.join(path, '.novel', 'novel'))
        config_path = os.path.expanduser('~/.makenovel/makenovel.cfg')
        if not os.path.exists(novel_path):
            raise RuntimeError(str("%s: not a makenovel project. " % path +
                                   "Please run `mnadmin.py` to create the" +
                                   " makenovel project."))
        
        envdict = parse_cfg(novel_path)
        return NovelEnvironment(path, config_path, envdict.get('last_edit'),
                                envdict.get('title'))
    
    def __repr__(self):
        from pprint import pformat
        return pformat({
            'last_edit': self.last_edit,
            'proj_path' : self.proj_path,
            'config_path' : self.config_path,
            'title': self.title,
            })

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
        #if create and key not in self.config:
        #self.config.update({key: Config("[user]", None)})
        self.config[key].value = value
        print("[makenovel] config - %s=%s" % (key, self.get_config(key)))
        self.write_config()
                
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
        return os.path.join(self.env.proj_path, p)
    
    def write_plotlines(self):
        self._write_csv(self.plotlines, self.env.plotlines_path)
    
    def write_parts(self):
        self._write_csv(self.parts, self.env.parts_path)
    
    def write_chapters(self):
        self._write_csv(self.chapters, self.env.chapters_path)
    
    def write_versions(self):
        self._write_csv(self.versions, self.env.versions_path)
    
    def write_drafts(self):
        self._write_csv(self.drafts, self.env.drafts_path)
    
    def write_config(self):
        with open(self.env.config_path, 'w') as cfg_file:
            for (k, v) in self.config.items():
                cfg_file.write('%s=%s\n' % (k, v.get_value()))
            cfg_file.close()
    
    def bind(self, comment=None, stage=None):
        num = len(self.versions)+1
        # Create a temporary filename for the novel.
        outpath = '%s_%d.%s' % (machine_str(self.title),
                                num,
                             self.get_config('chapter.ext'))
        title = (
            '<h1 id="title">%s<h1>' % self.title,
            '<h1 id="by">by</h1>',
            '<h1 id="author">%s<h1>' % self.author
            )
        with open(outpath, "w+") as outfile:
            for t in title:
                outfile.write('%s\n' % t)
            
            if self.parts and len(self.parts) > 0:
                for p in self.parts:
                    p.create_version(outfile)
            else:
                for c in self.chapters:
                    c.create_version(outfile)
            
            outfile.close()
        self.git_add_files([outpath,])
        self.git_commit_files([outpath,], "Creating version %d" % num)
        
        commits = self.git_file_commits(outpath)
        (git_hash, timestamp) = commits[0]
        
        if stage:
            draft = Draft(self, outpath, stage, git_hash, comment, timestamp)
            self.drafts.append(draft)
            self.write_drafts()
            self.git_commit_files([self.env.drafts_path,],
                                  "Create draft %s" % draft.stage)
            return draft
        else:
            version = Version(self, outpath, git_hash, comment, timestamp)
            self.versions.append(version)
            self.write_versions()
            self.git_commit_files([self.env.versions_path,],
                                  "Create version %s" % version.number)
            return version
    
    def git_file_commits(self, path):
        import subprocess
        git = self.get_config('git.path')
        CMD = [git, 'log', '--pretty="format:%H;%ai"', '--', path]
        print("[shell] %s" % ' '.join(CMD))
        out = subprocess.check_output(CMD, universal_newlines=True)
        lines = out.split('\n')
        commits = []
        for l in lines:
            if len(l) > 0:
                l = l.strip('"')
                (hsh, tstamp) = l.split(';')
                timestamp = datetime.datetime.strptime(tstamp, UNIX_DATE_FORMAT)
                commits.append([hsh, timestamp])
        return commits
    
    def git_add_files(self, paths=[]):
        import subprocess
        
        curr_dir = os.path.abspath(os.path.dirname('.'))
        os.chdir(self.env.proj_path)
        
        if not issubclass(type(paths), list):
            raise TypeError("`paths` must be a list.")
        for i in paths:
            if not os.path.exists(i):
                raise RuntimeError("%s: path not found\n" % i)
            
        git_cmd = self.get_config('git.path')
        for p in paths:
            CMD=[git_cmd, 'add', p]
            print("[shell] %s" % (" ".join(CMD)))
            return subprocess.call(CMD)
        
        os.chdir(curr_dir)
        
    def git_commit_files(self, paths=[], message=None):
        import subprocess
        
        curr_dir = os.path.abspath(os.path.dirname('.'))
        os.chdir(self.env.proj_path)
        
        for p in paths:
            if not os.path.exists(p):
                raise RuntimeError("%s: path not found" % p)
        
        git_cmd = self.get_config('git.path')
        CMD=[git_cmd, 'commit', '-am', '"[autocommit]"']
        if message:
            CMD = [git_cmd, 'commit', '-am', '"%s"' % message]
        print("[shell] %s" % (" ".join(CMD)))
        return subprocess.call(CMD)
    
        os.chdir(curr_dir)
    
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
        
        #from pprint import pformat
        #print("Config: %s" % pformat(cfg))
        author = Author.from_config(cfg)
        
        novel = Novel(env.title, author, cfg, env)
        
        Part.from_file(novel)
        Plotline.from_file(novel)
        Chapter.from_file(novel)
        Version.from_file(novel)
        Draft.from_file(novel)
        
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
    chapters = []
    
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
            plf.close()
    
    def write_row(self, writer):
        writer.writerow([self.tag, self.comment])
    
    def _is_ch(self, x):
        return x.plotline == self

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
            self.parent.children.append(self)
    
    def create_version(self, outfile, h=2):
        fmt = self.novel.get_config("title_format.part")
        outfile.write(fmt % {
            'title': self.title,
            'number': self.number,}
        )
        for child in self.children:
            child.create_version(outfile, h=h+1)
        for chapter in self.chapters:
            chapter.create_version(outfile, h=h+1)
    
    @property
    def number(self):
        if self.parent:
            return self.parent.children.index(self) + 1
        else:
            return self.novel.parts.index(self) + 1
    
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
        writer.writerow([self.title, parent_tag])
    
    def __repr__(self):
        if self.title:
            return 'Part %d: %s' % (self.number, self.title)
        return 'Part %d'

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
            filename = '%s.%s' % (self.tag, self.novel.get_config('chapter.ext'))
            if self.plotline is not None:
                pre = os.path.join(self.novel.env.proj_path, self.plotline.tag)
            else:
                pre = os.path.join(self.novel.env.proj_path)
            self.path = os.path.join(pre, filename)
        
        if old_path is not None:
            old_path = os.path.abspath(old_path)
        
        if self.path is not None:
            self.path = os.path.abspath(self.path)
        
        if None in (old_path, self.path) or old_path == self.path:
            return
        
        shutil.copy(old_path, self.path)
        print("[shell] cp %s %s" % (old_path, self.path))

    def word_count(self):
        count = 0
        if not os.path.exists(self.path):
            return 0
        with open(self.path, 'r+') as f:
            count += len(f.read().split(' '))
            f.close()
        return count
    
    def __repr__(self):
        if self.title:
            return "[%s] Chapter %d: %s" % (self.tag, self.number, self.title)
        return "[%s] Chapter %d" % (self.tag, self.number)
    
    def write_row(self, csvwriter):
        part_tag = None
        plotline_tag = None
        if self.part:
            part_tag = self.part.tag
        if self.plotline:
            plotline_tag = self.plotline.tag
        csvwriter.writerow([self.path,
                             plotline_tag, 
                             part_tag,
                             self.title,
                             ])
    
    @classmethod
    def from_file(self, novel):
        
        n = 0
        
        with open(novel.env.chapters_path) as chaptersfile:
            ch_reader = csv.reader(chaptersfile)
            for row in ch_reader:
                (path, plotline_tag, part_tag, title) = row
                
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
                                  path=path)
                novel.chapters.append(chapter)
                if plotline is not None:
                    plotline.chapters.append(chapter)
                if part is not None:
                    part.chapters.append(chapter)
            chaptersfile.close()
    
    def create_version(self, outfile, h=3):
        format_str = self.novel.get_config("title_format.chapter")
        format_vars = {}
        if '%(number)' in format_str:
            format_vars.update({'number': self.number,})
        if '%(title)' in format_str:
            format_vars.update({'title': self.title,})
        ch_title =  format_str % format_vars
        outfile.write('<h%d class="chapter">%s</h%d>\n' % (h, ch_title, h))
        with open(self.path, 'r') as chapterfile:
            outfile.write(chapterfile.read())
            chapterfile.close()
            outfile.write('\n')

class Version(Taggable, Commentable, Novelable):
    
    novel=None
    git_hash=None
    comment=None
    timestamp=None
    path=None
    
    def __init__(self, novel, path, git_hash, comment=None, timestamp=None):
        self.novel = novel
        self.path = path
        self.git_hash = git_hash
        self.comment = comment
        self.timestamp = timestamp
        if not timestamp:
            self.timestamp = datetime.datetime.now()
    
    @property
    def number(self):
        return self.novel.versions.index(self)+1
    
    def write_row(self, writer):
        writer.writerow([self.path, self.git_hash, self.comment, self.timestamp])
    
    @classmethod
    def from_file(Klass, novel):
        with open(novel.env.versions_path) as versions_file:
            v_reader = csv.reader(versions_file)
            for row in v_reader:
                v = Version(novel, *row)
                novel.versions.append(v)
            versions_file.close()

class Draft(Version):
    
    stage = None
    
    def __init__(self, novel, path, stage, git_hash, comment=None, timestamp=None):
        super(Draft, self).__init__(novel, git_hash, comment, timestamp)
        self.stage = stage
    
    def write_row(self, writer):
        writer.writerow([self.path, self.stage, self.git_hash, self.comment,
                         self.timestamp.strftime(UNIX_DATE_FORMAT)])
    
    @classmethod
    def from_file(Klass, novel):
        with open(novel.env.drafts_path) as drafts_file:
            drafts_reader = csv.reader(drafts_file)
            for row in drafts_reader:
                timestamp = datetime.datetime.strptime(row[-1], UNIX_DATE_FORMAT)
                draft = Draft(novel, *row[:-2])
                novel.drafts.append(draft)
            drafts_file.close()
