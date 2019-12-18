import unittest
from sacp import *


class TestInclude(unittest.TestCase):
    def test_path(self):
        # Ensure we have an 'Include' node
        parser = Parser(data='Include files/small_vhost.conf')
        self.assertTrue(parser)
        self.assertEqual(len(parser.nodes), 1, 'Parser returned incorrect number of nodes for Include')
        include = parser.nodes[0]
        self.assertTrue(isinstance(include, Include))

        # Ensure the path matches the expected path above.
        self.assertEqual(include.path, 'files/small_vhost.conf', 'Include path does not match expected.')


class TestParser(unittest.TestCase):
    def test_parents(self):
        # Ensure we have a known structure.
        configFile = ConfigFile(file='files/small_vhost.conf')
        self.assertTrue(configFile)
        self.assertTrue(isinstance(configFile, ConfigFile))
        self.assertTrue(configFile.children)

        # Extract the VirtualHost from the structure.
        vhost = configFile.children[0]
        self.assertTrue(isinstance(vhost, VirtualHost))
        self.assertTrue(isinstance(vhost._parent, ConfigFile))

        # Extract the first child, which should be a Directive, from the VirtualHost
        directive = vhost.children[0]
        self.assertTrue(isinstance(directive, Directive))

        # Ensure the Directives parent is properly typed to a VirtualHost
        self.assertTrue(isinstance(directive._parent, VirtualHost))

class TestNode(unittest.TestCase):
    def test_append_child(self):
        # Ensure we have some structure.
        configFile = ConfigFile(file='files/small_vhost.conf')

        # Ensure we have a new node, it can be blank.
        node = Node()
        self.assertTrue(node)

        # Ensure the node can be successfully appended.
        configFile.append_child(node)
        self.assertGreaterEqual(configFile.children.index(node), 0)

        # Ensure the node has been modified to have the correct parent.
        self.assertEqual(node.parent, configFile)