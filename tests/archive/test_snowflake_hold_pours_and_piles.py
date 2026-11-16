"""Holding the snowflake on pink mode's Christmas card keeps the snow pouring out until it is let go, and the poured
snow collects on the top edges of the cards (`.tz-card`, `.wx-card`): it lands, builds a mound that slumps to a slope
instead of a spike, tops out, and melts away slowly. The pure parts (a flake, a mound) run in node; the hold and the
piles run in the real page in the headless shell."""
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../suite'))  # noqa
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # noqa

from browser_page import browser, open_page  # noqa: F401  (browser is the fixture)
from node_js import run_node
from page_js import pick

PURE = pick('snowFlurryRng', 'snowFlurryBetween', 'snowFlurryFlake', 'snowPileAdd')


def node(expr):
    return run_node(PURE + 'console.log(JSON.stringify(%s))' % expr)


def test_a_flake_is_dealt_the_same_from_the_same_rng_state():
    two = '(() => { const r = snowFlurryRng(5); return [snowFlurryFlake(r, 100, 50), snowFlurryFlake(r, 100, 50)]; })()'
    a, b = node(two), node(two)
    assert a == b and a[0] != a[1]
    f = a[0]
    assert 1.2 <= f['r'] <= 3.2 and 2.2 <= f['life'] <= 3.8 and 0.35 <= f['alpha'] <= 0.75


def test_a_mound_slumps_to_a_slope_tops_out_and_spills_off_the_ends():
    h = node('(() => { let h = new Array(41).fill(0); for (let n = 0; n < 400; n++) h = snowPileAdd(h, 20, 1, 1.5, 10);'
             ' return h; })()')
    assert max(h) == 10                                          # tops out at the cap
    assert all(abs(h[i] - h[i + 1]) <= 1.5 + 1e-6 for i in range(40)), h   # no spikes: every step is a slope
    assert h[19] > 5 and h[21] > 5 and h[16] > 0                # it spread to its neighbours
    e = node('(() => { let h = new Array(20).fill(0); for (let n = 0; n < 100; n++) h = snowPileAdd(h, 0, 1, 1.5, 10);'
             ' return h; })()')
    assert e[0] <= 1.5 * 1.5 + 1e-6, e                           # a ledge's end holds little: the rest spills off


# One snapshot of the snow canvas: total opacity, and how many bright pixels (poured snow, brighter than the ambient)
# there are, with how many of those sit in a strip just above the top of a card.
LOOK = """() => {
  const c = document.getElementById('snow');
  const g = c.getContext('2d').getImageData(0, 0, c.width, c.height).data;
  const tops = [...document.querySelectorAll('.tz-card, .wx-card')].map(e => e.getBoundingClientRect())
    .filter(r => r.width > 0);
  let ink = 0, bright = 0, onEdges = 0;
  for (let y = 0; y < c.height; y++) for (let x = 0; x < c.width; x++) {
    const a = g[(y * c.width + x) * 4 + 3];
    ink += a;
    if (a > 200) {
      bright++;
      if (tops.some(r => x >= r.left - 2 && x <= r.right + 2 && y >= r.top - 16 && y <= r.top + 1)) onEdges++;
    }
  }
  return { ink, bright, onEdges, pouring: c.dataset.pouring || null };
}"""


def ready(page):
    """The pink page with its loading screen gone (with no outside sources it waits 20 s, and covers the snowflake)."""
    page.wait_for_selector('#sa-item .sa-symbol svg')
    page.evaluate("() => document.getElementById('loader') && document.getElementById('loader').remove()")
    page.wait_for_timeout(500)


def hold_snowflake(page):
    box = page.locator('#sa-item .sa-symbol').bounding_box()
    page.mouse.move(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2)
    page.mouse.down()


def test_holding_keeps_the_snow_pouring_until_let_go(browser):
    page = open_page(browser, 1512, 982, 'mode=pink')
    ready(page)
    before = page.evaluate(LOOK)['ink']
    hold_snowflake(page)
    page.wait_for_timeout(6500)              # a plain click's flurry is over by about 5 s
    held = page.evaluate(LOOK)
    page.mouse.up()
    page.wait_for_timeout(100)
    let_go = page.evaluate(LOOK)
    page.close()
    assert held['pouring'] == '1'
    assert held['ink'] > before * 1.4, (before, held['ink'])
    assert let_go['pouring'] is None


def test_poured_snow_collects_on_the_edges_of_the_cards_and_stays(browser):
    page = open_page(browser, 1512, 982, 'mode=pink')
    ready(page)
    hold_snowflake(page)
    page.wait_for_timeout(6000)
    page.mouse.up()
    page.wait_for_timeout(6500)              # everything in the air has landed or gone
    piled = page.evaluate(LOOK)
    page.wait_for_timeout(3000)
    later = page.evaluate(LOOK)
    page.close()
    assert piled['bright'] > 400, piled      # a real pile
    assert piled['onEdges'] >= piled['bright'] * 0.9, piled   # on the cards' top edges, not floating
    assert later['bright'] > piled['bright'] * 0.6, (piled, later)   # and it stays: it melts slowly


def test_a_plain_click_leaves_far_less_snow_than_a_hold(browser):
    page = open_page(browser, 1512, 982, 'mode=pink')
    ready(page)
    page.click('#sa-item .sa-symbol')
    page.wait_for_timeout(7000)
    click = page.evaluate(LOOK)
    page.close()
    page = open_page(browser, 1512, 982, 'mode=pink')
    ready(page)
    hold_snowflake(page)
    page.wait_for_timeout(6000)
    page.mouse.up()
    page.wait_for_timeout(6500)
    held = page.evaluate(LOOK)
    page.close()
    assert held['bright'] > click['bright'] * 1.3, (click, held)
