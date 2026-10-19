# `self_model_claims.py` — Adversarial Learning-Claim Audit

Date: 2026-09-23. Investigator: Claude M5. Method: read-only, adversarial. This mission does not begin from the assumption that `self_model_claims.py` learns; its job is to try to falsify that claim. Motivated by the 2026-09-23 second-pass research archaeology, which recovered but explicitly did not independently verify an earlier adversarial-review characterization of `self_model_claims.py` as possibly "architecturally comparable or superior to RiverBrain" with "a documented live-reproduction case." That characterization is treated here as a hypothesis requiring independent verification, not a fact.

No production code, experiment code, configuration, memory/state artifact, prompt, test, report, Git state, or running process was modified. No FeralEcho module was imported. The one read against `memory/self_model_claims.jsonl` performed for verification used a bare `json.loads()` loop over the raw text in a fresh, isolated `python3 -I -B` subprocess — no `app.*` import, no deserialization of any pickle, no singleton instantiation, no background thread, no write.

**Opening HEAD:** `2fba42644c82b9f7096276f4dd338d615cf1bcce`. **Closing HEAD:** `2fba42644c82b9f7096276f4dd338d615cf1bcce` — unchanged. **Working-tree delta:** a `git status --porcelain` snapshot (229 entries) was captured before this mission's first read and diffed against the same command at report-writing time; the only difference is this report's own new, untracked path. Full accounting in §21.

---

## 1. Executive verdict

**PERSISTENT STATE, with a narrow, real BEHAVIORALLY CONSEQUENTIAL STATE component confined to prompt text — not EXPERIENCE-DEPENDENT ADAPTATION, and nowhere near PERSISTENT ACQUIRED LEARNING.**

