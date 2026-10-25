"""The run record: every pytest run adds one line to test-runs.jsonl in the repo's main folder.

Each case builds a throwaway git repo holding this repo's pytest.ini, tests/conftest.py and
tools/failure_history.py, runs pytest there in a child process, and reads the line it wrote.
"""
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parents[2]
CLEAN_ENV = {k: v for k, v in os.environ.items() if not k.startswith(('GIT_', 'PYTEST_'))}
CLEAN_ENV.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM='1')     # no hooks or signing from this Mac
HASH = r'[0-9a-f]{10}'


def sh(*args, cwd):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, env=CLEAN_ENV, timeout=60)


def git(*args, cwd):
    r = sh('git', '-c', 'user.name=t', '-c', 'user.email=t@t', *args, cwd=cwd)
    assert r.returncode == 0, f'git {" ".join(args)} failed: {r.stderr}'
    return r.stdout.strip()


@pytest.fixture
def repo(tmp_path):
    root = tmp_path / 'main'
    (root / 'tests').mkdir(parents=True)
    (root / 'tools').mkdir()
    shutil.copy(HERE / 'pytest.ini', root / 'pytest.ini')
    shutil.copy(HERE / '.gitignore', root / '.gitignore')
    shutil.copy(HERE / 'tests' / 'conftest.py', root / 'tests' / 'conftest.py')
    shutil.copy(HERE / 'tools' / 'failure_history.py', root / 'tools' / 'failure_history.py')
    (root / 'tests' / 'test_sample.py').write_text(
        'def test_passes():\n    assert True\n\n'
        'def test_fails():\n    assert 1 == 2, "one is not two"\n')
    (root / 'notes.txt').write_text('first\n')
    git('init', '-q', '-b', 'main', cwd=root)
    git('add', '.', cwd=root)
    git('commit', '-qm', 'start', cwd=root)
    return root


def run(where, *args, cache=False):
    return sh(sys.executable, '-m', 'pytest', '-q', *([] if cache else ['-p', 'no:cacheprovider']), *args, cwd=where)


def lines(root):
    log = root / 'test-runs.jsonl'
    return [json.loads(x) for x in log.read_text().splitlines() if x.strip()] if log.exists() else []


def test_a_run_writes_one_line_with_every_field(repo):
    run(repo, 'tests/test_sample.py')
    [row] = lines(repo)
    assert row['commit'] == git('rev-parse', '--short', 'HEAD', cwd=repo)
    assert re.match(r'\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d[+-]\d{4}$', row['when'])
    assert row['dirty'] is False
    assert row['diff'] == ''
    assert row['args'] == ['-q', '-p', 'no:cacheprovider', 'tests/test_sample.py']
    assert row['full'] is False
    assert row['tests'] == 2
    assert row['exit'] == 1
    assert row['failed'] == ['tests/test_sample.py::test_fails']
    assert row['failed_files'] == ['tests/test_sample.py']
    assert row['why'] == {'tests/test_sample.py::test_fails': 'AssertionError: one is not two'}


def test_uncommitted_code_gets_a_diff_hash_that_tells_runs_apart(repo):
    (repo / 'notes.txt').write_text('second\n')
    run(repo, 'tests/test_sample.py')
    run(repo, 'tests/test_sample.py')
    (repo / 'notes.txt').write_text('third\n')
    run(repo, 'tests/test_sample.py')
    rows = lines(repo)
    a, b, c = (r['diff'] for r in rows)
    assert all(r['dirty'] is True for r in rows)
    assert re.fullmatch(HASH, a)
    assert a == b != c


def test_a_new_untracked_file_changes_the_diff_hash(repo):
    run(repo, 'tests/test_sample.py')
    (repo / 'tests' / 'test_new.py').write_text('def test_new():\n    pass\n')
    run(repo, 'tests/test_sample.py')
    run(repo, 'tests/test_sample.py')
    (repo / 'tests' / 'test_new.py').write_text('def test_new():\n    assert 1\n')
    run(repo, 'tests/test_sample.py')
    rows = lines(repo)
    clean, a, b, c = (r['diff'] for r in rows)
    assert [r['dirty'] for r in rows] == [False, True, True, True]
    assert clean == ''
    assert re.fullmatch(HASH, a)
    assert a == b != c


