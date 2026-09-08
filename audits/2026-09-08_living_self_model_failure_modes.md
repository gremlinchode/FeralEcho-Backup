# Living Self-Model — Failure Modes (Phase 16)

| Failure mode | Present in this implementation? | Evidence |
|---|---|---|
| Hollow write | No — `record_claim()`'s writes are read by `_build_self_model_claims()`, confirmed live. |
| Hollow reader | **Partially yes** — the claim IS retrieved into context (confirmed), but does not reliably change the main generated answer (see validation doc). This is the mechanism's real, honest limitation, not a false claim of success. |
| False verification | Not observed — Check 5's 5 test cases (4 canary + 1 extra uncertainty case) all discriminated correctly after the one real bug was found and fixed. |
| Stale truth | Not yet tested — no contradiction-lifecycle exists, so a claim once written as `verified: false` has no mechanism to be promoted/retired if circumstances genuinely change. Real gap, stated in the design doc. |
| Self-confirmation loop | Structurally prevented — `proposed_by != verified_by` refuses any claim where Echo's own text would count as its own verification. Tested directly (the refused-write case). |
| Documentation leakage | Not applicable here — this mechanism reads `self_model.json`/the claims ledger, not CLAUDE.md/README content. |
| Context contamination | Ruled out for the Test 2 result specifically — a genuinely fresh `conversation_id` was used, with no prior turns in that session; the claim history came only from the durable ledger, confirmed by direct inspection of what `get_structural_self_facts()` actually returned for that exact call. |
| Prompt parroting | Not conclusively distinguishable from real reasoning in this small a sample — Echo's language in Test 2 doesn't literally quote the injected claims-ledger line, but also doesn't correctly use it; this is closer to "context present but not weighted" than "context copied verbatim." |
| Overfitting to RiverBrain | Real, disclosed risk — `KNOWN_SUBJECTS` covers 5 hardcoded subjects; a 6th real subsystem would need someone to remember to add it (the exact CATEGORIES/TASK_TYPE_MAP pure-absence failure shape), only partially mitigated by the new Liveness Ledger check (which validates the existing entries stay correct, not that the set is complete). |
| Silent drift | Actively defended against, and tested: the new `self_model_claims_integrity` Liveness Ledger check would fail loudly (`[LIVENESS-ALERT]`) if `KNOWN_SUBJECTS`'s dotted paths stop matching `self_model.json`'s real shape — confirmed via the drifted-schema canary case, run for real. |
