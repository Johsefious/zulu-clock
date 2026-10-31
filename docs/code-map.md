# Code map

## Layout

```
zulu-clock/
├── zulu-clock.html   the page: markup and styles (entry point for the browser); sets the colour mode inline in <head>
├── zulu-clock.js     the page's script: clock, moon, weather, ticker, SA panel, Press, Missions
├── server.py         local server (entry point): serves only the page, its script and its two fonts (not the rest of the folder), makes every outside call, answers /status; started as `server.py PORT DIRECTORY [green|pink|blue]`
├── launch.sh         entry point for a person: asks `port home zulu-clock` for its port; if the port is held, stops the holder only when it is this folder's server.py or the plain `http.server` earlier versions started, else says so and exits; starts server.py on the port (with the mode, if one was given) and runs tools/open_clock.sh; stops the server on Ctrl+C; without python3 it opens zulu-clock.html directly
├── launch-pink.sh    launch.sh opening in pink mode
├── dock.json         the Dock icon's contract with docks: the Ports entry (`zulu-clock`) for the port, the page address and tab match, the `server.py` start command, `/status` as the health path, a restart when `server.py` changes, what a click and Quit do to an open clock tab, and restart safety; passes `MISSIONS_CALL` through
├── icons/            the Dock icon (zulu-clock.svg)
├── fonts/            Share Tech Mono and VT323, latin subsets (.woff2), declared by `@font-face` in zulu-clock.html and served by server.py
├── pytest.ini        the suite is tests/; tests/archive/ is skipped unless named
├── tests/
│   ├── conftest.py   one line that loads the testruns recorder (`testruns hook` wrote it)
│   ├── test_server_leaks.py  suite: who the server answers, which files and fields it sends
│   ├── test_dock_json.py     suite: dock.json agrees with launch.sh and server.py
│   └── archive/      builders' tests (fonts: `test_fonts_served_locally.py`)
├── app.json          what the repo is (family none, app, not shipped, uses docks and port) and the `tests` key testruns owns
├── tools/open_clock.sh   launch.sh's opener: waits up to 6 s (`CLOCK_SEEN_WAIT`) for `/__clock/seen`, then `open` only if no clock page checked in; never scripts the browser
├── docs/             code-map.md (this file), decisions.md, and handoff.md (git-ignored)
├── README.md, CLAUDE.md
└── .gitignore
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
| CLOCK TICK | `tick()`, run every second: the clock block, zone rows (`zoneRow`, in HELPERS), the sunrise and sunset flip and the Christmas card turnover each minute |
| WEATHER | `loadAllWx`: METAR (`fetchMetar`) and Open-Meteo (`fetchWx`) for the eight California places; the zones' sunrise and sunset (`fetchAllSunsets`) are in HELPERS |
| TICKER | the scrolling line (news, weather and SA alerts; `rebuildTicker`), driven by `requestAnimationFrame` |
| LIVE NEWS | `loadHeadlines` from the Google News sources, `httpOnly` for feed links |
| SITUATIONAL AWARENESS | the `saFetch*` fetchers (a failed one returns `saFailed()`), `saIsDegraded`, `saMerge`, the 48-hour store and the SA panel |
| PRESS | `loadPress`, `pressRender` |
| MISSIONS | `loadMissions`, `missionsRender` |
| MODES | green, pink, blue; the moon click and the M key |
| START | first paint, `onTheSecond` (the once-a-second tick, lined up with the turn of each second) and `launchWithRetry` for each loader (retries at 6, 18, 45 and 120 s while a loader reports itself degraded, then its normal interval), and the heartbeat (`heartbeatStep`): every 2 s it says hello and reloads the page when the server's boot id changes |

`zulu-clock.html` holds the markup in the same order (topbar, Zulu, moon, zones, weather, Press, Missions, ticker) and all the styles.

## Data flow

- **Outside sources.** Neither the page nor its script calls an outside site; the two fonts load from `/fonts/` on this server (`server.py:FONTS`). The script asks `server.py` at `/source/<name>?<query>` (`zulu-clock.js:src`), and `server.py` calls the fixed address for that name (`server.py:SOURCES`, the one list of every outside source). Answers to GET calls are cached 120 s in memory (`server.py:CACHE_SECONDS`, `server.py:call`); each call times out after 10 s (`server.py:TIMEOUT`).
- **Status.** `server.py:call` records how each distinct call went; `/status` reports it per source (`server.py:status`). The page prints every status word from `/status` (`zulu-clock.js:renderStatus`).
- **Weather and moon.** Open-Meteo and Aviation Weather through `/source/`; the moon is computed in the page (`getMoonPhaseData`), no source.
- **Clocks and Christmas.** `clockFace` picks what the clock block shows: Zulu big (`zuluTime`) with `LOCAL` and this device's time (`localClock`) small under it in green and blue, the two swapped in pink. In pink mode the SA panel shows the days until Christmas (`christmasItem`), computed in the page, no source.
- **Headlines.** Google News World, US and CA through `/source/` (`loadHeadlines`).
- **SA panel.** USGS, NWS, NHC, NASA EONET, NIFC, WHO and NOAA SWPC through `/source/` (`saFetch*`, merged by `saMerge`). Any alert seen in the last 48 hours is kept in the page's localStorage under `zc_sa_v1`, newest 60 (`saMerge` writes it, `saLoadStored` reads it). **This is a write that does not go through an endpoint.** A source that fails is told apart from one that answered with no alerts (`saFailed`); when more than half fail (`saIsDegraded`) the panel retries on `launchWithRetry`'s schedule.
- **Feed text.** Text from outside feeds goes into `innerHTML` only through `esc` (`zulu-clock.js:esc`); a feed link is kept only when it is http or https (`httpOnly`). Tests: `tests/archive/test_feed_text_is_text.py`, `test_server_leaks.py`.
- **Mode.** The last colour mode picked is kept in the page's localStorage under `zulu-mode` (`zulu-clock.js:nextMode`). **A write that does not go through an endpoint.** The inline script in `zulu-clock.html`'s `<head>` reads `?mode=` from the address first, then that key. `launch.sh` passes a mode to `server.py` as its third argument, and `/__clock/hello` hands it to an open page, which reloads on it.
- **Other apps' ports.** Presser's and cmd fs's addresses come from `port home presser` and `port home cmd-fs` on each call (`server.py:home_port`, `address`); a failed lookup shows as that source failing in `/status`. No port is typed in the code; `dock.json` names the clock's Ports entry (`"port": {"ports": "zulu-clock"}`), docks asks `port home` for the number, and the suite checks the fills against it.
- **Press.** `server.py` reads the Presser app's summary route (the `presser` source); the page draws the cards (`loadPress`, `pressRender`). Clicking Press opens `/go/presser`, which sends the browser on to Presser. Nothing is stored.
- **Missions.** `GET /missions` makes `server.py` call cmd fs's `mmGetMissions` at `POST <MISSIONS_CALL>/call/mmGetMissions` (`server.py:send_missions`), never the sheet. `MISSIONS_CALL` replaces cmd fs's home-port address. A refusal that arrives as an HTTP 200 is recorded as a failure. The page draws them (`loadMissions`, `missionsRender`). Nothing is stored.
- **In memory only.** The 120 s cache and the 24 h call log (`server.py:FORGET_SECONDS`) in `server.py`; each write drops what is past its time (`server.py:record`, `call`), and both refill from the next calls. Also whether a clock page has said hello (`server.py:page_seen`) and this run's boot id (`server.py:BOOT`). The server writes no file.

## Endpoints

One change endpoint, for docks. Nothing the clock reads is changed through the server; every other route is a read.

| Endpoint | Does | Variant parameter | Refuses when | Code |
|---|---|---|---|---|
| `POST /__docks/close` | Answers `{"answer": "closing", "reason", "as_of"}` (always: the cache and call log only refill), then stops the server so the process exits | `for` = restart \| quit | not this server's Host (403); not sent as `application/json`, so a web page cannot post it without asking first (415); a body that is missing, not JSON or without a known `for` (400); any other POST path (404) | `server.py:Handler.do_POST` |

Every request must name this server as its Host (`127.0.0.1` or `localhost`), else 403 (`server.py:OWN_HOSTS`), so a web page on another name cannot reach cmd fs or Presser through it. Only `/`, `/zulu-clock.html`, `/zulu-clock.js` and the two files in `FONTS` are served from the folder (`server.py:SERVED_FILES`); any other file is 404.

Reads, all GET:

- `GET /status`: `{"checked_at", "sources"}`; per source (the `SOURCES` names, then `mission-cmd`): `name`, `label`, `feeds`, its `state` (`answering`, `partial`, `failing`, `offline`, `not called`), the latest `error`, `calls`, `answered` and `last_call_at` (`server.py:status`).
- `GET /source/<name>?<query>`: the call to that source's fixed address, answered as it came back (404 for a name not in `SOURCES`; 502 when the source did not answer, when Presser's address is unknown, or when Presser sent no summary). `presser` is cut to the fields the press cards draw (`server.py:trim_summary`).
- `GET /__docks/restart-status`: `{"clear": true, "reason", "as_of"}`, built fresh, no outside calls (`server.py:restart_status`). Docks reads it in `docks check`.
- `GET /go/presser`: 302 to Presser's home address, or 502 with the reason when the ports list has none.
- `GET /missions`: cmd fs's missions, cut to the fields the mission cards draw, members as first names (`server.py:send_missions`, `trim_mission`); 502 with the reason when cmd fs's address is unknown, it does not answer, it refuses or it sends no missions.
- `GET /__clock/hello`: `{"boot", "mode"}`, this server run's id and the launch mode (or null); notes in memory that a clock page checked in. The page calls it every 2 s.
- `GET /__clock/seen`: `{"seen", "as_of"}`, whether a clock page has said hello since this start. `tools/open_clock.sh` reads it.
- Any other path: 404 (only the files in `server.py:SERVED_FILES` are served).

## Tests

- **Suite:** `tests/`, contract tests only: `test_server_leaks.py` (who the server answers, which files and fields it sends, `no-cache` on the page and script) and `test_dock_json.py` (`dock.json` agrees with `launch.sh` and `server.py`). Why only these: `docs/decisions.md`, "The suite holds only contract tests".
- **Archive:** `tests/archive/`, builders' tests, skipped by pytest unless named. Page tests run the script's own functions in node through `tests/archive/page_js.py` (`pick`).
- **Run record:** `test-runs.jsonl` in the repo's main folder, untracked, written on every run by the testruns recorder, which `tests/conftest.py` loads. `testruns last --full` and `testruns passed <commit>` read it back. The `tests` key in `app.json` says what the whole suite is.
- **Run the suite:** `.venv/bin/python -m pytest -q`. Run an archived test by naming its file, for example `.venv/bin/python -m pytest tests/archive/test_zone_rows.py -q`.
