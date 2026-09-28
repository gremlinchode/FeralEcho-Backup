# Self-Edit Evidence Preservation Investigation

Read-only. Nothing built, modified, restarted, or deliberately triggered. Git HEAD `2fba42644c82b9f7096276f4dd338d615cf1bcce` unchanged before and after (207 porcelain entries throughout, the same pre-existing set from earlier in this session). This mission follows directly from the VRM retrospective feasibility investigation, whose central finding — no historical self-edit attempt's actual generated code survives anywhere — is independently re-verified here, not assumed, and substantially extended by three prior audits this investigation located and read in full (`audits/2026-09-06_real_trace_f2_provenance_liveness.md`, `audits/2026-09-07_attempt_level_provenance_feasibility.md`, `audits/2026-09-07_consequential_learning_loop_design.md`) that had already done a large, directly relevant piece of this exact question two weeks earlier.

## 1. Executive conclusion

**OBSERVED, independently reconfirmed:** FeralEcho preserves rich, structured *metadata* about every real self-edit attempt (`memory/self_edit_attempt_ledger.jsonl` — trace_id, timestamps, full real tracebacks, retry linkage, fitness scores, deployment decision) but has never once preserved the *generated source code* of a failing attempt, and even a successful attempt's code survives only as the single most-recent value in a field that a subsequent retry silently overwrites. The gap is not "no evidence exists" — a great deal exists — it is specifically and only "the one artifact a repair-content mechanism (VRM or anything like it) would need to validate a transformation against was never captured." **The fix is small, additive, and does not require redesigning anything already working.**

**A second, important OBSERVED finding, not previously stated as sharply as it should be:** FeralEcho already has one real, closed, currently-running consequential learning loop — `choose_model("self_edit_coding")` → `generate_code_from_plan()` → `RiverBrain.learn()` → `model_task_stats` mutation → the *next* `choose_model()` call reading the mutated state — traced end-to-end with code citations by the 2026-09-07 design audit. This loop governs *which model* gets asked, not *what content* gets generated. Evidence preservation for VRM-style repair content is a genuinely separate question from this loop, and should not be conflated with it or wired into it.

**A third, load-bearing prior finding this investigation must not ignore:** a real, already-run experiment ("Architecture A", cited in the 2026-09-07 design audit) tested injecting a causal failure-diagnosis into the *retry* prompt specifically and found **zero measurable effect** (5/6 vs 5/6, identical). This is direct evidence, not speculation, that at least one plausible way of using preserved failure evidence already failed empirically. It does not mean evidence preservation is worthless — the same audit notes the *initial*-generation injection point remains untested — but it means any recommendation here must not imply that simply capturing more evidence guarantees a future mechanism will work.

## 2. Current self-edit lifecycle (independently retraced, current source, not merely cited from the prior audits)

```
perform_self_edit(prompt=None)                          self_edit_manager.py
  └─ execute_self_edit(prompt, dry_run)                  self_edit_manager.py:1867
        trace_id = uuid.uuid4()                          line ~1892   ← ORIGIN
        _attempt = {trace_id, task_type=None, timestamp,
                    initial_f2_outcome=None, initial_f2_error=None,
                    retry_occurred=False, retry_f2_outcome=None,
                    retry_f2_error=None, final_f2_outcome=None,
                    fitness_score=None, production_score=None,
                    fitness_decision=None, deployed=False,
                    terminal_state=None}                 line ~1904   ← in-memory only until _finish_attempt()
        reflection_entry = {prompt, task_type, generated_code=None,
                             timestamp, sandbox_feedback=None,
                             result="pending"}            (separate dict, no trace_id field)
        plan = plan_code_logic(..., trace_id=trace_id)    real council call, logged w/ trace_id
        code, model = generate_code_from_plan(..., trace_id=trace_id)
              reflection_entry["generated_code"] = code   line 1997    ← FIRST assignment
              river.learn(model, "self_edit_coding", code)             ← real RiverBrain write (heuristic-scored)
        success, sandbox_error = test_code_in_sandbox(code)   ← F2, FIRST PASS, real kernel sandbox
          ├─ success=True  → river.learn_from_sandbox_outcome(True, code=code); continue
          └─ success=False → river.learn_from_sandbox_outcome(False, error=sandbox_error)
                _attempt["initial_f2_outcome"]=False; ["initial_f2_error"]=sandbox_error   ← PRESERVED, full traceback
                clean_error = _sanitize_sandbox_error(sandbox_error)   ← local var, used only to build retry prompt
                retry_code = echo_query(retry_prompt, trace_id=trace_id)
                  reflection_entry["generated_code"] = retry_code      line 2094   ← SECOND, OVERWRITING assignment
                retry_success, retry_error = test_code_in_sandbox(retry_code)
                  _attempt["retry_occurred"]=True; ["retry_f2_outcome"]=...; ["retry_f2_error"]=...   ← PRESERVED
        _stage_and_import_test(code, ...)                 F3-equivalent staging check
        [terminal branches: import_hallucination / safety_blocked / staging_import_failed /
         rejected_not_improvement / load_blocked / success — each calls _finish_attempt(state)]
        _finish_attempt(terminal_state):
              _attempt["terminal_state"] = terminal_state
              _record_attempt_ledger(dict(_attempt))       ← ONE call site (confirmed by grep), fires on every branch
        [only on the success branch] backup_existing_code() + save_code(code) + load_self_edit_module()
              save_reflection(reflection_entry)             → memory/reflection_shard.jsonl (durable, LAST code only)
              record_pending_outcome(task_type, trace_id)   → memory/self_edit_outcomes.jsonl (ONLY on real deploy)
```

