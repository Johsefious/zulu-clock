"""dock.json declares Zulu Clock's Dock icon the way docks reads it (docks/docs/dock-json.md, f61fbe6),
and agrees with what the code does today: launch.sh's port, address and own-server check, the
environment server.py reads, and which files server.py reads once at start."""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REQUIRED = ['dock', 'key', 'name', 'bundle_id', 'icon', 'page', 'tab_match']
KNOWN = REQUIRED + ['icon_px', 'port', 'start', 'restart', 'ours', 'health', 'log', 'stale_if_changed',
                    'on_stale', 'restart_loses', 'reload_when', 'env', 'link_scheme']


def read(name):
    with open(os.path.join(ROOT, name)) as f:
        return f.read()


def dock():
    return json.loads(read('dock.json'))


def fill(text, d):
    return text.replace('{port}', str(d['port'])).replace('{repo}', ROOT)


def launch_sh(var):
    return re.search(rf'^{var}=(.*)$', read('launch.sh'), re.M).group(1).strip('"')


def test_every_field_is_known_and_the_required_ones_are_there():
    d = dock()
    assert d['dock'] == 1
    assert [k for k in REQUIRED if k not in d] == []
    assert [k for k in d if k not in KNOWN] == []
    assert (d['key'], d['name'], d['bundle_id']) == ('zulu', 'Zulu Clock', 'org.ffw.zulu-clock')


def test_the_icon_is_an_svg_in_this_repo():
    d = dock()
    assert d['icon'].endswith('.svg')
    assert read(d['icon']).lstrip().startswith('<svg')


def test_port_page_and_tab_match_agree_with_launch_sh():
    d = dock()
    port = launch_sh('PORT')
    assert d['port'] == int(port)
    assert fill(d['page'], d) == launch_sh('URL').replace('$PORT', port)
    assert fill(d['tab_match'], d) in fill(d['page'], d)


def test_a_server_docks_starts_is_one_launch_sh_and_docks_both_call_their_own():
    d = dock()
    command_line = ' '.join(fill(w, d) for w in d['start'])
    own = launch_sh('OWN_CMD').replace('$SCRIPT_DIR', ROOT).replace('$PORT', str(d['port']))
    assert own in command_line
    assert fill(d['ours']['command'], d) in command_line


def test_health_is_a_path_the_server_answers_itself():
    assert f"path == '{dock()['health']}'" in read('server.py')


def test_stale_means_server_py_changed_and_not_the_page_it_reads_every_request():
    d = dock()
    assert d['stale_if_changed'] == ['server.py']
    assert d['on_stale'] == 'restart'
    local_imports = [m for m in re.findall(r'^(?:from|import) (\w+)', read('server.py'), re.M)
                     if os.path.exists(os.path.join(ROOT, m + '.py'))]
    assert local_imports == []


def test_env_passes_through_every_variable_server_py_reads():
    read_vars = set(re.findall(r"os\.environ\.get\('(\w+)'", read('server.py')))
    assert read_vars and set(dock()['env']) == read_vars
    assert all(v is None for v in dock()['env'].values())
