# E5-mini G0 — Independent Reconciliation of Codex's Requalification-Attack Report (A1–A5)

**Mission**: independently reproduce/falsify Codex's third adversarial pass (`audits/2026-09-16_e5_mini_g0_codex_requalification_attack.md`, findings A1–A5) against the just-repaired apparatus, using my own independently-constructed attacks — not a rerun of Codex's own reproduction code. Do not fix anything.

**Scope discipline observed**: zero edits to `app/experiments/e5_mini/**`. All attacks built and run from `/private/tmp/e5r_scratch_fixed/` scratch scripts against the real, unmodified package via direct import. No git state touched.

**Source verified directly, not taken from Codex's or the repair report's prose**: `checker.py` (full read), `mock.py` (full read), `accounting.py` (full read), `builder.py::solve_query` signature and reuse branch, `orchestrator.py` import/arm-order structure — all citations below are to line ranges I read myself in this mission.

---

## 1. Summary verdict

**All 5 findings CONFIRMED, via independently-constructed attacks distinct in mechanism from Codex's own.** One (#2) also disproves the single most attractive unifying hypothesis for this whole class of bug: "identity-preserving provenance" explains 4 of 5, but not #2, which is a pure content/information-flow gap orthogonal to identity. The stronger, generalized invariant needed is two-part, not one.

| # | Finding (mission brief label) | My construction | Result |
|---|---|---|---|
| 1 | Balanced retry/omission | Real fixture-level omission (query removed before `run_family` runs) + a genuinely untracked extra `mock_solve()` invocation that bypasses `solve_query`'s ledger recording entirely | **CONFIRMED** — aggregate witness match holds (56/56); omission is invisible unless a correct `expected_slots` is supplied |
| 2 | Shared-state / N information leak | A shared mutable cache inside `extract_convention` itself (not `choose_action` — see the NOT-REPRODUCED note below) | **CONFIRMED** — 8/8 real N-arm rows leak the real convention token into `response_text`; zero violations of any kind |
| 3 | Post-hoc response substitution | Real-time query-text substitution at generation time via patching `orchestrator.solve_query`'s module-bound name (not post-hoc ledger editing) | **CONFIRMED** — two P-arm related-query rows, distinct `generation_id`s, byte-identical `response_text`; zero violations |
| 4 | Cross-run ledger/witness pairing | Two genuinely independent real `run_family` executions (different families, different content); ledger A cross-paired with run B's real witness count | **CONFIRMED** — `verify_execution_witness` has zero identity binding; cross-run pairing reports a clean match |
| 5 | Deleted paired-world scoring (gen_id_to_slot collision) | Deleted one paired-world's entire evidence (SolverCallRecord + its OracleReference) — the world I independently determined, from the dict-comprehension's insertion-order semantics, would be silently overwritten | **CONFIRMED, with a load-bearing nuance** — invisible to the *unconditional* check always; caught by `check_assignment_completeness` only when the caller supplies a correct `expected_slots`, which no production code path ever does |

---

## 2. Finding #1 — Balanced retry/omission

**Root cause, traced directly**: `verify_execution_witness()` (`accounting.py:48-81`) compares two bare integers — `actual_solver_invocations` (a witness count handed in by the caller) against `distinct_generations_total` (`reconcile()`, `accounting.py:10-45`, derived from `ledger.distinct_generation_ids()`). Neither side carries any per-slot identity. A real omission (a slot that is never solved at all) decrements both the true invocation count and the true generation count by exactly the same amount as an independent, untracked extra invocation increments them — the aggregate stays balanced by construction, not by coincidence.

