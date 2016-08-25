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
    
    def __init__(self, methodName):
        
        self.proj_path = os.path.join(TestNovel.CURRDIR, "testnovel")
        
        config = Novel.getUserConfig()
            
        create_project("testnovel", "Test Novel", "ancient")
        
        title = "Test Novel"
        author = Author("John", "Smith")
        
        env = NovelEnvironment(projdir = self.proj_path)
        
        self.novel = Novel(title, author, config, env)
        self.novel.parts = [Part(self.novel), Part(self.novel),]
        self.novel.plotlines = [Plotline(self.novel, "main", "Main Plotline"),
                                 Plotline(self.novel, "side", "Side plot"),]
        self.novel.write_parts()
        self.novel.write_plotlines()
        self.novel.git_commit_data(Novel.PLOTLINESFILE,
                                   message="Add test plotlines")
        self.novel.git_commit_data(Novel.PARTSFILE, message='add test parts')
        
        super(TestNovel, self).__init__(methodName)
    
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
        pth = os.path.join(self.proj_path, Novel.PLOTLINESFILE)
        with open(pth) as plf:
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
        if self.proj_path and os.path.exists(self.proj_path):
            print("Removing %s" % self.proj_path)
            shutil.rmtree(self.proj_path)
        self.novel = None
        self.env = None
        self.proj_path = None

if __name__=='__main__':
    unittest.main()