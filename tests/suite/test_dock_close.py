"""Zulu Clock answers docks' two restart-safety calls and stops itself after `closing`.

Starts the real server.py as a process on a port from `port take`.
"""
import http.client
import json
import os
import subprocess
import sys
import threading
import time
from datetime import datetime
from functools import partial
from http.server import ThreadingHTTPServer

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
import server  # noqa: E402


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


class Recording(ThreadingHTTPServer):
    """The real Handler's server, remembering whether anything asked it to shut down."""
    def shutdown(self):
        self.stopped.set()
        super().shutdown()


@pytest.fixture(scope='module')
def shared():
    """One in-process server for every test that must leave the clock running: the close call stops a server
    by calling its shutdown, so a refused close must never reach it. After the last test, a short wait: a
    refusal that still began a shutdown would have done so by then."""
    httpd = Recording(('127.0.0.1', 0), partial(server.Handler, directory=ROOT))
    httpd.stopped = threading.Event()
    threading.Thread(target=httpd.serve_forever, kwargs={'poll_interval': 0.01}, daemon=True).start()
    yield httpd, httpd.server_port
    refused_all = not httpd.stopped.wait(0.1)
    httpd.shutdown()
    httpd.server_close()
    assert refused_all, 'a refused close stopped the clock'


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
    assert not p.stopped.is_set()


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
    assert not p.stopped.is_set()


@pytest.mark.parametrize('body', [None, '', 'not json', '[]', '{}', '{"for": "reboot"}', '{"for": 3}'])
def test_close_with_a_bad_body_is_400_with_a_reason(shared, body):
    p, port = shared
    status, raw = ask(port, 'POST', '/__docks/close', body)
    assert status == 400 and len(raw.strip()) > 10
    assert not p.stopped.is_set()


def test_any_other_post_is_404(shared):
    p, port = shared
    assert ask(port, 'POST', '/status', '{"for": "quit"}')[0] == 404
    assert not p.stopped.is_set()


def test_a_close_that_is_not_json_is_refused_and_the_clock_keeps_running(shared):
    # A web page can send a form post as text/plain without asking; only docks sends application/json.
    p, port = shared
    c = http.client.HTTPConnection('127.0.0.1', port, timeout=5)
    c.request('POST', '/__docks/close', body='{"for": "quit"}', headers={'Content-Type': 'text/plain'})
    r = c.getresponse()
    assert r.status == 415 and b'application/json' in r.read()
    assert not p.stopped.is_set()
