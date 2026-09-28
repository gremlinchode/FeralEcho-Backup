# Self-Edit Candidate Logging — Implementation Qualification

Read-only. Nothing built, wired, restarted, or modified. Git HEAD `2fba42644c82b9f7096276f4dd338d615cf1bcce` unchanged throughout (209 porcelain entries, the same pre-existing set carried through this whole session). Every claim below was independently re-checked against live source in this pass — including claims from my own two immediately-preceding reports, one of which turned out to need a correction (§2).

## 1. Executive conclusion

**The proposed field set (initial candidate source, retry candidate source, a parent/baseline hash) is QUALIFIED, with one field redefined for precision and one real dependency-surface finding that changes how it must be built, not whether it should be.** The write-only invariant is achievable and has a real, already-proven template to copy exactly — this project already has a live, narrowly-scoped ledger consumer that reads one named field and ignores everything else in the row, which is the exact safe pattern any future reader of the new fields would need to follow. No existing reader of the ledger would break, because exactly one real reader exists and it already extracts by name, not by iterating the row. The harder question — whether this proves *influence*, not just *existence* — has a clean, honest answer: **no, and it isn't supposed to.** That gap is named precisely in §12/§13, not hidden.

## 2. Independent verification of prior findings — including a correction to my own prior report

Re-checked fresh, this pass, not carried forward on trust:

- **CONFIRMED, unchanged**: `reflection_entry["generated_code"]` is set at `self_edit_manager.py:1997` and reassigned at `:2094` — the retry's code overwrites the first attempt's, in memory, before either reaches disk. Re-read both lines directly again this pass.
- **CONFIRMED, unchanged, on the live file**: `memory/self_edit_attempt_ledger.jsonl` (1,330 real rows as of this check, growing) has no field that stores generated code, confirmed by reading the actual live keys and checking every string value in the most recent row for code-shaped text (`def `/`import `) — none found.
- **CORRECTED — my own prior report understated reality here.** I previously described the attempt ledger as a "pure write-only observation sink... read by nothing in the pipeline," citing the ledger module's own docstring. That docstring is now stale relative to the actual code: `self_edit_manager.py` has a real function, `_attempt_ledger_evidence_section()` (line 2791), that calls `read_recent_f2_error()` and injects the most recent matching `initial_f2_error` text into the *next* self-edit's initial-generation prompt (`_build_targeted_prompt()`, line 2864-2866). This was built and validated for plumbing-correctness on 2026-09-07 (`audits/2026-09-07_consequential_loop_validation.md`), **but that same report explicitly states the actual behavioral-effect experiment (does this measurably change generation quality) was deliberately deferred, not run** — a disclosed, honest scope limit in that report, not an oversight. **Net correction: the ledger is no longer purely write-only in practice — one field (`initial_f2_error`) already has one real, narrowly-scoped reader. This is directly relevant to this mission's own invariant question, and is treated as the load-bearing precedent in §6/§9 below, not glossed over.**
- **CONFIRMED, live, this pass**: the dry-run precedent (`memory/wolf_dryrun.jsonl`) really does store real code next to a real failing verdict, for 36 of its 48 real entries — re-sampled a different entry than my last check, same result.
- **CONFIRMED, live, this pass**: `snapshot_manager.py` already has a proven, reusable, bytes-only hashing utility (`_sha256_file()`, line 226) and already treats `app/core/self_edit_generated.py` as one of its tracked snapshot artifacts. This is directly relevant to §7 below — it means a hashing convention for exactly this file already exists in the codebase and should be reused, not reinvented.

## 3. Exact candidate lifecycle (re-traced, current source)

