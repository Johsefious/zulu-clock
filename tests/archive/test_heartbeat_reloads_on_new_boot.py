"""The page asks the server hello every HEARTBEAT_MS and reloads when the server's boot id changes (a restart).

heartbeatStep(first, answer, path, search) is the page's decision, run here in node. It returns {first, go}: first is the
boot id to remember (the first one heard), go is null (stay) or the address to load. A restart that carries a launch
mode loads path?mode=<mode>; one without reloads on the page's own address (so its ?mode= stays).
"""
import json
import subprocess

from page_js import pick


def run(call):
    script = pick('heartbeatStep') + 'console.log(JSON.stringify(%s))' % call
    return json.loads(subprocess.run(['node', '-e', script], capture_output=True, text=True, check=True).stdout)


def test_the_first_answer_is_remembered_and_nothing_reloads():
    assert run("heartbeatStep(null, {boot:'a', mode:null}, '/zulu-clock.html', '')") == {'first': 'a', 'go': None}


def test_the_same_boot_id_stays():
    assert run("heartbeatStep('a', {boot:'a', mode:'pink'}, '/zulu-clock.html', '')")['go'] is None


def test_a_new_boot_id_reloads_on_the_same_address():
    d = run("heartbeatStep('a', {boot:'b', mode:null}, '/zulu-clock.html', '?mode=blue')")
    assert d['go'] == '/zulu-clock.html?mode=blue'


def test_a_new_boot_id_with_a_mode_loads_that_mode():
    d = run("heartbeatStep('a', {boot:'b', mode:'pink'}, '/zulu-clock.html', '?mode=blue')")
    assert d['go'] == '/zulu-clock.html?mode=pink'


def test_a_bad_answer_changes_nothing():
    assert run("heartbeatStep('a', null, '/p', '')") == {'first': 'a', 'go': None}
    assert run("heartbeatStep('a', {}, '/p', '')") == {'first': 'a', 'go': None}
