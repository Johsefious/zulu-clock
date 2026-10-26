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
- **Status:** active

## Missions come live through cmd fs's own endpoint
- **Date:** 2026-10-23
- **Decided:** the clock reads missions only through cmd fs's `mmGetMissions`, live, from an always-open local router that uses Joe's own sign-in; it never reads the sheet. Facilities show on the mission cards.
- **Against:** reading the sheet, a private address with a key (anyone holding the key could read mission data), and a read-only snapshot preview.
- **Why:** nothing is opened to the web, and the clock shows what the live script says.
- **By:** Joe
- **Status:** active
