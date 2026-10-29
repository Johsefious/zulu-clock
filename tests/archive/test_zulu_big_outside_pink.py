"""Green and blue show Zulu as the big clock with LOCAL and this device's time on the small line under it; pink keeps
this device's time big with ZULU small. Runs the page's own clockFace in node, with the zone named so the result does
not depend on the machine running the test."""
import json
import subprocess

from page_js import pick

LA = 'America/Los_Angeles'
NOW = "new Date('2026-10-29T15:59:12Z')"


def run(call):
    script = pick('pad', 'DAYS', 'MONS', 'zoneParts', 'localClock', 'zuluTime', 'clockFace') + 'console.log(JSON.stringify(%s))' % call
    return json.loads(subprocess.run(['node', '-e', script], capture_output=True, text=True, check=True).stdout)


def test_green_and_blue_show_zulu_big_and_local_small():
    face = run("clockFace(%s, false, %r)" % (NOW, LA))
    assert face['big'] == '15:59:12'
    assert face['date'] == 'THU   29 OCT 2026   Z'
    assert (face['smallLbl'], face['small']) == ('LOCAL', '08:59:12')


def test_pink_keeps_local_big_and_zulu_small():
    face = run("clockFace(%s, true, %r)" % (NOW, LA))
    assert face['big'] == '08:59:12'
    assert face['date'] == 'THU   29 OCT 2026   PDT'
    assert (face['smallLbl'], face['small']) == ('ZULU', '15:59:12Z')


def test_the_big_label_names_what_is_big():
    assert 'ZULU TIME' in run("clockFace(%s, false, %r)" % (NOW, LA))['label']
    assert 'LOCAL TIME' in run("clockFace(%s, true, %r)" % (NOW, LA))['label']
