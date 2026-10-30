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

def test_no_other_apps_port_is_typed_into_the_code():
    for name in ('launch.sh', 'server.py', 'zulu-clock.js'):
        body = text(name)
        for number in ('8769', '8771', '8767'):
            assert number not in body, f'{number} is typed in {name}'
    assert 'PRESS_URL' not in text('zulu-clock.js')


def test_dock_json_takes_the_home_port_the_list_gives_the_clock():
    assert json.loads(text('dock.json'))['port'] == {'ports': 'zulu-clock'}
    assert home('zulu-clock').isdigit()


# ---- launch.sh ----

def test_launch_sh_stops_with_one_plain_line_when_the_list_has_no_port(tmp_path):
    fake = tmp_path / 'port'
    fake.write_text('#!/bin/sh\nexit 1\n')
    fake.chmod(0o755)
    env = dict(os.environ, PATH=f'{tmp_path}:/usr/bin:/bin')
    r = subprocess.run(['bash', os.path.join(ROOT, 'launch.sh')], capture_output=True, text=True, env=env, timeout=20)
    assert r.returncode == 1
    lines = [l for l in (r.stdout + r.stderr).splitlines() if l.strip()]
    assert len(lines) == 1 and 'zulu-clock' in lines[0] and 'port' in lines[0], lines


def test_launch_sh_reads_its_port_from_the_list():
    assert 'port home zulu-clock' in text('launch.sh')


# ---- server.py: the lookup ----

def test_home_port_finds_presser_and_cmd_fs_in_the_list():
    assert server.home_port('presser') == (int(home('presser')), '')
    assert server.home_port('cmd-fs') == (int(home('cmd-fs')), '')


def test_home_port_says_why_in_plain_words(monkeypatch):
    assert server.home_port('no-such-repo') == (None, 'no home port for no-such-repo')
    monkeypatch.setattr(server.shutil, 'which', lambda name: None)
    monkeypatch.setattr(server, 'PORT_FALLBACK', '/nonexistent/port')
    assert server.home_port('presser') == (None, 'port command not found')


def test_home_port_works_with_a_bare_path(monkeypatch):
    monkeypatch.setenv('PATH', '/usr/bin:/bin')
    assert server.home_port('presser')[0] == int(home('presser'))


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


def test_go_presser_sends_the_browser_to_presser(clock):
    status, location, _ = get(clock, '/go/presser')
    assert status == 302
    assert location == f"http://127.0.0.1:{home('presser')}/"


def test_go_presser_has_the_same_host_check_as_every_route(clock):
    assert get(clock, '/go/presser', host='attacker.example')[0] == 403


def test_go_presser_refuses_plainly_when_the_address_is_unknown(clock, monkeypatch):
    monkeypatch.setattr(server, 'home_port', lambda repo: (None, 'no home port for presser'))
    status, location, body = get(clock, '/go/presser')
    assert status == 502 and location is None
    assert b'no home port for presser' in body


def test_a_failed_lookup_is_failing_in_status_and_does_not_crash(clock, monkeypatch):
    monkeypatch.setattr(server, 'home_port', lambda repo: (None, f'no home port for {repo}'))
    assert get(clock, '/source/presser')[0] == 502
    assert get(clock, '/missions')[0] == 502
    p, m = state(clock, 'presser'), state(clock, 'mission-cmd')
    assert (p['state'], p['error']) == ('failing', 'no home port for presser')
    assert (m['state'], m['error']) == ('failing', 'no home port for cmd-fs')
    assert get(clock, '/status')[0] == 200


def test_missions_call_still_overrides_cmd_fs_address(clock, monkeypatch):
    monkeypatch.setattr(server, 'MISSIONS_CALL', 'http://127.0.0.1:1')
    monkeypatch.setattr(server, 'home_port', lambda repo: (None, 'must not be asked'))
    assert get(clock, '/missions')[0] == 502
    assert state(clock, 'mission-cmd')['state'] == 'offline'


def test_a_lookup_that_works_again_clears_the_old_failure(clock, monkeypatch):
    monkeypatch.setattr(server, 'home_port', lambda repo: (None, 'port command not found'))
    get(clock, '/source/presser')
    assert state(clock, 'presser')['state'] == 'failing'
    monkeypatch.setattr(server, 'home_port', lambda repo: (9, ''))
    assert get(clock, '/go/presser')[0] == 302
    assert state(clock, 'presser')['state'] == 'not called'
