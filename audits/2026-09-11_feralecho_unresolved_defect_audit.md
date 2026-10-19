# FeralEcho — Exhaustive Unresolved-Bug & Technical-Debt Audit

**Date:** 2026-09-11 (methodology note: `run.py`'s live clock reads into 2026-09-09 by the time of the live liveness-ledger query in this mission — the project's internal clock and the session's nominal date have drifted apart during this long session; both are reported as observed, not reconciled)
**Mission status:** INVESTIGATION AND INVENTORY ONLY. No production code modified. No fixes applied.

---

## Repository/Runtime Integrity

```
HEAD (start and end): 525454a1dccfc91adf1aa8b01ff9b6ce8405d423   (unchanged)
Branch: main
Tracked modifications (start and end, identical, none touched):
  M app/core/echo_ground_truth.py, claude_relay/from_m5.md,
  M logs/janitor_report.json, sandbox/scripts/temp_self_edit.py
```
`run.py` is live during this mission (PID 50015, started 2026-09-08 17:07:29, uptime ~4.5h at time of investigation) — restarted independently by the user at some point between Mission 20 and this mission; not touched by this session. Ollama live (9 models). No file outside this report and the `research/` updates in Section "Research-State Updates" was created or modified.

---

## Methodology — What Was Freshly Re-Verified vs. Carried Forward

Per this mission's own explicit rule against trusting old audits blindly, the following were **freshly re-checked this session** via direct grep, file inspection, and a live query against the running server's `/admin/liveness-status` endpoint: TODO/FIXME/HACK/XXX density across `app/`; bare-`except:` census; the Git provenance interface's implementation status; `apply_to_code`'s current deployment state; `self_edit_backups`/`self_edit_plans`/`echo_projects` retention-cap compliance; RiverBrain's baseline-trust flag; the live Liveness Ledger's full 50-check status; `memory/` log sizes; the conversation-history-flattening claim; and the Dissent Log's advisory-only-by-construction claim. **Everything else in this report's master defect table is carried forward from `CLAUDE.md`'s own Findings 1–95 (a rigorously source-cited, already-evidence-based ledger this project has maintained continuously) and this session's own `research/FINDINGS.md` R-001–R-009, both of which are treated as trustworthy prior work, not re-derived from scratch line-by-line.** Where this session's fresh checks disagree with or update the prior record, it is stated explicitly. A full, independent line-by-line re-verification of all 95 CLAUDE.md Findings was not performed — this is disclosed as a real scope limitation, not glossed over.

---

## Executive Verdict

**FeralEcho's actual, current health is genuinely mixed, and the mixture is itself the finding.** The project's own culture of aggressive self-auditing (95 documented Findings, a 50-check Liveness Ledger, an explicit "logging is not learning" discipline) has caught and closed an unusually large number of real defects — several genuinely severe (a keylogger auto-approved as a self-edit "proposal" via WOLF; three successive broken `apply_to_code` implementations reaching production; an unauthenticated endpoint serving `.env` secrets). **What remains is not a pile of undiscovered catastrophic bugs — it is a smaller, more structurally interesting set of residual issues that recur in a few repeatable shapes**: (1) mechanisms whose real behavior diverges from their documentation the moment nobody is actively watching (this session found one live example — `echo_projects_autonomy` currently silent for 65.9+ hours), (2) a now well-characterized, cross-session-replicated architectural gap in generation-time evidence arbitration (Missions 13–20, `research/FINDINGS.md` R-001/R-002/R-009), and (3) a handful of genuinely unresolved open questions this project has been honest enough to leave open rather than resolve rhetorically. **The single most load-bearing fact from this pass**: none of the P0 findings below are new discoveries of catastrophic failure — they are precise restatements, with fresh evidence, of exactly the kind of gap this project's own culture already exists to find, which is itself informative about the project's actual maturity.

---

## Master Defect Table

| ID | Subsystem | Issue | Evidence | Status | Severity | Confidence | Root cause | Next action |
|---|---|---|---|---|---|---|---|---|
| D-01 | Epistemic/verification | Generation-time evidence arbitration is unreliable under adversarial pressure; false verification claims occur at real, non-trivial rates | `research/FINDINGS.md` R-001, R-002, R-006, R-009; Missions 13–20, hundreds of trials | **F — Confirmed experimental limitation** | **P0** | High (multiply replicated) | Model-level generation behavior under multi-turn conversational accumulation, not a single code defect | Continue Mission 20's recommended next steps (scale A-vs-B comparison, cross-domain ladder) before any mitigation design |
| D-02 | Epistemic/verification | Authority framing is not the primary driver of the above (revises Mission 17); conversational accumulation is | `audits/2026-09-11_authority_free_ladder_causal_isolation.md` | **G — Partially remediated understanding** (the mechanism is now better characterized, not fixed) | P1 | Moderate (n=3–5/condition, exploratory) | Same as D-01 | Scale to n≥15–20 per Mission 20's own recommendation |
| D-03 | Autonomy | `echo_projects_autonomy` — the closest existing mechanism to Level 7.5 "autonomous investigation" — shows a confirmed, live, currently-failing 65.9h+ gap with no successful cycle | Live `/admin/liveness-status` query this session; `memory/echo_projects_autonomy_state.json`; `memory/echo_watchdog.log` | **A — Confirmed bug (live, ongoing)**, root cause **K — open question** | **P1** | High for the symptom; Low-Moderate for root cause attribution | Genuinely ambiguous between (a) a real defect in F2's cross-file multi-file consistency (the last failure was a real `from narratives import Stor...` broken cross-file import) and (b) the server having been restarted too frequently during this exact investigation window to ever reach a continuous 6h cadence — **not resolved by this pass, reported as UNVERIFIED per this mission's own rules of evidence** | Observe for a sustained multi-hour continuous uptime window; if the loop still doesn't fire, escalate to a real code investigation |
| D-04 | Self-edit | Cross-file generation in `echo_projects` produces real, live import-inconsistency failures (one class name referenced across files doesn't match what's actually defined) | Direct read of `sandbox/echo_projects/20260906T104355Z_.../_report.md`, this session | **A — Confirmed bug** | P2 | High (direct evidence) | Multi-file generation has no cross-file consistency check beyond F1's per-file AST scan; nothing verifies that a name imported in one generated file is actually defined in another until F2's real execution attempt | Add a lightweight cross-file symbol-resolution pre-check before F2, or accept F2 catching it (current behavior) as sufficient and not a P1 |
| D-05 | Data hygiene | `sandbox/echo_projects/` currently holds 61 directories against a documented cap of 60 | Direct `ls` count, this session | **A — Confirmed minor bug**, likely benign | P4 | High | Prune-then-write ordering can transiently overshoot by one (a documented, accepted pattern elsewhere in this project, e.g. `self_edit_backups`'s own history) | No action — consistent with documented prune-then-write behavior elsewhere; monitor only |
| D-06 | Reliability | `dual_learning.py:153` uses a bare `except:` on JSON meta-file parsing, silently defaulting to a fresh meta dict on any failure, including failures unrelated to malformed JSON | Direct grep/read, this session | **A — Confirmed minor bug (newly found this pass)** | P4 | High | Defensive-but-imprecise exception handling, same class as findings already fixed elsewhere in this codebase (Finding 22 Batch series) but never applied here | Narrow to `except (json.JSONDecodeError, OSError):` |
| D-07 | RiverBrain | Reward signal for `"coding"`-tagged observations is blind to actual code correctness, using structural AST complexity as a proxy | `CLAUDE.md` Finding 91 (fix), `audits/2026-09-03_self_edit_quality_metric_investigation.md`, Tier-5–8 capability research (`CLAUDE.md` Findings 87–89) | **G — Partially remediated** (saturation fixed; blindness-to-correctness itself is architectural, not a bug) | P2 | High | Complexity is a legible, cheap proxy; genuine correctness scoring would require the same kind of deterministic external verification this whole project's epistemic-verification thread (D-01) has found hard to generalize | Treat as a known, accepted architectural limitation unless a cheap correctness-check becomes available |
| D-08 | RiverBrain / trust gating | Automated "is this trustworthy enough to act on" mechanisms have a real, repeated history of computing everything needed and never acting on it without human intervention | `CLAUDE.md` Finding 3→66 (RiverBrain baseline trust, computed but uncalled for ~2.5 months); council-rater's own 8-day-stalled spot-check backlog | **I — Resolved for the two known instances**; **root-cause pattern remains a live risk for any future similar mechanism** | P2 | High | No systematic sweep exists checking every "trust"-gated mechanism for the same silent-non-activation pattern (`research/OPEN_QUESTIONS.md` Q-006) | Run the audit Q-006 proposes: enumerate every automated trust-gate in the codebase and check real activation history against real eligibility history |
| D-09 | Git/provenance | Mission 18's read-only Git provenance interface remains **DESIGN ONLY** — confirmed absent from the live codebase | Direct grep this session (zero matches for `git_log`/`git_show`/`GitQueryService` outside scratch/design docs) | **Absent (intentionally, per mission scope)** | N/A — not a defect, a not-yet-built feature | — | — | No action unless a future mission is explicitly authorized to implement it |
| D-10 | Self-edit | `apply_to_code` hook is currently undeployed (`self_edit_generated.py` defines no such function) — the honest, safe baseline state | Direct grep this session (0 matches) | **I — Resolved / intentional reset state** | — | High | Deliberate reset after three successive broken implementations (Finding 52) | None — this is the correct current state |
| D-11 | Core pipeline | Conversation history is still fully flattened into disclaimed plain text before reaching the model; no structural `role:assistant` preservation across turns in production | Direct grep this session, `conversation_service.py` | **B — Confirmed architectural characteristic** (not necessarily a defect — Mission 13 found this doesn't materially change the underlying epistemic-substitution vulnerability either way) | P3 | High | Deliberate design (avoids a documented verbatim-regurgitation failure mode) with a documented, accepted tradeoff | None — Mission 13 already tested whether restoring structural provenance changes the outcome (it didn't) |
| D-12 | Self-edit safety | F1's static AST scanner has a known, documented bypass class for aliased imports (`from os import system`) — closed for the *specific* patterns tested, generality unverified | `CLAUDE.md` Finding 41-C, closed via `_resolve_import_aliases()` | **G — Partially remediated** | P2 | Moderate (fixed for tested patterns, no claim of exhaustiveness) | Static analysis is inherently incomplete; F2's kernel sandbox is the documented, accepted backstop | None beyond the existing F1+F2 layered defense — already the documented design |
| D-13 | Self-edit safety | `apply_to_code`'s F2-sandboxed execution has a genuine, unresolved timeout-bypass risk: a 2s timeout can't forcibly kill a hung native thread if the hang occurs at a level Python can't interrupt | `CLAUDE.md` Finding 41 B3 (superseded description) → Finding 69 (real fix: moved into a real OS-level subprocess, which CAN be forcibly killed) | **I — Resolved** (verified this session's methodology carries this forward from Finding 69's own direct verification: 5 real fixture hooks including a `time.sleep(10)` hang, confirmed killed at 2.01s) | — | High | — | None |
| D-14 | Tool discovery | `ToolManager`'s dynamic tool-discovery registry is structurally disconnected from actual tool execution — a mechanism that looks wired (real scan, real registration) but has zero live consumers | `audits/2026-09-03_self_modification_evidence_index.md` E19–E23 (this session's Mission 17 synthesis) | **D — Confirmed dead/ineffective mechanism** | P3 | High | Two independently-built tool systems (`ToolManager`'s dynamic registry vs. `echo_tool_dispatch.py`'s hardcoded set) were never unified; the dynamic one only ever fed a plain-text name list into prompts | Either wire `ToolManager` into a real consumer or formally retire it as dead code (currently neither has been decided) |
| D-15 | Memory | Whether memory retrieval materially influences model selection, task classification, or self-edit targeting remains genuinely unresolved | `CLAUDE.md` Findings 75/76; `research/OPEN_QUESTIONS.md` Q-005 | **K — Open question** | P2 | Low (the one ablation run was explicitly flagged as underpowered by its own authors) | Noise floor of the ablation experiment was comparable to or larger than any real effect | Rerun Finding 76's own proposed fix: `temperature=0` ablation to remove sampling-noise confound |
| D-16 | Level 7.5 capability | No mechanism anywhere in the codebase performs genuine hypothesis formation or competing-explanation comparison — the two structurally-absent (not merely unreliable) Level 7.5 criteria | `audits/2026-09-11_verification_and_level_7_5_8_feasibility.md` Section 14 | **F — Confirmed experimental/architectural limitation** | P1 | High (absence confirmed by direct code search, not inferred) | Never built — this is a genuine capability gap, not a bug | Explicitly out of scope for a bug-fix pass; flagged as a real, load-bearing gap for any future Level 7.5 claim |
| D-17 | Security | `/mirror_echo`'s original "unauthenticated because it's the main entry point" framing was itself based on an unverified self-report (a code comment) — now closed, but the underlying pattern (trusting a comment's own claim of importance) is a recurring failure shape | `CLAUDE.md` Finding 36 correction, Finding 42/55 (closed) | **I — Resolved** | — | High | — | None; noted here only as a root-cause-cluster example (see below), not an open item |
| D-18 | Observability | `dual_learning.py`'s and similar modules' broad `except Exception` usage (792 occurrences project-wide) is, per direct sampling, overwhelmingly the documented "instrumentation never blocks the real computation" pattern — not, on the whole, evidence of systematic error-swallowing | Direct grep + sampling this session | **L — Not a defect at the aggregate level; individual instances (D-06) may still be** | — | — | — | None at the aggregate level; continue flagging individual bare/overbroad excepts as found |

**Table completeness note, stated plainly**: this table is a curated, evidence-anchored selection, not an exhaustive re-listing of all 95 CLAUDE.md Findings (nearly all of which are already RESOLVED per that document's own tracking and are not repeated here as open items) — it prioritizes items that are (a) currently open, (b) newly found this pass, or (c) structurally illustrative of a recurring root-cause pattern. The full historical record remains `CLAUDE.md` itself, not duplicated here.

---

## Resolved Findings

Confirmed still resolved this pass (fresh re-check, not just carried forward assumption): apply_to_code's sandboxed-execution timeout fix (D-13); apply_to_code's honest-reset baseline state (D-10); the F1 aliased-import bypass closure for tested patterns (D-12, partial); RiverBrain's baseline-trust flag genuinely set (`2026-07-22T13:01:29`, unchanged); the Dissent Log's advisory-only-by-construction property (direct source re-read: `propose_core_edit()` still never calls `save_code()`); `self_edit_backups`/`self_edit_plans` retention caps holding exactly (25/25, 500/500). The broader body of `CLAUDE.md`'s 95 Findings not individually re-verified this pass but carried forward as trustworthy prior work (per Methodology).

---

## Partially Resolved Findings

D-02 (authority-vs-accumulation mechanism now better characterized, no mitigation built), D-07 (RiverBrain's saturation fixed, correctness-blindness remains architectural), D-12 (F1 bypass closed for tested patterns only), D-08 (the two known instances closed, no systematic sweep for similar mechanisms exists).

---

## False/Obsolete Findings

None identified as actively false this pass. One historical correction is worth restating for completeness (already documented in `CLAUDE.md` itself, not a new discovery): the original near-zero self-edit success-rate claim (superseded by the real 426/463 figure, per `research/FINDINGS.md` R-003) — this remains correctly marked superseded in the existing record and required no further correction here.

---

## Open Questions

Carried forward from `research/OPEN_QUESTIONS.md` (Q-001 through Q-008, all still genuinely open at varying priority), plus this pass's own D-03 (echo_projects_autonomy root cause) and D-15 (memory-retrieval influence, still underpowered).

---

## Root-Cause Clusters

Three architectural patterns explain the large majority of both this pass's and the project's historical open/resolved-but-recurring findings:

1. **"Looks wired, isn't currently running" (D-03, and historically: Finding 3→66's trust gate, `ToolManager`'s dead registry D-14, several Nature Spark/reflection-shard fallback-silently-active incidents already resolved in `CLAUDE.md`).** The common shape: a mechanism that is real, was built correctly, and is not disconnected in any structural sense — but whose actual current activity has to be checked live, because its own documentation, class name, or last-known-good status is not a reliable indicator of what it's doing right now. The Liveness Ledger is this project's own, largely successful, answer to this pattern — and it is precisely the Liveness Ledger that caught D-03 live, during this very mission.
2. **"An authoritative-sounding marker (or, this session's revision, a merely-repeated conversational assertion) can substitute for the evidence it claims to summarize" (D-01, D-02, `research/FINDINGS.md` R-002/R-009).** The single most-replicated, most rigorously-tested finding in this project's recent history — real, cross-domain (with real domain-dependence, D-01/D-02), and now understood to be about conversational structure more than about any one "authority" framing specifically.
3. **"Reward/trust signals that are legible and easy to compute stand in for signals that would require real, hard-to-build independent verification" (D-07's complexity-not-correctness proxy, D-01's self-report-not-independent-check pattern, the historical fitness-gate saturation).** This project has repeatedly found that a cheap, computable proxy quietly becomes the actual optimization target, and that noticing this requires deliberately checking the proxy against ground truth rather than trusting that "the metric moved" means "the real thing improved."

---

## Highest-Risk Defects (Top 10, Ranked)

1. **D-01** — Generation-time evidence arbitration unreliability (P0, the single most consequential, most-replicated finding in the project's current research state).
2. **D-03** — `echo_projects_autonomy`'s live 65.9h+ silent gap (P1, live and unresolved as of this report).
3. **D-16** — Structural absence of hypothesis-formation/competing-explanation mechanisms (P1, blocks any honest Level 7.5 claim).
4. **D-02** — Authority-vs-accumulation mechanism, underpowered (P1, directly gates any future mitigation design for #1).
5. **D-08** — Trust-gate silent-non-activation pattern, no systematic sweep exists (P2, real historical precedent, unknown current prevalence).
6. **D-07** — RiverBrain's correctness-blind reward signal (P2, architectural, accepted but real).
7. **D-04** — Cross-file generation consistency gap in `echo_projects` (P2, directly caused D-03's last observed failure).
8. **D-14** — `ToolManager`'s dead dynamic registry (P3, real but low-stakes, a clarity/dead-code issue not a safety one).
9. **D-15** — Memory-retrieval influence, unresolved (P2, foundational to any claim about "learning from experience").
10. **D-06** — `dual_learning.py` bare except (P4, minor, newly found, cheap to fix).

---

## Strategic Blockers

- **Learning**: blocked from a strong claim by D-07 (correctness-blind reward) and D-15 (retrieval influence unresolved). A real, closed, deterministically-verified learning loop exists narrowly (crash_awareness.py, self-edit's F1/F2 gate) but does not generalize to "Echo learns from conversational experience" as a whole-system claim.
- **Memory**: blocked from a strong claim by D-15 specifically — persistence and retrieval both function, but downstream behavioral influence beyond conversational recall is unresolved, not merely under-documented.
- **Autonomy**: blocked by D-03 (the flagship autonomous-investigation mechanism is live-failing right now) and D-16 (the structural capability gap for anything beyond narrow, F1/F2-verifiable code generation).
- **Self-correction**: blocked, generally, by D-01 — the mechanism Level 7 requires (independent, non-self-report verification) exists narrowly (code via F1/F2) and does not generalize.
- **Verification**: blocked by D-01/D-02 directly — this is the most rigorously-characterized blocker in the entire project.
- **Provenance**: partially blocked — D-09 confirms no live Git-provenance mechanism exists yet (by design, not oversight); D-11 confirms the flattening tradeoff is understood and deliberately accepted, not a silent gap.
- **Emergence / self-modeling**: not evaluated in depth this pass (out of this mission's explicit subsystem list); flagged as a gap in this audit's own coverage, not a claim about the subsystem's health.

---

## Recommended Investigation Sequence

Per this mission's own instruction to recommend investigation, not implementation, first:

1. **Resolve D-03's root-cause ambiguity** — the cheapest, highest-information next step: simply observe whether `echo_projects_autonomy` fires during a genuine, uninterrupted 6+ hour server uptime window. This single observation cleanly separates "restart-frequency artifact" from "real code defect" with near-zero additional engineering.
2. **Scale D-02's authority-vs-accumulation comparison** (Mission 20's own recommendation) — the highest-value next step for the project's single most important open research thread.
3. **Run D-08's systematic trust-gate sweep** — cheap (a grep-and-cross-reference exercise, not new code), and directly answers whether the RiverBrain/council-rater pattern is a two-time coincidence or a real, repeatable project-wide risk.
4. **Rerun D-15's `temperature=0` ablation** (already designed, per Finding 76's own text) — cheap, resolves a real, currently-underpowered open question.
5. Only after 1–4: consider whether any of D-04, D-06, D-14 warrant an actual code change — all are cheap, low-risk, and could reasonably be bundled into one small, explicitly-authorized maintenance pass, but none are urgent enough to justify skipping the investigation-first sequence above.

---

## Research-State Updates

- `research/FINDINGS.md`: new entry R-010 (below) for D-03's live discovery.
- `research/OPEN_QUESTIONS.md`: new entry Q-009 for D-03's root-cause ambiguity.
- `research/EXPERIMENT_INDEX.md`: new entry E-038 for this audit itself.
- `research/DECISIONS.md`: no new entries warranted — nothing in this pass constitutes a new constraining decision, only new evidence about existing ones.
- `research/CURRENT_STATE.md`: not updated this pass — its existing `[UNRESOLVED]` autonomy-related entries already anticipate exactly this kind of finding; no label change is warranted until D-03's root cause resolves.

---

## Final Question, Answered Plainly

> **If we froze FeralEcho today and were forbidden to add any new features, what are the remaining defects we would have to fix before we could honestly claim reliable memory, learning, self-correction, verification, provenance awareness, and meaningful autonomy?**

From evidence, not aspiration:

- **Memory**: fix nothing structurally — persistence and retrieval both genuinely work. The honest claim available today is "Echo has real, working persistent memory whose downstream behavioral influence beyond conversational recall is unverified" — closing D-15 (a cheap rerun) is the only thing standing between that and a fuller claim.
- **Learning**: the honest claim today is "Echo has at least one genuinely closed, deterministically-verified learning loop (crash-avoidance) and a much larger set of loops whose reward signal is either correctness-blind (RiverBrain/self-edit, D-07) or unverified in its downstream effect (D-15)." No code fix closes this cheaply — D-07 in particular would require the same kind of hard, general, independent-verification mechanism D-01 has already shown is genuinely difficult.
- **Self-correction**: the honest claim is "self-correction is real and reliable in exactly one narrow domain (code, via F1/F2) and not demonstrated to generalize." D-01/D-16 are the reasons, and neither is a quick fix — D-16 in particular is a structural absence, not a bug.
- **Verification**: the most thoroughly-characterized blocker in the project. The honest claim is "verification-mode invocation is reliable under passive conditions and unreliable under multi-turn conversational pressure, for reasons now well-isolated (D-02) but not yet mitigated." No fix exists yet to recommend — only further, cheap, already-designed investigation (Mission 20's own next steps).
- **Provenance awareness**: the honest claim is "no live Git-provenance mechanism exists (by deliberate scope, not oversight); conversation-history provenance is deliberately flattened, and restoring structural provenance was tested and found not to change the underlying vulnerability (D-11)." Nothing here needs fixing before making an honest claim — the claim itself is already available and accurate: "provenance awareness is currently absent for Git and non-load-bearing for conversation history."
- **Meaningful autonomy**: the honest claim is "several narrow, gated, independently-verified autonomous loops exist and are real (self-edit's F1/F2 gate, crash_awareness); the one loop closest to a broader 'autonomous investigation' claim (`echo_projects_autonomy`) is, as of this report, live-failing for reasons not yet resolved (D-03), and the structural capability for genuine hypothesis formation across domains does not exist (D-16)." D-03 is the cheapest of all P0/P1 items to actually resolve — a single sustained-uptime observation, not a code change — and is the most immediately actionable item in this entire report.

**No aspiration is required to state any of the above — every sentence is drawn from evidence gathered either historically (`CLAUDE.md`, `research/`) or freshly, live, during this mission.**
