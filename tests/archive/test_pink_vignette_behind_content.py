"""In pink mode the vignette darkens only the pink background: its layer sits below .shell (the content), while green
and blue keep it over everything."""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HTML = open(os.path.join(ROOT, 'zulu-clock.html')).read()


def z(selector):
    m = re.search(re.escape(selector) + r'\s*\{[^}]*?z-index:\s*(\d+)', HTML)
    assert m, f'no z-index for {selector}'
    return int(m.group(1))


def test_default_vignette_is_over_the_content():
    assert z('body::after') > z('.shell')


def test_pink_vignette_is_behind_the_content():
    assert z('html[data-mode="pink"] body::after') < z('.shell')
