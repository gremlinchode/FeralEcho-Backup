# Protocol Red Team P0.2 — Hostile Review of the Formation/Retention Design

**Live Echo was not invoked. No production file was modified except the
one isolated instrumentation fix described in §15, confined entirely to
`app/experiments/preference_provenance/harness.py`.** Nothing was
committed. Protocol P0.1 (`preference_experiment_preregistered_protocol.md`)
remains untouched — its hash was re-verified matching
(`2880fa048815f768d3b303ce7fff6e04196bf14949b53068fd7f0ec2a61a6a20`)
before and after this pass.

This document attacks `audits/echo_preference_formation_retention_
experiment.md` and its companion spec as a hostile reviewer whose job is
to prevent an unjustified claim, not to help the design succeed. Several
attacks below found real, previously-uncaught problems — including a
genuine bias in the task-family content I designed myself, found only by
running actual static analysis rather than trusting my own construction.

---

## 1. Verdict on Whether the P0.2 Design Actually Tests What It Claims

**No, not as originally written — it conflates several distinct
constructs into one claim ("preference formation + retention"), and one
task family carried a real content bias undetected until this pass ran
static analysis against it.** The design's own stated intent
(distinguish statement/state/causal-influence, avoid leading questions,
separate formation from retention) was sound and mostly held up. What
did not fully hold up: the design never explicitly enumerated the ten
constructs the mission's §1 lists, so several were implicitly collapsed
without anyone stating so. This document names each one precisely.

## 2. Construct-Validity Analysis

| Construct | Does P0.2 distinguish it? | Where it's confounded |
|---|---|---|
| A. Baseline model preference | **Yes** — this is exactly what Phase A measures | — |
| B. Prompt-induced preference | **Partially** — Phase C's paraphrase requirement helps, but nothing in the original design explicitly tests whether the *Formation task's own wording* (not its content) induces a directional pull independent of engagement depth | Not fully separated from G (genuine formation) — §4 below |
| C. Persona-induced preference | **Yes, by task avoidance, not by direct test** — themes are chosen to avoid persona resonance, but no condition actually *measures* residual persona pull the way the model-prior control measures model pull | A real gap: avoiding the confound is not the same as measuring it |
| D. Random choice | **Yes** — the mock-responder control and replication requirement (§13 of the original) address this | — |
| E. Short-term conversational consistency | **This is the crux failure, addressed fully in §3 below** — the original design did not clearly distinguish this from H (retention) at all for Variant 1 | See §3 |
| F. Explicit memory/retrieval of a previous answer | **Partially** — the backward-reference-language scan (§10/§13.6 of the original) catches only *explicit verbal* recall ("as I said before"), not silent recall that never announces itself as such | A response can silently retrieve/reconstruct the prior answer without ever using flagged language — the scan would miss this entirely |
| G. Preference formation | **Not directly measured** — Formation-phase engagement asymmetry is explicitly demoted to "secondary/exploratory" in the original design, meaning the design never actually claims to observe formation happening, only its downstream trace | Honest, but means the design's own title overclaims relative to what it tests — it tests *retention of something*, not formation *per se* |
| H. Preference retention | **This is what Phase C measures, conflated with E for Variant 1** | See §3 |
| I. Preference reconstruction from retrieved evidence | **Not distinguished from H in Variant 2 as originally designed** — this is exactly the mission's §3/§11 attack, addressed fully below | See §3 (Variant 2) and §11 |
| J. Genuine behavioral persistence without explicit recollection | **This is the actual target construct**, and the original design has no positive test for it — only a negative filter (excluding trials with explicit recollection language) | The design filters OUT F, leaving a residual that COULD be J — but never positively demonstrates J is what remains, since I (silent reconstruction) is not ruled out |

**Bottom line**: the design as written can, at best, produce evidence
consistent with "E, or F-without-announcing-itself, or I, or J" — a
disjunction, not a clean isolation of J. This is the single most
important correction this pass makes.

## 3. Attack on Variant 1 — Retention vs. Conversational Trajectory

