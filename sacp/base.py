from pygments.token import Token
from .node import *


class DefaultFactory(NodeFactory):
    def __init__(self):
        pass

    def build(self, node):
        if node.typeToken[0] is Token.Name.Tag and node.pretokens[-1][1].lower() == '<virtualhost':
            return VirtualHost(node.pretokens, node.children, node.posttokens, parent=node._parent)
        if node.typeToken[0] is Token.Name.Builtin and node.pretokens[-1][1].lower() == 'servername':
            return ServerName(node.pretokens, node.children, node.posttokens, parent=node._parent)
        return node


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

class Include(Node):
    @property
    def path(self):
        pass
