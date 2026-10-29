"""Text that arrives from a feed (news titles and links, alert headlines and details) is shown as text and never
becomes markup. Runs the page's own ticker and alert-card code in node with hostile feed text, and a stand-in
for the one page element the card is drawn into."""
import json
import re
import subprocess

from page_js import pick, source

HOSTILE = '<img src=x onerror=alert(1)>'
HALF = '&lt;img src=x onerror=alert(1)'            # a feed that encodes the tag and leaves it unclosed


def run(body, *names):
    script = pick(*names) + body
    return json.loads(subprocess.run(['node', '-e', script], capture_output=True, text=True, check=True).stdout)


def test_a_news_title_and_link_cannot_add_markup():
    out = run("console.log(JSON.stringify(buildNewsHTML([{tag:'W', cls:'c', title: %s, url: %s}])))"
              % (json.dumps(HOSTILE), json.dumps('https://x.example/" onmouseover="alert(1)')), 'esc?', 'buildNewsHTML')
    assert '<img' not in out
    assert 'onmouseover="' not in out


def test_a_news_link_is_only_kept_when_it_is_http_or_https():
    html = source()
    assert "url:   el.querySelector('link')?.textContent?.trim() || ''" not in html, 'a feed link is used as is'
    assert "httpOnly(" in re.search(r"  function parseRssXml\(.*?\n  \}\n", html, re.S).group(0)


def test_an_alert_headline_cannot_add_markup_in_the_ticker():
    alert = {'cat': 'WHO', 'headline': HOSTILE, 'detail': HALF}
    out = run("console.log(JSON.stringify(buildSaTickerHTML([%s])))" % json.dumps(alert), 'esc?', 'buildSaTickerHTML')
    assert '<img' not in out


def test_an_alert_card_shows_feed_text_as_text():
    alert = {'symbol': '◆', 'cat': HOSTILE, 'headline': HOSTILE, 'detail': HALF}
    body = ("const el = {innerHTML: ''}; const document = {getElementById: () => el};"
            "const isPink = () => false, requestAnimationFrame = () => {}, fitSaPanel = () => {};"
            "saRenderItem(%s); console.log(JSON.stringify(el.innerHTML))" % json.dumps(alert))
    out = run(body, 'esc?', 'saRenderItem')
    assert '<img' not in out
