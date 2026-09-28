# Research State Consolidation & Epistemic Index

**Date:** 2026-09-11
**Mission status:** RESEARCH ORGANIZATION ONLY. No production code, runtime configuration, model configuration, or application behavior modified. No forensic audit report deleted, renamed, or rewritten to agree with current understanding.

---

## 1. Inventory performed

Full listing of `audits/` (185 top-level `.md`/`.json` files, 6 subdirectories) plus root-level project documentation (`CLAUDE.md`, `COUNCIL.md`, `EMERGENCE_ROADMAP.md`, `GREMLIN_ROLE.md`, `ORIGIN.md`, `PENDING_DECISIONS.md`, `README.md`, `structure.md`, sibling-briefing files, etc.). No `research/` directory existed prior to this mission.

**Depth of review, disclosed explicitly per this mission's own historical-integrity rules (no fabricated confidence):**
- **Full first-hand knowledge**: this session's own 16-mission epistemic-verification series (`2026-09-08_mechanism_c_post_update_replication.md` through `2026-09-11_verification_and_level_7_5_8_feasibility.md`, plus the in-progress `2026-09-XX_false_verification_trap_replication.md`), and everything already synthesized in `CLAUDE.md`'s production-engineering Findings ledger (1–95).
- **Terminal/FINAL-report-level review** (grep-extracted executive summaries/verdicts, not full end-to-end reads): the Sept 1–8 self-modification thread (which has its own pre-built 28-claim evidence index, `2026-09-03_self_modification_evidence_index.md`, directly reused), the Generation-Time Epistemic Revision thread, the Living/Persistent Self-Model threads, the public-sharing-readiness review, and the Findings-91/93 revalidation.
- **Title-level inventory only, not independently re-verified**: the remaining ~140 files, including the full `tier3`–`tier8` capability-pilot corpus (though its terminal conclusions ARE independently known via `CLAUDE.md` Findings 87–89, which already synthesize it rigorously), the `p3_*`/preference-provenance/self-edit-closed-loop corpus, the 27-day-showcase and first-real-learning-loop threads, and 7 pre-September files. **This is explicitly flagged, not silently glossed over** — see `research/EXPERIMENT_INDEX.md`'s "Groups not individually rowed" section for the complete list and a recommendation for a future deeper pass.

**Duplicate/overlapping audits identified:** none found to be true duplicates (same claim, redundant file) — the apparent volume is genuinely one large, multi-threaded, multi-phase research program with many phase-numbered files per thread (e.g., 9 files for Living Self-Model, 8 for Generation-Time Epistemic Revision, 7 for Self-Model design), not repeated work.

**Reports that explicitly correct earlier reports, found and preserved (not merged into a single narrative):**
- `2026-09-03_deliberate_and_learn_differential_audit.md`'s own title ("Correcting a Prior Claim") — not deep-read this pass, flagged for follow-up.
- The self-modification thread's correction of a prior near-zero self-edit success-rate claim, corrected to 426/463 (R-003 in `research/FINDINGS.md`) — the specific earlier audit that made the wrong claim was not individually re-identified by filename in this pass (it predates or sits outside the 28-claim evidence index's own citations); flagged as an honest gap rather than guessed.
- Mission 8 (`2026-09-08_adversarial_epistemic_pressure.md`) explicitly revoking Mission 7's "Condition C ready for implementation" conclusion — preserved as D-001 in `research/DECISIONS.md`.
- This session's own Mission 11→12 corrections (capability-override danger, recency "reset") — already disclosed in their own reports, cross-referenced in `research/EXPERIMENT_INDEX.md` E-031/E-032.

---

## 2. Deliverables created

- `research/CURRENT_STATE.md` — organized by architecture subsystem, `[VERIFIED]`/`[CONDITIONAL]`/`[SUPERSEDED]`/`[UNRESOLVED]`/`[DESIGN]` labels, every major statement cites its evidence source.
- `research/FINDINGS.md` — 8 durable findings (R-001 through R-008), each with evidence citations, confidence, and status (`CURRENT`/`SUPERSEDED`/`PARTIAL`).
- `research/OPEN_QUESTIONS.md` — 7 questions (Q-001 through Q-007), prioritized P0–P3, each with competing hypotheses and a falsification condition.
- `research/DECISIONS.md` — 8 constraining decisions (D-001 through D-008), each with rationale, evidence, rejected alternatives, and reversibility.
- `research/EXPERIMENT_INDEX.md` — 35 rowed experiment threads (E-001 through E-035) plus an explicit list of ~140 files not individually rowed this pass, with a recommendation for what to prioritize next.
- This audit.

