from pygments.lexer import RegexLexer, default, words, bygroups, include, using
from pygments.token import Text, Comment, Operator, Keyword, Name, String, \
    Number, Punctuation, Whitespace, Literal
from pygments.lexers.shell import BashLexer
from pygments.lexers.data import JsonLexer

from .node import *
import pygments
import glob


# Stolen from pygments for the purposes of fixing...
class ApacheConfLexer(RegexLexer):
    """
    Lexer for configuration files following the Apache config file
    format.

    .. versionadded:: 0.6
    """

    name = 'ApacheConf'
    aliases = ['apacheconf', 'aconf', 'apache']
    filenames = ['.htaccess', 'apache.conf', 'apache2.conf']
    mimetypes = ['text/x-apacheconf']
    flags = re.MULTILINE | re.IGNORECASE

    tokens = {
        'root': [
            (r'\s+', Text),
            (r'#(.*\\\n)+.*$|(#.*?)$', Comment),
            (r'(<[^\s>]+)(?:(\s+)(.*))?(>)',
             bygroups(Name.Tag, Text, String, Name.Tag)),
            (r'([a-z]\w*)(\s+)',
             bygroups(Name.Builtin, Text), 'value'),
            (r'\.+', Text),
        ],
        'value': [
            (r'\\\n', Text),
            (r'$', Text, '#pop'),
            (r'\\', Text),
            (r'[^\S\n]+', Text),
            (r'\d+\.\d+\.\d+\.\d+(?:/\d+)?', Number),
            (r'\d+', Number),
            (r'/([a-z0-9][\w./-]+)', String.Other),
            (r'(on|off|none|any|all|double|email|dns|min|minimal|'
             r'os|productonly|full|emerg|alert|crit|error|warn|'
             r'notice|info|debug|registry|script|inetd|standalone|'
             r'user|group)\b', Keyword),
            (r'"([^"\\]*(?:\\(.|[\n])[^"\\]*)*)"', String.Double),
            (r'[^\s"\\]+', Text)
        ],
    }


class Parser:
    def __init__(self, data, nodefactory=None, parent=None):
        # Use specified node generator to glenerate nodes or use the default.
        self._nodefactory = nodefactory
        if not self._nodefactory:
            self._nodefactory = DefaultFactory()

        self.nodes = []
        self._stream = pygments.lex(data, ApacheConfLexer())
        node = self.parse(parent=parent)
        while node:
            self.nodes.append(node)
            node = self.parse(parent=parent)

    def parse(self, parent=None):
        node = Node(parent=parent)
        # Flag that indicates we will be exiting a scoped directive after this
        # node completes building.
        for token in self._stream:
            if token[0] is Token.Error:
                raise ValueError("Config has errors, bailing.")
            node.pretokens.append(token)

            # Nodes don't have types until their first non-whitespace token is
            # matched, this aggregates all the whitespace tokens to the front
            # of the node.
            if not node.type_token:
                continue

            # The node has a type, the lexer will return either a Token.Text
            # with an empty OR string comprised only of newlines before the next node info is
            # available.
            if token[0] is Token.Text and (token[1] == '' or re.search(r'^\n+\s*$', token[1])):
                return self._nodefactory.build(node)

            # When handling Tag tokens, e.g. nested components, we need to
            # know if we're at the start OR end of the Tag. Check for '</'
            # first and flag that this node will be the closing tag or not,
            # if so and > is encountered then return this node since it is
            # complete, this closes the scoped directive.
            if token[0] is Token.Name.Tag and token[1][0] == '<' and token[1][1] == '/':
                node.closeTag = True
            if token[0] is Token.Name.Tag and token[1][0] == '>':
                # If we're closing a tag it's time to return this node.
                if node.closeTag:
                    return self._nodefactory.build(node)

                # Otherwise, we're starting a Tag instead, begin building out
                # the children nodes for this node.
                child = self.parse(parent=node)
                while child and child.closeTag is False:
                    node.children.append(child)
                    child = self.parse(parent=node)

                # If the child was a </tag> node it, migrate it's tokens into
                # posttokens for this node.
                if child and child.closeTag:
                    for pt in child.tokens:
                        node.posttokens.append(pt)
                return self._nodefactory.build(node)
        if len(node.tokens) > 0:
            # At the end of files we may sometimes have some white-space stragglers
            # this if block captures those into a new node.
            return node
        return None


class DefaultFactory(NodeFactory):
    def __init__(self):
        super().__init__()
        pass

    def build(self, node):
        if node.type_token[0] is Token.Name.Tag and node.type_token[1].lower() == '<virtualhost':
            return VirtualHost(node=node)
        if node.type_token[0] is Token.Name.Builtin and node.type_token[1].lower() == 'servername':
            return ServerName(node=node)
        if node.type_token[0] is Token.Name.Builtin and node.type_token[1].lower() == 'serveralias':
            return ServerAlias(node=node)
        if node.type_token[0] is Token.Name.Builtin and node.type_token[1].lower() == 'include':
            return Include(node=node)
        if node.type_token[0] is Token.Name.Builtin and node.type_token[1].lower() == 'includeoptional':
            return IncludeOptional(node=node)
        return node


class ConfigFile(Node):
    def __init__(self, node=None, file=None):
        Node.__init__(self, node=node)
        self._file = file
        if file:
            with open(file, "r") as f:
                data = f.read()
            self._parser = Parser(data, parent=self)
            self._children = self._parser.nodes

    def write(self):
        with open(self._file, "w") as self.__fh:
            self.__fh.write(str(self))


class VirtualHost(Node):
    @property
    def server_name(self):
        for node in self.children:
            if isinstance(node, ServerName):
                return node

    @property
    def server_alias(self):
        for node in self.children:
            if isinstance(node, ServerAlias):
                return node


class ServerName(Node):
    @property
    def server_name(self):
        regex = '((?P<scheme>[a-zA-Z]+)(://))?(?P<domain>[a-zA-Z_0-9.]+)(:(?P<port>[0-9]+))?\\s*$'
        match = re.search(regex, str(self))
        if match:
            return match.group(0).strip()
        return None


class ServerAlias(Node):
    @property
    def server_alias(self):
        regex = '(?P<domain>[a-zA-Z_0-9.]+)\\s*$'
        match = re.search(regex, str(self))
        if match:
            return match.group(0).strip()
        return None


class Include(Node):
    def __init__(self, node=None):
        Node.__init__(self, node=node)
        if len(glob.glob(self.path)) == 0:
            raise ValueError("Include directive failed to include '{}'".format(self.path))
        for path in glob.glob(self.path):
            cf = ConfigFile(file=path)
            cf._parent = self
            self._children.append(cf)

    @property
    def path(self):
        if not self.type_token:
            return None
        index = self.pretokens.index(self.type_token)
        s = ''
        for token in self.pretokens[index+1:]:
            s += "{}".format(token[1])
        return s.strip()

    @property
    def tokens(self):
        """
        :return: List of all the tokens for this node concatenated together, excluding children.
        """
        tokenList = []
        for token in self._pretokens:
            tokenList.append(token)
        for token in self._posttokens:
            tokenList.append(token)
        return tokenList


class IncludeOptional(Include):
    def __init__(self, node=None):
        try:
            Include.__init__(self, node=node)
        except ValueError:
            # Optional means we ignore when no files match the path and the ValueError exception is raised
            pass