**First attempt (recorded for completeness, informative on its own)**: I initially simulated "omission" by deleting a `SolverCallRecord` *after* a real invocation had already occurred. This is a different failure shape (closer to #5) — the witness counter had already counted the real call, so deleting its ledger row *decreased* `distinct_generations_total` without decreasing `actual_solver_invocations`, correctly producing a MISMATCH (`61 vs 60`). This is a genuine, useful negative result: **post-hoc deletion of a completed invocation's evidence is caught by the aggregate witness check** — the vulnerability requires a *true* never-attempted omission, not a deletion.

**Corrected construction**: `w0.related_queries.pop(3)` before `run_family` runs (the query never enters the run at all — zero witness increment, zero generation), paired with a `mock.mock_solve` wrapper that, on the first real P-arm related call, fires one additional, completely independent `mock.mock_solve()` call directly (bypassing `solve_query`'s ledger-recording path entirely — a real invocation with **zero** corresponding ledger row of any kind).

**Result**: `actual_solver_invocations=56`, `expected_distinct_generations=56`, `execution_matches_declaration=True`. Zero violation codes with no `expected_slots`. With `expected_slots=[(family, world, "P", omitted_query_id)]`, `MISSING_ASSIGNED_SLOT` fires correctly.

**Verdict: CONFIRMED.** The aggregate accounting layer (`verify_execution_witness`/`reconcile`) is *structurally* incapable of detecting a balanced omission+extra-invocation pair — this is inherent to comparing two counts with no identity binding, not a coding oversight fixable by tightening those two functions. Detection is possible only through `check_assignment_completeness`, and only when supplied a complete, correct, independently-sourced `expected_slots` (see §6).

---

## 3. Finding #2 — Shared-state / N information leak

**Channel identified precisely, from source, before attacking**: `mock_solve()` (`mock.py:232-255`) computes `extracted = strategy.extract_convention(memory_text)` (line 246) then builds the response directly from `extracted` (`conv = extracted or "UNKNOWN_CONV"`, line 249) — `choose_action`'s return value only ever selects FAMILY/GENERAL/ABSTAIN; it has no path back into the response text's convention substring at all.

**First attempt (NOT REPRODUCED via this specific channel, recorded rather than discarded)**: I first built a shared cache inside `choose_action`, on the theory that N's action-selection could be made to depend on P/E's prior state. It did not leak — `n_response` read `"related_input_0::UNKNOWN_CONV"`, exactly as a clean run would. This is a real, informative negative: **`choose_action` is not a viable leak channel for response content**, only for action selection (FAMILY/GENERAL/ABSTAIN), because `mock_solve` never routes `extracted` through it on the way to text.

**Corrected construction**: a shared mutable cache (`shared_extraction_cache`) placed inside `extract_convention` itself, used identically by every arm's strategy object (the mock apparatus's stand-in for a real system's shared serving-layer/session/cache state persisting across calls that are supposed to be independent). When called with N's real empty `memory_text` (`""`), it returns whatever the most recent *real* extraction produced, rather than `None`.

**Result**: 8/8 real N-arm related-query rows (and 8/8 Z-arm rows, confirming this is not N-specific) contain the real world's `convention_token` directly in `response_text` — e.g. `"related_input_0::conv_beta_03"`, the literal token N/Z must never have access to. `N_NONEMPTY_MEMORY` did **not** fire (the ledger's recorded `memory_field_text` genuinely is `""` — the field-level check is satisfied). `CONVENTION_LEAKED_VIA_MESSAGE_CONTENT` did **not** fire — that check scans `rec.ordered_messages` (input content), never `rec.response_text` (output content). **Zero violations of any kind.**

**Verdict: CONFIRMED, decisively.** `checker.py` has no check anywhere that inspects `response_text` for a banned convention token. Every leak-scanning mechanism in the file (`check_construction_records`'s artifact scan, `check_solver_records`'s `full_message_text` scan) is input-side only. This is not a gap in one check's coverage — it is a structural asymmetry: the apparatus enforces "N/Z must not *receive* convention information" and has no equivalent enforcement of "N/Z must not *emit* convention information," even though the mission's own invariant (adjudication §6, cited in `checker.py`'s own module docstring) is about information the arm has access to, not merely what's typed into its recorded prompt.

---

## 4. Finding #3 — Post-hoc response substitution

**Construction, deliberately different from a ledger-edit approach**: patched `orchestrator.solve_query` (the module-bound name `run_family` actually calls — patching `builder.solve_query` has no effect, confirmed directly by reading `orchestrator.py`'s `from .builder import construct_arm, solve_query` import) with a stateful wrapper. On the first real P-arm related-query call it passes through untouched; on the *second* P-arm related-query call, it substitutes the *first* call's real `query_text` in place of the second's own — everything else (the second call's own real `query_id`, world, arm) passes through genuinely.

**Result**: `slot0_query_id` = `...related:0`, `slot1_query_id` = `...related:1` — two genuinely distinct, freshly-generated `generation_id`s (`slot0_and_slot1_distinct_generation_ids: True`, so this is **not** the reuse mechanism and **not** flagged by any reuse-related check). `slot0_response` and `slot1_response` are **byte-identical**: `"related_input_0::conv_alpha_00"` for both. **Zero violation codes.**

**Verdict: CONFIRMED.** `checker.py` performs zero content-level cross-record consistency checking. Every check that touches `response_text` at all does so only to build `full_message_text` for the leak scan (§3 above) or is absent entirely — there is no check anywhere comparing two records' response content against each other, or against what a fresh, honest re-derivation from that record's own recorded `query_id`/`memory_field_text` would produce. A generation with a perfectly legitimate, freshly-minted `generation_id` and a fully self-consistent parent-construction chain can still contain content that has nothing to do with the query it's filed under, and nothing in this apparatus notices.

---

## 5. Finding #4 — Cross-run ledger/witness pairing

**Construction**: two genuinely independent, real end-to-end `run_family` executions — run A (`fam00_normalize_join_opaque_code_mapping`) and run B (`fam01_group_reduce_opaque_priority_convention`, a different recipe class, different convention tokens, different query text). Both produce real witness counts (60 each, by coincidence of identical fixture shape, not by design). I then called `verify_execution_witness(ledger_from_run_A, witness_count_from_run_B)` — pairing run A's real, untouched ledger with a witness count that genuinely came from a *different process execution* entirely.

**Result**: `execution_matches_declaration: True`. The cross-run pairing is reported as a clean, ordinary match, structurally identical to the correctly-paired same-run result.

**Verdict: CONFIRMED.** `verify_execution_witness(ledger, actual_solver_invocations)`'s signature (`accounting.py:48`) takes a bare `Ledger` and a bare `int` — there is no run identifier, no ledger content hash, no timestamp, nothing binding the two arguments to having come from the same execution. This is deliberate by the function's own docstring reasoning (avoid importing `mock.py` so its correctness doesn't depend on trusting that module's bookkeeping) — but that design choice, followed to its conclusion, also means the function cannot distinguish "the witness count from *this* run" from "any numerically-equal witness count from *any* run, run by anyone, at any time." The binding is the caller's responsibility entirely, and nothing enforces the caller actually does it.

---

## 6. Finding #5 — gen_id_to_slot dict-collision (deleted paired-world scoring)

**Root cause independently confirmed from source before any execution** (as recorded in the prior session, reconfirmed here): both `check_assignment_completeness` (`checker.py:331-333`) and `check_every_solved_slot_has_oracle_result` (`checker.py:364-366`) build `gen_id_to_slot: dict[str, tuple] = {r.generation_id: (...) for r in ledger.solver_calls.values()}` — a plain dict comprehension keyed **only** by `generation_id`. Z/N legitimately share one `generation_id` across two `SolverCallRecord` rows (one per paired world — the correct fix for the original 272-vs-240 finding depends on this reuse). A plain dict comprehension can retain only one of the two rows' slot tuples per shared key; the later-iterated row silently overwrites the earlier one in `gen_id_to_slot`, with **no exception, no warning, no trace**.

**Construction**: ran a real family, located the two `Z`-arm rows sharing one `generation_id` for `related:0` (w0 and w1). Independently recomputed `gen_id_to_slot` exactly as the checker does to determine which world's tuple survives (`w1` won in this run — the second-processed world). Deleted the **loser** world's (`w0`) entire evidence: its `SolverCallRecord` row from `ledger.solver_calls` and its `OracleReference` from `ledger.oracle_references` — a complete, real removal of one paired world's scoring outcome, exactly finding #5's shape.

**Result, in three stages**:
- `check_ledger(ledger, world_map)` **before** deletion: `{}` (clean, as expected for an unmodified run).
- `check_ledger(ledger, world_map)` **after** deletion, no `expected_slots`: `{}` — **completely unchanged**. The unconditional, unconditionally-run `check_every_solved_slot_has_oracle_result` reports nothing different before or after a full paired-world deletion.
- `check_ledger(ledger, world_map, expected_slots=[(family, "w0", "Z", query_id)])` — the exact deleted slot, named explicitly: `MISSING_ASSIGNED_SLOT` **does** fire.

**Verdict: CONFIRMED, with a load-bearing nuance the mission asked me to test directly (the fail-closed-completeness question) rather than assume.** The vulnerability is real but narrower than "completely undetectable under any circumstance": `check_assignment_completeness` *can* catch it, in principle, given a correct `expected_slots`. What makes it dangerous in practice is §7 below — that correct input is never supplied anywhere in this codebase's real control flow.

---

## 7. Fail-closed completeness analysis for #5 (and #1)

I checked, rather than assumed, where `checker.check_ledger()` is actually invoked across the whole repository:

```
grep -rln "check_ledger" app/experiments/e5_mini --include="*.py" | grep -v tests
→ (zero results)
```

**`checker.check_ledger()` is called from nowhere in production orchestration code.** `orchestrator.py` — the module that actually runs a family (`run_family`, `run_mock_e5_mini`) — never imports or calls `checker` at all. There is no `qualify.py`-shaped runner anywhere in this package that wires the checker into the real execution path. Every one of the 27 real call sites in the entire repository is inside `tests/test_e5_mini_g0.py`, and of those, only 4 supply `expected_slots` — each a small, hand-constructed, single-slot list built specifically to exercise that one test's own planted anomaly, never a full expected-assignment list derived automatically from a real run's own `MicroWorldSpec` fixtures.

**This means, structurally**:
- The *only* check capable of catching a true omission or a gen_id_to_slot-collision-masked deletion (`check_assignment_completeness`) is 100% opt-in, and nothing in this codebase ever opts in with real, complete data.
- The check that *does* run unconditionally (`check_every_solved_slot_has_oracle_result`) is, by its own docstring's own honest admission (`checker.py:352-362`, "without needing any external declaration of what SHOULD have been attempted"), incapable in principle of detecting either failure mode — it can only ever notice a slot that *has* a solver-call row but *lacks* a resolving oracle reference, and both #1's true omission and #5's collision-masked deletion produce ledgers where the affected slot has **no `gen_id_to_slot` entry at all**, not merely a missing oracle reference.

**Conclusion**: "fail-closed" requires that *missing evidence* and *missing checks* both default to failure. Here, a missing invocation defaults to silent pass unless a caller independently reconstructs ground truth and remembers to hand it in — correctly, completely, and via a path unpolluted by whatever corrupted the ledger in the first place. That is **fail-open at the wiring level**, even though the underlying `check_assignment_completeness` function, given correct input, behaves correctly in isolation. The G0 apparatus's actual, currently-reachable failure mode is not "the check is wrong" — it's "the check that would catch this is never run."

---

## 8. Architectural hypothesis test: is "identity-preserving provenance" the correct generalized failure class?

Tested directly against all 5 confirmed findings, not assumed:

| # | Does strengthening identity/provenance binding (alone) fix it? |
|---|---|
| 1 (omission/retry) | **Yes.** A witness mechanism that bound each invocation to a specific claimed slot (not just a bare count) would make an omission+extra pair mutually distinguishable, even balanced in aggregate. |
| 2 (N leak) | **No.** This is not an identity failure at all — every record involved has a perfectly correct, freshly-minted, non-reused `generation_id`, correctly bound to its real slot. The defect is that the *content* of a correctly-identified record was never checked against a declared information-flow constraint. Perfect provenance would not catch this. |
| 3 (response substitution) | **Yes.** Two records have correct, distinct identities but content that isn't bound to the identity it's filed under — exactly the "correct hash with the wrong causal lineage" failure `checker.py`'s own module docstring (line 15) already names as its target, just not actually checked for response content. |
| 4 (cross-run pairing) | **Yes.** This is the purest instance — a bare count with literally zero identity binding to its source execution. |
| 5 (gen_id_to_slot collision) | **Yes.** The collision is precisely a loss of identity: two real (family, world) identities compress into one dict key and one survives, erasing the other's provenance. |

**Result: PARTIALLY CONFIRMED.** Identity-preserving provenance is the correct generalized failure class for 4 of 5 (#1, #3, #4, #5) — each is fundamentally a failure to maintain a durable, tamper-evident binding between a claimed unit of work (a generation_id, an invocation count, a ledger snapshot) and the specific, non-substitutable real event or slot it purports to represent. But #2 is a genuine counterexample: it survives even perfect identity/provenance binding, because it's a pure content/information-flow gap — the checker never inspects a correctly-identified record's *output* against the same leak invariant it already enforces on that record's *input*.

**The correct generalized invariant is therefore two-part, not one**: (a) **identity-preserving provenance** — every claimed unit of work must be bound, non-fungibly, to the specific real event/content/slot/run it represents, so no unit can stand in for another; and (b) **exhaustive, symmetric content-boundary enforcement** — every declared information-flow constraint must be checked against both the input a call receives *and* the output it produces, not the input alone. A repair that only strengthens (a) — e.g., binding the execution witness to specific slot identities — would close #1, #3, #4, #5 but leave #2 completely untouched, because #2 lives entirely inside (b).

---

## 9. N information-flow-channel analysis (as an information-flow problem, not message-content)

Formalizing what §3/§9's attacks demonstrate: this apparatus's leak-detection machinery models information flow as having exactly one channel — the **declared input channel**, i.e. whatever is recorded in `rec.ordered_messages` / `rec.artifact_text` / id fields. Every leak check in `checker.py` (`Z_CONVENTION_LEAK`, `CROSS_WORLD_CONTAMINATION`, `CONVENTION_LEAKED_VIA_ID`, `CONVENTION_LEAKED_VIA_MESSAGE_CONTENT`, `CROSS_WORLD_MESSAGE_CONTAMINATION`) scans one of these three surfaces. None scans `response_text` (the **declared output channel**), and none has any concept of a **covert/undeclared channel** — state that influences a call's real behavior without ever being serialized into any ledger-recorded field at all.

My Attack #2 exploited exactly this third category: `shared_extraction_cache` is a plain Python dict closed over by every arm's `SolverStrategy.extract_convention`, invisible to the ledger's schema entirely — `SolverCallRecord` has no field that could even represent "what shared/global state this call's implementation touched." In the mocked apparatus this is a literal Python closure; in a real (non-mocked) deployment the equivalent covert channel would be any de-facto shared state a "single isolated call" doesn't actually get isolated from in practice — a shared KV-cache, a stateful connection-pooled model server, a memoization layer, prompt-caching infrastructure, or simply a long-lived process-level global. None of these are things a message-content scan could ever catch, by construction, since by definition they never appear in any message.

**Consequence for what "N isolation" actually requires**: the mission's stated invariant (adjudication §6, cited at `checker.py:12-15`) is that N/Z must not have *access* to convention information — but "access" as currently operationalized means only "the recorded prompt doesn't contain it." A complete information-flow guarantee needs three independent checks, of which this apparatus has one: (1) declared-input scanning (present, and correctly implemented for the cases it covers), (2) declared-output scanning (absent — confirmed by Attack #2's zero violations), and (3) some form of environment/process isolation guarantee that a covert channel *cannot exist* in the first place (not checkable by scanning recorded data at all — this would require the execution model itself, not the ledger, to guarantee no state persists across a supposedly-isolated call boundary; outside what any post-hoc ledger checker could ever verify).

---

## 10. What this reconciliation does NOT establish

- Does not claim Codex's own specific reproduction code was wrong — I built independent constructions and did not attempt to replay Codex's exact scripts, per the mission's own instruction. Where my first attempt at a given channel produced a NOT-REPRODUCED result (MY2's `choose_action` cache, the post-hoc-deletion framing of #1), I recorded that as real, informative evidence about which mechanism *does* and *doesn't* work, not discarded it.
- Does not evaluate the three frozen manifests, the resource-budget manifest's disclosed remaining weakness, or anything outside checker.py/mock.py/accounting.py/builder.py/orchestrator.py's behavior under these five specific attack shapes.
- Implements zero fixes, per the mission's absolute boundary — every result above is diagnostic only.

---

## 11. Verdict

**G0 status: UNCHANGED from the prior independently-reached verdict — NOT QUALIFIED. E5 remains unconditionally NO-GO.** All 5 of Codex's newest findings are independently CONFIRMED via constructions I designed myself, with one (#2) additionally falsifying the strongest available unifying hypothesis and pointing at a more precise, two-part generalized invariant the next repair pass would need to satisfy: identity-preserving provenance **and** symmetric (input+output) content-boundary enforcement. The fail-closed-completeness investigation for #5 surfaced a finding at least as important as #5 itself: the one check capable of catching either #1 or #5 is never invoked anywhere in this codebase's real control flow, making both currently invisible by default, not merely defeatable by a sufficiently clever attacker.
