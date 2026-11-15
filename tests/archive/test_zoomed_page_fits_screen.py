"""Zooming the browser in (cmd + =) shrinks the page's CSS viewport; the whole clock, ticker included, must still fit
the window. Before the fix the sections kept their size, the shell overflowed its height and the bottom of the page
(the scrolling headlines) was cut off. Loads the real page in the headless shell at the CSS sizes a 100%, 125%, 150%,
175% and 200% zoom of a 1512x982 window give, with every outside call refused, and measures where each part ends."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # noqa

import pytest

from browser_page import answer, browser, open_page  # noqa: F401  (browser is the fixture)

SIZES = [(1512, 982), (1210, 786), (1008, 655), (864, 561), (756, 491)]   # 100, 125, 150, 175, 200 % of 1512x982

# Press and Missions as the real apps send them: four cards each, the tallest a card can be.
STORY = {'id': 1, 'short_name': 'Pigs', 'doc': 'pa', 'overdue': 1, 'today': 1, 'upcoming': 2, 'progress': [3, 9],
         'next': {'text': 'Send the advisory', 'state': 'late'}, 'archived': False, 'old_builder': False,
         'countdown_to': '2099-01-01T00:00:00Z'}
PRESS = {'stories': [dict(STORY, id=i) for i in range(1, 5)], 'totals': {'overdue': 4, 'today': 4, 'messages': 2}}
MISSION = {'label': 'Farm visit', 'types': ['drone'], 'days_out': 1, 'members': ['Ann Lee', 'Bo Kim'],
           'confirmed': True, 'briefingSent': False, 'approved': False, 'gate_warning': True, 'planReceived': None,
           'planDue': '2099-01-01T00:00:00Z', 'facilities': ['Acme Farms'], 'cancelled': False}
MISSIONS = {'missions': [dict(MISSION, label=f'Farm {i}') for i in range(4)]}


MEASURE = """() => {
  const box = s => document.querySelector(s).getBoundingClientRect();
  return { vh: innerHeight, vw: innerWidth, ticker: box('.ticker').bottom, missions: box('#missions').bottom,
           press: box('#press').bottom, wx: box('.wx-section').bottom, tz: box('#tz-row').bottom,
           shellRight: box('.shell').right };
}"""


@pytest.mark.parametrize('w,h', SIZES)
def test_every_part_of_the_clock_ends_inside_the_window(browser, w, h):
    page = open_page(browser, w, h, 'mode=green',
                     [('**/source/presser*', answer(PRESS)), ('**/missions', answer(MISSIONS))])
    page.wait_for_selector('#press .press-card')
    page.wait_for_selector('#missions .press-card')
    page.wait_for_timeout(300)
    m = page.evaluate(MEASURE)
    page.close()
    for part in ('tz', 'wx', 'press', 'missions', 'ticker'):
        assert m[part] <= m['vh'] + 1, f'{part} ends at {m[part]:.0f}px, the window is {m["vh"]}px tall'
    assert m['shellRight'] <= m['vw'] + 1, f'the page is {m["shellRight"]:.0f}px wide in a {m["vw"]}px window'
