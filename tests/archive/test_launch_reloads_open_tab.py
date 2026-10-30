"""launch.sh leaves one clock tab: the open page reloads itself, and a tab is opened only when none checked in.

The page notices the server's new boot id (test_heartbeat_reloads_on_new_boot.py); tools/open_clock.sh PORT URL
opens URL only when /__clock/seen says no page has checked in (test_open_clock.py). launch.sh hands the opener the
mode and starts server.py with it, so a page that is already open can switch to it. Nothing scripts the browser.
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def launch():
    return open(os.path.join(ROOT, 'launch.sh')).read()


def test_launch_sh_uses_the_opener_instead_of_a_bare_open():
    body = launch()
    assert 'tools/open_clock.sh' in body
    assert '\n    open "$URL"' not in body


def test_launch_sh_passes_the_mode_to_the_server():
    body = launch()
    assert 'server.py" $PORT "$SCRIPT_DIR" $MODE' in body


def test_launch_sh_has_no_browser_scripting():
    for name in ('launch.sh', 'launch-pink.sh', os.path.join('tools', 'open_clock.sh')):
        body = open(os.path.join(ROOT, name)).read().lower()
        assert 'osascript' not in body and 'applescript' not in body, name
