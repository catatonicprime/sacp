from pygments.lexer import RegexLexer, default, words, bygroups, include, using
from pygments.token import Text, Comment, Operator, Keyword, Name, String, \
    Number, Punctuation, Whitespace, Literal
from pygments.lexers.shell import BashLexer
from pygments.lexers.data import JsonLexer
import re
import pygments

class ApacheConfLexer(RegexLexer):
    """
    Lexer for configuration files following the Apache config file
    format.

    .. versionadded:: 0.6
    """

    name = 'ApacheConf'
    aliases = ['apacheconf', 'aconf', 'apache']
    filenames = ['.htaccess', 'apache.conf', 'apache2.conf']
    mimetypes = ['text/x-apacheconf']
    flags = re.MULTILINE | re.IGNORECASE

    tokens = {
        'root': [
            (r'\s+', Text),
            (r'#(.*\\\n)+.*$|(#.*?)$', Comment),
            (r'(<[^\s>]+)(?:(\s+)(.*))?(>)',
             bygroups(Name.Tag, Text, String, Name.Tag)),
            (r'[a-z]\w*', Name.Builtin, 'value'),
            (r'\.+', Text),
        ],
        'value': [
            (r'\\\n', Text),
            (r'$', Text, '#pop'),
            (r'\\', Text),
            (r'[^\S\n]+', Text),
            (r'\d+\.\d+\.\d+\.\d+(?:/\d+)?', Number),
            (r'\d+', Number),
            (r'/([a-z0-9][\w./-]+)', String.Other),
            (r'(on|off|none|any|all|double|email|dns|min|minimal|'
             r'os|productonly|full|emerg|alert|crit|error|warn|'
             r'notice|info|debug|registry|script|inetd|standalone|'
             r'user|group)\b', Keyword),
            (r'"([^"\\]*(?:\\(.|[\n])[^"\\]*)*)"', String.Double),
            (r'[^\s"\\]+', Text)
        ],
    }

acl = ApacheConfLexer(ensurenl=False, stripnl=False)

data = 'Example \nServerName on'
for token in pygments.lex(data, acl):
    print("({}, {})".format(token[0], repr(token[1])))