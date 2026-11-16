"""Clicking the Christmas countdown in pink mode swaps its two numbers: `39 DAYS 7 HOURS` becomes `7 HOURS 39 DAYS`, and
the next click puts them back. The pure part (christmasItem's third argument) runs in node; the click runs in the real
page in the headless shell. A countdown with only hours (or Christmas day itself) has nothing to swap."""
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../suite'))  # noqa
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # noqa

import re

from browser_page import browser, open_page  # noqa: F401  (browser is the fixture)
from node_js import run_node
from page_js import pick

LA = 'America/Los_Angeles'


def headline(when, hours_first):
    call = 'christmasItem(new Date(%r), %r, %s).headline' % (when, LA, str(hours_first).lower())
    return run_node(pick('pad', 'DAYS', 'MONS', 'zoneParts', 'untilChristmas', 'christmasItem')
                    + 'console.log(JSON.stringify(%s))' % call)


def test_hours_first_puts_the_hours_before_the_days():
    assert headline('2026-10-29T16:00:00Z', False) == '56 DAYS 16 HOURS'
    assert headline('2026-10-29T16:00:00Z', True) == '16 HOURS 56 DAYS'
    assert headline('2026-12-24T07:00:00Z', True) == '1 HOUR 1 DAY'
    assert headline('2026-12-24T08:00:00Z', True) == '0 HOURS 1 DAY'


def test_nothing_to_swap_without_days():
    assert headline('2026-12-24T20:00:00Z', True) == '12 HOURS'
    assert headline('2026-12-25T07:30:00Z', True) == 'LESS THAN 1 HOUR'
    assert headline('2026-12-25T20:00:00Z', True) == 'CHRISTMAS DAY'


def test_clicking_the_countdown_swaps_the_order_each_time(browser):
    page = open_page(browser, 1512, 982, 'mode=pink')
    page.wait_for_selector('#sa-item .sa-headline')

    def read():
        return page.inner_text('#sa-item .sa-headline').strip()

    first = read()
    m = re.fullmatch(r'(\d+) DAYS? (\d+) HOURS?', first)
    assert m, first
    page.click('#sa-item .sa-headline')   # the snowflake above it starts a flurry instead
    assert re.fullmatch(r'%s HOURS? %s DAYS?' % (m.group(2), m.group(1)), read()), read()
    page.click('#sa-item .sa-headline')
    assert read() == first
    page.close()
