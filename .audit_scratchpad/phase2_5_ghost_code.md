# Phase 2.5: Ghost Code & Silent Failure Sweep (raw notes)

## Swallowed exceptions
- Zero `except: pass` bare patterns found across app/, run.py, terminal_client.py (excl. archive
  dirs). [VERIFIED via grep]
- Zero `except Exception:\n    pass` (unlogged) patterns found in app/. [VERIFIED via grep]
- Exactly one genuinely bare `except:` (no exception type) anywhere in scanned scope:
  app/learning/dual_learning.py:153, inside `_load_meta()` -- falls back to a sane default dict
  on any JSON-decode/read failure. Benign (bad style, not a silent-failure risk) -- read directly,
  confirmed the fallback path is reasonable and doesn't hide a real error condition from any
  caller that needs to know. [VERIFIED]
- Overall: this codebase does NOT exhibit the classic "silent swallow" ghost-code pattern at scale.
  Every non-bare except clause sampled during this audit logs via `logging.warning/error` at
  minimum, consistent with a codebase that has been through repeated self-directed bug-hunt passes
  (confirmed independently, not assumed).

## Self-edit safety pipeline (F1/F2/F3) -- confirmed REAL, not narrated vaporware
- F1: `scan_for_unsafe_operations()` -- real function, app/core/self_edit_manager.py:344.
  Also has real, non-trivial alias-resolution helpers `_resolve_import_aliases()` (:281) and
  `_is_blocked_module_attr()` (:320), wired into the scan at 3 call sites (:395, :418, :435) --
  addresses the "from X import Y" / "import X as y" AST-bypass class, confirmed present as real
  code (not just a comment describing an intended fix). [VERIFIED]
- F2: 3 real `subprocess` invocations of `sandbox-exec -f <profile> ...` checking for the literal
  string "SANDBOX_OK" in stdout, at self_edit_manager.py:772, :1335, :1591 (the third is a
  dedicated `apply_to_code` sandboxed-execution path, distinct from the main staging-test path).
  [VERIFIED]
- F3: `save_code()` (:878) calls `scan_for_unsafe_operations(on_disk)` again after writing to
  disk, at :919 -- confirmed the post-write re-scan is real, not just documented. [VERIFIED]
- `EDIT_FORBIDDEN_TARGETS` (self_edit_manager.py:68) is a real frozenset of 11 protected paths:
  echo_model_orchestrator.py, river_deliberation.py, echo_core.py, memory_bridge.py,
  introspection_channel.py, self_model_updater.py, bible_injection.py,
  app/subsystems/reflection_shard.py, run.py, Modelfile, echo_principles.json. [VERIFIED]
- Net: the self-edit safety architecture is real, load-bearing, and independently verifiable --
  not a facade. (Whether it is *sufficient* against every conceivable bypass is a separate
  question the codebase's own commit history shows active, ongoing hardening against -- e.g. the
  aliased-import fix above.)

## Memory / vector persistence -- confirmed real disk flush, not a discard-after-computation trap
- app/lib/vector_memory.py `VectorMemory.add()` (:87) unconditionally calls `self._persist()` at
  its end (:117) before returning. `_persist()` (:148) does two real, atomic temp-file-then-
  os.replace() writes: meta JSON first, then `faiss.write_index()` for the FAISS index --
  deliberate ordering documented in the function's own docstring to make a mid-write crash
  detectable (meta count > FAISS ntotal) rather than silently corrupting either file. [VERIFIED]
