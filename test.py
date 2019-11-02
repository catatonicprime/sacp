import binascii
import re
import pygments
from pygments.lexers.configs import ApacheConfLexer
from pygments.token import Token


'''
MultiLine
stream: tokenized stream
Consumes tokens from stream until a Token.Text matching '\n' without a preceding '\\' is encountered OR until the stream
is exhausted.
'''
class MultiLine:
    def __init__(self, stream):
        self._tokens = []
        for token in stream:
            self._tokens.append(token)
            if not self.type:
                # Occurs when the only tokens so far have been whitespace. Append and move on.
                continue
            if token[0] is Token.Text and token[1] == '':
                break
            if token[0] is Token.Text and token[1] == '\n':
                break

    @property
    def tokens(self):
        return self._tokens

    @property
    def type(self):
        for token in self._tokens:
            if token[0] is Token.Text and re.search(r'^\s+$', token[1]):
                continue
            return token[0]

    def __str__(self):
        s = ''
        for token in self._tokens:
            #s += "({}:{})".format(token[0], binascii.hexlify(bytearray(token[1], encoding='utf-8')))
            s += "({}:{})".format(token[0], token[1])
        return s


class Directive(MultiLine):
    def __init__(self, multiline):
        if not isinstance(multiline, MultiLine):
            raise ValueError("multiline must by of type 'MultiLine'")
        self._tokens = multiline._tokens
        if self.type is not Token.Name.Builtin:
            raise ValueError("First non-whitspace token is not Token.Name.Builtin")

    @property
    def name(self):
        for token in self._tokens:
            if token[0] is Token.Text and re.search(r'^\s+$', token[1]):
                continue
            return token[1]

    def __str__(self):
        s = ''
        for token in self._tokens:
            # s += "({}:{})".format(token[0], binascii.hexlify(bytearray(token[1], encoding='utf-8')))
            s += "{}".format(token[1])
        return s


class ConfigFile:
    def __init__(self, file=None):
        self._lines = []
        self._file = file
        if file:
            self.parseFile(file)

    def parseFile(self, file):
        with open(file, "r") as f:
            data = f.read()
        stream = pygments.lex(data, ApacheConfLexer())
        while True:
            line = MultiLine(stream)
            if len(line.tokens) == 0:
                break
            if line.type == Token.Name.Builtin:
                line = Directive(line)
            self._lines.append(line)

    def __str__(self):
        s = ''
        for line in self._lines:
            s += "---{}---\n{}\n".format(line.type, line)
        return s

# Get a stream of tokens!
print(ConfigFile(file="httpd.conf"))

