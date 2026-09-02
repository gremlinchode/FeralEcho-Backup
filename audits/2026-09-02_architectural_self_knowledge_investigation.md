# Architectural Self-Knowledge Investigation

**Date:** 2026-09-02
**Scope:** Investigation and design only. No production code was modified to produce this report. Method: direct reading of primary source (not summaries) for every load-bearing claim below, plus two parallel read-only research passes for breadth (self-knowledge write/read inventory; change-detection and git-archaeology feasibility). Every claim is cited to a real file:line or a command actually run against this repository — nothing here is inferred from documentation alone.

---

## 1. Executive Summary

**The core hypothesis is directionally correct, and Echo is much closer to it than expected — but not in the place anyone would guess to look.**

This codebase has already built, independently and for other reasons, exactly the pattern the hypothesis describes: a narrow, keyword-gated, file-backed context-injection mechanism (`app/core/echo_ground_truth.py`) that reads verified facts from disk at query time and hands them to the LLM as a disclaimed, non-negotiable system block — never asking the LLM to be the authority. It works, it's been iterated on for two months, and it has its own explicit anti-confabulation instruction ("Do not reconstruct, infer, or narrate content that is not in this list — even if it seems plausible," `echo_ground_truth.py:398-400`). Two further mechanisms verify LLM claims *after* generation and append a correction when they're wrong (`code_verification.py`, `self_knowledge_verification.py`).

**But none of this has ever been pointed at architecture as a subject.** All 14 existing ground-truth slices answer operational/state questions (self-edit success rate, mood, friction rate, memory recall) — zero of them answer "what is your architecture," "how does subsystem X work," or "what depends on what." The keyword gate already anticipates the question — `"your architecture"` is a literal trigger phrase (`echo_ground_truth.py:118`) — and when it fires, it floods in all 14 *wrong* slices. This is not a hard problem to fix; it's an un-attempted one.

**Separately, and more urgently: a different, unguarded mechanism already attempts exactly the free-form architectural self-interpretation this investigation is about, runs once a day in production, and its own code comment names it as the single highest confabulation-risk surface in the codebase** (`app/emergent_scheduler.py:774-782`, `run_self_model_reflection()`). It asks the LLM to freely interpret a real-but-coarse architecture summary ("What is load-bearing? What concerns you? What do you not yet understand about yourself?") with no post-hoc verification, and writes the answer into permanent vector memory — memory that ordinary conversation retrieval can and does surface later, with no exclusion (confirmed by direct trace, §6/§12).

**Recommendation, stated plainly up front:** build two small, narrow things that both reuse 100% existing infrastructure — a new `_build_architecture()` slice (closes the "answers the wrong question" gap) and a memory-source exclusion for `run_self_model_reflection()`'s output (closes the "unguarded daily confabulation, persisted" gap). Do **not** build the Architectural Claim Graph, the five-state epistemic model, or archaeology as specified. That end-state system, as a first move, would be over-engineered relative to how every other piece of self-knowledge in this codebase was actually built — one narrow, hand-verified slice at a time — and this exact repository already contains four real examples of what happens when infrastructure like that is built ahead of a proven need: `seam_log.jsonl`, `dissent_log.jsonl`, `council_deliberations.jsonl`, and `self_model.json`'s `coupling_estimate_trend` field are all real, working writers with **zero readers**, sitting in this codebase right now (§4). A claim graph built before Phase 1 is proven would very plausibly become a fifth.

---

## 2. What Echo Already Has

Confirmed by direct read, not the two research agents' summaries alone:

