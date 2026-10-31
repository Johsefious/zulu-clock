"""Every message that says what a restart loses names both things the server keeps in memory: the feed
cache and the call log /status reads. restart_status and dock.json's restart_loses once named only the cache."""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
import server  # noqa: E402


def names_both(text):
    return 'cache' in text and 'call log' in text


def test_the_close_reason_names_both():
    assert names_both(server.CLOSE_REASON)


def test_restart_status_names_both():
    assert names_both(server.restart_status()['reason'])


def test_dock_json_restart_loses_names_both():
    with open(os.path.join(ROOT, 'dock.json')) as f:
        assert names_both(json.load(f)['restart_loses'])
