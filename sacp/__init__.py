import re
import pygments
from pygments.lexers.configs import ApacheConfLexer
from pygments.token import Token


class Node:
    """
    Node structure:

            Node:
        /     |     \
    pre - children - post

    When processing tokens, e.g. when rendering, we process pre tokens first,
    then the children nodes, then the post tokens.

    Example:
    <VirtualHost *:80>
    ServerName server
    </VirtualHost>

    [<VirtualHost][ ][*:80][>][\n] -> pretokens
    [ServerName][ server][\n] -> children / pretokens
    [</VirtualHost][>][\n] -> posttokens
    """
    def __init__(self, pretokens, children, posttokens, closeTag=False, parent=None):
        self._parent = parent
        self._pretokens = pretokens
        self._children = children
        self._posttokens = posttokens
        self.closeTag = closeTag

    @property
    def tokens(self):
        """
        :return: List of all the tokens for this node & it's children
                 concatenated together.
        """
        tokenList = []
        for token in self._pretokens:
            tokenList.append(token)
        for child in self._children:
            for token in child.tokens:
                tokenList.append(token)
        for token in self._posttokens:
            tokenList.append(token)
        return tokenList

    @property
    def pretokens(self):
        return self._pretokens

    @property
    def children(self):
        return self._children

    @property
    def posttokens(self):
        return self._posttokens

    @property
    def typeToken(self):
        # Same as type but includes the whole token.
        for token in self._pretokens:
            if token[0] is Token.Text and re.search(r'^\s+$', token[1]):
                continue
            return token
        return None

    def __str__(self):
        s = ''
        for token in self.tokens:
            s += "{}".format(token[1])
        return s


class NodeFactory:
    def __init__(self):
        raise NotImplementedError

    def build(self, node):
        raise NotImplementedError


class DefaultFactory(NodeFactory):
    def __init__(self):
        pass

    def build(self, node):
        if node.typeToken is Token.Name.Tag and node.pretokens[-1][1].lower() == '<virtualhost':
            return VirtualHost(node.pretokens, node.children, node.posttokens, parent=node._parent)
        if node.typeToken is Token.Name.Builtin and node.pretokens[-1][1].lower() == 'servername':
            return ServerName(node.pretokens, node.children, node.posttokens, parent=node._parent)
        return node


class ServerName(Node):
    @property
    def ServerName(self):
        regex = '((?P<scheme>[a-zA-Z]+)(://))?(?P<domain>[a-zA-Z_0-9.]+)(:(?P<port>[0-9]+))?\\s*$'
        if re.search(regex, str(self)):
            return re.search(regex, str(self))[0].strip()
        return None


class VirtualHost(Node):
    @property
    def ServerName(self):
        for node in self.children:
            if isinstance(node, ServerName):
                return node


class Parser:
    def __init__(self, data, nodefactory=None):
        # Use specified node generator to glenerate nodes or use the default.
        self._nodefactory = nodefactory
        if not self._nodefactory:
            self._nodefactory = DefaultFactory()

        self.nodes = []
        self._stream = pygments.lex(data, ApacheConfLexer())
        node = self.ParseNode()
        while node:
            self.nodes.append(node)
            node = self.ParseNode()

    def ParseNode(self, parent=None):
        node = Node([], [], [], parent=parent)
        # Flag that indicates we will be exiting a scoped directive after this
        # node completes building.
        closeTag = False
        for token in self._stream:
            if token[0] is Token.Error:
                raise ValueError("Config has errors, bailing.")
            node.pretokens.append(token)

            # Nodes don't have types until their first non-whitespace token is
            # matched, this aggregates all the whitespace tokens to the front
            # of the node.
            if not node.typeToken:
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
                child = self.ParseNode(parent=node)
                while child and child.closeTag is False:
                    node.children.append(child)
                    child = self.ParseNode(parent=node)

                # If the child was a </tag> node it, migrate it's tokens into
                # posttokens for this node.
                if child and child.closeTag:
                    for pt in child.tokens:
                        node.posttokens.append(pt)
                return node
        return None


class ConfigFile:
    def __init__(self, file=None, recurseIncludes=True):
        self._file = file
        if file:
            with open(file, "r") as f:
                data = f.read()
        self._parser = Parser(data)

    def __str__(self):
        s = ''
        for node in self._parser.nodes:
            s += "{}".format(node)
        return s


class NodeVisitor():
    def visitNodes(nodes):
        raise NotImplementedError


class DefaultVistor(NodeVisitor):
    def __init__(self, depth=0, indent="\t"):
        super().__init__()
        self.__depth = 0
        self.__indent = indent

    def visitNodes(self, nodes):
        for node in nodes:
            if isinstance(node, ServerName):
                print ("ServerName found: {}".format(node.ServerName))

            print ("Node type: {}{}".format(self.__indent * self.__depth, type(node)))
            if node.children:
                self.__depth += 1
                self.visitNodes(node.children)
                self.__depth -= 1