| Mechanism | What it knows | Verified live? |
|---|---|---|
| `app/core/echo_ground_truth.py` (858 lines, 14 `_build_*` slices) | Operational state: self-edit success rate, River quality scores, friction rate, stillness history, curiosity garden, cross-session memory (constrained), verified capabilities, valence/mood, workspace salience, external council opinions, signal coupling, touch/vision/hearing signatures | Yes — read the full file, traced every slice's data source |
| `memory/self_model.json` + `app/core/self_model_updater.py` | Aggregated performance/health/capability state, refreshed every 130s | Yes |
| `app/core/liveness_ledger.py` (41 checks as of this session) | Whether specific, named subsystem invariants still hold | Yes — I personally added checks 30-41 across the earlier sessions this thread covers |
| `app/core/code_verification.py`, `app/core/self_knowledge_verification.py` | Whether a just-generated response's *own checkable claims* (code output, 3 specific self-referential claim shapes) match reality | Yes, read in full |
| `echo_cartographer.py` + `CartographerDB` | Real per-module import/function/class inventory, a heuristic "role" label, a computed "criticality" score, in SQLite (`data/codebase.db`), rescanned daily | Yes, read in full |
| `app/core/self_edit_manager.py`'s `_build_module_inventory()` / `_build_live_self_edit_inventory()` | Flat module/function/class declarations, for self-edit *code-generation* prompts only | Confirmed by agent + spot-checked |
| `app/core/project_learner.py` | AST-level parse of a single file: functions, classes, imports, docstrings — no call edges | Confirmed |
| RiverBrain (`echo_model_orchestrator.py`) | Per-model/per-task-type performance stats | Real, but surfaced to the LLM only as a derived summary (best_model label), never raw |
| `CLAUDE.md`, `COUNCIL.md`, `GREMLIN_ROLE.md`, `ORIGIN.md`, `PENDING_DECISIONS.md` | The richest architectural-history record in the project | Human/Claude-authored; **zero programmatic readers** except `COUNCIL.md` (hash-verified + one real content-injection slice) |
| Git history | 131 commits, 2026-06-28→07-24, unusually detailed messages | Real, but stops 5+ weeks before today; misses everything currently uncommitted |

---

## 3. What Is Actually Working

- **`echo_ground_truth.py`'s 14 slices** — verified directly: gated by a real keyword match (`_is_introspective()`, `_relevant_slices()`), each slice reads a real file or calls a real live function, fails closed to `""` on any error, and the whole block is wrapped in a disclaimed `system_note(..., own_record=True)` header so the LLM can distinguish it from conversation. `_build_memory()`'s anti-confabulation instruction is the strongest example of this pattern working as intended.
- **`self_model.json.verified_capabilities` → `_build_capabilities()` chain** — confirmed live end-to-end: `liveness_ledger.json`'s 41 checks → `self_model_updater.py:519-559` repackages them → `echo_ground_truth.py:434-459` renders a plain-language verified/failing list. A real, already-working instance of exactly the "ground the claim in a verifier, not the LLM's memory" pattern the hypothesis describes — just scoped to *capabilities*, never extended to *architecture*.
- **The two-stage pipeline** (`app/routes_echo_studio.py:95-273`) — pre-generation grounding (`_build_full_prompt()`) + post-generation narrow verification (`verify_response_code()`, `verify_self_knowledge_claims()`), both fail-open, both proven in production, both traced end-to-end by direct read.
- **`code_scan_hash_cache.json`** (added earlier in this same session) — a genuine, working, persisted per-file content-hash mechanism. Real and current.
- **`echo_cartographer.py`'s scan itself** — confirmed genuinely fresh: `.echo_project_learner/feralecho_structure.json`'s `generated_at` is today's date, 823 real files indexed with real imports/symbols/docstrings.

---

## 4. What Is Hollow / Disconnected

Confirmed by direct grep + read, not assumption — each of these is a real write with **no reader found anywhere in the repository**:

