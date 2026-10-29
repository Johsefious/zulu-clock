"""server.py forgets cached answers after 120 s and logged calls after 24 h, so it doesn't grow over weeks.

Drives server.call with a fake clock and a fake outside fetch (no network).
"""
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
import server  # noqa: E402

HOUR = 3600


class FakeReply:
    headers = {'Content-Type': 'text/plain'}

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def read(self):
        return b'ok'


@pytest.fixture
def clock(monkeypatch):
    now = [1_000_000.0]
    monkeypatch.setattr(server.time, 'time', lambda: now[0])
    monkeypatch.setattr(server.urllib.request, 'urlopen', lambda req, timeout=None: FakeReply())
    monkeypatch.setattr(server, '_cache', {})
    monkeypatch.setattr(server, '_calls', {})
    return now


def test_old_cache_entries_are_dropped(clock):
    for i in range(5):
        server.call('open-meteo', f'https://x.example/?lat={i}')
    clock[0] += server.CACHE_SECONDS + 1
    server.call('open-meteo', 'https://x.example/?lat=new')
    assert list(server._cache) == ['https://x.example/?lat=new']


def test_old_log_entries_are_dropped_and_status_keeps_the_last_day(clock):
    server.call('open-meteo', 'https://x.example/?old=1')
    clock[0] += 25 * HOUR
    server.call('open-meteo', 'https://x.example/?a=1')
    clock[0] += HOUR
    server.call('open-meteo', 'https://x.example/?b=1')
    assert set(server._calls['open-meteo']) == {'https://x.example/?a=1', 'https://x.example/?b=1'}
    row = next(s for s in server.status()['sources'] if s['name'] == 'open-meteo')
    assert (row['state'], row['calls'], row['answered']) == ('answering', 2, 2)


def test_a_source_not_called_for_a_day_leaves_no_log(clock):
    server.call('metar', 'https://x.example/?m=1')
    clock[0] += 25 * HOUR
    server.call('open-meteo', 'https://x.example/?a=1')
    assert 'metar' not in server._calls
    row = next(s for s in server.status()['sources'] if s['name'] == 'metar')
    assert row['state'] == 'not called'
