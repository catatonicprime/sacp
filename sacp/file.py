import re
from .node import *
from .parser import *


class ConfigFile:
    def __init__(self, file=None, options=None):
        self._file = file
        self._options = options
        if file:
            with open(file, "r") as f:
                data = f.read()
        self._parser = Parser(data)

    def __str__(self):
        s = ''
        for node in self._parser.nodes:
            s += "{}".format(node)
        return s