- This directly contradicts the ghost-code pattern the protocol specifically asked to check for
  ("vector store inserts... verify writes are actually flushed to disk and not just held in
  temporary, discarded memory") -- in this codebase, that pattern is NOT present for the core
  vector-memory write path.

## River Brain -- confirmed real online-learning system, not a stub
- `class RiverBrain` (echo_model_orchestrator.py:749) genuinely wraps the third-party `river`
  streaming-ML library: `river.tree.HoeffdingTreeClassifier`, `river.preprocessing.StandardScaler`,
  `river.metrics.Accuracy`, one classifier/scaler/accuracy-tracker per task_type. [VERIFIED]
- `learn()` (:799), `learn_from_sandbox_outcome()` (:861), `learn_from_council_rating()` (:927),
  `score_model()` (:969) are all real methods with real logic (feature extraction, online
  learn_one/predict_one calls, a documented incremental-mean `model_task_stats` dict) -- not
  hardcoded returns. [VERIFIED at the definition level; full behavioral correctness of the ML
  logic itself was not independently re-derived/tested in this pass -- HYPOTHESIS that the
  learning is *effective*, VERIFIED only that it is *real and wired*.]
- A background writer thread (`_writer_thread`, `_writer_loop`) drains a `queue.Queue` for saves
  -- a real single-writer concurrency pattern, not naive unguarded concurrent file writes.
  [VERIFIED at definition level]

## Internet fetch (app/internet_tools/autonomous_fetch.py) -- confirmed real, currently-honest
- `FETCH_SOURCES` (read directly, :86-101): 9 hardcoded sources (Wikipedia AI, StackOverflow,
  3x arXiv, BBC, NPR, Guardian, This Day History) + conditional NASA APOD / NewsAPI entries
  gated on real env-var presence (`if NASA_API_KEY: ... else: logging.debug(...)`), not silently
  no-op'd. [VERIFIED]
- A code comment immediately above the source list (:103-112) states Reddit sources were
  "Removed 2026-07-22" after failing 100% of the time on Reddit's anti-scraping policy -- this
  IS independently confirmed by direct code read (no Reddit entries anywhere in the live
  FETCH_SOURCES list or the rest of the file), not merely narrated. [VERIFIED]
- Real distinct exception handling per failure class (`requests.HTTPError` vs generic `Exception`
  vs `requests.RequestException`), plus a `_DISABLED_SOURCES` set to stop retrying a source that's
  confirmed permanently broken within one process lifetime, rather than hammering it forever.
  [VERIFIED at definition level]
- `_is_duplicate()` (:134) does a real FAISS cosine-similarity dedup check (threshold 0.92)
  before committing a new fetched snippet -- a real mock/ghost-code risk (a fetch source silently
  returning identical content, treated as fresh every cycle) is at least partially mitigated by
  design, though this pass did not independently verify the dedup threshold catches everything
  in practice (that would require live runtime data this static audit does not have access to).
  [HYPOTHESIS on real-world effectiveness; VERIFIED that the mechanism exists and runs before
  each commit]

## Auth surface -- see Phase 1 notes for the full route-by-route table. Summary:
- run.py: ~13 of 42 routes gated behind `_secret_ok()`/HMAC; the rest are either GET read-only
  admin/dashboard endpoints or explicitly-documented-as-intentionally-open (message_send).
- routes_echo_studio.py: zero `_secret_ok()` calls anywhere -- every route in this 720-line file
  (chat_stream, chat_regenerate, dashboard_health, memory_search, memory_browse, activity_log,
  projects_tree, projects_file, settings_view) is unauthenticated at the application layer.
  [VERIFIED] This is a REAL, current finding independent of any prior narrative -- whether this
  is acceptable depends entirely on whether the deployment's network boundary (firewall/Tailscale)
  is actually enforced, which this static audit cannot verify (no live network test performed,
  per the task's "no live-system test" constraint).
- app/sync/echo_messaging.py: `ECHO_PARTNER_SECRET` field IS explicitly stripped before both
  persisting to disk (`_log_message`, :147-157) and before serving via `get_recent_messages()`
  (:160-180, "Defense in depth: strip 'secret' even if it's already on disk") -- confirmed FIXED,
  not a live leak, independently re-verified by direct code read. [VERIFIED]
- app/routes_echo_studio.py `/projects/file`: confirmed hardened -- `_EXCLUDED_DIR_NAMES` path-
  component check PLUS an explicit `.env`-suffix filename block PLUS a content-based
  `_looks_like_secret_dump()` regex scan (7 patterns covering KEY/SECRET/TOKEN/PASSWORD fields,
  sk-/ghp_/github_pat_/AKIA prefixes, PEM private-key headers) -- all three layers present and
  read directly, not narrated. [VERIFIED] The specific historical leak file
  (`new_directory/app/core/env/environment.json`) does not exist in this checked-out worktree at
  all (gitignored, untracked) -- cannot independently confirm whether it exists on a live deployed
  machine's actual filesystem (out of scope for a git-checkout-only audit).

## Test coverage
- Exactly 4 files matching test_*/​*_test.py/tests/ anywhere in the tracked repo, all under
  sandbox/: test_baseline_race.py, test_faiss_atomicity.py, test_smoke.py, sandbox/test_reflect.py.
  [VERIFIED via git ls-files]
- No pytest.ini, no conftest.py, no tox.ini anywhere. [VERIFIED]
- scripts/verify_liveness_ledger.py (871 lines) is a real, substantial, custom discrimination-
  test harness -- NOT pytest-based, a bespoke script asserting specific check() cases against
  known-good/known-degraded evaluator behavior. [VERIFIED] This is a genuine, if unconventional,
  testing investment specifically for the liveness-ledger subsystem; no comparable harness exists
  for most of the rest of the ~600 files under app/.
- Net: "no project-wide test suite" is an accurate, independently-confirmed characterization.

## Liveness Ledger self-audit -- a genuinely interesting, independently-found doc-drift instance
- `_CHECKS` tuple (liveness_ledger.py:2024-2055) contains 30 real, distinct, named checks
  (counted directly from source). [VERIFIED]
- The very next function's docstring (`run_liveness_checks()`, :2062-2065) states: "Run all
  checks in _CHECKS (24 as of 2026-07-22)". 24 != 30. [VERIFIED, discovered independently by this
  audit by counting the tuple myself, not sourced from any pre-existing doc's own claim about
  this discrepancy]
- This is a live, current, self-contained example of exactly the "documentation claims a number
  that the code has since outgrown" failure mode -- occurring inside the one module in the entire
  codebase whose stated purpose is to make sure OTHER subsystems' self-reports can't drift
  silently from ground truth. Worth flagging prominently in the final report as illustrative of
  a systemic pattern in this project (rapid iteration outpacing inline documentation), not just
  a one-off nit.

## No-op / mock-trap sweep (targeted grep, not exhaustive)
- `emergent_scheduler.schedule_task()` -- not independently re-verified this pass (time-boxed);
  flagged as HYPOTHESIS ONLY pending direct read, not claimed as fact for this report.
- No hardcoded `return "mock"` / `return {"status": "ok"}` placeholder patterns found via a quick
  grep sweep of app/core for `# TODO` / `# FIXME` / `NotImplementedError` — [not exhaustively
  swept given time constraints; treat absence-of-evidence cautiously, not as proof of absence].
