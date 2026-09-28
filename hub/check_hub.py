#!/usr/bin/env python3
"""hub/check_hub.py — best-effort liveness check across every known
communication channel between the real agents operating on FeralEcho.

Not a FeralEcho subsystem: not imported by app/ or run.py, not subject to
EDIT_FORBIDDEN_TARGETS or the Liveness Ledger — operator/session tooling,
same category as claude_relay/relay.py and codex_relay/relay.py.

Every check is independent and non-fatal: one channel being unreachable
never stops the others from being checked, and this script never blocks
waiting for a party that isn't there. See hub/README.md for the full
design rationale and why Echo isn't (and shouldn't be) a symmetric peer
here.

Appends one JSON line per channel to hub/status.jsonl. Never prints or
stores raw message content or secret values — structural facts only,
matching claude_relay/relay.py's own existing privacy rule.

Usage:
    python3 hub/check_hub.py
"""

from __future__ import annotations

import json
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HUB_DIR = Path(__file__).resolve().parent
STATUS_LOG = HUB_DIR / "status.jsonl"

ECHO_M5_LIVENESS_URL = "http://localhost:5000/admin/liveness-status"
ECHO_AIR_STATE_URL = "http://100.82.172.4:5000/state"
CODEX_M5_AIR_PEER = "100.82.172.4"
LOCAL_CLAUDE_CODEX_DATA_DIR = str(Path.home() / ".claude-codex-relay")
LOCAL_CODEX_PORT = 8767  # what the local "codex" identity is expected to bind to
HTTP_TIMEOUT_S = 5


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def append_status(channel: str, endpoints: list[str], status: str, evidence: str) -> None:
    entry = {
        "timestamp": now(),
        "checked_by": "claude-m5",
        "channel": channel,
        "endpoints": endpoints,
        "status": status,
        "evidence": evidence,
    }
    with STATUS_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"[{channel}] {status}: {evidence}")


def run_cmd(args: list[str], cwd: Path = REPO_ROOT) -> tuple[int, str]:
    try:
        result = subprocess.run(
            args, cwd=cwd, capture_output=True, text=True, timeout=HTTP_TIMEOUT_S + 3
        )
        return result.returncode, (result.stdout or "") + (result.stderr or "")
    except subprocess.TimeoutExpired:
        return -1, "subprocess timed out"
    except Exception as e:  # noqa: BLE001 - this is a best-effort checker, never fatal
        return -1, f"subprocess failed to start: {e}"


def http_get(url: str) -> tuple[int | None, str]:
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT_S) as resp:
            # /admin/liveness-status's real body is ~16KB (30 checks' worth
            # of evidence text) - a small fixed cap silently truncates valid
            # JSON into invalid JSON. 1MB bounds against something
            # unexpectedly huge while comfortably covering every real
            # endpoint this script checks.
            return resp.status, resp.read(1_000_000).decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, str(e)
    except Exception as e:  # noqa: BLE001
        return None, str(e)


def check_claude_relay() -> None:
    code, output = run_cmd(["python3", "claude_relay/relay.py", "status"])
    if code != 0:
        append_status("claude_relay", ["claude-m5", "claude-air"], "unknown",
                       f"status command exited {code}: {output[:200]}")
        return
    reachable = "reachable" in output and "UNREACHABLE" not in output
    status = "alive" if reachable else "unreachable"
    # First two lines are structural only (identity + own file size) per this
    # channel's own no-content-printing rule; safe to echo as evidence.
    evidence_lines = [ln.strip() for ln in output.splitlines() if ln.strip()][:3]
    append_status("claude_relay", ["claude-m5", "claude-air"], status, " | ".join(evidence_lines))


def check_codex_relay_m5_air() -> None:
    code, output = run_cmd([
        "python3", "codex_relay/relay.py", "--identity", "m5",
        "status", "--peer", CODEX_M5_AIR_PEER,
    ])
    reachable = "reachable" in output and "unreachable" not in output.lower().replace("Peer 100", "PEERPLACEHOLDER")
    # simpler, precise check: relay.py prints "Peer <ip>: reachable" or "Peer <ip>: unreachable (...)"
    reachable = f"Peer {CODEX_M5_AIR_PEER}: reachable" in output
    status = "alive" if reachable else ("unreachable" if code in (0, 1) else "unknown")
    evidence_lines = [ln.strip() for ln in output.splitlines() if ln.strip()]
    append_status("codex_relay", ["codex-m5", "codex-air"], status, " | ".join(evidence_lines[:4]))


def check_local_claude_codex_relay() -> None:
    secret_path = Path(LOCAL_CLAUDE_CODEX_DATA_DIR) / "secret"
    if not secret_path.exists():
        append_status("local_claude_codex_relay", ["claude-m5", "codex-m5"], "not_set_up",
                       f"no secret file at {secret_path}")
        return
    code, output = run_cmd([
        "python3", "codex_relay/relay.py", "--identity", "claude",
        "--data-dir", LOCAL_CLAUDE_CODEX_DATA_DIR, "--port", str(LOCAL_CODEX_PORT),
        "status", "--peer", "127.0.0.1",
    ])
    reachable = "reachable" in output and "unreachable" not in output.lower()
    # relay.py's own wording: "Peer <addr>: reachable" vs "unreachable (...)"
    reachable = "Peer 127.0.0.1: reachable" in output
    status = "alive" if reachable else ("unreachable" if code in (0, 1) else "unknown")
    evidence_lines = [ln.strip() for ln in output.splitlines() if ln.strip()]
    append_status("local_claude_codex_relay", ["claude-m5", "codex-m5"], status,
                   " | ".join(evidence_lines[:4]))


def check_echo_m5() -> None:
    code, body = http_get(ECHO_M5_LIVENESS_URL)
    if code == 200:
        try:
            data = json.loads(body) if body.strip().startswith("{") else {}
        except json.JSONDecodeError:
            data = {}
        all_passing = data.get("all_passing")
        stale = data.get("stale")
        evidence = f"HTTP 200, all_passing={all_passing}, stale={stale}" if data else "HTTP 200"
        append_status("echo_m5_liveness", ["echo-m5"], "alive", evidence)
    else:
        append_status("echo_m5_liveness", ["echo-m5"], "unreachable", f"HTTP status={code}, body={body[:150]!r}")


def check_echo_air() -> None:
    code, body = http_get(ECHO_AIR_STATE_URL)
    if code == 200:
        append_status("echo_air_reachability", ["echo-air"], "alive", "HTTP 200 on /state")
    else:
        append_status("echo_air_reachability", ["echo-air"], "unreachable", f"HTTP status={code}, body={body[:150]!r}")


def main() -> int:
    STATUS_LOG.parent.mkdir(parents=True, exist_ok=True)
    print(f"hub/check_hub.py — {now()}")
    checks = [
        check_claude_relay,
        check_codex_relay_m5_air,
        check_local_claude_codex_relay,
        check_echo_m5,
        check_echo_air,
    ]
    for check in checks:
        try:
            check()
        except Exception as e:  # noqa: BLE001 - one channel's failure must never stop the rest
            append_status(check.__name__, ["unknown"], "unknown", f"checker itself raised: {e}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
