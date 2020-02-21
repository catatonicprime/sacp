from .base import *


class LineEnumerator(NodeVisitor):
    def __init__(self, nodes):
        NodeVisitor.__init__(self, nodes=nodes)
        self._lineno = 1
        self.lines = []
        self.visit(visitor=self.visitor)

    def visit(self, visitor):
        # We need to do depth-first node visit except for into Include or IncludeOptional.
        for node in self._nodes:
            visitor(node)
            if isinstance(node, Include):
                continue
            if node.children:
                nv = LineEnumerator(node.children)
                nv.visit(visitor)

    def visitor(self, node):
        if isinstance(node, ConfigFile):
            self._lineno = 1
        if node.type_token is None:
            return
        type_index = node._pretokens.index(node.type_token)
        for token in node._pretokens[:type_index]:
            self._lineno += token[1].count('\n')    
        self.lines.append((node, self._lineno))
        for token in node._pretokens[type_index:]:
            self._lineno += token[1].count('\n')
