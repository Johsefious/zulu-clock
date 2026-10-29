# Code map

## Layout

```
zulu-clock/
├── zulu-clock.html   the page: markup and styles (entry point for the browser); sets the colour mode inline in <head>
├── zulu-clock.js     the page's script: clock, moon, weather, ticker, SA panel, Press, Missions
├── server.py         local server (entry point): serves the folder, makes every outside call, answers /status
├── launch.sh         starts server.py on its port and opens the page; stops only an earlier Zulu Clock server
├── launch-pink.sh    launch.sh opening in pink mode
├── dock.json         how a Dock icon starts, restarts and opens the clock
├── icons/            the Dock icon
├── pytest.ini        the suite is tests/; tests/archive/ is skipped unless named
├── tests/
│   ├── conftest.py   writes one line per pytest run to test-runs.jsonl
│   └── archive/      builders' tests
└── tools/failure_history.py   reads test-runs.jsonl back: which tests failed, first and last time
```

### Page sections

`zulu-clock.js` runs top to bottom in sections, each opened by a `// ───` banner with its name. Search for the name, not a line number.

| Section | What it holds |
|---|---|
| LOADER | the loading screen and its own small clock; dismissed once weather, news and SA have answered |
| CONFIG | `ZONES`, refresh intervals, `PRESS_URL`, `src` (the `/source/` address) and other fixed values |
| STATUS | `renderStatus`: every status word, read from `/status` |
| DOM BUILD | the zone rows, built once from `ZONES` |
| HELPERS | `pad`, `zoneParts`, `localClock`, `zuluTime`, `clockFace`, the moon (`getMoonPhaseData`), `esc` and the other pure pieces |
| CLOCK TICK | `tick()`: the clock block, zone rows (`zoneRow`, in HELPERS) and once-a-minute work |
| WEATHER | METAR and Open-Meteo, sunrise and sunset |
| TICKER | the scrolling news line, driven by `requestAnimationFrame` |
| LIVE NEWS | `loadHeadlines` from the Google News sources, `httpOnly` for feed links |
| SITUATIONAL AWARENESS | the `saFetch*` fetchers (a failed one returns `saFailed()`), `saIsDegraded`, `saMerge`, the 48-hour store and the SA panel |
| PRESS | `loadPress`, `pressRender` |
| MISSIONS | `loadMissions`, `missionsRender` |
| MODES | green, pink, blue; the moon click and the M key |
| START | first paint and `launchWithRetry` for each loader |

`zulu-clock.html` holds the markup in the same order (topbar, Zulu, moon, zones, weather, Press, Missions, ticker) and all the styles.

## Data flow

- **Outside sources.** The page never calls an outside site. It asks `server.py` at `/source/<name>?<query>`
  (`zulu-clock.js:src`), and `server.py` calls the fixed address for that name (`server.py:SOURCES`, the one list of
  every outside source). Answers are cached 120 s in memory (`server.py:call`).
- **Status.** `server.py:call` records how each distinct call went; `/status` reports it per source
  (`server.py:status`). The page prints every status word from `/status` (`zulu-clock.js:renderStatus`).
- **Weather and moon.** Open-Meteo and Aviation Weather through `/source/`; the moon is computed in the page
  (`getMoonPhaseData`), no source.
- **Clocks and Christmas.** `clockFace` picks what the clock block shows: Zulu big (`zuluTime`) with `LOCAL` and this
  device's time (`localClock`) small under it in green and blue, the two swapped in pink. In pink mode the SA panel shows the days until Christmas (`christmasItem`), computed in the page, no source.
- **Headlines.** Google News World, US and CA through `/source/` (`loadHeadlines`).
- **SA panel.** USGS, NWS, NHC, NASA EONET, NIFC, WHO and NOAA SWPC through `/source/` (`saFetch*`, merged by
  `saMerge`). Any alert seen in the last 48 hours is kept in the page's localStorage (`saLoadStored`). **This is a write
  that does not go through an endpoint.**
- **Feed text.** Text from outside feeds goes into `innerHTML` only through `esc` (`zulu-clock.js:esc`); a feed link is
  kept only when it is http or https (`httpOnly`). Tests: `tests/archive/test_feed_text_is_text.py`, `test_server_leaks.py`.
- **Mode.** The last colour mode picked is kept in the page's localStorage (`nextMode`). **A write that does not go
  through an endpoint.**
- **Press.** `server.py` reads the Presser app's summary route (the `presser` source); the page draws the cards
  (`loadPress`, `pressRender`). Nothing is stored.
- **Missions.** `GET /missions` makes `server.py` call cmd fs's `mmGetMissions` at `POST <MISSIONS_CALL>/call/mmGetMissions`
  (`server.py:send_missions`), never the sheet. A refusal that arrives as an HTTP 200 is recorded as a failure. The page
  draws them (`loadMissions`, `missionsRender`). Nothing is stored.
- **In memory only.** The 120 s cache and the 24 h call log in `server.py`; each write drops what is past its time (`server.py:record`, `call`), and both refill from the next calls.

## Endpoints

None, read-only. Nothing the clock reads is changed through it. Every route is a GET:

Every request must name this server as its Host (`127.0.0.1` or `localhost`), else 403 (`server.py:OWN_HOSTS`), so a
web page on another name cannot reach cmd fs or Presser through it. Only `/`, `/zulu-clock.html` and `/zulu-clock.js` are served from the
folder (`server.py:SERVED_FILES`); any other file is 404.

- `GET /status`: per source, its state (`answering`, `partial`, `failing`, `offline`, `not called`), the latest error and how many calls answered.
- `GET /source/<name>?<query>`: the call to that source's fixed address, answered as it came back (404 for a name not in `SOURCES`, 502 when the source did not answer). `presser` is cut to the
  fields the press cards draw (`server.py:trim_summary`).
- `GET /missions`: cmd fs's missions, cut to the fields the mission cards draw, members as first names (`server.py:trim_mission`).
- Any other path: the file in this folder.

## Tests

- **Suite:** `tests/`, contract tests only: `test_server_leaks.py` (who the server answers, which files and fields it sends, `no-cache` on the page and script) and `test_dock_json.py` (`dock.json` agrees with `launch.sh` and `server.py`). Why only these: `docs/decisions.md`, "The suite holds only contract tests".
- **Archive:** `tests/archive/`, builders' tests, skipped by pytest unless named. Page tests run the script's own functions in node through `tests/archive/page_js.py` (`pick`).
- **Run record:** `test-runs.jsonl` in the repo's main folder, untracked, written on every run by `tests/conftest.py` (modelled on djitel's). `python3 tools/failure_history.py` reads it back.
- **Run the suite:** `.venv/bin/python -m pytest -q`. Run an archived test by naming its file, for example `.venv/bin/python -m pytest tests/archive/test_zone_rows.py -q`.
