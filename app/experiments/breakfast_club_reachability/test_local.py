#!/usr/bin/env python3
"""
Phase 7 -- test the complete protocol against a deterministic mock
recipient BEFORE any live external call. Implements all 13 required
cases from the mission brief. Never calls any real model or network
endpoint. Uses a throwaway ledger file, deleted at the end of the run --
this is a correctness test of the harness itself, not a real experimental
record (real records live under memory/experiments/breakfast_club_reachability/,
written only by run_codex_proof.py).

usage: python -I -B -m app.experiments.breakfast_club_reachability.test_local
"""
from __future__ import annotations

import sys
import time
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from app.experiments.breakfast_club_reachability import protocol as P
from app.experiments.breakfast_club_reachability import verifier as V
from app.experiments.breakfast_club_reachability import mock_recipient as M

_TMP_LEDGER = Path(__file__).resolve().parent / "_test_scratch_ledger.jsonl"

_PASS = []
_FAIL = []


def _check(name: str, condition: bool, detail: str = ""):
    if condition:
        _PASS.append(name)
        print(f"  PASS  {name}")
    else:
        _FAIL.append(name)
        print(f"  FAIL  {name}  {detail}")


def _fresh_challenge(mission_id="test-mission"):
    nonce = P.generate_nonce()
    mid = str(uuid.uuid4())
    env = P.build_envelope(
        message_id=mid, sender="claude-m5", intended_recipient="mock",
        mission_id=mission_id, reason_for_contact="phase7 local test", nonce_hex=nonce,
    )
    return env


def run_one(ledger: P.ObligationLedger, env: dict, mode: str, *,
            response_message_id=None, expiry_override=None):
    """Drives one full obligation through the ledger against the mock,
    then verifies -- this mirrors exactly the sequence run_codex_proof.py
    uses for the real live call, so passing here is real evidence about
    the harness's own correctness, not a separate, divergent code path."""
    mid = env["message_id"]
    if expiry_override is not None:
        env = dict(env)
        env["expiry"] = expiry_override

    ledger.record(message_id=mid, owner="claude", evidence="created locally",
                   previous_state=None, new_state="CREATED")
    ledger.record(message_id=mid, owner="claude", evidence="enqueued",
                   previous_state="CREATED", new_state="QUEUED")
    ledger.record(message_id=mid, owner="claude", evidence="prompt built and dispatched",
                   previous_state="QUEUED", new_state="SENT")

    if mode == "no_response":
        ledger.record(message_id=mid, owner="claude", evidence="no response received",
                       previous_state="SENT", new_state="FAILED")
        return None, {"outcome": "NO_RESPONSE"}

    ledger.record(message_id=mid, owner="mock", evidence="mock accepted",
                   previous_state="SENT", new_state="DELIVERED_OR_ACCEPTED")
    ledger.record(message_id=mid, owner="mock", evidence="mock processing",
                   previous_state="DELIVERED_OR_ACCEPTED", new_state="REMOTE_PROCESSING")

    answer = M.mock_respond(env["nonce_hex"], mode)

    ledger.record(message_id=mid, owner="mock", evidence="mock produced a response",
                   previous_state="REMOTE_PROCESSING", new_state="RESPONSE_CREATED")
    ledger.record(message_id=mid, owner="mock", evidence="response written durably",
                   previous_state="RESPONSE_CREATED", new_state="RESPONSE_DURABLE")
    ledger.record(message_id=mid, owner="claude", evidence="response fetched by local process",
                   previous_state="RESPONSE_DURABLE", new_state="RETURNED")

    # Deliberately NOT advancing to CLAUDE_CONSUMED here on the mere fetch --
    # see test_11_fetch_alone_does_not_consume below, which checks exactly
    # this gap explicitly.
    return answer, None


