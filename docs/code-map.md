# Code map

## Layout

```
zulu-clock/
├── zulu-clock.html   the page: markup and styles (entry point for the browser); sets the colour mode inline in <head>
├── zulu-clock.js     the page's script: clock, moon, weather, ticker, SA panel, Press, Missions
├── server.py         local server (entry point): serves the folder, makes every outside call, answers /status
├── launch.sh         asks `port home zulu-clock` for its port, starts server.py on it and reloads an already-open clock tab (or opens the page); stops only an earlier Zulu Clock server
├── launch-pink.sh    launch.sh opening in pink mode
├── dock.json         how a Dock icon starts, restarts and opens the clock, and what a click and Quit do to an open clock tab; declares restart safety
├── icons/            the Dock icon
├── pytest.ini        the suite is tests/; tests/archive/ is skipped unless named
├── tests/
│   ├── conftest.py   writes one line per pytest run to test-runs.jsonl
│   └── archive/      builders' tests
├── tools/failure_history.py   reads test-runs.jsonl back: which tests failed, first and last time
└── tools/open_clock.sh        launch.sh's opener: reloads an open Safari/Chrome tab matching `:PORT/zulu-clock`, else `open`
```

### Page sections

`zulu-clock.js` runs top to bottom in sections, each opened by a `// ───` banner with its name. Search for the name, not a line number.

| Section | What it holds |
|---|---|
| LOADER | the loading screen and its own small clock; dismissed once weather, news and SA have answered |
| CONFIG | `ZONES`, refresh intervals, `src` (the `/source/` address) and other fixed values |
| STATUS | `renderStatus`: every status word, read from `/status` |
| DOM BUILD | the zone rows, built once from `ZONES` |
| HELPERS | `fetchT` (every loader's fetch: a time limit, and a non-ok answer throws `HTTP <status>`), `pad`, `zoneParts`, `localClock`, `zuluTime`, `clockFace`, the moon (`getMoonPhaseData`), `esc` and the other pure pieces |
| CLOCK TICK | `tick()`: the clock block, zone rows (`zoneRow`, in HELPERS) and once-a-minute work |
| WEATHER | METAR and Open-Meteo, sunrise and sunset |
| TICKER | the scrolling news line, driven by `requestAnimationFrame` |
| LIVE NEWS | `loadHeadlines` from the Google News sources, `httpOnly` for feed links |
| SITUATIONAL AWARENESS | the `saFetch*` fetchers (a failed one returns `saFailed()`), `saIsDegraded`, `saMerge`, the 48-hour store and the SA panel |
| PRESS | `loadPress`, `pressRender` |
| MISSIONS | `loadMissions`, `missionsRender` |
| MODES | green, pink, blue; the moon click and the M key |
| START | first paint, `onTheSecond` (the once-a-second tick, lined up with the turn of each second) and `launchWithRetry` for each loader |

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
- **Other apps' ports.** Presser's and cmd fs's addresses come from `port home handmarks` and `port home cmd-fs` on each
  call (`server.py:home_port`, `address`); a failed lookup shows as that source failing in `/status`. No port is typed in
  the code; `dock.json` holds the clock's own, and the suite checks it against the list.
- **Press.** `server.py` reads the Presser app's summary route (the `presser` source); the page draws the cards
  (`loadPress`, `pressRender`). Clicking Press opens `/go/presser`, which sends the browser on to Presser. Nothing is stored.
- **Missions.** `GET /missions` makes `server.py` call cmd fs's `mmGetMissions` at `POST <MISSIONS_CALL>/call/mmGetMissions`
  (`server.py:send_missions`), never the sheet. A refusal that arrives as an HTTP 200 is recorded as a failure. The page
  draws them (`loadMissions`, `missionsRender`). Nothing is stored.
- **In memory only.** The 120 s cache and the 24 h call log in `server.py`; each write drops what is past its time (`server.py:record`, `call`), and both refill from the next calls.

## Endpoints

One change endpoint, for docks. Nothing the clock reads is changed through the server; every other route is a read.

| Endpoint | Does | Variant parameter | Refuses when | Code |
|---|---|---|---|---|
| `POST /__docks/close` | Answers `{"answer": "closing", "reason", "as_of"}` (always: the cache and call log only refill), then stops the server so the process exits | `for` = restart \| quit | not this server's Host (403); not sent as `application/json`, so a web page cannot post it without asking first (415); a body that is missing, not JSON or without a known `for` (400); any other POST path (404) | `server.py:Handler.do_POST` |

Every request must name this server as its Host (`127.0.0.1` or `localhost`), else 403 (`server.py:OWN_HOSTS`), so a
web page on another name cannot reach cmd fs or Presser through it. Only `/`, `/zulu-clock.html` and `/zulu-clock.js` are served from the
folder (`server.py:SERVED_FILES`); any other file is 404.

Reads, all GET:

- `GET /status`: per source, its state (`answering`, `partial`, `failing`, `offline`, `not called`), the latest error and how many calls answered.
- `GET /source/<name>?<query>`: the call to that source's fixed address, answered as it came back (404 for a name not in `SOURCES`, 502 when the source did not answer). `presser` is cut to the
  fields the press cards draw (`server.py:trim_summary`).
- `GET /__docks/restart-status`: `{"clear": true, "reason", "as_of"}`, built fresh, no outside calls (`server.py:restart_status`). Docks reads it in `docks check`.
- `GET /go/presser`: 302 to Presser's home address, or 502 with the reason when the ports list has none.
- `GET /missions`: cmd fs's missions, cut to the fields the mission cards draw, members as first names (`server.py:trim_mission`).
- Any other path: the file in this folder.

## Tests

- **Suite:** `tests/`, contract tests only: `test_server_leaks.py` (who the server answers, which files and fields it sends, `no-cache` on the page and script) and `test_dock_json.py` (`dock.json` agrees with `launch.sh` and `server.py`). Why only these: `docs/decisions.md`, "The suite holds only contract tests".
- **Archive:** `tests/archive/`, builders' tests, skipped by pytest unless named. Page tests run the script's own functions in node through `tests/archive/page_js.py` (`pick`).
- **Run record:** `test-runs.jsonl` in the repo's main folder, untracked, written on every run by `tests/conftest.py` (modelled on djitel's). `python3 tools/failure_history.py` reads it back.
- **Run the suite:** `.venv/bin/python -m pytest -q`. Run an archived test by naming its file, for example `.venv/bin/python -m pytest tests/archive/test_zone_rows.py -q`.
