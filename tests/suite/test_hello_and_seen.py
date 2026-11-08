# Flagged for the reviewer, reason: endpoint (docs/code-map.md Endpoints: GET /__clock/hello and GET /__clock/seen (server.py), including the foreign-Host 403)
"""server.py tells a clock page which run of the server it is talking to, and tells the launcher whether a page has checked in.

GET /__clock/hello answers {"boot": <id of this run>, "mode": <launch mode or null>} and notes that a page checked in.
GET /__clock/seen answers {"seen": bool, "as_of"}: has any page said hello since this start. Both refuse a foreign Host.
Starts the real server.py as a process on a port from `port take`; an optional third argument is the launch mode.
"""
import http.client
import json
import os
import subprocess
import sys
import threading
import time
from functools import partial
from http.server import ThreadingHTTPServer

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
import server  # noqa: E402


def take_port():
    return int(subprocess.run(['port', 'take'], capture_output=True, text=True, check=True).stdout.strip())


def spawn(*extra):
    port = take_port()
    p = subprocess.Popen([sys.executable, os.path.join(ROOT, 'server.py'), str(port), ROOT, *extra],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return p, port


def wait_up(port):
    for _ in range(500):
        try:
            http.client.HTTPConnection('127.0.0.1', port, timeout=1).request('GET', '/status')
            break
        except OSError:
            time.sleep(0.01)


@pytest.fixture
def srv(monkeypatch):
    """The real Handler in this process, as a fresh start: no page has said hello yet."""
    monkeypatch.setattr(server, 'page_seen', False)
    httpd = ThreadingHTTPServer(('127.0.0.1', 0), partial(server.Handler, directory=ROOT))
    threading.Thread(target=httpd.serve_forever, kwargs={'poll_interval': 0.01}, daemon=True).start()
    yield httpd.server_port
    httpd.shutdown()
    httpd.server_close()


def get(port, path, host=None):
    c = http.client.HTTPConnection('127.0.0.1', port, timeout=5)
    c.request('GET', path, headers={'Host': host} if host else {})
    r = c.getresponse()
    return r.status, r.read()


def test_seen_is_false_until_a_page_says_hello(srv):
    status, raw = get(srv, '/__clock/seen')
    d = json.loads(raw)
    assert status == 200 and d['seen'] is False and d['as_of']
    get(srv, '/__clock/hello')
    assert json.loads(get(srv, '/__clock/seen')[1])['seen'] is True


def test_each_start_has_its_own_boot_id_and_may_carry_a_mode():
    # Two real processes: a boot id belongs to a run of the process. Started together, so they boot side by side.
    started = [spawn(*extra) for extra in ((), ('pink',))]
    boots = []
    try:
        for p, port in started:
            wait_up(port)
            boots.append(json.loads(get(port, '/__clock/hello')[1]))
    finally:
        for p, _ in started:
            p.kill()
            p.wait()
    assert boots[0]['boot'] != boots[1]['boot']
    assert boots[0]['mode'] is None and boots[1]['mode'] == 'pink'


def test_a_foreign_host_gets_403_and_is_not_noted(srv):
    assert get(srv, '/__clock/hello', host='evil.example')[0] == 403
    assert get(srv, '/__clock/seen', host='evil.example')[0] == 403
    assert json.loads(get(srv, '/__clock/seen')[1])['seen'] is False
