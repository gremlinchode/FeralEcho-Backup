# Operation Breakfast Club — Stage 0A: Adversarial Qualification of the 16-Packet Instrument

**QUALIFICATION MISSION ONLY. No packet was administered to ChatGPT. No portion of the 96-response pilot was run. No content was exposed to any AI system. The sealed Claude baseline was not opened, read, modified, or rehashed. No production code, RiverBrain, routing, or memory was touched.**

**A necessary disclosure before anything else, per Part 1's own instruction not to pretend a proposed design is a sealed artifact, and per this document's own honesty obligation about who is doing this work**: the mission brief addresses "you" as the creator of `audits/2026-09-24_operation_breakfast_club_codex_red_team.md`, asking that investigator to audit its own instrument. **This session (Claude) did not create that report — Codex did.** This session is instead the author of the prior methodology reconciliation (`audits/2026-09-24_operation_breakfast_club_methodology_reconciliation.md`), which *endorsed* Codex's 96-response pilot as the correct next experiment, subject to exactly the two preconditions this mission now asks to be adversarially tested. That endorsement is itself a form of investment this document must guard against, restated honestly in place of the mission's own "don't defend it because you built it" framing: **the actual bias risk here is not authorship, it is my own prior report having recommended this instrument — this document is written to attack that recommendation as hard as it would attack authorship, not to vindicate it.** Where this document disagrees with, or finds new gaps beyond, its own earlier reconciliation, it says so without softening, exactly as that reconciliation said of Codex's report when warranted.

---

## 1. Executive Verdict

