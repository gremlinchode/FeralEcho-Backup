# Orphaned Memory Retrieval Forensic Audit

## 1. Executive Verdict

**`retrieve_relevant_memories()` is not an orphaned mechanism system-wide — it is a live, heavily-used, well-engineered function called from at least nine real production sites** (`run.py`, `app/routes_echo_studio.py` ×2, `app/emergent_scheduler.py`, `app/core/echo_tool_dispatch.py`, `app/core/echo_optuna.py`, `app/core/curiosity_engine.py`, `app/core/echo_core.py` as a wrapper, `app/core/echo_ground_truth.py`, `app/internet_tools/autonomous_fetch.py`, `app/sync/echo_messaging.py`). The prior Initial-Generation Influence audit's finding — that `self_edit_manager.py` imports it and never calls it — is **confirmed correct and unchanged**, but its own framing ("the orphaned retrieval mechanism") overstated the scope: this is one caller that never wired it in, not a dead organ.

**The more important, previously-undiscovered finding supersedes the retrieval-wiring question entirely: even if `self_edit_manager.py` called `retrieve_relevant_memories()` today, it would retrieve nothing useful about the `functools` failure, because the failure records were never embedded into the corpus the function searches.** `append_to_journal(tag, text)` routes by tag: only `tag=="MEMORY"` writes to `ACTIVE_JOURNAL` (`memory/memory_journal_active.log`), the one file `rebuild_vector_memory()` ever streams from into FAISS. Every self-edit failure is logged with `tag="SELF_EDIT"`, which routes to a structurally separate file, `memory/SELF_EDIT.log`, that is never read by the embedding pipeline. A direct scan of all 124,561 real vector-memory entries confirms **zero** contain the literal text "NameError" combined with "functools." This is not a retrieval-quality problem; it is a storage-boundary problem that would make retrieval moot even if reconnected.

A real, isolated, read-only replay of the actual live function against the actual live corpus additionally shows that even where lexically-adjacent content *does* exist, the top-scoring hits are surface-similar, not causally relevant — e.g., a `functools` query's top hit is a self-edit candidate's own code that successfully imports `functools`, not a record of the failure.

## 2. Safety Invariants

| Check | Before | After |
|---|---|---|
| `run.py` / watchdog process | not running | not running |
| Port 5000 | unbound | unbound |
| Git HEAD | `2cf2d95009943797db5ec41fea9b4021634fd5e6` | unchanged |
| `river_brain.pkl` sha256 | `eee193444a735d6ae510e8f8fa0faae1da4b2b1467a2a5da6f15c93467c9d815` | unchanged |
| `memory/faiss.index` mtime | `Sep 6 16:17:16 2026` | unchanged (confirmed identical before and after the Phase 3/10 replay) |
| `memory/memory_meta.json` mtime | `Sep 6 16:17:16 2026` | unchanged |
| Production source files modified | none | none |
| Real model calls made | none | none — Phase 3/10 replay is a pure `VectorMemory.search()` read (cosine similarity over an already-built FAISS `IndexFlatIP`); `embed_text()` runs the local sentence-transformer encoder only, no network/generation call |
| Memory data mutated | no | no — `retrieve_relevant_memories()`'s only I/O is the read-only `vector_memory.search()` call; `VectorMemory.add()`/`_persist()` were never invoked |

The four pre-existing `M` files in `git status` (`sandbox/safe_exec_wrapper.py`, `sandbox/scripts/temp_self_edit.py`, two `scripts/memory_ablation_*` result files) predate this mission — untouched here, left exactly as found from earlier forks this session. Only this report file was created.

## 3. Exact Implementation of `retrieve_relevant_memories()`

`app/core/memory_bridge.py:410-477`.

