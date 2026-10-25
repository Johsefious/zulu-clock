"""Which tests have failed in recorded runs: `python3 tools/failure_history.py [--full]`.

Reads test-runs.jsonl in the repo's main folder, which tests/conftest.py appends to after every
pytest run. `--full` counts only runs of the whole suite. Model: djitel's tools/failure_history.py.
"""
import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

here = Path(__file__).resolve().parent.parent
common = subprocess.run(['git', '-C', str(here), 'rev-parse', '--path-format=absolute', '--git-common-dir'],
                        capture_output=True, text=True).stdout.strip()
log = (Path(common).parent if common else here) / 'test-runs.jsonl'
if not log.exists():
    sys.exit('No runs recorded yet: test-runs.jsonl appears after the next pytest run.')
runs = [json.loads(line) for line in log.read_text(encoding='utf-8').splitlines() if line.strip()]
if '--full' in sys.argv:
    runs = [r for r in runs if r['full']]
if not runs:
    sys.exit('No matching runs recorded.')
tests = defaultdict(list)
why = {}
for r in runs:
    for t in r['failed']:
        tests[t].append(r['when'][:16].replace('T', ' '))
        why[t] = r.get('why', {}).get(t, why.get(t, ''))
print(f"{len(runs)} runs recorded, {runs[0]['when'][:16].replace('T', ' ')} to {runs[-1]['when'][:16].replace('T', ' ')}; "
      f"{sum(1 for r in runs if r['failed'])} had a failure")
for t, whens in sorted(tests.items(), key=lambda kv: -len(kv[1])):
    print(f"{len(whens):4d} runs  first {whens[0]}  last {whens[-1]}  {t}" + (f"  ({why[t]})" if why[t] else ''))
