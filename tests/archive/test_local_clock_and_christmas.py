"""The big clock shows the device's own time zone and Zulu moves to a small line under it; pink mode shows days until
Christmas in place of alerts. Runs the page's own localClock, zuluTime and christmasItem in node, with the zone
named so the result does not depend on the machine running the test."""
import json
import os
import re
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LA = 'America/Los_Angeles'


def run(call):
    html = open(os.path.join(ROOT, 'zulu-clock.html')).read()
    consts = [re.search(r'  const %s .*\n' % name, html).group(0) for name in ('pad', 'DAYS', 'MONS')]
    fns = [re.search(r'  function %s\(.*?\n  \}\n' % name, html, re.S).group(0)
           for name in ('zoneParts', 'localClock', 'zuluTime', 'daysUntilChristmas', 'christmasItem')]
    script = ''.join(consts + fns) + 'console.log(JSON.stringify(%s))' % call
    return json.loads(subprocess.run(['node', '-e', script], capture_output=True, text=True, check=True).stdout)


def test_the_big_clock_reads_the_device_zone_in_24_hours():
    assert run("localClock(new Date('2026-10-29T15:59:12Z'), %r)" % LA) == \
        {'time': '08:59:12', 'date': 'THU   29 OCT 2026   PDT'}


def test_the_big_clock_follows_daylight_saving_and_midnight():
    assert run("localClock(new Date('2026-12-01T20:00:00Z'), %r)" % LA) == \
        {'time': '12:00:00', 'date': 'TUE   01 DEC 2026   PST'}
    assert run("localClock(new Date('2026-10-30T07:00:05Z'), %r).time" % LA) == '00:00:05'


def test_zulu_is_still_shown_in_utc():
    assert run("zuluTime(new Date('2026-10-29T15:59:12Z'))") == '15:59:12Z'


def test_days_until_christmas_count_whole_local_days():
    assert run("daysUntilChristmas(new Date('2026-10-29T16:00:00Z'), %r)" % LA) == 57
    assert run("daysUntilChristmas(new Date('2026-12-25T05:00:00Z'), %r)" % LA) == 1   # still Dec 24 in LA
    assert run("daysUntilChristmas(new Date('2026-12-25T20:00:00Z'), %r)" % LA) == 0
    assert run("daysUntilChristmas(new Date('2026-12-26T20:00:00Z'), %r)" % LA) == 364


def test_the_christmas_card_reads_as_a_countdown():
    assert run("christmasItem(new Date('2026-10-29T16:00:00Z'), %r)" % LA) == \
        {'cat': 'DAYS UNTIL CHRISTMAS', 'headline': '57 DAYS', 'detail': 'FRI   25 DEC 2026'}
    assert run("christmasItem(new Date('2026-12-24T20:00:00Z'), %r).headline" % LA) == '1 DAY'
    assert run("christmasItem(new Date('2026-12-25T20:00:00Z'), %r)" % LA) == \
        {'cat': 'DAYS UNTIL CHRISTMAS', 'headline': 'CHRISTMAS DAY', 'detail': 'FRI   25 DEC 2026'}
