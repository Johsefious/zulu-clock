"""A finished Presser story (every step done) gets no card on the clock, the way an archived one gets none
(GitHub issue 1). Runs the page's own pressVisible in node."""
import json
import subprocess

from page_js import pick



def visible(stories):
    fn = pick('pressVisible')
    script = fn + 'console.log(JSON.stringify(pressVisible(%s).map(s => s.id)))' % json.dumps(stories)
    return json.loads(subprocess.run(['node', '-e', script], capture_output=True, text=True, check=True).stdout)


def story(id, progress, archived=False):
    return {'id': id, 'archived': archived, 'progress': progress}


def test_a_finished_story_gets_no_card():
    assert visible([story('done', [14, 14]), story('live', [11, 15])]) == ['live']


def test_an_archived_story_still_gets_none():
    assert visible([story('old', [3, 15], archived=True), story('live', [11, 15])]) == ['live']


def test_a_story_with_no_steps_or_no_progress_keeps_its_card():
    assert visible([story('none', [0, 0]), story('missing', None), story('new', [0, 15])]) == ['none', 'missing', 'new']
