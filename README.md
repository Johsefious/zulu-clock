# Zulu Clock

A full-screen tactical time display for macOS. Built as a single self-contained HTML file — no installation, no dependencies to install.

## What it shows

| Section | Data | Source |
|---|---|---|
| **Primary clock** | UTC/Zulu time (HH:MM:SSZ) | System clock |
| **Timezone row** | Los Angeles · Denver · Chicago · New York · London | System clock |
| **Moon phase** | Phase name, illumination %, rise/set | Calculated (no API) |
| **California weather** | Berkeley · Fresno · Tulare · Los Angeles — temp, feels-like, condition | [Open-Meteo](https://open-meteo.com) (free, no key) |
| **News ticker** | Live World / US / CA headlines | Google News RSS |
| **SA panel** | Rotating situational awareness alerts (see below) | Multiple (see below) |

Weather refreshes every 20 minutes. Headlines refresh every 5 minutes.

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

Opens the clock at `http://localhost:8765/zulu-clock.html` using Python's built-in HTTP server. Works in Safari, Chrome, Firefox, or any modern browser. Press `Ctrl+C` in the terminal to stop.

### Option B — Open directly in browser

Double-click `zulu-clock.html`, or:

```bash
open zulu-clock.html
```

Works in Safari and Chrome. All API calls go through CORS-friendly proxies so local file access is not an issue.

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
- All API calls have a 12-second timeout with automatic retry across three proxy services (rss2json → allorigins → corsproxy). If all news feeds fail, the ticker displays system status messages and retries in 30 minutes.
- Temperature color-codes: **amber** ≥ 90°F · **green** normal · **cyan** ≤ 45°F
- Fonts (VT323, Share Tech Mono) load from Google Fonts CDN. If offline, the display falls back to Courier New — the clock still works.

## Project structure

```
zulu-clock/
├── README.md
├── zulu-clock.html   ← the entire app (single file)
└── launch.sh         ← macOS launcher (starts local server + opens browser)
```
