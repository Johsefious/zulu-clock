"""launch.sh reloads a clock tab that is already open instead of opening a second one.

tools/open_clock.sh PORT URL KEEP|NEW does the opening. It asks Safari, then Google Chrome (only if
running; the AppleScript checks that) for a tab whose URL contains `:PORT/zulu-clock`. Found: that tab
is reloaded, on its own URL (KEEP) or on URL (NEW, a mode was passed), and `open` is not called.
Not found, or osascript fails: `open URL`. Tests put fake `osascript` and `open` on PATH.
"""
import os
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPT = os.path.join(ROOT, 'tools', 'open_clock.sh')
URL = 'http://localhost:8769/zulu-clock.html'


def run(tmp_path, osascript_body, how='KEEP'):
    bin_dir = tmp_path / 'bin'
    bin_dir.mkdir()
    log = tmp_path / 'calls.log'
    # the fake logs "osascript <args>" and then does what the test says
    (bin_dir / 'osascript').write_text('#!/bin/bash\necho "osascript $*" >> "%s"\n%s\n' % (log, osascript_body))
    (bin_dir / 'open').write_text('#!/bin/bash\necho "open $*" >> "%s"\n' % log)
    for f in bin_dir.iterdir():
        f.chmod(0o755)
    env = dict(os.environ, PATH='%s:%s' % (bin_dir, os.environ['PATH']))
    r = subprocess.run(['bash', SCRIPT, '8769', URL, how], capture_output=True, text=True, env=env)
    calls = log.read_text().splitlines() if log.exists() else []
    return r, calls


def test_an_open_tab_is_reloaded_and_nothing_new_is_opened(tmp_path):
    r, calls = run(tmp_path, 'echo reloaded')
    assert r.returncode == 0
    assert not [c for c in calls if c.startswith('open ')], calls
    assert any(c.startswith('osascript') and ':8769/zulu-clock' in c for c in calls), calls


def test_a_passed_mode_reloads_on_the_new_url(tmp_path):
    r, calls = run(tmp_path, 'echo reloaded', how='NEW')
    assert any(URL in c and c.startswith('osascript') for c in calls), calls
    assert not [c for c in calls if c.startswith('open ')], calls


def test_no_open_tab_opens_the_page(tmp_path):
    r, calls = run(tmp_path, 'true')
    assert r.returncode == 0
    assert calls.count('open ' + URL) == 1, calls


def test_osascript_failing_opens_the_page_silently(tmp_path):
    r, calls = run(tmp_path, 'echo "not allowed" >&2; exit 1')
    assert r.returncode == 0
    assert r.stdout == '' and r.stderr == ''
    assert calls.count('open ' + URL) == 1, calls


def test_launch_sh_uses_it_instead_of_a_bare_open():
    body = open(os.path.join(ROOT, 'launch.sh')).read()
    assert 'tools/open_clock.sh' in body
    assert '\n    open "$URL"' not in body
