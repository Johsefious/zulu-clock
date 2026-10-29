"""The big time's last digit ticks evenly. The main once-a-second work is scheduled from the current milliseconds, so
a late timer never holds a second or skips one. Runs the page's own onTheSecond in node with a fake clock whose timers
fire late by varying amounts."""
import json
import subprocess

from page_js import pick, source

HARNESS = """
let now = 1761754800123, timers = [], n = 0, lates = [0, 40, 250, 90, 600, 5, 400, 180, 30, 700];
Date.now = () => now;
globalThis.setTimeout = (fn, ms) => { timers.push({ at: now + ms, fn, late: lates[n++ % lates.length] }); };
const shown = [];
const work = () => shown.push(Math.floor(now / 1000));
%s
onTheSecond(work);
for (let i = 0; i < 300 && timers.length; i++) {
  timers.sort((a, b) => a.at - b.at);
  const t = timers.shift();
  now = Math.max(now, t.at + t.late);
  t.fn();
}
console.log(JSON.stringify(shown));
"""


def test_a_late_timer_never_holds_or_skips_a_second():
    script = HARNESS.replace('%s', pick('onTheSecond'))
    shown = json.loads(subprocess.run(['node', '-e', script], capture_output=True, text=True, check=True).stdout)
    assert len(shown) > 100
    assert [b - a for a, b in zip(shown, shown[1:])] == [1] * (len(shown) - 1)


def test_the_page_starts_its_once_a_second_work_through_it():
    js = source()
    assert 'setInterval(() => { tick(); if (pressData) pressRender(); }, 1000)' not in js
    assert 'onTheSecond(() => { tick(); if (pressData) pressRender(); })' in js