```python
def retrieve_relevant_memories(
    query: str,
    top_k: int = TOP_K,               # TOP_K = 6 (line 38)
    source_filter: Optional[str] = None,
) -> List[Dict[str, Any]]:
    try:
        qvec = embed_text(query)
        # Global Workspace bias blend (Phase 4a, see below) — optional, TTL-gated
        bias_query, bias_ts = _workspace_bias["query"], _workspace_bias["ts"]
        if bias_query and (now - bias_ts) < _WORKSPACE_BIAS_TTL:   # 300s
            qvec = normalize(0.7 * qvec + 0.3 * embed_text(bias_query))
            # publishes a "workspace.consumed" salience event — best-effort
        fetch_k = top_k * 3 if source_filter else top_k
        results = vector_memory.search(qvec, k=fetch_k)
        records = [{"text": r[0], "score": r[1], "meta": r[2]} for r in results]
        # Unconditional exclusion (Finding, 2026-09-02):
        records = [r for r in records
                   if r["meta"].get("role") not in _ALWAYS_EXCLUDED_MEMORY_CATEGORIES
                   and r["meta"].get("memory_source") not in _ALWAYS_EXCLUDED_MEMORY_CATEGORIES]
        if source_filter:
            filtered = [r for r in records if r["meta"].get("memory_source") == source_filter]
            return filtered[:top_k]     # no unfiltered-fallback padding (fixed Finding 22 Batch 6)
        return records[:top_k]
    except Exception as e:
        logging.error(f"Failed to retrieve memories: {e}")
        return []
```

Real dependency chain, verified by direct read of each:

```
caller
  ↓
retrieve_relevant_memories(query, top_k, source_filter)
  ↓
embed_text(query)                         memory_bridge.py:212
  → sentence_transformers .encode(normalize_embeddings=True)  → 384-dim float32
  ↓
vector_memory.search(qvec, k=fetch_k)     app/lib/vector_memory.py:120
  → faiss.normalize_L2(qe); self.index.search(qe, k)     [IndexFlatIP → cosine similarity]
  ↓
returns (text, score, meta) tuples, sourced from self.meta (memory/memory_meta.json)
  ↓
_ALWAYS_EXCLUDED_MEMORY_CATEGORIES filter (frozenset({"code_analysis", "self_model_reflection"}))
  ↓
optional source_filter post-filter
  ↓
List[Dict] returned to caller
```

Per-record fields that survive retrieval: `text` (raw stored string), `score` (cosine similarity, float), `meta` (a dict — whatever was attached at write time, typically `memory_source`, `role`, `timestamp`; NOT a fixed schema). **None of the fields the Hot-Stove audit's candidate-knowledge design calls for exist as first-class fields**: no `trace_id`, no `action`, no `consequence_signature`, no `causal_hypothesis`, no `confidence`, no `provenance`. Whatever a caller wrote as raw text is all that comes back — retrieval preserves exactly what was embedded, nothing more, nothing structured.

## 4. Complete Current Call-Site Inventory

Full repo grep for `retrieve_relevant_memories`, classified:

