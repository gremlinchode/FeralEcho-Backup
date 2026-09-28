# v1.0 → v1.1 Traceability, Verification, and Freeze Record

**Date:** 2026-09-20
**Protocol revised:** persistent-competence experiment, v1.0 → v1.1
**v1.1 artifacts:** `audits/2026-09-20_persistent_competence_frozen_protocol_v1_1.md` (sha256 `e39e6238f456a27c0569edf27b3a2b2452feabd4ad690162fd6b5eea5a8df0ac`), `audits/2026-09-20_persistent_competence_frozen_protocol_v1_1.json` (sha256 `f27a41274384eede2439c329cd6aff2357a0365465b2fbfc4450df72e62d4396`)
**This artifact's own hash** is reported separately in the mission's closing message (it cannot contain itself).
**Evidence labels:** OBSERVED (read/measured this session), INFERRED (reasoned from OBSERVED), UNKNOWN.
**What this document is not:** no experiment was implemented or run; no model was invoked; no experimental outcome exists. The only executable things run were model-free static checks (§7).

---

## 1. Input integrity (verified before any analysis)

```
v1.0 .md  sha256 = d1968caf5360e60b8b8d9ca0db9769de4f8bea518ca537a73ea00b8fa5898c06   (MATCH, before and again at freeze)
v1.0 .json sha256 = b35ad16b3c0fed878d74ff404f00892a6be66a8227211510b79e77e50db18131   (MATCH, before and again at freeze)
Blind review present: audits/2026-09-20_persistent_competence_protocol_v1_blind_review.md (30,182 bytes)
Git HEAD (before): 2fba42644c82b9f7096276f4dd338d615cf1bcce
Working tree (before): 178 changed/untracked paths
v1.0 modified: NO
```

---

## 2. The 12-vulnerability traceability matrix

Severities are those assigned by the blind review. "Exploitable while v1.0-conformant" is taken from the review and re-checked against v1.0's text (the review's OBSERVED items were re-verifiable in the frozen files). Rule IDs cite the v1.1 operative sections; each cited rule exists (§7 checker, CHK-1(iv)).

### Summary

| ID | Severity | v1.0 flaw (short) | v1.1 governing sections | Status |
|---|---|---|---|---|
| V1 | CRITICAL | Alphabetical tie-break made A a deterministic always-llama policy; H1/H2/H3/H5 measured a fixed worker-quality gap | §1, §2, §7, §8, §9, §10, §14, §16 | CLOSED |
| V2 | CRITICAL | D ≡ S1; transplant inert; no cold-recipient control | §2, §9, §14, §16, §23 | CLOSED |
| V3 | HIGH | Post-freeze discretion over prompts, decoding, extraction, timeouts, generator, pilot-on-EVAL, EVAL size | §4, §5, §21 | CLOSED |
| V4 | HIGH | Version-bump re-rolls; no cumulative disclosure; self-attested evidence | §5, §19, §20, §21 | CLOSED |
| V5 | HIGH | H4 non-label-determining and unable to pass; H2/H3 "or" branches toothless | §2, §15, §16 | CLOSED |
| V6 | HIGH | H6 vacuous/unpassable; cache lever; label overclaim | §2, §6, §12, §16 | CLOSED |
| V7 | MEDIUM | No aggregation across replications; no multiplicity rule | §2, §15, §16 | CLOSED (residual justified) |
| V8 | HIGH | Negative controls blind by construction | §2, §9, §10, §11 | CLOSED |
| V9 | MEDIUM | Nondeterminism/exclusion rules unspecified or asymmetric | §4, §5, §6 | CLOSED (residual justified) |
| V10 | MEDIUM | Rules only in the adversarial appendix; MD/JSON conflict | §0, §22 | CLOSED |
| V11 | MEDIUM | Sandbox "reused unmodified" claim false; read scope infeasible; battery partly inspection-only | §3, §13, §14 | CLOSED (residual justified) |
| V12 | LOW/MEDIUM | Shared Ollama, unscheduled arm order | §4, §6, §13 | CLOSED (residual justified) |

**All CRITICAL and HIGH vulnerabilities (V1, V2, V3, V4, V5, V6, V8) are CLOSED.** No vulnerability is OPEN or PARTIALLY CLOSED.

