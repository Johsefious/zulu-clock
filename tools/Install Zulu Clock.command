#!/bin/bash
# ============================================================================
#  Install Zulu Clock (Mac). Also updates it: run the newer one the same way.
#
#  In the zip this file sits next to "Read me.txt" and a "Files" folder. It:
#    1. checks for Python 3 (and says how to get it if it's missing)
#    2. installs the shared tools the zip carries (Docks and Ports), each only if missing or older
#    3. copies Zulu Clock to ~/Applications/Zulu Clock
#    4. has Docks make the Zulu Clock app, with its icon, in ~/Applications and put it in the Dock
#    5. checks that the clock's server starts and answers
#
#  Nothing is downloaded, and nothing here is hidden: this file is the whole installer.
#  The clock keeps no settings or data of its own on disk, so updating changes nothing of yours.
#
#  For testing: ZULU_SETUP_HOME=<folder> installs everything under that folder instead of your home, uses port
#  ZULU_SETUP_PORT for its check, refuses if something else is on that port, stops only the server it started,
#  and opens nothing.
# ============================================================================
set -u
_SELF="${BASH_SOURCE[0]:-$0}"
while [ -L "$_SELF" ]; do
  _to="$(readlink "$_SELF")"
  case "$_to" in /*) _SELF="$_to" ;; *) _SELF="$(dirname "$_SELF")/$_to" ;; esac
done
SRC="$(cd "$(dirname "$_SELF")" 2>/dev/null && pwd -P)"
FILES="$SRC/Files"
HOME_DIR="${ZULU_SETUP_HOME:-$HOME}"
CODE_HOME="$HOME_DIR/Applications/Zulu Clock"
APP_PATH="$HOME_DIR/Applications/Zulu Clock.app"
TESTING="${ZULU_SETUP_HOME:+1}"
DOCKS="$HOME_DIR/Library/Application Support/Docks/tool/bin/docks"
PORTS="$HOME_DIR/Library/Application Support/Ports/tool/port"
# A test install gets its own Docks home inside the folder it installs into, so it can never touch the real Dock.
if [ -n "$TESTING" ]; then
  unset DOCKS_TOOL_DIR DOCKS_TRASH DOCKS_DOCK_PLIST DOCKS_NO_DOCK DOCKS_LOG
  export DOCKS_HOME="$HOME_DIR/Library/Application Support/Docks"
  export DOCKS_TEST_HOME="${DOCKS_TEST_HOME:-$HOME_DIR/Docks test}"
  export DOCKS_APPS_DIR="$HOME_DIR/Applications"
fi

close_window() { [ "${TERM_PROGRAM:-}" = "Apple_Terminal" ] && ( sleep 1; osascript -e 'tell application "Terminal" to close (every window whose name contains "Install Zulu Clock")' ) >/dev/null 2>&1 & }
say()  { echo ""; echo "▶ $1"; }
stop() { echo ""; echo "✗ $1"; echo ""; [ -n "$TESTING" ] || { read -r -n 1 -p "Press any key to close this window…"; close_window; }; exit 1; }

NEW="$(cat "$FILES/VERSION" 2>/dev/null)"
OLD="$(cat "$CODE_HOME/VERSION" 2>/dev/null)"
# Versions are compared as numbers (1.10 comes after 1.9). An older install never goes over a newer one.
vcmp() { awk -v a="$1" -v b="$2" 'BEGIN{n=split(a,x,".");m=split(b,y,".");k=(n>m?n:m);for(i=1;i<=k;i++){p=x[i]+0;q=y[i]+0;if(p<q){print -1;exit}if(p>q){print 1;exit}}print 0}'; }
if [ -n "$OLD" ] && [ -n "$NEW" ] && [ "$(vcmp "$NEW" "$OLD")" = "-1" ]; then
  stop "This is Zulu Clock $NEW, but $OLD is already installed, and $OLD is newer. Nothing was changed. Keep using $OLD, or ask Joe for a newer zip."
fi
if [ -z "$OLD" ]; then echo "Installing Zulu Clock $NEW"
elif [ "$OLD" = "$NEW" ]; then echo "Reinstalling Zulu Clock $NEW"
else echo "Updating Zulu Clock $OLD to $NEW"; fi
[ -f "$FILES/server.py" ] && [ -f "$FILES/zulu-clock.html" ] && [ -f "$FILES/shared/install-shared.sh" ] \
  || stop "The Files folder is missing something. Unzip the zip again, then double-click Install Zulu Clock inside the new folder."

# ── 1. Python ────────────────────────────────────────────────────────────────
say "Checking Python 3"
if python3 -c 'import sys; sys.exit(sys.version_info < (3, 8))' 2>/dev/null; then
  PY="$(command -v python3)"
  echo "  ✓ $("$PY" --version 2>&1)"
else
  echo "  Python 3 isn't on this Mac yet. macOS will offer to install it (the \"command line developer tools\")."
  echo "  Click Install, agree to the licence, and wait for it to finish (a few minutes)."
  echo "  Then double-click Install Zulu Clock again."
  [ -n "$TESTING" ] || xcode-select --install >/dev/null 2>&1
  stop "Install will carry on after Python is installed."
fi

# ── 2. Shared tools ──────────────────────────────────────────────────────────
say "Installing the shared tools (Docks and Ports), only where missing or older"
_out="$(HOME="$HOME_DIR" PYTHON="$PY" "$FILES/shared/install-shared.sh" 2>&1)" \
  || stop "Couldn't install the shared tools. ${_out:-Send Joe a screenshot of this window.}"
echo "$_out" | sed 's/^/  /'

# The clock's port: what the installed Ports tool says, else 8769. Anything but one whole number from 1024 to 65535
# (or no answer in 2 seconds) counts as no answer.
home_port() {
  local p
  p="$(perl -e 'alarm 2; exec @ARGV' "$PORTS" home zulu-clock 2>/dev/null)" || p=""
  case "$p" in
    [1-9][0-9][0-9][0-9]) [ "$p" -ge 1024 ] && { echo "$p"; return; } ;;
    [1-9][0-9][0-9][0-9][0-9]) [ "$p" -le 65535 ] && { echo "$p"; return; } ;;
  esac
  echo 8769
}

# ── 3. Copy ──────────────────────────────────────────────────────────────────
say "Copying Zulu Clock to your Applications folder"
if [ -z "$TESTING" ]; then  # a running clock server keeps the old version loaded; stop it only if it is this one
  for _p in $(lsof -ti "tcp:$(home_port)" -sTCP:LISTEN 2>/dev/null); do
    case "$(ps -o command= -p "$_p" 2>/dev/null)" in
      *"$CODE_HOME/server.py"*) kill "$_p" 2>/dev/null && sleep 0.4 && echo "  ✓ Stopped the running clock server (the Dock starts it again)" ;;
    esac
  done
fi
mkdir -p "$CODE_HOME" || stop "Couldn't make $CODE_HOME."
rsync -a --delete --exclude '.DS_Store' --exclude '__pycache__' --exclude '/shared' "$FILES/" "$CODE_HOME/" \
  || stop "Couldn't copy Zulu Clock to $CODE_HOME."
xattr -dr com.apple.quarantine "$CODE_HOME" 2>/dev/null  # the copy you chose to install shouldn't be blocked again
echo "  ✓ Copied"

# ── 4. The app ───────────────────────────────────────────────────────────────
# Docks (the shared Dock-app tool) makes the Zulu Clock app, its icon and its Dock icon from the dock.json in the copy
# above, and runs the clock with the Python checked above.
say "Making the Zulu Clock app"
[ -f "$DOCKS" ] || stop "The Dock tool isn't installed where expected ($DOCKS). Send Joe a screenshot of this window."
_reg="$("$PY" "$DOCKS" app list 2>/dev/null | awk -F'  ' '$1=="zulu"{print $3}')"
if [ -z "$_reg" ]; then
  _out="$("$PY" "$DOCKS" app add "$CODE_HOME" --by installer --python "$PY" 2>&1)" || stop "Couldn't make the Zulu Clock app. ${_out:-Send Joe a screenshot of this window.}"
  echo "  ✓ $_out"
elif [ "$_reg" = "$CODE_HOME" ]; then
  _out="$("$PY" "$DOCKS" app refresh zulu --by installer --python "$PY" 2>&1)" || stop "Couldn't update the Zulu Clock app. ${_out:-Send Joe a screenshot of this window.}"
  echo "  ✓ $_out"
else
  echo "  ✓ The Dock icon was left as it is, because Docks already opens Zulu Clock from $_reg."
fi
echo "  ✓ $APP_PATH"

# ── 5. Check it, rather than claim it ────────────────────────────────────────
say "Checking Zulu Clock starts"
PORT="$(home_port)"
if [ -n "$TESTING" ]; then
  PORT="${ZULU_SETUP_PORT:-}"
  [ -n "$PORT" ] || stop "A test install needs ZULU_SETUP_PORT, a free port for its check."
fi
_pid=""
_p="$(lsof -ti "tcp:$PORT" -sTCP:LISTEN 2>/dev/null | head -1)"
if [ -n "$_p" ]; then
  if [ -n "$TESTING" ]; then
    stop "Port $PORT is in use by pid $_p. The test install needs it free, and doesn't stop what isn't its own."
  fi
  echo "  Port $PORT is already answering; checking that server."
else
  _pid="$( cd "$CODE_HOME" && HOME="$HOME_DIR" "$PY" -c 'import subprocess,sys; print(subprocess.Popen([sys.executable,"server.py",sys.argv[1],sys.argv[2]],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True).pid)' "$PORT" "$CODE_HOME" )"
fi
OK=""
for _ in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15; do
  curl -s "http://127.0.0.1:$PORT/status" | grep -q '"sources"' && { OK=1; break; }
  sleep 0.4
done
PAGE_OK=""
curl -s "http://127.0.0.1:$PORT/zulu-clock.html" | grep -q 'ZULU' && PAGE_OK=1
[ -n "$_pid" ] && kill "$_pid" 2>/dev/null  # only the server this check started
[ -n "$OK" ] && [ -n "$PAGE_OK" ] || stop "Zulu Clock's server didn't answer. Take a screenshot of this window and send it to Joe."
echo "  ✓ The clock's server answers on port $PORT, and serves the page"

echo ""
if [ -z "$OLD" ]; then echo "✅ Zulu Clock $NEW is installed."; else echo "✅ Zulu Clock is up to date ($NEW)."; fi
echo "   Open it from the Dock, or from Applications › Zulu Clock in your home folder."
echo "   You can delete the zip and the unzipped folder now."
[ -z "$TESTING" ] && { open "$APP_PATH" 2>/dev/null; sleep 3; }
close_window
exit 0