| Location | Classification | Notes |
|---|---|---|
| `app/core/memory_bridge.py:410` | DEFINITION | the function itself |
| `app/core/memory_bridge.py:45,395` | COMMENT | design-rationale comments referencing the function |
| `app/core/memory_bridge.py:575` | CALL | a real, live doctest-style smoke-check inline in the module (`results = retrieve_relevant_memories("calm walk")`) — self-test, not a consumer |
| `run.py:261` | IMPORT (guarded) | `try: from app.core.memory_bridge import ..., retrieve_relevant_memories, ...` |
| `run.py:264` | FALLBACK STUB | `except ImportError: retrieve_relevant_memories = lambda *a, **k: []` — only fires if the import itself fails |
| `app/routes_echo_studio.py:53-60` | CALL (live) | adapter wrapping the function for Echo Studio's memory-browser view |
| `app/routes_echo_studio.py:489-503` | CALL (live) | second, `source_filter`-aware passthrough |
| `app/emergent_scheduler.py:51,347` | CALL (live) | `retrieve_relevant_memories(prompt, top_k=1)` — recency/dedup check inside the autonomous loop |
| `app/emergent_scheduler.py:810` | COMMENT | references the function's exclusion behavior |
| `app/core/echo_tool_dispatch.py:249-250` | CALL (live) | a real tool-dispatch path, `source_filter=None` |
| `app/core/echo_optuna.py:9,41,59` | CALL (live) | seeds Optuna dry-run trial prompts from vector memory |
| `app/core/curiosity_engine.py:99-102` | CALL (live) | dedup/recency check before harvesting a curiosity question |
| `app/core/echo_core.py:447-461` | WRAPPER METHOD | `EchoCore.retrieve_relevant_memories()` — a defensive, `getattr`-probing indirection over whatever `self.memory_bridge` object is attached; not itself a call site into `memory_bridge.py`'s function unless something else wires `memory_bridge` in as `self.memory_bridge` |
| `app/core/echo_ground_truth.py:530-531` | CALL (live) | `_build_memory()` — the real conversational grounding consumer, see §13 |
| `app/core/liveness_ledger.py:886,3326,3377-3413` | LIVENESS CHECK (`code_analysis_retrieval_exclusion`) | a real, live Liveness Ledger check that verifies this exact function still unconditionally excludes `code_analysis`/`self_model_reflection` — see §9 |
| `app/core/self_edit_manager.py:19` | IMPORT (unused) | **the subject of this audit — imported, zero call sites in the file** |
| `app/experiments/learning/harness.py:134,154-157` | CALL (experiment) | a prior-session research harness, not production |
| `app/internet_tools/autonomous_fetch.py:8,137` | CALL (live) | dedup check before logging a fetched article |
| `app/sync/echo_messaging.py:543-544` | CALL (live) | cross-machine sync context lookup |
| `archive_optional_files/test_memory_stack.py` | ARCHIVED | not on any live path |
| `scripts/verify_behavioral_state.py:211-229` | TEST | monkeypatches the function to assert FAISS is never consulted by a *different* mechanism (`behavioral_state.py`) — confirms FAISS-independence of that module, not a caller |
| `scripts/verify_liveness_ledger.py:1388-1414` | TEST | synthetic real/degraded fixtures for the `code_analysis_retrieval_exclusion` discrimination suite |
| `scripts/memory_ablation_experiment.py:5,13,162` | RESEARCH SCRIPT | this session's own Finding 76 ablation experiment (see §14) |
| `archive_janitor/check_bible_sample.py` | ARCHIVED | not on any live path |

**Net: 9 real, live production call sites outside `self_edit_manager.py`. Zero call sites inside `self_edit_manager.py`, despite an unconditional top-of-file import.**

## 5. Historical Git Archaeology

```
$ git blame -L 19,19 app/core/self_edit_manager.py
^44e7a8e (Richie Tate 2026-06-28 23:38:59 -0700 19) from app.core.memory_bridge import append_to_journal, retrieve_relevant_memories, log_dream_bridge, log_interaction

$ git log --diff-filter=A --oneline -- app/core/self_edit_manager.py
44e7a8e FeralEcho — autonomous mind, clean initial commit

$ git log -S "retrieve_relevant_memories" --oneline -- app/core/self_edit_manager.py
(no output)

$ git log -p --follow -- app/core/self_edit_manager.py | grep -n "retrieve_relevant_memories"
5083:+from app.core.memory_bridge import append_to_journal, retrieve_relevant_memories, log_dream_bridge, log_interaction
```

The import line has existed, byte-identical, since the file's introduction in the repository's one reachable initial commit (`44e7a8e`, 2026-06-28 — per CLAUDE.md's own documented history, this is the "clean initial commit" that superseded a pre-history commit not present in this repo's object database). The `-S` pickaxe search — which finds every commit where the string's *occurrence count* changed — returns **zero commits**, meaning the string has never been added or removed at any other point in this file's visible history. It appears exactly once, in the file's first commit, and has never moved since.

**This blame result independently and more precisely re-confirms this file's own Finding 92 (2026-09-05, "complete Plan 5 (request-scoped trace_id)"), the file's own most recent real commit — that commit touched other functions in this file but never this import line, consistent with a genuine 71-day gap of zero attention to this specific line.**

