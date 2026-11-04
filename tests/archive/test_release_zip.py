"""Zulu Clock ships through `repo release`: app.json, VERSION, the release step's zip folder, the installer's rules,
and a server that finds the Ports tool where the installer put it."""
import json
import os
import shutil
import stat
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
import server  # noqa: E402

INSTALLER = 'Install Zulu Clock.command'


def text(name):
    with open(os.path.join(ROOT, name), encoding='utf-8') as f:
        return f.read()


def app_json():
    return json.loads(text('app.json'))


def test_app_json_says_it_ships_with_a_release_step():
    cfg = app_json()
    assert cfg['ships'] is True
    assert '{dest}' in cfg['release'] and '{version}' in cfg['release']
    assert set(cfg['uses']) == {'docks', 'port'}


def test_version_file_and_git_ignored_dist():
    parts = text('VERSION').strip().split('.')
    assert len(parts) == 3 and all(p.isdigit() for p in parts)
    assert 'dist/' in text('.gitignore').split()


@pytest.fixture(scope='module')
def built(tmp_path_factory):
    dest = tmp_path_factory.mktemp('zip') / 'Zulu Clock 9.9.9'
    dest.mkdir()
    step = [dest.as_posix() if a == '{dest}' else '9.9.9' if a == '{version}' else a
            for a in __import__('shlex').split(app_json()['release'])]
    r = subprocess.run(step, cwd=ROOT, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return dest


def listing(top):
    return sorted(os.path.relpath(os.path.join(d, n), top) for d, _, ns in os.walk(top) for n in ns)


def test_the_zip_folder_holds_an_installer_a_read_me_and_only_what_the_clock_runs(built):
    files = listing(built)
    assert INSTALLER in files and 'Read me.txt' in files
    assert os.stat(built / INSTALLER).st_mode & stat.S_IXUSR
    run = sorted(f[len('Files/'):] for f in files if f.startswith('Files/'))
    assert run == ['VERSION', 'dock.json', 'fonts/share-tech-mono-latin.woff2', 'fonts/vt323-latin.woff2',
                   'icons/Zulu Clock.icns', 'icons/zulu-clock.svg', 'server.py', 'zulu-clock.html', 'zulu-clock.js']
    assert not os.path.lexists(built / 'Files' / 'shared')
    assert (built / 'Files' / 'VERSION').read_text().strip() == '9.9.9'
    for must in ('server.py', 'zulu-clock.html', 'zulu-clock.js', 'dock.json', 'icons/zulu-clock.svg'):
        assert 'Files/' + must in files
    for name in files:
        assert not name.endswith(('.jsonl', '.md', '.env', '.sh')), name
        assert 'handoff' not in name and 'test-runs' not in name


def test_the_installer_follows_the_standard():
    body = text('tools/' + INSTALLER)
    assert subprocess.run(['bash', '-n', os.path.join(ROOT, 'tools', INSTALLER)]).returncode == 0
    assert 'install-shared.sh' in body
    assert 'ZULU_SETUP_HOME' in body and 'DOCKS_TEST_HOME' in body
    assert 'Library/Application Support/Docks/tool/bin/docks' in body
    assert 'Library/Application Support/Ports/tool/port' in body
    assert 'app add' in body and 'app refresh' in body
    for line in body.splitlines():
        s = line.strip()
        assert not s.startswith('git ') and ' git ' not in s.split('#')[0], line


def test_the_server_finds_the_ports_tool_where_the_installer_puts_it(tmp_path, monkeypatch):
    tool = tmp_path / 'Library' / 'Application Support' / 'Ports' / 'tool'
    tool.mkdir(parents=True)
    exe = tool / 'port'
    exe.write_text('#!/bin/sh\necho 4321\n')
    exe.chmod(0o755)
    monkeypatch.setenv('HOME', str(tmp_path))
    monkeypatch.setattr(shutil, 'which', lambda *_: None)
    monkeypatch.setattr(server, 'PORT_FALLBACK', '/nonexistent/port')
    assert server.home_port('presser') == (4321, '')
