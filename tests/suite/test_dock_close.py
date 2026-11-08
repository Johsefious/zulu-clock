"""Zulu Clock answers docks' two restart-safety calls and stops itself after `closing`.

Starts the real server.py as a process on a port from `port take`.
"""
import http.client
import json
import os
import subprocess
import sys
import time
from datetime import datetime

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def take_port():
    return int(subprocess.run(['port', 'take'], capture_output=True, text=True, check=True).stdout.strip())


def start():
    port = take_port()
    p = subprocess.Popen([sys.executable, os.path.join(ROOT, 'server.py'), str(port), ROOT],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(500):
        try:
            http.client.HTTPConnection('127.0.0.1', port, timeout=1).request('GET', '/status')
            break
        except OSError:
            time.sleep(0.01)
    return p, port


def stop(p):
    if p.poll() is None:
        p.kill()
    p.wait()


@pytest.fixture
def srv():
    """Its own server, for the tests that stop it."""
    p, port = start()
    yield p, port
    stop(p)


@pytest.fixture(scope='module')
def shared():
    """One server for every test that must leave the clock running. After the last of them, a short wait:
    a refused close that still began stopping the server would have done so by then."""
    p, port = start()
    yield p, port
    time.sleep(0.3)
    alive = p.poll() is None
    stop(p)
    assert alive, 'a refused close stopped the clock'


def ask(port, method, path, body=None, host=None):
    c = http.client.HTTPConnection('127.0.0.1', port, timeout=5)
    headers = {'Content-Type': 'application/json'}
    if host:
        headers['Host'] = host
    c.request(method, path, body=body, headers=headers)
    r = c.getresponse()
    return r.status, r.read()


def is_utc_iso(s):
    return datetime.fromisoformat(s).utcoffset().total_seconds() == 0


def test_restart_status_is_clear_with_a_reason(shared):
    p, port = shared
    t = time.time()
    status, raw = ask(port, 'GET', '/__docks/restart-status')
    assert time.time() - t < 0.1
    d = json.loads(raw)
    assert status == 200 and d['clear'] is True and d['reason'] and is_utc_iso(d['as_of'])
    assert p.poll() is None


@pytest.mark.parametrize('why', ['restart', 'quit'])
def test_close_answers_closing_then_the_process_exits(srv, why):
    p, port = srv
    status, raw = ask(port, 'POST', '/__docks/close', json.dumps({'for': why}))
    d = json.loads(raw)
    assert status == 200 and d['answer'] == 'closing' and d['reason'] and is_utc_iso(d['as_of'])
    assert p.wait(timeout=5) is not None


def test_close_refuses_a_foreign_host(shared):
    p, port = shared
    assert ask(port, 'POST', '/__docks/close', '{"for": "quit"}', host='evil.example')[0] == 403
    assert p.poll() is None


@pytest.mark.parametrize('body', [None, '', 'not json', '[]', '{}', '{"for": "reboot"}', '{"for": 3}'])
def test_close_with_a_bad_body_is_400_with_a_reason(shared, body):
    p, port = shared
    status, raw = ask(port, 'POST', '/__docks/close', body)
    assert status == 400 and len(raw.strip()) > 10
    assert p.poll() is None


def test_any_other_post_is_404(shared):
    p, port = shared
    assert ask(port, 'POST', '/status', '{"for": "quit"}')[0] == 404
    assert p.poll() is None


def test_a_close_that_is_not_json_is_refused_and_the_clock_keeps_running(shared):
    # A web page can send a form post as text/plain without asking; only docks sends application/json.
    p, port = shared
    c = http.client.HTTPConnection('127.0.0.1', port, timeout=5)
    c.request('POST', '/__docks/close', body='{"for": "quit"}', headers={'Content-Type': 'text/plain'})
    r = c.getresponse()
    assert r.status == 415 and b'application/json' in r.read()
    assert p.poll() is None
