"""Clicking the snowflake on pink mode's Christmas card starts a flurry for a few seconds, drawn on the snow canvas.
It is never the same one twice: the wind is dealt from a seed that is the time times the moon's percent lit (plus one,
so a new moon still varies), negative when the moon is waning. The pure parts (the seed, the plan of flakes and swirls,
the wind) run in node; the click runs in the real page in the headless shell."""
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../suite'))  # noqa
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # noqa

from browser_page import browser, open_page  # noqa: F401  (browser is the fixture)
from node_js import run_node
from page_js import pick

PURE = pick('snowFlurrySeed', 'snowFlurryRng', 'snowFlurryPlan', 'snowFlurryWind')


def node(expr):
    return run_node(PURE + 'console.log(JSON.stringify(%s))' % expr)


def test_seed_is_time_times_moon_percent_signed_by_waxing():
    assert node('snowFlurrySeed(1000, 50, true)') == 51000
    assert node('snowFlurrySeed(1000, 50, false)') == -51000
    # a new moon (0 % lit) does not collapse every flurry to one seed
    assert node('snowFlurrySeed(1000, 0, true)') != node('snowFlurrySeed(2000, 0, true)')


def test_same_seed_same_flurry_different_seed_different_flurry():
    a = node('snowFlurryPlan(12345, 1512, 982, 1300, 120)')
    assert a == node('snowFlurryPlan(12345, 1512, 982, 1300, 120)')
    assert a != node('snowFlurryPlan(12346, 1512, 982, 1300, 120)')
    assert a['swirls'] != node('snowFlurryPlan(-12345, 1512, 982, 1300, 120)')['swirls']


def test_a_flurry_is_neither_a_sprinkle_nor_a_blizzard():
    for seed in range(1, 40):
        p = node('snowFlurryPlan(%d, 1512, 982, 1300, 120)' % (seed * 7919))
        assert 80 <= len(p['flakes']) <= 220, (seed, len(p['flakes']))
        assert 2 <= len(p['swirls']) <= 4
        ends = [f['delay'] + f['life'] for f in p['flakes']]
        assert 3 <= max(ends) <= 6.5, (seed, max(ends))          # over in a few seconds
        assert all(f['alpha'] <= 0.8 and 1 <= f['r'] <= 3.5 for f in p['flakes'])


def test_the_wind_swirls_and_changes_with_place_and_time():
    plan = 'snowFlurryPlan(777, 1512, 982, 1300, 120)'
    w = node('[snowFlurryWind(%s, 300, 300, 1), snowFlurryWind(%s, 900, 600, 1), snowFlurryWind(%s, 300, 300, 3)]'
             % (plan, plan, plan))
    flat = [v for pair in w for v in pair]
    assert all(isinstance(v, (int, float)) and abs(v) < 400 for v in flat)
    assert w[0] != w[1] and w[0] != w[2]


# One snapshot of the snow canvas: the total opacity of what is drawn.
INK = """() => {
  const c = document.getElementById('snow');
  const g = c.getContext('2d').getImageData(0, 0, c.width, c.height).data;
  let a = 0;
  for (let i = 3; i < g.length; i += 4) a += g[i];
  return a;
}"""


def ink(page, ms):
    page.wait_for_timeout(ms)
    return page.evaluate(INK)


def test_clicking_the_snowflake_starts_a_flurry_that_passes(browser):
    page = open_page(browser, 1512, 982, 'mode=pink')
    page.wait_for_selector('#sa-item .sa-symbol svg')
    before = max(ink(page, 400) for _ in range(3))
    first = page.inner_text('#sa-item .sa-headline').strip()
    page.click('#sa-item .sa-symbol')
    during = max(ink(page, 700), ink(page, 600))
    assert during > before * 1.4, (before, during)              # visibly more snow
    assert page.inner_text('#sa-item .sa-headline').strip() == first   # the click did not swap the countdown
    after = ink(page, 7000)
    assert after < before * 1.2, (before, after)                # a few seconds, then it has passed
    page.close()


def test_two_clicks_are_two_different_flurries(browser):
    page = open_page(browser, 1512, 982, 'mode=pink')
    page.wait_for_selector('#sa-item .sa-symbol svg')
    seeds = []
    for _ in range(2):
        page.click('#sa-item .sa-symbol')
        seeds.append(page.evaluate("() => +document.getElementById('snow').dataset.flurry"))
        page.wait_for_timeout(30)
    page.close()
    assert all(isinstance(s, (int, float)) for s in seeds) and seeds[0] != seeds[1], seeds


def test_no_flurry_for_reduced_motion_or_outside_pink(browser):
    page = open_page(browser, 1512, 982, 'mode=pink')
    page.wait_for_selector('#sa-item .sa-symbol svg')
    page.emulate_media(reduced_motion='reduce')
    before = ink(page, 300)
    page.click('#sa-item .sa-symbol')
    assert ink(page, 800) <= before * 1.2
    page.close()
    page = open_page(browser, 1512, 982, 'mode=green')
    page.wait_for_timeout(500)
    page.click('#sa-item .sa-symbol')
    assert ink(page, 800) == 0
    page.close()