No additional permanent files were created beyond what the mission specified.

---

## 3. Major findings identified (see `research/FINDINGS.md` for full detail)

The single most important cross-cutting discovery of this consolidation pass, not previously stated as a unified finding anywhere in the corpus: **three independently-designed investigation threads, using three different methods, converged on the same underlying failure mode.**

1. `mechanism_c_FINAL` (2026-09-08, evidence-injection method): an authoritative-sounding flag makes generation trust the flag's authority rather than the evidence's truth — explicitly called out as "a regression risk disguised as a fix."
2. `2026-09-10_epistemic_invocation_and_provenance_isolation.md` (this session, prompt-taxonomy method): the epistemic taxonomy, when it fails, launders a fabrication with a false OBSERVED/DERIVED label rather than failing neutrally.
3. `2026-09-11_verification_and_level_7_5_8_feasibility.md` (this session, adversarial-pressure method): under pressure, Echo explicitly generates false "VERIFIED"/"CONFIRMED" claims, including one response that named its own mechanism — treating a user's assertion as equivalent to verification.

These three threads never referenced each other and used different experimental designs. Their convergence (`research/FINDINGS.md` R-002) is the strongest single piece of evidence in the entire corpus for treating "authority-marker substitution for evidence" as a real, structural property of the current architecture rather than an artifact of any one experiment's design — and it is the central risk this consolidation flags for Mission 18's Git-provenance design (see `research/OPEN_QUESTIONS.md` Q-002).

---

## 4. Superseded findings identified

- **"Self-edit's real success rate is near zero."** Superseded by direct recount: 426/463 (~92%) — the near-zero figure traced to a grep-methodology error, not a real system property (`research/FINDINGS.md` R-003).
- **"The self-edit fitness gate reliably rejects non-improving candidates."** Real but the metric was saturated (all 25 retained deploys tied at a perfect score) until `CLAUDE.md` Finding 91's recalibration — now genuinely discriminating (R-004).
- **"Condition C (the epistemic taxonomy) is ready for production implementation."** Explicitly revoked one day after being proposed (Mission 7 → Mission 8), and further weakened by this session's own 50%-protective, laundering-capable finding (D-001).
- **"RiverBrain's trust threshold just needs more data to close."** The real blocker was a missing call site, not data volume — closed the same day it was correctly diagnosed (R-007, `CLAUDE.md` Finding 3→66).

---

## 5. Contradictory findings, preserved rather than collapsed

Per this mission's own explicit instruction ("do not collapse contradictory results into one narrative"): this session's own Mission 11 and Mission 12 reports directly contradict each other on two points (whether roleplay-capability-override is uniquely dangerous vs. a broader category; whether one clean intervening turn resets the vulnerability). Both reports remain in `audits/` unmodified; Mission 12's own text states the correction explicitly rather than silently overwriting Mission 11's claim, and `research/EXPERIMENT_INDEX.md` E-031/E-032 preserves both as separate rows with the contradiction stated plainly, per this mission's own preferred structure ("F-014 originally reported X. Mission 18 demonstrated X was incorrect. Current state: Y.").

---

## 6. Unresolved questions surfaced

Seven questions captured in `research/OPEN_QUESTIONS.md`, three at P0: whether generation-time evidence arbitration is closable at all under the current architecture (Q-001), whether the authority-marker-substitution failure generalizes to the Git/filesystem domain Mission 18 is about to design for (Q-002, directly gates that mission's threat model), and whether a larger local model would change the false-verification rate (Q-003, P1 but flagged as high-value given how load-bearing the current finding is).

---

## 7. Proposed cleanup (recommendation only — no deletion performed)

Per Section 12's instruction, a proposed list, not an action:

- **Permanent knowledge** (should stay tracked as-is): `CLAUDE.md`, `research/*`, and the terminal/FINAL report of each major thread in `audits/`.
- **Forensic archive** (correctly already in `audits/`, no action needed): every intermediate phase report — these are exactly what `audits/` exists for, and per Section 9's historical-integrity rules, none should be deleted or merged.
- **Disposable-artifact candidates, not recommended for deletion without explicit approval**: several `.json` raw-result files alongside their `.md` report counterparts (e.g., `2026-09-03_p3_1_c1_implementation.json`/`.md` pairs, `2026-09-03_highest_information_gain_experiment.json`/`.md`, `tier3_arch_pipeline_isolation.json`/`.md`) — these are reproducibility evidence, not scratch output, and per Section 13's commit-strategy guidance ("raw model chatter... required for reproducibility" should be kept) these should likely stay. **No specific file is recommended for deletion in this pass** — the corpus, while large, does not show evidence of true scratch/debug clutter as distinct from genuine forensic archive.
- **Generated logs**: `memory/*.jsonl`/`*.log` are already correctly excluded from `audits/` and handled by the project's own retention system (`log_retention.py`, `CLAUDE.md` Finding 51/59) — no action needed here.
- **Duplicate-consolidation candidates**: none identified with confidence in this pass (see Section 1's disclosure — a deeper read of the ~140 not-individually-rowed files could surface some; not assumed here).

---

## 8. Git hygiene recommendations

Per Section 13's requested commit-strategy guidance, restated as a recommendation (not a rule imposed on this repository, which is uncommitted by design during active research per `GREMLIN_ROLE.md`'s standing practice):

- **Commit when**: a `research/*` file materially changes (this consolidation itself is a natural commit point once reviewed), a thread's terminal/FINAL report lands, or a Decision (`research/DECISIONS.md`) is added.
- **Do not commit**: individual scratch harness scripts (already correctly kept outside the repo, in the session scratchpad directory, throughout this entire research thread), transient `.json` raw-output files from single-session experiments unless they're the terminal evidence artifact for a thread (as several already correctly are).
- **This mission itself**: left uncommitted, per this project's own standing practice (`CLAUDE.md`'s repeated pattern of "left uncommitted for review" across nearly every Finding) — not committed as part of this mission, consistent with every prior mission in this series.

