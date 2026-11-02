"""Zulu Clock types no other app's port number: it asks `port home <repo>` (the ports repo's list).

- launch.sh takes its own port from `port home zulu-clock` and says so in one line when that fails.
- server.py finds Presser (repo presser) and cmd fs (cmd-fs) the same way; a failed lookup is `failing` in /status
  with a plain reason, never a crash. MISSIONS_CALL still wins for cmd fs.
- The Press link goes through GET /go/presser (302 to Presser's home address); the page holds no Presser port.
- dock.json names its Ports entry, {"ports": "zulu-clock"}, and docks asks `port home zulu-clock` for the number.
"""
import http.client
import json
import os
import subprocess
import sys
from functools import partial
from http.server import ThreadingHTTPServer
import threading

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
import server  # noqa: E402

PORT_CMD = '/opt/homebrew/bin/port'


def home(repo):
    return subprocess.run([PORT_CMD, 'home', repo], capture_output=True, text=True).stdout.strip()


def text(name):
    with open(os.path.join(ROOT, name)) as f:
        return f.read()


# ---- no typed numbers ----

# ---- launch.sh ----

# ---- server.py: the lookup ----

# ---- server.py: routes and status ----

def serve(handler):
    httpd = ThreadingHTTPServer(('127.0.0.1', 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


@pytest.fixture
def clock(monkeypatch):
    monkeypatch.setattr(server, 'MISSIONS_CALL', '')
    server._cache.clear()
    server._calls.clear()
    httpd = serve(partial(server.Handler, directory=ROOT))
    yield httpd.server_port
    httpd.shutdown()


def get(port, path, host=None):
    c = http.client.HTTPConnection('127.0.0.1', port, timeout=10)
    c.putrequest('GET', path, skip_host=True)
    c.putheader('Host', host or f'127.0.0.1:{port}')
    c.endheaders()
    r = c.getresponse()
    return r.status, r.getheader('Location'), r.read()


def state(port, name):
    _, _, body = get(port, '/status')
    return next(s for s in json.loads(body)['sources'] if s['name'] == name)


def test_a_failed_lookup_is_failing_in_status_and_does_not_crash(clock, monkeypatch):
    monkeypatch.setattr(server, 'home_port', lambda repo: (None, f'no home port for {repo}'))
    assert get(clock, '/source/presser')[0] == 502
    assert get(clock, '/missions')[0] == 502
    p, m = state(clock, 'presser'), state(clock, 'mission-cmd')
    assert (p['state'], p['error']) == ('failing', 'no home port for presser')
    assert (m['state'], m['error']) == ('failing', 'no home port for cmd-fs')
    assert get(clock, '/status')[0] == 200


def test_a_lookup_that_works_again_clears_the_old_failure(clock, monkeypatch):
    monkeypatch.setattr(server, 'home_port', lambda repo: (None, 'port command not found'))
    get(clock, '/source/presser')
    assert state(clock, 'presser')['state'] == 'failing'
    monkeypatch.setattr(server, 'home_port', lambda repo: (9, ''))
    assert get(clock, '/go/presser')[0] == 302
    assert state(clock, 'presser')['state'] == 'not called'
