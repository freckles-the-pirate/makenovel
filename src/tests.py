#!/usr/bin/env python3

import logging
import logging.config

logging.config.fileConfig("./logging.conf")
logger = logging.getLogger("testLogger")

import unittest
import os
import sys
import shutil

from models import (
    Config,
    Author,
    NovelEnvironment,
    Novel,
    Plotline,
    Part,
    Chapter,
    Version,
    Draft
    )
from mnadmin import create_project

from makenovel import *

class TestNovel(unittest.TestCase):
    
    CURRDIR = os.path.abspath( os.path.dirname(__file__) )
    
    novel = None
    env = None
    proj_path = None
    
    def setUp(self):
        
        create_project("testnovel", "Test Novel", "ancient")
        
        self.proj_path = os.path.join(TestNovel.CURRDIR, "testnovel")
        
        config = Config.get_ref()
        
        title = "Test Novel"
        author = Author("John", "Smith")
        
        env = NovelEnvironment.load(self.proj_path)
        
        self.novel = Novel(title, author, config, env)
        self.novel.parts = [Part(self.novel), Part(self.novel),]
        self.novel.plotlines = [Plotline(self.novel, "main", "Main Plotline"),
                                 Plotline(self.novel, "side", "Side plot"),]
        self.novel.write_parts()
        self.novel.write_plotlines()
        self.novel.git_commit_data(self.novel.env.plotlines_path,
                                   message="Add test plotlines")
        self.novel.git_commit_data(self.novel.env.parts_path,
                                   message='add test parts')
        os.chdir(self.proj_path)
        
    
    def testBasicAdds(self):
        self.assertEqual(len(self.novel.parts), 2)
        self.assertEqual(len(self.novel.plotlines), 2)
    
    def testList(self):
        # Since this is mainly visual, just ensure the methods run without
        # incident.
        list_plotlines(self.novel)
        list_parts(self.novel)
        list_chapters(self.novel)
        list_versions(self.novel)
        list_drafts(self.novel)
    
    def test_show(self):
        show_novel(self.novel)
        show_part(self.novel, "1")
        show_plotline(self.novel, "main")
    
    """
    " Add
    """
    
    def testAddPlotline(self):
        self.assertEqual(len(self.novel.plotlines), 2)
        with open(self.novel.env.plotlines_path) as plf:
            for l in plf:
                print("|%s" % l)
            plf.close()
        add_plotline(self.novel, "minor", "Minor plotline")
        self.assertEqual(len(self.novel.plotlines), 3)
    
    def testAddPart(self):
        self.assertEqual(len(self.novel.parts), 2)
        add_part(self.novel)
        self.assertEqual(len(self.novel.parts), 3)
        for i in range(0, len(self.novel.parts)):
            self.assertEqual(self.novel.parts[i].number, i+1)
    
    def testAddChapter(self):
        self.assertEqual(len(self.novel.chapters), 0)
        add_chapter(self.novel, "main", "First Test Chapter", "1")
        self.assertEqual(len(self.novel.chapters), 1)
        self.assertIsNotNone(self.novel.find_chapter("1__first_test_chapter"))
        part = self.novel.find_part("1")
        chapter = self.novel.find_chapter("1__first_test_chapter")
        self.assertIsNotNone(chapter)
        self.assertIn(chapter, part.chapters)
        self.assertIn(chapter, self.novel.parts[0].chapters)
        self.assertNotIn(chapter, self.novel.parts[1].chapters)
    
    """
    " Update
    """
    
    def test_update_part(self):
        add_part(self.novel, "Part 1 Original")
        add_part(self.novel, "Part 2 Original")
        self.assertEqual(len(self.novel.parts), 4)
        
        p2 = self.novel.find_part("3__part_2_original")
        p1 = self.novel.find_part("4__part_1_original")
        
        update_part(self.novel, tag="3__part_1_original", title="Part 1 Modified")
        self.assertEqual(self.novel.parts[0].title, "Part 1 Modified")
        update_part(self.novel, "4__part_2_original", before_tag="1__part_1_modified")
        self.assertEqual(self.novel.parts[0], p2)
        self.assertEqual(self.novel.parts[1], p1)
        
        # The titles and tags must be different, though.
        self.assertEqual(self.novel.parts[0].tag, "3__part_2_original")
        self.assertEqual(self.novel.parts[1].tag, "4__part_1_modified")
        self.assertEqual(self.novel.parts[0].tag, "3__part_2_original")
        self.assertEqual(self.novel.parts[1].tag, "4__part_1_modified")
    
    def testUpdateChapters(self):
        self.tearDown()
        self.setUp()
        add_part(self.novel)
        add_part(self.novel)
        t = '1'
        add_chapter(self.novel, "main", title="AAA", part_tag=t)
        add_chapter(self.novel, "main", title="BBB", part_tag=t)
        
        #self.novel.load(self.proj_path)
        
        parts = self.novel.parts
        p1 = parts[0]
        p2 = parts[1]
        self.assertEqual(len(p1.chapters), 3)
        self.assertEqual(len(p2.chapters), 0)
        
        update_chapter(self.novel, "1__aaa", title="CCC")
        update_chapter(self.novel, "2__bbb", title="DDD", part_tag='2')
        
        self.assertEqual(self.novel.parts[0].children, 1)
        self.assertEqual(self.novel.parts[1].children, 2)
        self.assertEqual(self.novel.chapters[0].tag, "1__ccc")
        self.assertEqual(self.novel.chapters[1].tag, "1__ddd")
    
    def tearDown(self):
        os.chdir(os.path.abspath(os.path.join(self.proj_path, '..')))
        if os.path.exists(self.proj_path):
            shutil.rmtree(self.proj_path)
        self.novel = None
        self.env = None
        self.proj_path = None

if __name__=='__main__':
    unittest.main()