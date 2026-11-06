"""dock.json declares Zulu Clock's Dock icon the way docks reads it (docks/docs/dock-json.md, f61fbe6),
and agrees with what the code does today: the port the ports list gives launch.sh, its address and own-server check, the
environment server.py reads, and which files server.py reads once at start."""

# The helpers and fixtures are the suite's own (tests/suite/test_dock_json.py), not a copy.
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

from suite.test_dock_json import read, dock  # noqa: E402,F401


def test_the_icon_is_an_svg_in_this_repo():
    d = dock()
    assert d['icon'].endswith('.svg')
    assert read(d['icon']).lstrip().startswith('<svg')
