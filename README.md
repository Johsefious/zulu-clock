# Zulu Clock

A full-screen tactical time display for macOS. Built as a single self-contained HTML file — no installation, no dependencies to install.

## Where things stand

Sessions working on the clock: the latest handoff is `handoff/HANDOFF.md` (git-ignored; on Joe's Mac only). Read it first.

## What it shows

| Section | Data | Source |
|---|---|---|
| **Primary clock** | UTC/Zulu time (HH:MM:SSZ) | System clock |
| **Timezone row** | Los Angeles · Denver · Chicago · New York · London | System clock |
| **Moon phase** | Phase name, illumination %, rise/set; click it to change mode | Calculated (no API) |
| **California weather** | Berkeley · Fresno · Tulare · Los Angeles — temp, feels-like, condition | [Open-Meteo](https://open-meteo.com) (free, no key) |
| **News ticker** | Live World / US / CA headlines | Google News RSS, fetched by `server.py` |
| **Press** | A card per story: checks done, overdue and due today, and the next step. The story with the nearest event comes first, with its countdown. Click to open the Presser app | Presser app's `/api/summary` at `http://127.0.0.1:8771` (local), through `server.py` |
| **Missions** | The next four FS missions: days to go, first names, type, facilities, confirmed / briefing / plan ticks, and when the plan is due or late. Red when a mission is two days out with no approved plan | Mission cmd's `mmGetMissions`, through `server.py` |
| **SA panel** | Rotating situational awareness alerts (see below) | Multiple (see below) |

Weather refreshes every 20 minutes. Headlines refresh every 5 minutes.

The Press section reads the Presser app's `/api/summary` through `server.py` every minute and stores nothing. When Presser does not answer, its head says so with the reason from `/status`. A click opens Presser at `PRESS_URL`.

## Status

Every status word on the clock comes from a real call. The page never calls an outside site itself: it asks `server.py` at `/source/<name>`, and `server.py` makes the call to that source's fixed address and keeps how it went. `GET /status` returns, per source, its state and the reason when it failed:

| State | Means |
|---|---|
| `answering` | Every distinct call's latest try got a reply in time (it does not check what the reply said) |
| `partial` | Some did, some didn't; `error` is the latest failure |
| `failing` | None did |
| `not connected` | Mission cmd only: no way in yet |
| `not called` | The clock hasn't asked for it since `server.py` started |

The top bar counts the sources answering and names the ones that aren't; the feed line, the weather head, the SA all-clear card, and the Press and Missions heads each print their own sources' states; the ticker's `[SYS]` items list every source that isn't answering (all of them when there are no headlines). The sources are the `SOURCES` table in `server.py`.

## Missions

The clock reads missions only through Mission cmd's own `mmGetMissions` endpoint (fs-coordination), never from the sheet. `server.py` passes it on at `/missions` every 2 minutes and keeps nothing. It shows first names, dates, mission types and facilities.

`server.py` calls `POST <MISSIONS_CALL>/call/mmGetMissions`, where `MISSIONS_CALL` is an environment variable. Mission cmd has no way in from outside the page yet (its Task 6), so for now the section says "Mission cmd not connected". Mission cmd's read-only preview (`node tools/preview.js <snapshot> 8790` in fs-coordination) speaks the same calls, so `MISSIONS_CALL=http://127.0.0.1:8790 ./launch.sh` shows a snapshot's missions.

## Modes

Three looks: **green** (the original), **pink** (white on hot pink) and **blue** (ice blue on deep navy). Click the moon or press `M` to go to the next one. The clock remembers the last mode picked in that browser.

To open in a given mode, run `./launch.sh pink` (or `green`, `blue`), or add `?mode=pink` to the address. `./launch-pink.sh` does the first; it replaces the separate Pink Clock page, which was a copy of this one in pink.

## Situational Awareness (SA) data sources

All SA alerts rotate in the left panel. Any alert from the past 48 hours is persisted in localStorage so it survives a page refresh even if the live feed goes quiet.

| Alert type | Source | Refresh |
|---|---|---|
| **Earthquakes** (M ≥ 5.5) | [USGS Earthquake Hazards](https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_hour.geojson) | 5 min |
| **CA severe weather / NWS alerts** | [NWS API](https://api.weather.gov/alerts/active?area=CA) | 5 min |
| **Tropical storms & hurricanes** | [NHC Current Storms JSON](https://www.nhc.noaa.gov/CurrentStorms.json) | 5 min |
| **Severe storms, floods, volcanoes** (global) | [NASA EONET v3](https://eonet.gsfc.nasa.gov/api/v3/events) | 5 min |
| **CA wildfires** (≥ 10 acres) | [NIFC WFIGS ArcGIS](https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/WFIGS_Incident_Locations_Current/FeatureServer/0/query) | 5 min |
| **Disease outbreaks / health watches** | [WHO News RSS](https://www.who.int/rss-feeds/news-english.xml) (outbreak-filtered) | 5 min |
| **Geomagnetic storms** (Kp ≥ 5) | [NOAA Space Weather](https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json) | 5 min |

Keywords monitored in WHO feed: outbreak, disease, virus, epidemic, influenza, flu, H5N1, bird flu, avian flu, mpox, measles, dengue, ebola, cholera, typhoid, plague, marburg, zoonotic.

## Requirements

- macOS
- Internet connection — weather, news, and SA are live data
- Python 3 (pre-installed on macOS 12+) **or** Safari

## How to run

### Option A — Launch script (recommended, works in any browser)

```bash
./launch.sh
```

Opens the clock at `http://localhost:8769/zulu-clock.html`, served by `server.py`, which also makes every outside call the clock needs (see Status). Works in Safari, Chrome, Firefox, or any modern browser. Press `Ctrl+C` in the terminal to stop. If port 8769 is already taken, `launch.sh` stops the holder only when it is an earlier Zulu Clock server; otherwise it says so and exits without stopping anything.

### Option B — Open directly in browser

Double-click `zulu-clock.html`, or:

```bash
open zulu-clock.html
```

Shows the time, time zones and moon only: weather, news, SA, Press and Missions all come through `server.py`, and the top bar says the status is unknown.

### Option C — Download from terminal

```bash
curl -L https://raw.githubusercontent.com/Johsefious/zulu-clock/main/zulu-clock.html -o zulu-clock.html
open zulu-clock.html
```

## Full-screen

| Browser | Shortcut |
|---|---|
| Safari | `⌘ Ctrl F` |
| Chrome | `⌘ Shift F` or F11 |

## Notes

- **Loading screen**: on first load, a Zulu clock is shown centered while all data sources initialize. Once all feeds respond (or after 20 seconds), the clock animates to its final position and the full display fades in. If any feed is slow, automatic retries run at 6s → 18s → 45s → 2min before settling into the normal refresh cadence.
- **SA persistence**: any SA alert seen in the last 48 hours stays visible even if the live feed doesn't return it on the next poll.
- News comes from `server.py` (it caches each call for 2 minutes). If all news feeds fail, the ticker shows each source's status from `/status` and keeps retrying.
- Temperature color-codes: **amber** ≥ 90°F · **green** normal · **cyan** ≤ 45°F
- Fonts (VT323, Share Tech Mono) load from Google Fonts CDN. If offline, the display falls back to Courier New — the clock still works.

## Project structure

```
zulu-clock/
├── README.md
├── zulu-clock.html   ← the entire app (single file)
├── server.py         ← local server: serves the page, makes every outside call, answers /status
├── launch.sh         ← macOS launcher (starts server.py + opens browser)
└── launch-pink.sh    ← the same, opening in pink mode
```