## 6. Introduction Commit

`44e7a8e` — "FeralEcho — autonomous mind, clean initial commit." Per CLAUDE.md's own Finding 7, this is a deliberate clean-history commit (the actual pre-history predecessor commit, `dc3795a`, is confirmed absent from this repository's object database — `git cat-file -e dc3795a` fails). This means **git archaeology on this specific question is bounded**: whatever happened to this import *before* the clean-history cut is permanently unrecoverable from this repository. What can be said with confidence is scoped to the 71 days this repo's visible history covers (2026-06-28 → present): within that entire window, the import was never called, never removed, and never referenced by any commit message.

## 7. Last Known Live Caller, If Any

**None found. No evidence of a historical caller within this file's visible git history.** Per Phase 6's explicit instruction, this is stated plainly rather than inferred: `git log -p` across the file's full history shows the import string appearing exactly once (its introduction) and never again — no diff ever added a call, and no diff ever removed one. There is no "OLD ARCHITECTURE" diagram to draw here, because there is no historical evidence a connection ever existed to lose.

## 8. Disconnection/Removal Evidence

**No evidence found.** A targeted search of the full commit-message history (`git log --oneline --grep` across memory/noise/contamination/bloat/hallucination-related terms, and a full read of `git log --oneline -- app/core/self_edit_manager.py`, 27 commits) turns up nothing discussing removing or disconnecting memory retrieval from self-edit. The one memory-retrieval-related commit message found anywhere in the full 161-commit visible history is `057c2c9`, "Run memory-retrieval ablation experiment, add Finding 76" — this session's own earlier ablation work (§14), unrelated to any historical removal.

Combined with §5-7: the honest conclusion is that this was very likely **never wired in the first place**, not disconnected after working. The import sits alongside three siblings from the same `from app.core.memory_bridge import ...` line — `append_to_journal` (19 real call sites in this file), `log_dream_bridge` (0 call sites), `log_interaction` (0 call sites) — meaning `retrieve_relevant_memories` is not uniquely unused; it's one of three functions imported from that line and never called, alongside two others. This is more consistent with an anticipatory or copy-paste-boilerplate import (bring in "the memory API," use one function from it, leave the rest available) than with a deliberate, then-reversed integration.

## 9. Actual Relevance Algorithm

Pure dense-embedding cosine similarity. No lexical/keyword matching, no exact-exception-text matching, no failure-signature matching, no task-type filtering baked into the ranking itself (task-type-style filtering is only available as an optional post-hoc `source_filter` on the coarse `memory_source` tag — `user_conversation`, `autonomous`, etc. — not on anything failure-specific).

