"""The page's own script (zulu-clock.js), cut into named consts and functions that node can run."""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def source():
    return open(os.path.join(ROOT, 'zulu-clock.js')).read()


def pick(*names):
    """Node-ready source for each name (a function or a const). A name ending in ? is left out when the page does
    not have it."""
    js = source()
    found = []
    for name in names:
        bare = name.rstrip('?')
        # A function runs from its declaration, at any indent, to the first `}` alone at that same indent.
        m = (re.search(r'^([ \t]*)(?:async )?function %s\(.*?\n\1\}[ \t]*\n' % bare, js, re.S | re.M)
             or re.search(r'^[ \t]*const %s .*\n' % bare, js, re.M))
        assert m or name.endswith('?'), f'{bare} is not in zulu-clock.js'
        found.append(m.group(0) if m else '')
    return ''.join(found)
