# Tier 1 Remediation Proposals — Review-Ready, Not Applied

**No fixes applied. No commits. No production code modified.** Every diff below is a proposal for
review. RiverBrain, model orchestration, RAOC, and evaluation methodology are untouched. No secret
value appears anywhere in this report, in any test, or in any terminal output produced while writing
it — every reproduction below uses boolean presence checks and counts only.

Before writing this report: `git status --porcelain` showed only pre-existing, already-known changes
(`sandbox/safe_exec_wrapper.py` modified from earlier tonight's Phase 1 work, `sandbox/scripts/
temp_self_edit.py` — a pre-existing, unrelated self-edit artifact — plus the untracked audit files
already produced tonight). Confirmed again after writing this report: only this new file added, nothing
else changed.

---

## 1. Executive Conclusion

All three defects are real, independently reproduced in this pass (not merely cited from Phase 1A), and
none require architectural redesign — each has a bounded, minimal fix. The environment-variable
exposure is the most serious: it is not limited to `GREMLIN_SECRET` as originally reported — **all five
real secrets in `.env`** are exposed by the same mechanism, confirmed directly below. The `blocked_write`
and `verified_success` issues are real but lower-severity, since `functional_quality.py` has zero live
callers (confirmed repeatedly tonight) — fixing them is a prerequisite for ever trusting the signal, not
an active production risk today. **Recommendation: APPROVE PROPOSED PATCHES**, with the environment fix
treated as must-fix-now and the other two as should-fix-before-any-Phase-2-wiring (§8).

---

## 2. Reproduction Evidence (independently reproduced this pass, not solely cited from Phase 1A)

**`blocked_write` false negative** — the real, currently-deployed `self_edit_generated.py` (its own
`get_shortened_code` function attempts `open("shortened_codes.txt", "w")`, genuinely blocked by the
sandbox):
```
outcome: verified_failure
blocked_write: False
 - get_shortened_code raised PermissionError: [SANDBOX] Write blocked outside scratch dir: '.../shortened_codes.txt'
```

**`blocked_write` false positive** — a trivial candidate that only imports a real project module:
```python
import app.emergent_scheduler as emergent
def noop():
    return 1
```
```
outcome: verified_success
blocked_write: True
```

**`verified_success` gaming**, three independently constructed cases, none touched by Phase 1A verbatim:
```
no-op stub (def transform(code): pass):                          verified_success
exception-swallowing (try: 1/0 except Exception: return code):    verified_success
plausible-but-wrong (def transform(code): return code.upper()):   verified_success
```

**Environment-variable exposure** — reproduced twice, the second time correctly. The first attempt
(a standalone `python3` process with no `.env` loaded) showed no exposure — this was a **methodology
error**, not evidence of safety, caught and corrected before being reported: a standalone process never
had the secrets in the first place. Redone with `load_dotenv()` called first, exactly matching
`run.py:44-45`'s real startup behavior:
```
own process now has gremlin secret loaded: True
sandboxed candidate output: gremlin_present=True partner_present=True newsapi_present=True
                            owm_present=True anthropic_present=True total_env_vars=66
```
**All five real secrets present in `.env`, not just `GREMLIN_SECRET`, are confirmed exposed.** This
widens the original finding's scope.

**Would existing tests catch any of these?** No. `scripts/verify_functional_quality_signal.py` (Phase 1's
own discrimination matrix) never constructed a case designed to separate "write blocked inside a
smoke-tested call" from "write blocked at import time," and never tested a no-op/exception-swallowing
candidate at all. No test anywhere in this codebase checks environment-variable isolation — confirmed by
grep, zero matches for `env=` in any sandbox-related test file.

**Hidden assumption found in the current implementation**: `functional_quality.py`'s `blocked_write`
detection assumes a write-block always surfaces to `proc.stderr` — true only when it happens *before*
the mode-specific dispatch (e.g., at import time, crashing the whole subprocess) and false whenever it
happens *inside* the smoke-test loop's own per-callable `try/except`, which was deliberately designed to
prevent one candidate's exception from crashing the whole batch (§3 explains why this is the right
design decision, just implemented with the wrong detection mechanism layered on top).

---

## 3. `blocked_write` Root Cause

`sandbox/safe_exec_wrapper.py`'s `--mode=functional_verify` block wraps each smoke-tested call in its
own `try/except Exception`, correctly recording `{"outcome": "raised", "error": str(exc)}` per callable
— this is right; one candidate function's write-block should not abort testing every other function in
the same file. The problem is entirely on the *reporting* side: nothing about that structured, precise,
per-callable information is surfaced anywhere the caller (`functional_quality.py`) looks. Instead,
`functional_quality.py:96-98` does:
```python
raw_err = (proc.stderr or "").strip()
if "[SANDBOX]" in raw_err and "blocked" in raw_err.lower():
    result["blocked_write"] = True
```
This is a coarse, position-blind text search over the *entire subprocess stderr stream* — it cannot
distinguish "this candidate's own code did this" from "some unrelated log line happened to contain these
words" (the false positive), and it never fires at all for the common case where the block was already
caught and structured before ever reaching stderr (the false negative).

---

## 4. `blocked_write` Proposed Fix

**Move detection into the structured JSON payload, at the source, where precise information already
exists — don't try to reconstruct it from unstructured text after the fact.**

`safe_exec_wrapper.py` diff (inside the existing `--mode=functional_verify` block):

```diff
             try:
                 _obj(*_args)
                 _results.append({"name": _name, "kind": _kind, "outcome": "executed_ok", "error": None})
             except Exception as _call_err:
-                _results.append({"name": _name, "kind": _kind, "outcome": "raised", "error": f"{type(_call_err).__name__}: {_call_err}"})
+                _is_write_block = (
+                    isinstance(_call_err, PermissionError)
+                    and str(_call_err).startswith("[SANDBOX]")
+                )
+                _results.append({
+                    "name": _name, "kind": _kind, "outcome": "raised",
+                    "error": f"{type(_call_err).__name__}: {_call_err}",
+                    "blocked_write": _is_write_block,
+                })

         _any_tested = any(r["outcome"] in ("executed_ok", "raised") for r in _results)
         _any_raised = any(r["outcome"] == "raised" for r in _results)
+        _any_blocked_write = any(r.get("blocked_write") for r in _results)
         with open(_out_path, "w", encoding="utf-8") as f:
-            _json.dump({"tested": _results, "any_tested": _any_tested, "any_raised": _any_raised}, f)
+            _json.dump({
+                "tested": _results, "any_tested": _any_tested, "any_raised": _any_raised,
+                "any_blocked_write": _any_blocked_write,
+            }, f)
```

`functional_quality.py` diff — read the precise, structured field instead of grepping stderr, and add
the import-time case as a distinct, honestly-labeled category rather than folding it into the same
boolean:

```diff
-    result = {
-        "outcome": SANDBOX_INFRA_FAILURE,
-        "tested": None,
-        "timed_out": False,
-        "blocked_write": False,
-        "detail": None,
-    }
+    result = {
+        "outcome": SANDBOX_INFRA_FAILURE,
+        "tested": None,
+        "timed_out": False,
+        # Replaces the single ambiguous boolean (Tier 1 remediation, this
+        # report) — "occurred" is only ever True from the structured JSON
+        # payload (a write blocked inside a specific smoke-tested call);
+        # "import_time" is a separate, narrower signal set only when the
+        # candidate's own module-level code (not a smoke-tested call) hit
+        # the write guard before the harness could even start testing —
+        # a real, different failure shape from either the candidate's
+        # runtime logic being broken or a normal exception.
+        "write_block": {"occurred": False, "import_time": False, "callable_name": None},
+        "detail": None,
+    }
     ...
             if proc.returncode == 0 and "SANDBOX_OK" in proc.stdout and os.path.isfile(output_path):
                 with open(output_path, "r", encoding="utf-8") as f:
                     payload = json.load(f)
                 tested = payload.get("tested", [])
                 result["tested"] = tested
+                if payload.get("any_blocked_write"):
+                    _blocked = next((t for t in tested if t.get("blocked_write")), None)
+                    result["write_block"] = {
+                        "occurred": True, "import_time": False,
+                        "callable_name": _blocked["name"] if _blocked else None,
+                    }
                 if payload.get("any_raised"):
                     result["outcome"] = VERIFIED_FAILURE
                 ...
                 return result

             raw = (proc.stderr or proc.stdout or "").strip()
             result["detail"] = raw[:1000]
             if "Traceback" in raw and "safe_exec_wrapper.py" in raw and "exec_module" in raw:
                 result["outcome"] = VERIFIED_FAILURE
+                if "[SANDBOX]" in raw and "PermissionError" in raw:
+                    result["write_block"] = {"occurred": True, "import_time": True, "callable_name": None}
             else:
                 result["outcome"] = SANDBOX_INFRA_FAILURE
             return result
```

The import-time branch still uses a text check (there's no structured payload to read when the module
fails to import at all — that failure happens before the mode-specific code ever runs) — but it's now
explicitly and honestly labeled `import_time: True`, distinct from a candidate-call-level block, rather
than collapsed into one ambiguous flag. **A single boolean was fundamentally inadequate — this replaces
it with a small structured result distinguishing candidate-attempted-write (`occurred` + `callable_name`)
from import-time exposure (`import_time`), which is as far as this specific mechanism can honestly go;
distinguishing "sandbox-policy-blocked" from "infrastructure write" beyond that would require information
the sandbox subprocess doesn't currently have reason to produce, and isn't proposed here since nothing
downstream needs it yet.**

**Tests proving this**: re-run the two reproduction cases from §2 — the real `self_edit_generated.py`
should now show `write_block.occurred=True, callable_name="get_shortened_code"`; the trivial
`import app.emergent_scheduler` case should now show `write_block.occurred=False` (the import succeeds
without the guard ever tripping in that specific run, so there is nothing to misreport).

**Backwards compatibility / historical-metrics implications**: `functional_quality.py` has zero live
callers (confirmed §2, and repeatedly earlier tonight) — this changes nothing about any already-computed
result, since nothing has ever consumed `blocked_write` in production. `scripts/verify_functional_quality_signal.py`
and `scripts/adversarial_functional_verifier_test.py` (Phase 1/1A's own test scripts) reference the old
field name and would need a small, mechanical update to read `write_block.occurred` instead of
`blocked_write` — not proposed as part of this diff, flagged as a required follow-up if this fix is
approved.

---

## 5. `verified_success` Root Cause

By design, not by bug: the verifier answers "did this raise," never "is this correct." `_score_response_quality()`-style
semantic checking doesn't exist for self-edit candidates (no per-family expected-output spec exists
anywhere in this codebase, confirmed earlier tonight), and the smoke test captures only exceptions, never
return values — so even if a spec existed, nothing today reads what a function actually *returns*. This
is Phase 1's own documented, disclosed scope. The problem is not that this limit exists — it's that a
single field named `verified_success` invites exactly the overclaim the mission is trying to prevent.

---

## 6. `verified_success` Proposed Fix

**Replace the implied claim with an explicit, multi-dimensional result. Do not invent semantic
correctness that doesn't exist.**

```diff
 def functional_execution_score(code: str, timeout: float = 10.0) -> dict:
     ...
-    result = {
-        "outcome": SANDBOX_INFRA_FAILURE,
+    result = {
+        # "outcome" retained for the discrimination-test scripts' existing
+        # shape (VERIFIED_SUCCESS/VERIFIED_FAILURE/NOT_APPLICABLE/
+        # SANDBOX_INFRA_FAILURE constants, unchanged) — but see the new
+        # "dimensions" dict below, which is the honest replacement for
+        # what "verified_success" was being read to imply.
+        "outcome": SANDBOX_INFRA_FAILURE,
+        "dimensions": {
+            "syntax_valid": None,          # set by the caller before this
+                                            # function runs (AST parse
+                                            # already gates entry elsewhere
+                                            # in this codebase's pipeline);
+                                            # None here because this
+                                            # function alone can't see it.
+            "execution_started": False,
+            "execution_completed": False,
+            "execution_succeeded": None,   # True/False once known — this
+                                            # is the OLD verified_success/
+                                            # verified_failure meaning,
+                                            # under its honest name.
+            "output_available": False,     # ALWAYS False today — see the
+                                            # note below. Not a bug fixed
+                                            # by this diff; a disclosed,
+                                            # structural gap.
+            "output_correct": "UNKNOWN",   # ALWAYS UNKNOWN. No per-family
+                                            # spec exists to check against.
+            "sandbox_policy_ok": True,
+            "verification_infrastructure_ok": True,
+        },
         "tested": None,
         "timed_out": False,
         "write_block": {"occurred": False, "import_time": False, "callable_name": None},
         "detail": None,
     }
```

With `dimensions` populated at each real branch of the function: `execution_started=True` once the
subprocess actually launches; `execution_completed=True`/`verification_infrastructure_ok=False` split
correctly on timeout vs. genuine completion (mirrors the existing `SANDBOX_INFRA_FAILURE` logic, just
made explicit per-dimension); `execution_succeeded` set from `any_raised` (unchanged logic, renamed
field); `sandbox_policy_ok=False` when `write_block.occurred` is true.

**`output_available`/`output_correct` deserve their own explanation, not a quiet default.** The current
smoke-test harness (`safe_exec_wrapper.py`'s `functional_verify` mode) calls each candidate function and
only asks "did it raise" — it never captures or serializes what the function *returned*. This means
**`output_available` cannot honestly be anything but `False` today**, and fixing it would require a real,
separate design decision (what counts as a safely-serializable return value; how to compare it to
anything, given no spec exists) — **not proposed as part of this remediation pass**, flagged explicitly
per the mission's own instruction not to invent a false solution to a limitation that should instead be
documented.

**Should `verified_success` remain a binary field at all?** No — recommend deprecating the bare
`outcome` string's implied meaning in favor of always reading `dimensions.execution_succeeded`
specifically for "did it raise," and never treating any single field as a stand-in for "this candidate is
good." The `outcome` constants (`VERIFIED_SUCCESS` etc.) are kept in this diff only for the two existing
test scripts' backward compatibility, not because they're the right long-term shape.

**Tests proving this**: re-run the three §2 gaming cases — all three should now show
`dimensions.execution_succeeded=True` alongside `dimensions.output_correct="UNKNOWN"` — the structured
result now honestly says "it ran without raising, and we don't know if it's right," instead of a single
field that reads as a verdict.

---

## 7. Sandbox Environment-Variable Exposure Root Cause

Every one of the four `subprocess.run()` call sites (`self_edit_manager.py:843`, `self_edit_manager.py:
1406`, `self_edit_manager.py:1668`, `functional_quality.py:81`) omits the `env=` parameter. Per Python's
own documented `subprocess.run()` behavior, omitting `env` means the child process inherits the parent's
**complete** environment. `run.py:44-45` calls `load_dotenv()` at real startup, which sets real OS-level
environment variables (confirmed directly: `load_dotenv()` genuinely populates `os.environ`, not a
separate in-memory store) for every real secret in `.env` — `GREMLIN_SECRET`, `ECHO_PARTNER_SECRET`,
`NEWSAPI_KEY`, `OPENWEATHER_API_KEY`, `ANTHROPIC_API_KEY`. None of the Seatbelt profile's rules
(`echo_sandbox.sb`) touch environment variables at all — they govern filesystem writes and network,
which is why this was never caught by the existing security work tonight (Findings 41-B3-style
timeout/write-kill fixes, F1/F2/F3) — **this is a genuinely different attack surface from everything
else this project's own extensive self-edit security history has addressed.**

---

## 8. Environment Isolation Proposed Fix — Highest Priority

**Positive allowlist, not a denylist**, per the mission's own stated preference and for the structural
reason a denylist can't provide: a denylist must be remembered and updated every time a new secret is
added to `.env`; an allowlist is safe by construction against any secret nobody thought to denylist yet.

**What the sandbox subprocess actually needs, determined directly, not guessed:**
- Baseline OS/shell functioning: `PATH`, `HOME`, `LANG`, `TMPDIR` (all present in the parent shell,
  confirmed directly).
- Native-library crash prevention (Findings 40/50's own already-documented, already-necessary guards):
  `KMP_DUPLICATE_LIB_OK`, `OMP_NUM_THREADS`, `MKL_NUM_THREADS`, `TOKENIZERS_PARALLELISM`,
  `HF_HUB_OFFLINE`, `TRANSFORMERS_OFFLINE`.
- **Not needed from the parent**: `MPLBACKEND`/`MPLCONFIGDIR` — `safe_exec_wrapper.py`'s own
  `_install_patches()` already sets both unconditionally, inside the child process itself, after it
  starts — confirmed directly (`_os.environ["MPLBACKEND"] = "Agg"`, line 176). No inheritance required.

Proposed new helper (duplicated in both files, matching this codebase's existing, deliberate pattern of
independently defining `_SANDBOX_WRAPPER`/`_SANDBOX_PROFILE` in each rather than sharing an import
between `self_edit_manager.py` and `functional_quality.py` — kept consistent, not introducing a new
coupling):

```python
_SANDBOX_SAFE_ENV_KEYS = frozenset({
    "PATH", "HOME", "LANG", "TMPDIR",
    "KMP_DUPLICATE_LIB_OK", "OMP_NUM_THREADS", "MKL_NUM_THREADS",
    "TOKENIZERS_PARALLELISM", "HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE",
})
_SANDBOX_REQUIRED_DEFAULTS = {
    "KMP_DUPLICATE_LIB_OK": "TRUE", "OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1",
    "TOKENIZERS_PARALLELISM": "false", "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1",
}


def _build_sandbox_env() -> dict:
    """Explicit allowlist, not inherited-minus-denylist — a new secret added
    to .env in the future is safe by construction, not by remembering to
    update a blocklist. Tier 1 remediation (this report), closing a real,
    confirmed exposure: every real secret in .env (GREMLIN_SECRET,
    ECHO_PARTNER_SECRET, NEWSAPI_KEY, OPENWEATHER_API_KEY, ANTHROPIC_API_KEY)
    was previously inherited by every sandboxed subprocess by default,
    since none of the four subprocess.run() call sites passed env=."""
    env = {k: os.environ[k] for k in _SANDBOX_SAFE_ENV_KEYS if k in os.environ}
    for k, v in _SANDBOX_REQUIRED_DEFAULTS.items():
        env.setdefault(k, v)
    return env
```

Applied at each call site (shown for one; identical shape at all four):

```diff
             result = subprocess.run(
                 ["sandbox-exec", "-f", _SANDBOX_PROFILE, "-D", f"SCRATCH={scratch_real}",
                  sys.executable, _SANDBOX_WRAPPER, scratch_real, staging_file],
                 capture_output=True,
                 text=True,
                 timeout=30,
                 cwd=os.getcwd(),
+                env=_build_sandbox_env(),
             )
```

**All four call sites need this identical one-line addition** — `self_edit_manager.py:843`,
`self_edit_manager.py:1406`, `self_edit_manager.py:1668`, `functional_quality.py:81`
(`sandbox/run_script.py`'s `run_sandbox_script_isolated()` also needs to be checked for whether it has
its own, fifth `subprocess.run()` call — confirmed it does not; it delegates to the same wrapper
invocation shape via a shared internal helper, not proposed as a separate diff here since no independent
call site exists there).

**Tests proving this**: re-run §2's exact reproduction (with `.env` loaded in the parent, matching real
`run.py` startup) — after the fix, `gremlin_present`/`partner_present`/`newsapi_present`/`owm_present`/
`anthropic_present` should all read `False`, `total_env_vars` should drop to roughly the size of
`_SANDBOX_SAFE_ENV_KEYS` (≤10) instead of 66.

---

## 9. Threat Model

| Attack path | Possible under current sandbox? | Evidence |
|---|---|---|
| Direct read (`os.environ`) | **Yes — confirmed, §2** | Direct reproduction, five real secrets |
| Child process launched by candidate | **Yes, by the same mechanism** — a grandchild process spawned by a candidate would inherit whatever the sandboxed parent has, which is currently the full environment | Not separately reproduced (would require the candidate to itself spawn a process, which F1's static scanner already blocks — `subprocess`/`os.system`/`os.fork` are unconditionally blocked at the AST level before this sandbox stage ever runs) — **structurally mitigated by F1, not by the sandbox's own env handling**, worth noting as a real, if secondary, layer |
| Shell invocation | Blocked by F1 (static scan) before reaching the sandbox at all — not re-tested here, inherited from this project's own extensive, already-verified F1 coverage | N/A |
| Indirect access via an imported module | **Yes** — the false-positive reproduction (§2, `import app.emergent_scheduler`) is itself proof an imported module's own code executes with full env access | Direct |
| Error/diagnostic leakage | **Plausible, not directly tested** — an uncaught exception's `str()` could in principle include environment-derived content if a candidate's own code embeds it in a message; not constructed as a specific case in this pass | Not reproduced — flagged as PLAUSIBLE, not proven |
| File exfiltration (write to a permitted scratch path) | **Yes, structurally** — a candidate could write `os.environ` to a file inside `SCRATCH`, which the sandbox permits by design; that file is then readable by whatever process created the scratch dir (the parent, briefly, before cleanup) | Not directly reproduced (would require constructing and reading back a real file containing secret-shaped content, which this report's own "never output the secret" constraint makes awkward to demonstrate cleanly) — logically follows from the confirmed read access, PLAUSIBLE at minimum |
| Output exfiltration (stdout/stderr) | **Yes, structurally — this is exactly how §2's own reproduction works** (a boolean summary printed to stdout) | Direct — the reproduction *is* this attack path, deliberately using booleans instead of the real value |
| Future training-data contamination | **Not directly testable today** (no training pipeline exists) — but real and worth flagging precisely because of the LoRA investigation running in parallel: if any future data pipeline is ever built from raw sandbox execution logs/output rather than validated, secret-scrubbed data, a leaked secret captured during this exposure window could be baked into persisted training material, which is far harder to remediate than deleting a log line and rotating a credential | Flagged, not fabricated — genuinely UNRESOLVED pending any future training-pipeline design |

---

## 10. Proposed Tests

- **Security**: the exact §2 reproduction, asserted to show all five `*_present` flags `False` and
  `total_env_vars` at or below the allowlist size, post-fix.
- **Compatibility**: a real self-edit staging/import test (the existing `test_code_in_sandbox()`/
  `_stage_and_import_test()` regression path already used throughout tonight) must still pass — proves
  the allowlist isn't missing something legitimately required.
- **Process inheritance**: a candidate that spawns a subprocess is already blocked by F1 before reaching
  this stage — no new test needed, this is existing, already-verified coverage.
- **Existing functionality**: re-run this session's own earlier regression suite (`--mode=import`,
  `--mode=script`, `--mode=apply_to_code`, all three confirmed passing earlier tonight) — must remain
  unaffected, since the allowlist includes every variable those paths were shown to actually need.
- **Telemetry correctness**: §4's two reproduction cases, re-run post-fix, must show the corrected
  `write_block` values described there.
- **Verifier behavior**: §6's three gaming cases, re-run post-fix, must show `execution_succeeded=True`
  alongside `output_correct="UNKNOWN"` — not a silent "success," an honest partial result.

---

## 11. Exact Diffs

All shown in §4, §6, §8 above, in full. No diff in this report has been applied.

For each: **what changes** (specific lines, named above); **why** (root cause, §3/§5/§7); **what defect
it fixes** (named per section); **what test proves it** (§10); **new failure modes introduced**: the
`write_block`/`dimensions` restructuring changes `functional_quality.py`'s return shape, which would
break `scripts/verify_functional_quality_signal.py` and `scripts/adversarial_functional_verifier_test.py`
if their own field references aren't updated alongside — a required, small follow-up, not a hidden risk,
since both scripts are already untracked test artifacts with zero production callers; **affects
production behavior**: no — zero live callers exist for `functional_quality.py` today (§1); the
environment-variable fix affects real, live subprocess calls in `self_edit_manager.py`, but only removes
variables no real candidate has ever been shown to need (§8's compatibility test is the check that
proves this); **changes historical metrics**: no — nothing has ever been trained or deployed based on
`functional_quality.py`'s output, and the environment fix doesn't touch scoring at all.

---

## 12. Regression Analysis

Covered per-fix in §4/§6/§8/§10. Net summary: the two telemetry fixes are purely additive/restructuring
to a module with zero live callers — regression risk is effectively limited to the two test scripts'
field-name references, a known, small, disclosed follow-up. The environment fix touches real,
currently-running production code paths (`self_edit_manager.py`'s three call sites are exercised
continuously by the live hourly/dry-run self-edit cycle) — its regression risk is real but bounded and
directly testable (§10's compatibility test), not theoretical.

---

## 13. LoRA Implications

Per the parallel LoRA ecosystem investigation (`audits/2026-09-06_lora_ecosystem_investigation.md`,
completed alongside this report): **the environment-variable exposure is not just a standalone security
bug — it is a prerequisite blocker for any future LoRA-adjacent data pipeline**, for the precise reason
named in §9's last row. A secret captured in sandbox execution logs before this fix lands could, in
principle, be baked into model weights if ever included in training material — a categorically harder
problem to remediate than a log line or a credential rotation. **This raises this fix's real priority
above "before showcase day" to "before any future training-data collection begins,"** independent of
the showcase timeline. Separately: an unreliable functional verifier (§5/§6) could produce mislabeled
training examples if `execution_succeeded` were ever naively treated as a positive training label without
the `output_correct="UNKNOWN"` caveat attached — the same "necessary floor, not a reward" framing Phase
1A already established, restated here because it applies with equal force to any future LoRA training-
data curation step, not just to RiverBrain.

---

## 14. Must-Fix / Should-Fix / Future-Hardening

**Must fix now**: §8, the environment-variable allowlist. Real, live, exploitable today, and — per §13 —
its priority window is actually narrower than "before showcase," given the LoRA investigation running in
parallel.

**Should fix soon**: §4 (`blocked_write`) and §6 (`verified_success` restructuring) — real defects, but
currently inert given zero live callers; must be fixed before any Phase 2 wiring decision, not
necessarily before the showcase itself if `functional_quality.py` stays disconnected through that window.

**Future hardening, not proposed in this pass**: capturing candidate return values (`output_available`,
§6) and any per-family expected-output spec (`output_correct`) — both real, both explicitly out of scope
here per the mission's own instruction not to invent a false solution to a limitation better left
documented. Error/diagnostic and file-exfiltration paths (§9's PLAUSIBLE rows) — worth a dedicated,
narrower follow-up investigation, not blocking this pass's recommendation.

---

## 15. Risks and Unresolved Questions

- The environment allowlist's exact membership (§8) was derived from direct observation of what the
  sandbox subprocess currently needs — not from an exhaustive audit of every code path a self-edit
  candidate could theoretically take. A candidate relying on some other, legitimate environment variable
  not yet identified would fail post-fix in a new way (a real, but safe-directioned, failure mode — fails
  closed, not open).
- §9's PLAUSIBLE-but-not-directly-reproduced rows (error leakage, file exfiltration) remain genuinely
  open — flagged, not resolved, consistent with this report's own evidence discipline.
- The `write_block`/`dimensions` restructuring (§4/§6) intentionally leaves `output_available`/
  `output_correct` unsolved rather than inventing a shallow fix — this is a disclosed limitation, not an
  oversight, but it does mean this remediation pass does not make `functional_quality.py` ready for
  Phase 2 wiring on its own; it only removes the two specific defects Phase 1A found.

---

## Recommendation

**APPROVE PROPOSED PATCHES.**

All three diffs are minimal, directly evidenced, individually testable, and — for the two telemetry
fixes — carry effectively zero production risk given the module's current isolation. The environment fix
carries real but bounded, directly-testable risk, and closes a genuinely serious, confirmed exposure
that this pass found to be broader (five secrets, not one) than originally reported. None of the three
require architectural redesign. Recommend applying the environment fix (§8) first and independently, as
the highest-priority, most time-sensitive item, with the two telemetry fixes (§4, §6) following once
reviewed — no reason found to require they land together as one change.
