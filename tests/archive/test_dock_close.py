"""Zulu Clock answers docks' two restart-safety calls and stops itself after `closing`.

Starts the real server.py as a process on a port from `port take`.
"""

# The helpers and fixtures are the suite's own (tests/suite/test_dock_close.py), not a copy.
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

from suite.test_dock_close import srv, ask  # noqa: E402,F401


def test_restart_status_refuses_a_foreign_host(srv):
    _, port = srv
    assert ask(port, 'GET', '/__docks/restart-status', host='evil.example')[0] == 403
