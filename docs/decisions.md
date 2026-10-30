# Decisions

Append-only, newest last. One entry per settled decision with Date, Decided, Against, Why, By and Status. A decision is
reopened by a new entry that supersedes it, never by editing the old one.

## Every status on the clock comes from a real call
- **Date:** 2026-10-23
- **Decided:** `server.py` makes every outside call and keeps how each went; the page prints each status from `/status`.
- **Against:** a separate health check beside the page's own calls, and statuses guessed from flags.
- **Why:** the ticker claimed sources were online when they weren't, and the SA fetchers turned failures into "no alerts".
- **By:** Joe
- **Status:** active

## One page, three colour modes
- **Date:** 2026-10-23
- **Decided:** green, pink and blue are modes of this one page and differ only in colour.
- **Against:** a separate copy of the page per colour (the Pink Clock page).
- **Why:** copies drift apart.
- **By:** Joe
- **Status:** active, except "only in colour": superseded by "Pink mode counts down to Christmas instead of showing alerts"

## Missions come live through cmd fs's own endpoint
- **Date:** 2026-10-23
- **Decided:** the clock reads missions only through cmd fs's `mmGetMissions`, live, from an always-open local router that uses Joe's own sign-in; it never reads the sheet. Facilities show on the mission cards.
- **Against:** reading the sheet, a private address with a key (anyone holding the key could read mission data), and a read-only snapshot preview.
- **Why:** nothing is opened to the web, and the clock shows what the live script says.
- **By:** Joe
- **Status:** active

