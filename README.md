# Zulu Clock

A full-screen tactical time display for macOS: Zulu time large with this device's local time under it (pink mode swaps them), five other time zones, the moon, California weather, a news ticker, a rotating situational-awareness panel (earthquakes, storms, fires, outbreaks, space weather), a Press card per story and the next four missions. It is one page, `zulu-clock.html` with its script `zulu-clock.js`, plus `server.py`, a small local server that makes every outside call for it.

Where things live, what each call reads and how data moves, and why each choice was made, are in the code map and the decisions log in this repo's docs folder.

## Install from the zip (teammates)

Unzip `Zulu Clock 1.0.0.zip`, open the folder and double-click `Install Zulu Clock`. It checks for Python 3, installs the shared Docks and Ports tools if they are missing or older, copies the clock to `~/Applications/Zulu Clock`, makes the Zulu Clock app and puts it in the Dock, and checks that the clock's server answers. Open Zulu Clock from the Dock. Run a newer installer the same way to update; it never goes back to an older version and keeps nothing of yours to lose (the clock stores no files). The weather, news and alert sources need no key. Press and Missions show as not answering unless Presser and cmd fs are running on the same Mac.

The zip is built with `repo release <this folder>`; the code map's Release section says what it holds.

## Install and run (this Mac, from the repo)

Needs macOS, Python 3, the `port` command from the ports repo (find it with `repo path ports`; see its README), an internet connection (weather, news and SA are live data) and, for the missions, cmd fs's router running on this Mac (without it the clock says so). The clock finds its own port, Presser's and cmd fs's in the ports list.

```bash
./launch.sh
```

This starts `server.py`. A clock tab that is already open reloads itself from the new server; when no clock page checks in within a few seconds, the clock opens in your browser. `./launch.sh pink` (or `green`, `blue`) opens it in that mode; `./launch-pink.sh` does the same for pink. `Ctrl+C` stops it. If its port is held by something else, `launch.sh` says so and exits (the code map says what it will stop). To see the port, run `port list`.

The clock has a Dock icon; `docks app list` shows its entry.

Opening `zulu-clock.html` directly (`open zulu-clock.html`) shows the time, time zones and moon only, because the rest comes through `server.py`.

Click the moon or press `M` to change mode. Pink mode shows the days until Christmas in place of the alerts. Full screen: Safari `⌘ Ctrl F`, Chrome `⌘ Shift F` or F11.

Missions come from cmd fs's router. To point the clock somewhere else, set `MISSIONS_CALL`: `MISSIONS_CALL=http://127.0.0.1:<port> ./launch.sh`.

To see which sources are answering right now, with the reason when one isn't, run `curl -s localhost:<port>/status` (the port from `port list`).

## Tests

The tests run on the shared test venv in app-dev (app-dev's CLAUDE.md gives the one-time setup), one at a time, because the server tests share ports.

```bash
"$(repo path app-dev)/.venv/bin/python" -m pytest -q -p no:xdist
```

## Status

Version 1.0.0 (`VERSION`) is the first one that ships to teammates; the zip is built and its installer proven on a throwaway home, not yet sent. The clock works: every source it shows is read through `server.py`, and every status word on it comes from a real call to that source. "Answering" means a reply came in time, not that the reply was good. A failed SA source counts as failed, not as "no alerts"; `/status` tells you which feed is down.