Mechanically: `embed_text()` runs a local sentence-transformer (`all-MiniLM-L6-v2`, 384-dim, per CLAUDE.md's documented startup guard) with L2-normalized output; `vector_memory.search()` runs `faiss.IndexFlatIP` (inner product on unit vectors = cosine similarity) and returns the raw similarity score, unthresholded — there is no minimum-similarity cutoff anywhere in the function; whatever the top-`k` nearest vectors are, they are returned regardless of how weak the match actually is.

**This directly answers Phase 2's central distinction.** The function measures **semantic similarity** only. It has no mechanism for, and makes no attempt at, **situational relevance** (was this the same kind of episode?), **causal relevance** (did this past event actually explain the present one?), or **actionable relevance** (would retrieving this change what should be done now?). A similarity score of `0.58` communicates only "these two texts occupy nearby regions of embedding space" — nothing about whether one caused, explains, or should influence a response to the other.

## 10. Real `functools` Replay

Run directly against the live, unmodified vector store (`memory/faiss.index` + `memory/memory_meta.json`, 124,561 real entries) via the real, unmodified `retrieve_relevant_memories()` function — no model calls, no mutation (mtimes confirmed byte-identical before and after, §2).

**Query: `"NameError: name 'functools' is not defined. Did you forget to import 'functools'?"`** (the exact real error text from `memory/SELF_EDIT.log`):

| Score | Source | Text (truncated) |
|---|---|---|
| 0.5790 | `user_conversation` | `import strip_prose from feral_echo importable modules import sys import ast import re import functools ...` |
| 0.5763 | `user_conversation` | `# from app.core.tool_manager import ToolManager # from app.core.self_edit_generated import main_function ...` |
| 0.5743 | `user_conversation` | `# from app.core.self_edit_generated import main_function # from app.core.tool_manager import Tool ...` |

**Zero of the top-3 (or any) results are the actual failure event.** All three are self-edit-generated *code* that happens to lexically contain the word "functools" (successfully imported, in these snippets) — the opposite information from what would be useful: "here is code that uses functools correctly," not "here is why a prior attempt failed to."

**Query: `"NameError: name 're' is not defined. Did you forget to import 're'?"`** (the other real, prior-fixed recurring signature):

Top hits are generic StackOverflow-fetched articles about `NameError`/`ImportError`/`ModuleNotFoundError` in general (scores 0.57-0.60) — topically adjacent but not this specific failure, and not from `SELF_EDIT.log` at all (confirmed: `memory_source="autonomous", role="fetch"` — the autonomous news-fetch pipeline, completely unrelated to self-edit).

**Query: `"IndexError: list index out of range in a data processing loop"`** (unrelated coding failure, for comparison): retrieves plausible, topically-adjacent StackOverflow articles about list iteration/indexing (scores 0.48-0.52) — a reasonable, if generic, match; same caveat that these are externally-fetched news snippets, not Echo's own experience.

**Query: `"What does it mean to have faith when everything is uncertain?"`** (non-coding, philosophical, for contrast): retrieves genuinely on-topic `[REFLECTION]` entries about faith and uncertainty at markedly higher similarity (0.75-0.80) than either coding query achieved (0.48-0.60). The corpus's dominant content (autonomous reflections, per the Garden Accidental Relevance baseline's own finding that the question garden and, evidently, the wider memory corpus too, skew heavily philosophical/relational) produces both denser coverage and tighter matches for this kind of query than for any coding-failure query.

**§10's decisive negative result, independent of and prior to any relevance-quality question**: a full scan of all 124,561 real vector-memory entries for the literal co-occurrence of "NameError" and "functools" returns **zero matches**. The retrieval mechanism cannot find what was never stored — see §13.

## 11. False-Relevance Analysis

The replay in §10 already demonstrates the core adversarial finding directly, using real data rather than a constructed test: the `functools` query's highest-scoring real result (0.579) is **surface-lexically similar** (contains the word "functools") but **causally unrelated** (it's a working import, not the record of a failure). This is precisely the "surface similarity vs. actual reusable experience" failure mode the mission asks to test for — found in production data on the first real query, not manufactured.

A second, sharper version of the same test: the `re`-import query's top hits are generic StackOverflow content about `NameError` in the abstract — genuinely on-topic in a broad sense, genuinely useless for the specific question "why did *my* `re` import fail *here*, previously." Same function, same failure class, different specific cause would be indistinguishable to this mechanism from same function, unrelated cause — because nothing in the embedding captures which specific symbol was undefined, only that the text is broadly about import errors.

**Conclusion for Phase 11: the mechanism retrieves surface similarity, not reusable experience, whenever it is asked a technical/causal question. It performs comparatively well on genuinely topic-coherent, high-density content (philosophical reflection) — not because the algorithm changes, but because that corpus segment is larger, more self-similar, and (critically) actually contains the kind of content being searched for.**

## 12. Data-Quality Analysis

Corpus composition, by `memory_source` tag, across all 124,561 entries:

