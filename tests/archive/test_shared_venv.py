"""Archive test: zulu-clock's tests run on the shared test venv, app-dev's .venv, not a venv of its own."""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_command_runs_the_shared_venv_python():
    with open(os.path.join(ROOT, "app.json"), encoding="utf-8") as f:
        command = json.load(f)["tests"]["command"]
    assert command.startswith('"$(repo path app-dev)/.venv/bin/python" -m pytest'), command