## Zulu is the big clock in green and blue, local time in pink
- **Date:** 2026-10-29
- **Decided:** green and blue show Zulu big with a small `LOCAL` line and this device's time under it. Pink swaps them: this device's time big (zone's name in its label and date line), Zulu small.
- **Against:** local time big in every mode (tried earlier the same day); Zulu big with no local time.
- **Why:** the clock is a Zulu clock first; local time is the extra line, and pink is the one mode that flips it.
- **By:** Joe
- **Status:** active

## Pink mode counts down to Christmas instead of showing alerts
- **Date:** 2026-10-29
- **Decided:** in pink mode the SA panel shows no disasters, only a snowflake and the days until Christmas (local date). The SA sources are still called, so other modes show alerts at once.
- **Against:** pink differing from the other modes only in colour.
- **Why:** Joe asked for pink mode without disasters.
- **By:** Joe
- **Status:** active

## The server answers only the clock and sends cards only what they draw
- **Date:** 2026-10-29
- **Decided:** `server.py` refuses a request whose Host is not `127.0.0.1` or `localhost`, serves only `zulu-clock.html` from the folder, and cuts `/missions` and the `presser` source to the fields the cards draw. Feed text reaches the page only through `esc`.
- **Against:** passing cmd fs's and Presser's whole answers through; serving the folder as it was.
- **Why:** a web page on another name could read missions (people, facilities, plans) through the server, and a bad feed item could do the same from inside the page.
- **By:** Joe
- **Status:** active

## The page's script lives in its own file
- **Date:** 2026-10-29
- **Decided:** the script moved from `zulu-clock.html` to `zulu-clock.js`; `server.py` serves the page and the script and nothing else, both with `Cache-Control: no-cache`. Only the small colour-mode script stays inline in `<head>`, so the page never flashes the wrong colour. Archived tests read functions from the script through one helper, `tests/archive/page_js.py`.
- **Against:** one 2,100-line HTML file; splitting the script into modules (more files for a page with no build step).
- **Why:** the page and its logic can be read and changed apart, and tests stop carrying six copies of the same extraction.
- **By:** Claude, from the 2026-10-29 code review; Joe asked for the review's work to be finished
- **Status:** active

## A failed SA source counts as failed
- **Date:** 2026-10-29
- **Decided:** each SA fetcher returns an empty list marked failed when its call fails or answers with an error, and a plain empty list when it answered with no alerts. More than half failed turns on `saDegraded`, which makes the start-up retries run.
- **Against:** treating every failure as "no alerts" (the old way), which kept the retries from ever running.
- **Why:** a quiet panel must mean quiet sources, not broken ones.
- **By:** Claude, from the 2026-10-29 code review
- **Status:** active

## The suite holds only contract tests
- **Date:** 2026-10-29
- **Decided:** two archived tests move into the suite: `test_server_leaks.py` (what the server answers, to whom, and which fields it sends) and `test_dock_json.py` (that `dock.json`, the contract docks reads, agrees with `launch.sh` and `server.py`). Everything else stays archived.
- **Against:** a rule in CLAUDE.md for changing `launch.sh` and `dock.json` together (the dock test enforces it); moving the clock-face, zone-row, SA, press and memory tests in, which check page behaviour or server internals and would rarely fail.
- **Why:** Joe wants the suite to guard contracts, stay small and be worth running, not grow with every feature.
- **By:** Joe set the bar; Claude picked the tests
- **Status:** active

## The test-run logger stays
- **Date:** 2026-10-29
- **Decided:** `tests/conftest.py` stays, now as one line that loads the shared testruns recorder (adoption replaced the copied recorder and `tools/failure_history.py`). The recorder writes `test-runs.jsonl`, which every repo on this Mac keeps by rule.
- **Against:** removing it as a copy that doesn't belong here.
- **Why:** without it no test run is recorded, and changes can't be reported by their failing and passing runs.
- **By:** Claude, after Joe asked whether it belongs here
- **Status:** active

## Ports come from the ports list
- **Date:** 2026-10-29
- **Decided:** no port is typed into the code. `launch.sh` and `server.py` ask `port home <repo>` (a command added to the ports repo for this) for the clock's, Presser's and cmd fs's home ports, and the Press link goes through the server's `/go/presser`. `dock.json` keeps the clock's port written in, because docks reads it as plain JSON, and the suite checks it against the list. `MISSIONS_CALL` still overrides cmd fs's address.
- **Against:** leaving 8769, 8771 and 8767 typed into four files (the dropped "Ports stay where they are" entry); reading `ports.json` directly, which would copy the lookup into this repo.
- **Why:** the ports list is the one home of every port on this Mac; a moved port should need one edit there.
- **By:** Joe agreed to the proposal; Claude built it
- **Status:** active

## The launcher reloads an open clock tab
- **Date:** 2026-10-29
- **Decided:** `launch.sh` asks Safari, then Chrome, through `tools/open_clock.sh`, for a tab matching `:PORT/zulu-clock` (dock.json's `tab_match`) and reloads it; only a browser already running is asked, and when none has the tab, or macOS refuses the asking, it opens the page as before.
- **Against:** always opening a new tab, which left the clock tab on the TV running the old page beside a duplicate.
- **Why:** the clock lives in one tab, often AirPlayed to the TV, and a restart should reach that tab.
- **By:** Joe chose the fix from a hand test; Claude built it
- **Status:** replaced by "The browser is never scripted" below

## The browser is never scripted
- **Date:** 2026-10-29
- **Decided:** the browser is never scripted. The page checks in with the server every 2 s and reloads when the server restarts; the launcher opens a tab only when no page checks in within 6 s.
- **Against:** asking Safari and Chrome to reload the tab, the decision above.
- **Why:** asking Chrome needs macOS Automation permission for whatever app runs the launcher, which would give that app control of all of Chrome.
- **By:** Joe ruled out browser control after a hand test; Claude built the replacement
- **Status:** active

## The Dock leaves the TV tab alone
- **Date:** 2026-10-29
- **Decided:** `dock.json` sets `front_open_tab: false` and `close_tabs_on_quit: true`. A tile click with a clock tab open anywhere raises nothing (a newer commit still reloads the tab in place), and Quit on the tile closes every clock tab, the TV one included, while the server keeps running.
- **Against:** docks' defaults, which bring the open tab's window forward on a click (pulling up the computer window that AirPlays to the TV) and leave the tabs open on Quit.
- **Why:** the clock runs full screen on the TV in the same Chrome as Joe's working tabs, so a click must not move windows and a Quit should clear the TV.
- **By:** Joe, through the docks session; Claude added the fields
- **Status:** active

## Zulu Clock declares restart safety to docks
- **Date:** 2026-10-29
- **Decided:** Zulu Clock declares `restart_safety` in `dock.json` and answers docks' two calls, `POST /__docks/close` and `GET /__docks/restart-status`. Quit on the Dock tile now stops the server as well as closing its tabs. The answer is always `closing`, because the only state is the in-memory cache and call log, which refill.
- **Against:** staying undeclared, which made Quit print "kept" and left the server running.
- **Why:** Joe wants every Dock app on the same docks contract.
- **By:** Joe, through the docks session; Claude built it
- **Status:** active
