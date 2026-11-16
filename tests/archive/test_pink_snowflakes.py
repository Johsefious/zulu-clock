"""Pink mode has faint snowflakes drifting down behind the clock: a canvas under the content that takes no clicks, with
some pixels drawn and the drawing moving. Green and blue show none. Loads the real page in the headless shell."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # noqa

from browser_page import browser, open_page  # noqa: F401  (browser is the fixture)

# One snapshot: how the canvas sits, and a fingerprint (count and total position) of the drawn pixels.
LOOK = """() => {
  const c = document.getElementById('snow');
  if (!c) return null;
  const cs = getComputedStyle(c), shell = getComputedStyle(document.querySelector('.shell'));
  const g = c.getContext('2d').getImageData(0, 0, c.width, c.height).data;
  let n = 0, sum = 0, peak = 0;
  for (let i = 3; i < g.length; i += 4) if (g[i]) { n++; sum += i; if (g[i] > peak) peak = g[i]; }
  return { display: cs.display, pointer: cs.pointerEvents, z: +cs.zIndex, shellZ: +shell.zIndex, n, sum, peak };
}"""


def test_pink_mode_drifts_faint_snow_behind_the_content(browser):
    page = open_page(browser, 1512, 982, 'mode=pink')
    page.wait_for_timeout(1500)
    a = page.evaluate(LOOK)
    page.wait_for_timeout(1000)
    b = page.evaluate(LOOK)
    page.close()
    assert a and a['display'] != 'none'
    assert a['pointer'] == 'none'
    assert a['z'] < a['shellZ']
    assert a['n'] > 50                         # flakes are drawn
    assert a['peak'] < 140                     # and faint: nothing near full opacity
    assert (a['n'], a['sum']) != (b['n'], b['sum'])   # and they move


def test_green_and_blue_show_no_snow(browser):
    for mode in ('green', 'blue'):
        page = open_page(browser, 1512, 982, f'mode={mode}')
        page.wait_for_timeout(1000)
        look = page.evaluate(LOOK)
        page.close()
        assert look is None or look['display'] == 'none' or look['n'] == 0, mode
