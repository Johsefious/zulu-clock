#!/usr/bin/env python3
"""Zulu Clock local server: serves this folder and makes every outside call the clock needs.

The page never calls an outside site itself. It asks this server at /source/<name>?<query>, and
the server makes the real call to that source's fixed address (browsers can't read Google News,
WHO or NWS directly anyway). Each call's outcome is kept, so /status can say, per source, how its
latest calls went. The clock prints only what /status says.

It also hands the clock cmd fs's missions at /missions, read through cmd fs's own
mmGetMissions endpoint, never from the sheet. MISSIONS_CALL names a router that takes
POST <MISSIONS_CALL>/call/<endpoint>: by default cmd fs's router on its home port (cmd-fs
tools/router.js); its read-only preview, tools/preview.js, speaks it too.
When nothing listens there, /status says cmd fs is offline.

No other app's port is typed here. Presser's and cmd fs's home ports come from `port home <repo>`
(the ports repo's list, ports.json). If that lookup fails the source is `failing` in /status, with the reason.

A clock page says hello at /__clock/hello every couple of seconds. The answer carries this run's boot id, so a page
that sees the id change knows the server restarted and reloads itself; it also carries the launch mode, if one was given.
/__clock/seen tells the launcher whether any page has said hello since this start, so it opens a tab only when none is there.

Usage: python3 server.py PORT DIRECTORY [green|pink|blue]
"""
import json
import os
import secrets
import re
import shutil
import socket
import subprocess
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
    'presser':    ('Presser', 'press', None),   # address: Presser's home port, found by home_port
}
MISSIONS_CALL = (os.environ.get('MISSIONS_CALL') or '').rstrip('/')   # empty: cmd fs's home port from the list
REPOS = {'presser': 'presser', 'mission-cmd': 'cmd-fs'}   # whose home port each source lives on
PORT_FALLBACK = '/opt/homebrew/bin/port'   # a server the Dock starts may have a bare PATH
LOOKUP = 'port home'   # the key under which a failed lookup is recorded
STATUS_ORDER = list(SOURCES) + ['mission-cmd']
CACHE_SECONDS = 120   # several open clocks share one call
TIMEOUT = 10
FORGET_SECONDS = 24 * 3600   # a call not made again in a day no longer counts
OFFLINE = 'Connection refused'   # plain_error's words when nothing listens at the address
_cache = {}           # url -> (fetched_at, content_type, body)
_calls = {}           # source -> {url: (at, ok, error)}, the latest outcome of each distinct call
_lock = threading.Lock()
BOOT = secrets.token_hex(8)   # names this run of the server; a page that sees it change reloads
MODES = ('green', 'pink', 'blue')
launch_mode = None            # set at start from the optional third argument
page_seen = False             # has a clock page said hello since this start

# Only the page and its script are served from the folder; nothing else in it (.git, the test log, docs) is reachable.
PAGE = '/zulu-clock.html'
SCRIPT = '/zulu-clock.js'
SERVED_FILES = {'/': PAGE, PAGE: PAGE, SCRIPT: SCRIPT}
# A request must name this server by one of these, or it comes from a web page that is not the clock
# (DNS rebinding), which must not reach cmd fs or Presser through us.
OWN_HOSTS = {'127.0.0.1', 'localhost'}


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
    now = time.time()
    with _lock:
        _calls.setdefault(name, {})[url] = (now, ok, error)
        for n in list(_calls):   # forget calls older than a day, and sources left with none
            _calls[n] = {u: c for u, c in _calls[n].items() if c[0] >= now - FORGET_SECONDS}
            if not _calls[n]:
                del _calls[n]


