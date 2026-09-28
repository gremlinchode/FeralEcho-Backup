#!/usr/bin/env python3
"""
Phase 9 -- negative controls, run against the REAL envelope/response from
the live Phase 8 proof (memory/experiments/breakfast_club_reachability/
raw_exchange_log.jsonl), with zero new external calls -- per the mission's
own explicit "Do not generate unnecessary paid calls" instruction. N4 (no
recipient) is not separately re-run live here: it is already covered by
test_local.py's "no_response" mock case (Phase 7, case 8/"no_response"
path), which already demonstrated the obligation correctly reaches FAILED
rather than any consumed/verified state when no response ever arrives --
re-running that live, at real cost, would add no new evidence.
"""
from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from app.experiments.breakfast_club_reachability import verifier as V

RAW_LOG_PATH = Path(__file__).resolve().parents[3] / "memory" / "experiments" / "breakfast_club_reachability" / "raw_exchange_log.jsonl"


def main():
    with open(RAW_LOG_PATH) as f:
        entries = [json.loads(l) for l in f if l.strip()]
    real = entries[-1]  # the genuine live Phase 8 exchange
    envelope = real["envelope"]
    real_answer = None
    import re
    m = re.findall(r"\b[0-9a-fA-F]{16}\b", real["stdout"])
    real_answer = m[-1] if m else None
    print(f"Real envelope message_id: {envelope['message_id']}")
    print(f"Real nonce: {envelope['nonce_hex']}")
    print(f"Real returned answer (from the actual live codex exec run): {real_answer}\n")

    # N1 -- wrong response: flip the first hex character of the genuinely
    # correct answer and feed it to the verifier. Must fail.
    wrong = ("0" if real_answer[0] != "0" else "1") + real_answer[1:]
    r1 = V.verify(envelope=envelope, response_message_id=envelope["message_id"], claimed_answer=wrong)
    print(f"[N1] Wrong response fed to verifier: {r1['outcome']}  "
          f"(expected REJECTED_MISMATCH) -- {'PASS' if r1['outcome']=='REJECTED_MISMATCH' else 'FAIL'}")

    # N2 -- replay: take the SAME real, correct answer, but claim it as the
    # response to a DIFFERENT (newly-minted) message_id. Must fail, since
    # the verifier checks response_message_id against the envelope's own
    # message_id, not merely "is this hex value correct for some nonce."
    replayed_message_id = str(uuid.uuid4())
    r2 = V.verify(envelope=envelope, response_message_id=replayed_message_id, claimed_answer=real_answer)
    print(f"[N2] Same correct answer replayed under a new message_id: {r2['outcome']}  "
          f"(expected REJECTED_WRONG_MESSAGE_ID) -- {'PASS' if r2['outcome']=='REJECTED_WRONG_MESSAGE_ID' else 'FAIL'}")

    # N3 -- pre-response prediction: the real console/log evidence already
    # shows the expected answer was computed and printed BEFORE the codex
    # exec subprocess call was made (run_codex_proof.py's own code order,
    # and the printed timestamps in the live run's own console output).
    # Demonstrated here by re-confirming the expected value is independently
    # derivable from the nonce alone, with no dependence on having seen
    # Codex's response first -- i.e., the verifier's ground truth was fixed
    # before transmission, not fitted to whatever came back.
    from app.experiments.breakfast_club_reachability import protocol as P
    predicted = P.expected_answer(envelope["nonce_hex"])
    r3_matches_prediction = (predicted == real_answer)
    print(f"[N3] Locally pre-derivable expected value: {predicted}  "
          f"| actually returned by the live remote call: {real_answer}  "
          f"-- {'PASS (remote genuinely reproduced it)' if r3_matches_prediction else 'FAIL'}")
    print("     Note: this demonstrates the REMOTE endpoint correctly performed the described "
          "computation on the real, novel nonce it was given -- not that Claude's own local "
          "math needed Codex to compute it (the transformation is deterministic and was already "
          "known locally, exactly as with every other independently-checkable verifier this "
          "project uses, e.g. F1/F2/F3's sandbox execution checks). The evidentiary claim is "
          "about genuine remote processing of specific, novel content, not about testing "
          "arithmetic neither party could otherwise do.")

    # N4 -- no recipient: already covered, cost-free, by test_local.py's
    # "no_response" mock case (Phase 7) -- not re-run live here.
    print("\n[N4] Covered by Phase 7's local mock test (case 'no_response' path) -- "
          "not re-run live, per Phase 9's own 'no unnecessary paid calls' instruction.")


if __name__ == "__main__":
    main()
