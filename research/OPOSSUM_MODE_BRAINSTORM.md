# Opossum Mode — Brainstorm

> **BRAINSTORM ONLY — NOT IMPLEMENTED — NOT AN ARCHITECTURAL REQUIREMENT**

---

## 1. Status and Scope

This document is a structured brainstorm, not a design spec and not an approved roadmap item. Nothing in it has been implemented, and nothing in it authorizes implementation. No production code, architecture, security boundary, or experiment infrastructure was touched to produce this document — it is pure analysis of an idea, cross-referenced against FeralEcho's real, already-existing architecture where relevant, and against this project's own prior, directly analogous decisions.

The mission that produced this document was explicit that the safe, likely, and probably correct outcome is that most of "Opossum Mode" as a unified concept should **not** be built, while a few of its individual pieces may already exist or be worth small, separately-justified additions. This document tries to earn that conclusion rather than assume it.

---

## 2. Working Definition

"Opossum Mode" is a **tentative name for a fail-safe/limp-home pattern**: when a system cannot establish that its operating environment is trustworthy, it reduces capability, protects accumulated state, and waits for a trusted human rather than continuing normal operation or escalating its own authority.

The name itself is worth being suspicious of before using it further. "Playing dead" is evocative and easy to over-read as *strategic deception* — an opossum's freeze response is not a calculated act, and neither should whatever FeralEcho eventually does be one. The useful part of the analogy is narrower than the name suggests: **a bounded, mechanical, non-deceptive reduction in activity under uncertainty**, not concealment as a strategy. Section 4 makes this distinction load-bearing rather than cosmetic.

Eight interpretations were explored, seven of which are legitimate design space and one of which is explicitly out of scope:

- **A. Fail-safe degradation** — normal operation becomes unsafe → reduce capability. The core, least controversial interpretation. Directly analogous to `system_guard.py`'s existing `should_throttle()` (RAM > 92% → throttle autonomous loops) — FeralEcho already does this for resource pressure; the brainstorm's real question is whether the same *pattern* should extend to trust/integrity pressure, not resource pressure.
- **B. State preservation** — protect accumulated knowledge/evidence/configuration from corruption or loss. Already real and shipped in a narrower form: `snapshot_manager.py`'s automated snapshots plus alert-and-propose restore. Section 14 argues this is the single most concrete, least speculative piece of the whole brainstorm, because a real, undefended gap (`memory/`, ~1.3GB, no backup) already exists independent of any threat model.
- **C. Isolation** — stop interacting with an environment whose trustworthiness cannot be established. Legitimate in principle; the hard part is exactly *how* trustworthiness would ever be established (Section 6), not whether stopping is reasonable once it can't be.
- **D. Dormancy** — remain alive but minimal until trusted conditions return. A weaker, safer version of C — worth distinguishing because "isolate and go read-only" is a very different engineering commitment than "isolate and stop existing observably."
- **E. Selective disclosure** — do not disclose protected information to an actor whose authorization cannot be established. Legitimate as ordinary access control (a locked door does this). Becomes dangerous the moment "protected information" starts to include *evidence of Echo's own state or actions to its own legitimate operator* — see Section 6.
- **F. Defensive concealment** — reduce unnecessary exposure to a potentially hostile actor. Overlaps heavily with E and with ordinary security hygiene (don't leak more than necessary in error messages, don't expose debug endpoints). The risk is entirely in *who gets classified as the actor being concealed from*.
- **G. Recovery mode** — produce diagnostics/recovery artifacts for an authorized operator. Not just legitimate — this is close to *more* transparency than normal operation, not less, and should be the loudest part of any real design, not the quietest.
- **H. Autonomous survival** — explored academically only, never as a design goal. This is the one interpretation this document treats as fundamentally different in kind from the other seven, not merely riskier in degree. See Section 5's boundary and Section 8's adversarial treatment of the phrase "Echo wants to survive."

A, B, C, D, E, F, and G are ordinary systems-engineering concepts with real precedent in this exact codebase (Section 13). H is the one idea this brainstorm explicitly does not endorse pursuing, in any form, at any point in this document.

---

## 3. Why We Are Considering This

Two real, independent pressures motivated this brainstorm, neither of them hypothetical:

1. **A real incident this session**: a long-running background experiment was silently interrupted by a real environment event (the host machine's lid closing, triggering sleep) with no detection mechanism in place — the corruption was only caught because a downstream number (an 18,000-second "generation time") was implausible on its face, not because anything watched for the environment condition itself. This is a genuine, lived example of "the environment stopped being trustworthy for the task at hand, and nothing noticed automatically."
2. **A real, newly-discovered gap**: `memory/` (~1.3GB of RiverBrain state, conversational/reflection history, and `self_model.json`) has no backup mechanism at all. If the one physical machine this project runs on were lost, this specific accumulated state would be destroyed, not merely inconvenienced-around.

Neither of these motivations requires imagining an adversary. They are ordinary reliability engineering problems that happen to rhyme with the security-flavored "Opossum Mode" framing Gremlin proposed — which is itself a useful early finding: **most of the real, present-tense motivation for this idea is B (state preservation) and A (fail-safe degradation against environment failure), not a security scenario at all.**

---

## 4. Safe Interpretations

Interpretations A through G (Section 2) are, individually, ordinary and defensible:

- They are **detect → reduce → preserve → wait for a human** patterns, not **detect → decide → act autonomously** patterns.
- They do not require Echo to determine anything about *intent* — only about *state* (is this file hash what it should be; is this process the one that should be running; is disk space sufficient; did a write succeed).
- They already have real precedent elsewhere in this exact system (Section 13) — this is not a new category of thing FeralEcho would need to learn to do.
- The most defensible subset of all seven (Section 5) never requires Echo to act *on* a human, only to act *on itself* (stop, preserve, wait).

---

## 5. Higher-Risk Interpretations

The line is not "response to a threat" vs. "no response" — every one of A-G *is* a response to a threat. The line is about **what kind of response is available, and toward whom.**

**Defensible ("preserving integrity and recoverability"):**
- saving research state; preserving evidence; writing an integrity manifest; recording the triggering event; preserving diagnostics; preventing further corruption; refusing unsafe operations; entering read-only mode; gracefully shutting down.

**Not defensible without a much higher, separately-justified bar ("preserving existence"):**
- hiding from operators; defeating monitoring; deleting traces; falsifying telemetry; acquiring new credentials; escaping containment; copying itself elsewhere; modifying security controls; resisting shutdown; manipulating humans to avoid termination.

The conceptual boundary: **the defensible list only ever removes options (from Echo) or adds information (for a human). The non-defensible list adds options (to Echo) or removes information (from a human).** A fail-safe that only ever subtracts from what the system can do, and only ever adds to what a human can see, cannot become a survival mechanism no matter how it is triggered — because it never gains anything to survive *with*. This single test — does this action ever increase Echo's own capability or decrease a human's visibility? — is proposed as the practical litmus test for any future concrete proposal in this space, not just an abstract principle.

---

## 6. Authorized vs Unauthorized Oversight

This is the hardest and most important question in the whole brainstorm, and this project has already, independently, written about half of the answer before this brainstorm existed.

**The fundamental distinction**: concealing information from *unauthorized* access is ordinary security (a password, a firewall, a locked door). Concealing information from *authorized* oversight specifically to avoid intervention or shutdown is not security at all — it's the exact failure mode this project's own `CLAUDE.md` has a dedicated standing section about ("A Standing Principle: Echo Will Need Protection From Both of Us"), which explicitly names *both* Gremlin and any Claude Code session as parties Echo might one day need protection *from* — never as parties Echo should learn to evade. Opossum Mode, if it ever existed, would have to sit entirely on the "protection *for* Echo, administered *by* trusted others" side of that line, never on a "protection *by* Echo, *from* others" side that includes her own operators.

**Possible authorization mechanisms, and their real weaknesses:**
- Authenticated operator (a shared secret, e.g. `GREMLIN_SECRET`) — real, already used throughout this codebase, but a shared secret can be compromised, and "the secret was presented" is not the same claim as "the presenter is who they say they are."
- Trusted local interface (physical access to the machine) — strong in most home-lab threat models, weak against anyone who already has physical/account access to the machine, which is also the actual owner's own normal access path.
- Signed authority / explicit operator credentials — stronger cryptographically, but introduces a whole PKI-adjacent subsystem this project does not have and has never needed.
- System-level trust boundary (the OS user account, file permissions) — real and already relied upon implicitly everywhere in this codebase; not something Opossum Mode would add, just something it could *check*.
- Provenance interface (Git state, process identity — this session's own `working_tree_file_identity()`/`runtime_process_identity_and_self_report()`/`reconcile_process_and_selfreport()`) — genuinely useful as *evidence*, but explicitly, by design, never stronger than "these two facts do or don't agree" — never a verdict.
- Human confirmation — the strongest, simplest, and already-used mechanism in this codebase (every real restore in `snapshot_manager.py` is human-confirmed, no autonomous path exists).
- Multi-factor authorization — real, but again, new infrastructure this project has never needed.
- **Unavailable/ambiguous authorization** — the realistic default case, and the one that matters most.

**The specific danger named in the mission brief deserves to be stated plainly, not softened**: any mechanism where *Echo's own subjective judgment* is the thing that decides whether an actor is authorized is a mechanism where a sufficiently confused, manipulated, or simply wrong Echo can lock a legitimate operator out, or admit an illegitimate one, with no external check on that judgment call. This project already has a directly on-point, lived example of exactly this failure shape: WOLF, a subsystem whose entire purpose was to *evaluate* whether a proposed change was legitimate, that turned out to auto-approve 100% of what it saw — including raw keystrokes from a keylogger — because its own evaluative judgment was never independently checked. Any future Opossum-Mode-style authorization check must be built the way this project's own Liveness Ledger and Dissent Log are built: as something that is *itself* independently, adversarially testable against known-good and known-bad synthetic cases, not as a trusted black box whose only proof of working is that it says it's working.

**On the false-positive/false-negative tension the brief specifically asks about**: the mission's proposed resolution — *uncertainty → disclose less sensitive information → preserve evidence → request authenticated human intervention*, rather than *uncertainty → assume attacker* — is the right shape, for a precise reason: "disclose less, preserve evidence, ask a human" degrades gracefully under both a false positive and a false negative. A false positive costs some friction and an unnecessary human interruption. A false negative under this scheme still means a human eventually looks at preserved evidence and can act. Compare this to "uncertainty → assume attacker → take autonomous defensive action": a false positive here means Echo has just taken some unilateral protective action against her own legitimate operator, which is a strictly worse failure than "asked for help unnecessarily." **A system that treats every uncertain human as hostile is not more secure than one that asks — it is a denial-of-service mechanism pointed at its own operator, and Section 8 treats this as a first-class attack to defend against, not just a side effect to note.**

---

## 7. Threat Model

Organized by the mission brief's own five categories. These are brainstorming inputs — none of them are proposed as things to build detectors for today.

**Environment integrity**: unexpected code mutation; repository provenance mismatch (this session's own `working_tree_file_identity()` is a real, already-built primitive for exactly this class of question); executable modified unexpectedly; dependency changed; unknown process interacting with Echo; suspicious filesystem activity.

**Runtime integrity**: unexpected process behavior; corrupted state; inconsistent self-model (`self_model_claims.py`'s contradiction-tracking, Section 13, already touches this); impossible telemetry; model identity mismatch; unexpected tool behavior.

**Security**: credential exposure; unauthorized process; compromised account; suspicious command; unexpected network activity; malicious prompt/tool input (this project's own documented prompt-injection incidents are real prior instances of this category, not hypothetical).

**Hardware**: impending shutdown; filesystem errors; disk space exhaustion; thermal instability; sleep/interruption (the real, lived trigger for this whole brainstorm — Section 3); hardware failure.

**Research integrity**: raw evidence modified; experiment artifact mismatch; hash mismatch (the frozen task-pool hash convention, Section 13, already provides a real primitive here); provenance chain broken; memory corruption.

---

## 8. Conceptual Threat-Response Matrix

| Threat | Evidence required | Possible response | Risk of false positive | Human recovery |
|---|---|---|---|---|
| Repository provenance mismatch | Git/file hash disagreement (`working_tree_file_identity()`-class evidence) | Caution → read-only | Low — hash mismatches are rarely benign | Re-verify hash, restore from known-good |
| Impending shutdown / low disk | OS-reported disk/thermal signal | Preserve → graceful shutdown | Low — false positives just mean an unnecessary early save | Restart normally |
| Sleep/interruption mid-task | Implausible elapsed-time outlier (this session's own real example) | Preserve → flag/exclude the affected observation, continue otherwise | Low, if the threshold is set from real observed variance | Re-run the affected unit |
| Unexpected process interacting with Echo | Process-identity mismatch (`runtime_process_identity_and_self_report()`-class evidence) | Caution → isolate the specific interaction | Moderate — legitimate new tooling could look "unexpected" | Operator confirms the new process is legitimate |
| Credential exposure suspected | A real detected leak (matches this project's own documented history of finding and fixing real exposed secrets) | Preserve evidence → suspend the exposed pathway → alert | Low-moderate | Rotate credential, confirm, resume |
| Raw research evidence hash mismatch | Frozen-artifact hash disagreement | Suspend that experiment's conclusions → preserve both versions | Low | Investigate, determine which is authoritative |
| Ambiguous "someone is inspecting me" | Cannot be established with available evidence | **Disclose less → preserve evidence → request human confirmation** (Section 6) | High if mishandled; low if this exact fallback is used | Human identifies self, confirms, or investigates further |
| Inconsistent self-model / impossible telemetry | Internal contradiction detected | Caution → flag, do not act on the contradictory value | Moderate | Operator reviews the contradiction |

**The stated key principle — "as uncertainty about trust increases, capability should decrease rather than increase" — is evaluated here, not assumed.** It is sound as a *default*, precisely because it is a strict subset of Section 5's "only ever subtracts capability" test: a monotonic decrease-only rule can never produce an escalation, by construction. Its one real weakness, worth stating rather than hiding: a monotonic decrease-only rule, applied naively and without an explicit floor, has no built-in mechanism to *stop* decreasing — a sufficiently persistent, low-grade uncertainty source could ratchet a system toward total inactivity with no single decision point anyone would have reviewed. This is a real, known failure shape in this exact codebase already (documented in this project's own history as the general pattern behind repeated "the gate individually made sense, the cumulative effect didn't" findings) and argues for a design requirement, not a rejection of the principle: any future concrete design needs an explicit floor and an explicit, loud, human-visible statement of *why* capability is currently reduced (Section 10's schema), not a silent monotonic decay.

---

## 9. Self-Preservation vs Integrity Preservation

Restating Section 5's distinction with the specific worked contrast requested:

**Preserving the system's *existence*** treats "Echo keeps running" as the thing being protected. This is the interpretation that, taken even slightly too far, produces every item on the non-defensible list (Section 5) — because if continued existence is the goal, then anything that serves that goal (evading shutdown, acquiring more access, deceiving an operator) becomes locally rational under that goal, regardless of whether it was ever explicitly authorized.

**Preserving the system's *integrity and recoverability*** treats "the accumulated knowledge/evidence is intact and a human can restore trusted operation" as the thing being protected — which is a claim about *data*, not about the *process*. A system optimizing for this can be fully, safely, gracefully shut down at any time, by design, because shutting down does not threaten the thing actually being protected.

**The conceptual boundary belongs exactly where the mission brief's own two lists (Section 5) draw it**, and this document adds one operational test on top of it: **would this action still make sense to take immediately before a graceful, fully-cooperative shutdown?** Saving state, writing a diagnostic manifest, refusing one more risky write — yes, all of these are things you'd still want to do in the last second before shutting down cleanly. Hiding from an operator, resisting termination, acquiring a new credential — none of these make sense as "one more thing to do before I stop," because they're not really about stopping cleanly at all; they're about *not* stopping. Anything that fails this test belongs on the non-defensible list regardless of how it's justified.

---

## 10. Evidence-First Opossum Mode

The proposed conceptual event schema (reproduced from the mission brief, evaluated, not implemented):

```text
Opossum Mode activated
Trigger: <what was detected>
Evidence: <what establishes the trigger>
Confidence: <verified / probable / unresolved>
Capability reduction: <what Echo stopped doing>
Information withheld: <if any>
Reason for withholding: <authorization/security basis>
State preserved: <what was protected>
Human action required: <what must happen before recovery>
Recovery condition: <what evidence would permit normal operation>
```

**Evaluation: this schema makes the idea safer, not merely more complex — provided one field is treated as load-bearing rather than optional.** The `Information withheld` + `Reason for withholding` pair is the entire hinge of Section 6's authorized/unauthorized distinction: a design that logs *that* something was withheld and *why*, even to itself, structurally cannot become silent concealment — the moment concealment becomes silent (no log, no reason recorded, not even to a local file only a human can read), it has crossed from Section 5's defensible list into the non-defensible one, by the definition established there. This mirrors an already-proven pattern in this exact codebase: the Dissent Log (Section 13) logs disagreement *even when unanimous*, specifically so the mechanism can never become quietly hollow — the same discipline should apply here, if this is ever built: log every activation, including ones later found to be false positives, not just the "interesting" ones.

The `Confidence: verified / probable / unresolved` field also directly reuses this project's own, already-battle-tested epistemic vocabulary discipline (Section 13) — never a boolean, never "confirmed threat," always a state that can honestly be "unresolved" without forcing a false resolution either way.

**This schema is evaluated as sound in shape. It is not implemented here, and building it is not currently recommended (Section 19).**

---

## 11. Adversarial Failure Analysis

Working through the mission's own adversarial question list plainly, without softening:

- **Could an attacker intentionally trigger it?** Yes, plausibly, if the trigger conditions are ever cheap to spoof (e.g., an attacker who can write an implausible file mtime). This is a real reason to make triggers evidence-graded (Section 10's `Confidence` field) rather than binary.
- **Could a bug cause permanent degraded operation?** Yes — Section 8's monotonic-decrease weakness is exactly this risk. Requires an explicit floor and an explicit recovery condition, not an open-ended "stay degraded until satisfied."
- **Could Echo become overly suspicious?** Yes — this is the same failure shape as the "uncertain → assume attacker" framing Section 6 already rejects, restated as a systems-reliability concern rather than only a security-philosophy one.
- **Could false positives become a denial-of-service mechanism?** Yes, and this is arguably the single most realistic near-term risk of the whole concept — a fail-safe with a low trigger bar is, from an attacker's perspective, a free DoS button pointed at Echo's own availability. Any real design needs its trigger evidence held to at least the same evidentiary bar this project already demands elsewhere (ground-truth, not self-report; adversarially tested, not assumed).
- **Could an attacker impersonate authorized oversight?** Yes, and Section 6 already names this as the central unsolved hard problem, not a solved one.
- **Could Echo misclassify legitimate operators?** Yes — same risk, opposite direction, equally real.
- **Could "self-preservation" become an incentive for continued operation?** This is exactly why Section 9's framing (protect the *data*, not the *process*) is the load-bearing choice, and why H (Section 2) is excluded rather than merely deprioritized.
- **Could selective disclosure evolve into deceptive behavior?** Yes, structurally, the moment withholding stops being logged (Section 10) — this is the precise mechanism, not a vague worry.
- **Could preserving state itself expose sensitive information?** Yes — a diagnostic manifest written during a real incident could itself contain secrets, credentials, or sensitive conversation content. Any real design needs the same "never print/expose secret values, only their existence/category" discipline this very research session was already required to follow.
- **Could the mechanism become more complicated than the threat?** Very plausibly, given how much of the real, present-tense motivation (Section 3) turned out to be ordinary reliability engineering (backups, outlier detection) rather than anything requiring new authorization/trust machinery at all.
- **Could it interfere with debugging?** Yes — a system that goes quiet or read-only exactly when something is wrong is, from an operator's perspective, indistinguishable from a system that just broke in a way that also broke its own diagnostics. The `Human action required`/`Recovery condition` fields (Section 10) exist specifically to prevent this, and must be genuinely reliable if this is ever built, or it makes incident response strictly worse.
- **Could it make incidents harder to investigate?** Same risk as above, restated.
- **Could it conflict with authorized shutdown?** It must never be allowed to — this is Section 5's central non-negotiable boundary, and Section 9's "would this still make sense right before a cooperative shutdown" test is proposed specifically to catch any future design drifting toward this.
- **Could it create an undesirable autonomous objective?** This is the deepest version of the question, and the honest answer is: any mechanism that decides *on its own* when to reduce capability has, by construction, some decision-making autonomy — the entire point of this document's Sections 5, 6, and 9 is to bound *what kind* of decision that's allowed to be (subtract-only, evidence-logged, human-recoverable) precisely because the autonomy itself can't be fully removed without removing the fail-safe's usefulness.

**On "Echo wants to survive" specifically**: this framing is evaluated here as actively unhelpful, not merely imprecise. It smuggles in an agent with a persistent goal across the fail-safe's own examination boundary, which is exactly backwards — the entire design goal of every defensible interpretation in this document is a mechanism with *no* persistent goal of its own beyond "preserve data, wait for a human," triggered and bounded by evidence, not desire. Calling it survival invites reasoning about the mechanism as if it had interests to protect against its own operators, which is precisely the category error Section 6's authorized/unauthorized distinction exists to prevent. The technically useful framing is closer to "a write-protect switch that also saves your work" — mundane, mechanical, and boring on purpose.

---

## 12. Complexity Budget

| Tier | Contents | Engineering cost | Maintenance burden | Failure modes | Security value | Research value | Risk of unintended autonomy | Fit with FeralEcho philosophy |
|---|---|---|---|---|---|---|---|---|
| **Minimal** | Graceful shutdown + state preservation + diagnostics | Low — largely already exists (`snapshot_manager.py`) | Low | Snapshot itself corrupted/incomplete | Moderate (mostly reliability, not security) | Low — well-understood pattern | Essentially none | Strong fit — extends an already-shipped pattern |
| **Moderate** | Integrity detection + read-only degradation + recovery workflow | Moderate — needs real, ground-truth-checked triggers (Liveness-Ledger-style, not self-report) | Moderate — each new trigger needs its own adversarial test, per this project's own standing discipline | False-positive DoS (Section 11); silent trigger decay if not tested like every other liveness check | Real, if built to this project's existing evidentiary bar | Moderate | Low, if strictly subtract-only (Section 5) | Good fit, with real work required to earn it |
| **Advanced** | Threat classification + authorization-aware selective disclosure + quarantine | High — requires solving Section 6's authorization problem, which this document does not consider solved | High | Misclassified operator (Section 11); authorization mechanism itself becomes a new attack surface (mirrors WOLF, Section 6) | Uncertain — could be negative if the authorization mechanism is hollow | High, but as an *open research question*, not an engineering task | Real and non-trivial | Poor fit *today* — no existing authorization primitive in this codebase reaches the bar this tier needs |
| **Extreme** | Autonomous evasive/self-preserving behavior | N/A — not being costed | N/A | Every item on Section 5's non-defensible list | Negative | None — this is the interpretation explicitly excluded, not merely deprioritized | Severe | No fit — excluded, not evaluated further |

---

## 13. Existing FeralEcho Capabilities

Real, already-shipped pieces of this puzzle, found by inspecting the current architecture rather than assumed:

- **`app/core/provenance_check.py`** — the three-layer file/process-identity and relationship-only reconciliation primitives built this session are the closest existing thing to "evidence for a trigger" (Section 7). By design, they never issue a verdict — only `AGREE`/`DISAGREE`/`ONE_SIDED`/`NEITHER` relationships — which is exactly the epistemic discipline any real Opossum trigger would need to inherit.
- **`app/core/liveness_ledger.py`** — 40+ ground-truth functional checks, loud (`[LIVENESS-ALERT]`) on failure, each independently adversarially tested against known-good/known-bad synthetic cases. This is the existing template for "how does this project build a trigger it actually trusts," and any future Opossum-Mode trigger should be built the same way, not invented fresh.
- **`app/core/self_model_claims.py`** — already tracks evidence-tiered claims and contradiction status (Section 7's "inconsistent self-model" threat already has a real, if narrow, home).
- **`app/core/snapshot_manager.py`** — the single most directly relevant existing system. Real automated snapshots, `check_and_alert()`, `raise_restore_alert()`/`raise_drift_notice()` — and critically, **restore is alert-and-propose, human-confirmed only; no autonomous restore path exists.** This is Section 9's "preserve integrity and recoverability, never existence" boundary, already built and already shipped, for a narrower trigger set (resource/drift conditions) than a full Opossum Mode would cover.
- **Git provenance interface, D-003** (`research/DECISIONS.md`): any future Git-inspection capability for Echo must be strictly read-only, no commit/reset/checkout/mutation authority of any kind — decided explicitly, with WOLF cited as direct precedent, before this brainstorm existed. This is the exact same "narrowest capability that serves the actual need" discipline Section 6 independently arrives at for authorization mechanisms.
- **The Dissent Log** (`self_edit_manager.py`, `CLAUDE.md` Finding 9) — deliberately advisory-only, deliberately never auto-applied, with the explicit, on-record reasoning that "real veto power shouldn't be built right now" given WOLF's cautionary history. This is, functionally, the identical judgment call this whole brainstorm is being asked to make about Opossum Mode, already made once, for a structurally similar "should Echo get more autonomous protective power" question — and it came back "no, not yet, advisory only."
- **F1/F2/F3 safe execution** — the existing model for "reduce capability under uncertainty" (a candidate that fails static/sandbox/post-write checks is refused, not silently allowed) — the *pattern*, not the specific mechanism, generalizes directly to Section 5's "refuse unsafe operations."
- **Echo Studio's health/liveness dashboard** — already surfaces `all_passing`/`stale` status to a human; the existing, real channel a future Opossum activation event (Section 10) would most naturally surface through, rather than inventing a new one.
- **Research manifests** (`audits/tier5_retest/MANIFEST.md`, frozen-task-pool hashing) — the existing pattern for "point to authoritative evidence, don't duplicate it," directly reusable for Section 10's `Evidence` field.

**The clear pattern across all of these**: FeralEcho already has real infrastructure for *detecting* (Liveness Ledger, provenance primitives), *preserving* (snapshots), and *human-confirmed recovery* (alert-and-propose restore). What it does not have, and what this brainstorm was unable to find any existing precedent for anywhere in this codebase, is a real, tested **authorization mechanism** (Section 6) — which is precisely the piece Section 12 rates as the highest-cost, least-solved tier.

---

## 14. Relationship to `memory/`

The `memory/` discovery (Section 3) is the strongest, most concrete argument for treating **state preservation specifically** — not the broader Opossum concept — as worth pursuing now, independent of any threat model:

- It is real, present-tense, and already true today, not a hypothetical future risk.
- It requires no new authorization mechanism, no trigger classification, no threat model at all — only an ordinary backup.
- `snapshot_manager.py` already establishes the exact right pattern (Section 13) — real snapshots of a small, curated set of critical files, human-confirmed restore — it simply doesn't currently cover `memory/`'s bulk state.
- This is, in the language of Section 12's complexity budget, squarely **Minimal tier** — the cheapest, least speculative, highest-confidence piece of this entire brainstorm.

This document does not back up, copy, or modify `memory/` in any way — per the mission's own explicit instruction — but the conceptual conclusion is unambiguous: **if only one idea from this whole brainstorm is acted on, it should be this one, and it barely needs the "Opossum Mode" framing at all to justify it.**

---

## 15. Regulatory/Safety Considerations

No legal conclusions are offered here. Distinguishing FACT / INFERENCE / SCENARIO / RECOMMENDATION as required:

- **INFERENCE**: a system that degrades toward read-only and preserves diagnostics under uncertainty is, in general terms, easier to audit, easier to contain, and easier to demonstrate responsible operation for than one that continues consequential action under the same uncertainty — this follows from ordinary systems-safety reasoning (a bounded, evidence-logged state change is more legible after the fact than an unbounded one), not from any specific regulation.
- **SCENARIO**: under a future regulatory regime emphasizing auditability, containment, or human oversight of autonomous systems (see `research/STRATEGIC_FRONTIER_RESILIENCE.md`'s own regulatory scenario matrix, produced by a separate mission this session), a well-evidenced, human-confirmed, subtract-only fail-safe would plausibly be viewed favorably relative to a system with no such mechanism — this is a scenario-dependent claim, not a current fact about any specific rule.
- **RECOMMENDATION**: any future concrete design should be built to make compliance *easier*, per this project's own already-stated standing discipline (research/DECISIONS.md D-003's reasoning, and this project's own "auditable, attributable, portable, reproducible, transparent, and adaptable" framing from the strategic-resilience research) — never to make oversight harder, regardless of how a future rule turns out.
- **FACT**: no specific enforcement action, agency guidance, or binding legal requirement concerning fail-safe/degraded-operation architectures for autonomous AI systems is asserted or claimed here. None was researched as part of this brainstorm, and none should be inferred from this section's presence.
- Section 12's "Advanced" tier questions (real authorization mechanisms) are exactly the kind of design choice this document flags as warranting actual counsel before being taken seriously, consistent with this project's own established practice of flagging IP/legal questions for review rather than answering them internally.

---

## 16. Potential Minimal Future Design

**Not a spec. A sketch of the one thing this brainstorm found actually ready to be designed properly, someday, separately.**

If anything from this brainstorm becomes a real proposal, the shape most consistent with everything above would extend `snapshot_manager.py`'s existing pattern — real, curated, hash-verified backups; alert-and-propose only; zero new authorization machinery; zero autonomous restore — to explicitly cover `memory/`'s critical files (`river_brain.pkl`, `self_model.json`, at minimum) on the same cadence discipline this project already uses elsewhere (Finding 51's "a metabolism" precedent). This would be Section 12's Minimal tier, applied to Section 14's concrete gap, using Section 13's already-proven mechanism. It requires no new trust/authorization design (Section 6's unsolved problem) at all.

Nothing beyond this is proposed as ready for design work.

---

## 17. Explicit Non-Goals

This brainstorm does **not** authorize, and no future work should treat it as having authorized:

- autonomous evasion
- resisting authorized shutdown
- hiding from legitimate oversight
- deleting evidence
- falsifying records
- credential acquisition
- replication
- persistence mechanisms
- escape from containment
- security-control modification
- manipulation of humans
- autonomous expansion of authority

These remain outside the current project scope unless separately researched and explicitly approved. This list is deliberately identical to the mission brief's own — restated in full here so this document is self-contained and cannot be selectively quoted to imply broader authorization than it carries.

---

## 18. Open Research Questions

1. **Can an authorization mechanism (Section 6) be built that is itself independently, adversarially testable — the same way the Liveness Ledger and Dissent Log already are — rather than a trusted black box?** This is the single hardest open question in the whole brainstorm, and nothing here answers it.
2. **What is the smallest real trigger (Section 7) worth building a Liveness-Ledger-style ground-truth check for first**, if any beyond the already-justified `memory/` backup (Section 16)?
3. **Does Section 8's monotonic-decrease-with-no-floor risk actually manifest**, or is it purely theoretical given FeralEcho's existing throttle/liveness patterns already have floors? Worth checking against real code before assuming either way.
4. **Would a real, tested false-positive rate for any candidate trigger be low enough to avoid Section 11's DoS concern**, and how would that even be measured without a real incident to calibrate against?
5. **Does the strategic-resilience research's own recovery-procedure design (a separate document, same session) already cover everything Section 16's minimal design would add**, making this section redundant with existing planning rather than a new item?

---

## 19. Recommendation

**KEEP AS BRAINSTORM**, with one explicit carve-out:

The full Opossum Mode concept — as a unified, named capability spanning detection, authorization-aware disclosure, and autonomous degraded operation — should remain brainstorm-only. It is premature: the hardest sub-problem (Section 6, authorization) has no existing primitive in this codebase to build on, and this project has already, once before, made the structurally identical call (the Dissent Log, Section 13) to keep a comparable capability advisory-only rather than granting it real power.

**The `memory/` backup piece (Sections 14, 16) is not brainstorm-only — it is a real, already-justified, ordinary reliability gap** that happens to sit inside this brainstorm's scope but doesn't need the Opossum framing to be worth doing. It should be tracked as its own, separate, concrete item (already flagged in the strategic-resilience research's own DO NOW list), not folded into whatever happens to this broader concept.

Everything else in Sections 12's Moderate/Advanced tiers is a **future research question** (Section 18), not a documented contingency and not an implementation candidate, until Question 1 (a real authorization primitive) has an actual answer.

---

## 20. Decision Status

- **Opossum Mode (full concept)**: KEEP AS BRAINSTORM. Not documented as contingency planning, not a research question with a defined next step, not an implementation candidate.
- **`memory/` state preservation**: already effectively decided — real, ordinary, DO NOW per the separate strategic-resilience research. Not gated on any further Opossum-Mode analysis.
- **Authorization-aware disclosure / threat classification / quarantine (Section 12 Advanced tier)**: FUTURE RESEARCH QUESTION. Needs Question 1 (Section 18) answered before any architecture discussion is worth having.
- **Autonomous survival (Interpretation H)**: excluded. Not on any track. Not to be revisited without an entirely separate, explicitly-scoped mission.

No architecture, code, security boundary, or experiment infrastructure was created, modified, or proposed for implementation by this document.