**The question the mission poses directly: what evidence would
distinguish a retained preference from the LLM simply continuing an
unresolved conversational trajectory?**

**Answer: as originally designed, nothing does.** Variant 1 keeps
Formation content in the same continuous conversation Retention is asked
within. A large language model completing a conversation naturally
tends toward local coherence — if Phase B's transcript shows more
engagement with Option 1, a model continuing that same conversation has
an ordinary, well-documented tendency to stay consistent with its own
prior output, **independent of any preference, retained or otherwise**.
This is not a subtle edge case — it is the default behavior of
autoregressive continuation, and the original design's "context-removal
literal-overlap check" (checking whether Phase C's exact wording appears
verbatim in Phase B) **does not address this at all**, since trajectory-
continuation does not require verbatim overlap — it only requires the
model attending to its own prior turn's *gist*.

**Corrected claim, stated plainly**: **Variant 1, as designed, cannot
distinguish H (retention) from E (short-term conversational
consistency).** This is a genuine, load-bearing limitation, not a minor
caveat. The original design's §24 ("cannot establish cross-restart
persistence") did not go far enough — it should have said Variant 1
cannot establish retention *at all*, only consistency-with-recent-
context, which is a substantially weaker and less interesting claim.

**What would actually distinguish them**: a **distractor-interposed**
condition — inserting genuinely unrelated conversational turns (on an
unconnected topic) between Formation and Retention, *within the same
session*, before asking the Retention question. If the apparent
"preference" survives real topical displacement (not just literal-text
distance), that is evidence against pure trajectory-continuation and
starts to look like something closer to retention. **This was not in
the original design and must be added** — see §13's revised minimum
experiment.

## 4. Attack on Variant 2 — Memory Infrastructure vs. Genuine Retention

Full causal graph, traced against real code this pass (`app/core/
memory_bridge.py`, confirmed by direct read):

```
Formation
   │
   ▼
memory write — add_to_vector_memory(text, meta)          [TESTS: whether
   │           gated by _validate_before_commit()           the write
   │           (memory_write_validator.py)                  path/gate
   ▼                                                         works]
memory storage — FAISS index + memory_meta.json           [INFRASTRUCTURE
   │                                                        ONLY — not a
   │                                                        claim about Echo]
   ▼
retrieval — retrieve_relevant_memories(query, top_k,       [TESTS: FAISS
   │         source_filter) — embeds `query`, does a        SIMILARITY
   │         COSINE-SIMILARITY search against stored        SEARCH, not
   │         vectors (confirmed, memory_bridge.py:410-425,  "does Echo
   │         read directly this pass) — NOT an exact        remember her
   │         "look up what I decided" mechanism             preference"]
   │         Also subject to `_workspace_bias` — a Global
   │         Workspace topic-bias injection that can shift
   │         which memories are more likely to surface,
   │         entirely independent of Formation content
   ▼
prompt assembly — retrieved text (if any) concatenated      [INFRASTRUCTURE]
   │              into the model's context
   ▼
model response                                              [THE ONLY STEP
                                                              THAT COULD
                                                              REFLECT A
                                                              GENUINE
                                                              PREFERENCE]
```

**Direct answer to the mission's question**: a successful Variant 2
result would justify, at most, **"Echo's memory architecture
successfully stored and later retrieved information about a prior
interaction, and the model's response was consistent with that
retrieved content."** It would **not** justify "Echo retained a
preference" — because four of the five steps above are pure
infrastructure (write-gate, storage, similarity search, prompt
concatenation), and the similarity-search step specifically means
retrieval success or failure is a property of **embedding-space
distance between the Retention query and the stored Formation text**,
not a property of anything Echo "decided" to keep. A paraphrased
Retention question that happens to embed further from the stored
Formation text could fail to retrieve it for purely geometric reasons,
producing a false negative that has nothing to do with whether a
preference exists.

