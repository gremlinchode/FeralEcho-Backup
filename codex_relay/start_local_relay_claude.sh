#!/bin/zsh
# Supervises the "claude" identity half of the local Claude<->Codex relay
# loopback (127.0.0.1:8765). Deliberately separate from start_echo.sh and
# from the "codex" identity's own script (start_local_relay_codex.sh) --
# see audits/2026-09-29_relay_hub_reliability_repair.md Phase 7: relay
# supervision must stay fully independent of Echo's own lifecycle, and each
# relay identity is its own independently-restartable process, not one
# script owning both.
#
# The shared secret is read from its existing, already-permission-protected
# file at runtime -- never embedded in this script or in the LaunchAgent
# plist that invokes it, per Phase 8's explicit requirement.
set -e
cd "$(dirname "$0")/.."  # repo root

SECRET_FILE="$HOME/.claude-codex-relay/secret"
LOG="$HOME/.claude-codex-relay/launchd_claude.log"

if [ ! -f "$SECRET_FILE" ]; then
    echo "[relay-supervisor] $(date -u +%Y-%m-%dT%H:%M:%SZ) No secret file at $SECRET_FILE -- refusing to start. This relay identity was never bootstrapped; see codex_relay/README.md." | tee -a "$LOG"
    exit 1
fi

while true; do
    echo "[relay-supervisor] $(date -u +%Y-%m-%dT%H:%M:%SZ) Starting claude-identity relay server" | tee -a "$LOG"
    export CODEX_RELAY_SECRET="$(cat "$SECRET_FILE")"
    python3 codex_relay/relay.py --identity claude --data-dir "$HOME/.claude-codex-relay" --port 8765 \
        serve --bind 127.0.0.1 --peer-identity codex 2>&1 | tee -a "$LOG"
    code=${pipestatus[1]}
    echo "[relay-supervisor] $(date -u +%Y-%m-%dT%H:%M:%SZ) claude-identity relay exited with code ${code}. Restarting in 10s..." | tee -a "$LOG"
    sleep 10
done