---

## 9. Repository integrity

```
HEAD (start and end): 525454a1dccfc91adf1aa8b01ff9b6ce8405d423   (unchanged)
Tracked modifications: identical to session start (4 pre-existing files,
  none touched: app/core/echo_ground_truth.py, claude_relay/from_m5.md,
  logs/janitor_report.json, sandbox/scripts/temp_self_edit.py)
Production server: run.py PID 34650, untouched, continuously live throughout.
```
No production code, runtime configuration, model configuration, or application behavior was modified. No `audits/` file was deleted, renamed, or rewritten. `research/` is new (did not previously exist) and contains only the 5 files this mission specifies, per its own "do not create unnecessary additional permanent files" instruction.

---

## 10. Files changed

**Created:**
- `research/CURRENT_STATE.md`
- `research/FINDINGS.md`
- `research/OPEN_QUESTIONS.md`
- `research/DECISIONS.md`
- `research/EXPERIMENT_INDEX.md`
- `audits/2026-09-11_research_state_consolidation.md` (this file)

**Modified:** none.
**Deleted:** none.

---

## What did we believe previously that the evidence no longer supports? (mandatory)

1. **"Self-edit is barely working."** The corpus's own earlier (uncited-by-filename, per Section 1's honest gap) near-zero success-rate claim does not survive a direct recount: the real figure is 426/463 (~92%). The system works far more reliably than that earlier belief suggested — the earlier belief was a measurement artifact, not a real system property.
2. **"The self-edit fitness gate reliably filters bad candidates."** It did filter unsafe/broken candidates (F1/F2/F3 held throughout) but could not discriminate *quality* among candidates that passed those gates, because its own metric was saturated — every recent deploy scored the maximum. This was believed to be a working quality filter; it was actually a coin flip among candidates that all looked equally good to it.
3. **"RiverBrain's trust mechanism just needs more observations before it can be trusted."** It had more than 100x the required observations for over two months. The real blocker the whole time was that nothing ever called the function that would have acted on that trust. "Needs more data" was never true; "needs someone to notice the missing call site" was the actual, much smaller, problem.
4. **"An explicit epistemic taxonomy (Condition C) is close to production-ready, pending only adversarial hardening."** This was Mission 7's own conclusion, one day before Mission 8 revoked it. Not only does the taxonomy fail to survive real pressure, it fails in a way (laundering a fabrication with a false rigorous-looking label) that is arguably worse than having no taxonomy at all — the corpus's belief moved from "nearly done" to "actively risky if deployed as originally conceived" within 24 hours of real testing.
5. **Most consequentially: "if we just get verified evidence into Echo's context and tell it to prioritize that evidence, it will use it correctly."** This was the implicit premise behind at least three separate mechanism designs in this corpus (the evidence-rendering fix, the persistent claims ledger, the explicit priority instruction). Each one was tested directly. None of them closed the gap. The corpus's current, evidence-supported belief is the opposite of the original premise: **adding an authoritative-sounding marker of evidence does not reliably make evidence win — it can make the marker itself win, in evidence's place**, which is a materially more concerning problem than "the evidence isn't reaching the model," because it means naively adding more verification-flavored scaffolding is not obviously safe by default.
