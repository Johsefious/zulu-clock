"""fetchT is the one fetch every loader uses and it throws `HTTP <status>` on a non-ok answer, so an HTTP 502 from
server.py is never parsed as data. Runs the page's own fetchT, fetchMetar and fetchFeed in node with fetch stubbed."""
import json
import subprocess

from page_js import pick, source

BAD = "async () => ({ ok: false, status: 502, json: async () => [{ icaoId: 'KSFO' }], text: async () => '<rss/>' })"
GOOD = "async () => ({ ok: true, status: 200, json: async () => [{ icaoId: 'KSFO' }], text: async () => '<rss/>' })"


def run(fetch_stub, names, call):
    script = ('const src = (n, q) => "/source/" + n;\n'
              'const WX_LOCS = [{ metar: "KSFO" }];\n'
              'const fetch = %s;\n' % fetch_stub
              + pick(*names)
              + '(async () => { try { console.log(JSON.stringify(await (%s))); }'
                ' catch (e) { console.log(JSON.stringify({ threw: e.message })); } })();' % call)
    return json.loads(subprocess.run(['node', '-e', script], capture_output=True, text=True, check=True).stdout)


def test_fetcht_throws_http_status_on_a_bad_answer():
    assert run(BAD, ['fetchT'], "fetchT('/x')") == {'threw': 'HTTP 502'}


def test_fetcht_returns_a_good_answer():
    assert run(GOOD, ['fetchT'], "fetchT('/x').then(r => r.status)") == 200


def test_metar_treats_a_502_as_no_data():
    assert run(BAD, ['fetchT', 'fetchMetar'], 'fetchMetar()') == {}
    assert run(GOOD, ['fetchT', 'fetchMetar'], 'fetchMetar()') == {'KSFO': {'icaoId': 'KSFO'}}


def test_a_news_feed_answering_502_is_rejected_with_the_status():
    feed = "({ source: 'x', query: '' })"
    assert run(BAD, ['fetchT', 'fetchFeed'], 'fetchFeed(%s)' % feed) == {'threw': 'HTTP 502'}


def test_no_loader_keeps_its_own_status_check():
    js = source()
    assert 'saFetchT' not in js
    assert "if (!r.ok) throw new Error('HTTP ' + r.status);" not in js.split('async function loadPress')[0]
