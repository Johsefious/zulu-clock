"""open_clock.sh PORT URL opens a tab only when no clock page has checked in with the server.

It asks GET /__clock/seen (curl) for up to CLOCK_SEEN_WAIT seconds (default 6). {"seen": true}: exit 0, `open` not called.
Never seen in that time: `open URL`. Tests put fake `curl` and `open` on PATH. No browser scripting anywhere.
"""
import os
import subprocess
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPT = os.path.join(ROOT, 'tools', 'open_clock.sh')
URL = 'http://localhost:8769/zulu-clock.html?mode=pink'


def run(tmp_path, curl_body, wait='1'):
    bin_dir = tmp_path / 'bin'
    bin_dir.mkdir()
    log = tmp_path / 'calls.log'
    (bin_dir / 'curl').write_text('#!/bin/bash\necho "curl $*" >> "%s"\n%s\n' % (log, curl_body))
    (bin_dir / 'open').write_text('#!/bin/bash\necho "open $*" >> "%s"\n' % log)
    for f in bin_dir.iterdir():
        f.chmod(0o755)
    env = dict(os.environ, PATH='%s:%s' % (bin_dir, os.environ['PATH']), CLOCK_SEEN_WAIT=wait)
    t = time.time()
    r = subprocess.run(['bash', SCRIPT, '8769', URL], capture_output=True, text=True, env=env)
    calls = log.read_text().splitlines() if log.exists() else []
    return r, calls, time.time() - t


def test_a_page_that_checked_in_means_nothing_is_opened(tmp_path):
    r, calls, took = run(tmp_path, 'echo \'{"seen": true, "as_of": "x"}\'')
    assert r.returncode == 0 and r.stderr == ''
    assert not [c for c in calls if c.startswith('open ')], calls
    assert 'http://127.0.0.1:8769/__clock/seen' in calls[0] and 'curl -s' in calls[0], calls
    assert took < 1


def test_a_page_that_checks_in_late_is_still_waited_for(tmp_path):
    # the fake says false the first two times, then true
    body = 'n=$(grep -c "^curl" "%s"); if [ "$n" -ge 3 ]; then echo \'{"seen": true}\'; else echo \'{"seen": false}\'; fi' % (
        tmp_path / 'calls.log')
    r, calls, _ = run(tmp_path, body, wait='5')
    assert not [c for c in calls if c.startswith('open ')], calls


def test_no_page_in_the_time_opens_the_url_once(tmp_path):
    r, calls, took = run(tmp_path, 'echo \'{"seen": false}\'')
    assert r.returncode == 0 and r.stderr == ''
    assert calls.count('open ' + URL) == 1, calls
    assert 1 <= took < 4


def test_a_server_that_does_not_answer_opens_the_url(tmp_path):
    r, calls, _ = run(tmp_path, 'exit 7')
    assert calls.count('open ' + URL) == 1, calls


def test_no_browser_scripting_in_the_opener():
    body = open(SCRIPT).read().lower()
    assert 'osascript' not in body and 'applescript' not in body and 'tell application' not in body
