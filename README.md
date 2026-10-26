# Zulu Clock

A full-screen tactical time display for macOS: UTC (Zulu) time and five other time zones, the moon, California weather,
a news ticker, a rotating situational-awareness panel (earthquakes, storms, fires, outbreaks, space weather), a Press
card per story and the next four missions. It is one page, `zulu-clock.html`, plus `server.py`, a small local server that
makes every outside call for it.

Where things live, what each call reads and how data moves: `docs/code-map.md`. Why a choice was made:
`docs/decisions.md`.

## Install and run

Needs macOS, Python 3 and an internet connection (weather, news and SA are live data).

```bash
./launch.sh
```

This starts `server.py` and opens the clock in your browser. `./launch.sh pink` (or `green`, `blue`) opens it in that
mode; `./launch-pink.sh` does the same for pink. `Ctrl+C` stops it. If its port is taken, `launch.sh` stops the holder
only when it is an earlier Zulu Clock server; otherwise it says so and exits. To see the port, run `port list`.

Opening `zulu-clock.html` directly (`open zulu-clock.html`) shows the time, time zones and moon only, because the
rest comes through `server.py`.

Click the moon or press `M` to change mode. Full screen: Safari `⌘ Ctrl F`, Chrome `⌘ Shift F` or F11.

Missions come from cmd fs's router. To point the clock somewhere else, set `MISSIONS_CALL`:
`MISSIONS_CALL=http://127.0.0.1:<port> ./launch.sh`.

To see which sources are answering right now, with the reason when one isn't, run `curl -s localhost:<port>/status`
(the port from `port list`).

## Tests

```bash
python3 -m venv .venv && .venv/bin/pip install pytest
.venv/bin/python -m pytest -q
```

## Status

The clock works: every source it shows is read through `server.py`, and every status word on it comes from a real call
to that source. "Answering" means a reply came in time, not that the reply was good. Missions need cmd fs's router
running, otherwise the clock says so. The SA fetchers still turn a failed call into "no alerts", so only `/status`
tells you a feed is down.
