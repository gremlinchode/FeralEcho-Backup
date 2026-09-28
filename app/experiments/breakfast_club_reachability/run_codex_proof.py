#!/usr/bin/env python3
"""
Phase 8 -- ONE minimal live proof, against the one route selected in
Phase 3 (audits/2026-09-24_operation_breakfast_club_reachability_proof_of_capability.md
Section on Phase 3): the already-authenticated `codex` CLI, non-interactive
`codex exec` mode. No new credential, no billing change, no account
connection, no browser automation -- see that report for the full
authorization reasoning, including the direct precedent this follows
(research/COLLABORATOR_SUBSTITUTION_CODEX_PILOT.md, this exact project,
which already made a live `codex exec` call under identical reasoning).

Never reads, prints, or logs any credential -- `codex` handles its own
already-established OAuth session; this script only ever passes plain
prompt text as a subprocess argument and captures stdout/stderr.

usage: python -B run_codex_proof.py
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from app.experiments.breakfast_club_reachability import protocol as P
from app.experiments.breakfast_club_reachability import verifier as V

OUT_DIR = Path(__file__).resolve().parents[3] / "memory" / "experiments" / "breakfast_club_reachability"
LEDGER_PATH = OUT_DIR / "obligation_ledger.jsonl"
RAW_LOG_PATH = OUT_DIR / "raw_exchange_log.jsonl"

MISSION_ID = "breakfast-club-reachability-proof-001"
CODEX_TIMEOUT_S = 120


def main():
    ledger = P.ObligationLedger(LEDGER_PATH)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # --- P1: Claude-originated novel information, generated locally, AFTER
    # the protocol (protocol.py) was frozen. ---
    nonce = P.generate_nonce()
    message_id = str(uuid.uuid4())
    envelope = P.build_envelope(
        message_id=message_id, sender="claude-m5", intended_recipient="codex-cli-local",
        mission_id=MISSION_ID, reason_for_contact="Operation Breakfast Club reachability proof-of-capability",
        nonce_hex=nonce,
    )
    expected = P.expected_answer(nonce)

    print(f"[P1] Nonce generated locally (CSPRNG): {nonce}")
    print(f"[P1] Nonce sha256 (recorded before transmission): {envelope['nonce_sha256']}")
    print(f"[P1] Expected answer (computed independently, NEVER sent to the recipient): {expected}")
    print(f"[protocol] message_id={message_id}  mission_id={MISSION_ID}")

    ledger.record(message_id=message_id, owner="claude", evidence=f"envelope={json.dumps(envelope)}",
                   previous_state=None, new_state="CREATED")
    ledger.record(message_id=message_id, owner="claude", evidence="dispatch queued",
                   previous_state="CREATED", new_state="QUEUED")

    prompt = P.build_challenge_prompt(nonce)

    # --- P2: independent delivery -- Claude Code invokes the already-
    # authenticated `codex` CLI directly; no human copies or retypes
    # anything between here and the subprocess call. ---
    ledger.record(message_id=message_id, owner="claude",
                   evidence=f"invoking codex exec, prompt_len={len(prompt)}",
                   previous_state="QUEUED", new_state="SENT")

    t0 = time.time()
    try:
        result = subprocess.run(
            ["codex", "exec", prompt],
            capture_output=True, text=True, timeout=CODEX_TIMEOUT_S,
        )
        elapsed = time.time() - t0
    except subprocess.TimeoutExpired:
        elapsed = time.time() - t0
        ledger.record(message_id=message_id, owner="claude",
                       evidence=f"codex exec timed out after {elapsed:.1f}s",
                       previous_state="SENT", new_state="FAILED")
        print(f"[P2/FAIL] codex exec timed out after {elapsed:.1f}s. No response to consume.")
        _write_raw_log(message_id, envelope, None, None, elapsed, "TIMEOUT")
        return 1
    except FileNotFoundError:
        ledger.record(message_id=message_id, owner="claude", evidence="codex binary not found",
                       previous_state="SENT", new_state="FAILED")
        print("[P2/FAIL] codex CLI not found on PATH.")
        return 1

    stdout = result.stdout or ""
    stderr = result.stderr or ""
    returncode = result.returncode

    print(f"[P2] codex exec returned in {elapsed:.1f}s, exit code {returncode}")

    _write_raw_log(message_id, envelope, stdout, stderr, elapsed, f"exit={returncode}")

    if returncode != 0:
        ledger.record(message_id=message_id, owner="claude",
                       evidence=f"codex exec nonzero exit {returncode}; stderr_len={len(stderr)}",
                       previous_state="SENT", new_state="FAILED")
        print("[P2/FAIL] codex exec exited nonzero. Real, honest negative result -- not treated as success.")
        print("--- stderr (first 2000 chars) ---")
        print(stderr[:2000])
        return 1

    # --- P3/P4: reasoning-level transformation actually occurred remotely
    # (not merely echoed), and the resulting answer returned to software
    # on this machine -- captured here in stdout, no human retyped it. ---
    ledger.record(message_id=message_id, owner="codex", evidence="process accepted and ran",
                   previous_state="SENT", new_state="DELIVERED_OR_ACCEPTED")
    ledger.record(message_id=message_id, owner="codex", evidence="remote reasoning/processing occurred",
                   previous_state="DELIVERED_OR_ACCEPTED", new_state="REMOTE_PROCESSING")
    ledger.record(message_id=message_id, owner="codex", evidence="response produced (stdout captured)",
                   previous_state="REMOTE_PROCESSING", new_state="RESPONSE_CREATED")
    ledger.record(message_id=message_id, owner="claude", evidence="raw exchange log written to disk",
                   previous_state="RESPONSE_CREATED", new_state="RESPONSE_DURABLE")
    ledger.record(message_id=message_id, owner="claude", evidence="stdout captured by this local process",
                   previous_state="RESPONSE_DURABLE", new_state="RETURNED")

    # Extract a claimed answer from raw stdout -- codex exec's own output
    # includes narration/formatting around the model's final text; take the
    # last line that looks like a bare 16-char hex token, since the prompt
    # explicitly asked for only that. This extraction is NOT part of the
    # verifier -- the verifier (verifier.py) independently re-validates
    # shape and correctness regardless of what this heuristic finds.
    claimed_answer = _extract_hex_answer(stdout)
    print(f"[P4] Extracted candidate answer from codex's real response: {claimed_answer!r}")

    # --- P5: explicit, separate consumption step (never automatic on
    # fetch -- see test_local.py case 11 for the harness-level proof of
    # this same discipline). ---
    ledger.record(message_id=message_id, owner="claude", evidence="explicit consumption step invoked",
                   previous_state="RETURNED", new_state="CLAUDE_CONSUMED")

    # --- P6: independent, deterministic, non-LLM verification. ---
    verify_result = V.verify(envelope=envelope, response_message_id=message_id,
                              claimed_answer=claimed_answer)
    print(f"[P6] Verifier result: {verify_result}")

    if verify_result["outcome"] == "VERIFIED":
        ledger.record(message_id=message_id, owner="verifier", evidence=str(verify_result),
                       previous_state="CLAUDE_CONSUMED", new_state="VERIFIED")
        ledger.record(message_id=message_id, owner="claude", evidence="obligation closed",
                       previous_state="VERIFIED", new_state="CLOSED")
        print("\n[RESULT] VERIFIED -- the returned answer matches the independently "
              "computed expected value. The response genuinely depended on the "
              "specific, novel nonce generated locally after the protocol was frozen.")
    else:
        ledger.record(message_id=message_id, owner="verifier", evidence=str(verify_result),
                       previous_state="CLAUDE_CONSUMED", new_state="FAILED")
        print(f"\n[RESULT] NOT VERIFIED ({verify_result['outcome']}) -- a real, honest "
              f"negative result, not smoothed over.")

    # --- P7: durable evidence -- already written throughout via the ledger
    # and the raw exchange log; print the final summary for the report. ---
    print(f"\nLedger: {LEDGER_PATH}")
    print(f"Raw exchange log: {RAW_LOG_PATH}")
    return 0 if verify_result["outcome"] == "VERIFIED" else 2


def _extract_hex_answer(stdout: str) -> "str | None":
    import re
    candidates = re.findall(r"\b[0-9a-fA-F]{16}\b", stdout)
    return candidates[-1] if candidates else None


def _write_raw_log(message_id, envelope, stdout, stderr, elapsed, status):
    entry = {
        "message_id": message_id,
        "envelope": envelope,
        "prompt": P.build_challenge_prompt(envelope["nonce_hex"]),
        "stdout": stdout,
        "stderr": stderr,
        "elapsed_s": round(elapsed, 2),
        "status": status,
        "logged_at": P.now_iso(),
    }
    with open(RAW_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


if __name__ == "__main__":
    sys.exit(main())
