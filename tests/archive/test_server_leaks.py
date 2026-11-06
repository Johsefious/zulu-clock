"""server.py hands out only what the page draws, only to the page, and only the page's own files.

Starts the real Handler on a free port beside two fake upstreams (cmd fs's router and the Presser app) that
answer with more than the clock needs, then asks the way a browser would, with the Host header it sends.
"""

# The helpers and fixtures are the suite's own (tests/suite/test_server_leaks.py), not a copy.
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

from suite.test_server_leaks import clock, get, cache_control  # noqa: E402,F401


def test_the_clock_itself_still_gets_answers(clock):
    for host in (f'127.0.0.1:{clock}', f'localhost:{clock}'):
        assert get(clock, '/missions', host=host)[0] == 200, host
        assert get(clock, '/status', host=host)[0] == 200, host


def test_the_page_and_script_are_revalidated_on_every_load(clock):
    # Without this Chrome may reuse a cached old zulu-clock.js against a new page after an update.
    for path in ('/', '/zulu-clock.html', '/zulu-clock.js'):
        assert cache_control(clock, path) == (200, 'no-cache'), path
