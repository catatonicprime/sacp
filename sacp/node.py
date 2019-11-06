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


class NodeVisitor():
    def visitNodes(nodes):
        raise NotImplementedError