| Source | Count | % |
|---|---|---|
| `code_analysis` | 59,948 | 48.1% |
| `autonomous` | 31,132 | 25.0% |
| `None` (untagged) | 23,716 | 19.0% |
| `user_conversation` | 6,230 | 5.0% |
| `sync_air` | 1,201 | 1.0% |
| `environment` | 1,122 | 0.9% |
| `claude_research` | 772 | 0.6% |
| `self_model_reflection` | 243 | 0.2% |
| `tool_manager` | 187 | 0.1% |
| `dream_v2` | 10 | <0.1% |

Two structural facts matter more than the raw distribution:

1. **`code_analysis` (48.1% of the entire corpus, the single largest category) is unconditionally excluded from every `retrieve_relevant_memories()` call** via `_ALWAYS_EXCLUDED_MEMORY_CATEGORIES` — confirmed both by direct source read (§3) and by the live `code_analysis_retrieval_exclusion` Liveness Ledger check (§9, `app/core/liveness_ledger.py:3319-3416`), which exists specifically because this category's raw AST-parser output was found, in a 2026-09-02 investigation, to be eligible to surface as if it were genuine experience. Effective searchable corpus is closer to 64,370 entries, not 124,561.
2. **No `memory_source` value corresponding to self-edit at all exists anywhere in the corpus.** There is no `"self_edit"`, no `"self_edit_failure"`, no equivalent tag — because, per §5-8, `SELF_EDIT.log` content is never routed through the embedding pipeline in the first place. This is not a filtering choice (unlike `code_analysis`); it's an absence at the point of ingestion.

There is no mechanism anywhere in the corpus that distinguishes **observation from interpretation**, or **correlation from causation** — every record is flat text plus a coarse source tag; there is no field for "this was a diagnosis," "this was a hypothesis," "this was confirmed," or "this action produced this consequence." Whatever raw text got embedded is retrievable; nothing about its epistemic status survives.

## 13. Intended Decision Path

Traced the one real, live conversational consumer end-to-end: `app/core/echo_ground_truth.py:523-544`, `_build_memory()`.

```python
def _build_memory(prompt: str) -> str:
    """Pre-run FAISS retrieval for cross-session memory queries and inject results
    with a hard binding constraint. Prevents Echo from narrating content not in
    the retrieved record..."""
    raw = retrieve_relevant_memories(prompt[:200], top_k=10)
    entries = [e for e in raw if e['meta'].get('memory_source') == 'user_conversation'][:5]
    if not entries:
        return "MEMORY CONSTRAINT: No cross-session memory entries matched this query. ..."
    # else: renders the up-to-5 matched entries as plain prose context
```

This is the clearest possible confirmation of the mission's own standing warning: **retrieval feeds a plain prose block appended to the system prompt. There is no ranking-authority mechanism, no confidence weighting propagated into generation, no structural distinction between "retrieved and highly relevant" and "retrieved and barely relevant" once the text reaches the model — the raw cosine score never crosses into the prompt at all.** The one safeguard present is a *negative* one (the "MEMORY CONSTRAINT" disclaimer preventing confabulation when nothing matches), not a positive influence mechanism.

Every other real caller (§4) follows the identical shape: `emergent_scheduler.py`/`curiosity_engine.py` use it only as a `top_k=1` recency/dedup probe (not as a knowledge-injection path at all); `echo_optuna.py` samples prompts for dry-run trials; `autonomous_fetch.py`/`echo_messaging.py` use it for deduplication. **Not one of the nine real live call sites uses retrieval as a decision-authority mechanism in the Hot-Stove sense** — none of them let a retrieved record override, constrain, or weight a consequential choice; every one either injects plain prose or uses the top-1 similarity purely as a duplicate-detector.

## 14. Historical Reason for Abandonment

**No evidence found.** Per §7-8, there is no commit-message or code-comment evidence that this specific integration (self-edit initial generation ↔ vector memory) was ever attempted, tested, and then deliberately withdrawn for a documented reason (noise, contamination, latency, etc.). The mechanism appears to have simply never been connected in this file, from the first commit onward.

