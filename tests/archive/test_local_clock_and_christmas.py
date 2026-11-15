"""The big clock shows the device's own time zone and Zulu moves to a small line under it; pink mode shows days and hours
until Christmas in place of alerts. Runs the page's own localClock, zuluTime and christmasItem in node, with the zone
named so the result does not depend on the machine running the test."""
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../suite'))  # noqa

from page_js import pick
from node_js import run_node

LA = 'America/Los_Angeles'


def run(call):
    script = pick('pad', 'DAYS', 'MONS', 'zoneParts', 'localClock', 'zuluTime', 'untilChristmas', 'christmasItem') + 'console.log(JSON.stringify(%s))' % call
    return run_node(script)


def test_the_big_clock_reads_the_device_zone_in_24_hours():
    assert run("localClock(new Date('2026-10-29T15:59:12Z'), %r)" % LA) == \
        {'time': '08:59:12', 'date': 'THU   29 OCT 2026   PDT'}


def test_the_big_clock_follows_daylight_saving_and_midnight():
    assert run("localClock(new Date('2026-12-01T20:00:00Z'), %r)" % LA) == \
        {'time': '12:00:00', 'date': 'TUE   01 DEC 2026   PST'}
    assert run("localClock(new Date('2026-10-30T07:00:05Z'), %r).time" % LA) == '00:00:05'


def test_zulu_is_still_shown_in_utc():
    assert run("zuluTime(new Date('2026-10-29T15:59:12Z'))") == '15:59:12Z'


def test_christmas_counts_down_in_days_and_whole_hours_to_local_midnight():
    # Oct 29 09:00 PDT to Dec 25 00:00 PST: the clocks go back on Nov 1, so the real gap is 56 days 16 hours
    assert run("untilChristmas(new Date('2026-10-29T16:00:00Z'), %r)" % LA) == {'days': 56, 'hours': 16, 'year': 2026}
    assert run("untilChristmas(new Date('2026-12-25T05:00:00Z'), %r)" % LA) == {'days': 0, 'hours': 3, 'year': 2026}
    assert run("untilChristmas(new Date('2026-12-24T08:00:00Z'), %r)" % LA) == {'days': 1, 'hours': 0, 'year': 2026}
    assert run("untilChristmas(new Date('2026-12-25T07:30:00Z'), %r)" % LA) == {'days': 0, 'hours': 0, 'year': 2026}


def test_christmas_day_and_the_day_after():
    assert run("untilChristmas(new Date('2026-12-25T08:00:00Z'), %r).today" % LA) is True   # 00:00 on the day
    assert run("untilChristmas(new Date('2026-12-25T20:00:00Z'), %r).today" % LA) is True
    assert run("untilChristmas(new Date('2026-12-26T20:00:00Z'), %r)" % LA) == {'days': 363, 'hours': 12, 'year': 2027}


def test_the_christmas_card_reads_as_a_countdown_that_changes_every_hour():
    assert run("christmasItem(new Date('2026-10-29T16:00:00Z'), %r)" % LA) == \
        {'cat': 'TIME UNTIL CHRISTMAS', 'headline': '56 DAYS 16 HOURS', 'detail': 'FRI   25 DEC 2026'}
    assert run("christmasItem(new Date('2026-10-29T17:00:00Z'), %r).headline" % LA) == '56 DAYS 15 HOURS'
    assert run("christmasItem(new Date('2026-12-24T07:00:00Z'), %r).headline" % LA) == '1 DAY 1 HOUR'
    assert run("christmasItem(new Date('2026-12-24T08:00:00Z'), %r).headline" % LA) == '1 DAY 0 HOURS'
    assert run("christmasItem(new Date('2026-12-24T20:00:00Z'), %r).headline" % LA) == '12 HOURS'
    assert run("christmasItem(new Date('2026-12-25T05:00:00Z'), %r).headline" % LA) == '3 HOURS'
    assert run("christmasItem(new Date('2026-12-25T07:30:00Z'), %r).headline" % LA) == 'LESS THAN 1 HOUR'
    assert run("christmasItem(new Date('2026-12-25T20:00:00Z'), %r)" % LA) == \
        {'cat': 'TIME UNTIL CHRISTMAS', 'headline': 'CHRISTMAS DAY', 'detail': 'FRI   25 DEC 2026'}
    assert run("christmasItem(new Date('2026-12-26T20:00:00Z'), %r).detail" % LA) == 'SAT   25 DEC 2027'
