"""dock.json declares Zulu Clock's Dock icon the way docks reads it (docks/docs/dock-json.md, f61fbe6),
and agrees with what the code does today: the port the ports list gives launch.sh, its address and own-server check, the
environment server.py reads, and which files server.py reads once at start."""
import json
import os
import re
import subprocess

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
REQUIRED = ['dock', 'key', 'name', 'bundle_id', 'icon', 'page', 'tab_match']
KNOWN = REQUIRED + ['icon_px', 'port', 'start', 'restart', 'ours', 'health', 'log', 'stale_if_changed',
                    'on_stale', 'restart_loses', 'restart_safety', 'reload_when', 'env', 'link_scheme',
                    'front_open_tab', 'close_tabs_on_quit', 'icon_icns']


def read(name):
    with open(os.path.join(ROOT, name)) as f:
        return f.read()


def dock():
    return json.loads(read('dock.json'))


def port_number(d):
    """The number docks uses: a typed one, or what `port home <repo>` prints for {"ports": "<repo>"}."""
    if isinstance(d['port'], dict):
        return int(subprocess.run(['port', 'home', d['port']['ports']], capture_output=True, text=True).stdout)
    return d['port']


def fill(text, d):
    return text.replace('{port}', str(port_number(d))).replace('{repo}', ROOT)


def launch_sh(var):
    return re.search(rf'^{var}=(.*)$', read('launch.sh'), re.M).group(1).strip('"')


def test_the_icon_is_an_svg_in_this_repo():
    d = dock()
    assert d['icon'].endswith('.svg')
    assert read(d['icon']).lstrip().startswith('<svg')
