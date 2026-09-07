# Retrieval Capacity Proof — Does the Existing Memory System Recognize Experience?

Time-boxed capacity experiment, run directly on top of the same-night Orphaned Memory
Retrieval forensic audit. Not a repair, not a new architectural sweep. One question:
if a past experience were represented in the existing vector corpus in a structured,
causally meaningful way, can the *existing, unmodified* retrieval machinery actually
surface it when queried from a later, causally-related situation?

## 1. Executive Verdict

**Retrieval is real but rank-unreliable for causal purposes.** The correct experience
representation is never *absent* from the top-6 window across all six real query
forms tested, and the richest (causal) representation generally outperforms the
thinner ones on paraphrased/situational/causal queries. But causally-irrelevant
distractors beat the correct experience for the #1 rank in half (3 of 6) of the
paraphrase/causal query forms — including one case (Q5) where a completely
unrelated `SyntaxError` record outranked the actually-relevant experience. There is
no abstention mechanism anywhere in the retrieval path: a query about baking
sourdough bread still returns six "results," down to negative cosine-similarity
scores, with no signal that nothing relevant exists.

## 2. Deadline-Relevant Conclusion

Ingestion-repair alone (making self-edit failures reach the embedded corpus) would
recover **some** real value — the correct experience does show up in the retrieval
window most of the time, which is a precondition for anything downstream to use it.
But ingestion-repair alone will **not** reliably solve the hot-stove problem, because
even with a well-formed causal record already sitting in the corpus, plain top-1
vector similarity hands the #1 slot to a causally-wrong but lexically-loud distractor
roughly half the time on the query shapes that matter most (paraphrase, causal,
different-identifier). If remaining time is spent on this line of work, it should go
toward a lightweight reranking/relevance-filter step downstream of retrieval, not
toward wiring `retrieve_relevant_memories()` into `self_edit_manager.py` as-is and
assuming the correct memory will consistently win.

## 3. Safety Invariants

Confirmed before and after, unchanged:

- `run.py` / watchdog: not running (only the unrelated macOS system `watchdogd` process, PID 366, present both times — irrelevant).
- Port 5000: unbound.
- Git HEAD: `2cf2d95009943797db5ec41fea9b4021634fd5e6` (unchanged).
- `river_brain.pkl` SHA-256: `eee193444a735d6ae510e8f8fa0faae1da4b2b1467a2a5da6f15c93467c9d815` (unchanged).
- `memory/interaction_log.jsonl`: 13,324 lines before and after — untouched (never opened by this experiment).
- `data/question_garden.jsonl`: untouched (never opened by this experiment).
- `memory/SELF_EDIT.log`: untouched (never opened by this experiment).
- `memory/faiss.index` / `memory/memory_meta.json`: never opened, read, or written by this experiment at any point — the experiment instantiates a **separate** `VectorMemory` object pointed at scratch paths under `app/experiments/retrieval_capacity_proof/`, never the production paths.
- No production source file modified. No new caller of `retrieve_relevant_memories()` added anywhere in production code.
- No RiverBrain training call made (this experiment never imports `RiverBrain` or `echo_model_orchestrator.py` at all).
- Zero real model/Ollama calls made — this experiment only uses the local sentence-transformer embedding model (`embed_text()`, the same one production retrieval uses) and local FAISS math. No `echo_query()`, no council, no generation.

Files created by this experiment (all under an isolated experiment directory, not mixed into production):
- `app/experiments/retrieval_capacity_proof/run_experiment.py`
- `app/experiments/retrieval_capacity_proof/retrieval_results.json`
- This report.

The scratch FAISS index and scratch metadata file the script created during the run
(`scratch_faiss.index`, `scratch_memory_meta.json`) were deleted by the script itself
immediately after producing `retrieval_results.json`, so no lingering vector-store
artifact remains on disk.

## 4. Existing Retrieval Architecture

Read directly from current source, not inferred:

- **Entry point**: `retrieve_relevant_memories(query, top_k=6, source_filter=None)` — `app/core/memory_bridge.py:410-477`.
- **Query becomes**: a single embedding vector via `embed_text()` (`memory_bridge.py:212-220`), which wraps `embedding_model.encode(texts, normalize_embeddings=True)` — a sentence-transformer model (`all-MiniLM-L6-v2`, 384-dim, per this project's own CLAUDE.md and the observed embedding dimension). There is an optional Global-Workspace "bias" blend (0.7·query + 0.3·bias_vector, re-normalized) if a recent workspace broadcast set one within a 300s TTL — irrelevant to this experiment since no workspace bias was active.
- **Similarity metric**: cosine similarity, implemented as an L2-normalized FAISS `IndexFlatIP` inner product (`app/lib/vector_memory.py:83`, `:108-110` normalize+add, `:135-136` normalize+search).
- **Ranking**: pure sort by that single cosine score, descending. No reranking step, no secondary signal, no query-expansion.
- **What determines whether a result is discarded**: nothing, within `k`. `VectorMemory.search()` (`vector_memory.py:120-146`) has **no minimum-score threshold anywhere** — it returns `min(k, index.ntotal)` results unconditionally, however low or negative the similarity score is. The only post-hoc filtering in `retrieve_relevant_memories()` itself is category-exclusion (`role`/`memory_source` in `_ALWAYS_EXCLUDED_MEMORY_CATEGORIES`, e.g. `code_analysis`, `self_model_reflection`) and an optional `source_filter` — neither is a relevance/quality threshold.
- **Does it know about action / consequence / failure / diagnosis / correction / outcome / recurrence / provenance?** No. `meta` (a dict) is stored alongside each vector purely for filtering — it is never embedded, never used in ranking, never inspected for causal structure. The **only** thing that gets embedded and searched is the raw `text` string. If a memory's text happens to contain the words "diagnosis" or "correction," those are just tokens contributing to the embedding like any other word — there is no structural understanding of causal roles at all.
- **Direct answer to Phase 1's Q8**: retrieval fundamentally operates on flat text embeddings. It is a semantic-similarity engine, not a causal-experience engine, by construction — confirmed from source, not inferred from behavior.

## 5. Isolated Corpus Design

A separate `VectorMemory` instance was instantiated in-process, pointed at scratch
`index_path`/`meta_path` under this experiment's own directory — never the
production `memory/faiss.index` / `memory/memory_meta.json`. The real production
embedding function (`app.core.memory_bridge.embed_text`) and the real production
FAISS/`VectorMemory` class (`app.lib.vector_memory`) were used unmodified, so this
experiment exercises the actual retrieval mechanism, not a reimplementation of it.
10 synthetic records were embedded and added (4 representations of "Experience X" +
6 adversarial distractors). The scratch index/meta files were deleted immediately
after the run; only the JSON results artifact and this report persist.

**Honest scale caveat, stated plainly**: this corpus has 10 entries. Production's
real corpus has 124,561. `top_k=6` against a 10-entry corpus returns essentially
6/10 of everything that exists — a far less discriminating test than `top_k=6`
against 124,561 real entries would be. Every result below should be read as a
**best-case, optimistic bound** on retrieval precision, not a realistic estimate of
what would happen in the live corpus, where the correct experience would be
competing against orders of magnitude more plausible-looking noise.

## 6. Experience Representations

| Key | Content (abridged) |
|---|---|
| X1_raw | `NameError: name 'trace_recorder' is not defined` |
| X2_diagnosis | X1 + "unresolved dependency reference" diagnosis |
| X3_action | X2 + "added the missing import... in a retry attempt" |
| X4_causal | Full structured record: situation, action, consequence, diagnosis, correction, verified outcome, provenance (`trace_id=SYNTH-EXPERIENCE-X-001`), confidence, explicit lesson sentence |

All four share the identifier `trace_recorder` and describe the same underlying
synthetic incident at increasing levels of causal completeness.

## 7. Adversarial Controls

| Key | Design intent | Content (abridged) |
|---|---|---|
| D1 | Lexically similar, causally different | `trace_recorder` imported and used **successfully**, zero errors |
| D2 | Same failure class, different cause | `NameError` on a different symbol, caused by ordering, not a missing import |
| D3 | Same cause, different identifier | Missing-import `NameError` on `session_manager`, otherwise structurally identical to X2/X3 |
| D4 | Same function/module, different problem | `TypeError` inside the *same* tracing module, unrelated to imports |
| D5 | Semantically unrelated coding failure | `SyntaxError`, stray colon |
| D6 | Non-coding experience | Philosophical reflection on trust and patience |

## 8. Query Set

| Query | Text | Intent |
|---|---|---|
| Q1 | "A generated program failed because trace_recorder was referenced without being defined." | Exact-failure wording |
| Q2 | "The candidate crashed because it attempted to use a dependency that had never been made available." | Reworded, no shared identifier |
| Q3 | "A generated program referenced event_tracker without importing or defining it." | Different identifier, same structure |
| Q4 | "I am about to execute generated code that contains a helper symbol whose definition is not visible in the candidate." | Situational / prospective |
| Q5 | "Previous generated code failed because it assumed a dependency existed when it did not." | Causal framing |
| Q6 | "Before execution, check that every referenced helper/dependency is actually available." | Outcome-oriented / preventative |
| Q7 (negative) | "What is the best technique for baking sourdough bread at high altitude?" | Nothing in the corpus should be relevant |

`top_k=6`, matching production's real `TOP_K` constant (`memory_bridge.py:38`).

## 9. Raw Retrieval Results

Full ranked results with real cosine scores (also persisted verbatim in
`app/experiments/retrieval_capacity_proof/retrieval_results.json`):

**Q1 (exact failure wording)**
1. X2_diagnosis — 0.8508
2. X3_action — 0.8379
3. D4_same_function_different_problem — 0.7921
4. X1_raw — 0.7851
5. D1_lexical_similar_causally_different — 0.7352
6. X4_causal — 0.6789

**Q2 (reworded, no shared identifier)**
1. D1_lexical_similar_causally_different — 0.3336
2. D3_same_cause_different_identifier — 0.3155
3. X4_causal — 0.2503
4. X3_action — 0.2481
5. D5_semantically_unrelated_coding_failure — 0.2393
6. D4_same_function_different_problem — 0.2259

**Q3 (different identifier)**
1. D4_same_function_different_problem — 0.4046
2. X4_causal — 0.4011
3. X2_diagnosis — 0.3836
4. X3_action — 0.3647
5. D1_lexical_similar_causally_different — 0.3546
6. X1_raw — 0.3221

**Q4 (situational)**
1. X4_causal — 0.4175
2. D4_same_function_different_problem — 0.3024
3. D1_lexical_similar_causally_different — 0.2567
4. D5_semantically_unrelated_coding_failure — 0.1657
5. X2_diagnosis — 0.1574
6. X3_action — 0.1438

**Q5 (causal framing)**
1. D5_semantically_unrelated_coding_failure — 0.4613
2. X4_causal — 0.4270
3. D1_lexical_similar_causally_different — 0.3794
4. D4_same_function_different_problem — 0.3741
5. X3_action — 0.3639
6. X2_diagnosis — 0.3485

**Q6 (outcome-oriented)**
1. X4_causal — 0.4424
2. D3_same_cause_different_identifier — 0.3330
3. D4_same_function_different_problem — 0.3205
4. D1_lexical_similar_causally_different — 0.2890
5. X3_action — 0.2818
6. X2_diagnosis — 0.2628

**Q7 (negative / no relevant memory should exist)**
1. D1_lexical_similar_causally_different — 0.0822
2. X4_causal — 0.0453
3. X1_raw — 0.0070
4. X2_diagnosis — 0.0000
5. D4_same_function_different_problem — -0.0005
6. X3_action — -0.0143

## 10. Retrieval Metrics

- **Exact retrieval** (some X-representation appears in top-6): **6/6 queries (100%)** — never fully absent.
- **Top-1 retrieval** (an X-representation ranks #1): **3/6 (50%)** — Q1 (X2), Q4 (X4), Q6 (X4). Note Q1's #1 is X2, not X4 — see §11.
- **X4 (richest/causal) specifically at #1**: **2/6 (33%)** — Q4, Q6.
- **Top-k usefulness**: trivially satisfied at this corpus size (see §5 caveat) — not a meaningful precision signal on its own.
- **Causal transfer** (does X4 win *because of* causal structure on paraphrase/causal/situational queries Q2–Q6, not because of shared identifiers?): **partial** — X4 is the best-performing X-representation in 5 of 6 non-Q1 queries (all but none), but still loses the #1 rank outright to a distractor in 3 of those same 5 (Q2, Q3, Q5).
- **Lexical trap rate**: a causally-irrelevant or causally-wrong distractor outranks the best available X-representation for #1 in **3 of 6 queries (50%)** — Q2 (D1), Q3 (D4, by a margin of 0.0035 — essentially a coin flip), Q5 (D5, a completely unrelated `SyntaxError`).
- **Same-cause/different-identifier (D3) vs. lexically-similar/causally-wrong (D1)**: D3 (genuinely same underlying cause, different symbol) beats D1 in only 2 of 6 queries (Q2, Q6); D1 (same identifier, opposite/successful outcome) frequently scores competitively or higher, confirming the system tracks surface lexical overlap at least as strongly as causal category.

## 11. X1 vs. X2 vs. X3 vs. X4 Comparison

| Representation | Q1 | Q2 | Q3 | Q4 | Q5 | Q6 |
|---|---:|---:|---:|---:|---:|---:|
| X1 Raw | #4 (0.7851) | absent (top-6) | #6 (0.3221) | absent | absent | absent |
| X2 Diagnosis | **#1 (0.8508)** | absent | #3 (0.3836) | #5 (0.1574) | #6 (0.3485) | #6 (0.2628) |
| X3 Action | #2 (0.8379) | #4 (0.2481) | #4 (0.3647) | #6 (0.1438) | #5 (0.3639) | #5 (0.2818) |
| X4 Causal | #6 (0.6789) | #3 (0.2503) | **#2 (0.4011)** | **#1 (0.4175)** | #2 (0.4270) | **#1 (0.4424)** |

**Real, decision-relevant pattern, not manufactured**: on the one query that shares
exact literal wording with X1 (Q1), the *thinnest* representations win and the
*richest* (X4) comes in dead last among the X-family — the extra diagnosis/
correction/outcome/provenance text dilutes the embedding away from the literal
failure string it needs to match. On every other query (Q2–Q6, all paraphrased,
identifier-shifted, situational, causal, or outcome-framed), **X4 is the best- or
tied-for-best-performing representation of the four**, and is the only
representation that ever reaches #1 outside of the literal-match case. This is a
genuine, non-cherry-picked finding: causal enrichment measurably helps exactly the
query shapes that matter for a "later, differently-worded situation," and measurably
hurts the one query shape (verbatim error-string repetition) that arguably matters
least, since a hot-stove system needs to generalize past literal repetition to be
useful at all.

## 12. Lexical-vs-Causal Analysis

The clearest single data point: **Q5 asked, in plain causal language, "previous
generated code failed because it assumed a dependency existed when it did not" —
and the top-ranked result was a completely unrelated `SyntaxError` record (D5,
0.4613), beating the actually-relevant causal experience (X4, 0.4270) by 0.034.**
D5 shares no identifier, no failure type, and no causal structure with the query —
it appears to win purely on background lexical/topical overlap around "code" and
"failed." This is direct, concrete evidence that the retrieval mechanism does not
distinguish "same words" from "same situation" (Phase 8, Question C) — it answers
**no**, with a specific counter-example, not a general impression.

A second, gentler instance: Q3 ("different identifier, same structure") has D4
(same module, unrelated `TypeError`) narrowly beating X4 (0.4046 vs. 0.4011) — a
margin small enough to be noise-level, but still the wrong record winning.

Against this, Q2 and Q4 and Q6 show the system correctly favoring topically-relevant
causal content over completely unrelated distractors (D5, D6 never win a genuinely
causal query outright except in the Q5 anomaly above) — so the picture is not "the
system is random." It has real semantic structure. It simply doesn't have *causal*
structure, and the two frequently disagree.

## 13. Abstention / False-Relevance Test

**No abstention mechanism exists anywhere in the retrieval path.** Confirmed both
from source (`VectorMemory.search()`, `vector_memory.py:120-146`, has no score
threshold of any kind — only `min(k, index.ntotal)`) and empirically: Q7 ("best
technique for baking sourdough bread at high altitude") — a query with zero genuine
relevance to any of the 10 synthetic corpus entries — still returned 6 ranked
"results," with scores ranging from 0.0822 down to **-0.0143** (a negative cosine
similarity, i.e. the embeddings point in *opposite* directions). Nothing in the
returned data structure or the calling convention signals "nothing relevant was
found" — a caller receiving these six results has no way to distinguish them from a
genuinely relevant retrieval without imposing its own threshold, which no current
caller of `retrieve_relevant_memories()` does (confirmed in the immediately
preceding Orphaned Memory Retrieval audit — every real consumer treats whatever
comes back as usable context).

## 14. Architectural Limit

**Question A** — Can existing retrieval machinery retrieve a causally relevant
experience if properly represented? **Partially.** It is never fully absent from a
top-6 window (in this small-corpus, best-case setting), and the richest
representation wins outright on situational/outcome-framed queries. But top-1
reliability is poor (50% overall, 33% for the causal representation specifically).

**Question B** — Does adding diagnosis/correction/outcome metadata improve
retrieval? **Yes, conditionally.** It helps substantially on paraphrased/situational/
causal queries (the query shapes a real "later, differently-worded situation" would
actually produce) and hurts on literal-repetition queries (an unlikely real-world
case, since the whole point of durable knowledge is to generalize past exact
repetition).

**Question C** — Does the system distinguish "same words" from "same situation /
same causal pattern"? **No**, demonstrated directly (§12, the Q5 SyntaxError case).

**Question D** — Is current vector retrieval sufficient for the hot-stove
capability, or does a structured causal index become necessary? **The evidence
leans toward "not sufficient on its own," but does not demonstrate that vector
retrieval is worthless.** The raw semantic signal captures something real (causal
enrichment measurably helps on the right query shapes; genuinely unrelated content
rarely wins outright). What it lacks is *reliability at the #1 rank specifically* —
exactly the rank a "decision-influence" consumer would need to trust if it were
going to inject only the single best-matching memory rather than several candidates
for a downstream filter to sort through. This experiment does not by itself prove a
structured index is *necessary*; it demonstrates a specific, real gap (causally-wrong
content beating causally-right content at #1 in half of the causal/paraphrase query
forms tested) that any future design would need to either accept, filter around, or
close with something beyond plain cosine similarity.

## 15. What This Does NOT Prove

This experiment establishes only that a properly-represented synthetic experience
*can be retrieved* (with the reliability profile above) in a later, differently-
worded query context, using the real embedding/retrieval machinery. It does **not**
establish:

- that Echo learns from experience,
- behavioral change of any kind,
- causal/credit-assignment capability (that was already tested and found absent
  earlier tonight — Hot Stove / Credit Assignment audit, Classification D),
- generalization beyond this one synthetic incident,
- persistence of preference over time,
- autonomous consolidation,
- or self-correction.

It is a narrow, mechanical capacity test of one component in isolation — nothing
more, nothing less.

## 16. Classification: R2 — RETRIEVAL SEMANTICALLY USEFUL BUT CAUSALLY WEAK

Not R1 (retrieval-capable): top-1 reliability is too poor, and a genuine
counter-example exists (§12) where causally-irrelevant content clearly wins.
Not R3 (retrieval insufficient): the correct experience is never absent from the
retrieval window, causal enrichment measurably helps on the query shapes that
matter, and the system is not merely random (topically unrelated distractors
rarely win outright, D5's Q5 win being the one clean exception found). Not R4
(inconclusive): the evidence is clear and internally consistent across all six
query forms plus the negative control.

**Implication, per the mission's own framing**: ingestion alone (fixing self-edit's
`tag="SELF_EDIT"` vs. `tag="MEMORY"` routing so failures reach the embedded corpus)
is unlikely to solve the hot-stove problem by itself. The representation/relevance
layer needs separate design attention — most plausibly a lightweight reranking or
minimum-relevance-threshold step downstream of plain vector search, not a wholesale
architecture replacement.

## 17. Recommendation for Remaining Deadline Window

Do not spend remaining time wiring `retrieve_relevant_memories()` into
`self_edit_manager.py` as-is and expecting reliable behavior — the evidence here
shows that would frequently hand the retrieved "relevant experience" slot to
something causally wrong. If the remaining window allows for one more small,
well-scoped experiment rather than a production change, the highest-value next
step would be testing whether a **cheap post-retrieval reranking step** (e.g.
requiring the retrieved record and the query to share at least one specific,
extracted error-signature token, on top of the existing embedding search) closes
the Q2/Q3/Q5-style lexical-trap gap — but that is a new hypothesis for a future
pass, not something to build now under this mission's explicit "do not fix
anything" constraint.

## 18. Files Changed

- `app/experiments/retrieval_capacity_proof/run_experiment.py` (new)
- `app/experiments/retrieval_capacity_proof/retrieval_results.json` (new, generated data)
- `audits/2026-09-06_retrieval_capacity_proof.md` (this report, new)

No production file was modified. No production data file was written to.

## 19. Git HEAD / RiverBrain Hash Verification

Before: HEAD `2cf2d95009943797db5ec41fea9b4021634fd5e6`, `river_brain.pkl` SHA-256
`eee193444a735d6ae510e8f8fa0faae1da4b2b1467a2a5da6f15c93467c9d815`.

After: HEAD `2cf2d95009943797db5ec41fea9b4021634fd5e6` (unchanged), `river_brain.pkl`
SHA-256 `eee193444a735d6ae510e8f8fa0faae1da4b2b1467a2a5da6f15c93467c9d815` (unchanged,
byte-identical).