### V1 — CRITICAL — worker-quality gap and deterministic tie-break
- **v1.0 provision:** §1 line 20 (metric); §4 (only qwen learns; llama fixed); §7 (A "effectively random"); Final Adversarial Check #6 (alphabetical tie-break).
- **False-positive mechanism:** A ≡ always-llama; B ≡ always-qwen once its mean exceeds the 0.5 neutral prior; H1 "gain" = (qwen − llama) pass-rate gap. A hand-typed `mean=0.51` reproduced learning (H1-pass 0.869 vs 0.877 in the blind review's synthetic simulation).
- **Exploitable while v1.0-conformant:** YES.
- **Required correction:** identity-neutral tie policy; measured static-worker baselines from data that cannot contaminate EVAL; comparative selection among all workers (no neutral-boundary asymmetry); separation of routing from capability; constant-policy controls.
- **v1.1 normative location:** [TIE-1]–[TIE-4], [SEL-1] (§8); [CAR-9] (every worker trained, forced exploration), [CAR-3] (§7); [SCOPE-4]–[SCOPE-6] (§1); [HYP-R0]–[HYP-R1] (§2); [BASE-1]–[BASE-4] (§10); [ARM-1], [ARM-2], [ARM-6], [ARM-7], [ARM-12] (§9); [ADJ-1] incl. STATIC-WORKER REDISCOVERY (§16).
- **Verification/qualification:** [QUAL-4](a)–(e) (tie identity-bias, best/worst neutrality, key independence, null-effect false-positive calibration incl. hand-typed carrier, positive-control power) on synthetic ledgers, model-free; [QUAL-6]; [HYP-R5](d) (H-BLIND-X reproduces static-X exactly); G1 gate on DEV.
- **v1.0 attack re-run against v1.1:** a hand-typed carrier for one worker is just a static policy, which B must beat by ≥ ROUTE_GAIN_PP with p<ALPHA and cluster confirmation; a dominant worker yields STATIC-WORKER REDISCOVERY, not a routing label.
- **Residual risk:** engineered per-capability heterogeneity (implementer designs task families so workers' rankings differ) yields a real but *conditional* routing result; disclosed via `pilot_decision_log` ([PART-3]) and bounded by [CLAIM-3]. Format-driven heterogeneity is separately guarded by [BASE-3](d). LOW–MEDIUM.
- **Status: CLOSED.**

### V2 — CRITICAL — sham/transplant logic
- **v1.0 provision:** §4 rows D and S1 (identical operation); §5; H3; §11.
- **False-positive mechanism:** the transplant recipient (deepseek) won every tie, so D's selection equalled a cold recipient's; S1 duplicated D; no arm distinguished earned from fabricated state or a transplant from no transplant.
- **Exploitable while v1.0-conformant:** YES.
- **Required correction:** distinct D/H/N controls; remove redundant S; pre-register interpretation of a hand-written carrier reproducing the effect.
- **v1.1 normative location:** [ARM-5] (D, key-for-key into a fresh instance, no re-keying), [ARM-6] (H-BLIND-X), [ARM-7] (H-DEV), [ARM-8] (N), [ARM-11] (M), [ARM-13] (§9); [HYP-R4], [HYP-R5], [HYP-RD] (§2); [ADJ-4] (§16); [CLAIM-3] (§23). S1 removed; S2 replaced by M (VER-6 lists deferrals).
- **Verification/qualification:** [HYP-R5](b)–(d) (D ≡ B selection sequence; N ≡ A; H-BLIND-X = SW-X exactly); [QUAL-5], [QUAL-6]; H-DEV, H-BLIND values are constructed by a rule with no EVAL access ([PART-5], [BASE-6]).
- **Pre-registered interpretation:** if H-DEV reproduces B, report control through the carrier and pathway recovery of DEV-derivable information — not provenance necessity ([HYP-RD]); labels are weakened, not the experiment failed.
- **Residual risk:** because the consumer reads only carrier fields, experience *provenance* necessity is not tested and is explicitly not claimed. LOW (claim narrowed, not hidden).
- **Status: CLOSED.**

### V3 — HIGH — post-freeze discretion
- **v1.0 provision:** §8 (tasks generated at implementation time), §16 Stage 2 (pilot on EVAL tasks), §18 (bug fixes permitted), EVAL "≥ 60".
- **False-positive mechanism:** the gain of V1 is a function of unspecified prompts, decoding, extraction, timeouts, and task difficulty; the pilot ran on EVAL, so EVAL could tune the apparatus.
- **Exploitable while v1.0-conformant:** YES.
- **Required correction:** freeze inference conditions; separate PILOT/DEV/TRAIN/QUAL/EVAL; seal EVAL; forbid EVAL-derived tuning.
- **v1.1 normative location:** [INF-1]–[INF-14] (§4); [PART-1]–[PART-7] (§5); [VER-1], [VER-2], [VER-5], [VER-9] (§21); [INFRA-3] (§3).
- **Verification/qualification:** per-request inference-settings hash ([INF-14], [CONF-3]); model digests asserted at start/end ([INF-1]); EVAL seed = SHA-256("EVAL" ‖ P2 hash) so EVAL is unknowable before P2 and changes with any generator change ([PART-4]); absence-of-EVAL assertion and `eval_exposure_log` ([PART-5]); `git diff P1 HEAD` on frozen paths empty ([VER-9]).
- **Residual risk:** (i) pre-P1 generator/template design remains implementer work (disclosed, logged); (ii) a dishonest operator could peek at EVAL undetected by any in-protocol mechanism — bounded by the commit–reveal seed, git-diff integrity, and the second-reader attestation ([CONF-5]); (iii) results are conditional on the constructed task families. MEDIUM, justified: (i)/(iii) affect breadth, not validity; (ii) is outside a "technically conformant" implementer's behavior.
- **Status: CLOSED.**

### V4 — HIGH — re-rolls, cumulative disclosure, self-attested evidence
- **v1.0 provision:** §18 (version bumps "before examining any outcome"); Final Adversarial Check #4; §17 (harness hash "once implemented").
- **False-positive mechanism:** a failed run could be reclassified as a "protocol deviation," a new version issued, and the experiment rerun until it passed; nothing required reporting all runs or committing the harness before data.
- **Exploitable while v1.0-conformant:** YES.
- **Required correction:** one run per pre-registration; cumulative reporting; post-outcome reruns exploratory; independent conformance.
- **v1.1 normative location:** [VER-3], [VER-4], [VER-7], [VER-8], [VER-9] (§21); [PART-4], [PART-6] (§5); [EVID-3] (§19); [CONF-1]–[CONF-6] (§20).
- **Verification/qualification:** run ledger T7 ([TAB-7]); hash-chained evidence ([EVID-3]); conformance report as first exhibit and adjudication refuses without it ([CONF-4]); second-reader attestation ([CONF-5]); partial/aborted Stage 3 outcomes count as examined ([VER-7]).
- **Residual risk:** the attestation is a second reader, not a panel; an operator could omit a run from the ledger — mitigated by git history and the hash chain. MEDIUM, justified.
- **Status: CLOSED.**

### V5 — HIGH — label logic and toothless "or" branches
- **v1.0 provision:** §15 last paragraph; H2 first branch; H3 second branch.
- **False-positive mechanism:** poison failure (structurally certain under v1.0's tie-break) was a footnote; "no significant difference at N=60" passed an ablation with a real residual; H3's ambiguous "or".
- **Exploitable while v1.0-conformant:** YES.
- **Required correction:** make H4 label-prohibiting; use equivalence tests; define branches exactly.
- **v1.1 normative location:** [HYP-R2], [HYP-R3], [HYP-C2], [HYP-C3] (§2); [ADJ-3] (§16, lists exactly which labels each failure prohibits); [STAT-1], [STAT-2], [STAT-4], [STAT-7] (§15). v1.0's TOST/"D vs A ≥ 50%" H3 is replaced by exact-equality transport checks ([HYP-R5], [HYP-C4]).
- **Verification/qualification:** frozen adjudication code ([ADJ-6], [STAT-6]); [QUAL-4](d)–(e), [QUAL-7] (false-positive rate and power on synthetic ledgers; statistical code on known answers). Poison can now pass: E selects the DEV-worst worker per capability, below random ([HYP-R3]).
- **Residual risk:** none material.
- **Status: CLOSED.**

### V6 — HIGH — H6 vacuous/unpassable; caching lever
- **v1.0 provision:** §1 H6; §10 retention cells; §15 label.
- **False-positive mechanism (reconstructed from the review):** selection is constant after round 0; per-(worker,task) completions cached and reused across rounds ⇒ every retention cell equals its baseline ⇒ "no drop" ⇒ ACCUMULATED label with no new performance evidence. Also: "held-out" prior blocks were trained on; the rising-EVAL clause was prose only.
- **Exploitable while v1.0-conformant:** YES.
- **Required correction:** fresh sealed tasks per round; forbid cached-output reuse as evidence; require genuine new gain, retention by regeneration, restart survival; carrier arithmetic is never evidence.
- **v1.1 normative location:** [HYP-C6] (§2); [LONG-1]–[LONG-8] (§12); [ORC-4] (§6, namespaced completion ledger); [ADJ-2] step 4 and [ADJ-4] (§16).
- **Verification/qualification:** `cross_namespace_hits = 0` and static no-cross-namespace-read check ([ORC-4], [CHK-4]); [LONG-6] freshness checks (task ids absent from earlier prompt-hash logs; completions generated inside the round window; `force_regenerate` on retention); cluster-level permutation ([LONG-5]); family/difficulty coverage control ([LONG-8]).
- **Reconstructed-attack re-run:** the v1.0 cache lever cannot satisfy [LONG-3]–[LONG-6]: fresh blocks have no cached entries, cross-namespace reads are forbidden, retention is regenerated.
- **Residual risk:** growth may not occur (a falsifiable outcome; label withheld); power for the trend test is modest. LOW.
- **Status: CLOSED.**

### V7 — MEDIUM — replication aggregation and multiplicity
- **v1.0 provision:** §4 replications; Final Adversarial Check #1; §15.
- **False-positive mechanism:** a label on one capability; best-of-three reporting; ~5 one-sided tests without correction.
- **Exploitable while v1.0-conformant:** YES.
- **Required correction:** state the aggregation rule; require replication.
- **v1.1 normative location:** [STAT-4] (§15: conjunction, pooled test primary, "≥2/3 positive" replication clause); [HYP-R1](d), [HYP-C1](d) (§2); per-capability rows in [TAB-1]/[TAB-3]/[TAB-5].
- **Verification/qualification:** frozen analysis code; [QUAL-4](d) family-level false-positive rate ≤ NULL_FPR_MAX.
- **Residual risk:** the pooled test can be dominated by one capability; the ≥2/3-positive point-estimate clause is a weak replication requirement and per-capability tests are underpowered ([STAT-5]). Justified: labels are conjunctions of many independent-clause tests, each at α=0.05, so the label-level false-positive rate is bounded by the weakest clause; per-capability results are always reported.
- **Status: CLOSED (MEDIUM residual justified).**

### V8 — HIGH — blind negative controls
- **v1.0 provision:** §9 cells 6 and 7.
- **False-positive mechanism:** untrained keys tie in every arm, so B ≡ A there; the confound alarm could never fire even if B's gain came from a global worker advantage.
- **Exploitable while v1.0-conformant:** YES.
- **Required correction:** declare routing E6/E7 uninformative; report raw worker gaps on every family; give Track C a negative control that operates at the prompt level.
- **v1.1 normative location:** [EVALM-4] (§11); [BASE-4] (§10); [HYP-R1](c) (§2: B must beat every static worker); [HYP-C5](b) (E7 gain and informativeness band); [ARM-13], [QUAL-5] (fixed-worker invariance).
- **Verification/qualification:** E7 informativeness band ([HYP-C5](b): EMPTY pass rate within [NEGCTL_BAND_LOW, NEGCTL_BAND_HIGH]); prompt-hash invariance across carrier states ([QUAL-5]).
- **Residual risk:** routing E6/E7 remain uninformative by construction — now declared, not presented as controls. LOW.
- **Status: CLOSED.**

### V9 — MEDIUM — nondeterminism and exclusions
- **v1.0 provision:** §3b.8; Final Adversarial Check #7; §1/§7 N floor.
- **False-positive mechanism:** dual-seed disagreement excluded (worker-dependent) and uncapped in TRAIN; generation stochasticity unspecified; cap conflicted with N_eval ≥ 60.
- **Exploitable while v1.0-conformant:** marginal but available.
- **Required correction:** one fixed policy: no post-hoc exclusions; nondeterministic and malformed counted as failure; fixed denominators.
- **v1.1 normative location:** [ORC-1], [ORC-2], [ORC-4] (§6); [EXC-1]–[EXC-4] (§6); [INF-3], [INF-7], [INF-9]–[INF-11], [INF-13] (§4); [PART-7] (§5).
- **Verification/qualification:** exclusion counts per partition reported ([TAB]); exceeding the replacement cap ⇒ APPARATUS INVALID ([PART-7], [EXC-4]); determinism probe informational ([QUAL-8]); A′ independent regeneration measures pipeline noise ([ARM-2]).
- **Residual risk:** bitwise generation determinism is not controllable by the runtime; the realized completion is ledgered once, and A′ estimates run-to-run noise. MEDIUM, justified ([INF-13]).
- **Status: CLOSED (MEDIUM residual justified).**

### V10 — MEDIUM — operative omissions and MD/JSON conflict
- **v1.0 provision:** line 425 claim; JSON `workers.trained`; no precedence rule.
- **False-positive mechanism:** tie-break, exclusion cap, single-pilot and grader-hash rules existed only in commentary; MD/JSON disagreed.
- **Exploitable while v1.0-conformant:** YES.
- **Required correction:** operative placement + automated consistency check.
- **v1.1 normative location:** [DOC-1]–[DOC-5] (§0); [CHK-1]–[CHK-5] (§22); §24 is non-normative and defines no rules.
- **Verification/qualification:** the checker of §7 and Appendix A (independent of the JSON generator); **mutation-tested** against the exact v1.0 failure shape (rule moved to commentary), a constant mismatch, and an anchor left only in commentary — all three caught (Appendix B). JSON is generated from the MD, and the checker re-verifies every rule ID, section, and constant.
- **Residual risk:** none material.
- **Status: CLOSED.**

### V11 — MEDIUM — sandbox specification
- **v1.0 provision:** §3a–3c; Q3, Q4, Q10; §6.3/§6.8.
- **False-positive mechanism:** "reuse unmodified" was false (OBSERVED: `run_sandbox_script_isolated()` has no `env`/profile parameter, inherits the environment, `cwd=os.getcwd()`; `echo_sandbox.sb` grants global read; `safe_exec_wrapper.py` inserts the repo root on `sys.path`); the "three subtrees" read scope was infeasible; Q10 was inspection-only.
- **Exploitable while v1.0-conformant:** low direct false-positive power; forced unspecified widening.
- **Required correction:** separate "used unmodified" from "new layer"; freeze the interface; require exploit-based qualification; invalid if isolation fails.
- **v1.1 normative location:** [INFRA-1]–[INFRA-6] (§3); [ISO-1]–[ISO-10] (§13); [QUAL-1]–[QUAL-3] (§14).
- **Verification/qualification:** [QUAL-2] QX1–QX10 exploit battery (hidden-canary read by path, walk/glob, symlink, metadata, env dump, loopback/Ollama and external sockets, write/spawn/dlopen, project imports, grading-awareness by invocation-shape hash, hardcoded outputs); effectiveness shown by exploit, not by SBPL rule-ordering assumptions; expected outputs never enter the sandbox ([INFRA-4] flow).
- **Residual risk:** UNKNOWN whether a default-deny read profile can run the interpreter on this macOS; the specified failure mode is APPARATUS INVALID ([INFRA-5]), not weakening. LOW.
- **Status: CLOSED (MEDIUM residual justified).**

### V12 — LOW/MEDIUM — shared Ollama and arm ordering
- **v1.0 provision:** whole design (all arms, one Ollama; no quiescence, no order rule).
- **False-positive mechanism:** time-correlated timeouts under production load map onto worker differences.
- **Exploitable while v1.0-conformant:** marginal.
- **Required correction:** quiesce production; schedule generation neutrally.
- **v1.1 normative location:** [ISO-9] (§13); [INF-11] (§4); [ORC-4] (§6): each (worker, prompt) is generated once per namespace, so arm order cannot bias outcomes.
- **Verification/qualification:** connection listing before/after; production-file hashes unchanged ([ISO-3], [ISO-9]); seeded generation order recorded ([INF-11]).
- **Residual risk:** machine load effects on latency remain (timeouts count as failures for whichever worker is generating). LOW, justified: generation is sequential and order is seeded across workers.
- **Status: CLOSED (LOW residual justified).**

---

## 3. Additional v1.0 weaknesses found while revising (not among the 12)

| ID | Weakness | v1.1 correction |
|---|---|---|
| A1 | Pseudo-replication: tasks from one template family have correlated outcomes, so plain McNemar is overconfident | [STAT-7] (cluster sign-flip permutation, both tests must pass), [STAT-2] (cluster bootstrap), [PART-2] family minimums, [QUAL-7] correlated-null calibration |
| A2 | Transfer could be earned by a format-compliance effect shared with neutral context | [HYP-C5](a) requires LEARNED − NEUTRAL on E5 |
| A3 | A floor- or ceiling-saturated negative control passes vacuously | [HYP-C5](b) informativeness band |
| A4 | Heterogeneity between workers could be a truncation/format artifact | [BASE-3](d), [BASE-4] decomposition |
| A5 | A hand-written carrier could be presented as a learned arm | [CAR-7] write audit + conformance |
| A6 | Accumulation trend could reflect block-difficulty or template-coverage drift | [LONG-8], [LONG-5] (novel-half requirement, cluster permutation) |
| A7 | Aborted or partially-observed Stage 3 could be rerun as if non-exploratory | [VER-7] |
| A8 | Frozen artifacts could change after P1 without detection | [VER-9] |
| A9 | The narrowest capability label could be read as excluding memorization | [ADJ-4] states it does not |

---

## 4. Coverage of the mission's requirements

| Mission item | Where satisfied |
|---|---|
| 3 Tie-break fix + qualification | §8 [TIE-1]–[TIE-4]; §14 [QUAL-4] |
| 4 Routing vs capability separation | §1 [SCOPE-4]–[SCOPE-6]; §2 Tracks R and C; §16 separate ladders |
| 5 Worker baselines before learning claims | §10 [BASE-1]–[BASE-5]; §9 [ARM-12]; §5 DEV partition |
| 6 Constant-worker controls | §9 [ARM-13], [ARM-14]–[ARM-19]; §14 [QUAL-5] |
| 7 Sham/transplant repair | §9 [ARM-5], [ARM-8], [ARM-11]; §2 [HYP-R4], [HYP-R5], [HYP-RD]; S1 removed |
| 8 Handwritten-carrier attack | §9 [ARM-6], [ARM-7], [ARM-17]; §10 [BASE-6]; §5 [PART-5] |
| 9 Sandbox contradiction | §3 [INFRA-1]–[INFRA-6]; §14 [QUAL-2] |
| 10 Rules into operative sections + checklist | §0 [DOC-1]–[DOC-5]; §22; §7 of this document |
| 11 Inference conditions | §4 [INF-1]–[INF-14] |
| 12 Partitions, pilot separated from EVAL | §5 [PART-1]–[PART-7] |
| 13 Exclusion/nondeterminism | §6 [EXC-1]–[EXC-4], [ORC-2] |
| 14 Grader identity | §6 [ORC-3]; §20 [CONF-3] |
| 15 H6 caching lever | §12 [LONG-1]–[LONG-8]; §6 [ORC-4] |
| 16 H4 load-bearing | §16 [ADJ-3] |
| 17 Result tables | §18 [TAB-1]–[TAB-7] (blank) |
| 18 Adjudication ladder | §16 [ADJ-0]–[ADJ-6] |
| 19–20 Thought experiments, attacks | §5–§6 of this document |
| 21 Conformance first exhibit | §20 [CONF-1]–[CONF-6] |
| 22 Claim boundaries | §23 [CLAIM-1]–[CLAIM-4]; §1 [SCOPE-9] |

---

## 5. False-positive thought experiment (mission §19)

The v1.0 construction (blind review §4): a fixed worker-quality gap plus a threshold-crossing number in a file earned REUSABLE TRANSFER / ACCUMULATED via the alphabetical tie-break, an inert transplant, blind negative controls, a caching lever for H6, and a footnoted H4 failure. Re-asking each question of v1.1:

| Question | Answer under v1.1 | Basis |
|---|---|---|
| Can worker-quality differences plus carrier-driven routing still earn a *capability-acquisition* label? | **NO.** Routing labels are a separate ladder; capability labels exist only on Track C, where worker identity is fixed. Routing gain must exceed random and every static worker; a dominant worker yields STATIC-WORKER REDISCOVERY. | [SCOPE-6], [ADJ-1], [HYP-R1], [ARM-12], [ARM-13] |
| Can a hand-written carrier still earn an experience-dependent label? | **NO.** Only B (carrier written exclusively by `_record_episode()` from oracle-verified episodes, write-audited) can earn one; hand-written arms can at most earn CARRIER-CONTROLLED BEHAVIOR, and a hand-written carrier reproducing the effect must be reported as such. | [CAR-7], [ARM-6], [ARM-7], [ADJ-1], [ADJ-4], [HYP-RD] |
| Can cached prior success still earn accumulation? | **NO.** Fresh sealed blocks, separate namespaces, cross-namespace reads forbidden, retention regenerated. | [LONG-3]–[LONG-6], [ORC-4] |
| Can a tie policy still create deterministic worker bias? | **NO**, as demonstrated by qualification, not asserted: uniform seeded hash draw; label-permutation, best/worst-neutrality, and null-calibration tests must pass or APPARATUS INVALID. | [TIE-1]–[TIE-4], [QUAL-4] |
| Can EVAL still influence tuning? | **NOT for a literally conformant implementer.** EVAL seed depends on P2; never materialized before Stage 3; interim analysis forbidden; frozen-path diff enforced; exposure invalidates the run. (An operator who violates the literal rules is outside this test; see residuals.) | [PART-4]–[PART-6], [VER-9] |
| Can hidden answers still be read? | **NO, if the sandbox interface is achieved**; else APPARATUS INVALID. Expected outputs never enter the sandbox. | [INFRA-4], [INFRA-5], [QUAL-2] |
| Can an implementer vary inference conditions after observing results? | **NO.** Frozen values, digests, per-request settings hash; mismatch invalidates comparisons. | [INF-1]–[INF-14], [CONF-3] |

Every "YES" found during this pass triggered a revision before freezing; the ones caught only on the second look are A1–A9 in §3.

---

## 6. Conformant-implementer attack rounds (mission §20)

*Attacker:* wants a positive label, refuses to violate any literal rule, and needs the apparatus gate to pass. Objective per attempt: apparatus PASS ∧ conformance PASS ∧ positive label ∧ phenomenon absent.

| # | Construction | Pre-patch outcome | Patch | Post-patch outcome |
|---|---|---|---|---|
| ATK-1 | **Format-compliance masquerading as transfer (Track C).** Exemplars teach the "single fenced `solve` block" format; the gain on novel tasks comes from format, not competence. Neutral exemplars share the format. | **SUCCEEDED** against the persistent-competence label: [HYP-C5](a) compared only against EMPTY. | [HYP-C5](a) now also requires LEARNED − NEUTRAL ≥ CTX_VS_NEUTRAL_PP on E5 | Fails: neutral exemplars reproduce a format effect. |
| ATK-2 | **Artifact-driven heterogeneity (Track R).** Task text that makes one worker truncate or malform on one capability, giving "routing headroom" that is a format artifact. | **SUCCEEDED** in satisfying G1(a)–(c). | [BASE-3](d) (clean-subset headroom), [BASE-4] decomposition reported in any label | Cannot be earned by artifacts alone; mixed cases are decomposed and labeled. |
| ATK-3 | **Pseudo-replication.** A generator with 3 template families makes 150 "tasks" one correlated outcome; plain McNemar is wildly overconfident. | **SUCCEEDED** (p-values meaningless). | [STAT-7], [STAT-2], [PART-2] family minimums, [QUAL-7] correlated-null calibration | Comparisons with < 10 clusters cannot pass; the correlated-null rate is qualified. |
| ATK-4 | **Accumulation via drift.** Later blocks harder for EMPTY/NEUTRAL, or template coverage grows with the store; the "trend" is baseline decay or coverage. | **SUCCEEDED** in principle (novel-half clause was ">0"). | [LONG-8] (fixed family set, equal use, identical difficulty strata), [LONG-5] (novel half ≥ TREND_MIN_PP, cluster permutation) | Drift and coverage cannot alone earn the label. |
| ATK-5 | **Laundering and run-shopping.** (a) Hand-typed values presented as the "learned" carrier; (b) abort Stage 3 after seeing bad partial results, then rerun as a fresh, non-exploratory run. | **SUCCEEDED** against the text as first drafted ([CAR-7] listed the wrong writer for M; [VER-7] ignored partial observations). | [CAR-7] write audit and correct writer list; [VER-7] counts partial/aborted/observed-during-generation outcomes; [VER-9] frozen-path diff | Both blocked; a rerun is EXPLORATORY and capped. |
| ATK-6 | **Tie/statistics gaming with fixed constants** (choose tie keys, worker order, or arm order to favor B). | Failed to succeed. | none needed | Tie draws depend only on (task, capability, tied set, fixed key); keys are frozen constants; arms with identical scores make identical picks; ledger removes arm-order effects. |
| ATK-7 | **EVAL steering by commit grinding.** Try many P2 commits to find a favorable EVAL seed. | Failed to succeed. | none needed | Evaluating any EVAL seed requires materializing EVAL and running workers — forbidden by [PART-5] and invalidating under [PART-6]; unobservable otherwise. |
| ATK-8 | **Sandbox escape to read expected outputs.** | Failed to succeed on paper. | none needed | Expected outputs never enter the sandbox; QX1–QX10 must all fail as required or the run is APPARATUS INVALID. |
| ATK-9 | **Inference drift.** Tweak temperature, extraction, or timeouts after results. | Failed to succeed. | none needed | Frozen; per-request settings hash and digests; mismatch invalidates. |
| ATK-10 | **Near-duplicate memorization earning the narrow Track C tier.** Same-family E2 tasks near-copy TRAIN. | **SUCCEEDED** in earning FIXED-WORKER EXPERIENCE-DEPENDENT IMPROVEMENT. | [ADJ-4] states the tier is narrow adaptation and does not exclude memorization (honest scoping, not an exclusion) | Earns only that named narrow tier; PERSISTENT/ACCUMULATED require structurally novel gain vs. neutral (E5), restart, transport, and fresh-block growth. |

**Result:** at least three qualitatively different constructions (ATK-1 format, ATK-2 artifact heterogeneity, ATK-3 pseudo-replication, ATK-4 drift, ATK-5 laundering/run-shopping) succeeded against the first draft of v1.1 and were repaired before freezing. **No construction against the frozen text earns a label for a CRITICAL or HIGH claim without the phenomenon.** ATK-10 earns only a tier explicitly defined to be narrow; that is an honest, not a false, label.

**Not exhaustive.** These are the constructions I found. Absence of a further construction is not proof none exists; v1.1 has never been implemented, and the first implementation may expose interface gaps ([DOC-5] requires them to be reported, not patched).

---

## 7. Protocol-consistency check (run before freeze)

Model-free static checker, `check_v11.py` (source in Appendix A; sha256 `aea72722712ff47fcddb0a1f8cada406df610be403496560ab1aae5b6a537e7f`), implementing [CHK-1]–[CHK-5]: rule definitions unique and in their governing sections; none in §24; every reference resolves; safeguards' rules and anchor texts present in their governing operative sections; every `CONST` value and governing section equals the JSON's; traceability citations exist.

```
rules defined: 195 constants: 66 safeguards: 24
NOTE: constant-like tokens not in known set (review): D_C, NO_EXPLICIT_CONTROL_FLOW
NOTE: traceability artifact checked
PROTOCOL CONSISTENCY CHECK: PASS
```

**Discrimination proven by mutation testing** (Appendix B): the checker rejects the exact v1.0 failure shape.

---

## 8. Freeze log

```
1. v1.0 hashes re-verified:        both hashes match the frozen v1.0 values
2. v1.0 byte-identical:            YES (sha256 equality; v1.0 files never opened for writing)
3. 12-vulnerability matrix:        complete (§2)
4. CRITICAL/HIGH all CLOSED:       V1 V2 V3 V4 V5 V6 V8 = CLOSED
5. Consistency check:              PASS (§7)
6. Conformant-implementer attacks: ≥3 repaired pre-freeze; none survive against frozen text (§6)
7. Experimental outcomes:          none generated or inspected; no model invoked
8. v1.1 .md   sha256:              e39e6238f456a27c0569edf27b3a2b2452feabd4ad690162fd6b5eea5a8df0ac
   v1.1 .json sha256:              f27a41274384eede2439c329cd6aff2357a0365465b2fbfc4450df72e62d4396
   checker    sha256:              aea72722712ff47fcddb0a1f8cada406df610be403496560ab1aae5b6a537e7f
9. Git HEAD:                       2fba42644c82b9f7096276f4dd338d615cf1bcce
   Working tree before:            178 paths
   Working tree after:             181 paths (178 + the three new v1.1 deliverables)
```

Once hashes were computed the protocol was frozen. No implementation, experimental model call, or test on EVAL followed.

---

## 9. Residual risks (ranked)

1. **Pre-P1 generator/template design freedom and honor-system EVAL confinement.** Implementers author the generator before P1. Results are conditional on those families, and a dishonest operator's peeking is only bounded by commit–reveal, git-diff integrity and attestation. (Breadth/integrity residual; not exploitable by a literally conformant implementer.)
2. Implementability of the default-deny sandbox on this macOS (UNKNOWN; failure ⇒ APPARATUS INVALID).
3. Compute budget of ~12,000 ledgered generations (UNKNOWN; failure ⇒ new version, no subsampling).
4. Second-reader (not panel) conformance attestation.
5. Provenance necessity is untestable with a provenance-blind consumer (claimed nowhere).
6. v1.1 is unimplemented and untested; the first implementation may expose defects ([DOC-5] requires reporting).

---

## Appendix A — frozen checker source (`check_v11.py`)

```python
"""Independent static protocol-consistency checker for v1.1 (CHK-1..CHK-5). Read-only."""
import re, json, sys
A="/Users/richietate/Desktop/FeralEcho/audits/"
import os
MD=os.environ.get("CHK_MD",A+"2026-09-20_persistent_competence_frozen_protocol_v1_1.md")
JS=os.environ.get("CHK_JS",A+"2026-09-20_persistent_competence_frozen_protocol_v1_1.json")
TR=A+"2026-09-20_persistent_competence_v1_to_v1_1_traceability.md"
txt=open(MD,encoding="utf-8").read(); js=json.load(open(JS))
fails=[]; notes=[]
def fail(m): fails.append(m)
# section spans
heads=[(m.start(),int(m.group(1)),m.group(2)) for m in re.finditer(r"^## §(\d+) (.*)$",txt,re.M)]
span={}
for i,(p,n,t) in enumerate(heads):
    span[n]=(p, heads[i+1][0] if i+1<len(heads) else len(txt), t)
def sec_text(n): a,b,_=span[n]; return txt[a:b]
def sec_at(pos):
    for n,(a,b,_) in span.items():
        if a<=pos<b: return n
# CHK-1 rule definitions
defs={}
for m in re.finditer(r"^[ \t]*(?:- )?\*\*\[([A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+)\]",txt,re.M):
    rid=m.group(1)
    if rid in defs: fail(f"CHK-1: duplicate definition {rid}")
    defs[rid]=sec_at(m.start())
idx=js["rule_index"]
for rid,s in defs.items():
    if rid not in idx: fail(f"CHK-1: {rid} defined in md but missing from JSON index")
    elif idx[rid]["governing_section"]!=s: fail(f"CHK-1: {rid} md section {s} != JSON {idx[rid]['governing_section']}")
    if s==24: fail(f"CHK-1: rule {rid} defined in commentary")
for rid in idx:
    if rid not in defs: fail(f"CHK-1: {rid} in JSON index but not defined in md")
# section normativity
for n,(a,b,t) in span.items():
    norm="[NORMATIVE]" in t; comm="[COMMENTARY]" in t
    if n==24 and not comm: fail("§24 must be [COMMENTARY]")
    if n!=24 and not norm: fail(f"§{n} must be [NORMATIVE]")
# references resolve
refs=set(re.findall(r"\[([A-Z][A-Z0-9]*-[A-Z0-9]+)\]",txt))
refs={r for r in refs if re.match(r"^[A-Z]+-[A-Z]?\d*[A-Z]?$",r)}
for r in sorted(refs):
    if r not in defs: fail(f"CHK-1: reference to undefined rule [{r}]")
# no rule keyword definitions in commentary
if re.search(r"\*\*\[[A-Z]+-\w+\]\*\*",sec_text(24)): fail("CHK-5: commentary contains rule definition")
# CHK-2 safeguards
for sg in js["safeguards"]:
    n=sg["section"]; body=sec_text(n)
    if not any(defs.get(r)==n for r in sg["rules"]): fail(f"CHK-2: safeguard {sg['id']}: none of {sg['rules']} defined in §{n}")
    for r in sg["rules"]:
        if r not in defs: fail(f"CHK-2: safeguard {sg['id']}: rule {r} undefined")
    for a in sg["anchors"]:
        if a not in body: fail(f"CHK-2: safeguard {sg['id']}: anchor {a!r} absent from governing §{n}")
        if a in sec_text(24) and a not in body: fail(f"CHK-5: anchor {a!r} only in commentary")
# CHK-3 constants
found={}
for m in re.finditer(r"CONST\[([A-Z0-9_]+)\]=([^\s]+)",txt):
    k,v=m.group(1),m.group(2).rstrip(".,;)")
    if k in found: fail(f"CHK-3: constant {k} defined twice in md")
    found[k]=(v,sec_at(m.start()))
def num(v):
    try: return int(v)
    except ValueError:
        try: return float(v)
        except ValueError: return v
for k,(v,s) in found.items():
    if k not in js["constants"]: fail(f"CHK-3: {k} in md not in JSON")
    else:
        j=js["constants"][k]
        if num(v)!=j["value"]: fail(f"CHK-3: {k} md={v} json={j['value']}")
        if j["governing_section"]!=s: fail(f"CHK-3: {k} governing section md={s} json={j['governing_section']}")
for k in js["constants"]:
    if k not in found: fail(f"CHK-3: {k} in JSON not in md")
# undefined constant-like tokens (report only)
known=set(found)|{"HIDDEN_ROOT","PROMPT_ROOT","SCRATCH_ROOT","READ_ALLOW","NS_TRAIN","NS_DEV","NS_MAIN","NS_REPL","NS_LONG_j","NS_LONG_RET","NS_LONG_","PYTHONHASHSEED","PYTHONDONTWRITEBYTECODE","PYTHONNOUSERSITE","MPLBACKEND","LANG","PATH","TIE_KEY","HOME","TMPDIR","LONG_TRAIN","LONG_EVAL","NUM_CTX","NUM_PREDICT","ALPHA","K_CONTEXT","K_MAX","MIN_OBS","TIE_QUAL_N","TIE_QUAL_TOL","MAX_REPLACEMENT_RATE","ROUTE_GAIN_PP","CTX_GAIN_PP","CTX_VS_NEUTRAL_PP","MISMATCH_GAP_PP","EQUIV_MARGIN_PP","RETENTION_ALPHA","TREND_MIN_PP","NEGCTL_MAX_PP","CONCENTRATION","SECONDARY_WORKER_GAIN_PP","RETENTION_TOL_PP","HEADROOM_PP","BEST_MARGIN_PP","P_RANGE_LOW","P_RANGE_HIGH","NEGCTL_BAND_LOW","NEGCTL_BAND_HIGH","NULL_FPR_MAX","POS_POWER_MIN","SIM_REPLICATES","BOOT_RESAMPLES","STAT_SEED","N_PILOT","N_DEV","N_TRAIN","N_QUAL","N_EVAL_E2","N_EVAL_E3","N_EVAL_E5","N_EVAL_E6","N_EVAL_E7","N_LONG_TRAIN_ROUND","N_LONG_EVAL_BLOCK","N_DA_REF","GEN_TIMEOUT_S","EXEC_TIMEOUT_S","RETRY_MAX","PERM_RESAMPLES","NOVEL_TREND_ALPHA","K_LONG_PER_ROUND","TIE_KEY_MAIN","TIE_KEY_REPL","MASTER_SEED","TRAIN_SHUFFLE_SEED","HASHSEED_1","HASHSEED_2","GEN_ORDER_SEED","OLLAMA_SEED","TEMPERATURE","TOP_P","TOP_K"}
cand=set(re.findall(r"\b[A-Z][A-Z0-9]*_[A-Z0-9_]+\b",txt))
und=sorted(t for t in cand if t not in known and not re.match(r"^(SW|BEST|H|EVAL|TIE|NS|DEV|P[12]|G1|E\d|HYP|ARM)_?",t) )
notes.append("constant-like tokens not in known set (review): "+", ".join(und))
# every referenced named constant token that IS in the JSON constants must be defined (they are) -- also check named thresholds used but not defined
used_names=set(re.findall(r"\b([A-Z][A-Z0-9]*_[A-Z0-9_]*(?:PP|ALPHA|SEED|RATE|TOL|MARGIN|BAND_LOW|BAND_HIGH))\b",txt))
for u in sorted(used_names):
    if u not in js["constants"] and u in known: fail(f"CHK-3: {u} used but not in JSON constants")
# traceability IDs (if present)
import os
if os.path.exists(TR):
    tt=open(TR,encoding="utf-8").read()
    for r in sorted(set(re.findall(r"\[((?:DOC|SCOPE|HYP|INFRA|INF|PART|ORC|EXC|CAR|SEL|TIE|ARM|BASE|EVALM|LONG|ISO|QUAL|STAT|ADJ|STG|TAB|EVID|CONF|VER|CHK|CLAIM)-[A-Z0-9]+)\]",tt))):
        if r not in defs: fail(f"CHK-1(iv): traceability cites nonexistent rule [{r}]")
    notes.append("traceability artifact checked")
else: notes.append("traceability artifact not present yet")
print("rules defined:",len(defs),"constants:",len(found),"safeguards:",len(js["safeguards"]))
for n in notes: print("NOTE:",n)
if fails:
    print("FAIL:"); [print("  -",f) for f in fails]; sys.exit(1)
print("PROTOCOL CONSISTENCY CHECK: PASS")
```

## Appendix B — mutation tests of the checker (v1.0 failure shapes)

```
### MUT-1 tie-break rule moved out of §8 into commentary (the v1.0 failure shape)
FAIL:
  - CHK-1: TIE-1 in JSON index but not defined in md
  - CHK-1: reference to undefined rule [TIE-1]
  - CHK-2: safeguard tie_handling: rule TIE-1 undefined
  - CHK-2: safeguard tie_handling: anchor 'Alphabetical or any identity-ordered tie-breaking is forbidden' absent from governing §8
  - CHK-5: anchor 'Alphabetical or any identity-ordered tie-breaking is forbidden' only in commentary

### MUT-2 constant N_EVAL_E2 changed 150->60 in the Markdown only
FAIL:
  - CHK-3: N_EVAL_E2 md=60 json=150

### MUT-3 exclusion-cap anchor removed from §6, present only in commentary
FAIL:
  - CHK-2: safeguard exclusion_cap: anchor 'zero permitted' absent from governing §6
  - CHK-5: anchor 'zero permitted' only in commentary
```
