#!/usr/bin/env bash
# Open the clock page, or reload the tab that already shows it.
# Usage: open_clock.sh PORT URL KEEP|NEW
#   KEEP reloads the open tab on its own URL (so its ?mode= stays); NEW loads URL in it (a mode was passed).
# Only Safari and Google Chrome that are already running are asked (never launched to check).
# Any osascript failure falls through to a plain `open`; a refusal (-1743, no Automation permission) says so on stderr first.
PORT="$1"; URL="$2"; HOW="${3:-KEEP}"
MATCH=":$PORT/zulu-clock"   # same pattern as tab_match in dock.json
[ "$HOW" = "NEW" ] && TARGET="$URL" || TARGET=""

# Each script prints "reloaded" when it found and reloaded a tab, nothing otherwise.
SAFARI='on run argv
if application "Safari" is not running then return ""
tell application "Safari"
repeat with w in windows
repeat with t in tabs of w
if (URL of t as text) contains (item 1 of argv) then
if (item 2 of argv) is "" then
set URL of t to (URL of t as text)
else
set URL of t to (item 2 of argv)
end if
return "reloaded"
end if
end repeat
end repeat
end tell
return ""
end run'
CHROME='on run argv
if application "Google Chrome" is not running then return ""
tell application "Google Chrome"
repeat with w in windows
repeat with t in tabs of w
if (URL of t as text) contains (item 1 of argv) then
if (item 2 of argv) is "" then
reload t
else
set URL of t to (item 2 of argv)
end if
return "reloaded"
end if
end repeat
end repeat
end tell
return ""
end run'

for APP in Safari "Google Chrome"; do
    [ "$APP" = Safari ] && SCRIPT="$SAFARI" || SCRIPT="$CHROME"
    ERR="$(mktemp)"
    OUT="$(osascript -e "$SCRIPT" "$MATCH" "$TARGET" 2>"$ERR")"
    # -1743: this app may not control the browser, so we cannot tell if a tab exists
    grep -q -- '-1743' "$ERR" && DENIED="$DENIED${DENIED:+, }$APP"
    rm -f "$ERR"
    [ "$OUT" = "reloaded" ] && exit 0
done
[ -n "$DENIED" ] && echo "  Could not reuse the open clock tab: this app may not control $DENIED (System Settings > Privacy & Security > Automation). Opening a new tab." >&2
open "$URL"
