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

    When processing tokens, e.g. when rendering, we process pre tokens first, then the children nodes, then the post
    tokens.

    Example:
    <VirtualHost *:80>
    ServerName server
    </VirtualHost>

    [<VirtualHost][ ][*:80][>][\n] -> pretokens
    [ServerName][ server][\n] -> children / pretokens
    [</VirtualHost][>][\n] -> posttokens
    """
    def __init__(self, pretokens, posttokens, children, parent=None):
        self._parent = parent
        self._pretokens = pretokens
        self._posttokens = posttokens
        self._children = children

    @property
    def tokens(self):
        """
        :return: List of all the tokens for this node & it's children concatenated together.
        """
        tokenList = []
        for token in self._pretokens:
            tokenList.append(token)
        for child in self._children:
            tokenList.append(child.tokens)
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
    def type(self):
        # This node's type will always be identifiable in the pretokens
        for token in self._pretokens:
            if token[0] is Token.Text and re.search(r'^\s+$', token[1]):
                continue
            return token[0]
        return None

    def __str__(self):
        s = ''
        if len(self.tokens) == 0:
            return s
        for token in self.tokens:
            if len(token) == 0:
                continue
            s += "{}".format(token[1])
        return s

class ConfigFile:
    def __init__(self, file=None):
        self._nodes = []
        self._file = file
        if file:
            with open(file, "r") as f:
                data = f.read()
            self._stream = pygments.lex(data, ApacheConfLexer())
            node = self.ParseNode()
            while node:
                # if len(node.tokens) == 0:
                #     break
                self._nodes.append(node)
                node = self.ParseNode()

    def ParseNode(self, parent=None):
        node = Node([], [], [], parent=parent)
        currentList = node.pretokens
        for token in self._stream:
            currentList.append(token)
            if not node.type:
                # Occurs when the only tokens so far have been whitespace. Append and move on.
                continue
            if token[0] is Token.Text and token[1] == '':
                return node
            if token[0] is Token.Text and token[1] == '\n':
                return node
            if token[0] is Token.Name.Tag and token[1][0] == '>' and currentList == node.pretokens:
                child = self.ParseNode()
                node.children.append(child)
                currentList = node.posttokens
            elif token[0] is Token.Name.Tag and token[1][0] == '>' and currentList == node.posttokens:
                return node
        return None


    def __str__(self):
        s = ''
        for node in self._nodes:
            #s += "---{}---\n{}\n".format(node.type, str(node))
            s += "{}".format(node)
        return s

# Get a stream of tokens!
cf = ConfigFile(file="httpd_short.conf")
print(cf)