def home_port(repo):
    """(port, '') from `port home <repo>`, or (None, plain reason)."""
    cmd = shutil.which('port') or (PORT_FALLBACK if os.access(PORT_FALLBACK, os.X_OK) else None)
    if not cmd:
        return None, 'port command not found'
    try:
        r = subprocess.run([cmd, 'home', repo], capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        return None, 'port command did not run'
    out = r.stdout.strip()
    if r.returncode == 1 and not out:
        return None, f'no home port for {repo}'
    if r.returncode or not out.isdigit():
        return None, 'port command failed'
    return int(out), ''


def address(name):
    """(base address, '') of a source that lives on another app's home port, or (None, reason). The outcome
    is recorded: a failed lookup shows as the source failing; a good one clears an earlier failure."""
    port, reason = home_port(REPOS[name])
    with _lock:
        if port:
            _calls.get(name, {}).pop(LOOKUP, None)
            if name in _calls and not _calls[name]:
                del _calls[name]
    if not port:
        record(name, LOOKUP, False, reason)
        return None, reason
    return f'http://127.0.0.1:{port}', ''


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
        now = time.time()
        with _lock:
            _cache[url] = (now, ctype, body)
            for u in [u for u, c in _cache.items() if now - c[0] >= CACHE_SECONDS]:
                del _cache[u]   # answers past their lifetime are never served again
    return ctype, body


def first_name(n):
    return str(n).split(' ')[0]


def trim_mission(m):
    """The fields a mission card draws, nothing else: members are cut to first names, a received plan to its review time."""
    plan = m.get('planReceived')
    return {
        'label': m.get('label', ''), 'days_out': m.get('days_out'), 'types': m.get('types') or [],
        'facilities': m.get('facilities') or [], 'members': [first_name(n) for n in m.get('members') or []],
        'confirmed': m.get('confirmed'), 'briefingSent': m.get('briefingSent'), 'approved': m.get('approved'),
        'cancelled': m.get('cancelled'), 'gate_warning': m.get('gate_warning'), 'planDue': m.get('planDue'),
        'planReceived': {'review_by': plan.get('review_by')} if isinstance(plan, dict) else None,
    }


def pick(d, keys):
    return {k: d.get(k) for k in keys}


def trim_story(st):
    out = pick(st, ('id', 'short_name', 'archived', 'countdown_to', 'doc', 'progress', 'overdue', 'today',
                    'upcoming', 'old_builder'))
    nxt = st.get('next')
    out['next'] = pick(nxt, ('text', 'state')) if isinstance(nxt, dict) else None
    out['sends_open'] = [pick(s, ('label', 'due')) for s in st.get('sends_open') or []]
    return out


def trim_summary(d):
    """The Presser summary down to the fields a press card draws."""
    return {'stories': [trim_story(st) for st in d['stories']],
            'totals': pick(d.get('totals') or {}, ('overdue', 'today', 'messages'))}


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


CLOSE_REASON = 'Nothing needs saving; a restart loses only the feed cache and call log, which refill on the next calls.'


def restart_status():
    """What docks asks before a restart: built fresh, no outside calls."""
    return {'clear': True, 'reason': 'A restart loses only the feed cache and call log, which refill on the next calls.',
            'as_of': now_iso()}


class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        path, _, query = self.path.partition('?')
        if self.headers.get('Host', '').partition(':')[0] not in OWN_HOSTS:
            return self.send_error(403, 'not the clock')
        if path == '/__docks/restart-status':
            return self.send_body('application/json', json.dumps(restart_status()).encode())
        if path == '/status':
            return self.send_body('application/json', json.dumps(status()).encode())
        if path == '/__clock/hello':
            global page_seen
            page_seen = True
            return self.send_body('application/json', json.dumps({'boot': BOOT, 'mode': launch_mode}).encode())
        if path == '/__clock/seen':
            return self.send_body('application/json', json.dumps({'seen': page_seen, 'as_of': now_iso()}).encode())
        if path == '/missions':
            return self.send_missions()
        if path == '/go/presser':
            base, reason = address('presser')
            if not base:
                return self.send_error(502, f'Presser address unknown: {reason}')
            self.send_response(302)
            self.send_header('Location', base + '/')
            self.send_header('Content-Length', '0')
            return self.end_headers()
        if not path.startswith('/source/'):
            if path not in SERVED_FILES:
                return self.send_error(404)
            self.path = SERVED_FILES[path]
            self.revalidate = True   # a reload must not run a cached old script against the new page
            return super().do_GET()
        name = path[len('/source/'):]
        if name not in SOURCES:
            return self.send_error(404, 'unknown source')
        base = SOURCES[name][2]
        if base is None:
            base, reason = address(name)
            if not base:
                return self.send_error(502, f'{SOURCES[name][0]} address unknown: {reason}')
            base += '/api/summary'
        url = base + ('?' + query if query else '')
        try:
            ctype, body = call(name, url)
        except Exception as e:
            return self.send_error(502, f'{SOURCES[name][0]} did not answer: {plain_error(e)}')
        if name == 'presser':
            try:
                ctype, body = 'application/json', json.dumps(trim_summary(json.loads(body))).encode()
            except (ValueError, KeyError, TypeError, AttributeError):
                return self.send_error(502, 'Presser did not send a summary')
        self.send_body(ctype, body)

    def do_POST(self):
        path = self.path.partition('?')[0]
        if self.headers.get('Host', '').partition(':')[0] not in OWN_HOSTS:
            return self.send_error(403, 'not the clock')
        if path != '/__docks/close':
            return self.send_error(404)
        # A web page can post text/plain without asking first; only docks sends JSON
        if self.headers.get('Content-Type', '').partition(';')[0].strip() != 'application/json':
            return self.send_error(415, 'The close call must be sent as application/json.')
        try:
            length = int(self.headers.get('Content-Length') or 0)
            asked = json.loads(self.rfile.read(min(length, 4096)))
            why = asked['for']
        except (ValueError, KeyError, TypeError):
            why = None
        if why not in ('restart', 'quit'):
            return self.send_error(400, 'The body must be JSON like {"for": "restart"} or {"for": "quit"}.')
        # Nothing here needs saving: the cache and call log only refill. Answer, then stop.
        self.close_connection = True
        self.send_body('application/json', json.dumps({'answer': 'closing', 'reason': CLOSE_REASON,
                                                       'as_of': now_iso()}).encode())
        self.wfile.flush()
        # shutdown() waits for serve_forever, which is on another thread, so it must not run on this one.
        threading.Thread(target=self.server.shutdown).start()

    def send_missions(self):
        base = MISSIONS_CALL
        if not base:
            base, reason = address('mission-cmd')
            if not base:
                return self.send_error(502, f'cmd fs address unknown: {reason}')
        url = base + '/call/mmGetMissions'
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
        try:
            body = json.dumps({'missions': [trim_mission(m) for m in answer['missions']]}).encode()
        except (KeyError, TypeError, AttributeError):
            return self.send_error(502, 'cmd fs did not send missions')
        self.send_body('application/json', body)

    def send_body(self, ctype, body):
        self.send_response(200)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def end_headers(self):
        if getattr(self, 'revalidate', False):
            self.send_header('Cache-Control', 'no-cache')
        super().end_headers()

    def log_message(self, *args):
        pass


if __name__ == '__main__':
    port, directory = int(sys.argv[1]), sys.argv[2]
    launch_mode = sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] in MODES else None
    httpd = ThreadingHTTPServer(('127.0.0.1', port), partial(Handler, directory=directory))
    httpd.serve_forever()   # returns after POST /__docks/close; the process then ends
    httpd.server_close()
