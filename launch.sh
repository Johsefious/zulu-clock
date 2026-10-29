#!/usr/bin/env bash
# Zulu Clock v1 — launcher for macOS
# Starts a local HTTP server so the app works in any browser (Safari, Chrome, etc.)

# The clock's port comes from the ports list (the ports repo), never typed here.
PORT="$(port home zulu-clock 2>/dev/null)" || { echo "  No home port for zulu-clock: run 'port home zulu-clock' to see why."; exit 1; }
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
URL="http://localhost:$PORT/zulu-clock.html"
HOW=KEEP   # an already-open clock tab reloads on its own URL, unless a mode is passed
# Optional mode: ./launch.sh pink (or green, blue). Without one, the clock opens in the last mode picked.
case "${1:-}" in
    green|pink|blue) URL="$URL?mode=$1"; HOW=NEW ;;
    "") ;;
    *) echo "  Unknown mode '$1' (use green, pink or blue)"; exit 1 ;;
esac

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ZULU CLOCK v1"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# If the port is taken, stop the holder only when it is Zulu Clock's own server
# (the one started below, or the plain http.server earlier versions started,
# serving this folder). Anything else is left alone.
OWN_CMD="$SCRIPT_DIR/server.py $PORT $SCRIPT_DIR"
OLD_CMD="-m http.server $PORT --directory $SCRIPT_DIR --bind 127.0.0.1"
HOLDERS="$(lsof -ti tcp:$PORT -sTCP:LISTEN 2>/dev/null || true)"
for PID in $HOLDERS; do
    HOLDER_CMD="$(ps -o command= -p "$PID" 2>/dev/null)"
    if [[ "$HOLDER_CMD" == *"$OWN_CMD"* || "$HOLDER_CMD" == *"$OLD_CMD"* ]]; then
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
    # server.py serves this folder and makes every outside call the clock needs
    python3 "$SCRIPT_DIR/server.py" $PORT "$SCRIPT_DIR" >/dev/null 2>&1 &
    SERVER_PID=$!
    sleep 0.6
    # reload a clock tab that is already open (Safari or Chrome) instead of opening a second one
    "$SCRIPT_DIR/tools/open_clock.sh" "$PORT" "$URL" "$HOW"
    trap "kill $SERVER_PID 2>/dev/null; echo ''; echo 'Server stopped.'" EXIT INT TERM
    wait $SERVER_PID
else
    # Python 3 not found — fall back to direct open (works fine in Safari)
    echo "  Python 3 not found — opening directly (use Safari for best results)"
    echo ""
    open "$SCRIPT_DIR/zulu-clock.html"
fi