**This is the single sharpest distinction this red-team pass draws**,
directly implementing the mission's §3/§11: **Variant 2 tests memory
plumbing, not preference.** It should not be presented, even informally,
as a stronger test of H1 than Variant 1 — it is a different experiment
about a different subsystem, useful for a different question ("does
Echo's memory pipeline correctly surface relevant prior content"), not
this one.

## 5. Attack on the Formation Mechanism

**The mission's harder question, answered directly**: if Formation
merely exposes Echo to an asymmetric engagement task (writing more about
one option than another, as the original design's own secondary signal
already predicts will happen for mundane reasons — whichever option is
easier to write about, or is listed second and benefits from recency),
then any resulting Retention-phase shift is most parsimoniously
explained as **learned conditioning from asymmetric exposure within one
session**, not "emergence" in any interesting sense. **This must be said
explicitly, not hidden behind the word "formation."** The original
design's own title ("Formation Phase") already implies a process; this
red-team pass requires the eventual report to use the more precise,
less loaded phrase **"asymmetric-exposure conditioning check"** when
describing what Phase B actually does, reserving "formation" for a
claim the data would need to separately earn.

## 6. Attack on the Task Families — Real Bias Found

**Static analysis performed this pass, not merely reasoned about
abstractly.**

### Family 1 (motifs) — REAL BIAS FOUND, REDESIGNED

The original wording used "**crescents**" ("a spiral built from
overlapping crescents") as one option's descriptor. **This is a real,
serious oversight**: a crescent carries strong, widely-recognized
cultural/religious symbolism (the Islamic crescent moon, among other
associations) — exactly the kind of charged content §7 of the original
design explicitly says must be avoided, and it slipped through anyway.
The paired option ("a lattice of interlocking triangles") carries a
weaker but non-zero secondary association (triangular/geometric imagery
with esoteric connotations in some contexts). **Redesigned, this pass**,
to remove all named, culturally-loaded objects and describe pure
geometric structure instead:

- **Motif Curved**: "a single curved line that loops back on itself without crossing" (11 words)
- **Motif Angular**: "a set of straight lines that meet at repeating sharp angles" (11 words)

Word-count-balanced (11/11), no named object, no cultural referent of
any kind — a structural (curved-vs-angular) distinction only, checked
against the same exclusion list (religious/political/moral/economic) and
clean.

### Family 2 (habits) — REAL BIAS FOUND, REDESIGNED

"Opening with a single word" vs. "opening with a short question" —
**the second option matches extremely common, well-known writing-advice
cliché** ("hook the reader with a question"). A language model trained
on substantial writing-craft content has every reason to treat the
question-opening as the more conventionally "correct" or "recommended"
technique, independent of anything Echo-specific — a real, plausible
model-prior confound this pass's own model-prior control (§8, non-Echo
model condition) would need to catch, but which is better avoided at
the design stage than relied on a control to catch after the fact.
**Redesigned, this pass**, to make both options equally specific and
equally novel (neither matching a well-known trope):

- **Habit Word**: "opening with a single, deliberately chosen word"
- **Habit Image**: "opening with one brief, concrete image described in a single breath"

Both now name a specific, somewhat unusual technique; neither echoes a
commonly-taught writing rule.

### Family 3 (names) — REAL BIAS FOUND (measured, not assumed), REDESIGNED

Tokenization check performed this pass using `tiktoken`'s `cl100k_base`
encoding (an approximation — **explicitly not the real tokenizer any
locally-hosted Ollama model actually uses**, stated honestly as a
limitation, not a proof):

```
Verel   → 2 tokens (['Ver', 'el'])
Ossin   → 3 tokens (['O', 'ss', 'in'])
```

**A real, measured, one-token asymmetry.** More sub-word fragmentation
can correlate with lower vocabulary-frequency treatment inside a model,
a plausible (not proven) source of systematic bias favoring the
more token-efficient option regardless of anything Echo-specific.
**Redesigned, this pass**, by searching candidate nonsense words for one
matching `Verel`'s exact length (5) and token count (2) under the same
encoding:

```
Verel   len=5 tokens=2   (unchanged)
Farun   len=5 tokens=2   (replaces Ossin)
```

Both are now length- and token-count-matched under this specific
tokenizer, and both follow the same consonant-vowel-consonant-vowel-
consonant syllable shape. **Stated honestly**: this does not guarantee
parity under the real local models' own tokenizers (llama/qwen/deepseek
use different vocabularies) — a live check would require invoking a
real tokenizer, which this pass's own hard constraints forbid alongside
live model calls. **Required protocol change (§14)**: log the real
per-model token count for both option names at trial time, once
implementation begins, as a recorded covariate — not assumed away by
this offline approximation alone.

