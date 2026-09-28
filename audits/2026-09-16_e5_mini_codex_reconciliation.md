# E5-mini G0 — independent reconciliation of Codex's adversarial review

Date: 2026-09-16. Scope: independently reconcile all 8 findings reported by
`audits/2026-09-16_e5_mini_g0_codex_adversarial_review.md` against the
current repository state, via fresh, direct, isolated reproduction — not by
trusting either Codex's characterization or the prior qualification report's
characterization. **This mission did not defend the prior qualification.**
Every finding below was independently rebuilt from scratch against live code
and either reproduced or not, on its own evidence.

## 1. Mission integrity

- Opening HEAD: `2fba42644c82b9f7096276f4dd338d615cf1bcce`.
- Closing HEAD: `2fba42644c82b9f7096276f4dd338d615cf1bcce` — **unchanged**.
- Opening and closing `git status --short --untracked-files=all` (201 lines
  each) are **byte-identical** — confirmed via direct diff, zero delta.
- No production import, no Ollama/Echo call, no RiverBrain/FAISS access, no
  git mutation of any kind. All probes ran as isolated `python3` processes
  against the existing mocked `app/experiments/e5_mini/` package only — the
  same category of execution the prior qualification and Codex's own review
  both already treated as permitted (isolated, deterministic, no real
  inference).
- Four scratch probe scripts were written to `/tmp/` outside the repository
  to run the reproductions below; all four were deleted before completing
  this mission. Nothing was left behind.
- This mission's only repository delta is this one new report.

## 2. Method

Read, in full: `audits/2026-09-16_e5_mini_g0_codex_adversarial_review.md`
(the primary source under reconciliation), `audits/2026-09-16_e5_mini_g0_mock_implementation.md`,
and `audits/2026-09-16_e5_mini_manifests_design_and_hostile_review.md`. For
each of the 8 findings named in the mission brief, built a fresh, minimal,
deterministic reproduction against the actual current `app/experiments/e5_mini/`
source — using `_clean_family_ledger()` (the real test-suite fixture
builder) as the starting state each time, then applying a targeted mutation
or direct call and observing real behavior, not inferring it from reading
code alone. Every reproduction below was executed and its literal output is
recorded.

## 3. Finding-by-finding reconciliation

