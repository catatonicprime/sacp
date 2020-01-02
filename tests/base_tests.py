import unittest
import os
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

    def test_children(self):
        configFile = ConfigFile(file='files/small_httpd.conf')
        self.assertTrue(configFile)
        self.assertTrue(isinstance(configFile, ConfigFile))
        self.assertTrue(configFile.children)
        self.assertGreaterEqual(len(configFile.children), 3)
        comment = configFile.children[0]
        self.assertTrue(isinstance(comment, Comment))
        directive = configFile.children[1]
        self.assertTrue(isinstance(directive, Directive))
        multilineComment = configFile.children[2]
        self.assertTrue(isinstance(multilineComment, Comment))
        self.assertTrue('Multi-line\\\ncomment' in str(multilineComment))


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


class TestDirective(unittest.TestCase):
    def test_name(self):
        configFile = ConfigFile(file='files/small_vhost.conf')
        vhost = configFile.children[0]
        self.assertEqual(vhost.name, "VirtualHost")
        sn = vhost.children[0]
        self.assertEqual(sn.name, "ServerName")


class TestServerName(unittest.TestCase):
    def test_server_name(self):
        configFile = ConfigFile(file='files/small_vhost.conf')
        vhost = configFile.children[0]
        sn = vhost.children[0]
        self.assertEqual(sn.server_name, "github.com")

    def test_empty_server_name(self):
        configFile = ConfigFile(file='files/bad_vhost.conf')
        vhost = configFile.children[0]
        sn = vhost.children[0]
        with self.assertRaises(ValueError):
            err = sn.server_name



class TestServerAlias(unittest.TestCase):
    def test_server_name(self):
        configFile = ConfigFile(file='files/small_vhost.conf')
        vhost = configFile.children[0]
        sa = vhost.children[1]
        self.assertEqual(sa.server_alias, "www.github.com")

    def test_empty_server_name(self):
        configFile = ConfigFile(file='files/bad_vhost.conf')
        vhost = configFile.children[0]
        sa = vhost.children[1]
        with self.assertRaises(ValueError):
            err = sa.server_alias


class TestConfigFile(unittest.TestCase):
    def test_write(self):
        testPath = '/tmp/.small_vhost.conf'
        configFile = ConfigFile(file='files/small_vhost.conf')
        cf_str_left = str(configFile)
        self.assertFalse(os.path.exists(testPath))
        configFile._file = testPath
        configFile.write()
        self.assertTrue(os.path.exists(testPath))
        configFile = ConfigFile(file=testPath)
        cf_str_right = str(configFile)
        self.assertEquals(cf_str_left, cf_str_right)
        os.remove(testPath)


class TestNodeVisitors(unittest.TestCase):
    def __init__(self, methodName="runTest"):
        (unittest.TestCase).__init__(self, methodName=methodName)
        self._parsed_nodes = ConfigFile(file='files/small_visitors.conf').children
        self._df_node_visit_index = 0
        self._bf_node_visit_index = 0
        self._bf_node_list = []
        self._df_node_list = []

    def depth_first_visitor(self, node):
        self._df_node_list.append((node, self._df_node_visit_index))
        self._df_node_visit_index += 1

    def breadth_first_visitor(self, node):
        self._bf_node_list.append((node, self._bf_node_visit_index))
        self._bf_node_visit_index += 1

    def test_node_visitor(self):
        NodeVisitor(self._parsed_nodes).visit(visitor=self.depth_first_visitor)
        self.assertEqual(self._df_node_list[0][1], 0)
        self.assertEqual(self._df_node_list[1][1], 1)
        self.assertEqual(self._df_node_list[2][1], 2)
        self.assertEqual(self._df_node_list[3][1], 3)
        self.assertTrue(isinstance(self._df_node_list[0][0], VirtualHost))
        self.assertTrue(isinstance(self._df_node_list[1][0], ServerName))
        self.assertTrue(isinstance(self._df_node_list[2][0], VirtualHost))
        self.assertTrue(isinstance(self._df_node_list[3][0], ServerName))

    def test_bfnode_visitor(self):
        BFNodeVisitor(self._parsed_nodes).visit(visitor=self.breadth_first_visitor)
        self.assertEqual(self._bf_node_list[0][1], 0)
        self.assertEqual(self._bf_node_list[1][1], 1)
        self.assertEqual(self._bf_node_list[2][1], 2)
        self.assertEqual(self._bf_node_list[3][1], 3)
        self.assertTrue(isinstance(self._bf_node_list[0][0], VirtualHost))
        self.assertTrue(isinstance(self._bf_node_list[1][0], VirtualHost))
        self.assertTrue(isinstance(self._bf_node_list[2][0], ServerName))
        self.assertTrue(isinstance(self._bf_node_list[3][0], ServerName))


class TestDefaultFactory(unittest.TestCase):
    def test_factory_builds(self):
        configFile = ConfigFile(file='files/factory.conf')
        self.assertTrue(isinstance(configFile.children[0], Comment))
        self.assertTrue(isinstance(configFile.children[1], Comment))
        self.assertTrue(isinstance(configFile.children[2], Directive))
        self.assertTrue(isinstance(configFile.children[3], Directive))
        self.assertTrue(isinstance(configFile.children[4], ScopedDirective))
        self.assertTrue(isinstance(configFile.children[5], Directory))
        self.assertTrue(isinstance(configFile.children[6], Directory))
        self.assertTrue(isinstance(configFile.children[7], DirectoryMatch))
        self.assertTrue(isinstance(configFile.children[8], Files))
        self.assertTrue(isinstance(configFile.children[9], Files))
        self.assertTrue(isinstance(configFile.children[10], FilesMatch))
        self.assertTrue(isinstance(configFile.children[11], Location))
        self.assertTrue(isinstance(configFile.children[12], LocationMatch))
        self.assertTrue(isinstance(configFile.children[13], Proxy))
        self.assertTrue(isinstance(configFile.children[14], ProxyMatch))