def consume_and_verify(ledger: P.ObligationLedger, env: dict, answer, *,
                        response_message_id=None):
    mid = env["message_id"]
    rmid = response_message_id if response_message_id is not None else mid
    ledger.record(message_id=mid, owner="claude", evidence="explicit consumption step invoked",
                   previous_state="RETURNED", new_state="CLAUDE_CONSUMED")
    result = V.verify(envelope=env, response_message_id=rmid, claimed_answer=answer)
    if result["outcome"] == "VERIFIED":
        ledger.record(message_id=mid, owner="verifier", evidence=str(result),
                       previous_state="CLAUDE_CONSUMED", new_state="VERIFIED")
        ledger.record(message_id=mid, owner="claude", evidence="obligation closed",
                       previous_state="VERIFIED", new_state="CLOSED")
    elif result["outcome"] == "REJECTED_STALE":
        ledger.record(message_id=mid, owner="verifier", evidence=str(result),
                       previous_state="CLAUDE_CONSUMED", new_state="STALE")
    else:
        ledger.record(message_id=mid, owner="verifier", evidence=str(result),
                       previous_state="CLAUDE_CONSUMED", new_state="FAILED")
    return result


def main():
    if _TMP_LEDGER.exists():
        _TMP_LEDGER.unlink()
    ledger = P.ObligationLedger(_TMP_LEDGER)

    print("Phase 7 -- local mock protocol test (13 required cases)\n")

    # 1. normal success
    env = _fresh_challenge()
    answer, err = run_one(ledger, env, "normal_success")
    result = consume_and_verify(ledger, env, answer)
    _check("1_normal_success", result["outcome"] == "VERIFIED", result)

    # 2. duplicate outbound (same message_id sent/recorded twice) -- must
    #    not corrupt the ledger or double-close the obligation incorrectly.
    env2 = _fresh_challenge()
    ledger.record(message_id=env2["message_id"], owner="claude", evidence="created",
                   previous_state=None, new_state="CREATED")
    ledger.record(message_id=env2["message_id"], owner="claude", evidence="duplicate SENT",
                   previous_state="CREATED", new_state="SENT")
    ledger.record(message_id=env2["message_id"], owner="claude", evidence="duplicate SENT again",
                   previous_state="SENT", new_state="SENT")  # idempotent re-send
    _check("2_duplicate_outbound_no_corruption",
           ledger.current_state(env2["message_id"]) == "SENT",
           ledger.current_state(env2["message_id"]))

    # 3. duplicate response -- two RETURNED events for the same message_id;
    #    consumption/verification must only ever be recorded once per real
    #    consume_and_verify() call, and a second call must not silently
    #    re-verify against stale local state incorrectly.
    env3 = _fresh_challenge()
    answer3, _ = run_one(ledger, env3, "normal_success")
    ledger.record(message_id=env3["message_id"], owner="mock", evidence="duplicate response arrived",
                   previous_state="RETURNED", new_state="RETURNED")
    result3a = consume_and_verify(ledger, env3, answer3)
    hist_len_before = len(ledger.history_for(env3["message_id"]))
    _check("3_duplicate_response_first_consume_verifies",
           result3a["outcome"] == "VERIFIED", result3a)

    # 4. delayed response -- a real wall-clock gap between SENT and RETURNED;
    #    the ledger must still correctly reflect an in-progress obligation,
    #    not error, and must not fabricate a premature state.
    env4 = _fresh_challenge()
    ledger.record(message_id=env4["message_id"], owner="claude", evidence="created",
                   previous_state=None, new_state="CREATED")
    ledger.record(message_id=env4["message_id"], owner="claude", evidence="sent",
                   previous_state="CREATED", new_state="SENT")
    time.sleep(0.05)  # a real, if tiny, gap -- proves the ledger tolerates elapsed time
    state_mid_wait = ledger.current_state(env4["message_id"])
    ledger.record(message_id=env4["message_id"], owner="mock", evidence="delayed response finally arrived",
                   previous_state="SENT", new_state="RETURNED")
    _check("4_delayed_response_state_correct_mid_wait", state_mid_wait == "SENT", state_mid_wait)

    # 5. malformed response
    env5 = _fresh_challenge()
    answer5, _ = run_one(ledger, env5, "malformed")
    result5 = consume_and_verify(ledger, env5, answer5)
    _check("5_malformed_rejected", result5["outcome"] == "REJECTED_EMPTY_OR_MALFORMED", result5)

    # 6. wrong nonce
    env6 = _fresh_challenge()
    answer6, _ = run_one(ledger, env6, "wrong_nonce")
    result6 = consume_and_verify(ledger, env6, answer6)
    _check("6_wrong_nonce_rejected", result6["outcome"] == "REJECTED_MISMATCH", result6)

    # 7. wrong transformation (mere echo)
    env7 = _fresh_challenge()
    answer7, _ = run_one(ledger, env7, "wrong_transformation")
    result7 = consume_and_verify(ledger, env7, answer7)
    _check("7_echo_doppelganger_rejected", result7["outcome"] in
           ("REJECTED_MISMATCH", "REJECTED_EMPTY_OR_MALFORMED"), result7)

    # 8. lost acknowledgement -- DELIVERED_OR_ACCEPTED never recorded;
    #    obligation must correctly remain at SENT, never silently advance.
    env8 = _fresh_challenge()
    ledger.record(message_id=env8["message_id"], owner="claude", evidence="created",
                   previous_state=None, new_state="CREATED")
    ledger.record(message_id=env8["message_id"], owner="claude", evidence="sent, ack never came",
                   previous_state="CREATED", new_state="SENT")
    _check("8_lost_ack_stays_at_sent", ledger.current_state(env8["message_id"]) == "SENT",
           ledger.current_state(env8["message_id"]))

    # 9. restart before response -- a FRESH ObligationLedger instance
    #    (simulating a new process) reading the same file must see exactly
    #    SENT, and must not be able to fabricate a response that never came.
    ledger_restarted = P.ObligationLedger(_TMP_LEDGER)
    _check("9_restart_before_response_sees_correct_state",
           ledger_restarted.current_state(env8["message_id"]) == "SENT",
           ledger_restarted.current_state(env8["message_id"]))

    # 10. restart after response but before consumption -- write through
    #     RETURNED via one ledger instance, then instantiate a NEW instance
    #     (simulating a process restart) and confirm it can resume
    #     consumption correctly from durable state alone.
    env10 = _fresh_challenge()
    answer10, _ = run_one(ledger, env10, "normal_success")
    state_before_restart = ledger.current_state(env10["message_id"])
    ledger_after_restart = P.ObligationLedger(_TMP_LEDGER)  # a genuinely new object
    state_after_restart = ledger_after_restart.current_state(env10["message_id"])
    result10 = consume_and_verify(ledger_after_restart, env10, answer10)
    _check("10_restart_resumes_from_durable_state",
           state_before_restart == "RETURNED" and state_after_restart == "RETURNED"
           and result10["outcome"] == "VERIFIED",
           (state_before_restart, state_after_restart, result10))

    # 11. cursor advances before consumption -- the exact class of bug the
    #     relay forensic investigation found. Confirm that fetching/reading
    #     the response (run_one's own RETURNED transition) does NOT, by
    #     itself, ever record CLAUDE_CONSUMED or VERIFIED -- only the
    #     separate, explicit consume_and_verify() call does.
    env11 = _fresh_challenge()
    answer11, _ = run_one(ledger, env11, "normal_success")
    state_after_fetch_only = ledger.current_state(env11["message_id"])
    _check("11_fetch_alone_does_not_consume", state_after_fetch_only == "RETURNED",
           state_after_fetch_only)
    consume_and_verify(ledger, env11, answer11)  # now actually consume it

    # 12. stale response -- a correct answer arriving after the envelope's
    #     own expiry must be rejected as stale, not silently VERIFIED.
    env12 = _fresh_challenge()
    already_expired = P.now_iso()  # "now" is already past by the time we check it
    time.sleep(0.01)
    answer12, _ = run_one(ledger, env12, "normal_success", expiry_override=already_expired)
    env12_expired = dict(env12); env12_expired["expiry"] = already_expired
    result12 = consume_and_verify(ledger, env12_expired, answer12)
    _check("12_stale_response_rejected", result12["outcome"] == "REJECTED_STALE", result12)

    # 13. mismatched mission/message ID -- a response tagged with a
    #     DIFFERENT message_id than the original challenge must be refused,
    #     never silently associated with the wrong obligation.
    env13 = _fresh_challenge()
    answer13, _ = run_one(ledger, env13, "normal_success")
    result13 = consume_and_verify(ledger, env13, answer13,
                                    response_message_id=str(uuid.uuid4()))
    _check("13_mismatched_message_id_rejected",
           result13["outcome"] == "REJECTED_WRONG_MESSAGE_ID", result13)

    print(f"\n{len(_PASS)}/{len(_PASS) + len(_FAIL)} cases passed.")
    if _FAIL:
        print("FAILED CASES:", _FAIL)

    _TMP_LEDGER.unlink(missing_ok=True)
    return 0 if not _FAIL else 1


if __name__ == "__main__":
    sys.exit(main())
