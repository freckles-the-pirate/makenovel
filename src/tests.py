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
        
        env = NovelEnvironment(projdir = self.proj_path)
        
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
        self.assertIn(self.novel.chapters[0], part.chapters)
    
    def tearDown(self):
        os.chdir(os.path.abspath(os.path.join(self.proj_path, '..')))
        if os.path.exists(self.proj_path):
            shutil.rmtree(self.proj_path)
        self.novel = None
        self.env = None
        self.proj_path = None

if __name__=='__main__':
    unittest.main()