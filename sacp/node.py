import re
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

    def __init__(self, node=None, close_tag=False, parent=None):
        self._parent = parent
        self._pretokens = []
        self._children = []
        self._posttokens = []
        self.closeTag = close_tag
        if node:
            self._parent = node._parent
            self._pretokens = node._pretokens or []
            self._children = node._children or []
            self._posttokens = node._posttokens or []
            self.closeTag = node.closeTag

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
    def parent(self):
        return self._parent

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
    def type_token(self):
        """
        :return: returns the first non-whitespace token for the node. This is the first indicator of the type for this node.
        """
        for token in self._pretokens:
            if token[0] is Token.Text and token[1].isspace():
                continue
            return token
        return None

    @property
    def depth(self):
        depth = 0
        node = self._parent
        while node:
            depth += 1
            node = node._parent
        return depth

    def append_child(self, node):
        node._parent = self
        self._children.append(node)

    def append_children(self, nodes):
        for node in nodes:
            self.append_child(node)

    def __str__(self):
        s = ''
        for token in self.tokens:
            s += "{}".format(token[1])
        return s


class NodeFactory:
    def __init__(self):
        pass

    def build(self, node):
        """
        Used to build a begin building a new Node, is called as soon as a parser identifies enough information to construct a node.
        """
        raise NotImplementedError


class NodeVisitor:
    def __init__(self, nodes=None):
        self._nodes = nodes
    
    def visit(self, visitor):
        for node in self._nodes:
            visitor(node)

class DFNodeVisitor(NodeVisitor):
    def visit(self, visitor):
        for node in self._nodes:
            visitor(node)
            if node.children:
                nv = DFNodeVisitor(node.children)
                nv.visit(visitor)

class BFNodeVisitor(NodeVisitor):
    def visit(self, visitor):
        for node in self._nodes:
            visitor(node)

        for node in self._nodes:
            if node.children:
                nv = BFNodeVisitor(node.children)
                nv.visit(visitor)
