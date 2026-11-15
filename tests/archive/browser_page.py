"""Loads the real clock page in the headless shell for the archive tests that look at it in a browser.

`open_page` serves the folder with the real server.py handler and every outside call refused, unless a test answers it.
"""
import json
import os
import sys
import threading
from functools import partial
from http.server import ThreadingHTTPServer

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
import server  # noqa: E402

CHROME = os.path.expanduser('~/Library/Caches/djitel-test-chrome/chrome-headless-shell-mac-arm64/chrome-headless-shell')


@pytest.fixture(scope='module')
def browser():
    """(browser, port): one headless shell and one server for the module."""
    if not os.path.exists(CHROME):
        pytest.skip('headless shell is not installed')
    from playwright.sync_api import sync_playwright
    httpd = ThreadingHTTPServer(('127.0.0.1', 0), partial(server.Handler, directory=ROOT))
    threading.Thread(target=httpd.serve_forever, kwargs={'poll_interval': 0.01}, daemon=True).start()
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=CHROME, args=['--use-mock-keychain', '--password-store=basic'])
        yield b, httpd.server_address[1]
        b.close()
    httpd.shutdown()


def answer(body, content_type='application/json'):
    """A route handler that answers with this body (a dict or list is sent as JSON, a string as it is)."""
    text = body if isinstance(body, str) else json.dumps(body)
    return lambda r: r.fulfill(status=200, content_type=content_type, body=text)


def open_page(browser, width, height, query, routes=()):
    """A new page at this size on the clock, `query` being e.g. 'mode=pink'. Every /source/ call is refused first;
    `routes` is (pattern, handler) pairs registered after, so they win."""
    b, port = browser
    page = b.new_page(viewport={'width': width, 'height': height})
    page.route('**/source/**', lambda r: r.abort())
    for pattern, handler in routes:
        page.route(pattern, handler)
    page.goto(f'http://127.0.0.1:{port}/zulu-clock.html?{query}')
    return page
