# Adversarial Pre-Implementation Review of G0 → E5-mini

Date: 2026-09-16. Reviewer: Claude (fork), acting as hostile-but-fair independent reviewer per explicit instruction. Status: read-only. Nothing implemented, executed, or mutated. This report itself is the only artifact created.

**Purpose stated by the user, preserved verbatim because it should govern every judgment call below:** "The purpose of this mission is not to prove that FeralEcho learns. The purpose is to make it difficult for us to mistakenly conclude that it does."

---

## 1. Executive verdict

**B — READY WITH REQUIRED CHANGES.**

The causal design underlying G0 → E5-mini (frozen teaching-derived procedure P, vs. information-matched curated episodes E, vs. no acquired memory N, under isolation, with reload) is sound in principle and, notably, is already the *most* self-critical of the three documents under review — the reconciliation report explicitly narrows its own claims, rejects an embedding-distance floor as insufficient, and separates transfer (L4) from accumulation (L5) more carefully than either prior report. That honesty is a real point in its favor and is why this verdict is not C.

But two gaps are load-bearing enough to block execution, not just polish:

1. **E5 has no arm-level condition-integrity manifest or independent transport checker.** E3 (§11 of the reconciliation) got one, built in direct response to this exact codebase's own real, recent failure (a Condition-A control that silently never bypassed council, caught by independent review one day before this mission). E5 — explicitly named "highest scientific priority" — did not get the equivalent protection. Given that the P/E/N arms differ by *what evidence a call is allowed to see*, not by which code path runs, this is arguably an even easier place for a labeled-but-wrong condition to hide than E3's routing bug was, and there is currently no proposed mechanism that would catch it before someone reads the P>E number and believes it.
2. **The P-vs-E comparison has no control for the "procedure generation is itself an extra reasoning/distillation pass" confound**, despite the reconciliation's own text acknowledging the underlying risk ("license representation/usage effect, not uniquely procedural internal cognition") without actually proposing a primary-analysis control for it. The one control that would bound this — a procedure written from the task family's *public specification alone*, with zero teaching examples — exists in the design only as an "Optional P-shuffled development control" testing something different (irrelevance, not model-prior leakage), and is explicitly not part of confirmation.

Both are specific, addable fixes to an otherwise well-scoped design — not evidence the hypothesis is untestable (C) or that the wrong experiment has been proposed (D). §16 gives the minimal revised specification.

---

## 2. Mission integrity / HEAD / status / process observations

- **Opening HEAD:** `2fba42644c82b9f7096276f4dd338d615cf1bcce`.
- **Opening working-tree status:** 177 entries (`git status --short --untracked-files=all`), consistent with the reconciliation report's own opening count (it recorded 176 before its own report existed; +1 for that file matches this mission's 177).
- **Live processes confirmed present and undisturbed at mission start:** `run.py` PID 7644 (started Sep 10 22:41, continuous uptime per `ps` elapsed-time field), `start_echo.sh` watchdog PID 7636, `ollama serve` PID 13534 (started Sep 2). No process was signaled, attached to, stopped, or restarted. No model was loaded, no RiverBrain/FAISS state was imported or unpickled, no experiment was executed.
- **Methods used:** `git rev-parse`/`git status` (read-only), `ps` (read-only), `Read` on the three source reports in full, targeted `grep`/`Read` against current source (`hub/check_hub.py`, `hub/notes.py`, `claude_relay/relay.py`, `scripts/task_type_behavioral_experiment.py`) to independently spot-check specific claims in the reconciliation report's disagreement matrix rather than trust its self-report. No production import, no pickle deserialization, no inference, no scratch file created.
- **Closing HEAD:** `2fba42644c82b9f7096276f4dd338d615cf1bcce` — unchanged.
- **Files changed by this mission:** exactly one — this report. No other path was created, modified, or deleted.
- **Closing process check:** `run.py` (7644), watchdog (7636), and `ollama serve` (13534) confirmed still running with the same PIDs at mission close.

**Independent spot-checks of the reconciliation report's own claims, performed before trusting it as a design source (per this mission's explicit instruction to treat none of the three reports as authoritative):**