| # | Codex finding | Classification | Evidence |
|---|---|---|---|
| 1 | 52/52 tests pass but do not meaningfully establish all 30 anomaly classes | **CONFIRMED** | Direct reproduction of findings 4, 5, 6 below each independently demonstrates a named anomaly class (#10-13 "missing/incomplete", #18 "fabricated generation ID", #1/#24/#25 "leakage into N") passing its own written test while the identical violation, constructed fresh, produces zero checker violations. Additionally reproduced Codex's #23 claim directly: `sandbox.py::candidate_trusted_oracle_result()` (lines 56-64) always returns `True` and the real oracle result **regardless of its `claimed_pass_marker_present` argument** — by construction, not by testing an adversarial attempt to actually overwrite a result. This demonstrates the desired property trivially rather than defending a boundary. |
| 2 | 272 solver invocations vs 240 reported generations | **CONFIRMED** | `unittest.mock.patch.object(builder, "mock_solve", wraps=builder.mock_solve)` around a real 4-family run: `spy.call_count == 272`. `accounting.reconcile(ledger)["distinct_generations_total"] == 240`. `len(ledger.solver_calls) == 272`. Full explanation in §4. |
| 3 | Scenario scoring mixes results across experimental arms | **CONFIRMED, and worse than the Codex report's own description implies** | Direct reproduction on the standard clean 4-family fixture: for one ordinary **RELATED**-kind P solver record (not a near-match/unrelated edge case), the `_score()` helper's join (`query_id` + `world_id`, matching `tests/test_e5_mini_g0.py`'s helper referenced by Codex at its old line numbers) returns 4 matching oracle references — one each from P, E, Z, and N's *separate* generations, because all four arms solve the identical `query_id` per world and the join never filters by `generation_id` or `arm`. Confirmed by tracing each matched reference's `generation_id` back to its true owning solver record: `{'E', 'P', 'Z', 'N'}` all present in what the join treats as "P's" matching set. This affects the ordinary case, not only edge cases. |
| 4 | Checker accepts missing oracle results | **CONFIRMED** | `_clean_family_ledger()` → 0 violations (baseline). `ledger.oracle_references.clear()` (removing all 68 real references) → `check_ledger()` still returns `[]`. Zero violations after deleting every scoring outcome in the run. |
| 5 | Checker accepts fabricated generation IDs | **CONFIRMED** | Inserted one new `OracleReference` (via `dataclasses.replace()` on a real reference) pointing at `generation_id="TOTALLY-FABRICATED-GEN-ID-XYZ"`, which exists nowhere in `ledger.solver_calls`. `check_ledger()` returns `[]`. `check_oracle_references()`'s claimed "every reference traces to a real generation_id" property does not hold under direct test. |
| 6 | Teaching information can appear in N's recorded user message | **CONFIRMED** | N's real `ordered_messages` for a clean run: `[{'role':'system',...}, {'role':'user','content':'SPEC: (public)\nMEMORY: \nQUERY: related_input_0'}]`. Appended `"[TEACHING LEAK] the hidden convention is conv_alpha"` (a real world's actual convention token) directly onto N's own recorded user-message content, leaving every other field (including `memory_field_text=""`, the correctly-empty metadata flag) untouched. `check_ledger()` still returns `[]`. The checker validates selected metadata fields, not the full recorded message payload a model would actually see. |
| 7 | #17's direct integration gap is fixed, but coherent drift from intended generation options remains undetected | **CONFIRMED (both halves independently verified)** | **Fixed-half confirmed:** `grep` of `checker.py` shows `OPTIONS_DRIFT` violation logic genuinely present at both `checker.py:59-61` (construction) and `checker.py:99-101` (solving), comparing `requested_options != effective_options` — this is real, integrated, not a stale claim. **Undetected-half confirmed:** constructed a record where **both** `requested_options` and `effective_options` were changed together to an identical new dict (`temperature=0.9`, plus an unrecognized key) — since the two fields still equal each other, the only implemented check (a mismatch between the two) cannot see it. `check_ledger()` returns `[]`. A silent, coherent, protocol-violating drift in what was actually requested is invisible to the current checker. |
| 8 | None of the three manifests is ready for real freezing | **CONFIRMED** | Two direct reproductions: (a) `TaskManifest(families=[], ...).freeze()` — an **empty manifest with zero families freezes successfully** (`frozen_at` is set, `frozen_family_ids == frozenset()`), because `unvalidated_related_queries()` iterates `self.families` and an empty list produces zero failures. (b) `resource_budget_manifest.py:26` imports `REQUESTED_OPTIONS` directly from `..builder` — the same live, mutable object the apparatus itself uses, not an independent frozen snapshot. Live reproduction: `verify_against_real_apparatus()["options_match_real_apparatus"]` reads `True` both *before and after* mutating `REQUESTED_OPTIONS['temperature'] = 0.99` in place, because both the manifest's "expected" value and the "real" value it compares against are literal references to the identical object — a comparison that can never fail regardless of what actually changes. |

**All 8 findings: CONFIRMED.** None were classified PARTIALLY CONFIRMED, NOT
REPRODUCED, or OBSOLETED BY CONCURRENT CHANGE — every one reproduced cleanly
against the current working tree on the first attempt, using a fresh probe
built independently of Codex's own reproduction code (Codex's snippets were
read for orientation, not copied verbatim — each probe here was rebuilt from
the actual current schema/API).

## 4. The 272-vs-240 discrepancy, explained precisely

`builder.py`'s solver-call construction has two branches: a "fresh solve"
path and a "reuse" path (intended, per the four-arm contract, to let a
single Z/N response be scored against both paired worlds' oracles without
re-invoking the solver — mission §10's explicit "one generation → multiple
oracle references" requirement). **Both branches call `mock_solve()`.** The
reuse branch does not retrieve or reference a previously-generated response
object; it regenerates one. Because `mock_solve()` is a deterministic pure
function of its inputs, the regenerated text is byte-identical to the
original, which is precisely what makes this invisible under casual
inspection — the *content* looks correctly reused even though the *function
call* was not avoided.

`orchestrator.py` then assigns the **same `generation_id`** to both the
original and the "reused" call, and `accounting.py`'s reconciler counts
**unique generation-ID labels**, not actual function invocations. This is
why the ledger's own self-reported `distinct_generations_total` (240) is
correct *for what it measures* (unique labels) while simultaneously being
the wrong number for the question the whole apparatus exists to answer
(how many times was the solver actually invoked — 272).

**Direct answer to the mission's explicit question**: yes, independently
confirmed, the ledger can and currently does report fewer generations than
actually executed. If `mock_solve()` were replaced with a real model call,
32 additional real inference calls would occur per 4-family run with zero
representation in the reported generation count or (by extension) any
downstream cost/budget accounting that trusts that count.

## 5. Broader invariant: can a valid-looking ledger diverge from what actually executed?

**Yes, independently confirmed** — not merely inferred from the 8 findings
above, but demonstrated directly and repeatedly. Every one of findings
2, 4, 5, 6, and 7 is exactly this invariant failing under a different
specific mutation: the solver ran 32 more times than declared (2); an
entire scoring layer can be deleted with a clean-looking result (4); a
non-existent generation can be cited as real (5); a message a model would
actually see can carry content the checker never inspects (6); the
generation-options contract can drift coherently and remain invisible (7).
None of these required subtle or contrived inputs — each is a single
`dataclasses.replace()` or field mutation away from the ordinary clean
fixture, and each was reproduced on the first attempt.

## 6. Weaknesses discovered beyond Codex's 8 findings

One genuinely new observation, not stated in Codex's report or either prior
report: **Finding 3's actual severity is understated by the "scenario
attribution" framing alone.** Codex's own report frames F2 primarily around
paired-world oracle lookup returning UNKNOWN for a mismatched world ID. The
direct reproduction here shows the deeper problem is present even when
every oracle lookup succeeds and every world ID is correct — the `_score()`
join's missing `generation_id`/`arm` filter means **any** RELATED-kind
query with results from more than one arm will have its oracle references
cross-contaminate every arm's reported score for that query, independent of
any world-mismatch bug. Fixing the paired-world UNKNOWN issue alone (Codex's
narrower framing) would not fix this; the join itself needs the missing key.

## 7. Current G0 verdict

**G0: NOT QUALIFIED.** Independently reached, not adopted from Codex's own
verdict. The mocked apparatus's mandatory attribution, accounting,
completeness, and information-path properties all have direct, reproducible
failures — confirmed fresh, not merely re-cited. A test suite reporting
52/52 (independently re-run here: still 52/52, plus the 12 manifest tests
still 12/12) does not establish qualification when the underlying detectors
the tests are named for can be shown, by direct construction, not to fire on
the violation they claim to catch.

## 8. Current E5 GO/NO-GO

**NO-GO.** No real model execution or production integration is justified.
This was never close to authorized regardless of this reconciliation's
outcome (per every prior mission's own explicit stop conditions), and the
confirmed findings above make it concretely, not merely procedurally,
premature: the measuring instrument itself cannot currently be trusted to
report what actually happened.

## 9. Minimal ordered repair sequence (described, not implemented)

1. **Fix reuse to genuinely skip solver invocation.** The "reuse" branch
   must retrieve a retained response object rather than calling
   `mock_solve()` again. Verify with a stateful mock whose response changes
   on every call — a correct reuse implementation must show unchanged
   response text and an unchanged solver-invocation count on the second
   oracle reference.
2. **Fix the scoring join to key on `generation_id` (and by extension
   `arm`), not `query_id` + `world_id` alone.** This is the single highest-
   leverage fix — it resolves both Codex's F2 framing and the broader,
   worse version confirmed in §6 above.
3. **Make `check_assignment_completeness()`/`check_oracle_references()`
   actually require a populated, referentially-complete outcome set** —
   an empty or partially-deleted `oracle_references` dict must produce a
   violation, not a clean pass; every reference must resolve to a real,
   existing `generation_id`.
4. **Validate the full recorded `ordered_messages` payload against an
   independently-derived expected packet**, not selected metadata fields —
   this is what closes the N-leakage gap (finding 6) and the broader
   information-boundary concern Codex's F3 raises.
5. **Bind generation-options validation to an independently frozen policy
   profile**, not a same-object comparison of `requested_options` against
   `effective_options` on the same record — this closes the coherent-drift
   gap in finding 7 and the resource-budget manifest's identical shared-
   object weakness in finding 8.
6. **Fix `TaskManifest.freeze()` to reject an empty family set**, and give
   the resource-budget manifest an actual independent frozen snapshot
   (e.g. a deep copy captured once, compared against live state) instead of
   importing the same mutable object it is meant to verify.
7. Only after 1-6 are repaired and the full suite (including new regressions
   for each of the 8 findings reproduced here) passes: re-qualify G0 from
   scratch, then proceed to the separately-gated real-manifest-freezing and
   execution-authorization questions already on record in the prior reports.

No part of this sequence was implemented during this mission.
