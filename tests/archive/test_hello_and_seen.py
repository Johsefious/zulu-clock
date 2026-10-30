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
import time

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def take_port():
    return int(subprocess.run(['port', 'take'], capture_output=True, text=True, check=True).stdout.strip())


def start(*extra):
    port = take_port()
    p = subprocess.Popen([sys.executable, os.path.join(ROOT, 'server.py'), str(port), ROOT, *extra],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(50):
        try:
            http.client.HTTPConnection('127.0.0.1', port, timeout=1).request('GET', '/status')
            break
        except OSError:
            time.sleep(0.1)
    return p, port


@pytest.fixture
def srv():
    p, port = start()
    yield port
    p.kill()
    p.wait()


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


def test_hello_gives_a_boot_id_and_no_mode_by_default(srv):
    status, raw = get(srv, '/__clock/hello')
    d = json.loads(raw)
    assert status == 200 and d['boot'] and d['mode'] is None
    assert json.loads(get(srv, '/__clock/hello')[1])['boot'] == d['boot']


def test_each_start_has_its_own_boot_id_and_may_carry_a_mode():
    boots = []
    for extra in ((), ('pink',)):
        p, port = start(*extra)
        try:
            boots.append(json.loads(get(port, '/__clock/hello')[1]))
        finally:
            p.kill()
            p.wait()
    assert boots[0]['boot'] != boots[1]['boot']
    assert boots[0]['mode'] is None and boots[1]['mode'] == 'pink'


def test_a_foreign_host_gets_403_and_is_not_noted(srv):
    assert get(srv, '/__clock/hello', host='evil.example')[0] == 403
    assert get(srv, '/__clock/seen', host='evil.example')[0] == 403
    assert json.loads(get(srv, '/__clock/seen')[1])['seen'] is False
