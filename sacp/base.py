import pygments
from pygments.lexers.configs import ApacheConfLexer
from pygments.token import Token
from .node import *


class Parser:
    def __init__(self, data, nodefactory=None):
        # Use specified node generator to glenerate nodes or use the default.
        self._nodefactory = nodefactory
        if not self._nodefactory:
            self._nodefactory = DefaultFactory()

        self.nodes = []
        self._stream = pygments.lex(data, ApacheConfLexer())
        node = self.parse()
        while node:
            self.nodes.append(node)
            node = self.parse()

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

            # We have enough information to know what type of node this is
            # and we can combine this with the generator to build a more
            # specific type of Node.
            node = self._nodefactory.build(node)

            # The node has a type, the lexer will return either a Token.Text
            # with an empty OR newline string before the next node info is
            # available.
            if token[0] is Token.Text and token[1] == '':
                return node
            if token[0] is Token.Text and '\n' in token[1]:
                return node

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
                    return node

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
                return node
        return None


class ConfigFile(Node):
    def __init__(self, node=None, file=None):
        Node.__init__(self, node=node)
        self._file = file
        if file:
            with open(file, "r") as f:
                data = f.read()
        self._parser = Parser(data)
        self._children = self._parser.nodes


class DefaultFactory(NodeFactory):
    def __init__(self):
        super().__init__()
        pass

    def build(self, node):
        if node.type_token[0] is Token.Name.Tag and node.pretokens[-1][1].lower() == '<virtualhost':
            return VirtualHost(node=node)
        if node.type_token[0] is Token.Name.Builtin and node.pretokens[-1][1].lower() == 'servername':
            return ServerName(node=node)
        if node.type_token[0] is Token.Name.Builtin and node.pretokens[-1][1].lower() == 'include':
            return Include(node=node)
        return node


class DefaultVisitor(NodeVisitor):
    def __init__(self, nodes=None):
        NodeVisitor.__init__(self, nodes=nodes)

    def visit(self, visitor=None):
        if not visitor:
            return
        for node in self._nodes:
            visitor(node)
            if node.children:
                DefaultVisitor(node.children).visit(visitor)


class ServerName(Node):
    @property
    def server_name(self):
        regex = '((?P<scheme>[a-zA-Z]+)(://))?(?P<domain>[a-zA-Z_0-9.]+)(:(?P<port>[0-9]+))?\\s*$'
        if re.search(regex, str(self)):
            return re.search(regex, str(self))[0].strip()
        return None


class VirtualHost(Node):
    @property
    def server_name(self):
        for node in self.children:
            if isinstance(node, ServerName):
                return node


class Include(Node):
    def __init__(self, node=None):
        Node.__init__(self, node=node)

    @property
    def path(self):
        pass
