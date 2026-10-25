import os as _os
import subprocess as _subprocess
import time as _time

# ── the run record ─────────────────────────────────────────────────────────────────────────
# Each run appends one line to `test-runs.jsonl` (untracked), in the repo's main folder so that
# every worktree writes to the same file: when, which commit, a short hash of the uncommitted
# code (new untracked files included), how it was started, whether it was the whole suite, and every test that failed with the
# first line of why. A test file that will not load counts as a failure. `tools/failure_history.py`
# reads it back. Model: djitel's tests/conftest.py.
_HERE = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
_RUN_SEEN = {'tests': 0, 'failed': set(), 'why': {}}


def _git(*a):
    r = _subprocess.run(['git', '-C', _HERE, *a], capture_output=True, text=True, timeout=10)
    return r.stdout.strip() if r.returncode == 0 else ''


def _main_folder():
    common = _git('rev-parse', '--path-format=absolute', '--git-common-dir')
    return _os.path.dirname(common) if common else _HERE


def _first_line_of_why(report):
    crash = getattr(report.longrepr, 'reprcrash', None)
    if crash is not None and crash.message:
        return crash.message.strip().splitlines()[0]
    text = str(report.longrepr)
    marked = [ln[1:].strip() for ln in text.splitlines() if ln.startswith('E ')]
    rest = [ln.strip() for ln in text.splitlines() if ln.strip()]
    return (marked or rest or [''])[-1 if marked else 0]


def _seen_failing(report):
    _RUN_SEEN['failed'].add(report.nodeid)
    _RUN_SEEN['why'].setdefault(report.nodeid, _first_line_of_why(report))


def pytest_runtest_logreport(report):
    if _os.environ.get('PYTEST_XDIST_WORKER'):
        return
    if report.when == 'call':
        _RUN_SEEN['tests'] += 1
    if report.failed:
        _seen_failing(report)


def pytest_collectreport(report):
    if not _os.environ.get('PYTEST_XDIST_WORKER') and report.failed:
        _seen_failing(report)


def pytest_sessionfinish(session, exitstatus):
    _record_the_run(session, exitstatus)


def _record_the_run(session, exitstatus):
    if _os.environ.get('PYTEST_XDIST_WORKER'):
        return
    try:
        import hashlib as _hashlib
        import json as _json
        cfg = session.config
        here = _os.path.realpath(_HERE)
        whole = {here, _os.path.join(here, 'tests')}     # no path given: pytest uses testpaths
        given = [_os.path.realpath(_os.path.join(cfg.invocation_params.dir, a)) for a in cfg.args]
        full = (all(a in whole for a in given) and not cfg.getoption('keyword')
                and not cfg.getoption('markexpr') and not cfg.getoption('lf', False))
        diff = _subprocess.run(['git', '-C', _HERE, 'diff', 'HEAD'], capture_output=True, timeout=10).stdout
        new = _git('ls-files', '--others', '--exclude-standard').splitlines()     # git diff leaves these out
        for name in new:
            diff += b'\0' + name.encode() + b'\0'
            try:
                with open(_os.path.join(_HERE, name), 'rb') as f:
                    diff += f.read()
            except OSError:
                pass     # a file that cannot be read counts by its name only
        failed = sorted(_RUN_SEEN['failed'])
        row = {'when': _time.strftime('%Y-%m-%dT%H:%M:%S%z'), 'commit': _git('rev-parse', '--short', 'HEAD'),
               'dirty': bool(diff), 'diff': _hashlib.sha1(diff).hexdigest()[:10] if diff else '',
               'full': full, 'args': list(cfg.invocation_params.args), 'tests': _RUN_SEEN['tests'],
               'exit': int(exitstatus), 'failed': failed,
               'failed_files': sorted({n.split('::')[0] for n in failed}),
               'why': {n: _RUN_SEEN['why'][n] for n in failed}}
        with open(_os.path.join(_main_folder(), 'test-runs.jsonl'), 'a', encoding='utf-8') as f:
            f.write(_json.dumps(row) + '\n')
    except Exception:
        pass     # a record that cannot be written must never fail a run
