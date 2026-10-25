#!/usr/bin/env python3
"""Zulu Clock local server: serves this folder and makes every outside call the clock needs.

The page never calls an outside site itself. It asks this server at /source/<name>?<query>, and
the server makes the real call to that source's fixed address (browsers can't read Google News,
WHO or NWS directly anyway). Each call's outcome is kept, so /status can say, per source, how its
latest calls went. The clock prints only what /status says.

It also hands the clock cmd fs's missions at /missions, read through cmd fs's own
mmGetMissions endpoint, never from the sheet. MISSIONS_CALL names a router that takes
POST <MISSIONS_CALL>/call/<endpoint>: by default cmd fs's router on its home port 8767
(cmd-fs tools/router.js); its read-only preview, tools/preview.js, speaks it too.
When nothing listens there, /status says cmd fs is offline.

Usage: python3 server.py PORT DIRECTORY
"""
import json
import os
import re
import socket
import sys
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

# Every outside source the clock reads: name -> (label, what it feeds on the clock, address).
# Only these can be called; the page adds its own query string to the address.
SOURCES = {
    'open-meteo': ('Open-Meteo', 'weather, sunrise and sunset', 'https://api.open-meteo.com/v1/forecast'),
    'metar':      ('Aviation Weather', 'weather signals', 'https://aviationweather.gov/api/data/metar'),
    'news-world': ('Google News World', 'headlines', 'https://news.google.com/rss/headlines/section/topic/WORLD'),
    'news-us':    ('Google News US', 'headlines', 'https://news.google.com/rss/headlines/section/topic/NATION'),
    'news-ca':    ('Google News CA', 'headlines', 'https://news.google.com/rss/search'),
    'usgs':       ('USGS', 'earthquakes', 'https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson'),
    'nws':        ('NWS', 'CA weather alerts', 'https://api.weather.gov/alerts/active'),
    'nhc':        ('NHC', 'tropical storms', 'https://www.nhc.noaa.gov/CurrentStorms.json'),
    'eonet':      ('NASA EONET', 'storms, floods, volcanoes', 'https://eonet.gsfc.nasa.gov/api/v3/events'),
    'nifc':       ('NIFC', 'CA wildfires', 'https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/'
                                           'WFIGS_Incident_Locations_Current/FeatureServer/0/query'),
    'who':        ('WHO', 'health watch', 'https://www.who.int/rss-feeds/news-english.xml'),
    'swpc':       ('NOAA SWPC', 'geomagnetic storms', 'https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json'),
    'presser':    ('Presser', 'press', 'http://127.0.0.1:8771/api/summary'),
}
MISSIONS_CALL = (os.environ.get('MISSIONS_CALL') or 'http://127.0.0.1:8767').rstrip('/')
STATUS_ORDER = list(SOURCES) + ['mission-cmd']
CACHE_SECONDS = 120   # several open clocks share one call
TIMEOUT = 10
FORGET_SECONDS = 24 * 3600   # a call not made again in a day no longer counts
OFFLINE = 'Connection refused'   # plain_error's words when nothing listens at the address
_cache = {}           # url -> (fetched_at, content_type, body)
_calls = {}           # source -> {url: (at, ok, error)}, the latest outcome of each distinct call
_lock = threading.Lock()


def now_iso(t=None):
    return datetime.fromtimestamp(t or time.time(), timezone.utc).isoformat(timespec='seconds')


def plain_error(e):
    if isinstance(e, urllib.error.HTTPError):
        return f'HTTP {e.code}'
    reason = getattr(e, 'reason', e)
    if isinstance(reason, (socket.timeout, TimeoutError)) or isinstance(e, (socket.timeout, TimeoutError)):
        return f'no answer in {TIMEOUT} s'
    return re.sub(r'^\[Errno -?\d+\]\s*', '', str(reason)) or type(e).__name__


def record(name, url, ok, error=''):
    with _lock:
        _calls.setdefault(name, {})[url] = (time.time(), ok, error)


def call(name, url, data=None):
    """Makes the call, records how it went, and returns (content_type, body) or raises."""
    if data is None:
        with _lock:
            hit = _cache.get(url)
            if hit and time.time() - hit[0] < CACHE_SECONDS:
                return hit[1], hit[2]
    req = urllib.request.Request(url, data=data, method='POST' if data is not None else 'GET',
                                 headers={'User-Agent': 'Mozilla/5.0 (Zulu Clock)'})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            ctype, body = r.headers.get('Content-Type', 'application/octet-stream'), r.read()
    except Exception as e:
        record(name, url, False, plain_error(e))
        raise
    record(name, url, True)
    if data is None:
        with _lock:
            _cache[url] = (time.time(), ctype, body)
    return ctype, body


def status():
    """Per source: how its latest calls went. 'answering' means each distinct call's latest try
    got a reply within the time limit; it says nothing about what the reply contained."""
    out = []
    cutoff = time.time() - FORGET_SECONDS
    with _lock:
        calls = {n: {u: c for u, c in byurl.items() if c[0] >= cutoff} for n, byurl in _calls.items()}
    for name in STATUS_ORDER:
        label, feeds = ('cmd fs', 'missions') if name == 'mission-cmd' else SOURCES[name][:2]
        latest = list(calls.get(name, {}).values())
        ok = [c for c in latest if c[1]]
        bad = sorted((c for c in latest if not c[1]), key=lambda c: c[0])
        if not latest:
            state, error = 'not called', ''
        else:
            state = 'answering' if not bad else 'failing' if not ok else 'partial'
            error = bad[-1][2] if bad else ''
            if state == 'failing' and error == OFFLINE:
                state = 'offline'   # nothing listens at its address
        out.append({
            'name': name, 'label': label, 'feeds': feeds, 'state': state, 'error': error,
            'calls': len(latest), 'answered': len(ok),
            'last_call_at': now_iso(max(c[0] for c in latest)) if latest else None,
        })
    return {'checked_at': now_iso(), 'sources': out}


class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        path, _, query = self.path.partition('?')
        if path == '/status':
            return self.send_body('application/json', json.dumps(status()).encode())
        if path == '/missions':
            return self.send_missions()
        if not path.startswith('/source/'):
            return super().do_GET()
        name = path[len('/source/'):]
        if name not in SOURCES:
            return self.send_error(404, 'unknown source')
        url = SOURCES[name][2] + ('?' + query if query else '')
        try:
            ctype, body = call(name, url)
        except Exception as e:
            return self.send_error(502, f'{SOURCES[name][0]} did not answer: {plain_error(e)}')
        self.send_body(ctype, body)

    def send_missions(self):
        url = MISSIONS_CALL + '/call/mmGetMissions'
        try:
            _, body = call('mission-cmd', url, data=b'null')
        except Exception as e:
            return self.send_error(502, f'cmd fs did not answer: {plain_error(e)}')
        try:
            answer = json.loads(body)
        except ValueError:
            answer = {'refused': 'bad_answer', 'reason': 'not JSON'}
        # The router sends a refusal (signed_out, google, ...) with HTTP 200; it is not an answer.
        if isinstance(answer, dict) and answer.get('refused'):
            record('mission-cmd', url, False, f"refused {answer['refused']}: {answer.get('reason', '')}")
            return self.send_error(502, f"cmd fs refused: {answer['refused']}")
        self.send_body('application/json', body)

    def send_body(self, ctype, body):
        self.send_response(200)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


if __name__ == '__main__':
    port, directory = int(sys.argv[1]), sys.argv[2]
    ThreadingHTTPServer(('127.0.0.1', port), partial(Handler, directory=directory)).serve_forever()