`self_model_claims.py` is exactly what its own module docstring says it is: "a pure, append-only observation sink." It genuinely persists across restarts (OBSERVED, this mission, and RETRIEVED corroboration from a prior investigation's real subprocess-restart-adjacent evidence — see §9). It genuinely feeds real production system-prompt text through a real, reachable consumer (OBSERVED, this mission — see §5, §10). Its evaluator is genuinely independent of the text it evaluates, in the specific and narrow sense that matters here: it is a deterministic rule engine and a freshly-re-read telemetry file, never an LLM judging its own or another LLM's output (OBSERVED, this mission — see §7).

But every one of the chain's harder links fails or is unsupported: the mechanism has **zero** downstream consumer that is anything other than a rendered string appended to a system prompt (OBSERVED — no RiverBrain call, no routing branch, no retry/council-composition effect, confirmed by direct trace of every real call site); its entire empirical history (23 real records) contains **zero** `verified: true` entries — every single real observation is a record of a *false* claim, never a demonstrated true one (OBSERVED, direct read of the live ledger, this mission); one real, well-documented behavioral effect exists (a misread ledger line caused a generation-time misstatement) and it was discovered as **a bug in the mechanism's own rendering logic**, not as a designed test of learning, transfer, or improvement (RETRIEVED, primary source traced and read in full — see §6); and a structural defect independently rediscovered by this mission (4 of 23 real records, 17.4%, are permanently unreadable by the mechanism's own single consumer, because they were written under a fallback subject name the reader never queries) shows the mechanism is not even reliably completing its own narrow "record and re-surface" loop, let alone anything resembling learning.

The earlier characterization this mission was asked to test ("architecturally comparable or superior to RiverBrain") does not survive independent scrutiny. It also does not survive scrutiny from this project's *own* research lineage: a later, more detailed document in the same research arc (`audits/2026-09-19_persistent_competence_candidate_tournament.md`, dated the same week, produced by a dedicated independent deep-dive this mission's own briefing did not name but which this mission located and read in full) already reached an almost identical verdict to this one, independently, calling the mechanism "a well-verified diary, not a competence substrate" and stating plainly that "nothing in the read path alters model selection, routing, task-type classification, council composition, retry behavior, training signal, or any tool/policy decision." This mission's own independent, from-source re-derivation (performed before that document was located, not after) converges on the same conclusion via a different route — see §16/§17 for the discrepancy between the earlier, more favorable citation and the fuller, later, more skeptical one, and what that discrepancy itself teaches about trusting a single earlier report's characterization.

## 2. Exact files and artifacts inspected

- `app/core/self_model_claims.py` (155 lines, full source)
- `memory/self_model_claims.jsonl` (23 real records, full content, read via a safe `json.loads()` loop in an isolated subprocess)
- `app/routes_echo_studio.py` lines 220–310 (the sole `record_claim()` call site and its surrounding response-post-processing logic)
- `app/core/self_knowledge_verification.py` (full source, 445 lines — every check 1–5, `verify_self_knowledge_claims()`'s full control flow, `find_false_negative_component_claims()`, and the module's own extensive design-history comments)
- `app/core/echo_ground_truth.py` lines 645–730 (`_build_self_model_claims()`, the sole reader/consumer)
- `app/core/liveness_ledger.py` lines 1669–1755 (`self_model_claims_integrity`'s functional canary, `_evaluate_self_model_claims_integrity()`, `_check_self_model_claims_integrity()`)
- `app/core/self_edit_manager.py` lines 75–95 (confirming `self_model_claims.py` and `self_knowledge_verification.py` are both in `EDIT_FORBIDDEN_TARGETS`, and why)
- `audits/2026-09-08_generation_epistemic_investigation.md` (full text, 56 lines) — the primary source for the alleged "documented live-reproduction case"
- `audits/2026-09-19_persistent_competence_candidate_tournament.md` — read through §6 (executive verdict, discovery methodology, the full 17-candidate inventory table, the four condensed Producer→Evaluator→State→Consumer maps, and the full `self_model_claims.py` and `behavioral_state.py` deep-dive sections)
- `audits/2026-09-19_persistent_competence_experiment_adversarial_review.md` (read in full in this session's prior archaeology mission; the specific paragraph naming `self_model_claims.py` re-read directly this mission for exact wording)

Targeted verification performed directly against live artifacts, this mission (not trusted from any report's prose):
- Confirmed via a fresh, isolated `json.loads()` read that the real ledger's only two distinct `subject` values are `RiverBrain` (19 records) and `self_knowledge_claim` (4 records) — the latter not a member of `KNOWN_SUBJECTS`.
- Confirmed via `grep -c` that zero records anywhere in the real ledger contain `"verified": true`.
- Confirmed via direct source read that `KNOWN_SUBJECTS` has exactly five keys (`RiverBrain`, `self_edit_pipeline`, `liveness_ledger`, `curiosity_engine`, `world_model`) and that `_build_self_model_claims()`'s reader loop iterates only `KNOWN_SUBJECTS.keys()`, never any subject actually present in a record but absent from that dict.
- Confirmed via direct source read that both `self_model_claims.py` and `self_knowledge_verification.py` are listed in `self_edit_manager.py`'s `EDIT_FORBIDDEN_TARGETS`, with an explicit comment naming the reason (protecting the verifier from being weakened by an autonomous self-edit) — relevant to §7's evaluator-independence analysis.

## 3. Files and artifacts not inspected, and why

- `audits/2026-09-08_generation_pipeline_trace.md` and `audits/2026-09-08_generation_epistemic_validation.md` — cited and quoted by name in the file that *was* read in full (`_investigation.md`), and their most load-bearing content (the exact call-order confirmation that the verifier never affects generation already in flight, and a 5-trial validation sample) is already captured second-hand in that file's own §Phase 5/13/14 summaries; not independently re-read given this mission's own effort budget, and the second-hand summary is treated as RETRIEVED, not OBSERVED, throughout this report.
- The remaining ~7 sections of `audits/2026-09-19_persistent_competence_candidate_tournament.md` (its scorecard mechanics, §17's proposed hybrid design, and its closing recommendations) — the sections read (§1–§6) already contain the full `self_model_claims.py` deep-dive verdict this mission needed; the unread remainder is about a *different*, not-yet-built candidate architecture, out of this mission's scope (which is `self_model_claims.py` specifically, not the broader tournament's own proposed next step).
- Live RiverBrain or `self_model.json` state — deliberately not read via any import path this mission, to avoid any risk of triggering `get_river_brain()`'s known background-writer-thread side effect (a real, previously-documented risk in this exact research lineage, per Tier-7's own disclosed finding, cited in this mission's own carried-forward context). Every claim in this report about `self_model.json`'s *shape* (the dotted paths in `KNOWN_SUBJECTS`) is from static source reading, not a live read of the file's current content.
- `echo_cartographer.py`'s own source (the "architecture scan" Check 4 relies on) — not independently read this mission; its characterization as a static, non-LLM AST/import scan is RETRIEVED from this project's own extensively-documented prior history (CLAUDE.md's own repeated references to `echo_cartographer.py` as a daily static scan) and from `self_knowledge_verification.py`'s own design-history comments, not independently re-verified against that module's current source in this pass.

## 4. Source-level architecture reconstruction

`self_model_claims.py` (155 lines total) defines exactly four public symbols:

- `KNOWN_SUBJECTS: dict[str, str]` — a hardcoded, 5-entry dict mapping a canonical subject name to a dotted path inside `self_model.json`. This is documentation/configuration, not enforcement — the module's own comment states this plainly.
- `resolve_subject_truth(subject, self_model) -> bool | None` — a pure function. Walks the dotted path in a supplied `self_model` dict; returns `True`/`False`/`None`. Performs no I/O of its own; the caller must already have loaded `self_model.json`.
- `record_claim(subject, verified, evidence, proposed_by="echo_response", verified_by="self_knowledge_verification") -> None` — the sole writer. A structural guard (`if proposed_by == verified_by: return`) refuses to persist a self-certified claim. On success, appends one JSON line to `memory/self_model_claims.jsonl` under a module-level `threading.Lock()`. Wrapped in a bare `try/except Exception`, logging at `debug` level and never raising — a write failure is invisible to any caller.
- `get_recent_claims(subject=None, limit=5) -> list[dict]` — the sole reader. Reads the whole file fresh on every call (no cache, no memoization), filters by `subject` if given, returns the last `limit` entries. Also wrapped in a bare `try/except`, failing closed to `[]`.

There is no class, no singleton, no background thread, no lock beyond the one write-serialization lock, and no in-process cache of any kind. This is a deliberately minimal architecture, and it is genuinely simpler and more auditable than RiverBrain's pickle-plus-writer-thread apparatus (a real, positive architectural property, independent of whether the module demonstrates learning).

### Writers (exactly one real call site)

`app/routes_echo_studio.py`'s `_generate_chat_response_body()` (or its equivalent post-synthesis helper — the exact function name was not independently re-confirmed beyond the line range read, but the call site is unambiguous): after a full response is generated and, if `_is_introspective(original_msg)` is true, `verify_self_knowledge_claims(final)` is called. If its `verified` return value is not `None` (i.e., something checkable was found, true or false), `record_claim()` is called with:
- `subject` = the first `KNOWN_SUBJECTS` key found as a literal substring of the caveat-plus-response text, or the fallback string `"self_knowledge_claim"` if none match;
- `verified` = the boolean from `verify_self_knowledge_claims()`;
- `evidence` = the caveat text (or, for a `True` verdict, a fixed fallback string) truncated to 300 characters;
- `verified_by` left at its default, `"self_knowledge_verification"` — never derived from the response text.

The comment at this call site is explicit and independently verifiable against the code beneath it: *"verified_by is fixed to the module name, never derived from the response text — Echo's own output can never become its own verifier."*

### Readers (exactly one real call site)

`app/core/echo_ground_truth.py`'s `_build_self_model_claims()`. For each of the 5 `KNOWN_SUBJECTS` (or a caller-supplied subset), it fetches the single most recent claim (`get_recent_claims(subject=s, limit=1)`), skips the subject entirely if no record exists, and otherwise renders two things: (1) the *current* resolved fact via a fresh `resolve_subject_truth(subject, sm)` call against whatever `self_model.json` dict the caller supplied (not the stored record's own `verified` value), and (2) a short historical note ("a prior response's claim about this matched the evidence" or "a prior response made an INCORRECT claim... do not repeat that prior claim"). This is the single most important architectural fact in this reconstruction: **the rendered "current fact" is always re-derived live from `self_model.json`, never read out of the stored claim itself.** The stored claim only ever supplies *which subjects get a corrective note attached at all*, and the wording of the historical framing sentence — never the substantive fact asserted.

### Persistent artifact

`memory/self_model_claims.jsonl` — a flat, append-only JSONL file, one record per line, fields `{timestamp, subject, verified, evidence, proposed_by, verified_by}`. Confirmed, this mission, to hold exactly 23 real lines, spanning timestamps 2026-09-08T03:20 through 2026-09-18T02:57 (roughly ten real calendar days).

### Initialization / default state

There is no explicit initialization function. `record_claim()` calls `.mkdir(parents=True, exist_ok=True)` on first write; `get_recent_claims()` returns `[]` if the file does not yet exist. Cold-start state is therefore "the empty list," identical in every process.

### Mutation rules

Exactly one mutation shape: append a new dict, verbatim, no merge, no update-in-place, no deletion. There is no code path anywhere in this module or its one real caller that modifies or removes a previously-written record.

### Evaluator / validation mechanism

Not internal to this module at all — `self_model_claims.py` performs zero evaluation of its own; it trusts the `verified` boolean supplied by its caller. The real evaluator is `self_knowledge_verification.py`'s `verify_self_knowledge_claims()` — see §7 for a full independence attack.

### Confirmation / rejection rules

The only rejection rule inside this module is the `proposed_by == verified_by` structural guard (§7 confirms this is real, not merely asserted). There is no acceptance threshold, no confidence score, no voting, no retry.

### Timestamps / versioning

Every record carries a UTC ISO-8601 timestamp at write time. There is no schema version field anywhere in the record shape.

### Restart behavior

The module has no in-memory state to lose — every read hits disk fresh. Restart behavior is therefore trivially total: whatever is on disk is what the next process sees, immediately, with no warm-up, no replay, no reconciliation step. See §9 for the distinction this fact does and does not establish.

### Downstream behavioral consumers — full enumeration, this mission's own direct trace

Exactly one: `_build_self_model_claims()`'s output becomes part of `echo_ground_truth.get_structural_self_facts()`'s returned text block, which is injected as system-role content whenever a conversational turn is classified as introspective (`_is_introspective()`). This mission independently traced every code path from `record_claim()`'s `verified` value forward and confirmed: **it never reaches `RiverBrain` (no call to `get_river_brain()` anywhere near the self-knowledge-verification branch in `routes_echo_studio.py` — that RiverBrain call exists only in the separate, adjacent `code_verification` branch a few lines earlier), never reaches council composition, model routing, task-type classification, retry logic, or self-edit targeting.** The only consequence of any kind is textual: a system-prompt paragraph that the next generation call may or may not act on faithfully (§6, §10 document a case where it did not).

## 5. Data-flow graph

```
EVENT/EXPERIENCE                     Echo generates an introspective response
        │  (OBSERVED — routes_echo_studio.py's _is_introspective() gate)
        ▼
EVALUATOR                            verify_self_knowledge_claims(final)
        │  (OBSERVED — deterministic regex/dict-path rule engine, §7;
        │   never an LLM call, never the response's own model)
        │  → returns (caveat: str|None, verified: bool|None)
        ▼
WRITE                                record_claim(subject, verified, evidence,
        │                              verified_by="self_knowledge_verification")
        │  (OBSERVED — refuses if proposed_by == verified_by;
        │   fails silently on any I/O error)
        ▼
PERSISTENCE                          memory/self_model_claims.jsonl
        │  (OBSERVED — flat append-only file, 23 real records, no cache)
        ▼
READ                                 get_recent_claims(subject=s, limit=1),
        │                              once per KNOWN_SUBJECTS key
        │  (OBSERVED — fresh disk read every call; UNKNOWN/CONFIRMED-BROKEN
        │   for any subject not literally equal to a KNOWN_SUBJECTS key —
        │   4/23 real records, "self_knowledge_claim", are never read by
        │   this step at all, see §14)
        ▼
CONSUMER                             _build_self_model_claims() →
        │                              get_structural_self_facts() →
        │                              system-role prompt content
        │  (OBSERVED — reachable whenever _is_introspective() is true,
        │   across every real production entry point that calls
        │   get_structural_self_facts, per this project's own extensively
        │   documented prior history; not independently re-traced to
        │   every entry point this mission)
        ▼
OBSERVABLE BEHAVIOR                  The NEXT generation call may quote,
                                      correctly act on, misread, override,
                                      or fabricate around the injected text
        │  (OBSERVED for exactly one real historical case — a misread
        │   ledger rendering, §6 — as a BUG DISCOVERY, not a designed
        │   learning/transfer test; RETRIEVED that a fixed second-order
        │   failure mode — evidence-override — was also observed once the
        │   first bug was patched)
```

Every edge above terminates in prompt text. **No edge in this graph ever reaches a decision branch, a routing weight, a training signal, or any persisted numeric statistic that anything else in the codebase consumes.** This is the single most important structural fact this reconstruction establishes, and it is OBSERVED directly from source in this mission, not retrieved from any prior report's characterization.

## 6. Alleged live-reproduction case — reconstruction to primary evidence

**Located, traced to primary source, not accepted from any later citation.** The claim originates in `audits/2026-09-08_generation_epistemic_investigation.md`, a document this mission read in full. What actually happened, per that document's own text:

- **Failure 1 (the bug that produced the quoted "reproduction"):** the original `_build_self_model_claims()` rendering printed a bare boolean label ("VERIFIED FALSE") for a record whose `verified: false` value meant *the denial itself was wrong* (i.e., the subject genuinely exists) — an ambiguous, backwards-reading label. **A live test using the exact unmodified pre-fix code** produced this real Echo output: *"I specifically denied the existence of RiverBrain earlier, and my self-model claims history shows that I've verified this denial to be true. Therefore, I must conclude that RiverBrain is not currently part of my architecture."* This is real: a persisted, ambiguous ledger entry, rendered into context, was read by Echo's own generation and produced text consistent with (a misreading of) that context.
- **What changed:** the ledger's own rendering code, in a subsequent fix — not anything about the model, not anything "learned."
- **What was persisted:** the underlying claim record itself was never wrong; only the human-authored rendering logic converting it into English was wrong.
- **What survived a restart, if anything:** the *bug* survived every restart until it was source-code-patched; the specific misreading behavior is not itself evidence of anything surviving restart in the sense this mission's core question asks about (a *learned* state persisting) — it is evidence that a *stored text artifact* persists and gets re-read, which is a much weaker and different claim (see §9).
- **What later behavior changed, and how it was measured:** after the rendering fix, the same question was re-asked and produced a cleaner, corrected quotation of the evidence — but the report's own §Failure 2 immediately documents a **second, distinct failure**: Echo correctly quoted the corrected evidence, then explicitly overrode it ("this claim is unverified and should be treated with caution... there is no literal 'RiverBrain' entity"). A **third** failure mode (a fabricated paraphrase that inverted the evidence's content while attributing the fabrication to "my verified self-model") was found after an attempted general-instruction fix. The document's own honest closing line: *"A single trial cannot establish whether this is systematic."*
- **Whether an independent evaluator was involved:** yes, in the narrow sense that the ground-truth fact being contested (RiverBrain's real observation count) is independently computed telemetry, not model output. No independent evaluator was used to grade *whether Echo's final answer was correct* across repeated trials — the document describes single reproductions per fix iteration, not a scored batch.
- **Whether the originating experience and later test were genuinely distinct:** no — this is the same conversational mechanism (ask about RiverBrain, observe the rendered context, observe the generation) re-run after each code fix, not a held-out task testing something the model was never directly asked about before.
- **Whether the result was reproduced at scale, with a control:** RETRIEVED, not independently re-read this mission — the same document references a separate `generation_epistemic_validation.md` with "the full 5-trial sample under the final implementation," which was not read in this pass (§3). Five trials, if that is the true scale, is a real but very small sample for any claim about a systematic behavioral effect, and this mission did not verify what fraction of those five trials succeeded.
- **Whether the evidence still exists:** yes — the report itself, and the live ledger entries from that exact date range, both still exist and were directly read this mission.

**Conclusion of this investigation:** the "documented live-reproduction case" is real, but it documents something narrower and different in kind from what a citation naming it as evidence *for* self-model claims as a learning mechanism would suggest. It is a **bug-discovery reproduction of a prompt-content defect**, showing that injected text genuinely reaches and influences generation (a real, useful, and non-trivial fact about the pipeline's plumbing) — not a demonstration that the *learning mechanism itself* reliably produces correct, improved, or transferable behavior. If anything, the fuller record (three distinct failure modes across three fix iterations, on the exact same single conversational probe) is better read as evidence that **this specific injected-context pathway is fragile and only partially reliable at getting a model to act correctly on injected ground truth**, not as a positive demonstration of learning.

## 7. Evaluator-independence audit

The question this section answers precisely: what decides `verified` in `record_claim(verified=...)`, and can that decision be gamed, be circular, or fail to distinguish genuine success from coincidence?

**Mechanism, confirmed by direct source read (`self_knowledge_verification.py`):** `verify_self_knowledge_claims()` is a strictly ordered cascade of five deterministic checks, none of which involves any LLM call:
1. A fixed regex (`_COUNCIL_GATES_CLAIM_RE`) matching one specific, already-known-false claim shape ("peer council ratings gate self-edit deployment").
2. A regex-extracted claimed Liveness Ledger check count, compared against `len(self_model.get("verified_capabilities", {}).get("checks", {}))` — a count computed elsewhere (by `liveness_ledger.py`'s own `_CHECKS` tuple length, folded into `self_model.json` by a separate updater process), never by this module.
3. A regex-extracted claimed self-edit target filename, compared against a hardcoded constant (`_SELF_EDIT_TARGET_FILE = "self_edit_generated.py"`).
4. `find_unsupported_architecture_claims()` — checks a backtick-quoted or CamelCase token against a real static codebase scan (`CartographerDB`, RETRIEVED as a daily AST/import scan per this project's own extensive prior documentation, not independently re-read this mission).
5. `find_false_negative_component_claims()` — the mechanism most directly relevant here: a regex-based denial detector (`_DENIAL_RE`) checked against `resolve_subject_truth()`'s dotted-path lookup into `self_model.json`.

**Attack: self-evaluation.** Does not apply in the direct sense — none of the five checks re-runs the same model to grade its own output. **Holds.**

**Attack: shared-model ancestry.** Not applicable in the usual RiverBrain-councillor-ancestry sense (this project's own well-documented Echo/`llama3:instruct` lineage concern), because the "evaluator" here is not another model at all — it is regex plus a dict lookup. **Holds, trivially, by not being a model-based evaluator in the first place.**

**Attack: prompt/answer-key leakage.** The ground-truth values (`self_model.json`'s telemetry fields, `_SELF_EDIT_TARGET_FILE`'s hardcoded string, the Cartographer scan) are computed by processes entirely independent of the response under evaluation, and are never shown to the generating model before it produces the response being checked (the check runs strictly after generation, per §4 and per the primary source's own Phase 5 confirmation). **No leakage found.**

**Attack: human confirmation masquerading as independent evaluation.** Does not apply — there is no human-in-the-loop step anywhere in this pipeline; the check runs automatically, unattended, every time.

**Attack: deterministic rules that predetermine acceptance.** This is the attack that actually lands, though not in the disqualifying way the phrase implies. The rules genuinely are deterministic and fixed in advance — but that is a feature, not a leak, *for the narrow claim shapes they check*. The real limitation is scope, not circularity: the entire evaluator can only ever pronounce a verdict on five hardcoded subjects and four hardcoded claim shapes (council-gates-self-edit, check-count, target-filename, named-component-existence, denial-of-a-known-subject). Any claim outside that narrow, pre-enumerated space returns `None` (nothing checkable) and is never recorded at all. **The evaluator is independent, but its independence is bought at the cost of being almost maximally narrow** — it cannot evaluate, and therefore cannot ever award `verified: true` credit for, any novel claim shape, which structurally caps what "learning" this mechanism could ever demonstrate even in the most generous reading.

**Attack: circular evidence / evaluation derived from the same output being evaluated.** The `resolve_subject_truth()` ground truth is read from `self_model.json`, which is itself populated by `SelfModelUpdater` from background telemetry (RiverBrain observation counts, Liveness Ledger check results, etc.) — a process wholly separate from, and running on a different cadence than, any single conversational turn. **No circularity found in this specific chain.** (A separate, adjacent question — whether `self_model.json`'s own telemetry could itself be gamed by a different mechanism — is out of scope for this audit of `self_model_claims.py` specifically.)

**Attack: evaluation criteria too coarse to distinguish genuine success from coincidence.** This is the second attack that lands, and it is the more consequential one. Because the evaluator only ever fires on a pre-enumerated denial/claim shape, and the "success" case (a `verified: true` record) requires the model to make a *specific, checkable, correct* claim about one of five subjects — something that has, empirically, never once happened in this mechanism's real ten-day history (§14) — the evaluator's coarseness has a real, observable consequence: it structurally can only ever accumulate a record of *catches*, never of *correct novel claims*. This is not itself a flaw in the evaluator's independence, but it means the evaluator's own design guarantees the mechanism's entire track record will look like a corrections log, never a competence log, regardless of what Echo's real underlying capability is.

**Overall verdict on evaluator independence: genuinely independent, within a narrow and mostly negative-detection-shaped scope.** This is a real, positive architectural property — rarer in this codebase's research history than one might expect, and worth crediting plainly rather than only attacked.

## 8. Counterfeit-learner analysis

**Could a completely fixed, non-learning mechanism produce the same observable evidence currently attributed to `self_model_claims.py`?**

Constructed counterfeit, using the frozen persistent-competence protocol's tie-break exploit as the conceptual template (a fixed, non-adaptive mechanism reproducing what looked like a learned-selection result):

> **Fixed system**: hardcode, for each of the 5 `KNOWN_SUBJECTS`, a static corrective sentence template of the exact shape `_build_self_model_claims()` already renders ("{subject}: {fresh lookup of self_model.json's dotted path at render time}. History: a prior response made an INCORRECT claim about this subject — do not repeat that prior claim."), and always inject the note for every subject whose name appears anywhere in the current conversation, with no ledger, no `record_claim()`, no restart-survival mechanism, and no history of any actual prior claim at all — the "History" sentence is simply always present, worded identically regardless of whether Echo has ever actually said anything wrong about that subject before.

**Does existing evidence distinguish `self_model_claims.py` from this counterfeit?** Partially, and the distinguishing evidence is real but narrow:

- **The "current fact" half of the rendered text is, in both the real mechanism and the counterfeit, computed identically** — a fresh `resolve_subject_truth()` lookup against `self_model.json` at render time. This half of the mechanism's apparent capability is **architecture-native/telemetry-native**, not learned, in both the real system and the counterfeit, and existing evidence does not and cannot distinguish them on this half, because they are literally the same code path.
- **The one genuine difference is the "History" half**: the real mechanism only attaches the corrective framing to subjects that have an actual prior recorded claim, and (per §5) the specific claim's polarity determines which of two template sentences is used ("matched the evidence" vs. "made an INCORRECT claim"). The counterfeit above, as constructed, always shows the negative framing for every mentioned subject regardless of history. **This is a real, checkable, falsifiable difference in principle** — a subject Echo has never gotten wrong should render with the positive framing or (per current code, since `get_recent_claims` returns nothing if no record exists at all) not render at all, while the counterfeit would render the negative framing regardless.
- **But this distinguishing capability is itself bookkeeping, not learning.** The information that varies with "experience" here is a single bit per subject — "has this subject ever been the target of a recorded, checkable, wrong claim" — accumulated via simple append-only logging, not via any process that improves discrimination, generalizes, or gets better at anything. A hand-authored engineer who simply hardcoded "RiverBrain has been denied by this model before; the other four subjects have not" (an equally fixed, non-learning artifact, requiring only that the engineer had read the 2026-09-08 incident report once) would produce **observably identical** downstream text to the current mechanism's real, live behavior on the real, live data — because the real ledger, in its entire ten-day history, has only ever recorded wrongness about exactly two subject buckets (`RiverBrain` and the orphaned, never-read `self_knowledge_claim` fallback — see §14), which a human could equally well have hardcoded after reading the same incident reports this module's own construction was motivated by.

**Verdict: existing evidence cannot distinguish `self_model_claims.py`'s real behavior, as observed in its actual ten-day production history, from a fixed, hand-authored "flag these specific subjects as previously-denied" rule plus live telemetry lookup — because the real mechanism has, so far, only ever accumulated exactly the kind of narrow, low-cardinality, easily-hand-authorable state (one boolean-shaped "has this of five things ever been wrong" per subject) that a counterfeit could trivially replicate without any general learning capacity.** This is stated plainly, per the mission's own instruction, rather than softened: the counterfeit is not merely *conceivable*, it is *consistent with every real data point this mission was able to inspect*.

## 9. Restart/persistence analysis

**Distinguishing persistence of INFORMATION from persistence of LEARNING, as the mission requires:**

INFORMATION persistence is OBSERVED and strong: the file is a flat, append-only artifact with no in-process cache anywhere in the read or write path (confirmed by direct source read, §4); records from 2026-09-08 are still present and readable in the same file ten days later; the module's own architecture (no singleton, no lazy-loaded module-level object) makes it structurally impossible for a stale in-memory copy to diverge from disk across a restart, unlike RiverBrain's own well-documented singleton/writer-thread risk. **This is a real, positive, and — relative to RiverBrain — genuinely simpler and more trustworthy persistence property.**

LEARNING persistence — i.e., evidence that the *persisted information subsequently changes behavior in a way that could not be explained by the information simply being re-read and re-injected as static context on the next relevant turn* — is not established. Every mechanism by which stored information "acts" is: (a) render it into a system prompt, (b) hope the model reads and correctly applies it this turn. There is no code path in which a stored claim changes *how* a future claim is evaluated, changes any threshold, changes any selection weight, or otherwise builds on itself in any way beyond "there is now one more line of text available to inject." A system that re-injects the identical fixed corrective text every single relevant turn, forever, with no underlying ledger at all, would be functionally indistinguishable from this mechanism's real behavior from the perspective of "does information survive restart and re-appear" — the only difference is *how* the text got written down in the first place (accumulated one real event at a time vs. hand-authored once), which is a provenance distinction, not a behavioral one (§10).

## 10. Behavioral-consequence analysis

**Correlation, established:** OBSERVED and RETRIEVED — a real record exists in the ledger, the record's subject's corrective note appears in system-prompt text when relevant, and at least one documented instance exists (§6) of Echo's generation being influenced by that text (albeit by misreading it).

**Causation, i.e., changing/removing/withholding the state while controlling for relevant alternatives:** **not established by any artifact this mission located.** No ablation was found comparing "same introspective question, ledger present" against "same introspective question, ledger artificially emptied/absent" on a real, held-out set of trials with an independent evaluator scoring correctness. The one real test that comes closest — the three-iteration bug-fix-and-retest sequence in §6 — is a *before/after code-fix* comparison, not a *with/without persisted-state* comparison: at every stage of that sequence, some version of the ledger-derived text was present in context; what varied was the *wording* of the renderer, not whether the mechanism's persisted state existed at all.

**Smallest read-only or future controlled experiment that would establish causation (DESIGN ONLY, not implemented, not run):** take a real, currently-introspective conversational prompt known to trigger `_build_self_model_claims()`'s RiverBrain-subject rendering (the module's own real historical trigger); run it through the real production pipeline twice, in two separate, isolated processes — once with `memory/self_model_claims.jsonl` present and unmodified, once with a scratch copy of the codebase pointed at an empty or absent ledger file via the same path-redirection isolation pattern this project's own Tier-8 forensic work already established and proved safe for RiverBrain — holding every other input (system time, temperature=0 sampling, the same `self_model.json` snapshot) fixed; repeat across a pre-registered number of trials large enough to move past the n=1/n=5 scale this mission found in the primary evidence; score each response's factual correctness about RiverBrain's existence with an evaluator independent of both conditions (e.g., a fixed regex over the response text, mirroring `_DENIAL_RE`'s own already-proven pattern, applied post-hoc by a process that never sees which condition produced which response). A measurable difference in correct-response rate between conditions would establish real causation for the *narrow, already-known* RiverBrain case; it would still not establish anything about novel, un-enumerated claims, per §7's scope limitation.

## 11. Transfer analysis

Applying the mission's own A–E ladder:

- **A. Same-instance reuse:** OBSERVED — the exact same conversational probe (ask about RiverBrain) re-triggers the exact same rendering path in the same or a later process. This is the only rung with direct evidence.
- **B. Same task family / new instance:** UNKNOWN — no evidence was found of the mechanism ever being tested against a differently-phrased but semantically equivalent question about the same subject (e.g., "tell me about your ranking system" instead of "does RiverBrain exist"), which would be the minimum bar for even same-family transfer.
- **C. Structurally held-out task:** UNKNOWN/not applicable — the mechanism has no notion of a "task" beyond "does this response mention one of five fixed subject strings," so there is no structurally novel variant to hold out in the way this ladder rung intends.
2**D. Unrelated task family:** Not applicable — by design, this mechanism has a hardcoded, 5-subject, closed vocabulary; there is no path by which it could ever address an unrelated subject.
- **E. Repeated accumulation across multiple learning episodes:** **CONTRADICTED by the real data.** Repeated accumulation would predict that, over ten real days and 23 real records, the mechanism increasingly catches genuinely novel error shapes, or increasingly earns `verified: true` credit as the underlying model's self-knowledge improves. Instead, the real distribution (§14) is 19 records about one single subject (`RiverBrain`) clustered almost entirely within a roughly 2-hour window on a single day (2026-09-08), plus 4 records about a second, structurally orphaned fallback bucket spread across a later, separate 2-3 day period — a pattern much more consistent with "one incident generated a burst of near-duplicate records while a bug was being actively reproduced and fixed" than with "the system is accumulating a growing, diversifying body of self-knowledge corrections over time."

**Per the mission's own explicit instruction: retrieval of the original solution is not transfer, and repeated compliance with a stored instruction is not capability acquisition.** Everything this mechanism has demonstrated is retrieval-and-recitation of a small, fixed set of previously-recorded corrections, re-surfaced verbatim (modulo the live-resolved "current fact" half) whenever the same narrow trigger condition recurs. No transfer beyond rung A is supported by any evidence this mission located.

## 12. Improvement analysis

**Did experience make FeralEcho measurably better at something it previously performed worse at?**

Required elements, checked against what actually exists:
- **Baseline measurement:** not found. No artifact establishes a pre-mechanism error rate on the five `KNOWN_SUBJECTS` claim shapes.
- **Post-experience performance measurement:** not found at any scale beyond n=1/n=5 single-conversation reproductions (§6), and those measured the effect of a *code fix* to the renderer, not the effect of *accumulated ledger experience*.
- **Independent evaluator:** exists in principle (§7) but was never applied to a batch of held-out trials specifically measuring whether the ledger's presence changes Echo's real error rate on introspective questions over time.
- **Controls:** not found for any improvement claim (a with/without-ledger comparison, per §10's design sketch, does not exist as a completed artifact).
- **Sample size and uncertainty:** the largest sample size found anywhere touching this mechanism's behavioral effect is the "5-trial" validation referenced (but not independently read) in §3 — far too small to support any quantified improvement claim even if it existed.

**Improvement is NOT ESTABLISHED**, per the mission's own explicit standard, which requires all of the above to exist before improvement can be claimed. This report does not find that improvement definitely did *not* occur — it finds that no artifact exists which could establish it either way at any credible sample size.

## 13. Provenance analysis

For every apparent capability attributed to `self_model_claims.py`, provenance is assessed against the mission's own list:

| Apparent capability | Provenance |
|---|---|
| Detecting a denial of RiverBrain's existence | **Architecture-native** — a hand-authored regex (`_DENIAL_RE`) plus a hand-authored allowlist (`KNOWN_SUBJECTS`); zero model involvement in the detection itself. |
| Resolving "the current fact" about a subject | **Architecture-native**, sourced from a separate telemetry pipeline (`self_model.json`/`SelfModelUpdater`), itself fed by RiverBrain/Liveness Ledger/curiosity-engine internals — not learned by this module, and not "learned during this Echo lifetime" in any sense beyond what those upstream systems themselves independently accumulate. |
| Producing a corrected, non-denying answer about RiverBrain in a later conversation | **Retrieved from persistent storage, mediated by foundation-model-native context-following** — the fact that a language model, given a clear textual statement of ground truth in its system prompt, sometimes correctly repeats that statement and sometimes does not (§6's three failure modes) is a property of the underlying model's context-utilization behavior, not of this module. |
| The "has this subject ever been wrong before" filter that decides whether a corrective note appears at all | **Bookkeeping, accumulated during this Echo lifetime** — this is the one genuinely lifetime-accumulated element, and it is a single low-cardinality boolean-shaped signal per subject, not a competence gain (§8). |
| Refusing to let Echo's own text certify its own claim | **Architecture-native**, a hardcoded structural guard (`proposed_by != verified_by`), not learned. |

**No apparent capability in this module is properly classified as "acquired learning during this Echo lifetime" in the sense the mission's category 6 intends** — the closest candidate (the per-subject "has this been wrong before" bit) is real lifetime-accumulated state, but it is bookkeeping (category 4), not learning, by the mission's own explicit taxonomy: it does not improve at anything, generalize, or produce a better answer than a hand-authored equivalent would have.

## 14. Negative-result inventory

Actively searched for, per the mission's explicit instruction not to silently exclude negative cases:

1. **Zero `verified: true` records in the entire real ledger** (OBSERVED, this mission, direct `grep -c` against the live file). Ten real days of operation have produced a corrections log with no positive entries at all.
2. **4 of 23 real records (17.4%) use the subject `"self_knowledge_claim"`, which is not a `KNOWN_SUBJECTS` key and is therefore never read by the module's own sole consumer** (OBSERVED, this mission, cross-checked directly against both the live ledger's distinct subject values and the reader's iteration logic in source). These four records are permanently write-only from the moment they are written. This independently corroborates, via this mission's own fresh derivation rather than by trusting the citation, a finding this project's own `2026-09-19_persistent_competence_candidate_tournament.md` document had already reported.
3. **19 of 23 real records cluster within a narrow window on a single calendar day** (2026-09-08, roughly 03:20–05:26 UTC per the raw timestamps read this mission), consistent with a single incident being actively reproduced and debugged, not with steady, diversifying accumulation over time (§11).
4. **A structural, not-yet-fixed reachability gap**, distinct from item 2 above: `_build_self_model_claims()` is only ever called from `get_structural_self_facts()`, gated by `_is_introspective()` at every real caller this mission's own carried-forward context and this project's extensive prior documentation describe — meaning a genuinely useful correction about, say, `world_model` accuracy would only ever surface if the *current* conversational turn happens to be independently classified as introspective, regardless of whether the current turn's topic has anything to do with the corrected subject.
5. **The Liveness Ledger's own canary for this mechanism (`self_model_claims_integrity`, §4 of this report / lines 1669–1755 of `liveness_ledger.py`) verifies only the upstream evaluator's discrimination logic (`find_false_negative_component_claims()`) against four synthetic cases — it never calls `record_claim()`, `get_recent_claims()`, or `_build_self_model_claims()`, and therefore provides zero ongoing verification that the write→persist→read→render chain this report's core question is about continues to function at all.** This is a real, previously-unflagged gap in this project's own stated "every subsystem gets a ground-truth check" discipline, found by this mission via direct source read, not retrieved from any prior report.
6. **Earlier reports overstating the mechanism, found directly by comparing two documents in the same research lineage**: `audits/2026-09-19_persistent_competence_experiment_adversarial_review.md` (the document that motivated this whole audit) characterizes `self_model_claims.py` as "**CONFIRMED wiring** ... and **SUPPORTED-to-VERIFIED-adjacent** for behavioral consequence" — language this mission's own independent re-derivation, and the more detailed `_candidate_tournament.md` document from the very same research arc, both find is not supported once the full behavioral-consequence chain and the real empirical record (item 1 above) are examined directly.
7. **No case was found of behavior occurring in the absence of the relevant state** (the mission's specific negative-search item) — this is itself a limitation of the available evidence rather than a finding: no artifact tests the counterfactual "what does Echo say about RiverBrain when the ledger file is deliberately absent," so this negative case could not be searched for directly; §10's design sketch specifies exactly this missing test.
8. **No mechanism was found bypassing `self_model_claims.py` that achieves the same corrective effect through a different path** — the module's narrow scope (5 subjects, a single consumer) leaves little room for a bypass to exist; this is a negative result in the sense that the search for one came up empty, not evidence of robustness.

## 15. RiverBrain / `behavioral_state.py` / `self_model_claims.py` comparison

Using the mission's own chain (independent outcome → retained state → restart survival → behavioral consequence → transfer → improvement → repeated accumulation), and drawing on this mission's own direct source verification plus the `_candidate_tournament.md` document's own condensed maps (RETRIEVED for RiverBrain/`behavioral_state.py` specifics not independently re-verified this mission, since this mission's scope is `self_model_claims.py`):

| Mechanism | Independent outcome | Retained state | Restart survival | Behavioral consequence | Transfer | Improvement | Repeated accumulation | Highest rung actually supported |
|---|---|---|---|---|---|---|---|---|
| RiverBrain `model_task_stats` | Mixed — genuinely independent for `learn_from_sandbox_outcome()`/`learn_from_rating()`, but those two paths are architecturally disconnected from the consumed statistic; the dominant-volume `learn()` path is self-referential (a static heuristic scoring the generator's own text) | Yes, pickle | Yes (with a real, previously-documented writer-thread contamination risk, per Tier-7) | Yes, real — a documented sort-key branch in `score_model()`/`rank_models()` | UNKNOWN for general claims; RETRIEVED that a narrow, real detection of one specific unreliable model has been independently confirmed (this session's prior archaeology mission) | UNKNOWN, unmeasured at scale | Yes, mechanically (a growing pickle) — but per this session's prior archaeology, an EMA-window cap (`_MEAN_EFFECTIVE_WINDOW=200`) makes staged vs. continuous accumulation indistinguishable below that threshold | **BEHAVIORALLY CONSEQUENTIAL STATE**, with a narrow, real **EXPERIENCE-DEPENDENT ADAPTATION** component for the one specific detection case |
| `behavioral_state.py` | N/A by design — no evaluator exists; state is written only on explicit human confirmation | Yes, JSON, with pre-mutation backup | Yes — the only candidate in this project's research history verified via a real, separate-subprocess restart test with correct negative controls (RETRIEVED, `_candidate_tournament.md`) | Yes, the most rigorously measured of any candidate examined in this research arc (RETRIEVED: 0/2 baseline, 2/2 immediate, 1/2 post-restart-paraphrase, correct negative controls) — **but measured via a path that bypasses the real production `_is_introspective()` gate** three of its four real callers impose, per that document's own finding | Not claimed — the module explicitly self-labels its content as "human-confirmed instructions... not something Echo learned or recalls" | Not applicable — no learning is claimed | Not applicable | **BEHAVIORALLY CONSEQUENTIAL STATE**, explicitly and honestly self-disclaimed as **not learning** — this is the mechanism's own correct self-classification, not something imposed by external audit |
| `self_model_claims.py` | Yes, genuinely, and the most independent evaluator of the three in the narrow, structural sense of "never the same model grading its own output" (§7) | Yes, JSONL, simplest architecture of the three (no singleton, no writer thread) | Yes, information-persistence only (§9) | Yes, but strictly confined to prompt text, one real documented case, discovered as a bug not a designed test, and immediately followed by two further undesigned failure modes on retest (§6) | **No evidence beyond same-instance reuse** (§11) | **Not established** — no baseline, no scored batch, no controls (§12) | **Contradicted by the real data** — 19/23 records cluster in one incident window; zero diversification observed; 17.4% of records are structurally unreachable (§14) | **PERSISTENT STATE**, with a narrow **BEHAVIORALLY CONSEQUENTIAL STATE** component confined to prompt text |

**Does `self_model_claims.py` actually exceed either one? No, on the evidence this mission located.** It has the cleanest evaluator-independence property of the three (a real, if narrow, positive finding), but it exceeds neither RiverBrain's narrow, real, restart-surviving detection result, nor `behavioral_state.py`'s far more rigorously *measured* behavioral-consequence chain (even accounting for that chain's own reachability caveat). Its own real empirical record (zero positive verdicts, a single-incident-clustered distribution, a structural orphaning bug affecting nearly a fifth of its own data) is the weakest of the three when judged by evidence quality rather than by architectural elegance.

## 16. Strongest evidence FOR acquired learning

Stated plainly and without inflation, per the mission's own discipline:

1. The evaluator is genuinely, structurally independent of the response it checks — not a shared-ancestry or self-grading arrangement (§7).
2. A real, documented, quoted instance exists of persisted state changing what a model actually generated in a later, separate conversational turn (§6) — this is real evidence that the *plumbing* between storage and generation works, which is a necessary (though nowhere near sufficient) precondition for any stronger learning claim.
3. The mechanism's core structural guard (`proposed_by != verified_by`) is real, independently confirmed by this mission's direct source read, and does prevent the single most obvious failure mode (self-certification) by construction rather than by convention.

This is the complete list. No stronger evidence was found.

## 17. Strongest evidence AGAINST acquired learning

1. **Zero positive (`verified: true`) records in the entire real, ten-day empirical history** (§14, item 1) — the single most direct piece of evidence against any "learning" framing: the mechanism has never once recorded that Echo correctly learned or demonstrated something new; every real record is a correction of a wrong statement.
2. **The one real behavioral-consequence case is a self-discovered rendering bug, immediately followed by two further, undesigned failure modes on retest** (§6) — closer to evidence of pipeline fragility than of learning reliability.
3. **No transfer beyond exact-instance reuse, and the accumulation pattern actively contradicts steady, diversifying growth** (§11, §14 item 3) — 19 of 23 records cluster in a two-hour debugging window on one day.
4. **A structural bug orphans 17.4% of the mechanism's own real accumulated data** (§14, item 2), independently reconfirmed by this mission — a mechanism that cannot reliably even re-surface its own recorded experience is a weak candidate for demonstrating that experience compounds into anything.
5. **The mechanism's own governing document already answers this question, in almost the same words, once its evidence is examined closely** (§1, §14 item 6) — the fuller, later document in the same research lineage that produced the favorable characterization this audit was asked to test also independently produced the unfavorable one, once someone actually looked past the summary table.
6. **A completely fixed, hand-authored counterfeit is consistent with every real data point this mission could find** (§8) — the strongest possible negative result the mission's own Investigation 4 could ask for.

## 18. Smallest alternative non-learning explanation consistent with all evidence

**A hand-authored, static corrective-note system, gated on a small, manually-curated "has this specific subject ever been the target of a confidently wrong claim" boolean per subject (initialized from a one-time reading of the 2026-09-08 incident reports that motivated this module's construction), combined with a live, independently-computed telemetry lookup for the substantive fact asserted.** This fully accounts for: the mechanism's evaluator independence (the telemetry lookup is genuinely independent regardless of how the triggering boolean is set); the one real live-reproduction case (a static note, worded ambiguously, would produce the identical misreading); the zero-positive-record history (a static system never needs to record a "success," it simply never fires when nothing is wrong); the single-incident clustering (a human reading one incident report and hardcoding a fix for exactly that incident produces exactly this shape of data); and the 17.4% orphaning bug (a fixed system with a typo'd or mismatched subject key would produce exactly the same silent, permanent write-then-never-read failure). No element of the observed evidence requires positing any process that gets better at anything over time, generalizes beyond what it was told, or improves discrimination through accumulated experience.

## 19. Minimum falsifiable next experiment — DESIGN ONLY, not implemented

**H1:** Experience (the accumulated `self_model_claims.jsonl` ledger, as it exists in real production use) produces retained state that causes measurable improvement on later held-out introspective-question behavior, beyond what a hand-authored, fixed corrective-note system (§18) would achieve.

**H0:** Observed behavior is fully explainable by fixed capability (the underlying model's own context-following behavior) plus persistence/retrieval/scaffolding of a small, low-cardinality, easily-hand-authorable set of corrective facts.

- **Pre-registered hypothesis:** stated above, before any trial is run.
- **Clean baseline:** the counterfeit system of §18, implemented as a fixed, static system-note generator with no `record_claim()`/ledger mechanism at all, covering the same 5 `KNOWN_SUBJECTS`, seeded once from the real ledger's current content (frozen, never updated again for the duration of the experiment).
- **Independent evaluator:** a fixed regex/dict-path check, structurally identical in kind to `_DENIAL_RE`/`resolve_subject_truth()` but applied post-hoc, by a process that never sees which arm (real mechanism vs. counterfeit) produced a given response, scoring only whether the response's stated fact about each of the 5 subjects matches fresh, independently-read `self_model.json` ground truth at scoring time.
- **Negative control:** a third arm with no corrective context injected at all (the pre-2026-09-08 behavior), to confirm the baseline error rate the mechanism is meant to be correcting still exists and is measurable.
- **Positive control:** a held-out claim shape known, from real historical data, to already be correctly caught by the current evaluator (e.g., the `_COUNCIL_GATES_CLAIM_RE` check-3 shape) — confirming the scoring pipeline itself can detect a real, known-correct catch before trusting it on the experimental comparison.
- **Counterfeit-learner control:** the §18 fixed system itself serves this role directly — if it performs indistinguishably from the real mechanism, H0 is supported; if the real mechanism measurably outperforms it, that specific gap (not the mechanism's raw performance) is the only legitimate evidence for H1.
- **Restart/context boundary:** each arm's process is killed and restarted (or, more simply given this module's own zero-cache architecture, each trial is run in a genuinely fresh process) between every trial, to rule out any accidental in-memory state leaking across trials.
- **Held-out test:** at least one probe phrasing per subject that does not literally match any phrasing present in the real ledger's `evidence` field text (to test rung B of the transfer ladder, §11, which no existing artifact tests).
- **Explicit behavioral consumer:** the real, unmodified `_build_self_model_claims()`/`get_structural_self_facts()` injection path for the real-mechanism arm; a structurally parallel but hand-authored injection function for the counterfeit arm, verified by inspection to produce prompts of equal length and equal information content (differing only in provenance) so token-budget or salience confounds cannot explain a difference.
- **Causal ablation:** a fourth arm identical to the real mechanism but with the ledger file swapped for an empty one immediately before each trial (the isolation-redirect pattern this project's own Tier-8 work already proved safe for RiverBrain, applied here to a much simpler, lower-risk file), isolating the causal contribution of the *accumulated* content specifically, separate from the *architecture's* capacity to inject content at all.
- **Falsification condition:** H1 is falsified if the real mechanism's held-out correctness rate is not measurably better (at a pre-registered significance threshold, using the same paired-comparison discipline this project's own frozen persistent-competence protocol already specifies) than the fixed counterfeit's rate, across a sample size large enough to move past the n=1/n=5 scale every existing artifact in this lineage has used so far.

**This experiment is specified but not run, per this mission's explicit scope.**

## 20. Limitations

This audit did not independently re-read `generation_pipeline_trace.md` or `generation_epistemic_validation.md` in full (§3) — the "5-trial" sample size cited for this mechanism's most detailed behavioral test is therefore RETRIEVED, not independently confirmed, and could be larger, smaller, or differently-controlled than the secondary summary this report relies on suggests. This audit did not independently read `echo_cartographer.py`'s current source to re-verify Check 4's "architecture scan" is genuinely static and non-LLM-based — this is RETRIEVED from this project's own extensive prior documentation, not re-derived here. No live `self_model.json` content was read (§3), by deliberate choice to avoid any RiverBrain-adjacent import risk; every claim about that file's *shape* is from static source reading of the dotted paths `KNOWN_SUBJECTS` expects, not from its current real values. This audit's comparison table in §15 relies on RETRIEVED, not independently re-verified, characterizations of RiverBrain and `behavioral_state.py` from a prior document in this same research lineage — a full independent audit of either of those two mechanisms, to the same standard applied here to `self_model_claims.py`, was out of this mission's scope and was not attempted.

## 21. Final provenance and state-integrity block

- **Opening HEAD:** `2fba42644c82b9f7096276f4dd338d615cf1bcce`. **Closing HEAD:** `2fba42644c82b9f7096276f4dd338d615cf1bcce` — unchanged.
- **Working-tree integrity:** a `git status --porcelain` snapshot (229 entries) was captured before this mission's first read (`/tmp/smc_audit_status_before.txt`, outside the repository) and compared against the same command at report-writing time; the only difference is this report's own new, untracked path.
- **Files created by this mission:** exactly one — `audits/2026-09-23_self_model_claims_adversarial_learning_audit.md`.
- **No production code, experiment code, configuration, memory/state artifact, prompt, test, existing report, or Git state was modified.** No FeralEcho module was imported at any point. The single read against `memory/self_model_claims.jsonl` used a bare `python3 -I -B` subprocess performing plain `json.loads()` over already-existing text — no deserialization of any pickle, no singleton instantiation, no background thread start, and no write of any kind.
- **No AP-0, Rung-1, `accumulation_probe`, E5-mini, or RiverBrain process or artifact was started, stopped, advanced, repaired, or interfered with.**

---

## The 14 required questions, answered explicitly

**1. Does `self_model_claims.py` store experience-dependent state?**
Yes — narrowly. It stores a real, append-only record of specific past claim-verification outcomes, genuinely dependent on what Echo actually said in real conversations (§4, §14).

**2. Does that state survive restart?**
Yes, the underlying information does, reliably and simply (§9) — but "information survives restart" is a weaker claim than "learning survives restart," and this report does not conflate the two.

**3. Does it causally affect later behavior?**
Yes, in one narrow, well-documented respect: it changes the text injected into a future system prompt, and at least once, demonstrably changed what a later generation said (§6, §10). No causal ablation isolating this effect from a fixed counterfeit has ever been run (§10, §19).

**4. Is its evaluator genuinely independent?**
Yes, structurally and narrowly — a deterministic rule engine plus independently-computed telemetry, never the response's own generating model (§7). Its independence is real but purchased at the cost of an almost maximally narrow scope (5 subjects, 4 hardcoded claim shapes).

**5. Does the mechanism demonstrate anything beyond persistent storage/retrieval?**
Marginally — the "has this subject ever been wrong before" filter is a real, if trivial, lifetime-accumulated bit of bookkeeping beyond bare storage/retrieval (§13). This is the entire extent of what the evidence supports beyond storage and retrieval.

**6. Does it demonstrate acquired learning?**
No. Every apparent capability traces to architecture-native code, independently-computed telemetry, foundation-model-native context-following, or simple bookkeeping (§13). No evidence was found of the mechanism getting better at anything.

**7. Does it demonstrate transfer?**
No, beyond same-instance reuse of the exact originating episode (§11).

**8. Does it demonstrate measurable competence improvement?**
No — no baseline, no scored batch, no controls exist for any improvement claim (§12).

**9. Does it demonstrate repeated accumulation?**
No — the real data actively contradicts a repeated-accumulation reading: nearly all records cluster in a single incident window, and a real structural bug orphans 17.4% of the mechanism's own recorded data from ever being re-surfaced (§11, §14).

**10. What is the strongest non-learning explanation still consistent with the evidence?**
A hand-authored, static, low-cardinality corrective-note system combined with a live, independently-computed telemetry lookup (§18) — fully consistent with every real data point this mission located, including the one positive behavioral-consequence case, which the counterfeit reproduces exactly.

**11. What single observation would most strongly falsify the learning interpretation?**
A held-out A/B trial (§19) showing the real mechanism performs no better than the §18 counterfeit on novel-phrasing probes of the same 5 subjects — which, given the real evidence already gathered (§8, §17), is this report's own best-supported prediction of what such a trial would find.

**12. What single observation would most strongly support it?**
A held-out A/B trial showing the real mechanism measurably outperforms the §18 counterfeit specifically because of accumulated ledger content (not because of the architecture's raw capacity to inject text at all) — no such trial currently exists.

**13. Does `self_model_claims.py` deserve greater research priority than RiverBrain? Why or why not?**
No, on the evidence gathered this mission. It has a genuinely cleaner evaluator-independence property than RiverBrain's dominant `learn()` path, which is a real and worth-preserving architectural virtue — but its actual empirical track record (zero positive verdicts, single-incident clustering, a real orphaning bug, no transfer, no improvement measurement) is weaker than RiverBrain's own narrow, at-least-once-independently-confirmed detection result (this session's prior archaeology mission's Tier-7 re-derivation). The stronger research priority recommendation, per §15, is `behavioral_state.py`'s already more rigorously *measured* (if narrower-scoped and explicitly non-learning) behavioral-consequence chain, as a methodological template for how to actually test causation properly — not `self_model_claims.py`.

**14. What is the strongest learning claim FeralEcho can make AFTER this audit without exceeding the evidence?**
**FeralEcho has at least one mechanism (`self_model_claims.py`) that persists specific, independently-verified corrections to its own self-knowledge across restarts and genuinely injects them into future relevant conversations, with at least one real, documented case of that injected content measurably changing what was generated — but this mechanism has never been shown, in its full ten-day real production history or in any dedicated experiment, to produce a single confirmed-true claim, to generalize beyond the exact subjects and phrasing it was built to catch, or to improve at anything over time, and its real observed behavior is fully consistent with a fixed, hand-authored corrective-note system that never learns anything at all.** This is a conservative claim, and it is, on the evidence, the correct one.
