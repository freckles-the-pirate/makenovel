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
    
    novel = None
    env = None
    CURRDIR = os.path.abspath( os.path.dirname(__file__) )
    proj_path = None
    
    def setUp(self):
        
        self.proj_path = os.path.join(TestNovel.CURRDIR, "testnovel")
        
        if os.path.exists(self.proj_path):
            shutil.rmtree(self.proj_path)
            
        create_project("testnovel", "Test Novel", "ancient")
        
        title = "Test Novel"
        config = {
            "chapter.ext": Config("File extension for chapter files.", "rst"),
            }
        author = Author("John", "Smith")
        
        env = NovelEnvironment(projdir = self.proj_path)
        
        self.novel = Novel(title, author, config, env)
        self.novel.parts.extend([Part(self.novel), Part(self.novel),])
        self.novel.plotlines.extend([Plotline(self.novel, "main", "Main Plotline"),
                                 Plotline(self.novel, "side", "Side plot"),])
    
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
        print("PLF!!!!")
        with open(PLOTLINESFILE) as plf:
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
    
    def tearDown(self):
        shutil.rmtree(self.proj_path)
        self.novel = None
        self.env = None
        self.proj_path = None


if __name__=='__main__':
    unittest.main()