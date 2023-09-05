import unittest
import os
import tempfile
from sacp import *


class TestInclude(unittest.TestCase):
    def test_path(self):
        # Ensure we have an 'Include' node
        parser = Parser(data='Include files/small_vhost.conf')
        self.assertTrue(parser)
        self.assertEqual(len(parser.nodes), 1, 'Parser returned incorrect number of nodes for Include')
        include = parser.nodes[1]
        self.assertTrue(isinstance(include, Include))

        # Ensure the path matches the expected path above.
        self.assertEqual(include.path, 'files/small_vhost.conf', 'Include path does not match expected.')

    def test_path_absolute_glob(self):
        # Ensure we have an 'Include' node
        parser = Parser(data="Include {}/files/glob/*.conf".format(os.getcwd()))
        self.assertTrue(parser)
        self.assertEqual(len(parser.nodes), 1, 'Parser returned incorrect number of nodes for Include')
        include = parser.nodes[0]
        self.assertTrue(isinstance(include, Include))

    def test_exceptions(self):
        with self.assertRaises(IncludeError):
            Parser(data='Include')
        with self.assertRaises(ValueError):
            Parser(data='Include nonexistent.conf')

    def test_child_tokens_not_accessed(self):
        include = Parser(data='Include files/small_vhost.conf').nodes[0]
        self.assertEqual(len(include.tokens), 3)


class TestIncludeOptional(unittest.TestCase):
    def test_path(self):
        # Ensure we have an 'Include' node
        parser = Parser(data='IncludeOptional files/small_vhost.conf')
        self.assertTrue(parser)
        self.assertEqual(len(parser.nodes), 1, 'Parser returned incorrect number of nodes for IncludeOptional')
        include = parser.nodes[0]
        self.assertTrue(isinstance(include, IncludeOptional))

        # Ensure the path matches the expected path above.
        self.assertEqual(include.path, 'files/small_vhost.conf', 'IncludeOptional path does not match expected.')

    def test_exceptions(self):
        with self.assertRaises(IncludeError):
            Parser(data='IncludeOptional')

    def test_failed_include(self):
        Parser(data='IncludeOptional nonexistent.conf')


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

    def test_parser(self):
        nodes = Parser(data="ServerName github.com").nodes
        self.assertEqual(len(nodes), 1)
        with self.assertRaises(ValueError):
            Parser(data="ServerName github.com", nodefactory=0)
        with self.assertRaises(ValueError):
            Parser(data="ServerName github.com", acl=NodeFactory())

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

    def test_exceptions(self):
        with self.assertRaises(ValueError):
            configFile = ConfigFile(file='files/lex_errors.conf')


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

        # Test the depth of the node.
        self.assertEqual(node.depth-1, node.parent.depth)

    def test_append_children(self):
        # Ensure we have some structure.
        configFile = ConfigFile(file='files/small_vhost.conf')

        # Ensure we have a new node, it can be blank.
        node = Node()
        self.assertTrue(node)

        # Ensure the configFile can be successfully appended.
        node.append_children([configFile])
        self.assertGreaterEqual(node.children.index(configFile), 0)

        # Ensure the configFile has been modified to have the correct parent.
        self.assertEqual(configFile.parent, node)

        # Test the depth of the node.
        self.assertEqual(configFile.depth-1, configFile.parent.depth)

    def test_node_factory(self):
        nf = NodeFactory()
        node = Node()
        with self.assertRaises(NotImplementedError):
            nf.build(node)


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
        self.assertTrue(sn.isValid)
        self.assertEqual(sn.arguments[0], "github.com")
        self.assertEqual(vhost.server_name.arguments[0], "github.com")

    def test_empty_server_name(self):
        configFile = ConfigFile(file='files/bad_vhost.conf')
        vhost = configFile.children[0]
        sn = vhost.children[0]
        self.assertFalse(sn.isValid)

    def test_bad_servername(self):
        nodes = Parser(data='ServerName invalid/domain').nodes
        sn = nodes[0]
        self.assertFalse(sn.isValid)


class TestServerAlias(unittest.TestCase):
    def test_server_alias(self):
        configFile = ConfigFile(file='files/small_vhost.conf')
        vhost = configFile.children[0]
        sa = vhost.children[1]
        self.assertTrue(sa.isValid)
        self.assertEqual(sa.arguments[0], "www.github.com")
        self.assertEqual(vhost.server_alias.arguments[0], "www.github.com")
        self.assertEqual(sa.arguments[1], "m.github.com")
        self.assertEqual(vhost.server_alias.arguments[1], "m.github.com")

    def test_bad_server_alias(self):
        nodes = Parser(data='ServerAlias www.github.com bad/alias github.com').nodes
        sa = nodes[0]
        self.assertFalse(sa.isValid)

    def test_empty_server_alias(self):
        configFile = ConfigFile(file='files/bad_vhost.conf')
        vhost = configFile.children[0]
        sa = vhost.children[1]
        self.assertFalse(sa.isValid)


