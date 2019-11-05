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
    def __init__(self, pretokens, children, posttokens, closeTag=False, parent=None):
        self._parent = parent
        self._pretokens = pretokens
        self._children = children
        self._posttokens = posttokens
        self.closeTag = closeTag

    @property
    def tokens(self):
        """
        :return: List of all the tokens for this node & it's children concatenated together.
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
        # Flag that indicates we will be exiting a scoped directive after this node completes building.
        closeTag = False
        for token in self._stream:
            if token[0] is Token.Error:
                raise ValueError("Config has errors, bailing.")
            node.pretokens.append(token)
           
            # Nodes don't have types until their first non-whitespace token is matched, this aggregates all the
            # whitespace tokens to the front of the node.
            if not node.type:
                continue

            # The node has a type, the lexer will return either a Token.Text with an empty OR newline string before
            # the next node info is available.
            if token[0] is Token.Text and token[1] == '':
                return node
            if token[0] is Token.Text and '\n' in token[1]:
                return node

            # When handling Tag tokens, e.g. nested components, we need to know if we're at the start OR end of the Tag.
            # Check for </ first and flag that this node will be the closing tag or not, if so and > is encountered
            # then return this node since it is complete, this closes the scoped directive.
            if token[0] is Token.Name.Tag and token[1][0] == '<' and token[1][1] == '/':
                node.closeTag = True
            if token[0] is Token.Name.Tag and token[1][0] == '>':
                # If we're closing a tag it's time to return this node.
                if node.closeTag:
                    return node

                # Otherwise, we're starting a Tag instead, begin building out the children nodes for this node.
                child = self.ParseNode(parent=node)
                while child and child.closeTag == False:
                    node.children.append(child)
                    child = self.ParseNode(parent=node)

                # If the child was a </tag> node it, migrate it's tokens into posttokens for this node.
                if child and child.closeTag:
                    for pt in child.tokens:
                        node.posttokens.append(pt)
                return node
        return None


    def __str__(self):
        s = ''
        for node in self._nodes:
            #s += "---{}---\n{}\n".format(node.type, str(node))
            s += "{}".format(node)
        return s
