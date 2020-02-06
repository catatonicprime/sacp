from .node import *
from pygments.lexer import RegexLexer, default, words, bygroups, include, using
from pygments.token import Text, Comment as pygComment, Operator, Keyword, Name, String, \
    Number, Punctuation, Whitespace, Literal
import pygments
import glob


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
            (r'#(.*\\\n)+.*$|(#.*?)$', pygComment),
            (r'(<[^\s>]+)(?:(\s+)(.*))?(>)',
             bygroups(Name.Tag, Text, String, Name.Tag)),
            (r'[a-z]\w*', Name.Builtin, 'value'),
            (r'\.+', Text),
        ],
        'value': [
            (r'\\\n', Text),
            (r'$', Text, '#pop'),
            (r'\\', Text),
            (r'[^\S\n]+', Text),
            (r'\d+\.\d+\.\d+\.\d+(?:/\d+)?', Number),
            (r'\d+', Number),
            (r'/([*a-z0-9][*\w./-]+)', String.Other),
            (r'(on|off|none|any|all|double|email|dns|min|minimal|'
             r'os|productonly|full|emerg|alert|crit|error|warn|'
             r'notice|info|debug|registry|script|inetd|standalone|'
             r'user|group)\b', Keyword),
            (r'"([^"\\]*(?:\\(.|[\n])[^"\\]*)*)"', String.Double),
            (r'[^\s"\\]+', Text)
        ],
    }


class Parser:
    def __init__(self, data, nodefactory=None, parent=None, acl=None):
        # Use specified node generator to generate nodes or use the default.
        if nodefactory is None:
            nodefactory = DefaultFactory()
        if not isinstance(nodefactory, NodeFactory):
            raise ValueError("nodefactory must be of type NodeFactory")
        self._nodefactory = nodefactory

        # Use specified lexer to generate tokens or use the default.
        if acl is None:
            acl = ApacheConfLexer(ensurenl=False, stripnl=False)

        if not isinstance(acl, ApacheConfLexer):
            raise ValueError("acl must be of type ApacheConfLexer")

        self._stream = pygments.lex(data, acl)

        # Start parsing and tracking nodes
        self.nodes = []
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
        NodeFactory.__init__(self)
        pass

    def build(self, node):
        if node.type_token[0] is Token.Name.Tag:
            node = ScopedDirective(node=node)
        elif node.type_token[0] is Token.Name.Builtin:
            node = Directive(node=node)
        elif node.type_token[0] is Token.Comment:
            node = Comment(node=node)

        if isinstance(node, ScopedDirective):
            if node.name.lower() == 'virtualhost':
                node = VirtualHost(node=node)
            if node.name.lower() == 'directory':
                node = Directory(node=node)
            if node.name.lower() == 'directorymatch':
                node = DirectoryMatch(node=node)
            if node.name.lower() == 'files':
                node = Files(node=node)
            if node.name.lower() == 'filesmatch':
                node = FilesMatch(node=node)
            if node.name.lower() == 'location':
                node = Location(node=node)
            if node.name.lower() == 'locationmatch':
                node = LocationMatch(node=node)
            if node.name.lower() == 'proxy':
                node = Proxy(node=node)
            if node.name.lower() == 'proxymatch':
                node = ProxyMatch(node=node)
        if isinstance(node, Directive):
            if node.name.lower() == 'servername':
                node = ServerName(node=node)
            elif node.name.lower() == 'serveralias':
                node = ServerAlias(node=node)
            elif node.name.lower() == 'include':
                node = Include(node=node)
            elif node.name.lower() == 'includeoptional':
                node = IncludeOptional(node=node)

        # Fix up children's parent.
        for child in node.children:
            child._parent = node

        return node


class Directive(Node):
    @property
    def name(self):
        return self.type_token[1]

    @property
    def arguments(self):
        """
        return: Array of arguments following a directive.
        example: 'ServerName example.com' returns [u'example.com']
        example: 'Deny from all' returns [u'from', u'all']
        """
        args = []
        directiveIndex = self.tokens.index(self.type_token)
        for token in self.tokens[directiveIndex+1:]:
            if token[0] is Token.Text and (not token[1] or token[1].isspace()):
                continue
            args.append(token[1].strip())
        return args


class ScopedDirective(Directive):
    @property
    def name(self):
        return super(ScopedDirective, self).name.split('<')[1]


class Comment(Node):
    pass


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


class VirtualHost(ScopedDirective):
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


class ServerName(Directive):
    @property
    def isValid(self):
        if len(self.arguments) == 0 or len(self.arguments) > 1:
            return False

        regex = '^((?P<scheme>[a-zA-Z]+)(://))?(?P<domain>[a-zA-Z_0-9.]+)(:(?P<port>[0-9]+))?\\s*$'
        match = re.search(regex, self.arguments[0])
        if match:
            return True
        return False


class ServerAlias(Directive):
    @property
    def isValid(self):
        if len(self.arguments) == 0:
            return False

        regex = '^(?P<domain>[a-zA-Z_0-9.]+)\\s*$'
        for name  in self.arguments:
            match = re.search(regex, name)
            if not match:
                return False
        return True


class IncludeError(Exception):
    pass


class Include(Directive):
    def __init__(self, node=None):
        Node.__init__(self, node=node)
        if not self.path:
            raise IncludeError("path cannot be none")
        if len(glob.glob(self.path)) == 0:
            raise ValueError("Include directive failed to include '{}'".format(self.path))
        for path in glob.glob(self.path):
            cf = ConfigFile(file=path)
            cf._parent = self
            self._children.append(cf)

    @property
    def path(self):
        """
        :return: The glob pattern used to load additional configs.
        """
        if len(self.arguments) > 0:
            return self.arguments[0].strip()
        return None

    @property
    def tokens(self):
        """
        :return: List of all the tokens for this node concatenated together, excluding children.
        """
        # Because Includes are directives (not scoped directives) they will never have posttokens.
        tokenList = []
        for token in self._pretokens:
            tokenList.append(token)
        return tokenList


class IncludeOptional(Include):
    def __init__(self, node=None):
        try:
            Include.__init__(self, node=node)
        except ValueError:
            # Optional means we ignore when no files match the path and the ValueError exception is raised
            pass


class Directory(ScopedDirective):
    pass


class DirectoryMatch(ScopedDirective):
    pass


class Files(ScopedDirective):
    pass


class FilesMatch(ScopedDirective):
    pass


class Location(ScopedDirective):
    pass


class LocationMatch(ScopedDirective):
    pass


class Proxy(ScopedDirective):
    pass


class ProxyMatch(ScopedDirective):
    pass