This session's own prior, independent work is directly relevant context, not a historical explanation of *this* gap: `scripts/memory_ablation_experiment.py` (Finding 76, commit `057c2c9`) ran a real, controlled ablation of `retrieve_relevant_memories()` on the **conversational** `personal`-task path (`echo_ground_truth.py`'s `_build_memory()`) and found the embedding-distance and quality-score effects of ablating retrieval were statistically indistinguishable from pure sampling noise (Mann-Whitney p=0.48). That result is about a different call site than self-edit and does not explain why self-edit's own import was never wired — but it is directly relevant supporting evidence that, *even where this exact mechanism is genuinely live and consequential-looking*, no measurable behavioral effect has yet been demonstrated. This strengthens rather than weakens §12-13's conclusion: the retrieval mechanism, as currently built, has not been shown to move outcomes anywhere it's actually connected, on top of never having been connected at all inside self-edit.

## 15. Primary Classification

**Primary: A — VALID BUT ORPHANED**, with two important qualifications that a bare "A" would understate:

- The mechanism is not merely "sound and useful" in the abstract — it is **already live, in real production use, at nine other call sites** at the time of this audit. This is not a fossil; it is working infrastructure with one missing caller.
- **Secondary: E — INCOMPLETE / NONFUNCTIONAL, but specifically scoped to the self-edit use case, not the mechanism itself.** For the *particular* purpose this investigation cares about — closing the `functools` hot-stove gap — reconnecting the call alone would not work, because (§10, §12) the corpus the function searches contains zero embedded records of self-edit's own failures. The retrieval *algorithm* is complete and functional (B does not apply — it is not "too noisy," it is simply empty for this domain); the *data pipeline feeding it* is incomplete for this specific source.

Neither **C** (architecturally obsolete — the mechanism is actively used elsewhere, current) nor **D** (dangerous to reconnect — no evidence of any historical harm, §14) nor **F** (intended caller lost — §7 found no historical caller to lose) apply. **G** (no historical basis) is the closest fit for *why* it was never connected, but "orphaned/incomplete for this purpose" (A+E) is the more useful and complete characterization of *what the evidence actually shows*.

## 16. Recommendation

**INVESTIGATE HISTORICAL ARCHITECTURE FURTHER** is not warranted — §5-8 already exhausted what git history can answer, and it answered "no evidence found," definitively, not "insufficient search."

**DO NOT TOUCH** is too conservative given the strength of the positive evidence that the mechanism itself works correctly and safely elsewhere (nine live callers, no history of harm).

**REPAIR THE ORPHANED PATH AFTER SEPARATE VALIDATION** — this is the closest fit, but needs to be stated precisely to avoid repeating the "lesson dump" trap this whole session has guarded against: the validation required is not "does calling `retrieve_relevant_memories()` from self-edit work" (§10-13 already show that, as currently built, it would retrieve near-nothing useful — the corpus doesn't contain the data). **The actual prerequisite repair is upstream of retrieval entirely: self-edit failure records need a path into the embedded corpus in the first place** (e.g., a real `tag="MEMORY"`-routed write alongside the existing `tag="SELF_EDIT"` one, or an equivalent explicit ingestion step) before a retrieval-side reconnection could be meaningfully tested at all. Reconnecting `retrieve_relevant_memories()` into `self_edit_manager.py` today, without that upstream fix, would very likely reproduce Architecture A's exact null result (Section 10's `functools` query already demonstrates what it would retrieve: nothing about the actual failure) — a second confirmed-null experiment on a boundary already shown to be empty, not new information.

**Recommended next step, stated as a design question rather than an implementation instruction (per this mission's own no-fix mandate): before any code changes, a follow-up forensic pass should determine whether routing self-edit failure records into the embedded corpus (via `tag="MEMORY"` or an equivalent) is itself safe and useful — i.e., repeat this exact audit's Phase 2/8/11 methodology (relevance algorithm, data quality, false-relevance) against a *hypothetical* corpus that actually contains this content, before recommending it be built.** This is squarely a design decision for Architecture B, not something this archaeology pass should resolve unilaterally.
