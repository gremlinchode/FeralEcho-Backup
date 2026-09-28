# Research Arc Provenance Audit — September 2026

**Date:** 2026-09-11 (investigation conducted this session; artifacts under review span 2026-09-06 through 2026-09-11)
**Type:** Investigation-only. No production code, git state, or audit documents were modified.
**Mission:** Forensic provenance audit of ~65 untracked research/audit documents. Determine whether FeralEcho can demonstrate a traceable chain from research finding → decision → implementation → verification → documented architectural truth, and quantify the current documentation/reality gap.

---

## Executive Summary

The September research corpus is **not one arc** — it is at least **four semi-independent work streams** running concurrently across 2026-09-06 through 2026-09-11, with materially different completion states (OBSERVED, via git log, PENDING_DECISIONS.md, and cross-reference of research/*.md against the untracked file list):

1. **Epistemic-arbitration / self-model research** (the bulk of the 63 untracked `audits/*.md` files, ~40 of them) — a rigorous, self-correcting, evidence-labeled investigation into whether verified evidence in Echo's context reliably changes what it says. This thread has its own internal provenance apparatus (`research/CURRENT_STATE.md`, `FINDINGS.md`, `OPEN_QUESTIONS.md`, `DECISIONS.md`, `EXPERIMENT_INDEX.md`), which was itself **committed to git in `cfd01b7`** (2026-09-09) — but the audit report that explains why/how that index was built (`audits/2026-09-11_research_state_consolidation.md`) was **not** committed alongside it, and remains untracked today (OBSERVED).
2. **F2 sandbox stdin-contract hardening** (Missions 21–30, a sub-thread of #1 that turned into real production code) — this is the **most complete chain in the entire corpus**: audit → finding → decision → implementation → verification, with the implementation **already substantially committed to git** (`75721f0` through `1081f26`/`ea5e5e8`) and **live in the running server right now** (OBSERVED: `/admin/liveness-status` reports 52 checks passing this session, up from CLAUDE.md's last documented count of 41). Its final piece (OS-level fd0 closure) remains uncommitted in both code and its own audit report. **Zero of this — neither the committed nor uncommitted parts — appears anywhere in CLAUDE.md.**
3. **Production-engineering fixes** (`PENDING_DECISIONS.md` items #20–23): `/admin/restore` council gate, `select_best_fallback_candidate()` rewrite, `temporal_environment.py` location split, and the F2 stdin overlap above. This is the **best-documented** stream — `PENDING_DECISIONS.md` itself carries full, dated, evidence-cited writeups for all four — but none has a corresponding CLAUDE.md Finding yet, and all four sit uncommitted in the working tree (independently reviewed and confirmed legitimate in a prior pass this session).
4. **Two narrow, self-contained side investigations** — the `task_type_classifier.py` causal-learning audit (Missions 32–35) and the Codex-relay architecture investigation — both produced real, isolated, non-production experiment code (`app/experiments/task_type_ground_truth/`, `codex_relay/`), both are **absent from `research/*.md`'s own index** (a real gap in that index's own coverage, not just CLAUDE.md's), and both are completely absent from CLAUDE.md.

**Central answer to the mission's central question**: FeralEcho **can** demonstrate a traceable chain for specific, individual findings — several chains in this corpus are complete end-to-end, with real verification evidence at every link (SUPPORTED to VERIFIED, see the graph below). But **no chain in this corpus reaches the final "documented architectural truth" link in CLAUDE.md** — the project's own canonical, single-source-of-truth ledger has had zero entries since Finding 95 (2026-09-05). Every thread described above post-dates that by at least one day. This is not a case of missing traceability; it is a case of a **known, disclosed, and currently five-plus-day-wide extension of the exact gap CLAUDE.md's own Finding 86 was created to close once already.**

---

## Repository State at Audit Start

OBSERVED, via `git status --porcelain`, `git log`, `git rev-parse HEAD`:

- **HEAD**: `e92ec3b7fe4743f75746d161a06601db0232bff2` ("docs: track MacBook/phone location separation decision", 2026-09-09).
- **19 modified tracked files** (independently reviewed in a prior pass this session; all syntax-check clean, all appear complete and legitimate — see that pass's own summary, not repeated in full here).
- **94 total uncommitted paths.**
- **63 untracked Markdown files under `audits/`**, dated 2026-09-07 through 2026-09-11 (the user's framing said "approximately 65"; exact count confirmed via `git status --porcelain -- audits/` is 63).
- **2 untracked JSON companions** to two of those audits, plus **2 untracked `.jsonl` result files** under `audits/tier3_apparatus/`.
- **4 untracked new paths**: `.claude/` (containing the stale worktree), `codex_relay/`, `app/experiments/task_type_ground_truth/`, `app/experiments/real_trace_f2_provenance/_scratch/`.
- **2 untracked reusable scripts**: `scripts/run_tier3_reisolated_rerun.py`, `scripts/verify_select_best_fallback_candidate.py`.
- **1 untracked data file**: `claude_relay/facts_m5.jsonl`.
- **research/ directory** (5 files: `CURRENT_STATE.md`, `FINDINGS.md`, `OPEN_QUESTIONS.md`, `DECISIONS.md`, `EXPERIMENT_INDEX.md`) — **tracked and committed** in `cfd01b7` (2026-09-09); `FINDINGS.md` and `OPEN_QUESTIONS.md` carry small further uncommitted modifications on top of that commit (2 lines each — not independently traced in this pass, low apparent stakes).

**Methodological disclosure for this audit itself**: given 63 files (est. 1.5–2MB of prose), this pass did not independently read every file end-to-end. It relied heavily on `research/*.md` — itself a real, evidence-labeled, append-only synthesis of most of this corpus, already committed to git — cross-checked by direct reads of `research_state_consolidation.md` in full, direct grep-extraction of executive summaries/verdicts from the files `research/*.md` does *not* cover (the task-type-classifier and Codex threads), and independent live-system verification of the single most load-bearing liveness claim in the corpus (see Superseded Findings). This mirrors `research/*.md`'s own disclosed depth-of-review discipline, and the same limitation applies here: claims sourced from `research/*.md` are labeled **SUPPORTED/REMEMBERED** (a real, self-consistent, evidence-labeled prior synthesis) rather than **VERIFIED/OBSERVED** by this pass specifically, except where explicitly noted as independently re-checked.

---

## September Research Timeline

*(GENERATED — reconstructed from file dates, `research/EXPERIMENT_INDEX.md`'s own mission numbering, and git commit dates. Mission numbers are as the corpus itself uses them; note two overlapping numbering sequences exist — see caveat below.)*

- **2026-09-01 to 09-05** (predates the untracked window; already covered by CLAUDE.md Findings 86–95, and by `research/`'s own citations to `2026-09-03_self_modification_*` and `2026-09-05_public_sharing_readiness_review.md`): the self-modification causal-chain reconstruction (→ R-003/R-004/R-005/R-008), preference-provenance protocol freeze, public-sharing readiness review.
- **2026-09-06**: RiverBrain capability-pilot forensics conclude (Tier-5 through Tier-8, already in CLAUDE.md Finding 87–89); `real_trace_f2_provenance` experiment run (→ the scratch pickle, see below); 27-day showcase Phase 0/6.
- **2026-09-07** (8 files): authority/consequence-boundary groundwork, shadow-treatment harness archaeology, attempt-level provenance feasibility — largely scaffolding for the epistemic-arbitration thread that follows.
- **2026-09-08** (34 files, the single densest day in the corpus): the epistemic-arbitration thread proper — Mechanism C (evidence-injection), generation-time epistemic revision, Living/Persistent Self-Model design and implementation, sensory-gate fix (the one authorized production change this thread made), adversarial pressure testing, taxonomy-laundering discovery. Also: `select_best_fallback_candidate()`'s Tier-6/Tier-7 forensic basis (via `PENDING_DECISIONS.md` #20, dated 2026-09-09 build but referencing prior audits).
- **2026-09-09** (13 files, plus `cfd01b7`/`e92ec3b` commits): the F2 stdin-contract chain runs start-to-finish in one day (Missions 24–30: timeout forensics → contract archaeology → resolution experiment → enforcement boundary → implementation → OS-level fd0 forensics → implementation), largely **committed same-day**; `research/*.md` index committed; the task-type-classifier causal audit (Missions 32–35) and Codex-relay architecture investigation run as **separate, parallel threads**, producing `app/experiments/task_type_ground_truth/` and `codex_relay/`; `PENDING_DECISIONS.md` #20–23 closed (restore council gate, fallback-candidate fix, Tier-3 reisolated rerun, temporal_environment split — `e92ec3b`'s own commit covers #23 only, the rest remain uncommitted).
- **2026-09-10**: one file (`epistemic_invocation_and_provenance_isolation.md`, Mission 13) — pre-response-diagnostic and provenance-representation isolation experiment.
- **2026-09-11** (7 files, this session and the one immediately prior): false-verification replication, authority-vs-escalation causal isolation (Missions 19–20), the unresolved-defect sweep that discovered `echo_projects_autonomy`'s liveness gap (Mission 21), Git-provenance interface design (Mission 18, still in progress), and the research-state consolidation itself.

**Numbering caveat (OBSERVED)**: `research/FINDINGS.md`/`EXPERIMENT_INDEX.md` use "Mission N" labels that restart or overlap across different investigating sessions — e.g., "Mission 19/20/21" appears both as part of the 1–30 F2-stdin/epistemic sequence *and* as "this session[']s own" numbering in several 2026-09-11 entries. This is a real, minor provenance-hygiene gap in the research corpus's own numbering discipline — not confusing enough to break traceability (every claim still cites its actual filename), but worth flagging as a paper-cut for whoever maintains this index next.

---

## Audit → Finding → Decision → Implementation → Verification → Documentation Graph

Chains below are the mission's most load-bearing ones. Each link is labeled per-link, not per-chain — a strong early link does not imply a strong late one.

### Chain 1 — F2 sandbox stdin/fd0 contract (Missions 24–30)
```
AUDIT (2026-09-09_f2_sandbox_timeout_forensics.md, OBSERVED file exists)
  → FINDING: subprocess inherits run.py's live tty stdin, input() hangs (OBSERVED, root-caused via direct reproduction per the report's own text — SUPPORTED, not independently re-run by this audit)
  → DECISION: enforce at safe_exec_wrapper.py via sys.stdin replacement + os.close(0), not run_script.py (SUPPORTED, cited reasoning in Missions 27/29)
  → IMPLEMENTATION: sandbox/safe_exec_wrapper.py's _install_patches() (OBSERVED — this session independently read the current diff; sys.stdin=_BlockedStdin() already committed via 1081f26; _os.close(0) still uncommitted, present in current working-tree diff)
  → VERIFICATION: liveness_ledger.py's f2_stdin_contract check, extended this pass to cover os_fd0_blocked independently (OBSERVED — read the diff directly; the check itself is a static source-anchor, not a functional re-test, by the report's own disclosed design choice)
  → DOCUMENTATION: NONE in CLAUDE.md (OBSERVED — CLAUDE.md's Liveness Ledger table and Self-Edit Safety Pipeline sections make no mention of a stdin/fd0 contract anywhere in the content available to this audit)
```
**Chain status: COMPLETE through Verification, BROKEN at Documentation.** This is the strongest engineering chain in the corpus and the single most consequential documentation gap — a real, live, security-relevant sandbox boundary is running in production, undocumented.

### Chain 2 — `/admin/restore` council gate (`PENDING_DECISIONS.md` #20-adjacent work, this session)
```
AUDIT: CLAUDE.md's own "Standing Principle" section (2026-07-18), naming /admin/restore as an unbuilt protection gap (OBSERVED — read directly)
  → FINDING: no second-signer/review exists on this specific continuity-altering action (OBSERVED, by omission)
  → DECISION: additive advisory council review, mirroring propose_core_edit()'s proven non-hollow pattern (OBSERVED — read run.py's diff directly, docstring states this reasoning explicitly)
  → IMPLEMENTATION: run.py's admin_restore(), snapshot_manager.py's _council_review_restore()/_build_restore_dissent_entry()/_log_restore_dissent_entry() (OBSERVED — full diff read this session, syntax-clean)
  → VERIFICATION: liveness_ledger.py's new restore_council_gate check — a combined static-anchor + ground-truth cross-check against real dissent-log entries (OBSERVED — read directly); NOT yet exercised against a real restore (SUPPORTED only — the check's own "no real restores since deployment" honest-pass branch was read but not triggered)
  → DOCUMENTATION: PENDING_DECISIONS.md item #20's dated closing note documents this in detail (OBSERVED). CLAUDE.md: NONE.
```
**Chain status: COMPLETE through Verification (with one honest caveat — the ground-truth half is untested against real activity), PARTIAL at Documentation** — real documentation exists, but not in the canonical ledger.

### Chain 3 — `select_best_fallback_candidate()` rewrite
```
AUDIT: audits/tier6_disagreement_resolution_forensic.md + tier7 (REMEMBERED via PENDING_DECISIONS.md #20's own citation — not independently re-read this pass)
  → FINDING: "prefer longest" heuristic is a confound for councillor identity, not a correctness signal (SUPPORTED)
  → DECISION: 3-stage rule; RiverBrain tiebreak explicitly NOT deployed per Tier-7's own "do not deploy" recommendation (OBSERVED — read directly in the code docstring and PENDING_DECISIONS.md)
  → IMPLEMENTATION: river_deliberation.py (a forbidden-edit-target file; OBSERVED, full diff read this session)
  → VERIFICATION: scripts/verify_select_best_fallback_candidate.py, replayed against the real captured Tier-4 corpus (OBSERVED script exists; its reported 78.2%→96.1% result is SUPPORTED/REMEMBERED from PENDING_DECISIONS.md's own text, not independently re-run by this audit)
  → DOCUMENTATION: PENDING_DECISIONS.md #20 (OBSERVED, thorough). CLAUDE.md: NONE.
```
**Chain status: COMPLETE through Verification, PARTIAL at Documentation.**

### Chain 4 — `task_type_classifier.py` causal audit (Missions 32–35)
```
AUDIT: 2026-09-09_mission32_task_type_classifier_causal_audit.md (OBSERVED, exec summary extracted this pass)
  → FINDING: 99.5% of real training signal traces back to the same static heuristic it's meant to be independent of; L2 not L3 (SUPPORTED, cross-checked by Mission 33's independent-review pass, itself read this session)
  → DECISION: build a genuinely independent gold-label dataset to test whether independent supervision helps (OBSERVED, Mission 33's own design)
  → IMPLEMENTATION: app/experiments/task_type_ground_truth/ (OBSERVED — read schema.py directly; confirmed via grep zero production imports)
  → VERIFICATION: Missions 34/35 ran the experiment twice (human-labeled and fresh-LLM-labeled gold sets) — result: NULL/inconclusive, ranking of conditions flips depending on labeler (OBSERVED, exec summaries read directly)
  → DOCUMENTATION: NONE — not in research/*.md's own index (confirmed by direct inspection of EXPERIMENT_INDEX.md, which does not row Missions 32-35 anywhere, including its own "not individually rowed" disclosure list), and NONE in CLAUDE.md.
```
**Chain status: COMPLETE through Verification (a genuine, self-aware negative result, not a failure of method), BROKEN at Documentation — doubly so, since even the corpus's own internal index missed it.** Two real, unfixed bugs surfaced as a side effect (a bare "I"/"my" pronoun misrouting `compute_intent_heatmap()`, and `/mirror_echo` bypassing the classifier gate entirely) are **orphaned** — see below.

### Chain 5 — Codex relay architecture
```
AUDIT: 2026-09-09_openai_codex_local_agent_architecture_investigation.md (+ the superseded-in-part subscription-independence proof) (OBSERVED, exec summaries read directly)
  → FINDING: Codex CLI viable for an unattended mailbox-pattern relay; API-key auth recommended over subscription for the automated piece (SUPPORTED)
  → DECISION: build codex_relay/ mirroring claude_relay/'s existing pattern (INFERRED from the code's existence and structure — no explicit decision document connecting the finding to the build was found)
  → IMPLEMENTATION: codex_relay/ (relay.py, README.md, test_relay.py) (OBSERVED — directory contents listed, zero production imports confirmed via grep, no secrets found via targeted scan)
  → VERIFICATION: UNKNOWN — claude_relay/from_m5.md's uncommitted diff references live cross-machine Codex-relay testing in progress ("Air Codex now reaches M5... gets HTTP 404"), suggesting real but incomplete end-to-end verification (SUPPORTED, not independently re-tested by this audit)
  → DOCUMENTATION: NONE anywhere — not in research/*.md, not in CLAUDE.md.
```
**Chain status: PARTIAL through Verification (real but incomplete/in-flux), BROKEN at Decision (no explicit rationale document) and Documentation.**

---

## Orphaned Findings

### A. Implemented but undocumented (in CLAUDE.md)
1. **F2 stdin/fd0 sandbox contract** (Chain 1) — the most severe instance: partially *already committed to git and live in production* with zero CLAUDE.md acknowledgment.
2. **`/admin/restore` council gate + Dissent Log extension** (Chain 2).
3. **`select_best_fallback_candidate()` 3-stage rewrite** (Chain 3).
4. **`temporal_environment.py` MacBook/phone location split** (`PENDING_DECISIONS.md` #23; independently reviewed and verified correct in a prior pass this session).
5. **`echo_ground_truth.py`'s see/hear conjunction regex fix** — the one explicitly-authorized production change inside the epistemic-arbitration thread (Mission 5, `2026-09-08_sensory_gate_fix_and_provenance_forensics.md`, REMEMBERED); independently reviewed and verified correct in a prior pass this session.

### B. Documented but unimplemented
1. **Mission 18's read-only Git-provenance interface** — an extensively designed (~29KB design doc, evidence-hierarchy, threat model) capability with **zero code anywhere** (confirmed via direct grep for plausible identifiers: `read_only_git`, `git_provenance`, `ReadOnlyGit` — no hits in `app/` or `run.py`). Correctly labeled `[UNRESOLVED — active design mission]` in `research/CURRENT_STATE.md` itself — this is *not* a broken promise, it's an honestly-labeled in-progress design. Included here because a future reader of `research/DECISIONS.md` D-003 could otherwise mistake the decision for a shipped capability.

### C. Investigated but intentionally rejected (not failures — recorded as such)
1. **Condition C epistemic taxonomy** (OBSERVED/DERIVED/INFERRED/SPECULATIVE/IMAGINED) — proposed and revoked within 24 hours (Mission 7→8), formalized as `research/DECISIONS.md` D-001. Good example of the methodology working as intended.
2. **RiverBrain historical-score tiebreak for `select_best_fallback_candidate()`** — Tier-7's own "do not deploy before further validation" recommendation was respected; stage 2 deliberately skipped in the shipped code (Chain 3).
3. **Reusing real historical prompts for the task-type gold-label dataset** — Mission 33's own sketch, explicitly reconsidered and rejected by Mission 34 before building, to avoid giving the production classifier a hidden home-field advantage.

### D. Investigated with no discernible consequence (possible research churn)
1. **Q-004** (hypothesis-formation / competing-explanation comparison) — flagged as a real capability gap, explicitly "not yet designed," no next step exists.
2. **Q-006** (is RiverBrain's trust-gate history representative of a broader "automated trust never self-activates" pattern?) — proposed as "a dedicated audit of every trust-gated mechanism," not run.
3. **Q-005** (does memory retrieval materially influence model selection?) — restates a gap already identified in CLAUDE.md Finding 76 (July) with the same proposed next experiment (`temperature=0` rerun) still not run, two months later, across two separate research passes now.

**Note on Category D's real size**: `research/EXPERIMENT_INDEX.md`'s own "Groups not individually rowed" disclosure already accounts for most of the corpus's remaining bulk as *parts of larger, consequential threads* (e.g., the ~9 Sept 8 self-model sub-phase files feed directly into the Living/Persistent Self-Model implementation), not as standalone dead ends. This audit did not independently re-verify that disclosure's accuracy file-by-file — it is SUPPORTED/REMEMBERED, not VERIFIED. If it is wrong, Category D is larger than stated here.

---

## Superseded Findings

1. **R-010 / Q-009 — `echo_projects_autonomy` "65.9+ hour silent gap"** (`audits/2026-09-11_feralecho_unresolved_defect_audit.md`, Mission 21). **This audit independently re-checked this claim against the live, currently-running server** (OBSERVED, this session, via `GET /admin/liveness-status`): the `echo_projects_autonomy_activity` check currently reports `pass: true`, evidence: *"Last real autonomous cycle was 6.1h ago (within the 12h tolerance), status='f2_failed', spec_source='garden'"* — a real cycle fired at `2026-09-10T23:53:01Z`. **The specific liveness-gap claim (nothing has fired) is now stale/superseded by direct observation** — the loop is firing, it is simply still failing F2 on generation quality, which is a different, narrower problem than the one Mission 21 flagged. This directly and favorably answers half of `research/OPEN_QUESTIONS.md` Q-009 (the scheduler is not permanently stalled) without resolving the other half (why the underlying F2 failure rate is still apparently high — not independently checked this pass).
2. **Mission 21's specific root-cause claim** ("a real cross-file import inconsistency") for the failure that motivated R-010 — directly corrected by Mission 22 (the referenced class was found, on re-inspection, to genuinely exist; the causal claim was unsupported by the truncated evidence it was based on). Preserved by the corpus itself as a stated correction, not silently fixed — good methodology, cited here as a positive example.
3. **`research/DECISIONS.md` D-002** ("false verification... replication in progress") is **internally stale relative to `research/EXPERIMENT_INDEX.md` E-035 in the same committed index**, which already marks the replication `REPLICATED, with qualification`. Both files were committed together in `cfd01b7`; this is a real, small, self-inconsistency inside the corpus's own canonical index, not a hypothetical risk.
4. **R-002's "authority marker overrides evidence" framing** — narrowed twice in sequence within the corpus itself: first by R-009 (checkability + escalation-structure matter, not authority-framing alone), then by R-009's own Mission 20 update (authority is *not required* for the dominant capture effect; only a narrow, secondary, false-verification-claim-rate effect survives). The corpus's own discipline of dated "Update" annotations rather than silent rewrites makes this traceable — a real strength of this methodology, worth preserving as a pattern.
5. **`audits/2026-09-09_codex_headless_subscription_independence_proof.md`'s own "YELLOW" verdict** — explicitly superseded in part by its own later "Part 2" section in the same file, after installation was separately authorized and performed.
6. **"Self-edit's real success rate is near zero"** — corrected to 426/463 (~92%) via direct log recount; the corpus is explicit that this was a grep-methodology error, not a real system property (R-003). Already independently, separately confirmed in CLAUDE.md's own history (Finding 22 Batch 4-adjacent material describes the fitness-gate mechanism this rate measures) — this is a case of the research corpus re-deriving a number CLAUDE.md's engineering history had different visibility into; not a contradiction, but worth flagging that the two ledgers were computing similar-sounding numbers somewhat independently.

---

## CLAUDE.md Reality Gap

**CLAUDE.md's last dated content available to this audit is Finding 95 (2026-09-05, the RAOC harness build).** Everything below is dated after that.

### Claims that remain supported
- Nothing in this corpus contradicts any CLAUDE.md claim dated 2026-09-05 or earlier. The one apparent tension (R-004's fitness-gate saturation finding) is actually a re-derivation *confirming* CLAUDE.md's own Finding 91, not a conflict.

### Claims that are now outdated
- **CLAUDE.md's Liveness Ledger table** (documented as reaching a specific check count as of Finding 85, later editions of this doc). **This session's own live query shows 52 checks currently passing** — a real, undocumented growth of at least 11 checks since CLAUDE.md's own table was last updated, including at minimum `f2_stdin_contract` and (per this session's own reviewed diff) `restore_council_gate`, neither of which appears in CLAUDE.md's check table.
- **CLAUDE.md's Snapshot and Restore System section** — describes `/admin/restore` as "alert-and-propose, human-confirmed only," which remains true, but omits the new council-review layer sitting in front of it (Chain 2).

### Important September findings absent from CLAUDE.md
1. The full F2 stdin/fd0 sandbox-contract chain (Chain 1) — a real, security-relevant, partially-already-shipped hardening of the self-edit and `echo_projects` sandbox boundary.
2. `/admin/restore`'s new council-review gate (Chain 2) — directly closes a gap CLAUDE.md's own "Standing Principle" section (2026-07-18) named as unbuilt.
3. `select_best_fallback_candidate()`'s rewrite (Chain 3) — a real, measured (78.2%→96.1% on the real corpus) improvement to council-disagreement resolution.
4. `temporal_environment.py`'s location-source split (`PENDING_DECISIONS.md` #23).
5. `echo_ground_truth.py`'s see/hear conjunction fix.
6. The convergent R-001/R-002 finding ("authority markers can override evidence, and this is a regression risk if naively 'fixed'") — arguably the single most important negative architectural result in this entire corpus, with real implications for any future mechanism CLAUDE.md's own "Emergence roadmap" style sections might propose. Currently exists only in `research/FINDINGS.md`, which is not cross-referenced from CLAUDE.md at all.
7. `echo_projects_autonomy`'s real, current 0/61 historical success rate (Mission 22) and its now-superseded liveness-gap symptom (see above) — CLAUDE.md's own Finding 85 introduced `echo_projects_autonomy` and would be the natural place for a status update.
8. Two real, unfixed bugs from the task-type-classifier audit: `compute_intent_heatmap()`'s bare "I"/"my" pronoun misrouting, and `/mirror_echo` bypassing the classifier gate.
9. The Codex-relay architecture and its live cross-machine testing status.

### Findings that should NOT be added to CLAUDE.md as currently stated
1. **The Condition C taxonomy** — already correctly recorded as "do not deploy" (D-001); it never shipped, and CLAUDE.md documents shipped/live mechanisms plus explicitly-flagged-and-deferred ones, not every rejected design.
2. **The codex subscription-independence proof's original "YELLOW, untested" verdict** — superseded by its own Part 2; citing it would introduce a stale claim into CLAUDE.md on day one.
3. **Mission 21's "cross-file import inconsistency" root-cause claim** — already self-corrected by Mission 22; citing the original would reintroduce a disproven claim.
4. **Most of the ~9 individual Sept 8 self-model sub-phase files** — `research/FINDINGS.md`/`CURRENT_STATE.md` already synthesize this thread's terminal conclusions; inlining each phase file into CLAUDE.md would duplicate, not improve, the record. A single CLAUDE.md pointer to `research/*.md` (the way CLAUDE.md already points to `Desktop/Forensic Audit/` for a different corpus) is the right level of indirection, not a full Finding per phase.

---

## New Artifact Provenance

| Artifact | Problem that caused it | Source audit/finding | Experimental or production? | Verification | Live-imported? | Documented anywhere? | Safe to commit as-is? |
|---|---|---|---|---|---|---|---|
| `codex_relay/` | Need for an unattended, subscription-independent Codex↔Codex mailbox channel between M5/Air | `2026-09-09_openai_codex_local_agent_architecture_investigation.md` + subscription-independence proof | **Experimental** — real, structured, tested in isolation; cross-machine round-trip appears in-progress per uncommitted `claude_relay/from_m5.md` diff | Partial — component-level tests exist (`test_relay.py`); full cross-machine round-trip status UNKNOWN to this audit | **No** — confirmed via grep, zero references from `app/`, `run.py` | No — absent from `research/*.md` and CLAUDE.md | Needs the in-progress cross-machine verification resolved first; no secrets found in a targeted scan, so no blocker on that front |
| `app/experiments/task_type_ground_truth/` | Test whether `task_type_classifier.py`'s apparent learning survives contact with a genuinely independent supervision signal | `2026-09-09_mission33_independent_ground_truth_audit.md` (design), Missions 34/35 (execution) | **Experimental**, explicitly modeled on the existing `raoc/`/`preference_provenance/` isolation convention per its own docstring | Real — two independent gold-label runs, result NULL/inconclusive at this scale, honestly reported | **No** — confirmed via grep | No — absent from `research/*.md`'s own index and from CLAUDE.md | Yes, low risk — self-contained, isolated, produced a real negative result worth preserving as a record even though the underlying question stays open |
| `scripts/run_tier3_reisolated_rerun.py` | Re-run two isolation-tainted Tier-3 sub-results cleanly | `PENDING_DECISIONS.md` #21 (CLAUDE.md Findings 87–89's own thread) | Reusable verification tool, already used once for real | Its own output (`audits/tier3_apparatus/*_REISOLATED_RERUN_*.jsonl`) is present and untracked | N/A (standalone script) | Yes — `PENDING_DECISIONS.md` #21 documents its use and result in detail | Yes |
| `scripts/verify_select_best_fallback_candidate.py` | Reusable replay methodology for Chain 3's verification | `PENDING_DECISIONS.md` #20 | Reusable verification tool, already used | Self-verifying by design (replays against the real captured corpus) | N/A | Yes — `PENDING_DECISIONS.md` #20 | Yes |

---

## Stale Worktree Assessment

OBSERVED, via `git worktree list`, `git status`, `find`:

- **Identity**: `worktree-agent-abe6ecca0408fd0fb`, registered at `.claude/worktrees/agent-abe6ecca0408fd0fb/`.
- **Base commit**: `a23b9403f18973e1964f6b9647971f560792d54f` — "Retire mlx:gemma3, add MLX memory cap for qwen3 (Finding 74)", dated 2026-07-22.
- **Age relative to current HEAD**: 59 commits behind.
- **Unique untracked content**: `.audit_scratchpad/` (7 files: `depgraph.json`/`.py`, `orphans.py`, `phase1_map.md`, `phase2_dependencies.md`, `phase2_5_ghost_code.md`, `phase3_architecture.md`, all dated 2026-07-23) and `FERALECHO_FORENSIC_AUDIT.md`.
- **`FERALECHO_FORENSIC_AUDIT.md` is NOT unique** — an identically-named file exists in the main working tree (`OBSERVED via find`). Content was not diffed byte-for-byte in this pass (UNKNOWN whether they're identical or diverged).
- **`.audit_scratchpad/`'s 7 files were NOT independently checked for content overlap** against the main tree's own extensive July audit history (CLAUDE.md Findings 28/30 cover exactly this kind of dependency-graph/orphan-code sweep from the same week) — UNKNOWN whether this is redundant or genuinely unique material.
- **No current code or documentation references anything inside `.claude/worktrees/`** (OBSERVED via grep across `app/`, `run.py`, `CLAUDE.md`'s content, `research/*.md`).

**Recommendation**: likely safe to remove later, but not yet confirmed to the standard this report otherwise holds itself to — a single follow-up step (diff `FERALECHO_FORENSIC_AUDIT.md` between the worktree and main tree; skim `.audit_scratchpad/`'s 7 files against CLAUDE.md's July 22-24 Findings for overlap) would close the remaining uncertainty cheaply. Do not delete based on this report alone.

---

## Scratch Artifact Assessment

OBSERVED, via direct file inspection and cross-referencing five separate audit mentions:

- **Generator**: `app/experiments/real_trace_f2_provenance/run_real_self_edit.py` (a real, checked-in — though itself untracked — script with its own hardcoded `SCRATCH_DIR = "app/experiments/real_trace_f2_provenance/_scratch"` constant).
- **Origin mission**: `audits/2026-09-06_real_trace_f2_provenance_liveness.md`, which explicitly names the pickle in its own Files-Changed section as *"scratch decoy, not real state."*
- **Referenced/disclosed by five later audits** (`2026-09-07_shadow_treatment_harness_archaeology.md`, `2026-09-07_attempt_level_provenance_feasibility.md`, `2026-09-10_epistemic_invocation_and_provenance_isolation.md`, `2026-09-11_verification_and_level_7_5_8_feasibility.md`, and this document) as a known, intentionally-preserved, pre-existing untracked path — every one of them explicitly notes it was "left untouched," not accidentally created.
- **Reproducible**: yes — `run_real_self_edit.py` exists and regenerates it on demand.
- **Contains information unavailable elsewhere**: no evidence either way was found in this pass; UNKNOWN, low-stakes given it's an explicitly-labeled decoy/scratch copy, not a unique data source.
- **Does CLAUDE.md Finding 89 accurately describe this specific artifact?** **No** — Finding 89 documents a different (though philosophically related) mechanism: `tempfile.mkdtemp()`-generated scratch directories under `/tmp`, created by `install_isolation()` for RiverBrain-contamination testing in the Tier-3–8 capability-pilot lineage, with the explicit caveat that those "don't auto-clean... accumulate under /tmp." **This artifact is a different mission's own fixed, named, project-local path** (not under `/tmp`, not from `install_isolation()`), generated once by a single dedicated script. Same spirit (isolated copy, safely left behind), different mechanism and different mission — Finding 89's text should not be cited as covering this specific file.

**Recommendation**: leave untouched, or `gitignore` it — it is disclosed, harmless, reproducible, and explicitly labeled as scratch by its own originating mission. Not a priority.

---

## Quantitative Classification

*(Counts are this audit's own classification of the corpus's ~63 untracked `audits/*.md` files plus the 5 committed `research/*.md` files, based on the evidence gathered above — not a claim of exhaustive per-file reclassification. Category boundaries below are best-effort; some threads plausibly span two categories.)*

| Category | Approx. count | Basis |
|---|---:|---|
| Architectural consequence (real code shipped or currently live) | ~6 findings / ~10 files | F2 stdin chain (7 files), restore-council-gate + fallback-candidate + temporal_environment work (documented in PENDING_DECISIONS, source files reviewed separately), sensory-gate fix |
| Implemented fix, undocumented in CLAUDE.md | 5 (listed in Orphans A) | Cross-referenced against CLAUDE.md's available content |
| Experiment only (real, run, no production change) | ~15 files | Task-type-classifier thread (4), epistemic-arbitration adversarial-pressure/replication series (~11) |
| Rejected proposal | 3 (D-001, RiverBrain tiebreak, historical-prompt reuse) | `research/DECISIONS.md` + PENDING_DECISIONS.md |
| Superseded finding | 6 (listed above) | Direct cross-reference within the corpus + one independently re-verified by this audit |
| Documentation-only finding (design, no code) | ~2 threads (Mission 18 Git-provenance; several self-model design-phase files) | Confirmed via grep (zero code) |
| Duplicate/redundant research | 0 confirmed | `research_state_consolidation.md`'s own claim of "no true duplicates found," not independently falsified by this pass |
| Unresolved (open question, real next-step defined) | 7 (Q-001 through Q-009 minus the 3 answered this arc) | `research/OPEN_QUESTIONS.md` |
| No discernible consequence / possible churn | ~3 (Q-004, Q-006, Q-005's repeat) | See Orphans D |
| **Title-level only, not independently reviewed this pass (by either this audit or `research/*.md` itself)** | ~10-15 files | Several Sept 8 self-model sub-phase files not individually confirmed against `EXPERIMENT_INDEX.md`'s own "not rowed" list |

**Reading**: the arc is **not** primarily research churn. The largest single category by file count (epistemic-arbitration adversarial testing) produced a real, convergent, three-times-independently-discovered negative finding (R-001/R-002) with direct, stated implications for future mechanism design (Mission 18's own threat model already cites it) — that is a durable engineering consequence, even though it did not ship code. The genuinely low-consequence tail (Category "no discernible consequence") is small, ~3 items, all explicitly flagged as open by the corpus's own discipline rather than silently dropped.

---

## Top Architectural Consequences

*(Ranked by actual consequence to what FeralEcho currently is or does, not by how interesting the finding sounds — per the mission's own instruction.)*

1. **R-001/R-002 — verified evidence in context does not reliably override Echo's generated belief, and authority-flavored scaffolding can make this worse, not better.** Evidence: 3 independently-designed threads converging (SUPPORTED, multiply cross-referenced within the corpus). Decision: do not deploy Condition C (D-001); treat any future "verification flag" design as high-risk by default (D-004/D-007). Consequence: no code shipped, but this is a real constraint on every future mechanism-design decision in this project going forward — the highest-leverage *negative* result in the corpus. Documentation: **absent from CLAUDE.md.**
2. **F2 stdin/fd0 sandbox contract, now live.** Evidence: OBSERVED this session (current diff + live liveness-check count). Decision → implementation → verification: complete. Consequence: closes a real, previously-undocumented sandbox-escape-adjacent gap (a generated program could hang the sandbox indefinitely, or — pre-fix — read a live terminal). Documentation: **absent from CLAUDE.md**, despite being partially already committed to git.
3. **`/admin/restore`'s new council-review gate.** Evidence: OBSERVED, full diff reviewed. Consequence: directly closes a gap CLAUDE.md's own "Standing Principle" section named as unbuilt over a month ago. Documentation: PENDING_DECISIONS.md only.
4. **`echo_projects_autonomy`'s real 0/61 historical success rate, and this audit's own live-verified correction that the liveness-gap symptom is now stale.** Evidence: VERIFIED (independent, live re-query this session). Consequence: the underlying capability (Finding 85's flagship "autonomous investigation" mechanism) has never once succeeded in its full operational history — a materially important fact about a mechanism CLAUDE.md currently describes without this caveat.
5. **`select_best_fallback_candidate()` rewrite.** Evidence: real, corpus-verified improvement (78.2%→96.1%). Consequence: directly improves council-disagreement resolution quality for every real multi-model deliberation going forward.
6. **`task_type_classifier.py` is L2, not L3 — its apparent learning is 99.5% traceable to the same heuristic it's meant to be independent from.** Evidence: SUPPORTED, independently cross-checked by a dedicated review mission within the corpus itself. Consequence: tempers any future claim that this classifier represents genuine independent learning; two real, unfixed bugs surfaced as a byproduct.
7. **`temporal_environment.py`'s location-source split.** Evidence: OBSERVED, verified in a prior pass this session. Consequence: a real correctness fix (previously-merged MacBook/phone location signals, now separated) plus a dead-endpoint fix (`ipapi.co`→`ip-api.com`).
8. **Two internal self-inconsistencies found within `research/*.md`'s own committed index** (D-002 vs. E-035; Mission 21's self-corrected root-cause claim). Consequence: modest on its own, but a useful signal about how quickly even a well-disciplined index can drift internally without a maintenance pass.
9. **Codex-relay architecture.** Evidence: real, isolated code exists; cross-machine status in flux. Consequence: a real new inter-agent communication channel, currently unverified end-to-end and completely undocumented outside its own source audits.
10. **`echo_ground_truth.py`'s see/hear conjunction fix.** Evidence: OBSERVED, verified in a prior pass. Consequence: small but real correctness improvement to Echo's sensory ground-truth grounding.

---

## Final Verdict

1. **Does the Sept 7–10(–11) arc have a coherent causal history?** Yes, for each of the four identified work streams individually (SUPPORTED to VERIFIED per chain above) — but there is no single overarching narrative; treating it as "one arc" would itself be a documentation error. The corpus's own dated-annotation discipline (never silently overwriting a prior claim) is genuinely strong methodology, observed directly in R-002/R-009's revision history.
2. **How much actually changed the live architecture?** A meaningful amount, concentrated in a few places: the F2 stdin/fd0 sandbox contract (partially committed, fully live), the sensory-gate regex fix, and — pending commit — the restore council gate, fallback-candidate rewrite, and location split. Most of the epistemic-arbitration thread's ~40 files changed **understanding**, not code (by design — D-006 explicitly commits this thread to investigation-only by default).
3. **How much remains merely experimental?** The majority by file count: the epistemic-arbitration adversarial-testing series, the task-type-classifier ground-truth experiment, and the in-flight Codex-relay cross-machine testing.
4. **How much is now obsolete?** A small, explicitly-disclosed set (6 items, Superseded Findings above) — importantly, all self-disclosed by the corpus's own later missions, not discovered as silent drift by this audit alone (with one exception: the `echo_projects_autonomy` liveness-gap staleness, which this audit did independently re-verify and correct).
5. **How severe is the current documentation/reality gap?** **Severe, and getting worse, not stable.** CLAUDE.md's own Finding 86 was created specifically to backfill a prior ~6-week gap; this corpus represents a further, continuous ~5–6 day gap on top of that, including a live production sandbox-hardening change (Chain 1) that CLAUDE.md's readers currently have zero way to know exists.
6. **Are there architectural claims FeralEcho currently makes that the evidence no longer supports?** One found directly: the implicit framing (nowhere explicitly false, but nowhere corrected either) that `/admin/restore` has "no second-signer" protection — CLAUDE.md's own "Standing Principle" section still reads as an open gap; it is not, as of this uncommitted work.
7. **Are there implemented mechanisms the canonical documentation doesn't yet acknowledge?** Yes — the F2 stdin/fd0 contract, most severely (already live), plus the restore council gate, fallback-candidate rewrite, and location split.
8. **Is `codex_relay` mature enough to be treated as a separate commit?** Not yet — real, isolated, no secrets found, but its own cross-machine verification appears incomplete (UNKNOWN final status per this pass) and it has zero decision-document tracing why it exists in this exact form. Recommend resolving the live cross-machine test first.
9. **Is the stale worktree safe to clean later?** Likely, but not confirmed to this report's own evidentiary standard — one cheap follow-up check (diff the duplicate file, skim the scratchpad against existing July Findings) is recommended before deleting.
10. **Is the scratch pickle safe to clean later?** Yes — disclosed, reproducible, explicitly labeled scratch by its own originating mission, referenced by name in five later audits specifically to note it should be left alone. Lowest-priority item in this entire report.
11. **What should be committed now?** In order of confidence: the F2 stdin/fd0 implementation + its own audit report (Chain 1 — already half-committed, finish it); the restore council gate (Chain 2); the fallback-candidate rewrite (Chain 3) and its verification script; `research_state_consolidation.md` itself (its own deliverables are already committed — committing the report that explains them closes a real, ironic gap this audit found). All were independently reviewed and found legitimate in a prior pass this session, and none require production risk beyond what's already running.
12. **What should remain uncommitted pending further investigation?** `codex_relay/` (pending cross-machine verification), the task-type-classifier experiment package (real negative result, low urgency either way), the ~55 remaining epistemic-arbitration audit files (recommend committing as a single research-archive batch once someone decides whether CLAUDE.md gets a pointer-Finding to `research/*.md` or a fuller backfill — a decision, not a default).

---

## Recommended Next Actions

1. **Write one CLAUDE.md Finding (or a short pointer-Finding, matching the existing "Desktop/Forensic Audit" pattern) that (a) links to `research/*.md` as the canonical epistemic-arbitration/self-model ledger, and (b) individually documents the F2 stdin/fd0 contract, the restore council gate, the fallback-candidate rewrite, and the location split** — these four are concrete, verified, in-CLAUDE.md's-normal-style engineering changes, unlike the research corpus's broader findings.
2. **Commit `audits/2026-09-11_research_state_consolidation.md`** — closes the one clean "artifact committed, its own explanation not" gap this audit found.
3. **Resolve `codex_relay/`'s live cross-machine test status** before deciding whether to commit it.
4. **One cheap follow-up on the stale worktree** (diff the duplicate file, skim the scratchpad) before recommending deletion with full confidence.
5. **Do not re-open Q-001/Q-002/Q-008 by default** — they are genuinely open, correctly labeled, and each already has a next discriminating experiment specified in `research/OPEN_QUESTIONS.md`; re-litigating them without new evidence would be exactly the research-churn this audit was asked to watch for.
6. **A future pass should independently verify `research/EXPERIMENT_INDEX.md`'s own "no true duplicates found" claim** — this audit relied on it (SUPPORTED, not VERIFIED) and did not have budget to falsify it directly.

---

## Integrity / Tally

```
Audit documents examined (audits/*.md, untracked, ~65 requested / 63 confirmed):
  - Full read: 1 (research_state_consolidation.md)
  - Executive-summary/verdict extraction (direct grep of this document's contents): 8
    (mission32, mission33, mission34, mission35, codex_headless_subscription_independence_proof,
     openai_codex_local_agent_architecture_investigation, read_only_git_provenance_design [partial])
  - Relied upon via research/*.md's own pre-built, evidence-labeled index (SUPPORTED/REMEMBERED,
    not independently re-read this pass): ~40
  - Title-level only, neither independently read nor covered by research/*.md's own index: ~14
  (research/*.md's 5 companion files, all tracked/committed, were read in full: CURRENT_STATE.md,
   FINDINGS.md, OPEN_QUESTIONS.md, DECISIONS.md, EXPERIMENT_INDEX.md)

Provenance chains fully established (Audit→Finding→Decision→Implementation→Verification, with
Documentation the only broken link): 5 (F2 stdin contract; restore council gate; fallback-candidate
rewrite; task-type-classifier audit; sensory-gate fix, reviewed in a prior pass this session)

Provenance chains partially established (one or more links missing evidence beyond Documentation): 1
(Codex relay — broken at Decision and Documentation, partial at Verification)

Provenance chains broken entirely (no real chain beyond the audit itself): 0 confirmed this pass —
every substantive finding investigated traced to at least a real decision or explicit rejection

Superseded findings: 6 (R-010/Q-009 liveness gap [independently re-verified live by this audit];
Mission 21's root-cause claim; research/DECISIONS.md D-002 vs. EXPERIMENT_INDEX.md E-035;
R-002's authority-framing, twice-narrowed; the codex subscription-independence YELLOW verdict;
the pre-existing near-zero self-edit success-rate claim)

Findings with no discernible consequence: ~3 (Q-004, Q-006, Q-005's unrepeated proposal)

Implemented-but-undocumented-in-CLAUDE.md findings: 5
(F2 stdin/fd0 contract; restore council gate; fallback-candidate rewrite; location split; see/hear fix)

Documented-but-unimplemented findings: 1 primary (Mission 18's Git-provenance interface — correctly
self-labeled as in-progress, not a broken promise)

Current Git HEAD: e92ec3b7fe4743f75746d161a06601db0232bff2 (unchanged before and after this audit)

Repository state mutated during this audit: NO.
  - No commits created. No files deleted. No files modified (source, audit, or CLAUDE.md/
    PENDING_DECISIONS.md). No git history operations of any kind performed.
  - One live, read-only HTTP query was made against the already-running production server
    (GET /admin/liveness-status, localhost only) — no state-changing request was sent.
  - No services started or restarted by this audit (the server was already running, restarted
    earlier this session by the user for an unrelated reason — a terminal freeze — before this
    audit began).
  - git status --porcelain path count confirmed identical (94) before and after this audit.
```
