# Zulu Clock

A full-screen tactical time display for macOS. Built as a single self-contained HTML file — no installation, no dependencies to install.

![Dark hacker-style clock with green-on-black digital display]

## What it shows

| Section | Data | Source |
|---|---|---|
| **Primary clock** | UTC/Zulu time (HH:MM:SSZ) | System clock |
| **Timezone row** | Los Angeles · Denver · Chicago · New York · London | System clock |
| **California weather** | Berkeley · Fresno · Tulare · Los Angeles — temp, feels-like, condition | [Open-Meteo](https://open-meteo.com) (free, no key) |
| **News ticker** | Live World / US / CA headlines | Google News RSS, via proxy cascade |

Weather refreshes every 20 minutes. Headlines refresh every 30 minutes with a live countdown in the topbar.

## Requirements

- macOS
- Internet connection — weather and news are live data
- Python 3 (pre-installed on macOS 12+) **or** Safari

## How to run

### Option A — Launch script (recommended, works in any browser)

```bash
cd v1
./launch.sh
```

Opens the clock at `http://localhost:8765/zulu-clock.html` using Python's built-in HTTP server. Works in Safari, Chrome, Firefox, or any modern browser. Press `Ctrl+C` in the terminal to stop.

### Option B — Open directly in browser

Double-click `v1/zulu-clock.html`, or:

```bash
open v1/zulu-clock.html
```

Works in Safari and Chrome. All API calls go through CORS-friendly proxies so local file access is not an issue.

## Full-screen

| Browser | Shortcut |
|---|---|
| Safari | `⌘ Ctrl F` |
| Chrome | `⌘ Shift F` or F11 |

## Notes

- All API calls have a 12-second timeout with automatic retry across three proxy services (rss2json → allorigins → corsproxy). If all news feeds fail, the ticker displays system status messages and retries in 30 minutes.
- Temperature color-codes: **amber** ≥ 90°F · **green** normal · **cyan** ≤ 45°F
- The `FETCH #N` counter in the topbar confirms headlines have refreshed N times since page load.
- Fonts (VT323, Share Tech Mono) load from Google Fonts CDN. If offline, the display falls back to Courier New — the clock still works.

## Project structure

```
zulu-clock/
├── README.md
└── v1/
    ├── zulu-clock.html   ← the entire app (single file)
    └── launch.sh         ← macOS launcher (starts local server + opens browser)
```
