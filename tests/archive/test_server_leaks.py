"""server.py hands out only what the page draws, only to the page, and only the page's own files.

Starts the real Handler on a free port beside two fake upstreams (cmd fs's router and the Presser app) that
answer with more than the clock needs, then asks the way a browser would, with the Host header it sends.
"""
import http.client
import json
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from functools import partial

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
import server  # noqa: E402

MISSION = {
    'id': 'm1', 'key': 'k1', 'label': 'Fresno', 'date': '2026-11-02', 'days_out': 4, 'types': ['drone'],
    'facilities': ['Acme Farm'], 'members': ['Pat Quinn', 'Sam Lee'], 'confirmed': True, 'briefingSent': False,
    'approved': False, 'cancelled': False, 'gate_warning': True, 'planDue': '2026-10-31T00:00:00Z',
    'planReceived': {'review_by': '2026-11-01T00:00:00Z', 'link': 'https://docs.example/secret'},
    'pointPerson': 'Pat Quinn', 'lead': 'Sam Lee', 'briefingDoc': 'DOC-ID', 'remoteSupport': 'Kim Ro',
    'checkin': '555-0100', 'clockedOut': {'by': 'x'}, 'gate_reason': 'why', 'problems': ['p'],
}
STORY = {
    'id': 's1', 'short_name': 'Acme', 'kind': 'advisory', 'archived': False, 'countdown_to': '2026-11-02T18:00:00Z',
    'doc': 'PA', 'status': 'draft', 'progress': [1, 4], 'overdue': 0, 'today': 1, 'upcoming': 2,
    'next': {'text': 'Call desk', 'state': 'late', 'contact': 'reporter@example.org'}, 'work': 3,
    'sends_open': [{'label': 'Send PA', 'due': '2026-11-01T12:00:00Z', 'to': 'desk@example.org'}], 'old_builder': False,
}
SUMMARY = {'stories': [STORY], 'today': {'messages': ['text to a reporter'], 'verify': ['a claim']},
           'totals': {'stories': 1, 'overdue': 0, 'today': 1, 'messages': 1, 'verify': 1, 'work': 3}}


class Fake(BaseHTTPRequestHandler):
    def reply(self, obj):
        body = json.dumps(obj).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        self.reply({'read_at': 'now', 'problems': [], 'missions': [MISSION]})

    def do_GET(self):
        self.reply(SUMMARY)

    def log_message(self, *a):
        pass


def serve(handler):
    httpd = ThreadingHTTPServer(('127.0.0.1', 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


@pytest.fixture
def clock(monkeypatch):
    fake = serve(Fake)
    monkeypatch.setattr(server, 'MISSIONS_CALL', f'http://127.0.0.1:{fake.server_port}')
    monkeypatch.setitem(server.SOURCES, 'presser', ('Presser', 'press', f'http://127.0.0.1:{fake.server_port}/api/summary'))
    server._cache.clear()
    httpd = serve(partial(server.Handler, directory=ROOT))
    yield httpd.server_port
    httpd.shutdown()
    fake.shutdown()


def get(port, path, host=None):
    c = http.client.HTTPConnection('127.0.0.1', port, timeout=10)
    c.putrequest('GET', path, skip_host=True)
    c.putheader('Host', host or f'127.0.0.1:{port}')
    c.endheaders()
    r = c.getresponse()
    return r.status, r.read()


def cache_control(port, path):
    c = http.client.HTTPConnection('127.0.0.1', port, timeout=10)
    c.request('GET', path)
    r = c.getresponse()
    r.read()
    return r.status, r.getheader('Cache-Control')


def test_a_foreign_host_name_gets_nothing(clock):
    for path in ('/missions', '/source/presser', '/status', '/zulu-clock.html'):
        assert get(clock, path, host='attacker.example')[0] == 403, path
        assert get(clock, path, host=f'attacker.example:{clock}')[0] == 403, path


def test_the_clock_itself_still_gets_answers(clock):
    for host in (f'127.0.0.1:{clock}', f'localhost:{clock}'):
        assert get(clock, '/missions', host=host)[0] == 200, host
        assert get(clock, '/status', host=host)[0] == 200, host


def test_missions_carry_only_what_the_card_draws(clock):
    status, body = get(clock, '/missions')
    assert status == 200
    m = json.loads(body)['missions'][0]
    assert set(m) == {'label', 'days_out', 'types', 'facilities', 'members', 'confirmed', 'briefingSent',
                      'approved', 'cancelled', 'gate_warning', 'planDue', 'planReceived'}
    assert m['members'] == ['Pat', 'Sam']                     # first names only, as the card shows
    assert m['planReceived'] == {'review_by': '2026-11-01T00:00:00Z'}
    assert 'secret' not in body.decode() and 'Quinn' not in body.decode()


def test_press_carries_only_what_the_card_draws(clock):
    status, body = get(clock, '/source/presser')
    assert status == 200
    d = json.loads(body)
    assert set(d) == {'stories', 'totals'}
    assert set(d['totals']) == {'overdue', 'today', 'messages'}
    assert set(d['stories'][0]) == {'id', 'short_name', 'archived', 'countdown_to', 'doc', 'progress', 'overdue',
                                    'today', 'upcoming', 'next', 'sends_open', 'old_builder'}
    assert d['stories'][0]['next'] == {'text': 'Call desk', 'state': 'late'}
    assert d['stories'][0]['sends_open'] == [{'label': 'Send PA', 'due': '2026-11-01T12:00:00Z'}]
    assert 'example.org' not in body.decode() and 'a reporter' not in body.decode()


def test_only_the_page_is_served_from_the_folder(clock):
    assert get(clock, '/zulu-clock.html')[0] == 200
    assert get(clock, '/')[0] == 200
    status, body = get(clock, '/zulu-clock.js')
    assert status == 200 and b'function pressVisible' in body
    for path in ('/.git/config', '/test-runs.jsonl', '/server.py', '/docs/handoff.md', '/tests/conftest.py',
                 '/tests/archive/page_js.py', '/zulu-clock.js.bak', '/zulu-clock.css',
                 '/%2e%2e/etc/passwd'):
        assert get(clock, path)[0] == 404, path


def test_the_page_and_script_are_revalidated_on_every_load(clock):
    # Without this Chrome may reuse a cached old zulu-clock.js against a new page after an update.
    for path in ('/', '/zulu-clock.html', '/zulu-clock.js'):
        assert cache_control(clock, path) == (200, 'no-cache'), path