```
generate_code_from_plan()                                    self_edit_manager.py:1797
  current_contents = open(SELF_EDIT_FILE).read()              line 1808  ← PARENT SNAPSHOT POINT (see §7)
  code_prompt built from current_contents + plan
  model_name, _ = choose_model(...)
  code = echo_query(code_prompt, ...)                         ← INITIAL CANDIDATE EXISTS HERE, in memory
  code = _strip_markdown_fences(code); ... ; code = _apply_self_edit_output(code)
  return code, model_name
        ↓ (back in execute_self_edit())
reflection_entry["generated_code"] = code                     line 1997  ← FIRST durable-bound copy (in-memory dict)
success, sandbox_error = test_code_in_sandbox(code)           ← INITIAL EXECUTION (real F2 kernel sandbox)
  ├─ success=True  → continue
  └─ success=False → _attempt["initial_f2_outcome"]=False
                      _attempt["initial_f2_error"]=sandbox_error      ← INITIAL FAILURE, captured (error only)
                      retry_prompt built from _sanitize_sandbox_error(sandbox_error)
                      retry_code = echo_query(retry_prompt, ...)      ← RETRY CANDIDATE EXISTS HERE
                      reflection_entry["generated_code"] = retry_code  line 2094  ← OVERWRITES the line-1997 copy
                      retry_success, retry_error = test_code_in_sandbox(retry_code)   ← RETRY EXECUTION
                      _attempt["retry_occurred"]=True; retry_f2_outcome/error set
[terminal branches] _finish_attempt(terminal_state) → _record_attempt_ledger(dict(_attempt))   ← LEDGER WRITE, single call site
```

## 4. Exact evidence-loss points

