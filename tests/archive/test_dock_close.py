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


@pytest.fixture
def srv():
    port = take_port()
    p = subprocess.Popen([sys.executable, os.path.join(ROOT, 'server.py'), str(port), ROOT],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(50):
        try:
            http.client.HTTPConnection('127.0.0.1', port, timeout=1).request('GET', '/status')
            break
        except OSError:
            time.sleep(0.1)
    yield p, port
    if p.poll() is None:
        p.kill()
    p.wait()


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


def test_restart_status_refuses_a_foreign_host(srv):
    _, port = srv
    assert ask(port, 'GET', '/__docks/restart-status', host='evil.example')[0] == 403
