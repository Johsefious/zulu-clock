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
        m = (re.search(r'  (?:async )?function %s\(.*?\n  \}\n' % bare, js, re.S)
             or re.search(r'  const %s .*\n' % bare, js))
        assert m or name.endswith('?'), f'{bare} is not in zulu-clock.js'
        found.append(m.group(0) if m else '')
    return ''.join(found)
