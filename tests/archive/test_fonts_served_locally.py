"""The page loads its two fonts from this server, not from Google, so /status covers every outside call."""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from test_server_leaks import ROOT, clock, get  # noqa: E402,F401

FONTS = ('/fonts/share-tech-mono-latin.woff2', '/fonts/vt323-latin.woff2')


def test_the_page_names_no_outside_host():
    page = open(os.path.join(ROOT, 'zulu-clock.html')).read()
    assert not re.search(r'(?:href|src)=["\']https?://|url\(\s*["\']?https?://', page)


def test_the_page_declares_both_fonts_from_this_server():
    page = open(os.path.join(ROOT, 'zulu-clock.html')).read()
    for path in FONTS:
        assert f'url({path})' in page or f"url('{path}')" in page, path


def test_the_two_font_files_are_served(clock):
    for path in FONTS:
        status, body = get(clock, path)
        assert status == 200 and body[:4] == b'wOF2', path


def test_other_files_in_fonts_are_not_served(clock):
    assert get(clock, '/fonts/')[0] == 404
    assert get(clock, '/fonts/LICENSE.txt')[0] == 404