Two, both already named in my prior report and reconfirmed here with no change: (1) `reflection_entry["generated_code"]`'s overwrite at line 2094, destroying the first attempt's *code* the instant a retry runs (the *error text* survives separately in `_attempt`, only the code doesn't); (2) the ledger's `_attempt` dict never had a code slot to begin with. **New precision this pass**: the ledger write itself (`_record_attempt_ledger`) happens at the *end*, at whichever terminal branch is reached — meaning if a candidate-code field is added to `_attempt`, it must be *set* at the same point `initial_f2_error` is already set (immediately after the F2 call, using the `code`/`retry_code` variables that are already in scope there), not computed lazily at write time, because `code`/`retry_code` are local to `generate_code_from_plan()`'s caller and would not be reliably available at the `_finish_attempt()` call site otherwise. This is a real, concrete implementation constraint, not just a preference.

## 5. Proposed minimum evidence set — the three original fields, examined one at a time

- **`initial_candidate_code`**: **REQUIRED, unchanged.** The one artifact this whole line of investigation exists to preserve.
- **`retry_candidate_code`** (null if no retry): **REQUIRED, unchanged.** FeralEcho's own current blind-retry mechanism is itself a real, if crude, repair attempt — its content is directly relevant evidence, not optional extra.
- **`parent_baseline_hash`**: **REQUIRED, but redefined for precision, per the mission's own explicit demand not to accept a rigorous-sounding-but-ambiguous field.** Precise definition, tied to an exact line of code rather than a vague notion of "current production": **the sha256 of `current_contents` as read at `self_edit_manager.py:1808`, at the moment this specific attempt's prompt was built** — not "whatever `self_edit_generated.py` looks like now" (ambiguous, time-of-query-dependent) and not a git commit hash (the file is git-tracked, confirmed this pass, but commits happen on a human's schedule, not per self-edit attempt, so a git hash would usually be stale relative to the exact moment generation happened, especially since multiple real attempts can occur between commits). **Recommend reusing `snapshot_manager._sha256_file()`'s exact byte-only hashing method** (confirmed already proven, already used on this exact file) rather than writing a second hash utility.
- **No fewer fields would suffice**: without `parent_baseline_hash`, a stored candidate can't be checked against what it was actually a diff of — a repair validity test needs both the failing code and what it was failing *against*. Without either candidate field, the central VRM-style question (would earlier experience have repaired a later failure) stays exactly as untestable as my prior report found.
- **No more fields are required for this specific, narrow qualification.** A hash of each candidate (`initial_candidate_hash`/`retry_candidate_hash`) remains genuinely USEFUL but not required — recomputable from the stored code at any time, so its absence doesn't block anything, only adds a cheap convenience.

## 6. Ledger/storage dependency surface — traced exhaustively, not assumed

**Every real hit found by grepping for the ledger module, the file path, and the function name across the whole repository**, each individually checked rather than trusted:

| Match | Real consumer? | Finding |
|---|---|---|
| `app/core/self_edit_attempt_ledger.py` | Yes (the module itself) | Defines `record_attempt()` (pure append, best-effort, never raises) and `read_recent_f2_error()` (returns the *whole* parsed row, see below). |
| `app/core/self_edit_manager.py` | Yes | The one real writer (`_finish_attempt`) and the one real reader (`_attempt_ledger_evidence_section`). |
| `scripts/verify_attempt_ledger_prompt_evidence.py` | Yes, a test | Redirects `_LEDGER_PATH` to a scratch tempfile before running, confirmed by reading its own header — never touches the real file. |
| `staging/self_edit_candidate.py` | **No — false positive.** | A stale, commented-out draft self-edit candidate sitting in the transient staging directory; the two matching lines are Python comments (`# from app.core import self_edit_attempt_ledger`), not executed code. |
| `app/core/self_model_claims.py` | **No — false positive.** | A comment referencing the same safety-discipline pattern by name, not an import or call. |
| `app/internet_tools/claude_research.py` | **No — false positive.** | Has its own, unrelated, locally-defined `_record_attempt()` function (tracking Claude-research call cadence) — a coincidental name collision, confirmed by reading the function body, nothing to do with self-edit. |

**The critical detail for the write-only invariant**: `read_recent_f2_error()` (the one real reader's own data source) returns the **entire parsed dict** for the best-matching row (`best = entry`, confirmed by direct read of the function body) — it does *not* pre-filter to a safe subset before returning. **Safety currently depends entirely on the caller** (`_attempt_ledger_evidence_section()`) choosing to extract only `entry.get("initial_f2_error", "")` and discard the rest — confirmed directly, that function touches no other key. **This means adding `initial_candidate_code`/`retry_candidate_code` to the row today is safe only because the one real caller doesn't iterate the row — it is not safe by any structural guarantee of the ledger module itself.** This is a real, precise finding this qualification exists to surface: **if a future change ever makes `_attempt_ledger_evidence_section()` (or a new consumer) start passing the whole `entry` dict into a prompt, log line, or any other surface — instead of continuing to extract one named field — the new code fields would leak into generation with no additional gate to stop it.** Recommend, as part of implementing this (not now, but noted for whoever does): a one-line comment at the top of `read_recent_f2_error()`'s docstring stating plainly that it returns a full row including any future fields, and that every caller is individually responsible for extracting only what it needs — making the existing implicit safety property an explicit, documented contract instead of an accident of how the one current caller happens to be written.

**Analytics/dashboards/backup jobs**: none found touching this file specifically (checked via the same repo-wide grep); this project's existing dashboard code (`echo_studio/views/health_dashboard_view.py`, per this session's earlier reading of CLAUDE.md) reads `introspection_channel.py`'s aggregated state, not the raw ledger file directly.

## 7. Parent/baseline provenance semantics — answered precisely, per §5

**What exact artifact is "the parent"?** The byte content of `app/core/self_edit_generated.py`, read once at `self_edit_manager.py:1808`, at the specific moment this specific attempt's prompt-construction began. Not "current production" in the abstract (ambiguous — production can and does change between when a prompt is built and when its candidate is eventually judged, since the fitness gate compares against *current* production at judgment time, a possibly-different moment). **This distinction matters and must not be blurred**: the *fitness gate*'s `current_quality` check (already existing, unchanged by this proposal) reads production at judgment time; the *proposed* `parent_baseline_hash` would record production at generation-start time. These can legitimately differ if another self-edit deploy landed in between — a real, if rare, possibility given Optuna's ~10 dry-run trials/hour running alongside the hourly real attempt. **Recommend naming the field `parent_baseline_hash_at_generation` if this ambiguity is judged worth resolving in the name itself**, rather than leaving `parent_baseline_hash` to imply a single, unambiguous "the" parent when two meaningfully different moments could both plausibly claim that title.

**Can it be deterministically hashed?** Yes — `snapshot_manager._sha256_file()` already does exactly this, on exactly this file, already proven safe (bytes-only, never a pickle/format loader, confirmed by its own docstring and this pass's direct re-read).

**Does an existing identifier already provide this?** Partially, and worth naming rather than silently duplicating: `snapshot_manager.py`'s own periodic snapshots already hash `self_edit_generated.py` — but only at snapshot time (startup, or immediately after a *successful* self-edit deploy), not once per attempt. A rejected or failed attempt (the overwhelming majority, per this session's own VRM investigation) occurs *between* snapshots and would not have a matching snapshot-time hash to reuse. **Recommendation: reuse the hashing *function*, not the existing snapshot *records* — compute a fresh hash per attempt using the same proven method, rather than trying to retroactively match an attempt to whichever snapshot happened to be nearest in time (which would itself be an ambiguous, error-prone join).**

## 8. Storage strategy

**Recommend: inline in the ledger row, not a separate content-addressed store.** Reasoning, checked against the mission's own listed concerns:
- **Duplicate candidates**: a hash field (§5, USEFUL not REQUIRED) makes exact-duplicate detection cheap without needing CAS; genuine near-duplicates still require reading the text either way, so CAS buys nothing extra here.
- **File growth**: re-confirmed this pass — real attempt volume is on the order of 60-90/day (unchanged from the prior report's measurement, re-derived from the same ledger this pass shows continuing at a consistent rate), candidate size 1-3KB. Inline growth stays in the single-digit-MB/month range, confirmed order-of-magnitude consistent with the prior report.
- **Atomicity**: the existing `_ledger_lock` (a plain `threading.Lock()`, already guarding the single `record_attempt()` append) covers a larger row exactly as it covers the current smaller one — no new locking primitive needed.
- **Malformed Unicode**: `json.dumps()` (the existing write path) already handles arbitrary Python strings, including malformed-looking generated code, by escaping — no special handling needed beyond what's already there; a genuinely non-UTF8-decodable byte sequence would have already failed earlier in the pipeline (Python string handling upstream), not a new risk this change introduces.
- **Very large generations**: self-edit's own documented scope (single-function, targeted changes per Finding 16/32's convergence-tracking history) keeps this bounded in practice; if ever a genuine outlier occurred, the existing `record_attempt()`'s best-effort/never-raise contract means a JSON-serialization failure degrades to "this one row's write is silently skipped," not a crash — an acceptable, already-proven failure mode, not a new one.
- **Partial writes**: `record_attempt()` opens the file in append mode and writes one line, then closes — the existing, already-proven crash-tolerance story (§10) is unchanged by a longer line.

**Content-addressed storage would be over-engineering here** — it solves a scale problem (many megabytes to gigabytes of unique content, needing dedup) this project doesn't have at its real, measured volume.

## 9. Inertness / security analysis

Re-verified, not assumed, against the specific list of paths the mission named:
- **Execution/import/evaluation**: storing a string in a JSONL row cannot execute it — confirmed this is true of the *existing* `initial_f2_error` field today (real tracebacks, sometimes containing fragments of blocked dangerous calls, already sit in this exact file and have never been executed by anything that reads it) — the same reasoning applies unchanged to a code field.
- **Indexing into active memory / prompt inclusion**: the one real reader (§6) extracts exactly one named field and ignores the rest — a new code field is not read by anything today. The one honest, disclosed residual risk (§6's finding): this safety is currently a property of how the one caller happens to be written, not a structural guarantee of the ledger module. Recommend documenting this explicitly as part of implementation, not treating it as self-evidently permanent.
- **Deployment/restoration into production**: no code path reads the attempt ledger to decide what to deploy — deployment reads only `code`/`retry_code` local variables directly, in the same function call, never round-tripping through the ledger file. Confirmed by the lifecycle trace in §3 — the ledger write happens at or after the terminal branch, strictly after any deploy decision, never before or feeding into one.
- **RiverBrain, model selection, council/synthesis, fitness/deployment decisions, future attempts**: none of these read the ledger file at all today (§6's exhaustive grep found exactly one real reader, and it's none of these) — the new fields would be exactly as inert to all of them as `initial_f2_error` already is.

## 10. Concurrency / crash behavior

Traced against the mission's six named moments:
- **Before candidate persistence** (i.e., before the ledger write happens at all — since candidate persistence *is* the ledger write in this design): a crash here means the attempt simply never gets a ledger row, same as today — no false claim is created, because nothing is claimed. Correct, safe default.
- **After persistence but before execution**: cannot occur in this design, because the proposed capture point (§4) sets `_attempt["initial_candidate_code"]` immediately *after* `test_code_in_sandbox()` already ran and returned a real result — code and its execution outcome are captured together, in the same in-memory step, not persisted separately before execution.
- **During execution**: F2 itself already handles this (a hung/crashed sandbox subprocess is F2's own existing timeout/error-handling concern, unchanged by this proposal).
- **After execution but before result persistence**: the real, structural risk — if the whole `execute_self_edit()` process crashes between setting `_attempt["initial_f2_outcome"]` and reaching `_finish_attempt()`, the entire row (execution result *and* candidate code, together) is lost, exactly as today's rows are already lost in this scenario. **This proposal does not make this specific window worse — the code and its outcome are already bound together in the same in-memory dict as the existing fields, so a crash here loses the whole record, not a partial, misleading one.** This is the honest answer to the mission's "generated candidate vs. executed candidate" distinction: **because the code is captured only after execution already produced a real result, no record can ever claim a candidate "was executed" when it wasn't** — there is no intermediate state where code exists in the ledger without also having a real F2 outcome attached, by construction of where the capture point sits in the code.
- **During retry**: same reasoning, one level in — `retry_candidate_code` is set only after `test_code_in_sandbox(retry_code)` already returned.
- **During ledger write itself**: unchanged from today's existing, already-proven behavior — a single `open(...).write()` under a lock; a crash mid-write could in principle leave a truncated final line, which any JSONL reader must already tolerate as a matter of course (this is not a new failure mode introduced by longer rows).

**Concurrency and misattribution**: `trace_id` is minted once per `execute_self_edit()` call and threaded through the same in-memory `_attempt` dict that would hold the new fields — two concurrent attempts (a real possibility given Optuna's dry-run trials) cannot cross-contaminate each other's candidate code, because each call has its own local `_attempt` dict and its own local `code`/`retry_code` variables; nothing here is shared mutable state across calls.

## 11. Observational-equivalence test design

Proposed, not run:
1. **Generation/retry/execution/fitness/deployment**: run a matched pair of self-edit cycles with identical seeds/prompts (or, more realistically given real Ollama non-determinism, statistically comparable real cycles) with the logging change present vs. absent, and confirm: same candidate code is produced (same model call, same inputs — the logging change adds no new read that could alter the prompt), same F2 outcome, same fitness decision, same deploy/no-deploy result. **Expected result, statable in advance**: identical, because the proposed change only *appends a value already computed* to a dict that already exists and is already written — it introduces no new read, no new branch, no new conditional anywhere in the generation/execution/fitness path.
2. **Persistent learning state (RiverBrain) / model-selection state**: confirm `model_task_stats` before and after a logged cycle is identical to before and after an unlogged one — trivially true, since the proposed change touches none of RiverBrain's call sites, confirmed by the lifecycle trace (§3) showing the new fields are set entirely within `_attempt`, never passed to `river.learn()`/`learn_from_sandbox_outcome()`.
3. **Timing**: measure wall-clock time for `_finish_attempt()`'s write with and without the new fields, on a realistic candidate size (1-3KB) — expect a difference on the order of microseconds to low milliseconds (one JSON serialization of a few extra KB), utterly dwarfed by the tens-to-hundreds-of-seconds real Ollama calls already dominating each cycle (confirmed order-of-magnitude from this session's own AP-0/reconciliation timing data). **Cannot claim this is exactly zero difference — only that it is not a difference plausibly capable of mattering to anything downstream**, an honest, bounded claim rather than an overclaimed "no effect whatsoever."

## 12. Future experimental value

**What this WOULD establish, if built**: whether a stored failing candidate, from a strictly earlier time, shares enough structure with a strictly later failing candidate that a transformation validated against the earlier one could be tested against the later one's real, preserved source — closing exactly the VRM-2 gap this session's prior VRM report found completely blocked today.

## 13. What this does NOT establish — the artifact-provenance vs. influence-provenance distinction, addressed directly, not glossed over

**Artifact provenance** ("what did Echo try") is what §5-§11 above qualifies. **Influence provenance** ("what prior experience did Echo actually have available, or actually use, when producing a later attempt") is a **different, harder, and currently unaddressed question — this logging change does not solve it, and must not be described as if it did.**

Here is the honest, precise state of that second question today, checked directly rather than assumed: for the *code-generation* step specifically, the answer is currently trivial and verifiable by omission — **nothing today feeds any prior candidate's code into a later attempt's prompt at all** (confirmed, §3's lifecycle trace: `generate_code_from_plan()`'s prompt is built from `current_contents` + the plan text only). The *one* real exception, found in §2's correction, is `initial_f2_error` text (not code) being injected via `_attempt_ledger_evidence_section()` — and even there, the actual behavioral effect of that injection is explicitly unproven (§2, citing the 2026-09-07 validation report's own disclosed deferral).

**This means: today, "was prior experience actually used" has a clean, correct, negative answer for candidate code specifically, by construction — because nothing consumes it.** That will remain true the moment this logging change ships, and it should remain true — this mission does not propose building a consumer. The moment a *future*, separately-designed experiment does introduce a consumer (e.g., feeding a stored earlier candidate into a later generation prompt, the way `initial_f2_error` already is for error text), **that future experiment must log, separately, exactly what it fed into that specific prompt** — the evidence proposed here does not automatically provide that, and no amount of preserving *past* candidates retroactively tells you what a *future* mechanism actually looked at. Preserving artifact provenance is a necessary precondition for that future experiment to even be possible; it is not a substitute for that experiment also instrumenting its own consumption honestly.

## 14. Simplest implementation plan, if qualified (not implemented here)

- Add three fields to the existing `_attempt` dict literal (`self_edit_manager.py`, near line 1904): `initial_candidate_code: None`, `retry_candidate_code: None`, `parent_baseline_hash: None`.
- Set `_attempt["parent_baseline_hash"]` once, early, from `hashlib.sha256(current_contents.encode()).hexdigest()` — reusing `current_contents`, which is already read at line 1808 for the prompt itself (no new file read).
- Set `_attempt["initial_candidate_code"] = code` at the same point `_attempt["initial_f2_error"]` is already set (immediately after the first `test_code_in_sandbox()` call returns).
- Set `_attempt["retry_candidate_code"] = retry_code` at the same point `_attempt["retry_f2_error"]` is already set.
- No change to `record_attempt()`, `read_recent_f2_error()`, or `_attempt_ledger_evidence_section()` — the existing write-through and the existing narrow-extraction reader both continue working unchanged, by construction (§6).
- One documentation addition, not a behavior change: a comment on `read_recent_f2_error()` stating explicitly that it returns the full row and that callers must continue to extract only named fields — making §6's currently-implicit safety property explicit.

## 15. Required tests

1. Unit test: a synthetic failing `execute_self_edit()` call confirms `_attempt["initial_candidate_code"]` exactly matches the string passed to `test_code_in_sandbox()`.
2. Same, for the retry path, confirming it only populates when `retry_occurred` is true.
3. `parent_baseline_hash` matches an independently-computed `hashlib.sha256()` of a known test file's content.
4. Regression: `scripts/verify_attempt_ledger_prompt_evidence.py`'s existing suite still passes unchanged (confirms the new fields don't disturb the one real existing reader).
5. A new, explicit regression test asserting `_attempt_ledger_evidence_section()` still extracts *only* `initial_f2_error` from a synthetic row that also contains the new candidate-code fields — directly testing §6's safety property, not just hoping it holds.
6. A record-attempt failure-mode test: feed `record_attempt()` a dict with a non-serializable value and confirm the existing silent-fail contract still holds with the larger row shape.

## 16. Reasons to reject or defer — actively attempted, not perfunctory

- **Existing infrastructure already preserves enough?** No — independently re-confirmed in §2/§4, the gap is real and precisely located, not resolved by anything already shipped.
- **Security problems from storing full source?** Not found — §9's analysis, checked against every named path, found the new fields exactly as inert as the existing traceback field already is.
- **Ledger readers break?** No — exactly one real reader exists, and it's safe by construction (§6), though the *reason* it's safe (a coding convention, not a structural guarantee) is itself worth fixing at the same time, not a reason to reject.
- **Logging affects timing enough to matter?** No — bounded and dwarfed by existing real model-call latency (§11).
- **Concurrent attempts make attribution unreliable?** No — each attempt's `_attempt` dict and local variables are independent, `trace_id`-scoped (§10).
- **Storage estimate wrong?** Re-derived this pass from the live, currently-growing ledger and found consistent with the prior report's order of magnitude — not found wrong.
- **Source alone insufficient to reconstruct execution?** Partially true, and named honestly: source plus its F2 outcome (already captured) is sufficient to know *what was tried and what happened*; it is not sufficient, alone, to prove a future mechanism's *transformation-generation* step would work — a distinct, larger, unaddressed question (§13), correctly out of scope for a logging qualification.
- **Parent provenance cannot be established?** It can, precisely, once redefined as in §7 — the original phrasing ("parent_baseline_hash") was genuinely ambiguous until pinned to an exact line and moment; not ambiguous once pinned.
- **Dry-run precedent not comparable?** Partially fair — `wolf_dryrun.jsonl`'s path never retries, so it never faced the overwrite problem this proposal specifically targets; it's evidence that storing code-plus-verdict is safe and cheap, not evidence that the retry-overwrite case specifically is solved elsewhere. Correctly used only for the narrower claim in this report.
- **A simpler mechanism exists?** None found that closes the same gap with less code — this proposal is already the minimum extension of a mechanism (`self_edit_attempt_ledger.py`) built for exactly this purpose two weeks ago.

**No clean NO-GO was found.** The proposal survives every attack attempted against it, with one real, honest caveat carried forward rather than dismissed: the write-only invariant currently rests on a coding convention in one function, not a structural guarantee, and that should be made explicit (§14's documentation step) at the same time this ships.

## 17. Final recommendation

Qualified for implementation, with the two precision fixes carried through this report: rename or clearly redefine `parent_baseline_hash` to name the exact moment it captures (§7), and add the one-line explicit-contract comment to `read_recent_f2_error()` (§6/§14) in the same change, so the safety property this report found — real today, but implicit — becomes a documented one instead of an accident of how the current single caller happens to be written.

---

**ARTIFACT PROVENANCE GAP:** CONFIRMED

**PROPOSED LOGGING CHANGE:** QUALIFIED

**BEHAVIORAL INERTNESS:** SUPPORTED

**EXISTING CONSUMER COMPATIBILITY:** SUPPORTED

**READY FOR IMPLEMENTATION:** CONDITIONAL — conditional only on the two precision fixes in §17 being included in the same change, and on this report itself being reviewed and explicitly approved before anything is written, per this project's own standing report-then-pause discipline. No open technical question remains.

**What is the smallest change we should actually make, and what claim will that change allow us to test later that we cannot test today?** Add three fields — the initial candidate's code, the retry candidate's code (if any), and a precisely-defined hash of the production file at the moment generation started — to the attempt-ledger row that already exists for every self-edit attempt, set at the same points neighboring fields are already set, using the same lock and fail-silent write already proven safe. That change would let a future, separately-designed and separately-authorized experiment ask, for the first time, whether a repair validated against an earlier real failure would actually have fixed a later real failure sharing its structure — a question this session's own VRM investigation found completely unanswerable from history today, because the one artifact that question depends on has never once been preserved. It would still not tell us whether any future mechanism actually uses that evidence, or uses it well — only that the evidence would finally exist to check.