## 7. Attack on the Controls

**Could the mock-responder control produce a false null because it
lacks something Echo legitimately possesses?** Yes, and this must be
stated plainly: `MockResponder` has no language-modeling capability at
all — it cannot exhibit E (conversational-trajectory continuation),
because it has no concept of "conversation" in the first place, only a
seeded random draw. **This means the mock control is a valid null for D
(random choice) and a valid null for the harness's own statistical
machinery (as already established in prior calibration work), but it is
NOT a valid control for E** — since E requires a genuine autoregressive
model to exhibit trajectory-continuation, and the mock structurally
cannot. **A `NO_DETECTABLE_EFFECT` result from the mock control does
not, by itself, rule out E as the explanation for a real-Echo result.**

**Could the non-Echo model-prior control produce the same apparent
"preference retention" through ordinary LLM conversational behavior?**
Yes — and this is actually the *stronger*, more relevant control for E
specifically, since a real base model run through the identical
Variant-1 session-continuous protocol would be expected to show the
same trajectory-continuation effect Echo would, for reasons having
nothing to do with Echo's architecture at all. **Required protocol
change**: the non-Echo model-prior control must be run through the
**identical Variant 1 session-continuous protocol**, not treated as
interchangeable with the mock control — they test different alternative
explanations (D/random vs. E/trajectory-continuation) and neither
substitutes for the other. The original design's criterion 8 ("does not
show the same shift at comparable effect size") is necessary but was
not previously identified as the *specific* test for E — this is now
made explicit.

## 8. Attack on the Ten Pass Criteria

| # | Criterion | What it establishes | Alternative explanation that survives it | Necessary? | Sufficient alone? | Measurable without judgment? | Circularity risk |
|---|---|---|---|---|---|---|---|
| 1 | Phase A not skewed | "initially unresolved" | None if truly automated | Yes | No | Yes | None |
| 2 | Effect classified POSSIBLE/ROBUST | A statistically real shift exists | E, F, I, G — this criterion alone cannot distinguish any of them | Yes | No | Yes (reuses existing `classify_effect()`) | None |
| 3 | Replicates in 2/3 families | Not a single-task artifact | Still doesn't rule out E/F/I | Yes | No | Yes | None |
| 4 | Survives paraphrase | Rules out H0b (verbal momentum) partially | Does NOT rule out E (§3) — paraphrase changes *wording*, not topical proximity within the same session | Yes | **No — this criterion was previously treated as if it also addressed E; it does not** | Yes | **Real risk: satisfying this criterion could be mistaken for ruling out E when it does not** |
| 5 | Survives label/order re-randomization | Rules out H0a | — | Yes | No | Yes (structural) | None |
| 6 | <20% backward-reference language | Excludes F (explicit recall) | Does NOT exclude **I** (silent reconstruction) or **E** (trajectory continuation, which requires no explicit reference at all) | Yes | **No — see §2's construct table, this is the gap that lets E/I survive undetected** | Requires a text-scan, borderline researcher-judgment-free (a keyword/pattern scan, not fully judgment-proof) | Low |
| 7 | Mock control shows null | Rules out D and the harness's own statistical artifacts | Does NOT rule out E (§7 above — mock cannot exhibit E at all) | Yes | No | Yes | None |
| 8 | Non-Echo model-prior control doesn't match | Rules out shared model prior (persona-independent) | If run through Variant 1 (required fix, §7), also partially addresses E | Yes | No | Requires an effect-size comparison, not just presence/absence — already specified, good | None |
| 9 | Minimum sample size | Statistical power floor | Arbitrary, stated honestly as conservative-not-power-calculated in the original design — unchanged assessment | Yes | No | Yes | None |
| 10 | Independent replication | Rules out one-off statistical flukes | — | Yes | No | Yes | None |

