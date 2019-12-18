import sys
sys.path.append('../')

import unittest
from sacp import *

class TestInclude(unittest.TestCase):
    def test_path(self):
        parser = Parser(data='Include files/small_vhost.conf')
        self.assertTrue(parser)
        self.assertEqual(len(parser.nodes), 1, 'Parser returned incorrect number of nodes for Include')
        include = parser.nodes[0]
        self.assertTrue(isinstance(include, Include))
        self.assertEqual(include.path, 'files/small_vhost.conf', 'Include path does not match expected.')

class TestParser(unittest.TestCase):
    def test_parents(self):
        configFile = ConfigFile(file='files/small_vhost.conf')
        self.assertTrue(configFile)
        self.assertTrue(isinstance(configFile, ConfigFile))
        self.assertTrue(configFile.children)
        vhost = configFile.children[0]
        self.assertTrue(isinstance(vhost, VirtualHost))
        self.assertTrue(isinstance(vhost._parent, ConfigFile))
        directive = vhost.children[0]
        self.assertTrue(isinstance(directive, Directive))
        self.assertTrue(isinstance(directive._parent, VirtualHost))