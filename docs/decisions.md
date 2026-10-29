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
