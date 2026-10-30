"""open_clock.sh says why it could not reuse a tab when a browser refuses Apple events (-1743)."""
import os
import subprocess

SCRIPT = os.path.join(os.path.dirname(__file__), '..', '..', 'tools', 'open_clock.sh')
URL = 'http://127.0.0.1:8800/zulu-clock'
DENIED = 'execution error: Not authorized to send Apple events to {}. (-1743)'


def _run(tmp_path, osascript_body):
    bin_dir = tmp_path / 'bin'
    bin_dir.mkdir()
    log = tmp_path / 'open.log'
    (bin_dir / 'osascript').write_text('#!/bin/bash\n' + osascript_body + '\n')
    (bin_dir / 'open').write_text('#!/bin/bash\necho "$1" >> "%s"\n' % log)
    for f in bin_dir.iterdir():
        f.chmod(0o755)
    env = dict(os.environ, PATH='%s:%s' % (bin_dir, os.environ['PATH']))
    r = subprocess.run(['bash', SCRIPT, '8800', URL, 'KEEP'], env=env, capture_output=True, text=True)
    return r, (log.read_text().split() if log.exists() else [])


def test_denied_browser_is_named_and_open_still_runs(tmp_path):
    # the script text names the app; fake keys off it
    body = ('case "$*" in *\'application "Google Chrome"\'*) echo "%s" >&2;; '
            '*) echo "%s" >&2;; esac; exit 1' % (DENIED.format('Google Chrome'), DENIED.format('Safari')))
    r, opened = _run(tmp_path, body)
    assert 'Google Chrome' in r.stderr and 'Safari' in r.stderr
    assert 'Opening a new tab' in r.stderr
    assert opened == [URL]


def test_reloaded_tab_is_quiet_and_open_not_called(tmp_path):
    r, opened = _run(tmp_path, 'echo reloaded')
    assert r.stderr == ''
    assert opened == []
