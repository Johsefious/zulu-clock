#!/usr/bin/env bash
# Zulu Clock v1 — launcher for macOS
# Starts a local HTTP server so the app works in any browser (Safari, Chrome, etc.)

PORT=8765
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
URL="http://localhost:$PORT/zulu-clock.html"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ZULU CLOCK v1"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Kill anything already on that port
lsof -ti:$PORT | xargs kill -9 2>/dev/null || true

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
