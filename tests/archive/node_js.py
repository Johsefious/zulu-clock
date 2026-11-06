"""Runs a node script built from the page's own code (page_js.pick) and reads back the JSON it prints.

One runner for every archive test that runs the page's script in node.
"""
import json
import subprocess


def run_node(script, env=None):
    return json.loads(subprocess.run(['node', '-e', script], capture_output=True, text=True, check=True,
                                     env=env).stdout)
