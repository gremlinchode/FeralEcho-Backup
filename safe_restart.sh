#!/bin/zsh
# Safe replacement for the manual "kill $(lsof -ti :5000) && python run.py"
# restart idiom documented in CLAUDE.md's "Starting the System" section.
#
# Why this exists: start_echo.sh runs an independent watchdog loop that
# restarts run.py automatically on exit/crash. If a human (or a Claude Code
# session) manually kills port 5000 and starts python run.py by hand while
# that watchdog is *also* alive, both supervisors race to reinitialize the
# same process and shared state files (FAISS index, self_edit_cooldown.json,
# log_retention_state.json, etc.) at nearly the same moment. This has
# happened for real, more than once, on both this machine and the 2020 Intel
# MacBook ("Ark") — see CLAUDE.md Finding 51, which documents a real crash
# and a duplicate log rotation caused by exactly this collision. The fix
# isn't "be more careful" (that has already failed repeatedly for two
# different operators across two machines) — it's a cheap check at the point
# of intervention, since nothing currently warns you before the collision.
#
# Usage:
#   ./safe_restart.sh            # checks for a watchdog first, refuses if found
#   ./safe_restart.sh --force    # proceeds anyway (you accept the collision risk)

cd "$(dirname "$0")"

WATCHDOG_PIDS=$(pgrep -f "start_echo.sh")

if [ -n "$WATCHDOG_PIDS" ]; then
    echo "[SAFE-RESTART-BLOCKED] start_echo.sh watchdog is already running (PID(s): $WATCHDOG_PIDS)."
    echo ""
    echo "Manually killing port 5000 and starting run.py by hand while this"
    echo "watchdog is alive causes two supervisors to race on the same restart —"
    echo "this has caused a real crash and a duplicate log rotation before"
    echo "(CLAUDE.md Finding 51). Pick one:"
    echo ""
    echo "  (a) Let the watchdog handle it — just clear the port and step back,"
    echo "      it will restart run.py within 10s on its own:"
    echo "        kill \$(lsof -ti :5000)"
    echo ""
    echo "  (b) Take manual control — stop the watchdog first, then start"
    echo "      run.py yourself:"
    echo "        kill $WATCHDOG_PIDS"
    echo "        python run.py"
    echo ""
    echo "Refusing to proceed. Re-run with --force if you're certain you want"
    echo "to restart anyway (the collision risk is on you at that point)."
    if [ "$1" != "--force" ]; then
        exit 1
    fi
    echo ""
    echo "[SAFE-RESTART] --force given, proceeding anyway."
fi

echo "[SAFE-RESTART] No conflicting watchdog detected. Restarting..."
PID=$(lsof -t -i :5000)
if [ -n "$PID" ]; then
    kill "$PID" 2>/dev/null
    sleep 1
else
    echo "[SAFE-RESTART] Port 5000 was not in use."
fi
exec python run.py
