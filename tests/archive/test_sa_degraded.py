"""The SA panel counts a source that failed (fetch rejected or HTTP error) as failed, so saDegraded can turn true and
launchWithRetry backs off; a source that answered with no alerts is not a failure. Runs the page's own fetchers in
node with fetchT stubbed."""
import json
import subprocess

from page_js import pick

FETCHERS = ['saFetchT', 'saFailed', 'saIsFailed', 'saIsDegraded', 'saFetchSpace', 'saFetchNwsAlerts']


def run(fetch_stub, call):
    script = ('const src = (n, q) => "/source/" + n;\n'
              'async function fetchT(url) { return (%s)(url); }\n' % fetch_stub
              + pick(*FETCHERS)
              + '(async () => console.log(JSON.stringify(await (%s))))();' % call)
    return json.loads(subprocess.run(['node', '-e', script], capture_output=True, text=True, check=True).stdout)


OK_QUIET = "u => ({ ok: true, status: 200, json: async () => [['t','kp'],['x','2']] })"
HTTP_500 = "u => ({ ok: false, status: 500, json: async () => ({ error: 'x' }) })"
REJECTS = "u => { throw new Error('offline'); }"


def failed(stub, fetcher='saFetchSpace'):
    return run(stub, "%s().then(r => ({ alerts: r.length, failed: saIsFailed({ status: 'fulfilled', value: r }) }))" % fetcher)


def test_a_source_that_answered_with_no_alerts_is_not_failed():
    assert failed(OK_QUIET) == {'alerts': 0, 'failed': False}


def test_a_source_answering_500_is_failed():
    assert failed(HTTP_500) == {'alerts': 0, 'failed': True}
    assert failed(HTTP_500, 'saFetchNwsAlerts') == {'alerts': 0, 'failed': True}


def test_a_source_whose_fetch_rejects_is_failed():
    assert failed(REJECTS) == {'alerts': 0, 'failed': True}


def test_degraded_when_more_than_half_failed_and_the_alert_list_is_unchanged():
    out = run(HTTP_500, """(async () => {
      const bad = await saFetchSpace(), good = [{ cat: 'X' }];
      const rs = n => Array.from({ length: 7 }, (_, i) => ({ status: 'fulfilled', value: i < n ? bad : good }));
      return { four: saIsDegraded(rs(4), 7), three: saIsDegraded(rs(3), 7),
               merged: rs(4).flatMap(r => r.value).length };
    })()""")
    assert out == {'four': True, 'three': False, 'merged': 3}
