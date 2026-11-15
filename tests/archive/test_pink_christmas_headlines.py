"""In pink mode every other headline in the ticker is about Christmas: the 30 news headlines (10 each from World, US and
CA) alternate with 30 Christmas ones, 60 in all. Green and blue show the news alone and never ask for the Christmas
feed. Not fail-first: the green ticker test guards behaviour that already worked, so it passed before the change.
Runs the page's own withChristmas in node, then the whole ticker in the headless shell with the feeds faked."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # noqa
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../suite'))  # noqa

from browser_page import answer, browser, open_page  # noqa: F401  (browser is the fixture)
from node_js import run_node
from page_js import pick


def with_christmas(news, xmas):
    return run_node(pick('withChristmas') + 'console.log(JSON.stringify(withChristmas(%s, %s)))' % (news, xmas))


def test_christmas_headlines_alternate_with_the_news():
    assert with_christmas("['n1','n2','n3']", "['x1','x2','x3']") == ['n1', 'x1', 'n2', 'x2', 'n3', 'x3']


def test_the_longer_list_carries_on_alone_when_the_other_runs_out():
    assert with_christmas("['n1','n2','n3']", "['x1']") == ['n1', 'x1', 'n2', 'n3']
    assert with_christmas("['n1']", "['x1','x2','x3']") == ['n1', 'x1', 'x2', 'x3']


def test_no_christmas_headlines_leaves_the_news_as_it_was():
    assert with_christmas("['n1','n2']", '[]') == ['n1', 'n2']


def rss(prefix, n):
    items = ''.join(f'<item><title>{prefix} {i} - Source</title><link>https://example.com/{prefix}{i}</link></item>'
                    for i in range(n))
    return f'<?xml version="1.0"?><rss><channel>{items}</channel></rss>'


def feeds(asked):
    """The three news feeds send 12 items each (the page keeps 10), the Christmas feed 40 (the page keeps 30)."""
    def handler(route):
        asked.append(route.request.url)
        name = route.request.url.split('/source/')[1].split('?')[0]
        body = rss('XMAS', 40) if name == 'news-xmas' else rss(name.upper(), 12)
        answer(body, 'application/rss+xml')(route)
    return [('**/source/news-*', handler)]


TICKER = """() => [...document.querySelectorAll('#ticker-inner .ntag')]
  .map(e => e.textContent).filter(t => ['[WORLD]', '[US]', '[CA]', '[XMAS]'].includes(t))"""


def ticker_tags(browser, query, press_m=False):
    asked = []
    page = open_page(browser, 1512, 982, query, feeds(asked))
    page.wait_for_function('() => /^\\d+ HEADLINES/.test(document.getElementById("feed-status").textContent)')
    if press_m:
        page.keyboard.press('m')
        page.wait_for_timeout(1500)
    tags = page.evaluate(TICKER)
    page.close()
    return tags, asked


def test_pink_ticker_has_sixty_headlines_every_other_one_about_christmas(browser):
    tags, _ = ticker_tags(browser, 'mode=pink')
    assert len(tags) == 60
    assert tags[1::2] == ['[XMAS]'] * 30
    assert tags[0::2] == ['[WORLD]'] * 10 + ['[US]'] * 10 + ['[CA]'] * 10


def test_green_ticker_has_the_thirty_news_headlines_and_never_asks_for_christmas(browser):
    tags, asked = ticker_tags(browser, 'mode=green')
    assert tags == ['[WORLD]'] * 10 + ['[US]'] * 10 + ['[CA]'] * 10
    assert not [u for u in asked if 'news-xmas' in u]


def test_switching_to_pink_brings_the_christmas_headlines_in(browser):
    tags, asked = ticker_tags(browser, 'mode=green', press_m=True)   # M: green to pink
    assert len(tags) == 60 and tags[1::2] == ['[XMAS]'] * 30
    assert [u for u in asked if 'news-xmas' in u]