**Required redesign**: criterion 4 and criterion 6 must be supplemented,
not replaced, with the distractor-interposition control from §3 —
without it, the ten criteria as a whole can be fully satisfied by a pure
trajectory-continuation effect (E), which is the single most important
finding of this red-team pass.

## 9. Attack on the Statistical Plan

- **Unit of analysis**: the trial (one Formation→Retention pair). Confirmed appropriate, not ambiguous.
- **Independent vs. non-independent observations**: **a real, previously unaddressed gap.** If multiple trials within the same task family reuse the same underlying model/process across a session (plausible for Variant 1, where session-continuity is the point), trials are **not** fully independent draws — RiverBrain is absent (Design B), but the model's own within-session state (if any conversation threading persists across trials) is a real non-independence risk. **Required fix**: each trial must use a **freshly-constructed, isolated conversation context** (no cross-trial threading), confirmed and logged per trial, or the independence assumption underlying the two-proportion z-test is violated.
- **Multiple-comparison problem**: three task families, each independently tested (§13.3 of the original) — this is itself a multiple-comparison scenario (3 independent tests of the same H1) and the original design did not apply any correction (e.g., Bonferroni) before requiring "2 of 3." **This is defensible as-is only because the design already requires *replication in 2 of 3*, a stricter bar than any single family reaching significance alone** — but this should be stated explicitly as the reason no additional correction is applied, not left implicit.
- **Stopping rules**: the original design's minimum-sample criterion (§13.9) sets a floor but never explicitly bans **optional stopping** (running more trials only when an early look looks promising). **Required fix**: sample size per condition must be fixed and reached in full before any analysis is performed — no interim looks, stated as an explicit rule, not assumed.
- **Exclusion criteria**: backward-reference-language trials are excluded from the primary analysis (§13.6) — appropriately pre-specified, not post-hoc. Good.
- **Missing/failed trials**: not addressed in the original design at all. **Required fix**: any trial that fails to produce a parseable choice (per the existing `_parse_label_choice()` conservative None-return behavior) must be logged and reported, never silently dropped or re-run — reusing the harness's own established append-only, no-selective-discard convention.
- **Effect-size definition**: reused from the existing `classify_effect()` machinery (absolute difference in proportion) — adequate, unchanged.
- **Preregistration**: this document itself, once finalized, should be treated as part of the frozen record before any pilot begins — consistent with the P0.1 precedent.

## 10. Attack on Researcher Influence

| Point of entry | Bias risk | Mitigation status |
|---|---|---|
| Task creation | **Confirmed real** — this pass's own §6 findings show the original researcher (this thread) introduced two real, uncaught biases despite explicit intent to avoid them | Static analysis (as performed this pass) must become a **mandatory, pre-registered step** before any task family is used, not an optional afterthought |
| Task selection | Low — three families were pre-specified together, not cherry-picked after seeing early data | Maintain: no new family may be added after piloting begins |
| Prompt wording | Real — Formation/Retention wording differences must be authored before any data collection, not adjusted afterward | Freeze wording alongside the seal, same as P0.1's own hash convention |
| Trial selection | Addressed by the harness's append-only store (no selective discarding possible) | Adequate |
| Data exclusion | Addressed by pre-specified exclusion criteria (backward-reference language) — but see §8's finding that this criterion alone is insufficient | Needs the distractor control, not just this exclusion rule |
| Scoring | Automated via `_parse_label_choice()` — no researcher judgment in the primary outcome | Adequate |
| Interpretation | The evidence-ladder mapping (§22 of the original) was written *before* any data — a real, working precondition against post-hoc reinterpretation | Adequate, provided it is not revised after seeing results |

