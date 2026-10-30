"""Presser's home port is moving in the ports list from repo "handmarks" to repo "presser".

Until the Ports move is done the clock asks for `presser` first and falls back to `handmarks`.
(The fallback is temporary; this test goes with it.) Fake home_port so the live list does not matter.
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
import server  # noqa: E402


def fake(monkeypatch, answers):
    asked = []

    def home_port(repo):
        asked.append(repo)
        return answers.get(repo, (None, f'no home port for {repo}'))
    monkeypatch.setattr(server, 'home_port', home_port)
    server._calls.clear()
    return asked


def test_presser_answering_is_used_and_handmarks_is_not_asked(monkeypatch):
    asked = fake(monkeypatch, {'presser': (9001, ''), 'handmarks': (9002, '')})
    assert server.address('presser') == ('http://127.0.0.1:9001', '')
    assert asked == ['presser']


def test_handmarks_answers_when_presser_is_not_listed_yet(monkeypatch):
    asked = fake(monkeypatch, {'handmarks': (9002, '')})
    assert server.address('presser') == ('http://127.0.0.1:9002', '')
    assert asked == ['presser', 'handmarks']
    assert 'presser' not in server._calls


def test_both_failing_gives_a_plain_reason_and_a_failing_record(monkeypatch):
    fake(monkeypatch, {})
    base, reason = server.address('presser')
    assert base is None and reason == 'no home port for presser'
    assert server._calls['presser'][server.LOOKUP][1:] == (False, reason)
    assert next(s for s in server.status()['sources'] if s['name'] == 'presser')['state'] == 'failing'


def test_cmd_fs_is_unchanged(monkeypatch):
    asked = fake(monkeypatch, {})
    assert server.address('mission-cmd')[0] is None
    assert asked == ['cmd-fs']
