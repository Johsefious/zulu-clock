"""dock.json tells docks to leave an open clock tab where it is (it may be full screen on the TV) and to close the
clock's tabs on Quit (docks/docs/dock-json.md on feat/restart-safety: front_open_tab, close_tabs_on_quit)."""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def dock():
    with open(os.path.join(ROOT, 'dock.json')) as f:
        return json.load(f)


def test_a_tile_click_does_not_front_an_open_clock_tab():
    assert dock().get('front_open_tab') is False


def test_quit_closes_the_clock_tabs():
    assert dock().get('close_tabs_on_quit') is True


def test_the_clock_is_a_tab_so_docks_accepts_both():
    assert dock().get('kind', 'tab') == 'tab'
