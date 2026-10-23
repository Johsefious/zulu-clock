#!/usr/bin/env bash
# Zulu Clock v1 — launcher for macOS
# Starts a local HTTP server so the app works in any browser (Safari, Chrome, etc.)

PORT=8769
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
URL="http://localhost:$PORT/zulu-clock.html"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ZULU CLOCK v1"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# If the port is taken, stop the holder only when it is Zulu Clock's own server
# (the one started below, serving this folder). Anything else is left alone.
OWN_CMD="-m http.server $PORT --directory $SCRIPT_DIR --bind 127.0.0.1"
HOLDERS="$(lsof -ti tcp:$PORT -sTCP:LISTEN 2>/dev/null || true)"
for PID in $HOLDERS; do
    if [[ "$(ps -o command= -p "$PID" 2>/dev/null)" == *"$OWN_CMD"* ]]; then
        echo "  Port $PORT: stopping the earlier Zulu Clock server (pid $PID)"
        kill "$PID" 2>/dev/null || true
        for _ in 1 2 3 4 5 6 7 8 9 10; do
            kill -0 "$PID" 2>/dev/null || break
            sleep 0.3
        done
    fi
done
if [ -n "$(lsof -ti tcp:$PORT -sTCP:LISTEN 2>/dev/null)" ]; then
    echo "  Port $PORT is held by something that is not Zulu Clock's server."
    echo "  Nothing was stopped. Free port $PORT, then run this again."
    exit 1
fi

if command -v python3 >/dev/null 2>&1; then
    echo "  Server : $URL"
    echo "  Stop   : Ctrl+C"
    echo ""
    python3 -m http.server $PORT --directory "$SCRIPT_DIR" --bind 127.0.0.1 >/dev/null 2>&1 &
    SERVER_PID=$!
    sleep 0.6
    open "$URL"
    trap "kill $SERVER_PID 2>/dev/null; echo ''; echo 'Server stopped.'" EXIT INT TERM
    wait $SERVER_PID
else
    # Python 3 not found — fall back to direct open (works fine in Safari)
    echo "  Python 3 not found — opening directly (use Safari for best results)"
    echo ""
    open "$SCRIPT_DIR/zulu-clock.html"
fi