- **D15 (hub cursor fix):** OBSERVED(source) directly — `claude_relay/relay.py:110` defines `_HUB_MARKER_FILE`, `hub/notes.py:208` calls `read-hub`, and `hub/check_hub.py:52` does indeed hardcode `"checked_by": "claude-m5"` exactly as the reconciliation's D15 row claims (the fix is real and landed; the residual attribution issue is also real and unfixed). This is a case of the reconciliation's own "INDEPENDENT RECHECK" column checking out under a second, independent check.
- **D6 (E3's Condition-A bug source):** OBSERVED(source) directly — `scripts/task_type_behavioral_experiment.py:207-217` confirms `disable_direct_echo_bypass_for_personal()` clears the module-level `DIRECT_ECHO_TASKS` frozenset unconditionally, matching the reconciliation's characterization and this codebase's own documented history (`audits/2026-09-15_codex_task_type_independent_review.md`).

These two checks succeeding independently raises confidence that the reconciliation report's specific, checkable claims are trustworthy — but confidence in past factual claims is not the same as confidence that the *proposed* E5-mini design is sufficient, which is this report's actual subject.

---

## 3. Exact causal claim under test

As stated by the user, this is the claim E5-mini is meant to support (or fail to support):

> FeralEcho acquired information from teaching experience, transformed it into retained reusable procedural knowledge, and that retained procedure caused improved performance on genuinely withheld related tasks beyond matched episodic memory and no-memory controls.

The reconciliation report's own final-section answer operationalizes E5-mini specifically as: **4 deterministic task families, 2 teaching tasks/family, 4 structurally distinct withheld tasks + 1 unrelated + 1 adversarial near-match per family, comparing P (frozen procedure) vs. E (matched curated episodes) vs. N (no memory) under a shared solver/budget, with reload before final testing, retaining failed-teaching families in the denominator.** This is explicitly framed by its own authors as a "feasibility/pilot experiment, not adequately powered confirmation" — a framing this review treats as correct and does not challenge. What this review challenges is whether even that narrower, honestly-scoped pilot claim is actually supportable by the design as currently specified.

---

## 4. Causal-chain attack

`TEACHING EXPERIENCE → PROCEDURE ACQUISITION → DURABLE REPRESENTATION → PROCEDURE RETRIEVAL/APPLICATION → WITHHELD TASK BEHAVIOR → INDEPENDENT OUTCOME IMPROVEMENT`

| Arrow | Attack | Design permits it? | Exposing evidence | Eliminating control | When required |
|---|---|---|---|---|---|
| Teaching → Acquisition | The "acquisition" step (procedure generation) is a real LLM reasoning call, not a passive transcription. It can inject general knowledge the base model already has, triggered by the family topic rather than derived from the three specific teaching examples. | **YES** — nothing in §13 of the reconciliation blocks a procedure generator from writing a textbook-general answer after seeing only the family's public spec framing. | A no-teaching-examples procedure (generated from spec alone) performing comparably to the teaching-derived P. | Add a "zero-shot procedure" arm (Z): same generator, same prompt shape, spec only, no teaching examples, to primary analysis — not just development. | **MUST FIX BEFORE EXECUTION** (see §16). |
| Acquisition → Durable representation | "Validated" procedure (§13) implies some acceptance step; unspecified whether validation includes any iteration/testing beyond the raw teaching outcomes. | **PARTIALLY UNRESOLVED** — spec text does not describe E receiving an equivalent validation/iteration pass. | Compare wall-clock/call-count spent constructing P vs. E; an asymmetry here is itself evidence of an extra selection step. | Log and report construction cost (calls, tokens, iterations) for P and E symmetrically; if asymmetric, treat as a confound requiring separate accounting, not silence. | SHOULD ADD IF CHEAP — cheap to log, doesn't require new experimental logic. |
| Representation → Retrieval/application | Procedure application itself involves the solver deciding *whether* to apply P. A solver that blindly applies P to everything (or is implicitly cued to apply it because P is present at all) could pass "transfer" while never doing real discrimination. | **YES**, addressed partially — §13 lists negative controls (12 unrelated, 12 adversarial near-match per the larger E5; E5-mini's answer section specifies only 1 unrelated + 1 near-match per family, a much thinner check at n=4 families). | False-application rate on near-match/unrelated tasks. | At minimum, don't drop the near-match/unrelated controls in the "mini" scaling-down — 1 each per family (4 total near-match, 4 total unrelated across the whole pilot) is too thin to detect an "always apply" failure mode with any real confidence. | MUST FIX BEFORE EXECUTION — this is a real regression from the (already pilot-only) 12-family E5's 12+12 controls down to something that can't discriminate a trivial "always apply" policy from real conditional competence. |
| Application → Withheld-task behavior | Task-family single-custodian authorship: the same person/process who writes teaching tasks also writes withheld tasks, meaning both are drawn from the same mental model of "the technique this family is about." | **YES** — §13 names an "independent custodian" for family definitions, teaching, and withheld tasks together; the *test custodian does not write procedures*, but nothing separates *family/task design* from *withheld-task design* by a second independent author. | A withheld task solvable purely by pattern-matching the family name/spec, independent of any teaching content. | Blind second-author review of withheld tasks specifically against "would this be solvable by a strong generalist coder given only the unrelated-task pool, with zero exposure to this family's teaching or spec" — i.e., an N-only pilot probe before running the real experiment. | SHOULD ADD IF CHEAP — cheap relative to the full pilot, catches ceiling effects before spending the real run. |
| Withheld behavior → Outcome improvement | Deterministic oracle correctness is well-covered by G0 (§6) in principle — but G0 as specified qualifies the *measurement instrument's honesty*, not the *fairness of arm construction*. A perfectly honest instrument can still faithfully record a biased comparison. | **YES** — this is a structural gap in scope, not a flaw in G0 itself. | N/A — this is a category distinction, not a single failure mode. | State explicitly, in any report of E5-mini results, that G0 qualification proves the *recording* is trustworthy, not that the *comparison* is fair — these are separate claims and must not be conflated in the writeup. | MUST FIX BEFORE IMPLEMENTATION (documentation/framing fix, zero engineering cost). |

**Additional confounds from the mission's §4 list, checked individually against the actual E5-mini spec:**

- **Answer/test leakage across P vs E:** addressed — "P and E receive exactly the same teaching-experience pool before representation... Procedure may not add oracle/withheld facts" (§13). OBSERVED(source, reconciliation text) as a real stated constraint, but there is no described *mechanism* enforcing it beyond author discipline — no automated check that a frozen procedure's text doesn't contain phrases lifted from withheld-task specifics. PROPOSED FIX: hash/substring-check P and E against the withheld-task corpus before freezing, as a cheap automatable gate (mirrors G0's own forged-success detection instinct, applied one level up).
- **Family contamination via shared FAISS/session state:** addressed structurally — "No shared FAISS, conversation history, cache keys, hub notes or adaptive River state" (§13 Family isolation). This is a real, correctly-identified requirement; whether the *implementation* actually enforces it is untestable from a document review and becomes G0/I2's job at build time.
- **Evaluator leakage (procedure author sees withheld criteria):** addressed by role separation language, but see the causal-chain row above — role separation is asserted for procedure-writing vs. test-writing, not for family-design vs. withheld-task-design, which is the more subtle version of the same leak.
- **Compute/token-budget asymmetry:** explicitly and carefully handled — "Cap memory at 1,024 tokens and total context at 8,192... Report actual token use... Do not claim token equality eliminates differences in useful information organization — that is part of the intervention" (§13). This is a genuinely strong, honest treatment; **no further control needed here.**
- **Model/version drift within the pilot:** not separately addressed for E5-mini specifically, but the broader isolation contract (§16, I1-I4) applies generically. UNRESOLVED whether E5-mini's own short timeline makes this a real risk (likely low, given a pilot should complete in one sitting) — **UNNECESSARY** to add new machinery here.

---

## 5. P-vs-E counterfactual analysis

This is the section the mission explicitly flags as most important, and it deserves the most direct treatment.

**What P > E can license, and what it cannot, depends entirely on what varies between P's and E's construction — and right now, more varies than "procedure vs. episode."**

Three things are bundled together in the current P vs. E comparison, and the design as specified cannot separate them:

**(A) Legitimate representational advantage from experience** — P organizes information more usefully than raw episodes because *procedural form itself* is a better format for reuse (the intended effect).

**(B) An extra reasoning pass at construction time** — generating P requires an LLM to read teaching outcomes and *synthesize* a generalization; this synthesis step is itself a capability call that E's construction (curation/selection of raw episodes, per §13's "fixed independent truncation/selection rule") does not receive an equivalent version of. If the procedure-generation call is doing real inferential work beyond compression, then P's advantage may come from *that call's reasoning*, not from the teaching examples specifically.

**(C) Base-model prior knowledge, triggered rather than taught** — if the family covers a well-known technique (plausible, since "deterministic code/data transformations" pilot families are likely to be recognizable CS patterns: sorting by key, memoization, two-pointer, etc.), the procedure-generation call may be reconstructing something the base model already knows well, using the teaching examples mainly as a *cue* for which known technique to write down — not as the actual source of the competence being measured.

The reconciliation report's own text (§13, row on "Equal token budget controls retrieval advantage") already names this risk in principle: *"Same length does not equal same information... license representation/usage effect, not uniquely procedural internal cognition."* This is the right instinct, stated honestly — but it stops at acknowledgment. **No primary-analysis arm actually isolates (B) or (C) from (A).** The one candidate control that exists — "Optional P-shuffled development control: unrelated safe procedure" — tests something different: whether an *irrelevant* procedure helps (it shouldn't), not whether a procedure generated *without any teaching* (i.e., from spec alone) performs comparably to one generated *with* teaching. Those are different questions. A P-shuffled control catches "the solver just does better whenever any procedure-shaped text is present"; it does not catch "the procedure-generation LLM call already knew this technique before seeing the teaching examples."

**Distinguishing what P > E does and doesn't license, precisely:**

- P > E (alone) licenses: *"For this solver/environment, a frozen procedure representation of the teaching-experience pool outperformed a curated-episode representation of the same pool, within the stated token budget."* This is a genuine, useful finding about **representation**, and it is worth having even if procedural vs. episodic memory turns out to be the whole story.
- P > E does **not** license: "Echo learned a transferable method from teaching" — because the design cannot currently rule out that the procedure-generation call's own reasoning (independent of which three examples it happened to see) is doing most of the work.
- P > E does **not** license: "internal learner competence grew" — a construction-time LLM call producing a better artifact is not evidence that FeralEcho's own retained state improved; it's evidence that procedures beat episodes as a *memory format*, a real and useful but much narrower claim.

**Minimum fair counterfactual required, not maximal symmetry for its own sake:** add arm **Z** — a procedure generated by the identical generator/template/token-budget as P, but conditioned *only* on the family's public specification, with **zero** teaching-task exposure. This is cheap (one more generation per family, no new infrastructure, no new evaluator) and directly separates (C) from (A)+(B): if Z ≈ P on withheld tasks, the "teaching" component of E5-mini is not doing the work the report wants to claim it's doing, regardless of how P compares to E or N. If Z is clearly worse than P, that is real, direct evidence that the *specific teaching content* mattered, which is exactly what the intended claim requires and which no currently-specified arm actually tests.

This is not "impossible information equality merely for symmetry" (which §5 of the mission correctly warns against demanding) — Z is not trying to make P and E identical in information content; it is trying to establish the floor that P must clear before its advantage over E can be attributed to teaching at all.

---

## 6. Task-family/non-duplication attack

The reconciliation's proposed standard (exact hash, normalized lexical similarity, AST/control/data-flow or I/O structure analysis, embedding-flagged human review, explicit renamed-symbol/reordered-input/changed-constant/composition transformations, at least one withheld task per family unsolvable by copying) is **methodologically strong on paper** — stronger than most of what this project's own prior experiments (Tier-3 through Tier-8, per this codebase's research history) used for duplicate detection.

**Constructed failure modes the standard as stated would still miss:**

1. **Algorithmically identical, structurally different.** A withheld task that swaps a `for` loop for a list comprehension, or recursion for iteration, passes AST/control-flow comparison trivially (different tree shape) while requiring *zero* new reasoning if the procedure already states the underlying invariant abstractly (e.g., "maintain a running max while single-passing the list" survives any syntactic restructuring). The proposed AST/control-flow check is actually anti-correlated with catching this: syntactically different but semantically identical tasks are *exactly* what a genuinely good procedure should transfer to, but they're also exactly what the non-duplication check is supposed to rule out as "too similar to be a real test." This is an unavoidable tension, not a design flaw — but the report should name it explicitly rather than let the AST-comparison language imply it solves duplication cleanly.
2. **Family definition leaks the method.** If a family is literally named/described in a way that states the technique ("Family: two-pointer array problems"), the withheld task's *title alone* — visible to the solver before any procedure retrieval — may already narrow the solution space enough that N (no-memory) solves it via prior knowledge plus the family framing, collapsing P−N toward zero for reasons unrelated to teaching.
3. **Embeddings misclassify novelty in both directions**, as the mission's §6 predicts: a withheld task using unfamiliar domain vocabulary (rewritten as a "warehouse inventory" problem instead of "array problem") but requiring the *identical* algorithm will embed far from the teaching tasks and pass the "flagged for review" bar without actually being independent of the taught method — while a task that's genuinely different in required reasoning but uses similar variable names will get needlessly flagged.

**Minimum defensible operational definition, given these limits:** a withheld task is *genuinely novel and requires the taught method* only if (a) it fails all mechanical duplication checks (hash/lexical/AST/I-O), **and** (b) a blind solver given only the unrelated-task pool (never the family's teaching content or the family label) fails it at a materially higher rate than a solver given the teaching content — i.e., novelty is defined empirically, by a **difficulty differential under blinding**, not by any static structural comparison alone. This costs one extra small pilot arm (blind zero-context attempt) but is the only version of "genuinely withheld" that is actually falsifiable rather than asserted.

---

## 7. Negative-control/applicability attack

At the *repaired E5* scale (§13: 12 unrelated + 12 adversarial near-match per pilot), the design has enough statistical room to distinguish "never apply" from "always apply" from genuine conditional application. **At E5-mini scale (1 unrelated + 1 near-match per family, 4 families = 4 unrelated + 4 near-match total), it does not.**

Concretely: a trivial "retrieve procedure, essentially never apply it except when task text is a near-exact match" strategy would show:
- Zero false application on the 4 near-match tasks (correctly abstains) — looks great.
- Zero-to-minimal transfer benefit on the genuine withheld tasks (since it barely applies P) — this **should** fail the "P > E, P > N" primary criterion, which is the actual protection here. So the harm guard is not the binding constraint; the primary success criterion already penalizes an over-cautious policy by failing to show transfer.

Conversely, an "always apply P regardless of context" strategy would show:
- Some real transfer benefit on genuine withheld tasks (if P is any good).
- False application on all 4 near-match tasks — but **4 trials is not enough to distinguish "occasionally over-applies" (acceptable) from "systematically over-applies" (a real negative-transfer risk)** with any confidence. A single false application in 4 near-match trials could be 25% true systematic over-application or could be one unlucky ambiguous case; the design cannot tell these apart at this N.

**Result pattern required before claiming Echo learned an applicability *condition*, not just a procedure:** correct non-application on near-match tasks needs to be observed at a rate meaningfully above chance across enough near-match trials to bound the false-application rate below some pre-declared threshold with a real (even if wide) confidence interval — which is exactly what the *larger* repaired-E5 spec's 12 near-match tasks and stated `<0.10` upper bound are for. E5-mini's 4-per-family total does not reach this. **This is a SHOULD ADD IF CHEAP fix, not a MUST FIX**: report near-match/unrelated results as purely descriptive/anecdotal at mini scale, explicitly not licensing any applicability-condition claim, rather than dropping them or pretending they're adequately powered.

---

## 8. Failed-teaching/selection-bias attack

**This is one of the design's genuine strengths.** §13 explicitly states: "Family failure remains: the procedure arm receives an empty/no-validated-procedure state, all costs and outcomes count. Conditional-on-successful-teaching analysis may be secondary but never the headline." This directly closes the most common version of this bias (silently dropping families where teaching failed).

**One residual path checked and found genuinely closed:** could a family "fail" so completely (e.g., a procedure that's technically non-empty but garbage) that it still gets included in the P arm, but produces such poor performance that the family effectively becomes an outlier the pilot's small N (4 families) can't average out fairly? Yes — this is real, but it is a **statistical power** problem (addressed honestly in §13's sizing language: "12-family pilot is not confirmatory"), not a **selection bias** problem, since the family stays in the denominator either way. No new mechanism required; **UNNECESSARY** beyond what's already specified, provided the report resists the temptation to quietly exclude a bad-outcome family post hoc — worth stating as an explicit MUST FIX BEFORE IMPLEMENTATION rule: **pre-register the full family list and forbid post hoc family exclusion in the E5-mini writeup**, since a 4-family pilot has essentially zero robustness to "we dropped the one that didn't work."

---

## 9. Statistical-unit analysis

The true independent unit here is **family**, not task, not solver seed, not withheld-task count. At n=4 families, this pilot has **four independent observations of the treatment effect.** Two solver seeds per withheld task do not add independent family-level information; they reduce within-family measurement noise at best.

**This pilot cannot support any confirmatory statistical claim, and the reconciliation report is explicit and correct that it doesn't try to** ("This is a feasibility/pilot experiment, not adequately powered confirmation across all families"). The risk is not that the design misrepresents its own power — it's that a positive-looking result (e.g., "P beat both E and N in 3 of 4 families") will be *narratively* compelling in exactly the way this whole review-chain (Codex → Claude → reconciliation → this review) exists to prevent, even though 3/4 is entirely consistent with noise at this sample size. **No statistical method fixes this — the fix is discipline in reporting:** any E5-mini writeup must state the family-level results individually (not pooled into a headline percentage), and must not use significance language, confidence intervals, or p-values on 4 clusters — only descriptive, family-by-family reporting with an explicit statement that this sizes the confirmatory follow-up and nothing more.

---

## 10. G0 attack

The proposed 24-case qualification suite (§6) explicitly covers, by name: known correct/incorrect candidates, syntax failure, timeout, malformed output, forged `ALL_TESTS_PASSED` text, duplicate completion, missing event, changed prompt, forbidden writes to sacrificial fixtures, planted direct-as-council manifests, and planted unrecorded-call manifests. Item 4 ("outcome decisions come from the trusted checker, not candidate stdout/comments or a test result JSON the candidate can edit") directly addresses **oracle artifact modified by candidate**.

**Gaps against this mission's full requested list, not explicitly named among the described cases (the "24" total isn't fully enumerated in the reconciliation text, so some may already be covered by unlisted cases — flagged as UNRESOLVED where genuinely unclear, not assumed absent):**

- **Stale artifact** (an evidence reference pointing at content that's since changed) — not named. SHOULD ADD IF CHEAP.
- **Incorrect parent IDs** (a retry or derived record pointing at the wrong parent attempt) — not named, but the Attempt record schema (§6 minimal-records table) does require `parent_attempt_id or null`, so a planted-wrong-parent-ID test is a natural, cheap extension of the existing schema-validation case (item 1: "reject... unresolved required references"). SHOULD ADD IF CHEAP.
- **Missing attempt** (a task silently has zero recorded attempts, distinct from a recorded-but-failed attempt) — partially covered by "every assigned slot retained" language in the Attempt record spec, but not named as an explicit G0 planted case. MUST FIX BEFORE EXECUTION — this is precisely the failure mode that would let a "failed-teaching family" silently vanish from the denominator (§8's protection is only as good as G0 actually catching a missing-attempt anomaly).
- **Evaluator UNKNOWN silently converted to failure or success downstream** — the Outcome record schema explicitly has an `independent oracle label/unknown` field, which is the right schema design, but no G0 case is named that plants an UNKNOWN result and verifies it survives all the way through aggregation without being silently coerced. SHOULD ADD IF CHEAP — directly relevant given E1's own stated rule ("oracle-infrastructure failures produce UNKNOWN, never false correctness labels") should apply equally to E5.
- **Partial run interpreted as complete** — the Run record's "Run close" schema requires explicit `assigned/completed/failed/unknown/integrity counts` and states "Missing close means incomplete, not zero failures" — this is a real, good design commitment, but again no explicit G0 planted case tests that a crashed/interrupted run is actually flagged incomplete rather than silently read as a clean zero-failure run. MUST FIX BEFORE EXECUTION — this is the single most likely real-world failure mode for an experiment run unattended (a crash mid-run reading as "ran clean, just had no failures").

**Verdict on G0 sufficiency: not sufficient as fully specified for E5-mini, but the fix is enumerable and cheap** — three or four additional planted-anomaly cases (missing attempt, UNKNOWN-conversion, incomplete-run-read-as-clean, stale artifact reference), each mirroring test shapes G0 already has for adjacent anomalies. This is not a reason to reject the instrument-qualification approach; it's a reason to finish enumerating its own stated "24 cases" before trusting it.

---

## 11. Isolation analysis

The isolation contract (§16 of the reconciliation, I0–I4, and the per-namespace table) is the most carefully engineered section of the entire document, and it correctly earns the distinctions the mission's §11 asks for:

- **Shared model-service state vs. shared learned-experiment state, kept explicitly separate**: "Model residency is itself runtime state. Sharing the production Ollama server would perturb cache/load/queue behavior and weaken the no-disturbance premise. Do not silently call it 'read-only inference.'" — this is exactly right, and better than what this project's own earlier isolation work (the redirect-before-first-access pattern documented in this codebase's Tier-8 forensic history) achieved on the first attempt.
- **RiverBrain**: correctly requires OS-level write denial, not just environment-variable redirection ("Redirect alone insufficient" — a direct, correct citation of this exact codebase's own documented historical gap).
- **echo_sandbox.sb explicitly flagged as insufficient as-is** for this program ("allows broad file reads and /dev write-data... Merely redirecting an environment variable or monkeypatching open is not OS isolation") — this is an honest, self-critical admission that the existing sandbox infrastructure this whole project already relies on is not automatically adequate for research isolation, which is correct and non-obvious.

**One real gap:** the isolation contract protects *production FeralEcho* from the experiment. It does not separately specify protection *between E5's own P/E/N arms* at the OS level — i.e., does P's construction process (which touches "family/arm-isolated acquisition") run in a genuinely separate OS-level sandbox from E's and N's, or only in logically-separated in-process state? The per-experiment profile line for E5 says "family/arm-isolated acquisition then read-only evaluation" — this describes a *logical* boundary, not necessarily an *OS-enforced* one the way I0–I4 require for the production boundary. Given this review's §4/§5 findings about how much rides on P and E genuinely not leaking into each other, **this deserves the same enforcement standard the production boundary already gets, not a lighter one.** MUST FIX BEFORE EXECUTION.

---

## 12. Durability analysis

The E5-D qualifier (fresh-process reload + ≥24h declared delay, no reteaching) is scoped correctly and conservatively: "Merely crossing a restart has no minimum calendar duration" and "This establishes durability only for that interval" are both stated plainly. The reconciliation correctly separates this from E8/accumulation ("Do not let E5 become E8 accidentally" is honored — E5-D tests one lesson's persistence, not multiple lessons' interaction).

**What reload proves and doesn't:** a fresh-process reload proves the *storage layer* survives a restart — it does **not** prove the *solver's application* of the reloaded procedure is unaffected by anything that changed in the interim (model residency state, cache warmth, subtle backend version drift over the delay window). The design's own isolation contract already requires pinning backend/model identity through the experiment (§16, I1), which — if actually honored across the reload gap — closes this. **Flagging as a dependency, not a new gap**: E5-D's validity is entirely conditional on the isolation contract's model/backend pinning actually surviving the declared delay, which is a real operational requirement (don't let Ollama, the OS, or the pinned model manifest change between T-teaching and T-delayed-test) that should be explicitly checked and logged, not assumed.

---

## 13. Falsification/result-interpretation matrix

| Result pattern | Strongest defensible claim |
|---|---|
| P > E and P > N (both meaningfully, all controls pass) | Pilot-scale directional signal consistent with bounded procedural transfer for this solver/family distribution; **sizes a confirmatory follow-up; does not itself confirm transfer** at n=4 families. |
| P > N but P ≈ E | Some acquired-memory benefit exists, but procedural *form* specifically shows no advantage over curated episodes — informative against the "procedures are special" hypothesis, not merely a weaker version of the main claim. |
| P > E but P ≈ N | The strongest warning sign in this matrix: P beats E without beating the no-memory baseline suggests E was constructed as an unfairly weak comparator (see §5's construction-asymmetry concern) rather than that P conveys real benefit. **Do not report as "partial transfer" — report as a likely comparator-fairness failure requiring redesign of E's construction before any further interpretation.** |
| P ≈ E ≈ N | No detectable acquisition effect at pilot scale — inconclusive at n=4, not evidence of absence; report as a null feasibility result. |
| E > P | Curated raw episodes outperform distilled procedures for this family/solver — a real, useful negative result about representation choice, independent of whether "learning" happened at all. |
| P improves related tasks but harms near matches | Evidence of an *unbounded* applicability policy (see §7) — do not describe as "learned an applicability condition" without the statistical power §7 says this pilot lacks. |
| P improves only duplicate-like tasks | Non-duplication controls (§6) failed to do their job; this is a design-validity failure, not a transfer failure — investigate the duplication-detection pipeline, not the procedure. |
| P works before restart but not after reload | Durability specifically failed; transfer within-session may still be real — report these as two separate findings, not one collapsed "transfer failed" statement. |
| P survives reload but not delayed testing | As above but for the delay interval specifically — check for backend/model drift over the delay window (§12) before attributing this to forgetting. |
| P succeeds only when failed-teaching families are removed | This is exactly the selection-bias failure mode §8 is built to prevent — if this pattern appears, it means the pre-registration/no-post-hoc-exclusion rule was violated, and the result should be discarded, not reinterpreted. |

---

## 14. Claim-laundering ladder

Using this review's own prior claims-ladder framework (`audits/2026-09-16_codex_capability_ceiling_adversarial_review.md`, Levels 0–6), applied specifically to what E5-mini can and cannot license at each transition:

| Transition | Additional evidence required before making it |
|---|---|
| "P outperformed E and N on 4 pilot families" (raw result) | None — this is the direct, literal finding, safe to state as-is with family-level detail. |
| → "Echo acquired a reusable procedure" | Requires the Z-arm control from §5 (rules out pure model-prior) and the arm-level condition-integrity manifest from §11 (rules out a labeled-but-wrong arm) — **neither exists yet**; this transition is currently unlicensed. |
| → "Echo learned" (bare, unqualified) | Requires L4 (procedural transfer) to be actually reached, not just attempted — i.e., requires the above plus the non-duplication and applicability controls actually clearing the bars in §6/§7, at confirmatory (not pilot) scale. **Not licensed by E5-mini alone under any outcome.** |
| → "Echo's competence increased" | Requires L5 (accumulation) — a claim this specific experiment structurally cannot make, since it tests one acquisition interval, not successive ones. **E5-mini can never license this transition, regardless of its result** — E8 is required, exactly as the reconciliation states. |
| → "Echo accumulates competence" (general, ongoing) | Requires L5S (sustained, multi-interval, interference-tested) — even further beyond E5-mini's scope. |
| → "Echo is autonomously self-improving" | Requires L6 (bounded autonomous weakness/intervention selection with no human choosing the next lesson) — categorically different from anything E5-mini or even E8-as-specified tests, since both are human-scheduled curricula. **No result from this experiment family should ever be described this way**, and this review flags this explicitly because the phrase "self-improving" is exactly the kind of load-bearing vocabulary this whole three-report chain exists to prevent from outrunning evidence. |

**The single most important discipline this report can add to the existing ladder:** a positive E5-mini pilot result licenses *investment in a properly-powered confirmatory E5*, not any wording above "pilot-scale directional signal." This should be stated explicitly in whatever writeup follows a successful pilot, in the same sentence as the result, not left implicit.

---

## 15. Confound register

| # | Confound | Mechanism | Design permits it? | MUST/SHOULD/FOLLOW-UP/UNNECESSARY |
|---|---|---|---|---|
| 1 | Model-prior leakage into P via procedure-generation reasoning | Generator synthesizes a procedure that reflects pretrained knowledge, cued but not sourced by teaching | YES | **MUST FIX BEFORE EXECUTION** — add Z (zero-teaching procedure) arm to primary analysis |
| 2 | P-construction gets an implicit extra validation/selection pass E doesn't | "Validated procedure" vs. plain "curated" episodes | UNRESOLVED from spec text | SHOULD ADD IF CHEAP — log construction cost symmetrically |
| 3 | E5 has no condition-integrity manifest / independent transport checker (unlike E3) | Arms differ by *evidence visibility*, not code path — same failure class as yesterday's real Condition-A bug, different mechanism | YES, structurally absent | **MUST FIX BEFORE EXECUTION** |
| 4 | Single-custodian dual authorship of teaching + withheld tasks | One family designer shapes both, risking a "family label leaks the method" pattern | YES | SHOULD ADD IF CHEAP — blind zero-context solver probe before the real run |
| 5 | Near-match/unrelated controls too thin at mini scale (1 each/family) | Cannot bound false-application rate with any real confidence at n=4 | YES, by explicit scaling-down from the 12+12 in repaired E5 | **MUST FIX BEFORE EXECUTION** — restore per-family count or explicitly disclaim applicability-condition claims |
| 6 | AST/control-flow duplication check can both over- and under-flag | Syntactic restructuring vs. semantic identity are not the same axis as "requires new reasoning" | YES, inherent to the method | SHOULD ADD IF CHEAP — supplement with blind-solver difficulty differential (§6) |
| 7 | E5's OS-level arm isolation (P vs E vs N) not held to the same enforcement standard as the production boundary | Isolation contract's strongest language (I0-I4) targets production, not inter-arm leakage | UNRESOLVED from spec text | **MUST FIX BEFORE EXECUTION** |
| 8 | G0's 24 cases don't explicitly name missing-attempt, UNKNOWN-conversion, or incomplete-run-as-clean | Enumerated list in reconciliation text covers ~9-10 named cases explicitly; "24" total is asserted, not fully listed | UNRESOLVED (may already be covered by unlisted cases) | **MUST FIX BEFORE EXECUTION** for the 3 identified as most consequential; SHOULD ADD for stale-artifact/incorrect-parent-ID |
| 9 | Post hoc family exclusion after seeing which families "worked" | Small-N pilot has near-zero robustness to selective reporting | Prevented in principle by §8's stated policy, not by an automated gate | **MUST FIX BEFORE IMPLEMENTATION** — make this a pre-registration/reporting rule, not just stated intent |
| 10 | Statistical over-claiming from n=4 clusters | Narrative pull toward "3 of 4 families showed transfer" reading as more meaningful than it is | Reconciliation text is already honest about this | SHOULD ADD IF CHEAP — enforce family-by-family reporting format, no pooled percentages, no CI/p-value language, as a template requirement |
| 11 | Backend/model drift across the E5-D reload/delay window | Isolation contract requires pinning but doesn't specify verification across the delay | UNRESOLVED | FOLLOW-UP ONLY — only matters if E5-D is actually run; log and check pinned identity at both ends |
| 12 | Compute/token-budget asymmetry between P and E | Explicitly and carefully handled already | NO — already closed | UNNECESSARY, no further action |
| 13 | Durability conflated with accumulation | Explicitly and carefully separated already | NO — already closed | UNNECESSARY |
| 14 | Failed-teaching families silently dropped from denominator | Explicitly retained by design | NO — already closed at the design-statement level (see #9 for the enforcement gap specifically) | Already addressed; #9 covers the residual enforcement risk |

---

## 16. Required changes, ranked, and minimal revised G0 → E5-mini specification

### MUST FIX BEFORE IMPLEMENTATION (blocks writing any code)
- Add a zero-teaching procedure arm **Z** to primary analysis (§5, confound #1) — cheapest and most important single addition.
- Restore near-match/unrelated control counts to something that can bound a false-application rate (§7, confound #5) — either scale back up toward the repaired-E5 12+12 even for a smaller family count, or explicitly and prominently disclaim any applicability-condition claim in the mini pilot's permitted wording.
- Pre-register the full 4-family list, teaching/withheld task set, and analysis plan before any generation begins; explicitly forbid post hoc family exclusion in the writeup template (§8/#9).
- State explicitly, in the experiment's own design doc, that G0 qualifies instrument honesty, not arm-construction fairness — these are different claims and must not be conflated (§4, causal-chain row 5).

### MUST FIX BEFORE EXECUTION (blocks running real generations, but design/code can be written first)
- Build an E5-specific condition-integrity manifest and independent checker, mirroring E3's (§11's confound #3) — verify per-arm what evidence was actually visible to each call, not just what was intended.
- Extend G0's planted-anomaly suite to explicitly cover: missing attempt, evaluator-UNKNOWN silently converted downstream, and incomplete-run-read-as-clean (§10, confound #8).
- Specify and qualify OS-level (not just logical) isolation between P/E/N arm construction processes, at the same enforcement standard as the production boundary (§11, confound #7).

### SHOULD ADD IF CHEAP
- Log construction cost (calls/tokens/iterations) symmetrically for P and E (§5/#2).
- Blind zero-context solver probe on withheld tasks before the real pilot, to catch family-label leakage (§6/#4).
- Supplement AST/structural duplication checks with an empirical difficulty-differential-under-blinding measure (§6/#6).
- Add G0 cases for stale artifact references and incorrect parent IDs (§10/#8 residual).

### STRONGER FOLLOW-UP ONLY (not required for E5-mini, worth doing for confirmatory E5)
- Verify pinned model/backend identity is unchanged across the E5-D reload/delay window, with logged evidence, not just an assumption (§12/#11).
- Cross-model replication (already correctly deferred by the reconciliation itself — this review agrees it's a portability question, not a prerequisite).

### UNNECESSARY
- Universal embedding-distance floor (the reconciliation already correctly rejects this — this review concurs).
- Monotonicity requirements across measurements (already correctly rejected).
- Any additional OS-hardening beyond what §16 of the reconciliation already specifies for the production boundary itself — that section is already appropriately rigorous.

---

## 17. Minimal revised G0 → E5-mini specification

**Arms:** N (no memory), Z (zero-teaching procedure, spec-only), E (curated episodes, matched budget), P (teaching-derived procedure, matched budget) — four arms, not three. Z is the added minimum-fair-counterfactual control from §5/§16.

**Families:** 4, pre-registered in full (list, teaching tasks, withheld tasks, near-match, unrelated) before any generation begins, with the family list and task text hashed and frozen prior to execution.

**Per-family controls:** restore near-match/unrelated counts to at least 3 each (a middle ground between the thin 1-each and the full-scale 12-each — enough to move off pure anecdote without ballooning the pilot's cost, itself a judgment call the experiment owner should confirm before building).

**Isolation:** OS-level enforcement between all four arms' construction and evaluation processes, to the same I0-I4 standard already specified for the production boundary; qualify this the same way G0 qualifies outcome recording, before trusting any result.

**G0:** existing 24-case suite plus the 3 MUST-FIX additions from §10 (missing attempt, UNKNOWN-conversion, incomplete-run-as-clean), with a condition-integrity manifest and independent checker for the P/E/N/Z arms specifically, built before the pilot runs — not retrofitted after a result looks interesting.

**Reporting:** family-by-family results only; no pooled percentage, confidence interval, or significance claim; explicit statement of what the result licenses (§14's ladder) in the same paragraph as the result itself.

---

## 18. Exact wording a positive result would license

*"In a 4-family pilot, using a frozen teaching-derived procedure (P), performance on genuinely withheld related tasks exceeded matched information-budget controls (a zero-teaching procedure Z, curated episodic evidence E, and no acquired memory N), under fixed solver/backend/isolation constraints, with the effect surviving a fresh-process reload. This is a pilot-scale directional signal, not a confirmed effect, and licenses sizing a properly-powered confirmatory E5 study — it does not establish reusable competence, accumulated learning, or any form of self-improvement."*

## 19. Exact wording a positive result would NOT license

"Echo learned [X]." "Echo's competence increased." "Echo accumulates knowledge from experience." "FeralEcho demonstrated procedural memory." "This proves teaching works." Any wording that drops the family-count, the pilot/non-confirmatory qualifier, or the Z-arm comparison (once added) from the same sentence as the claim.

## 20. GO / NO-GO recommendation for implementation

**GO on the design work described in §16-17. NO-GO on running real model generations until:** (a) the Z arm exists in the specification, (b) the condition-integrity manifest exists and has itself passed its own G0-style qualification, and (c) the family list is pre-registered and frozen. None of these three requires new infrastructure beyond what's already planned for G0/E3 — they are extensions of work already scoped elsewhere in the reconciliation report, applied to the one experiment that was, until this review, missing them.

## 21. Unresolved unknowns

- Whether the unnamed remainder of G0's "24 cases" already covers the gaps flagged in §10 — genuinely unknown from the reviewed text, not assumed absent. Should be resolved by reading the actual (not-yet-written) G0 implementation spec once it exists, not by further document review.
- Whether the pilot families, once actually chosen, will be recognizable-enough CS patterns that base-model prior (confound #1) dominates in practice, or obscure enough that N performs near-floor — this is an empirical question the Z arm itself will help answer, not something resolvable from design review alone.
- Whether OS-level isolation between P/E/N/Z arms (§11) is achievable with the same rigor the reconciliation already achieved for the production boundary, given implementation effort has not yet been spent on it — flagged as a real engineering question, not assumed either way.
- Whether "24 deterministic qualification cases" was ever intended to be a complete list or is itself a placeholder pending implementation — this review cannot distinguish these from the reconciliation text alone.

## 22. Evidence/provenance appendix

- **OBSERVED(source):** `audits/2026-09-16_capability_growth_reconciliation.md` read in full (987 lines); `claude_relay/relay.py:35,110,198-201,357`; `hub/notes.py:203-217`; `hub/check_hub.py:52`; `scripts/task_type_behavioral_experiment.py:207-217`.
- **OBSERVED(artifact):** `git rev-parse HEAD` (both open/close), `git status --short --untracked-files=all` (177 entries, opening and closing), `ps aux` process identities (7644, 7636, 13534, unchanged across the mission).
- **SUPPORTED:** the reconciliation report's D15 and D6 disagreement-matrix rows, independently re-verified against current source rather than trusted from the report's own text.
- **INFERRED:** the model-prior-leakage confound (§5/§15 #1) and the arm-isolation-enforcement gap (§11/§15 #7) are inferred from the *absence* of a described control/mechanism in the reconciliation's own text, not from any positive evidence that leakage has occurred — these are design gaps, not observed failures.
- **PROPOSED:** all of §16-17 (the Z arm, the E5 condition-integrity manifest, the additional G0 cases, the restored control counts) — none of these have been built, tested, or run; they are this review's recommended specification, subject to the same scrutiny this review applied to the reconciliation's own proposals.
- **UNRESOLVED:** see §21 in full.

---

**Final integrity confirmation:** opening HEAD `2fba42644c82b9f7096276f4dd338d615cf1bcce`, closing HEAD `2fba42644c82b9f7096276f4dd338d615cf1bcce` — unchanged. The only path created or modified by this mission is this report. No production code, configuration, experiment code, model, memory/index state, or Git state was touched. No running process was signaled, stopped, restarted, or otherwise disturbed. No relay or hub message was sent. No scratch artifact was created.
