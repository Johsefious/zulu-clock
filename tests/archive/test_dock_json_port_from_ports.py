"""dock.json takes the clock's port from Ports (docks/docs/dock-json.md, `port` row, ed079d8): it writes
{"ports": "zulu-clock"} instead of a typed number, and Ports has a home port under that name."""
import json
import os
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_dock_json_names_the_ports_list_entry_instead_of_a_number():
    with open(os.path.join(ROOT, 'dock.json')) as f:
        assert json.load(f)['port'] == {'ports': 'zulu-clock'}


def test_ports_has_a_home_port_for_that_name():
    r = subprocess.run(['/opt/homebrew/bin/port', 'home', 'zulu-clock'], capture_output=True, text=True)
    assert r.returncode == 0 and r.stdout.strip().isdigit()
