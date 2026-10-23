#!/usr/bin/env python3
"""Zulu Clock local server: serves this folder and fetches the news feeds.

Browsers can't read Google News RSS directly (no CORS headers), and the free
CORS proxies the clock used to rely on have all closed. This server fetches the
three feeds itself, so the page reads them from its own origin at /news/<TAG>.

It also hands the clock Mission cmd's missions at /missions, read through Mission cmd's own
mmGetMissions endpoint, never from the sheet. MISSIONS_CALL names a router that takes
POST <MISSIONS_CALL>/call/<endpoint> (Mission cmd's preview, tools/preview.js, speaks it).
Without it, /missions answers 503 and the clock says Mission cmd is not connected.

Usage: python3 server.py PORT DIRECTORY
"""
import os
import sys
import threading
import time
import urllib.request
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

# Only these feeds can be fetched; anything else under /news/ is refused.
FEEDS = {
    'WORLD': 'https://news.google.com/rss/headlines/section/topic/WORLD?hl=en&gl=US&ceid=US:en',
    'US':    'https://news.google.com/rss/headlines/section/topic/NATION?hl=en&gl=US&ceid=US:en',
    'CA':    'https://news.google.com/rss/search?q=california+news&hl=en&gl=US&ceid=US:en',
}
MISSIONS_CALL = os.environ.get('MISSIONS_CALL', '').rstrip('/')
CACHE_SECONDS = 120   # several open clocks share one fetch
_cache = {}           # tag -> (fetched_at, body)
_lock = threading.Lock()


def fetch_feed(tag):
    with _lock:
        hit = _cache.get(tag)
        if hit and time.time() - hit[0] < CACHE_SECONDS:
            return hit[1]
    req = urllib.request.Request(FEEDS[tag], headers={'User-Agent': 'Mozilla/5.0 (Zulu Clock)'})
    with urllib.request.urlopen(req, timeout=10) as r:
        body = r.read()
    with _lock:
        _cache[tag] = (time.time(), body)
    return body


def fetch_missions():
    req = urllib.request.Request(MISSIONS_CALL + '/call/mmGetMissions', data=b'null', method='POST')
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.read()


class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.split('?')[0] == '/missions':
            return self.send_missions()
        if not self.path.startswith('/news/'):
            return super().do_GET()
        tag = self.path[len('/news/'):].split('?')[0].upper()
        if tag not in FEEDS:
            return self.send_error(404, 'unknown feed')
        try:
            body = fetch_feed(tag)
        except Exception as e:
            return self.send_error(502, f'feed fetch failed: {e}')
        self.send_response(200)
        self.send_header('Content-Type', 'application/xml; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def send_missions(self):
        if not MISSIONS_CALL:
            return self.send_error(503, 'Mission cmd not connected')
        try:
            body = fetch_missions()
        except Exception as e:
            return self.send_error(502, f'Mission cmd did not answer: {e}')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


if __name__ == '__main__':
    port, directory = int(sys.argv[1]), sys.argv[2]
    ThreadingHTTPServer(('127.0.0.1', port), partial(Handler, directory=directory)).serve_forever()
