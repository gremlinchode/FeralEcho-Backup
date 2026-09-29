#!/bin/zsh
# Supervises the "codex" identity half of the local Claude<->Codex relay
# loopback (127.0.0.1:8767). See start_local_relay_claude.sh's own header
# comment for the full design rationale -- this is its exact mirror image
# for the other identity, deliberately its own independent process/script/
# LaunchAgent rather than sharing one supervisor with the "claude" side.
set -e
cd "$(dirname "$0")/.."  # repo root

SECRET_FILE="$HOME/.claude-codex-relay/secret"
LOG="$HOME/.claude-codex-relay/launchd_codex.log"

if [ ! -f "$SECRET_FILE" ]; then
    echo "[relay-supervisor] $(date -u +%Y-%m-%dT%H:%M:%SZ) No secret file at $SECRET_FILE -- refusing to start. This relay identity was never bootstrapped; see codex_relay/README.md." | tee -a "$LOG"
    exit 1
fi

while true; do
    echo "[relay-supervisor] $(date -u +%Y-%m-%dT%H:%M:%SZ) Starting codex-identity relay server" | tee -a "$LOG"
    export CODEX_RELAY_SECRET="$(cat "$SECRET_FILE")"
    python3 codex_relay/relay.py --identity codex --data-dir "$HOME/.claude-codex-relay" --port 8767 \
        serve --bind 127.0.0.1 --peer-identity claude 2>&1 | tee -a "$LOG"
    code=${pipestatus[1]}
    echo "[relay-supervisor] $(date -u +%Y-%m-%dT%H:%M:%SZ) codex-identity relay exited with code ${code}. Restarting in 10s..." | tee -a "$LOG"
    sleep 10
done