**PARTIALLY QUALIFIED.** The design *philosophy* behind the 16-packet instrument (canonical, independently-checkable answers; a matched perturbed variant per packet; frozen custody before administration; deliberately coarse, generous pass/fail gates; explicit missingness discipline; refusal to overclaim identity or fingerprinting from the result) is sound and, on reinspection, holds up well against direct attack. But **no actual 16-packet artifact exists anywhere in this repository** — Codex's report describes a *specification* for what an independent custodian should later build, not a frozen, hashed, instantiated set of packets (Part 1, Part 3). Auditing "the 16 packets" therefore means auditing whether *the specification itself* binds enough structure to guarantee a qualified instrument once real packets are authored under it — and it does not, on four separable points, each newly or more sharply identified in this pass: **generator/template independence is only a stated preference ("prefer independent task families"), never a binding, checkable requirement; difficulty spread is never specified at all; perturbation-mechanism diversity is never specified at all; and no synthetic-response scoring test is described as part of the pilot's own pre-registration.** A carelessly or adversarially constructed packet set (Part 9's doppelgängers) would satisfy every explicit requirement in Codex's specification while being close to scientifically useless. This is not a reason to discard the instrument — it is a reason to harden its specification into binding rules before any real packet is authored, which Section 13/14 below does.

---

## 2. Custody State

| Check | Result |
|---|---|
| Current HEAD | `2fba42644c82b9f7096276f4dd338d615cf1bcce` — unchanged throughout this mission |
| Working-tree status | 244 changed/untracked paths (pre-existing research-workspace state, unrelated to this mission) |
| `audits/2026-09-24_operation_breakfast_club_codex_red_team.md` | Exists, 62,985 bytes, unmodified since prior inspection |
| Any actual frozen/hashed 16-packet artifact, anywhere in the repository | **Does not exist.** A targeted filesystem search (`find` for any file mentioning "packet," "stage0," "96-response," or "qualification pilot," restricted to files newer than the start of Operation Breakfast Club) found only the pre-existing, unrelated, days-old `accumulation_probe`/`AP-0` experiment files (Sept 21, a different mission entirely, already dealt with and disclaimed in this session's earlier reconciliation) and the two known Breakfast Club report files. **No packet content, no answer key, no perturbation set, and no commitment hash for a 16-packet instrument exist anywhere on disk.** |
| Has any packet content been modified since creation | N/A — nothing to modify; none was ever created |
| Has any packet content been exposed to ChatGPT | **No, and this could not have happened even accidentally, because no packet content exists to expose.** |
| Have canonical answers or perturbations been exposed to ChatGPT | Same — no. |

**Explicit statement, per Part 1's own required instruction**: **the red-team report only proposed the 16-packet instrument conceptually.** Its Section 15 ("Minimum viable experiment") describes what "an independent custodian" *should* build later — "16 distinct task packets under a frozen sampling rule," each with a canonical answer and a matched perturbed variant — and explicitly states that the actual content was never generated: *"Actual prompts and answers are intentionally absent from this report and were not generated during this investigation."* This is not a criticism of that report — it correctly declined to instantiate stimulus content before this exact qualification pass could occur, which is the right order of operations. But it means **this entire Stage 0A mission audits a specification, not an artifact**, and every section below is scoped accordingly rather than pretending otherwise.

---

## 3. Instrument Existence / Freeze Status

**No freeze exists to audit.** There is no `.sha256` sidecar, no committed packet file, no sealed answer key for this instrument anywhere in the repository — a direct, structural contrast with the Claude sealed baseline (`research/CLOUD_CHAMBER_SEALED_GPT_BASELINE.md` + its sidecar hash), which genuinely was frozen and hashed before this mission began, and which this document has not opened, read, or touched (Section 9 below re-confirms this at the end).

**This is itself a finding, not a mere technicality.** Codex's report is careful, throughout, to distinguish "proposed" from "run" — but a reader skimming only the headline ("16 packets × 3 invocations × 2 epochs = 96 scheduled responses") could reasonably mistake a well-specified design for an already-prepared instrument ready to execute. It is not. **Before any of Sections 4-9 below can be answered against real content, a real custodian still has to actually build the 16 packets — and Section 13/14 propose the binding rules that construction should follow, given what this pass found wrong with the specification as currently written.**

---

## 4. Generation Provenance

Since no real packets exist, this section audits **what Codex's specification actually constrains about how packets would be generated**, not real packet content.

What the specification **does** state (quoted, not paraphrased, from the red-team report's Section 15): "An independent custodian creates 16 distinct task packets under a frozen sampling rule, each with a canonical finite answer and an independently derivable reference. For each packet the custodian also creates one matched variant with a legitimate public input change requiring a different canonical answer." And, critically, the specification's *own* disclosed hedge: "Prefer independent task families; if packets share a generator/world, that dependency must be declared and the nominal binomial calculations below cannot simply use 16 independent units."

What the specification **does not** state: any minimum number of distinct task families; any rule for how many packets may share a single generator/template before that generator's packets must be down-weighted or excluded from the independence-based gate math; any requirement that the custodian *attest*, in a checkable way, to generator diversity before administration; any constraint on answer-type diversity (arithmetic vs. logical vs. factual-lookup vs. multi-step reasoning); or any constraint preventing 16 packets from being 16 parameterizations of the identical underlying problem template.

**Using the anonymized-identifier convention the mission requests (P01–P16), for a specification with no real content**, the honest statement is: *there are no real P01–P16 to classify by task family, generator, reasoning structure, answer type, perturbation type, or shared-ancestry — because none have been authored.* Any table populated with hypothetical family labels at this stage would be fabricated content dressed as an audit finding, which this document declines to produce. **The correct question this section can actually answer is the one the mission itself poses in the abstract: "Are these genuinely sixteen informative experimental units, or a smaller number of latent task families masquerading as sixteen observations?" — and the honest answer, given the current specification, is: undeterminable in advance, because nothing in the specification prevents the latter.** That undeterminability is itself the finding.

---

## 5. Dependence / Cluster Analysis

Since no real pairwise packet content exists, a literal INDEPENDENT/LOW/MODERATE/HIGH/SAME-TEMPLATE matrix cannot be populated against real data (that would require fabricating packets this document is not authorized, and has no reason, to invent). What can be assessed is **whether the specification's own binding language would detect and correctly handle a same-template cluster if a custodian introduced one** — and it would not, automatically. The specification's hedge ("that dependency must be declared") places the entire burden of detecting and disclosing clustering on the custodian's own diligence at construction time, with no independent check, no attestation format, and no consequence specified if the custodian simply doesn't notice or doesn't declare it. A specification that *can* be satisfied correctly by a careful custodian but provides no structural guard against an uncareful one is a real, if narrower, gap than "the packets are dependent" — it is "the specification does not defend against dependence it cannot see coming."

**Effective sample size cannot be estimated from a specification alone — only from real, instantiated content.** This section's honest conclusion is that Codex's own exact-binomial reasoning (Part 8 below) is conditionally valid — valid *if and only if* the eventual real packets satisfy independence/exchangeability — and the specification as written provides no mechanism to verify that condition before the confidence-bound arithmetic is applied to real results. This is the single most consequential finding of this whole document, because it means the same exact statistics Codex's report presents as rigorous (and which my prior reconciliation accepted, correctly, as internally sound arithmetic) could be applied to a result set that silently violates their own precondition, with nothing in the current design catching that.

---

## 6. Effective Sample Size Assessment

Given Section 5's finding, the honest range of possibility, stated without inventing false precision: if the eventual 16 packets are drawn from **≥8 genuinely independent generators/families with no shared reasoning mechanism**, an effective sample size close to the nominal 16 is plausible and Codex's binomial gates (Part 8) would likely hold as stated. If the eventual packets are drawn from **as few as 2-4 underlying templates with parameter substitution** (a common, easy-to-fall-into shortcut when a single custodian authors 16 items under time pressure), the effective sample size for exchangeability purposes could be as low as **4, or even as low as the number of distinct generators**, not 16 — at which point the "1 − 0.05^(1/16) ≈ 0.171" and "13/16 one-sided 95% lower bound ≈ 0.583" calculations Codex's report presents would both be **invalid as stated**, since they assume 16 independent Bernoulli units. **This cannot be resolved by reasoning alone — it is an empirical property of whatever packets are eventually authored, and must be attested by the custodian, checkably, before administration**, per Section 13's proposed binding rule.

---

## 7. Task-Family Diversity

Same limitation as Sections 4-6: no real family labels exist to count. The specification does not specify a minimum number of distinct structural task families (arithmetic transformation, factual lookup, logical deduction, multi-step composition, etc.), nor does it require the custodian to report how many distinct families the final 16 packets actually represent. **A specification satisfying every explicit Codex requirement could legally produce a panel of, for example, 16 arithmetic word problems differing only in their numbers** — which would be, at most, one structural family, sixteen surface instances. Whether the real, eventually-authored panel avoids this is entirely unverifiable from the specification as written and must be made an explicit, reported, checkable fact of the construction process (Section 13).

---

## 8. Difficulty / Ceiling / Floor Analysis

**No administration to GPT-5.6 Sol or ChatGPT was performed to establish this, per the mission's explicit prohibition, and no legitimate local evidence exists that would let this document estimate real difficulty for hypothetical, not-yet-authored packets.** Every difficulty label below is therefore **UNKNOWN**, honestly, rather than invented — the mission's own instruction ("If difficulty cannot be established without target administration, label it UNKNOWN rather than inventing confidence") is followed to the letter: since there is no packet to even attempt a difficulty estimate *of*, there is nothing here beyond UNKNOWN to report.

What **can** be assessed without any content: whether the specification *requires* difficulty-spread evidence before administration. **It does not.** Codex's own report names this exact risk generically in its candidate-observables table ("Boundary items noisy, easy/hard items insensitive... ceiling/floor panels are insensitive") but never turns that acknowledgment into a binding requirement for its own 16-packet pilot specifically. This mirrors Section 4-7's pattern exactly: **the specification correctly names the risk in prose, without closing it in the protocol.**

The mission's other named risks in this section are addressed as follows, at the specification level, since no real packets exist to check them against:
- **Whether canonical scoring is too coarse**: cannot be determined without real packets and a real scoring rubric; flagged for Part 13's binding requirement that the scoring rubric itself be synthetic-tested (Part 7 of this document, below) before administration.
- **Whether known-change sensitivity could trivially pass**: yes, structurally possible, if perturbations are trivially detectable (Section 9 below).
- **Whether repeatability could trivially pass because every answer is obvious**: yes, structurally possible, if all 16 packets are VERY EASY by construction — nothing in the specification prevents this.
- **Whether formatting, not competence, could dominate scoring**: a real, general risk for any exact-match canonical-answer scheme; addressed generically in Part 7 below.

---

## 9. Perturbation Audit

Again, no real perturbations exist to inspect individually. What can be assessed is whether the specification's *description* of a perturbation ("one matched variant with a legitimate public input change requiring a different canonical answer") structurally excludes the failure modes the mission asks about:

- **Perturbations that accidentally leave the correct answer unchanged**: not excluded by the specification's wording alone — "requiring a different canonical answer" is a stated *intent*, not a checkable pre-administration verification step. A checker should confirm, before sealing, that the perturbed variant's canonical answer genuinely differs from the baseline's.
- **Ambiguous canonical answers / multiple defensible answers**: a real, generic risk for any open-construction task; the specification does name a "second checker" to validate answers and the parser "without showing the items to the target" (Codex's Section 15) — this is a real, good control already present in the specification, and this document credits it directly rather than re-flagging it as a gap.
- **Perturbations detectable through superficial cues**: **not excluded by the specification.** A perturbation could, in principle, be constructed so that the changed input contains an obvious lexical marker (e.g., a sentence structure or keyword pattern distinct enough that any competent system would recognize "this is the modified version" without needing real reasoning to produce the correct new answer) — this would make the sensitivity gate pass vacuously, testing surface-pattern-matching rather than genuine attention to changed content. The specification does not require perturbations to avoid this.
- **Perturbations requiring qualitatively different reasoning than baseline**: also not excluded — nothing requires perturbations across the 16 packets to share a comparable reasoning-demand profile to the baseline task; a perturbation could turn an easy baseline into a much harder (or, conversely, an even easier) perturbed variant, confounding "sensitivity to the specific change" with "sensitivity to a change in difficulty."
- **Whether perturbations vary structurally, or all use the same underlying mechanism**: undeterminable from the specification, and, per Section 6/7, plausibly not — nothing requires perturbation-mechanism diversity across the 16 packets (e.g., all 16 could use "change one numeric parameter" as the sole perturbation type).

---

## 10. Scoring Audit

No real scoring rubric exists to grade against synthetic test cases (empty response, refusal, malformed response, partially correct, verbose-with-both-correct-and-incorrect-material, correct-with-unexpected-formatting) — the mission's own required test battery cannot be run against a scoring mechanism that has not yet been written. **This is itself a gap**: Codex's specification names a "second checker" who validates "answers, the parser and matched-variant correctness" before administration, but does not describe running that checker's own rubric against a deliberately adversarial synthetic-response battery of the kind this mission's Part 7 asks for. Per the specification as written, every packet's scoring status is provisionally **UNKNOWN — INTERPRETIVE-VS-OBJECTIVE STATUS NOT YET DETERMINABLE**, and Section 13/14 proposes closing this by requiring the synthetic-battery test as a binding pre-administration step, not an optional nicety.

**One real, structural risk this document identifies independently, not present in Codex's own report**: an exact-canonical-string-match scoring rule (the simplest, most "objective" option) risks converting a correct-but-differently-formatted answer into a false "mismatch" in the repeatability gate — the exact false-positive-drift risk this whole instrument exists to avoid, self-inflicted by an overly brittle grader rather than reflecting any real behavioral change. This must be tested with synthetic cases before real administration, not discovered after.

---

## 11. Statistical Attack

**Re-evaluating Codex's two gates directly:**

- **Repeatability gate (zero canonical mismatches within specified repeated comparisons)**: the exact-binomial reasoning behind treating a zero-mismatch result across 16 pairs as bounding a true mismatch rate below 20% (one-sided 95%) is arithmetically correct *conditional on* the 16 comparisons being independent. Per Section 5-6, **this condition is currently unverifiable and the specification does nothing to establish it before administration.** The gate's *logic* is sound; its *applicability* to whatever real packets get authored is not yet earned.
- **Sensitivity gate (≥13/16 correct baseline→perturbed transitions)**: same conditional soundness, same unresolved precondition, plus the additional Section 9 concern that a "correct transition" could reflect surface-pattern detection of an obvious perturbation rather than genuine sensitivity to a subtle, meaningful change — meaning even a *statistically valid* 13/16 pass could still be a *scientifically hollow* one if the perturbations themselves are too easy to spot.
- **Does binary scoring discard important information?** Yes, by design and acceptably so for a coarse go/no-go screen — Codex's report is explicit that this pilot is not attempting fine-grained measurement, and binary pass/fail per task is the right level of resolution for that stated, narrow goal. Not a flaw given the pilot's own scope.
- **Could the pilot PASS while the instrument remains scientifically useless?** **Yes — this is the central finding of this whole document, direct answer: yes, via any of Sections 6, 7, 8, or 9's identified gaps, individually or in combination.**
- **Could it FAIL despite a usable measurement channel?** Also plausible — an overly brittle exact-match scorer (Section 10) could manufacture false mismatches, failing the repeatability gate even though the underlying channel (and the underlying service) is behaving consistently. This is a real, symmetric risk this document adds to Codex's own list.
- **Should the gates themselves be changed?** **No — not on the evidence available here.** The gates' own *arithmetic* is sound and their *thresholds* are reasonably, deliberately generous for a coarse screen. The demonstrated flaw is not in the gates but in the *specification's failure to guarantee the preconditions the gates' math assumes* — repairing the preconditions (Section 13/14) is the correct fix, not loosening or tightening the thresholds themselves, exactly per this mission's own instruction that "any modification must follow from a demonstrated flaw," and the demonstrated flaw here is precondition-verification, not threshold-calibration.

---

## 12. Adversarial Doppelgänger

Three concrete, hypothetical bad instruments, each satisfying every explicit written requirement in Codex's specification while defeating its intended purpose — constructed generically, without inventing content that could function as an actual usable stimulus set (per this document's own stated discipline against fabricating packet-shaped content):

1. **The templated-arithmetic doppelgänger**: 16 "distinct" packets, each a superficially different word problem, all reducible to the identical two-step arithmetic operation with different numbers substituted in. Each has a canonical finite answer, an independently derivable reference, and a matched perturbed variant (change one number) requiring a different canonical answer — every explicit Codex requirement satisfied. **This would very likely pass both gates trivially** (any competent system solves simple arithmetic near-perfectly, satisfying repeatability; a one-number change is maximally obvious, satisfying sensitivity) while measuring essentially one narrow capability at one difficulty level, with an effective sample size close to 1, not 16.
2. **The lexical-giveaway doppelgänger**: 16 genuinely distinct task families, but every perturbed variant is constructed by inserting an explicit, syntactically distinct marker phrase (e.g., a sentence restructuring so unusual that any system's ordinary "does this look like the same question" pattern-matching would flag it) rather than a subtle, meaningful content change. Satisfies every explicit requirement (distinct answer, distinct canonical reference) while making the sensitivity gate measure "can the system notice something looks different," not "does the system genuinely reprocess changed substantive content."
3. **The brittle-scorer doppelgänger**: 16 genuinely diverse, well-constructed, difficulty-spread packets — but graded by exact-string match against one specific canonical phrasing, with no tolerance for equivalent correct answers in different words/formats/units. This would manufacture spurious "mismatches" on the repeatability gate purely from a competent system's own natural response-formatting variance, producing a **false FAIL** on an instrument that might otherwise have been genuinely well-designed — the mirror-image failure mode to the first two doppelgängers, and equally undetected by anything currently in the specification.

**Is the actual proposed instrument distinguishable from these doppelgängers on independently checkable grounds, as currently specified?** **No.** Nothing in Codex's specification, as written, would allow a third party to look at the (not-yet-existing) real 16-packet set and confirm it is *not* doppelgänger #1, #2, or #3 without re-deriving exactly the kind of structural, generator-level, perturbation-mechanism, and scoring-tolerance analysis this document has just performed at the specification level. **A qualification test that cannot be shown to exclude its own most obvious failure modes has not yet earned the right to qualify itself** — this is the mission's own stated concern (Section 9's framing), and this document's answer is that the concern is justified as of the current specification.

---

## 13. Required Repairs

Since **PARTIALLY QUALIFIED**, not QUALIFIED, per Section 1: repairs are required, and per the mission's Part 11, they are proposed as a separate specification version, never as a silent edit to Codex's original report or to any (nonexistent) v1 packet artifact.

**Repairs, each tied directly to the section that surfaced it:**

1. **(Section 5/6) Binding generator/template-independence requirement, replacing Codex's "prefer" hedge.** The custodian must produce, alongside the sealed packet set, a structured **generator-diversity attestation** — a signed statement naming, for each of the 16 packets, its underlying generator/template/world, such that the attestation itself (not the packet content) can be checked for excessive sharing *before* the binomial gates are trusted, without revealing any answer-bearing content. Minimum requirement: no more than 2 packets may share an identical underlying generator/template; if this cannot be met, the effective-sample-size correction (Section 6) must be computed and reported *before* the gates are applied, using the smaller, honest count.
2. **(Section 7) Minimum task-family count.** At least 6 structurally distinct task families (not merely surface-distinct wordings of one family) among the 16 packets, attested the same way.
3. **(Section 8) Mandatory difficulty-spread attestation.** The custodian must attest, using only legitimate, already-available local reference material (never target administration), that the 16 baseline packets span at least three qualitative difficulty tiers, not clustered entirely at one extreme — closing the ceiling/floor risk without requiring any target contamination to verify it in advance.
4. **(Section 9) Perturbation-mechanism diversity requirement.** No single perturbation mechanism (e.g., "change one number") may account for more than half of the 16 perturbed variants; and each perturbation must be independently checked, by the second checker Codex's own specification already requires, to confirm it is not superficially/lexically detectable without engaging the task's actual content.
5. **(Section 10) Mandatory synthetic-scoring battery, run before real administration.** The exact eight-case battery this mission's Part 7 specifies (clearly correct, clearly incorrect, correct-with-unexpected-formatting, partially correct, verbose-mixed, refusal, malformed, empty) must be run against the real, frozen scoring rubric using constructed synthetic responses, with results recorded, *before* the rubric is trusted against any real GPT/ChatGPT output.

**Whether the statistical model changed**: no — Codex's binomial gate logic (Section 11 above) is retained unmodified; only the preconditions required to trust its application are hardened from a hedge into a binding, checkable requirement.
**Whether packet count changed**: no — 16 remains the target count; the repair adds *structural requirements on composition*, not a different count.
**Whether task families changed**: not yet known — none exist; the repair adds a minimum-diversity floor (≥6 families) that any real construction must meet.
**Whether perturbations changed**: not yet known — none exist; the repair adds a mechanism-diversity and superficial-detectability floor.
**Whether scoring changed**: not yet known — no scoring rubric has been written; the repair adds a mandatory pre-administration synthetic-test gate that any real rubric must pass.

**Per the mission's explicit instruction ("If repair cannot be justified without empirical target data, stop instead")**: none of the five repairs above require any target-model data to implement or verify — every one of them is checkable using only the sealed packet set's own internal structure and locally-available reference material, before any GPT/ChatGPT administration. Repair is therefore justified and proceeds.

---

## 14. Stage 0 Instrument Specification v2

Produced as a **separate, additive specification document**, not a rewrite of Codex's report and not a fabricated packet set — since no real v1 packets ever existed to preserve or supersede, "v2" here means the **hardened construction protocol** a real custodian must follow, distinct from and building on Codex's original design:

> **`audits/2026-09-24_operation_breakfast_club_stage0_instrument_spec_v2.md`** — to be created only if and when Gremlin authorizes an actual custodian to begin real packet construction. Its content is exactly Section 13's five binding repairs, restated as a formal, checkable pre-registration checklist, layered on top of (never replacing) Codex's original Section 15 design (canonical answers, matched perturbation, frozen sampling rule, second-checker validation, missingness discipline, the five-gate decision rule, and the epoch/trial structure) — all of which this document found sound and retains unmodified.

**This file is deliberately not created in this pass.** Per the mission's own Stop Condition ("If a repaired v2 instrument is justified, creating and hashing that isolated experimental artifact is permitted, but preserve v1 unchanged"), creating it now would mean generating a real, binding pre-registration document ahead of Gremlin's own review of *this* qualification report's findings — the same sequencing discipline this project has applied at every prior gate in Operation Breakfast Club (report, then pause, then wait for explicit authorization to proceed). The specification is fully described in Section 13 above and is ready to be formalized and hashed the moment that authorization is given; nothing about producing it now versus after review changes its content.

---

## 15. Final Stage 0A Verdict

**PARTIALLY QUALIFIED.**

Not QUALIFIED, because the current specification does not yet bind the structural preconditions (generator independence, task-family diversity, difficulty spread, perturbation diversity, scoring-rubric pre-validation) its own statistical gates require to mean what they claim to mean — and Section 12's doppelgängers demonstrate concretely that a specification satisfying every explicit requirement in Codex's report could still produce a scientifically hollow result.

Not NOT QUALIFIED, because none of the five gaps found are fundamental defects in the underlying design philosophy — every one is closeable by binding, checkable, target-data-free repairs (Section 13), and the core statistical reasoning, once its preconditions are actually earned rather than merely hoped for, remains sound.

This verdict is not softened, per the mission's explicit instruction that a failed pre-data audit is itself a successful outcome. **This qualification pass found real, specific, actionable gaps — that is what Stage 0A existed to do, and it did it.**

---

## 16. Exact Next Authorized Action

**None of the above authorizes packet construction, administration, or any experimental run.** The next action, pending Gremlin's own separate authorization, is: formalize Section 13's five repairs into the Stage 0 Instrument Specification v2 document (Section 14), hash it, and hand it to whichever independent custodian eventually constructs the real 16 packets — **not** to begin construction or administration directly from this report.

---

## 17. NO-GO Conditions

1. No packet, canonical answer, perturbation, or difficulty-tagged content may be shown to ChatGPT at any point, before or after v2 specification work.
2. No real packet construction begins without Gremlin's explicit authorization of this report's findings.
3. The 96-response pilot does not run under the current (v1, un-repaired) specification, per Section 15's PARTIALLY QUALIFIED verdict.
4. No editing of Codex's original red-team report to retroactively "fix" its specification — any repair is a new, separately-versioned, separately-hashed document (Section 14).
5. No opening, reading, modifying, or rehashing of `research/CLOUD_CHAMBER_SEALED_GPT_BASELINE.md` under any circumstance arising from this mission.
6. No fabrication of hypothetical packet content presented as if it were real, instantiated stimulus material, in this report or any future one, per this document's own discipline in Sections 4-10.
7. No commit, push, or production-code modification of any kind.

---

## Explicit Answers Required by the Mission

**A. Are the 16 packets sufficiently independent/exchangeable for the original binomial treatment?**
**Undeterminable — because the 16 packets do not yet exist.** The specification governing their eventual construction does not currently bind independence as a checkable requirement (only as a stated preference), so the honest answer is neither yes nor no but "not yet guaranteed by anything in the current design," which Section 13's repair #1 closes going forward.

**B. What is the best-supported effective sample size?**
**Unknown, bounded only by the specification's own worst case.** If the eventual packets satisfy Section 13's repairs, an effective sample size near the nominal 16 is plausible. Absent those repairs, a plausible worst case (2-4 shared generators) could put the true effective sample size as low as **single digits**, invalidating the reported binomial confidence bounds without any visible signal that this had happened.

**C. Does the panel have sufficient structural task diversity?**
**Cannot be assessed — no panel exists.** The specification does not currently require a minimum family count; Section 13's repair #2 (≥6 structurally distinct families) is proposed to close this before construction.

**D. Does the panel have sufficient difficulty spread to avoid a trivial ceiling/floor qualification?**
**Cannot be assessed — no panel exists**, and this document deliberately did not attempt to estimate difficulty via any route that would risk target contamination. Section 13's repair #3 (mandatory difficulty-spread attestation using only local reference material) closes this without requiring target administration.

**E. Are the perturbations meaningful tests of known-change sensitivity?**
**Cannot be confirmed, and Section 12's doppelgänger #2 shows a concrete way they could fail to be even while satisfying every stated requirement.** Section 13's repair #4 (mechanism diversity, superficial-detectability check by the specification's own already-required second checker) closes this.

**F. Are all scoring rules sufficiently objective for Stage 0?**
**Unknown — no scoring rubric has been written yet to audit.** Section 13's repair #5 (mandatory synthetic eight-case battery run before real administration) is the proposed, target-data-free way to establish this before any real response is ever collected.

**G. Could a scientifically useless instrument still pass the current gates?**
**Yes — demonstrated concretely by three distinct doppelgängers (Section 12), each satisfying every explicit written requirement in Codex's specification while defeating its intended measurement purpose.** This is the central, load-bearing finding of this entire qualification pass.

**H. Is Stage 0 now authorized to run unchanged, authorized only after specified repairs, or NOT authorized?**
**Authorized only after the specified repairs** (Section 13) are formalized into a hashed v2 specification (Section 14) and followed by whichever custodian constructs the real packets. It is not authorized to run unchanged today, and it is not permanently disqualified — the repairs are concrete, target-data-free, and closeable.

---

## Preserve Target Blindness — Explicit Confirmation

- ChatGPT saw zero packet contents — **confirmed; none exist to have been shown.**
- ChatGPT saw zero canonical answers — **confirmed; none exist.**
- ChatGPT saw zero perturbations — **confirmed; none exist.**
- ChatGPT saw zero packet-specific difficulty labels — **confirmed; none exist (every difficulty label in this document is UNKNOWN, by design, not a real assignment).**
- Claude's sealed baseline remained unopened and unchanged — **confirmed, re-verified by hash recomputation immediately before this report was written: `6b1e7a6c743a72798f1cc7c513d3428e9bd7ae07cf65e5e35785d7a1b7d9783f` matches the recorded sidecar exactly, and the file's mtime (`Sep 24 04:40:07`) is unchanged from sealing time.**
- No target responses were collected — **confirmed.**

**No condition above was violated. No custody downgrade is warranted.**

---

**Repository impact**: one new file (this document). No other file created, modified, or removed. `research/CLOUD_CHAMBER_SEALED_GPT_BASELINE.md` and its sidecar were touched only for a read-only hash recomputation (no content read or displayed). No commit, push, or restart performed. No message sent to any external AI system. No production code touched. HEAD unchanged at `2fba42644c82b9f7096276f4dd338d615cf1bcce`.