**Where things exist, and where they stop:**
- **Task/problem origin**: `SelfModelUpdater().get_weak_task_type()` → `_build_targeted_prompt()`. Real, deterministic, not part of the evidence-loss problem.
- **Context reaching generation**: the full self-edit prompt (current file contents + plan + Focus text) — computed fresh each time, not itself persisted as a distinct artifact separate from the plan file (`app/core/self_edit_plans/plan_<timestamp>.txt`, capped at 500 by Finding 58's retention policy).
- **Where candidate code is produced**: in-memory only, inside `generate_code_from_plan()`'s return value and `reflection_entry["generated_code"]` / the local `code`/`retry_code` variables.
- **Execution**: `test_code_in_sandbox()` → real `sandbox-exec` kernel jail, via `safe_exec_wrapper.py`. Genuinely independent of the LLM's own claims.
- **stdout/stderr/tracebacks**: captured as `sandbox_error`/`retry_error` (full text), and — **OBSERVED, this is the one piece of good news** — the *first-pass* traceback is durably preserved verbatim in `self_edit_attempt_ledger.jsonl`'s `initial_f2_error` field, confirmed directly against 881 real rows in this session's own prior VRM investigation. This closes exactly the gap the 2026-09-06 audit found missing two weeks ago (`f2_first_pass_error` was "UNAVAILABLE from production data" then; the ledger built in direct response now preserves it).
- **What is overwritten/destroyed**: the actual *code* (not the error text) of a first-attempt failure, the instant a retry occurs — `reflection_entry["generated_code"]` is reassigned at line 2094, and the ledger never stored code at all, by design (see its own docstring's explicit exclusion list, quoted below). This is the real, specific, and only significant gap.
- **What reaches RiverBrain**: `model_name` and the response *text*, scored by a heuristic (`learn()`) or a boolean (`learn_from_sandbox_outcome()`) — neither ever persists the code as an inspectable artifact; RiverBrain's own state is a rolling statistic, not a code store.
- **Identifiers connecting stages**: `trace_id` (one per attempt, threaded through `plan_code_logic()`, `generate_code_from_plan()`, `interaction_log.jsonl`, `council_deliberations.jsonl`, and the attempt ledger) is the one reliable join key across every durable artifact that has it. `self_edit_outcomes.jsonl` also carries it, but only on the rare real-deploy path.

## 3. The evidence-loss boundary — independently re-verified, not assumed from the prior report

**Did the code ever exist as a complete artifact?** Yes, always, in-process, for every attempt — `code`/`retry_code` are complete, syntactically-real Python strings at the moment `test_code_in_sandbox()` runs. This was never a "the code was never fully generated" problem.

**At what exact point is it discarded?** Two distinct mechanisms, both confirmed directly against current source in this session:
1. **Overwrite**: `reflection_entry["generated_code"] = code` (line 1997) is unconditionally replaced by `reflection_entry["generated_code"] = retry_code` (line 2094) the moment a retry occurs — regardless of whether the retry succeeds. The *first* attempt's code is gone from this dict, in memory, before it's ever written to disk (`reflection_shard.jsonl` only receives whichever value the dict holds at the terminal branch).
2. **Never captured**: the attempt ledger (`self_edit_attempt_ledger.py`) was built specifically to close the metadata half of this gap and, per its own stated design philosophy, *deliberately* never stores code, diagnosis, or any interpreted field — "no diagnosis, no causal explanation, no confidence score, no relevance score, no 'lesson' field... every field here is an observable fact with a single, traceable source line." Preserving code was never in this module's scope, by design, not by oversight.

**Could current logs reconstruct it exactly?** No. Re-verified directly, going beyond the prior VRM report's search: `staging/` (the per-call-unique F2 staging file) is transient and already overwritten by unrelated work; `self_edit_backups/` retains only the 25 most recent *deployed* versions, named by timestamp, not by trace_id; `self_edit_plans/` holds the input plan text, not generated code; `SELF_EDIT.log`'s 162,967 narrative lines carry a truncated prompt prefix and truncated reason string, no code, and — checked directly this session — essentially no trace_id linkage (119 trace_id-shaped substrings across the entire file, not systematically joinable to specific rows); `apply_to_code_invocations.jsonl` records only `before_len`/`after_len` integers, never text, by explicit design (Finding 31/69, for an unrelated safety reason).

**Are successful candidates preserved differently?** Yes, and better, but still incompletely: a *deployed* candidate's final code is preserved as a real file in `self_edit_backups/` (until pruned past 25) and as the live content of `app/core/self_edit_generated.py` itself. But this is only the version that reached deployment — if a first attempt failed F2 and a retry succeeded and deployed, the *first, failing* attempt's code is still gone, even though the overall attempt was a "success."

**Are hashes/IDs available to establish identity?** `trace_id` is real and reliable for correlating metadata across files. No hash of the generated code itself is computed or stored anywhere in the current pipeline — confirmed by grep, no `hashlib`/`sha256` call exists in `execute_self_edit()`'s own body.

**Could concurrent attempts create attribution ambiguity?** Real risk, structurally present but not exercised: `_self_edit_deploy_lock` serializes the deploy-decision critical section (Finding 22 Batch 4), but Optuna's ~10 dry-run trials/hour and the hourly real attempt can, in principle, be mid-flight concurrently before that lock is acquired. `trace_id` is minted per-call and threaded consistently, so as long as any future code-preservation write includes `trace_id`, concurrent attempts remain distinguishable — this is not a new risk introduced by the proposal below, but worth stating as a precondition it must satisfy (see §4).

## 4. Existing persistent evidence — inventory, corrected against direct verification

| Artifact | What survives | What doesn't |
|---|---|---|
| `memory/self_edit_attempt_ledger.jsonl` | trace_id, timestamp, task_type, full raw tracebacks (`initial_f2_error`/`retry_f2_error`), retry occurrence/outcome, fitness/production scores, terminal state, deployed flag — one row per attempt, every branch | The generated code itself, in any form |
| `memory/reflection_shard.jsonl` | The *last* code version this attempt produced (post-retry if one occurred), prompt, task_type, sandbox_feedback string, result | The *first* attempt's code if a retry occurred; no trace_id field; `sandbox_feedback` becomes the uninformative literal `"success_on_retry"` on that path, destroying even the *fact* of what the first error was in this file (the ledger elsewhere preserves the fact, just not in this file) |
| `memory/SELF_EDIT.log` | A truncated one-line narrative per terminal event | Code, most of the diagnosis, reliable trace_id linkage |
| `app/core/self_edit_backups/` | Up to 25 most recent *deployed* full files, by timestamp | Everything non-deployed; not trace_id-addressable |
| `app/core/self_edit_plans/` | Up to 500 most recent input plan texts | The candidate code that resulted from each plan |
| `memory/self_edit_outcomes.jsonl` | Pre/post quality-signal deltas around a real deploy, with trace_id | Only exists for the rare deploy-success path; no code |
| `memory/interaction_log.jsonl`, `memory/council_deliberations.jsonl` | The real `echo_query()`/deliberation text for plan/codegen/retry calls, trace_id-linked | Not scoped to self-edit's own candidate-vs-outcome question; a valid but indirect and expensive way to recover code text (the *response* text of the codegen/retry call, before cleanup functions like `_strip_markdown_fences()`/`_apply_self_edit_output()` run — a real but imperfect proxy for the exact code `test_code_in_sandbox()` actually received) |

## 5. Minimum sufficient schema

**Design principle, matching the discipline this project already applies to `self_edit_attempt_ledger.py` itself:** attempt facts (objective, independently checkable) only. No diagnosis, no confidence score, no "lesson." This proposal is an *extension* of the existing ledger's own fields, not a new philosophy.

```
trace_id                 str    — already minted; join key
timestamp                str    — already present
task_type                str    — already present
initial_candidate_code   str    — NEW: the exact `code` string passed to the FIRST test_code_in_sandbox() call
initial_candidate_hash   str    — NEW: sha256 of the above, for cheap dedup/identity checks
initial_f2_outcome       bool   — already present
initial_f2_error         str    — already present (full traceback)
retry_occurred           bool   — already present
retry_candidate_code     str|null — NEW: the exact `retry_code` string, only if retry_occurred
retry_candidate_hash     str|null — NEW
retry_f2_outcome         bool|null — already present
retry_f2_error           str|null — already present
final_f2_outcome         bool   — already present
parent_baseline_hash     str    — NEW: sha256 of app/core/self_edit_generated.py's content at the moment generation started (what the candidate was a modification of)
fitness_score            int|null — already present
production_score         int|null — already present
fitness_decision         str    — already present
deployed                 bool   — already present
deployed_artifact_hash   str|null — NEW: sha256 of the file actually written to app/core/self_edit_generated.py, only if deployed (already indirectly available via self_edit_backups/, but not joined to trace_id today)
terminal_state           str    — already present
```

**Explicitly not proposed**, matching the mission's own instruction to favor minimum sufficiency: model/generation-parameter identity (already recoverable via `interaction_log.jsonl`'s trace_id-linked entries, no need to duplicate), a diagnosis/causal-hypothesis field (already deliberately excluded from the existing ledger, for good, stated reasons — a stored claim doesn't become truer for being stored, per the 2026-09-07 audit's own explicit finding), any relevance/similarity score, any "learned" flag, environment/hardware telemetry beyond what already exists in the freeze-provenance mechanisms this project's research sessions already use ad hoc.

### Field-by-field classification

| Field | Class | Why |
|---|---|---|
| `trace_id` | **REQUIRED** | Already the only reliable cross-artifact join key; nothing here works without it. |
| `timestamp` | **REQUIRED** | Chronological-firewall experiments (§8 below) are impossible without trustworthy, already-append-only timestamps. |
| `task_type` | **REQUIRED** | Every self-edit row today is `"coding"`, but this must not be hardcoded into any future schema — a future task-type expansion should not silently break analysis. |
| `initial_candidate_code` | **REQUIRED** | This is the entire point of the investigation — without it, VRM-2 and above remain permanently untestable, exactly as this session's own VRM report found. |
| `initial_candidate_hash` | **USEFUL** | Cheap, makes exact-duplicate detection (a real adversarial concern, §14) trivial without re-reading full text; not strictly required if code is stored, since a hash can always be recomputed later. |
| `retry_candidate_code` / `retry_candidate_hash` | **REQUIRED** if any repair-transfer question is ever asked about retries specifically; **USEFUL** otherwise | The retry *is* FeralEcho's own existing, if blind, attempted repair — its content is direct evidence for "what does an attempted fix look like," valuable baseline data even without VRM. |
| `parent_baseline_hash` | **REQUIRED** | Without knowing what the candidate was a diff against, "would this transformation apply to a later, different baseline" can't be evaluated — a repair is a function of (failing code, target) not just (failing code) in isolation. |
| `deployed_artifact_hash` | **USEFUL** | Already recoverable indirectly via `self_edit_backups/`; storing it directly in the ledger removes a manual join step for future researchers. |
| `initial_f2_error`, `retry_f2_error`, `retry_occurred`, `final_f2_outcome`, `fitness_score`, `production_score`, `fitness_decision`, `deployed`, `terminal_state` | **Already present, REQUIRED (unchanged)** | No case for removing any of these; the existing design already got this part right. |
| A diagnosis/causal-hypothesis field | **UNNECESSARY (deliberately)** | Already excluded from the current ledger for a stated, sound reason (storing a claim doesn't verify it); repeating that exclusion here rather than reversing it. |
| Model/generation-parameter identity as a duplicate field | **UNNECESSARY** | Already recoverable via `interaction_log.jsonl`'s trace_id join; duplicating it here adds a second source of truth to keep in sync for no real gain. |
| Any relevance/similarity/confidence score | **UNNECESSARY** | This project has already run and lost two experiments (the Minimal Relevance Gate mission, cited in the 2026-09-07 design audit) demonstrating that a bare similarity score or an LLM relevance judge is unreliable and gameable — adding one here would repeat that mistake in a new location. |

## 6. Provenance requirements

- **Candidate X really preceded experience E**: `trace_id` + `timestamp`, both already append-only and already independently verified (this session's own VRM investigation confirmed the ledger file is strictly append-only by re-hashing mid-analysis and finding only new rows appended). Sufficient, no new mechanism needed.
- **E was derived only from allowed earlier attempts**: requires that any future analysis explicitly filter on `timestamp < E's derivation time` — a *procedural* discipline for the researcher to follow (exactly what this session's VRM report's chronological-firewall section attempted, and disclosed a real lapse in), not something the schema itself can enforce mechanically. Worth naming honestly: **no schema field can substitute for actual investigator discipline here** — the ledger's append-only property makes the check possible, it doesn't make it automatic.
- **Later candidate Y was generated after E existed, and wasn't copied from X**: `initial_candidate_hash`/`retry_candidate_hash` make "was Y byte-identical to X" a trivial check; genuine near-duplication (not byte-identical, but substantially copied) would require an actual diff, which is possible once both texts are stored but isn't a new field, just an analysis step.
- **Holdout information was unavailable when E was created**: not enforceable by the schema alone — this is a claim about the *researcher's* process (did they look at the holdout period before freezing E), the same limitation named in §3 above and in this session's own VRM report's disclosed lapse. **A schema cannot prevent investigator contamination; it can only make contamination detectable after the fact**, by preserving enough that another researcher can check whether a specific analysis script or record was touched before or after a stated freeze point (comparing file mtimes/git history of the analysis code itself against the claimed freeze timestamp).
- **Retained state survived the required boundary**: the existing `river_brain.pkl` isolation pattern (`RIVER_BRAIN_PATH` redirection before `get_river_brain()` is ever called, per the 2026-09-06 audit's own verified technique) is the established, reusable model for "prove a restart genuinely happened and state genuinely reloaded from disk" — directly reusable for any future evidence file too (redirect the ledger path, take a hash, restart the reading process, re-hash).
- **Evaluation remained independent of the learner**: already true structurally — F2's `test_code_in_sandbox()` is a real subprocess the generating process doesn't control, unchanged by anything proposed here.

## 7. Blinded chronological experiment support

Directly informed by running this exact kind of split in the immediately-preceding VRM investigation: **DEVELOPMENT / PROSPECTIVE / HOLDOUT periods, chosen by calendar date before looking at period-specific content, are already possible today for the metadata half** (this session did exactly that). The schema proposed in §5 extends the same discipline to the code half: once code is stored per-attempt, a researcher can freeze a candidate signature-and-transformation vocabulary from DEV rows only, then mechanically check PROSPECTIVE/HOLDOUT rows' *stored code* (not just their error text) without needing to regenerate or re-derive anything, and — critically, the part today's data cannot support at all — actually **attempt the frozen transformation against the later stored candidate and re-run it through the real F2 sandbox** to see if it would have passed. **Contamination detection**: require any such study to state, verifiably, (a) the exact git commit / script hash used to derive the DEV-period signature set, and (b) that script's own file-modification timestamp relative to the PROSPECTIVE/HOLDOUT period's data — if the analysis script was authored or edited *after* seeing later data, that's a real, checkable red flag, not an unfalsifiable claim of blindness.

## 8. Repair vs. avoidance vs. recognition — what evidence would distinguish them, without building the mechanism

- **Recognition** (a later failure matches an earlier signature): needs only the existing ledger's error text — already possible today.
- **Avoidance** (recognizing a signature is *unfixable by code change* and choosing not to retry it — e.g., this session's VRM investigation found exactly this case, a `RuntimeError` from an MLX/Metal call that can never succeed inside the sandbox, matching this project's own Finding 23) — needs a *decision record* distinct from a repair record: something must state "signature S was matched, and the decision taken was 'skip', not 'attempt transformation T'" — not present in the §5 schema as stated, and worth naming as a real, additional field a future avoidance mechanism (not proposed or built here) would need: a `signature_action` field with values like `{"attempted_repair", "avoided", "unrecognized"}`. **Not added to §5's minimum schema because no avoidance mechanism exists yet to produce this value** — flagged for whoever builds one, not built preemptively here.
- **Repair** (a stored transformation is applied and independently re-verified via F2): needs `initial_candidate_code` + `retry_candidate_code` (or a future stored transformation) + the real F2 outcome of applying it — exactly what §5 proposes.
- **Transfer to a structurally related but non-identical task**: needs the ability to compare two *different* `parent_baseline_hash` values whose failing code shares a signature but isn't byte-identical — supported by §5's hash fields, no new field needed.
- **Consulting a static list** (the doppelgänger this session's VRM report already named as a live risk): indistinguishable from "recognition" by the evidence alone — a static list and a genuinely experience-derived list produce identical-looking ledger rows. **The only way to tell them apart after the fact is to also preserve the actual vocabulary/list a mechanism consulted at the moment of the decision**, timestamped — i.e., if a future mechanism is ever built, *it* must log its own decision inputs, not just the outcome. This is a real, honest limit: **evidence preservation on the self-edit side alone cannot retroactively distinguish a learned rule from a hard-coded one — that distinction requires the mechanism itself to log what it consulted, which is a design requirement for any future VRM-like system, not something today's preservation gap can be blamed for.**

## 9. Storage and operational cost

- **Candidate size**: sampled directly from real recent tracebacks/plans in this session — typical self-edit candidate files run roughly 500–3,000 characters (the earlier VRM investigation's own sample rows showed comparable orders of magnitude for error text; generated code for a single-function self-edit target is not large). Estimate: **~1–3 KB per candidate**, ~2–6 KB per attempt including both initial and retry code.
- **Attempts/day**: **OBSERVED** directly from the ledger — roughly 60–90 real F2-reaching attempts/day during the active window sampled in this session's VRM investigation (492 dev-period failures over 8 days ≈ 60/day, consistent with the ~1 real attempt/hour + Optuna's ~10 dry-run trials/hour cadence this project's own documentation already states, most of which fail before or at F2).
- **Expected growth**: at ~2–6 KB/attempt × ~70 attempts/day ≈ **150–420 KB/day, roughly 4.5–13 MB/month** — trivially small relative to this project's own existing logs (`SELF_EDIT.log` alone is already 28.9 MB; `quarantine_journal.jsonl` 35 MB). **Not a telemetry-warehouse risk at this scale.**
- **Compression**: not necessary at this volume; if ever revisited, this project already has a working, reused pattern (`log_retention.py`'s gzip-on-threshold rotation, Finding 51) that could apply unchanged.
- **Content-addressed storage**: the hash fields in §5 already give the *benefit* of content-addressing (dedup detection, identity checks) without needing a separate CAS subsystem — storing the code inline in the JSONL row is simpler and sufficient at this volume; a separate CAS store would be over-engineering for the data size involved.
- **Retention**: this project already has a directly reusable, proven pattern — `_MAX_SELF_EDIT_BACKUPS`/`_MAX_SELF_EDIT_PLANS`-style file-count or size caps (Finding 58) or `log_retention.py`'s size-threshold rotation (Finding 51) — either applies unchanged; no new retention mechanism needs inventing.
- **Concurrency**: the existing `_ledger_lock` (a `threading.Lock()` already guarding `record_attempt()`'s file append) covers this extension unchanged — appending a larger row is not a new concurrency risk, just a larger write under the same lock.
- **Crash consistency**: `record_attempt()` already appends one JSON line per call inside a lock, best-effort, never raising — the existing pattern already handles a mid-write crash by design (a torn last line, if it ever happened, would affect only the newest row, and JSONL readers already have to tolerate a malformed trailing line as a matter of course). No new crash-consistency work needed.
- **Risk of slowing the live self-edit loop**: negligible — this adds a few more string fields to a dict that's already being serialized and appended once per attempt; the dominant cost of a self-edit cycle by orders of magnitude is the real Ollama generation calls (tens to hundreds of seconds each, per this session's own AP-0/reconciliation timing data), not a JSONL append of a few extra kilobytes.

## 10. Security / inert-artifact considerations

Generated self-edit candidates are, by construction, unreviewed and occasionally hallucinated or malformed. Storing them as **plain string values inside a JSONL row** (exactly how `initial_f2_error`'s full tracebacks are already stored today) is inert by construction — a JSON string is never executed by anything that merely reads or indexes the file. The real risks to guard against, named explicitly rather than left implicit:
- **Accidental execution during inspection**: a human or tool `cat`-ing or `python -c "exec(...)"`-ing a stored candidate directly would run it outside any sandbox — this is a *tooling discipline* risk (any future script reading this ledger for analysis must treat the code fields as inert text, the same discipline this session's own VRM investigation and prior sessions' F2-provenance investigations already applied when reading real tracebacks). No new technical control is needed beyond "never `exec()` a value read from this file outside a sandbox," which is already this project's standing rule for self-edit candidates generally.
- **Indexing/backup**: plain JSONL text is safe to back up, gzip, or full-text-index by any conventional tool without risk — nothing about storing code-as-string introduces a new attack surface beyond what already exists for the full, real tracebacks already being stored today, which already routinely contain file paths and, occasionally, fragments of attempted (blocked) dangerous calls (e.g., a `PermissionError: [SANDBOX] Write blocked...` line, already present in real historical rows).
- **Restoration**: restoring this file from backup and re-reading it is exactly as safe as restoring any other JSONL ledger already in this project — no code path anywhere currently deserializes a stored candidate and runs it automatically; this proposal does not create one and explicitly should not.

## 11. Existing infrastructure to reuse

- **`self_edit_attempt_ledger.py`**: the correct place to extend, not replace — same lock, same file, same append-only writer, same fields plus the new ones in §5. No new module needed.
- **`trace_id`** (Plan 5, 2026-09-05): the existing, already-proven join key across every durable artifact.
- **`log_retention.py` / `_MAX_SELF_EDIT_BACKUPS` / `_MAX_SELF_EDIT_PLANS`**: directly reusable retention patterns, no new mechanism to invent.
- **The RiverBrain-isolation technique** (redirect `RIVER_BRAIN_PATH` before first instantiation, verified by hash before/after) from the 2026-09-06 audit: the reusable template for proving any future evidence-file's read/write survives a real restart cleanly, without needing to invent a new verification method.
- **The Liveness Ledger's discrimination-test pattern** (`_evaluate_X()` pure function + `scripts/verify_liveness_ledger.py` case): if a future consumer of this evidence is ever built (not proposed here), this is the established, already-proven way to guard it against silent degradation — cited for completeness, not something this investigation is recommending building now.
- **`safe_exec_wrapper.py`'s kernel sandbox**: the correct, already-existing mechanism for any future "would this stored candidate + a transformation pass F2" retrospective test — no new sandbox needs building.

## 12. Minimal future implementation surface (not implemented)

**Insertion point**: `execute_self_edit()`'s existing `_attempt` dict (currently built incrementally and written once via `_finish_attempt()` → `_record_attempt_ledger()`, confirmed by direct source read to be a single call site). The minimal change: add the new fields from §5 to the same dict, populated at the same points the existing fields already are (`_attempt["initial_candidate_code"] = code` right where `_attempt["initial_f2_error"]` is currently set; same pattern for the retry fields; `parent_baseline_hash` computed once near the top of the function, before generation, by hashing the already-read `current_contents` of `SELF_EDIT_FILE`).

**Data flow**: no new data flow — the code strings already exist as local variables (`code`, `retry_code`) at exactly the points where other `_attempt` fields are already being set from equally-local variables (`sandbox_error`, `retry_error`). This is copying an existing pattern, not inventing a new one.

**Files affected**: `app/core/self_edit_manager.py` only (the `_attempt` dict's construction and the handful of assignment sites already listed in §2), plus `app/core/self_edit_attempt_ledger.py`'s own docstring, which would need updating to reflect that code is now captured (a documentation change, not a behavior change to that module — `record_attempt()`'s own signature and logic don't need to change at all, since it already accepts an arbitrary dict).

**Approximate complexity**: **Low** — a handful of one-line additions at existing assignment points, plus one `hashlib.sha256(...)` call for `parent_baseline_hash`. No new function, no new file, no new lock, no new thread.

**Failure modes**: a very large generated candidate (self-edit targets are historically small, single-function changes, per this project's own convergence-tracking findings) could bloat individual ledger rows — mitigated by the same size-based rotation already used elsewhere (§9), not a reason to avoid the change. A malformed/non-UTF8 candidate string could fail JSON serialization — `record_attempt()` already wraps its write in a try/except that fails silently rather than raising (confirmed in its own source), so this degrades to "this one row's new fields are dropped," not a crash.

**Tests that would be required**: (a) a unit test confirming `_attempt["initial_candidate_code"]` is populated and matches the real string passed to `test_code_in_sandbox()` on a synthetic failing candidate; (b) confirming the retry fields populate only when a retry actually occurs, matching the existing `retry_occurred` boolean's own semantics; (c) confirming `parent_baseline_hash` matches an independently-computed hash of `self_edit_generated.py`'s real content at a known point in time; (d) a regression test confirming `record_attempt()`'s existing best-effort/never-raise contract still holds with the larger dict (feed it a dict with a non-serializable value and confirm the write fails silently rather than propagating).

**Must-have instrumentation**: `initial_candidate_code`, `retry_candidate_code`, `parent_baseline_hash` (§5's REQUIRED rows) — without these, VRM-2 remains exactly as untestable as this session's own VRM report already found.

**Nice-to-have instrumentation**: the hash fields (`initial_candidate_hash`, `retry_candidate_hash`, `deployed_artifact_hash`) — genuinely useful for cheap dedup and identity checks, but derivable after the fact from the code fields if omitted now, so not blocking.

## 13. Adversarial analysis

| Question | Answer |
|---|---|
| Could a lookup table produce the same evidence? | Yes, indistinguishable from the evidence alone — §8's honest limit: distinguishing a learned rule from a hard-coded one requires the *consuming* mechanism to log what it consulted, which is out of this investigation's scope (no mechanism is being built). |
| Could the model already know the solution (pretrained capability)? | Not addressable by preservation alone — this is the same confound the VRM report already named (Section 10 there): a stronger frozen model might simply produce fewer of these failures in the first place, for reasons unrelated to any FeralEcho mechanism. Preserving code doesn't resolve this; keeping the current model as a frozen control (already recommended in the VRM report) is the actual mitigation. |
| Could context leakage mimic retention? | Real risk if a future mechanism's prompt construction accidentally includes held-out-period text — the schema itself doesn't prevent this; it only makes it detectable after the fact, by comparing what was actually sent (`interaction_log.jsonl`'s already-real request text, trace_id-joined) against the claimed freeze boundary. |
| Could task repetition mimic transfer? | Yes — if the "structurally related but non-identical" later task is, in fact, nearly identical to an earlier one (the self-edit prompt-family space is not large, per this project's own convergence-tracking findings about near-duplicate function families), an apparent "transfer" result could just be near-repetition. `parent_baseline_hash` plus the prompt/plan text (already separately preserved in `self_edit_plans/`) gives a future researcher what they'd need to check this, but doesn't prevent it by construction. |
| Could evaluator leakage contaminate generation? | No new risk introduced — F2 remains a separate real subprocess; storing its output as inert text after the fact cannot feed back into the generation that already happened. |
| Could timestamps or IDs falsely imply causality? | Yes, in principle — a later trace_id with a later timestamp only proves temporal order, not that anything about the earlier attempt causally influenced the later one, unless a future mechanism explicitly reads and uses the earlier evidence (which nothing does today — the ledger remains, even after this proposed extension, a pure write-only sink per its own stated design). This report does not claim otherwise. |
| Could a later researcher unknowingly train on holdout data? | Real risk, same as any retrospective study — mitigated only by procedural discipline (§6, §7), not by the schema itself. |
| Could logging itself alter self-edit behavior? | No — the proposed fields are populated from values that already exist as local variables at the point of assignment; no new read, no new decision, no new branch is introduced into `execute_self_edit()`'s control flow. |
| Could successful deployment backups already solve part of this? | Yes, partially, and already noted (§4) — `self_edit_backups/` already preserves *deployed* code, just not trace_id-addressable and not reaching failing/rejected attempts. `deployed_artifact_hash` in §5 is the minimal bridge between the two, not a replacement for either. |
| Is preserving source alone insufficient? | **Yes, stated plainly**: source alone establishes recognition and enables retrospective repair-validity testing (closing the exact VRM-2 gap), but it does not, by itself, establish that a future mechanism's *transformation-generation* step will work — this project's own AP-0 investigation already found local-model induction from small evidence sets to be weak, and Architecture A already found injecting a diagnosis into a retry prompt specifically to have zero measurable effect. Preserving evidence removes one real blocker; it does not manufacture the capability to use it well. |

## 14. Remaining unknowns

**UNKNOWN**: whether the specific transformation-generation step any future VRM-like mechanism would need (given the code) performs any better than AP-0's already-demonstrated weak induction or Architecture A's null retry-injection result — this investigation cannot resolve that, only remove the evidentiary blocker to testing it. **UNKNOWN**: whether preserving code changes anything about the security posture of backups/exports beyond what's already true of the existing full-traceback fields (INFERRED to be negligible, per §10's reasoning, but not independently red-teamed here). **UNKNOWN**: the true byte-size distribution of self-edit candidates over a longer window than this session's own sample — the storage estimate in §9 is a reasonable order-of-magnitude projection, not a measured multi-month average.

## 15. Recommendation

Extend `self_edit_attempt_ledger.py`'s existing `_attempt` dict with the REQUIRED fields from §5 (`initial_candidate_code`, `retry_candidate_code`, `parent_baseline_hash`), populated at the same points the existing fields already are, using the same lock, same file, same append-only, best-effort, never-raise contract already proven safe in production. This is a **pure evidence-preservation change**: no new decision point, no new consumer, no change to what self-edit is permitted to do, no change to any existing gate. It does not implement VRM, does not implement any avoidance or repair mechanism, and does not wire anything new into `choose_model()`, the fitness gate, or RiverBrain. It closes exactly the one gap this session's VRM investigation found and this investigation has now independently reconfirmed and precisely located: without it, no future study — VRM or otherwise — can ever test whether experience-derived repair knowledge actually works, only whether recurring failure signatures exist.

## 16. Not implemented

Per the mission's explicit constraint, nothing above was built, wired, or triggered. No production file was edited. No self-edit attempt was generated or forced for this investigation.

---

**EVIDENCE PRESERVATION NEED:** HIGH

**CURRENT HISTORICAL RECONSTRUCTABILITY:** INSUFFICIENT

**MINIMUM LOGGING CHANGE FEASIBILITY:** HIGH

**READY TO IMPLEMENT INSTRUMENTATION:** CONDITIONAL

The need is HIGH because this is now the second independent investigation (this one and the immediately-preceding VRM feasibility study) to hit the identical wall — a real, otherwise well-instrumented pipeline that captures rich metadata about every self-edit attempt but has never once preserved the one artifact (the actual generated code) any future causal-repair experiment would need, and the gap is currently unbounded going forward (every hour that passes without this change is more permanently-lost evidence, at a real, measured rate of ~60–90 attempts/day). Current reconstructability is INSUFFICIENT, confirmed independently across every plausible recovery path checked (backups, staging, plans, logs, invocation records) rather than assumed. The logging-change feasibility is HIGH: the insertion points, data flow, and reuse pattern all already exist almost verbatim in the same function, at the same dict, guarded by the same lock — this is one of the lowest-risk instrumentation changes this project's own recent history has evaluated. Readiness is CONDITIONAL, not YES, only because implementation itself was explicitly out of scope for this mission and requires the same report-then-pause review this project applies to every other change, however small — not because any open technical or design question remains unresolved.