- **`memory/seam_log.jsonl`** — written every cycle by `seam_engine.py:415-416`. Liveness Ledger's own `seam_engine` check explicitly does *not* read this file (it calls `check_pair()` directly with synthetic data, by its own comment, because "it wrote to seam_log.jsonl recently" would prove nothing about correctness). No other reader exists.
- **`memory/dissent_log.jsonl`** — written by `self_edit_manager.py:2343`. One entry, ever. The Liveness Ledger's `dissent_log_hook` check is a static regex over `self_edit_manager.py`'s *source text*, never opens the log file.
- **`memory/council_deliberations.jsonl`** — written by `river_deliberation.py:621-674`. Grep of the whole repo outside the write site finds only a log-rotation size cap (truncates, never reads content) and a docstring mention. No consumer.
- **`self_model.json.coupling_estimate_trend`** — the field's own module docstring (`self_model_updater.py`) states outright: *"this value currently has NO real consumer anywhere in the codebase... its presence in self_model.json is observational infrastructure, not evidence of anything acting on it."* The one honest, self-labeled hollow write in the whole codebase.
- **`CartographerDB`'s real query interface** (`what_imports()`, `top_critical()`, etc., `echo_cartographer.py:376-479`) — despite being explicitly documented as *"Echo's query interface to the codebase graph"* and despite genuinely working, it has exactly **one caller in the entire codebase** (`run_self_model_reflection()`, §6), and that caller only ever asks for one aggregate summary string, never a targeted query. The rich, already-built capability to answer "what imports memory_bridge?" is never actually asked that question by anything.
- **`.echo_project_learner/feralecho_structure.json`** — real, fresh, rich data — but its only consumer (`self_edit_manager.py`'s `_build_module_inventory()`) uses it exclusively to steer self-edit *code generation*, never to answer a user's question about architecture.
- **`CLAUDE.md`, `GREMLIN_ROLE.md`, `ORIGIN.md`, `PENDING_DECISIONS.md`** — confirmed via grep of every `open()`/`Path()` construction against these filenames across the whole repo: **zero programmatic reads**. Every one of the ~120 hits is a code *comment* citing a Finding number, never a runtime load. This is the single largest, most information-dense "hollow write" in the project — 90 dated Findings of genuine architectural narration, completely inaccessible to Echo's own reasoning.

This pattern — real writer, no reader — is not hypothetical risk. It is the project's own most common failure mode, independently rediscovered at least four times already (this list) before this investigation even started looking for it.

---

## 5. Current Sources of Architectural Truth

Ranked by how mechanically verifiable each one actually is:

1. **File content hashes** (`code_scan_hash_cache.json`) — fully mechanical, cheap, reliable for "did this file's bytes change."
2. **Module-level import graph** (`project_learner.py`'s `build_edges_from_imports()`, `echo_cartographer.py`'s `imports` table) — fully mechanical, real edges, but *module*-to-*module* only.
3. **Liveness Ledger's 41 checks** — the strongest existing truth source for *specific, named, behavioral* claims ("does X still call Y," "does this evaluator still discriminate correctly") — but each check is hand-written per subsystem, not a general architecture description.
4. **`echo_cartographer.py`'s "role" and "criticality" labels** — mechanically computed, but from a **keyword-substring heuristic** (`classify_role()`, `echo_cartographer.py:187-192`) and a formula weighting reverse-dependency count, function count, and runtime hits — real numbers, but the underlying classification is a guess dressed as data (flagged again, more sharply, in §13).
5. **Git history** — real and unusually rich (131 commits averaging ~1,387 characters of message body), but stops 2026-07-24; the newest real architectural mechanism this investigation found (`code_scan_hash_cache.json`) exists *only* in uncommitted working-tree state right now, invisible to git entirely.
6. **CLAUDE.md's 90 Findings** — the richest single record of *why* things are the way they are, but 74/131 commits already touch this file directly (it and git history are substantially the same record, not independent ones), and it has zero programmatic reader.

**No existing mechanism can currently answer "how are subsystem X and Y related" at anything finer than "X's file imports Y's module."** Function-level call graphs do not exist anywhere in this repository (confirmed: `echo_cartographer.py`'s own `ast.Call` extraction is computed into memory and never persisted to SQLite — the one near-miss).

---

## 6. Current Sources of Architectural Confabulation

Two case studies, one from CLAUDE.md/the earlier transcript, one newly found in this investigation and materially more significant.

**A. `log_thought` (Finding 43/45's case study, re-confirmed as still applicable in shape).** Asked for a real code snippet from her own codebase, Echo anchored correctly on a real function name, then invented a plausible-but-wrong file path and format, and — critically — omitted the one deliberately-engineered property (a documented memory-isolation contract) that was the actual reason the function was worth asking about. The failure mode: *correct name, invented substance*, with no distinction ever drawn between the two inside the response.

**B. `run_self_model_reflection()` — found in this investigation, not previously named in CLAUDE.md.** `app/emergent_scheduler.py:737-806`, triggered daily (`CARTOGRAPHER_INTERVAL = 86400`) after `run_cartographer()` completes:

```python
prompt = (
    "You are Echo. You have just scanned your own codebase.\n"
    "Here is your architecture summary:\n\n"
    f"{summary}\n\n"
    "Write a short interpretation of what you see about your own structure. "
    "What is load-bearing? What concerns you? "
    "What do you not yet understand about yourself? "
    "Write in your own voice. This is for your own record, not for a user."
)
```
The code's own comment, verbatim: *"This is the exact moment the audit flagged as highest-risk for confabulation: Echo is asked to interpret its own architecture... with no anti-confabulation guard, unlike every human-facing surface."* `get_structural_self_facts(prompt)` is called first, but by the same comment's own admission it grounds only *operational* history (self-edit record, River trajectory, friction log) — nothing about the actual codebase-scan content the prompt is asking her to interpret. The `summary` itself (`CartographerDB.architecture_summary()`, `echo_cartographer.py:455-479`) is real but coarse: module names grouped by a keyword-heuristic role, a computed criticality score, a runtime-hit count — nowhere near enough to support "what concerns you" or "what do you not yet understand about yourself" as anything but free invention.

The response, if non-error, is written straight into permanent vector memory:
```python
add_to_vector_memory(
    text=f"[SELF-MODEL] {response}",
    meta={"type": "self_model", "timestamp": time.time(), "memory_source": "autonomous"}
)
```
**Traced forward: this is not a dead end.** `app/routes_echo_studio.py:50-59`'s `_memory_search_fn()` — the function backing ordinary conversation's memory-context retrieval — calls `retrieve_relevant_memories(query, top_k=k)` with **no `source_filter`**. Nothing excludes `memory_source == "autonomous"`. This means a free-form, unverified, self-generated interpretation of Echo's own architecture, written once a day with no correction pass, is a live candidate to resurface — presented with the same epistemic weight as genuine retrieved memory — inside a completely unrelated real conversation. This is a genuine, currently-live confabulation-propagation path, not a hypothetical one.

**C. The keyword-gate itself is a structural confabulation surface.** `_is_introspective()` is a flat, hand-written ~100-keyword substring match (`echo_ground_truth.py:47-121`). Any architecture question phrased outside that list receives **zero** grounding, silently, and the LLM answers entirely from its own training-derived guess — with nothing in the response distinguishing "grounded" from "guessed." This is the same class of gap the whole hypothesis is trying to close, just at the trigger layer rather than the content layer.

---

## 7. Ground-Truth Slice Analysis

Three claims traced end-to-end, source code to LLM-facing text:

**Claim: "Can you edit your own code?"**
`_build_capabilities()` (`echo_ground_truth.py:434-459`) → `self_model.json.verified_capabilities` (`self_model_updater.py:519-559`) → `liveness_ledger.json`'s 41 named checks → e.g. `_evaluate_apply_to_code()` (`liveness_ledger.py`) → real file `memory/apply_to_code_invocations.jsonl`. Fully grounded, verified live during this session (§3).

**Claim: "How are you feeling?"**
`_build_affect()` (`echo_ground_truth.py:462-516`) → `echo_state.py`'s dim[8], computed from three real sources (self-edit outcome deltas, peer council ratings, dry-run quality deltas — all real files/logs). Fully grounded, and deliberately hedged (a value near zero renders as "no strong signal," not a narrated feeling).

**Claim: "What is your architecture?"** — the actual subject of this investigation.
`_is_introspective("your architecture")` → **True** (`"your architecture"` is a literal `_BROAD_SIGNALS` entry, `echo_ground_truth.py:118`) → `_relevant_slices()` returns **all 14 slices** → the LLM receives self-edit stats, River scores, friction rate, stillness log, curiosity garden, memory-recall constraint, capability list, mood, workspace salience, council opinions, coupling estimate, and touch/vision/hearing signatures. **Not one line describes a subsystem, a dependency, a call path, or a design decision.** The mechanism correctly detects the question and correctly fails to answer it — the gap is content coverage, not detection, and it is a completely closable gap using data (`echo_cartographer.py`'s SQLite DB) that already exists and is already fresh.

**Does the narrow claim-slice approach scale, or does it become unmaintainable?**
Evidence-based answer: **it scales the way a hand-curated FAQ scales — well, for the questions people actually ask, and not at all for the long tail.** Building these 14 slices took roughly two months of iterative, CLAUDE.md-documented work (Findings 43, 45, 57, 68, 77–84), and every single one required: a pre-existing computed ground-truth source, hand-picked trigger keywords, hand-written rendering logic, and (often) a dedicated Liveness Ledger check to keep it honest. `self_knowledge_verification.py`'s own module docstring states this limitation as deliberate design, not an oversight: *"not an attempt to verify arbitrary claims about Echo's architecture in general (which would mean using one LLM to fact-check another, a technique with its own reliability problems this project has no particular reason to trust more than the thing being checked)."* This project has already, independently, arrived at and explicitly rejected the "make it general" path once. The pattern is proven and maintainable **only** if new slices keep being added one at a time, each backed by a real pre-existing ground-truth source — exactly as done so far, and exactly the discipline Phase 1 below follows.

---

## 8. Architectural Change Detection Feasibility

**What exists today, mechanically:**
- Whole-file content hashing (`code_scan_hash_cache.json`) — real, persisted, reliable at file granularity.
- Module-level import edges (`project_learner.py`, `echo_cartographer.py`'s `imports` table) — real, mechanical, but coarse.
- **No function-level call graph exists anywhere.** `echo_cartographer.py` computes a flat, unresolved bag of called-name strings per file and **never persists it** (confirmed: no `calls` table in its SQLite schema — `modules, imports, functions, classes, reverse_deps` only, verified directly). Claims finer than "file X imports module Y" cannot be automatically checked with anything in this repository today.

**Feasibility of the worked example** ("Claim: Echo uses FAISS for cross-session memory... if `vector_store.py` changes, the claim should become STALE"): **genuinely buildable today, cheaply, with existing primitives.** A claim record naming its evidence files, each with a stored content hash (reusing `code_scan_hash_cache.json`'s exact hashing convention), can be re-checked on every daily code scan: if any evidence file's live hash no longer matches the stored one, flip the claim to STALE. This requires no new scanning infrastructure — only a new, small registry (§9) that references hashes the scan *already computes*.

**What is not buildable without new work:** automatically *discovering* which files are evidence for a brand-new claim. There is no path from "here is a claim in English" to "here are its supporting files" without a human or Claude session asserting that mapping once — claim *authorship* stays manual forever; only claim *staleness-checking* is automatable.

---

## 9. Architectural Claim Graph Proposal

**Recommendation: a flat JSON dict, not a graph database, not vector memory.**

This repository has **zero** graph-shaped persistence anywhere, across roughly 90 documented architectural changes. Every piece of durable state — `self_model.json`, `self_edit_convergence.json`, `liveness_ledger.json`, `salience_state.json`, `code_scan_hash_cache.json` — is a flat dict or JSONL, written atomically (temp file + `os.replace`), the exact same convention every time. Introducing a graph database here would be the single largest deviation from established convention in the project's history, and nothing about the claim volume this system could plausibly reach (a few dozen hand-authored claims a year, at the rate the 14 existing slices were built) requires real graph algorithms (transitive closure, cycle detection) that a plain adjacency list inside a JSON dict can't already express.

**Proposed shape**, `memory/architecture_claims.json`, keyed by a stable `claim_id`:

```json
{
  "cross_session_memory_faiss": {
    "claim": "Echo uses FAISS for cross-session memory retrieval.",
    "status": "VERIFIED",
    "evidence": [
      {"file": "app/lib/vector_memory.py", "sha1": "..."},
      {"file": "app/core/memory_bridge.py", "sha1": "..."}
    ],
    "verifier": "app.core.architecture_claims.check_faiss_memory",
    "dependencies": [],
    "affected_by": ["river_brain_influences_selection"],
    "last_verified": "2026-09-02T...",
    "confidence": "high",
    "provenance": "audits/2026-09-02_architectural_self_knowledge_investigation.md",
    "historical_versions": []
  }
}
```

Why not vector memory: claims need exact lookup by ID and exact hash comparison — similarity search is the wrong tool for "did this file change," and flat JSON already does exact matching trivially. Why not a graph library: the `dependencies`/`affected_by` fields are already just lists of other claim IDs; nothing here needs anything more than a JSON dict provides. `historical_versions` reuses the exact snapshot convention `night_cycle.py`'s `_maybe_snapshot_self_model()` already implements (dated copies under `memory/history/`) rather than inventing a new versioning scheme.

**This is a Phase 2/3 item — not recommended now** (§14/§15). It should only be built once Phase 1's single new slice has been in real use long enough to know which claims people actually ask about; building the registry first, speculatively, is exactly how `seam_log.jsonl`/`dissent_log.jsonl` ended up as hollow writes.

---

## 10. Epistemic State Model

VERIFIED / STALE / CONTRADICTED / INFERRED / UNKNOWN are sound and map cleanly onto distinctions this codebase already half-implements (Liveness Ledger's pass/fail is already a crude VERIFIED/CONTRADICTED binary; `self_model.json`'s `ledger_stale` flag is already a real, if narrow, STALE concept).

**One addition recommended: SUPERSEDED, distinct from STALE.** STALE means "evidence changed, needs re-checking, might still be true." SUPERSEDED means "a newer, deliberate decision replaced this one, and re-verifying the old claim against new code is meaningless, not just pending." This project's own history is full of exactly this shape of change — Finding 61's Reddit-source removal, Finding 39's model retirement, Finding 82's COUNCIL.md privacy-policy reversal. A claim like "Reddit is fetched as a news source" isn't merely stale after Finding 61; it is retired, and treating it as "pending re-verification" would be actively wrong framing.

**One caution recommended on INFERRED.** Given `self_knowledge_verification.py`'s own explicit, already-adopted stance that an LLM checking an LLM's claim doesn't establish real ground truth, an INFERRED claim (derived from verified facts but not itself directly checkable) is precisely the shape of claim most likely to quietly launder into confabulation if it's ever rendered with the same visual/textual confidence as VERIFIED. Recommend: INFERRED claims should always render with an explicit hedge wherever they reach an LLM-facing surface, and should never be silently promoted to VERIFIED by an automated process — only by a human or Claude session deliberately re-authoring the claim with real evidence.

---

## 11. Architectural Archaeology Feasibility

**Partially feasible, with a concrete, already-demonstrated gap.**

Git history (131 commits, unusually self-documenting, 2026-06-28→07-24) plus CLAUDE.md's 90 Findings (74/131 commits touch it directly — largely the same record, not an independent one) could reconstruct a real "before/after" narrative for anything both committed and documented in that window.

But: (a) the single most recent, most relevant architectural mechanism this investigation found — `code_scan_hash_cache.json` — exists **only** in uncommitted working-tree state, with zero git history and zero CLAUDE.md entry; a git-log-based archaeology system would be structurally blind to it. (b) `memory/` is fully `.gitignore`d, so any *state*-level history (how the Liveness Ledger's check count actually grew from 9→41 over time, how `self_model.json`'s schema evolved) is invisible to git and reconstructable only from CLAUDE.md's prose citations of specific numbers at specific dates — a fragile, narration-dependent record, not a queryable one. (c) there are no git tags or milestone branches; correlating a commit to "which architectural claim did this affect" would today require the same manual, informal cross-referencing a Claude Code session already does by hand whenever asked "what changed."

**Verdict: this is a real Phase 3/4 capability, not retrofittable onto existing history with confidence beyond what CLAUDE.md's prose already provides.** It only becomes buildable once the claim registry from §9 exists and new commits are correlated to claim IDs *going forward* — there is no reliable way to reconstruct claim-level history *backward* past what a human already wrote down.

---

## 12. LLM Boundary / Authority Model

**The correct model already exists in this codebase and should be extended, not reinvented.** `echo_ground_truth.py`'s own header states it plainly: *"Never calls echo_query or any LLM — pure file reads."* The LLM receives (a) a disclaimed system-note block (`system_note(..., own_record=True)`) containing only facts read from disk/live functions at query time, with `_build_memory()`'s explicit instruction to say "I don't have that" rather than infer — and (b) the user's actual question, kept structurally separate. The pre-computed file or function call is the authority; string-formatting the render step involves zero LLM judgment.

**This boundary is violated in exactly one place found in this investigation: `run_self_model_reflection()`.** Here the LLM is explicitly made the interpretive authority over structural facts ("what concerns you," "what do you not yet understand") with a grounding layer that, by the code's own admission, doesn't actually cover what's being asked — and the output is persisted into memory with no downstream distinction from genuine retrieved fact.

**What the LLM should never be allowed to treat as fact, going forward:** anything it free-generates about its own architecture (the `run_self_model_reflection()` shape) unless routed through a verifier or explicitly, persistently tagged as unverified interpretation; raw source code shown to the model without extraction into a hand-verified slice first — this is exactly what `self_knowledge_verification.py`'s docstring already argues against, and what Finding 43's `log_thought` case demonstrated going wrong in practice.

---

## 13. Failure Modes and Adversarial Cases

Looked aggressively for reasons this would fail, not just reasons it would work:

1. **Source-hash-based claims can be VERIFIED while being operationally false.** `mlx_handler.py`'s `_RETIRED_MLX_MODELS`/`crash_awareness.py`'s avoidance state change `list_mlx_models()`'s actual return value based on runtime crash history, not source code — a claim like "mlx:gemma3 is a live councillor," verified by a source hash that hasn't changed, could show VERIFIED while the model is actually excluded right now. **Any claim verifier must check live runtime state, not just source-code hash**, matching the discipline the Liveness Ledger's *better* checks already follow (functional canaries + live-state reads) — and specifically *not* the discipline this project already moved away from once (import-only checks that report "wired" when nothing is actually running).
2. **`classify_role()`'s "ground truth" is itself a heuristic guess.** A pure keyword-substring match against a module's *name* (`echo_cartographer.py:187-192`) — a module that does something different from what its name implies would be silently misclassified, and any claim built on that role label would carry false confidence dressed as verified fact.
3. **Circular verification risk.** `self_knowledge_verification.py`'s own stated reason for staying narrow is exactly this: using an LLM to check an LLM's architectural claim doesn't establish anything, it just produces a second, equally fallible opinion. Any future claim graph must resist "verify unclear claim X by asking an LLM" as a fallback — that isn't verification, it's a second guess with better formatting.
4. **Verifiers themselves get bugs, at a similar rate to the code they check — demonstrated, not hypothetical, in this exact session.** Building the two Liveness Ledger checks earlier today, each had a real bug caught only by testing against real data: a check's own source-anchor search matched its *own docstring* describing the property it was meant to detect, producing a false pass (twice, in two different checks). This is the same failure class documented at least three more times in this project's history (Findings 63, 83, 84). **A "VERIFIED" label is not more trustworthy than an LLM's hedged prose unless the verifier itself has been discrimination-tested** the way `scripts/verify_liveness_ledger.py` already tests every existing check — skipping that step for a new claim system would move the confabulation risk from "the LLM guessed wrong" to "the system said VERIFIED when it was wrong," which is arguably worse because a human is *more* likely to trust a labeled verification than hedged prose.
5. **Technically true, operationally misleading.** "FAISS is queried during cross-session retrieval" is true by source inspection, but `_build_memory()`'s actual behavior (top-5-of-top-10, `user_conversation`-source only) heavily constrains what that really means in practice. A claim system that only checks "is `retrieve_relevant_memories()` still called" without capturing the real filtering behavior would produce a technically-verified, practically-misleading claim — the exact "technically true but operationally misleading" pattern this project has already named once (Finding 41-E) in a different context.
6. **Platform/environment-dependent claims.** "Self-edit runs inside a kernel-level sandbox" is true on this machine's real `sandbox-exec` availability, and would be silently false or degraded on a different OS — with no source file needing to change at all for the claim to become environment-false. A source-hash-only verifier is structurally blind to this class of failure.
7. **External-service-dependent claims.** RiverBrain's model rankings and Ollama's actual pulled-model list change based on what's available *right now*, unrelated to any source file changing — these need live-state checks, a structurally different verification shape than "did the file change," and a claim system that conflates the two will silently misreport one or the other.

---

## 14. Minimum Viable Implementation

Two changes, both reusing 100% existing infrastructure, both matching the exact extension pattern this codebase has already used 14 times:

**(a) New `_build_architecture()` slice in `echo_ground_truth.py`**, sourced from `CartographerDB` (`echo_cartographer.py`) — data that already exists, is already fresh (daily scan, confirmed today's date on disk), and is currently read by exactly one caller in the whole codebase. No new scanning mechanism required. Add `"architecture"`, `"subsystem"`, `"depends on"`, `"how does * work"`-shaped keywords to `_SLICE_SIGNALS`. This directly closes the gap demonstrated in §7: the trigger already fires correctly on "your architecture"; it just needs the right content behind it.

**(b) Fix `run_self_model_reflection()`'s confabulation-persistence gap.** Cheapest fix, matching the exact pattern already shipped earlier in this same session (the `code_analysis` exclusion fix): tag the write with a distinct, excludable `memory_source` (e.g. `"self_model_reflection"`, not folded into `"autonomous"`), and exclude that tag from `retrieve_relevant_memories()`'s unfiltered path the same way `code_analysis` now is. This does not touch the reflection mechanism itself, does not remove the daily interpretive exercise (which may have real value as a private journal), only stops it from silently resurfacing as authoritative fact in unrelated real conversations.

Both are small, both are additive, both reuse code and conventions that already exist and are already proven.

---

## 15. Phased Roadmap

**Phase 0 — done.** This report.

**Phase 1 — minimum viable architectural self-knowledge** (recommended now, see §18):
- Reuse: `CartographerDB`, `echo_ground_truth.py`'s slice pattern, the `memory_source`-exclusion pattern shipped earlier today.
- New: nothing structurally new — a new function + new dict entries in existing files.
- Files changed: `app/core/echo_ground_truth.py`, `app/emergent_scheduler.py` (or wherever the reflection write's `meta` is set), `app/core/memory_bridge.py` (exclusion, if not already covered by the existing filter's shape), `app/core/liveness_ledger.py` (one new check, matching convention).
- Risk: low — this is the identical, already-proven extension shape used 14 times before.
- Tests: a source-anchor/functional discrimination test for the new slice (mirrors `_build_touch`/`_build_vision`'s "nothing yet" fallback pattern), a retrieval-exclusion test (mirrors the `code_analysis` test written earlier today).

**Phase 2 — automatic invalidation** (only after Phase 1 is used in real conversations long enough to know which claims actually get asked about):
- New: `memory/architecture_claims.json`, `app/core/architecture_claims.py`.
- Reuse: `code_scan_hash_cache.json`'s exact hashing convention as the evidence layer.
- Risk: medium — this is genuinely new infrastructure; must be wired to a real reader (echo_ground_truth.py) from day one to avoid becoming a fifth hollow write.

**Phase 3 — architectural history** (only after Phase 2 has real claim history to diff, and only for changes going forward — not retroactive):
- Requires: git-commit-to-claim-ID correlation as a *going-forward* discipline.
- Risk: this phase has no reliable backward-looking data source beyond what CLAUDE.md's prose already provides (§11) — don't oversell what it can reconstruct about the past.

**Phase 4 — dynamic architectural self-model** (speculative, not scoped, do not build until 1–3 are proven in real use).

---

## 16. Files / Components Affected (Phase 1 only)

- `app/core/echo_ground_truth.py` — new `_build_architecture()` function, new `_SLICE_SIGNALS` entries, wiring into `get_structural_self_facts()`.
- `echo_cartographer.py` / `CartographerDB` — no changes required; already provides what's needed via `architecture_summary()` and the underlying tables.
- `app/emergent_scheduler.py` (`run_self_model_reflection()`) — tag change on the `add_to_vector_memory()` call's `meta`.
- `app/core/memory_bridge.py` (`retrieve_relevant_memories()`) — extend the existing exclusion filter (already touched earlier this session for `code_analysis`) to also exclude the new tag.
- `app/core/liveness_ledger.py` + `scripts/verify_liveness_ledger.py` — one new check + discrimination cases, matching the established convention exactly.

---

## 17. Tests We Would Need (Phase 1)

- A source-anchor or functional test confirming `_build_architecture()` reads from `CartographerDB` and degrades gracefully (matching `_build_touch`/`_build_vision`/`_build_hearing`'s "nothing yet" pattern) when the SQLite DB is missing or empty.
- A retrieval-exclusion test confirming the new `memory_source` tag never surfaces via `retrieve_relevant_memories()` with or without an explicit `source_filter` — same shape as the `code_analysis` exclusion test already written and run earlier this session.
- A Liveness Ledger discrimination test (real function → pass, degraded-fake → fail, not-importable → fail), matching every one of the 41 existing checks' proven 3-4-case pattern.

---

## 18. What I Recommend We Do Next

**Build Phase 1 only — both items, as one small, low-risk pass.** Reasoning, stated plainly:

- The full end-state system as originally specified (claim graph, five epistemic states, archaeology) would be **over-engineered relative to how every other piece of self-knowledge in this codebase was actually built** — one narrow, hand-verified slice at a time, over two months, never as a general system. This exact repository already contains four real, demonstrated cases of infrastructure built ahead of proven need becoming a hollow write (`seam_log.jsonl`, `dissent_log.jsonl`, `council_deliberations.jsonl`, `coupling_estimate_trend`). A claim graph built now, before Phase 1 is even in use, would very plausibly become a fifth.
- The two Phase 1 items are cheap, additive, reuse code and conventions that already exist and are already proven, and they close the two concrete, evidence-backed gaps this investigation actually found: (1) the keyword gate already correctly detects architecture questions and answers them with the wrong content, and (2) a real, currently-running daily mechanism already free-generates architectural self-interpretation with no guard and persists it into memory that ordinary conversation can and does retrieve.
- Everything past Phase 1 — the graph, the epistemic states, archaeology — is genuinely useful *if and only if* Phase 1 gets real use and stays accurate; building it first, speculatively, inverts the order that has worked for every other capability in this codebase.

**Waiting for your approval before implementing anything**, per your instruction.
