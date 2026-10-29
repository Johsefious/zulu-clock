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
- **In memory only.** The 120 s cache and the 24 h call log in `server.py`; both refill from the next calls.

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

- **Suite:** `tests/` (only `conftest.py` so far; pytest runs what is in `tests/`).
- **Archive:** `tests/archive/`, builders' tests, skipped by pytest unless named.
- **Run record:** `test-runs.jsonl` in the repo's main folder, untracked, written on every run by `tests/conftest.py`.
  `python3 tools/failure_history.py` reads it back.
- **Run the suite:** `.venv/bin/python -m pytest -q`. Run an archived test by naming its file, for example
  `.venv/bin/python -m pytest tests/archive/test_dock_json.py -q`.