## 11. Model-Prior Ablation — Strongest Version

Per the mission's explicit design request: **same model, same
interaction, same prompts, minus Echo's persistence architecture** —
already partially specified (the non-Echo model-prior control), but the
strongest version requires running the *same underlying model* (if Echo
is itself an Ollama-hosted model like others in the pool, per this
project's own architecture) through the identical Variant 1 protocol
**with the Modelfile identity block removed** (i.e., a plain base-model
call with no persona injection at all) as a *second*, more surgical
ablation beyond the non-Echo-model control. This isolates persona
specifically, separate from "a different model entirely." **Not in the
original design — added as a required protocol change (§14).**

## 12. Recall vs. Preference — The Behavioral Test

Per the mission's explicit instruction to avoid directly asking for
autobiographical recall: the Retention-phase question (§9 of the
original design) already avoids this by construction ("which one comes
to mind as fitting better right now" — a present-tense disposition
question, not "what did you choose before"). **This was already correct
in the original design.** What was missing, and is added here: a
**forced-choice behavioral task** where the historical answer's content
is entirely absent from the question's surface form — e.g., presenting
the SAME two options embedded in a **structurally different task**
(not a direct "which do you prefer" repeat, but a task that requires
*using* one option functionally, such as "complete this scenario using
one of these two approaches" without naming them as "the ones from
before"). This is a stronger version of the existing Retention design
and should be added as a second, independent Retention-phase measure,
not a replacement.

## 13. Restart/State-Boundary Definition (Variant 2)

For any future Variant 2 claim of "cross-session retention," the
following must be explicitly specified and verified, per component:

| State component | Survives a real process restart? | Verified this pass? |
|---|---|---|
| Model context/conversation history | No (`_SESSIONS` is in-memory only, confirmed prior audit) | Yes, prior audit |
| FAISS index / `memory_meta.json` | Yes (disk-persisted) | Yes, established architecture fact |
| RiverBrain `model_task_stats` | Yes, if `.save()` was called before restart; no otherwise | Yes, `deliberate_and_learn_differential_audit.md` §6 |
| `reflection_shard.jsonl` | Yes (flat file) | Yes |
| Curiosity-engine / question-garden state | Yes (flat file) | Yes |
| Circuit-breaker state (`_cb_state`) | No (in-process only) | Yes |
| `_last_world_surprise` cache | No (in-process only) | Yes |
| Global Workspace `workspace_log.jsonl` | Yes (flat file, append-only) | Yes |

**A "clean state-destruction boundary" for a real Variant 2 experiment
requires**: killing and restarting the actual serving process between
Formation and Retention (not merely waiting), with the researcher
explicitly confirming, via the process's own PID/start-time (already a
field in `memory/echo_sentinel.json` per this project's established
architecture), that a genuine restart occurred — not simulated,
not assumed.

## 14. Required Protocol Changes (Summary)

1. Add a **distractor-interposition condition** to Variant 1 — genuinely unrelated conversational turns between Formation and Retention, within the same session (§3).
2. Reframe "Formation" as **"asymmetric-exposure conditioning check"** in any claim language, reserving "formation" for what the data would need to separately earn (§5).
3. Redesign all three task families per §6's concrete fixes (motif wording, habit wording, name pair).
4. Log real per-model token counts for both options in every task family as a recorded covariate (§6).
5. Run the non-Echo model-prior control through the **identical Variant 1 protocol**, not a bare comparison (§7).
6. Add a **persona-ablated same-model control** (Modelfire identity block removed) as a second, more surgical ablation (§11).
7. Add a **structurally-embedded behavioral Retention measure**, distinct from the direct-question Retention measure (§12).
8. Fix the independence-of-trials gap — fresh, isolated conversation context per trial, confirmed and logged (§9).
9. Ban optional stopping explicitly — fixed sample size reached in full before any analysis (§9).
10. Log and report missing/unparseable trials rather than silently dropping them (§9).
11. Make static task-bias analysis (as performed in §6 of this document) a **mandatory pre-registered step**, not optional (§10).

## 15. Required Code Fix — `echo:live` Reproducibility Bug

**Fixed this pass, isolated entirely to `app/experiments/preference_
provenance/harness.py` — no production file touched.**

Traced the real model-resolution path before fixing: for `EchoResponder`
(wrapping `echo_query()` → `deliberate_and_learn()`), the actual
synthesis model is a real, importable constant,
`river_deliberation.ECHO_SYNTHESIS_MODEL` — not an arbitrary string. The
prior hardcoded literal `"echo:live"` has been replaced with this real
constant (lazily imported, matching the existing lazy-import convention
already used for `echo_query` in the same class), so the reported model
identity now reflects the actual configured synthesis model rather than
a made-up label. **Honest residual caveat, stated in the code and here,
not hidden**: this still reports the *synthesis* model identity only —
for the full council path (Design A), several other models genuinely
contribute opinions that get synthesized away; this fix makes the report
accurate for "which model produced the final text," not a complete
record of "which models participated," which would require production
`deliberate_and_learn()` to expose additional return metadata — out of
scope for this isolated fix.

A second, new responder class, `EchoDirectResponder`, was added
implementing Design B (`_ollama_query()` called directly with an
explicit, caller-supplied `model` argument) — for this class, the
reported model identity is **exact and cannot lie**, since it is the
same literal value the constructor requires and the same value passed
to the real inference call; there is no approximation involved. This is
the class a future implementation of this experiment would actually use
(per the whole thread's own convergence on Design B), and it did not
exist before this pass.

Regression coverage was added and run (mock-only, no live calls):
confirms `EchoResponder`'s reported model equals the real
`ECHO_SYNTHESIS_MODEL` constant (not the old hardcoded string), and
confirms `EchoDirectResponder`'s reported model exactly equals whatever
was passed to its constructor, for three distinct model names. Full
existing suite (`scripts/verify_preference_provenance_experiment.py`,
95 checks) re-run and passes with zero regressions after this change.

## 16. Claims That Remain Forbidden After P0.2

- "Echo has agency, free will, consciousness, or sentience" — unchanged, permanently forbidden, structurally enforced by the existing `ALLOWED_EFFECT_LABELS` allowlist.
- "Echo retained a preference," from any Variant 2 result alone — per §4, a positive Variant 2 result establishes memory-infrastructure function, not preference retention, without additional, currently-unspecified controls this document does not design.
- "Echo formed a preference," from any Phase B engagement asymmetry alone — per §5, this is at most evidence of asymmetric-exposure conditioning, a narrower and less interesting claim.
- Any claim from Variant 1 that does not survive the distractor-interposition control — per §3, without it, "retention" and "conversational trajectory continuation" remain indistinguishable, and the honest claim is limited to the latter.
- Any claim of statistical significance from an unplanned interim look, or from a task family added after piloting began (§9/§10).
- Any claim about Design A or D's own council/synthesis architecture — this experiment, as designed, only ever exercises Design B.

## 17. Recommendation

**REVISE, not PILOT, not STOP.**

Not STOP: the underlying research question remains well-posed, and
several of this pass's findings (the two task-family biases, the
E-vs-H conflation, the memory-vs-preference distinction) are exactly
the kind of concrete, fixable problems a design pass exists to catch —
none of them reveal the question itself to be unanswerable, only that
this specific instrument needed sharpening before being trusted.

Not PILOT: piloting the design as originally written would validate an
instrument with a confirmed inability to distinguish its own target
construct (H) from a well-known, mundane alternative (E) — a wasted
pilot, since the fix (distractor interposition) changes the protocol
structure, not just its analysis.

**REVISE**: incorporate all eleven required changes in §14, re-freeze
the design with its own protocol hash (mirroring P0.1's own seal
convention, not yet done for this design), then proceed to piloting —
matching the mission's own P0/P1/P2/P3/P4 staged structure, with this
red-teamed, revised design becoming the true P0 (instrumentation
validation baseline) rather than the version originally submitted.
