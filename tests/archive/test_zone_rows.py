"""The zone rows read each zone's time through zoneParts (Intl parts), not by parsing a locale string in the device's
zone. Runs the page's own zoneRow in node with the machine's zone set to Tokyo, so a round-trip through the device's
zone would give a different answer."""
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../suite'))  # noqa
import os

from page_js import pick
from node_js import run_node


def run(call):
    script = pick('pad', 'DAYS', 'MONS', 'zoneParts', 'zoneRow') + 'console.log(JSON.stringify(%s))' % call
    env = dict(os.environ, TZ='Asia/Tokyo')
    return run_node(script, env=env)


def test_zone_row_format():
    row = run("zoneRow(new Date('2026-10-29T15:59:12Z'), 'America/Los_Angeles')")
    assert row == {'hm': '08:59 AM', 'meta': 'THU OCT 29'}


def test_zone_row_across_the_fall_back_hour():
    # 2026-11-01 08:30Z is 01:30 PDT; an hour later (09:30Z) is 01:30 PST. The same wall time twice.
    first = run("zoneRow(new Date('2026-11-01T08:30:00Z'), 'America/Los_Angeles')")
    second = run("zoneRow(new Date('2026-11-01T09:30:00Z'), 'America/Los_Angeles')")
    assert first == second == {'hm': '01:30 AM', 'meta': 'SUN NOV 01'}
    assert run("zoneRow(new Date('2026-11-01T10:30:00Z'), 'America/Los_Angeles')")['hm'] == '02:30 AM'


def test_zone_row_midnight_is_twelve_am():
    assert run("zoneRow(new Date('2026-10-29T07:05:00Z'), 'America/Los_Angeles')")['hm'] == '12:05 AM'
