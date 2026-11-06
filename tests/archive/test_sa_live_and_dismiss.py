"""The SA panel shows what the sources report now (no 48-hour store), and a double-click on an alert hides it until the
page is reloaded. The dismissed list lives in the page's memory only, so nothing is stored and no endpoint is involved.
Runs the page's own functions in node with the panel's other pieces stubbed."""
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../suite'))  # noqa
import json
import re

from page_js import pick, source
from node_js import run_node

FUNCS = ['saDeduplicateStorms', 'saKey', 'saBuild', 'saDismissCurrent']

NHC = {'cat': 'TROPICAL', 'headline': 'MILTON · CAT 3 HURRICANE', 'detail': '100KT', 'sev': 4}
EONET_DUP = {'cat': 'SEVERE STORMS', 'headline': 'TROPICAL STORM MILTON', 'detail': 'EONET', 'sev': 2}
QUAKE = {'cat': 'SEISMIC', 'headline': 'M4.1 · NEAR RIDGECREST', 'detail': '2HR AGO', 'sev': 1}
HEAT = {'cat': 'CA ALERT', 'headline': 'EXCESSIVE HEAT WARNING', 'detail': 'FRESNO', 'sev': 3}


def run(body, pink='false'):
    script = ('let saDismissed = new Set(), saAlerts = [], saIdx = 0, saLastFresh = [];\n'
              'const calls = [];\n'
              'const isPink = () => %s;\n'
              'function saStartCycle() { calls.push("cycle"); }\n'
              'function rebuildTicker() { calls.push("ticker"); }\n' % pink
              + pick(*FUNCS)
              + '(() => { %s })();' % body)
    return run_node(script)


def test_the_panel_lists_only_what_the_sources_report_now_sorted_by_severity():
    out = run('console.log(JSON.stringify(saBuild([%s, %s]).map(a => a.cat)));' % (json.dumps(QUAKE), json.dumps(HEAT)))
    assert out == ['CA ALERT', 'SEISMIC']


def test_the_page_keeps_no_48_hour_store():
    js = source()
    assert 'zc_sa_v1' not in js
    assert not re.search(r'SA_PERSIST_MS|saLoadStored|saMerge', js)


def test_a_double_click_hides_the_alert_on_screen_and_the_next_one_comes_up():
    out = run("""
      saLastFresh = [%s, %s];
      saAlerts = saBuild(saLastFresh); saIdx = 0;
      saDismissCurrent();
      console.log(JSON.stringify({ shown: saAlerts.map(a => a.cat), idx: saIdx, calls }));
    """ % (json.dumps(HEAT), json.dumps(QUAKE)))
    assert out == {'shown': ['SEISMIC'], 'idx': 0, 'calls': ['cycle', 'ticker']}


def test_a_dismissed_alert_stays_hidden_on_the_next_refresh():
    out = run("""
      saLastFresh = [%s, %s];
      saAlerts = saBuild(saLastFresh); saIdx = 0;
      saDismissCurrent();
      console.log(JSON.stringify(saBuild([%s, %s]).map(a => a.cat)));
    """ % (json.dumps(HEAT), json.dumps(QUAKE), json.dumps(HEAT), json.dumps(QUAKE)))
    assert out == ['SEISMIC']


def test_an_alert_whose_headline_changed_is_a_new_alert_and_comes_back():
    changed = dict(HEAT, headline='EXTREME HEAT WARNING')
    out = run("""
      saLastFresh = [%s];
      saAlerts = saBuild(saLastFresh); saIdx = 0;
      saDismissCurrent();
      console.log(JSON.stringify(saBuild([%s]).map(a => a.headline)));
    """ % (json.dumps(HEAT), json.dumps(changed)))
    assert out == ['EXTREME HEAT WARNING']


def test_dismissing_the_last_alert_leaves_an_empty_list():
    out = run("""
      saLastFresh = [%s]; saAlerts = saBuild(saLastFresh); saIdx = 0;
      saDismissCurrent();
      console.log(JSON.stringify({ shown: saAlerts.length, calls }));
    """ % json.dumps(HEAT))
    assert out == {'shown': 0, 'calls': ['cycle', 'ticker']}


def test_dismissing_a_storm_also_hides_the_eonet_copy_of_it():
    out = run("""
      saLastFresh = [%s, %s]; saAlerts = saBuild(saLastFresh); saIdx = 0;
      saDismissCurrent();
      console.log(JSON.stringify(saBuild(saLastFresh).map(a => a.cat)));
    """ % (json.dumps(NHC), json.dumps(EONET_DUP)))
    assert out == []


def test_in_pink_mode_a_double_click_dismisses_nothing():
    out = run("""
      saLastFresh = [%s]; saAlerts = saBuild(saLastFresh); saIdx = 0;
      saDismissCurrent();
      console.log(JSON.stringify({ shown: saAlerts.length, calls }));
    """ % json.dumps(HEAT), pink='true')
    assert out == {'shown': 1, 'calls': []}


def test_the_alert_card_listens_for_a_double_click():
    assert re.search(r"getElementById\('sa-item'\)\.addEventListener\('dblclick',\s*saDismissCurrent\)", source())
