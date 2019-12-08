# Simple Apache Config Parser
Welcome to the Simple Apache Config Parser! This package is intended to ease the parsing/analysis of apache config files. This parser uses the Apache Config Lexer provided by the [pygments](http://pygments.org/) project.

This project is still very much in its infancy, but my focus is on providing easy to use/understand object interfaces to analyze and modify apache config files while attempting to minimize the deltas between the original configs and the modified content. If this software is not quite meeting your needs, drop in an Issue and I'll do my best to address/help, but even if that's failing checkout this other neat parser [apacheconfig](https://github.com/etingof/apacheconfig).

# Example usage
Here are some example usages. Note that these examples assume your current working directory properly set to match Include patterns. In the examples below this is for a CentOS installation where the root apache directory tends to be /etc/httpd/.

## Parsing
Parsing a config file is easy!
```python
from sacp import *
cf = ConfigFile(file="conf/httpd.conf")
```
This will automatically parse the httpd.conf from the current directory. Any dependent configs (e.g. those that are listed in an Include or IncludeOptional directive) will also be loaded.

## Walking the nodes
Visiting all the nodes is also easy!
```python
from sacp import *
  
def visit(node):
    print("{}{}".format(node.depth * " ", type(node)))

cf = ConfigFile(file="conf/httpd.conf")
NodeVisitor([cf]).visit(visitor=visit)
```
This visits all of the nodes in the config file, including it's children, and prints each node type with it's relative depth represented as well.

# Contribute
Want to contribute? Awesome! Fork, code, and create a PR.
