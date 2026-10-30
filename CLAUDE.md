# Zulu Clock: working rules

## Start here
Read `docs/code-map.md` first, then `docs/handoff.md` and follow its instructions.

## Commands
- Run the tests: `.venv/bin/python -m pytest -q`
- Run an archived test: `.venv/bin/python -m pytest tests/archive/<file>.py -q`
- Which tests have failed: `testruns last --full` (see `testruns --help`)
- Start the clock: `./launch.sh`
- Get a port for a test server: `port take`

## Pointers
- `README.md`: what it is, how to run it, status.
- `docs/decisions.md`: why each choice was made.
- `docs/code-map.md`: layout, data flow, endpoints, tests.
- `docs/handoff.md` is git-ignored.

## Repo rules
None yet.

## Learned the hard way
- Every status indicator on the clock points to an actual measurement.