def test_an_unreadable_new_file_still_gets_the_line_written(repo):
    (repo / 'dangling').symlink_to(repo / 'nowhere')
    run(repo, 'tests/test_sample.py')
    [row] = lines(repo)
    assert row['dirty'] is True
    assert re.fullmatch(HASH, row['diff'])


def test_finder_files_do_not_count_as_uncommitted_code(repo):
    (repo / '.DS_Store').write_bytes(b'\0Bud1')
    (repo / 'tests' / '.DS_Store').write_bytes(b'\0Bud1')
    run(repo, 'tests/test_sample.py')
    [row] = lines(repo)
    assert row['dirty'] is False
    assert row['diff'] == ''


def test_only_a_plain_run_counts_as_the_whole_suite(repo):
    run(repo)
    run(repo, 'tests')
    run(repo, '-k', 'passes')
    run(repo, 'tests/test_sample.py')
    run(repo, '-m', 'slow')
    run(repo, '--lf', cache=True)
    assert [r['full'] for r in lines(repo)] == [True, True, False, False, False, False]


def test_a_file_that_will_not_load_is_a_failure_and_still_written(repo):
    (repo / 'tests' / 'test_sample.py').unlink()
    (repo / 'tests' / 'test_broken.py').write_text('import no_such_module\n\ndef test_x():\n    pass\n')
    result = run(repo)
    [row] = lines(repo)
    assert result.returncode != 0
    assert row['tests'] == 0
    assert row['exit'] == result.returncode
    assert row['failed'] == ['tests/test_broken.py']
    assert row['why'] == {'tests/test_broken.py': "ModuleNotFoundError: No module named 'no_such_module'"}


def test_a_worktree_writes_to_the_main_folder(repo, tmp_path):
    tree = tmp_path / 'tree'
    git('worktree', 'add', '-q', str(tree), '-b', 'side', cwd=repo)
    (tree / 'notes.txt').write_text('side\n')
    git('commit', '-qam', 'side', cwd=tree)
    run(tree, 'tests/test_sample.py')
    assert not (tree / 'test-runs.jsonl').exists()
    [row] = lines(repo)
    assert row['commit'] == git('rev-parse', '--short', 'HEAD', cwd=tree)


def test_a_line_that_cannot_be_written_does_not_stop_the_run(repo):
    (repo / 'test-runs.jsonl').mkdir()
    result = run(repo, 'tests/test_sample.py')
    assert result.returncode == 1
    assert '1 failed, 1 passed' in result.stdout
    assert 'Traceback' not in result.stdout + result.stderr
    [warning] = [ln for ln in result.stderr.splitlines() if 'run record not written' in ln]
    assert 'Is a directory' in warning     # it got as far as opening the file


def test_the_history_tool_lists_failed_tests_first_and_last(repo):
    rows = [
        {'when': '2026-10-01T10:00:00-0700', 'full': True, 'failed': ['tests/a.py::t1'], 'why': {'tests/a.py::t1': 'boom one'}},
        {'when': '2026-10-02T10:00:00-0700', 'full': False, 'failed': ['tests/a.py::t1', 'tests/b.py'], 'why': {'tests/b.py': 'ImportError: x'}},
        {'when': '2026-10-03T10:00:00-0700', 'full': True, 'failed': ['tests/a.py::t1'], 'why': {'tests/a.py::t1': 'boom three'}},
        {'when': '2026-10-04T10:00:00-0700', 'full': True, 'failed': []},
    ]
    (repo / 'test-runs.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in rows))
    tool = [sys.executable, str(repo / 'tools' / 'failure_history.py')]

    def history(*args):
        r = sh(*tool, *args, cwd=repo)
        assert r.returncode == 0, r.stderr
        return r.stdout.splitlines()

    head, t1, b = history()
    assert head == '4 runs recorded, 2026-10-01 10:00 to 2026-10-04 10:00; 3 had a failure'
    assert 'tests/a.py::t1' in t1     # most failures first
    assert '3 runs' in t1 and 'first 2026-10-01 10:00' in t1 and 'last 2026-10-03 10:00' in t1
    assert 'boom three' in t1
    assert 'tests/b.py' in b and '(ImportError: x)' in b
    head, t1 = history('--full')
    assert head.startswith('3 runs recorded')
    assert 'tests/a.py::t1' in t1 and '2 runs' in t1
