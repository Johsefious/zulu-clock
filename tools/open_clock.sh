#!/usr/bin/env bash
# Open the clock page only if no clock page is already open.
# Usage: open_clock.sh PORT URL
# An open clock page says hello to the server every couple of seconds (and reloads itself when the server restarts),
# so this asks the server whether one has: GET /__clock/seen. Seen: nothing is opened. Not seen within
# CLOCK_SEEN_WAIT seconds (default 6), or the server does not answer: `open URL`. The browser is never scripted or asked.
PORT="$1"; URL="$2"
WAIT="${CLOCK_SEEN_WAIT:-6}"

END=$((SECONDS + WAIT))
while :; do
    case "$(curl -s --max-time 1 "http://127.0.0.1:$PORT/__clock/seen" 2>/dev/null)" in
        *'"seen": true'*) exit 0 ;;
    esac
    [ "$SECONDS" -ge "$END" ] && break
    sleep 0.5
done
open "$URL"