class TestConfigFile(unittest.TestCase):
    def test_write(self):
        testPath = tempfile.TemporaryFile().name
        configFile = ConfigFile(file='files/small_vhost.conf')
        cf_str_left = str(configFile)
        self.assertFalse(os.path.exists(testPath))
        configFile._file = testPath
        configFile.write()
        self.assertTrue(os.path.exists(testPath))
        configFile = ConfigFile(file=testPath)
        cf_str_right = str(configFile)
        self.assertEqual(cf_str_left, cf_str_right)
        os.remove(testPath)


class TestNodeVisitors(unittest.TestCase):
    def __init__(self, methodName="runTest"):
        (unittest.TestCase).__init__(self, methodName=methodName)
        self._parsed_nodes = ConfigFile(file='files/small_visitors.conf').children

    def reset_test_state(self):
        self._node_visit_index = 0
        self._node_list = []

    def visitor(self, node):
        self._node_list.append((node, self._node_visit_index))
        self._node_visit_index += 1

    def test_node_visitor(self):
        self.reset_test_state()
        NodeVisitor(self._parsed_nodes).visit(visitor=self.visitor)
        self.assertEqual(self._node_visit_index, 3)
        self.assertEqual(self._node_list[0][1], 0)
        self.assertEqual(self._node_list[1][1], 1)
        self.assertTrue(isinstance(self._node_list[0][0], VirtualHost))
        self.assertTrue(isinstance(self._node_list[2][0], VirtualHost))

    def test_dfnode_visitor(self):
        self.reset_test_state()
        DFNodeVisitor(self._parsed_nodes).visit(visitor=self.visitor)
        self.assertEqual(self._node_visit_index, 4)
        self.assertEqual(self._node_list[0][1], 0)
        self.assertEqual(self._node_list[1][1], 1)
        self.assertEqual(self._node_list[2][1], 2)
        self.assertEqual(self._node_list[3][1], 3)
        self.assertTrue(isinstance(self._node_list[0][0], VirtualHost))
        self.assertTrue(isinstance(self._node_list[1][0], ServerName))
        self.assertTrue(isinstance(self._node_list[2][0], VirtualHost))
        self.assertTrue(isinstance(self._node_list[3][0], ServerName))

    def test_bfnode_visitor(self):
        self.reset_test_state()
        BFNodeVisitor(self._parsed_nodes).visit(visitor=self.visitor)
        self.assertEqual(self._node_visit_index, 4)
        self.assertEqual(self._node_list[0][1], 0)
        self.assertEqual(self._node_list[1][1], 1)
        self.assertEqual(self._node_list[2][1], 2)
        self.assertEqual(self._node_list[3][1], 3)
        self.assertTrue(isinstance(self._node_list[0][0], VirtualHost))
        self.assertTrue(isinstance(self._node_list[1][0], VirtualHost))
        self.assertTrue(isinstance(self._node_list[2][0], ServerName))
        self.assertTrue(isinstance(self._node_list[3][0], ServerName))


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


class TestScopedDirective(unittest.TestCase):
    def test_argument_child_tokens(self):
        configFile = ConfigFile(file='files/small_vhost.conf')
        self.assertTrue(isinstance(configFile.children[0], ScopedDirective))
        sd = configFile.children[0]
        self.assertTrue(len(sd.arguments) == 1)


class TestLineEnumerator(unittest.TestCase):
    def test_line_numbers(self):
        cf = ConfigFile(file='files/factory.conf')
        le = LineEnumerator(nodes=[cf])
        self.assertTrue(isinstance(le.lines[0][0], Comment))
        self.assertTrue(le.lines[0][1] == 1)
        self.assertTrue(isinstance(le.lines[1][0], Comment))
        self.assertTrue(le.lines[1][1] == 2)
        self.assertTrue(isinstance(le.lines[2][0], Directive))
        self.assertTrue(le.lines[2][1] == 5)


    def test_line_number_recurse_include(self):
        parser = Parser(data='Directive simple\nInclude files/factory.conf\nDirective simple')
        le = LineEnumerator(nodes=parser.nodes)
        self.assertTrue(isinstance(le.lines[0][0], Directive))
        self.assertTrue(le.lines[0][1] == 1)
        self.assertTrue(isinstance(le.lines[1][0], Include))
        self.assertTrue(le.lines[1][1] == 2)
        self.assertTrue(isinstance(le.lines[-1][0], Directive))
        self.assertTrue(le.lines[2][1] == 3)

    def test_line_number_recurse_include_optional(self):
        parser = Parser(data='Directive simple\nIncludeOptional files/factory.conf\nDirective simple')
        le = LineEnumerator(nodes=parser.nodes)
        self.assertTrue(isinstance(le.lines[0][0], Directive))
        self.assertTrue(le.lines[0][1] == 1)
        self.assertTrue(isinstance(le.lines[1][0], IncludeOptional))
        self.assertTrue(le.lines[1][1] == 2)
        self.assertTrue(isinstance(le.lines[-1][0], Directive))
        self.assertTrue(le.lines[2][1] == 3)
