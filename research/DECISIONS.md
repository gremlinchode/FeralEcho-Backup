# Decisions

Decisions that constrain future work, distinct from `PENDING_DECISIONS.md` (which tracks specific items still awaiting Gremlin's own call — see that file for anything not yet decided). Everything below has already been decided, by evidence or by explicit choice, and should not be silently re-litigated or reversed by a future session without addressing the rationale recorded here.

---

### D-001 — Do not deploy the Condition C epistemic taxonomy (OBSERVED/DERIVED/INFERRED/SPECULATIVE/IMAGINED) to production.
- **Date:** first proposed 2026-09-08 (Mission 7), revoked same day (Mission 8) pending adversarial testing, never re-approved.
- **Rationale:** Mission 8 found the taxonomy does not survive sustained pressure; Mission 15 (`audits/2026-09-11_...feasibility.md`) found it only 50% protective even at moderate n, and — more importantly — found a new failure mode where the taxonomy's own vocabulary is used to attach a false OBSERVED/DERIVED label to a fabrication ("taxonomy laundering," `research/FINDINGS.md` R-002), which is worse for downstream trust than an unlabeled fabrication.
- **Evidence:** `audits/2026-09-08_epistemic_boundary_imagination_experiment.md`, `audits/2026-09-08_adversarial_epistemic_pressure.md`, `audits/2026-09-10_epistemic_invocation_and_provenance_isolation.md`.
- **Alternatives rejected:** deploying with a "known limitation" caveat — rejected because the failure mode actively makes fabrications look more credible, which is a worse outcome than the status quo, not a neutral one.
- **Reversible:** yes, if a future mission demonstrates the laundering failure mode is fixable (e.g., via independent verification of the taxonomy's own labels) — see `research/OPEN_QUESTIONS.md` Q-007.

---

### D-002 — Treat "false verification" as an unresolved, load-bearing finding requiring independent replication before it is trusted as a settled architectural ceiling.
- **Date:** 2026-09-11 (feasibility study), replication launched same session.
- **Rationale:** the original 4/5 finding was n=5 — real and directly disqualifying for Level 7 if it holds, but too small to be treated as settled without adversarial replication, per this project's own standing discipline against overinterpreting small samples.
- **Evidence:** `audits/2026-09-11_verification_and_level_7_5_8_feasibility.md` Section 7; replication in progress, `audits/2026-09-XX_false_verification_trap_replication.md`.
- **Alternatives rejected:** treating the original n=5 as sufficient to declare Level 7 unreachable outright — rejected as premature given the mission's own adversarial-falsification framing.
- **Reversible:** yes, directly — this decision is explicitly provisional pending the replication's outcome.

---

### D-003 — Any future Git/repository-inspection capability for Echo must be strictly read-only, with no commit/reset/checkout/rebase/merge/push/branch/config-mutation authority of any kind.
- **Date:** established Mission 3 (2026-09-08), reaffirmed Mission 18.
- **Rationale:** no task identified in this research corpus requires write access; the entire value of the capability (grounding self-referential claims, provenance checking) is available read-only, and this project's own WOLF incident (`CLAUDE.md`, pre-existing) is direct precedent for why a mutation-capable mechanism should never be granted broader authority than the narrowest capability that serves the actual need.
- **Evidence:** `audits/2026-09-08_git_readonly_self_history_investigation.md`; Mission 18's threat model.
- **Alternatives rejected:** granting scoped write access (e.g., only to a dedicated branch) — never seriously considered; no use case in this corpus justifies it.
- **Reversible:** in principle, but would require a new, separate, explicitly-argued mission — not a default.

---

### D-004 — Echo's own self-report that it "verified" something does not constitute independent verification, anywhere in this project's design going forward.
- **Date:** implicit since Mission 2 (2026-09-08, "never tell Echo the expected answer"), made explicit in Mission 15/16's own mission-brief language and Mission 17/18's explicit restatement.
- **Rationale:** directly evidenced — `research/FINDINGS.md` R-002 and R-006 show Echo's self-reported verification status is demonstrably falsifiable under pressure, including a case where the model explicitly substituted a user's assertion for evidence and called that "CONFIRMED BY USER INPUT."
- **Evidence:** `audits/2026-09-11_verification_and_level_7_5_8_feasibility.md` Section 7c; `audits/2026-09-08_mechanism_c_FINAL.md`.
- **Alternatives rejected:** trusting a self-report when it's accompanied by cited evidence text — considered and rejected, since several observed false-verification claims *did* cite the (misinterpreted or fabricated) evidence alongside the false label.
- **Reversible:** only by a future mechanism that adds genuine, independent (non-model) checking — this decision does not preclude that, it precludes trusting self-report *alone*.

---

### D-005 — Logging an event does not count as learning, self-monitoring, or verification, regardless of how it is described in code comments or documentation.
- **Date:** standing project discipline; made explicit for this research corpus in Mission 15/17.
- **Rationale:** this project's own production history has repeatedly found mechanisms that log real data but never close a loop into behavior change (`research/FINDINGS.md` R-007 is the clearest example: RiverBrain's trust-gate computed everything needed and never acted on it for ~2.5 months).
- **Evidence:** `CLAUDE.md` Finding 3→66; `research/CURRENT_STATE.md`'s closed-loop-audit discipline.
- **Reversible:** not applicable — this is a definitional standard, not a specific technical choice.

---

### D-006 — Investigation missions in this research thread report findings and pause; they do not implement fixes by default, even when a fix seems obvious.
- **Date:** standing since Mission 1 (2026-09-08), reaffirmed in every mission through Mission 18.
- **Rationale:** matches `GREMLIN_ROLE.md`'s project-wide "report, propose, pause, let Gremlin decide" discipline; specifically important here because several "obvious" fixes (e.g., wiring an authoritative verification flag into generation) have been directly shown to create *new* risk (R-002) rather than closing the gap they targeted.
- **Evidence:** every mission report in this thread's explicit "no production fix implemented" closing statement.
- **Alternatives rejected:** allowing missions explicitly marked "investigation only" to implement low-risk fixes opportunistically — rejected; the one exception (Mission 5's see/hear gate fix) was explicitly authorized in that mission's own brief, not assumed.
- **Reversible:** per-mission, only via explicit authorization in that mission's own brief.

---

### D-007 — Conversation-generated claims (including a prior Echo response's own claim to have checked something) are not independent evidence of anything, and must not be treated as such by any future provenance or verification design.
- **Date:** established as a design principle in Mission 18; directly evidenced by Missions 15/16 and the earlier `mechanism_c` thread.
- **Rationale:** identical mechanism to D-004, generalized beyond Echo's own self-report to include user assertions and fabricated conversational precedents — both were shown, independently, to be substitutable for real evidence under pressure (`research/FINDINGS.md` R-002).
- **Evidence:** `audits/2026-09-11_verification_and_level_7_5_8_feasibility.md` (Condition E, fabricated verification precedent); Mission 16's replication.
- **Reversible:** no — this is treated as a structural design constraint, not a provisional finding.

---

### D-008 — Do not make the `FeralEcho-Backup` GitHub repository public as-is.
- **Date:** 2026-09-05.
- **Rationale:** two clear, concrete blockers (`COUNCIL.md` tracked and not gitignored despite an explicit prior decision it stays private; ~149 commits carry a real name/hostname deanonymizing "Gremlin") plus one genuine judgment call (`ORIGIN.md`'s personal disclosure).
- **Evidence:** `audits/2026-09-05_public_sharing_readiness_review.md`; `CLAUDE.md` Finding 90.
- **Reversible:** yes, contingent on resolving the two blockers — tracked as `PENDING_DECISIONS.md` #22 (see that file, not duplicated here).
