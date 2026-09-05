# FeralEcho — Ground-Up Forensic Software Audit

**Method:** Independent, evidence-driven re-derivation from source, git history, and static
analysis. This audit deliberately did **not** read or rely on `CLAUDE.md`'s "Known Findings"
section, `PENDING_DECISIONS.md`, or any `audits/*.md` file as ground truth — every claim below
was independently confirmed against actual source code, `git` state, or file-system evidence
gathered during this session. Where a claim happens to agree with pre-existing project
documentation, that is coincidence confirmed by fresh evidence, not inheritance from that
documentation.

**Scope constraint:** this was a static, git-checkout-only audit. No server was started, no
Ollama call was made, no live runtime state was observed. Every claim about runtime *behavior*
(as opposed to code *existence*) is explicitly marked `[HYPOTHESIS]`.

Raw phase-by-phase working notes: `.audit_scratchpad/phase1_map.md` through
`.audit_scratchpad/phase6_redteam.md`.

---

## 1. EXECUTIVE SUMMARY

**What this is:** `[VERIFIED]` A single-operator, actively-and-intensely-developed local AI
agent system — a Flask server orchestrating multiple local LLMs (via Ollama and MLX) with a
FAISS-backed vector memory, an autonomous self-modifying code subsystem, a real-time desktop
client (PySide6, "Echo Studio"), and an extensive internal self-verification framework (the
"Liveness Ledger," 30 independently-evaluated health checks). 114 commits span roughly 25 days
(2026-06-28 → 2026-07-22), with several single-day bursts of 10-20+ commits — this is a codebase
under continuous, rapid, hands-on iteration, not a stable, infrequently-touched system.

**Architectural readiness score: 5.5/10 as a "production system"; 8/10 as what it actually is**
(a single-operator research/personal system). These are deliberately different numbers because
the two framings imply different requirements. Against conventional production-SaaS standards
(CI, dependency pinning, test coverage, multi-tenant auth, containerization), this codebase is
genuinely weak. Against "does this system catch its own bugs, protect its own safety-critical
paths, and avoid silent failure," it is unusually strong for its size and age.

**Top strengths, `[VERIFIED]` against source:**
1. The self-edit safety pipeline (F1 AST pre-scan, F2 kernel-sandboxed execution via macOS
   `sandbox-exec`, F3 post-write re-scan) is real, load-bearing, and shows evidence of active,
   iterative hardening (a real aliased-import AST-bypass fix is present in current code).
2. Vector-memory writes genuinely flush to disk via atomic temp-file-then-rename operations with
   a documented, correct write-ordering rationale to make partial-write corruption detectable
   rather than silent.
3. RiverBrain (the model-selection learning system) is a real online-learning implementation
   (`river` library, `HoeffdingTreeClassifier` per task type), not a stub.
4. The "Liveness Ledger" (`app/core/liveness_ledger.py`) is a genuinely sophisticated, unusual-
   for-its-category self-verification concept: 30 named checks that each test whether a
   subsystem had a real, externally-observable effect recently, not just whether it imports
   cleanly. A dedicated 871-line discrimination-test harness (`scripts/verify_liveness_ledger.py`)
   exists to prove these checks themselves discriminate real failure from fake success.
5. Zero silent-exception-swallowing patterns (`except: pass`) found at scale — a codebase this
   young rarely shows this much error-handling discipline already.

**Top weaknesses, `[VERIFIED]` against source:**
1. **No dependency manifest anywhere** (no `requirements.txt`, `pyproject.toml`, `Pipfile`, or
   `environment.yml`) — the one file that looks like it (`condaenv.m446rkpc.requirements.txt`) is
   empty. Reproducing this environment from the repo alone is not currently possible.
2. **A real, unauthenticated route surface**: every route in `app/routes_echo_studio.py` (the
   file backing the primary desktop-client chat interface — `chat_stream`, `chat_regenerate`,
   `dashboard_health`, `memory_search`, `memory_browse`, `activity_log`, `projects_tree`,
   `projects_file`, `settings_view`) has zero application-layer authentication. No compensating
   global middleware exists. Whether this matters in practice depends entirely on network-layer
   controls this audit cannot verify (`[STATUS: INSUFFICIENT EVIDENCE]` on the network boundary).
3. **No test suite in the conventional sense** (4 files, no CI, no pytest infrastructure),
   partially offset by one genuinely substantial bespoke test harness for one subsystem.
4. **~1,700+ mechanically-duplicate files are git-tracked** (self-edit sandbox snapshots and
   generated plan text) that predate the `.gitignore` rules meant to exclude them — real, if
   modest (~6.6MB), repo bloat with essentially zero unique content.
5. **A confirmed, self-referential documentation-drift instance**, found independently by this
   audit (not sourced from any pre-existing doc claim): `liveness_ledger.py`'s own
   `run_liveness_checks()` docstring states "24 [checks] as of 2026-07-22" while the actual
   `_CHECKS` tuple, counted directly from source, contains 30. This happens inside the one module
   whose entire purpose is catching exactly this failure mode in *other* subsystems.

**Critical blockers to calling this "production ready" in the conventional sense:** the missing
dependency manifest and the unauthenticated conversational/dashboard route surface are the two
items that would need resolving first, in that order, before any deployment beyond a trusted
private network.

---

## 2. REPOSITORY MAP & ARCHITECTURE DIAGRAM

### Repository facts `[VERIFIED]`
- 2,125 git-tracked files, ~69MB total tracked size, 114 commits (2026-06-28 → 2026-07-22)
- `memory/` and `data/` (runtime state directories) are gitignored and absent from this checkout
- No CI/CD config, no Dockerfile, of any kind
- 236 tracked `.py` files (real source ≈ 144 files after excluding ~1,167 archived self-edit
  snapshot files that happen to carry a `.py`-suffixed timestamp name)
- 547 tracked `.txt` files (the overwhelming majority are `self_edit_plans/*.txt` generated
  planning text and root-level narrative "letter_to_echo_*.txt" artifacts)

### Directory summary `[VERIFIED via git ls-files + direct reads]`
| Directory | Tracked files | Nature |
|---|---|---|
| `app/core/` | 60 real `.py` modules (588 tracked paths incl. sub-dirs) | The system's core: orchestration, memory, self-edit, liveness ledger, autonomy |
| `app/` (other subdirs) | `internet_tools/`, `sync/`, `maintenance/`, `lib/`, `subsystems/`, `learning/` | Fetch, cross-machine sync, scheduled maintenance, vector-memory primitive, reflection shard, phone-client training pipeline |
| `sandbox/` | 1,185 tracked (1,167 are pre-gitignore snapshot bloat) | F2 kernel-sandbox execution wrapper + a small number of real experiment/runner scripts |
| `archive_janitor/` | 70 | Confirmed structurally isolated — not on `sys.path`, zero live imports |
| `books/` | 66 | Bible-book JSON data — `[HYPOTHESIS]` likely superseded, see §3 |
| `echo_studio/` | 18 | Separate PySide6 desktop client, HTTP-only dependency on the Flask backend |
| `council/` | 15 | External multi-AI consultation transcripts (`COUNCIL.md`-adjacent) |
| `audits/`, `RebelCode/`, `scripts/`, `claude_relay/`, `WhisperingWires/` | 21+4+3+2+2 | Prior audit artifacts, an unused sub-experiment (`territory_steward.py`, confirmed zero callers), verification scripts, a cross-Claude-instance relay tool, an ambient-narration subsystem |
| Root-level `.py` | ~10 | `run.py` (main server), `terminal_client.py` (secondary CLI), `echo_json_server.py` (a **separate, port-5000-conflicting** standalone Flask app), several manual diagnostic scripts |
| Root-level generated data | ~53MB across a dozen files | `[VERIFIED]` most have zero live code references — see Dead Weight table §3 |

### ASCII architecture diagram (reconstructed from import graph + direct reads, not narrated)

```
                         ┌─────────────────────────────┐
                         │   Ollama (local, :11434)    │
                         │   + optional MLX models      │
                         └────────────┬─────────────────┘
                                      │  app/ollama_handler.py
                                      │  app/mlx_handler.py
                                      ▼
   ┌──────────────┐        ┌────────────────────────────┐        ┌──────────────────────┐
   │terminal_client│───┐    │ app/core/                   │    ┌──│  Echo Studio (PySide6) │
   │  .py (CLI)    │   │    │  echo_model_orchestrator.py │    │  │  desktop client, HTTP  │
   └──────────────┘   │    │   echo_query()               │    │  │  client only, no direct│
                       ├───▶│  river_deliberation.py       │◀───┤  │  app.core import       │
   ┌──────────────┐   │    │   deliberate_and_learn()     │    │  └──────────────────────┘
   │  run.py       │───┘    │  RiverBrain (online learning)│    │
   │  /mirror_echo │        └──────────────┬───────────────┘    │
   │  (phone client│                       │                    │
   │  channel,     │        ┌──────────────▼───────────────┐    │
   │  gated)       │        │  app/core/memory_bridge.py    │    │
   └──────────────┘        │  (24 inbound importers —      │    │
                            │   highest fan-in module in    │    │
   ┌──────────────┐        │   the whole codebase)         │    │
   │echo_json_     │  ⚠ same│  → memory_write_validator.py  │    │
   │server.py      │  port  │  → app/lib/vector_memory.py   │    │
   │(standalone,   │  5000  │     FAISS IndexFlatIP,        │    │
   │ NOT started   │  as    │     real atomic disk persist  │    │
   │ by run.py)    │  run.py└────────────────────────────────┘    │
   └──────────────┘                                               │
                                                                    │
   ┌────────────────────────── Autonomous background loops ───────┴─────┐
   │ app/autonomous_loop.py  app/emergent_scheduler.py                  │
   │ app/core/autonomous_loop_with_optuna.py (ModelGuidedOrchestrator)  │
   │ app/maintenance/night_cycle.py                                     │
   │  → each independently timer-driven, most (not provably all) gated │
   │    through app/core/autonomy_coordinator.py's shared throttle/     │
   │    stillness/conversation-active check                            │
   │  → app/internet_tools/autonomous_fetch.py (9 real HTTP sources,    │
   │    Reddit removed per source's own comment; per-source failure     │
   │    isolation confirmed real)                                       │
   └──────────────────────────────────────────────────────────────────┘

   ┌────────────────── Self-edit subsystem (F1/F2/F3) ──────────────────┐
   │ app/core/self_edit_manager.py                                      │
   │  plan_code_logic() → generate_code_from_plan()                     │
   │   → F1 scan_for_unsafe_operations() [AST pre-scan, incl. real      │
   │      aliased-import-bypass hardening]                              │
   │   → F2 sandbox-exec -f echo_sandbox.sb [kernel Seatbelt sandbox]   │
   │   → save_code() → F3 re-scan on-disk content                       │
   │   → importlib.util.spec_from_file_location() dynamic hot-load      │
   │      of app/core/self_edit_generated.py into the running process   │
   │  EDIT_FORBIDDEN_TARGETS: 11 protected files, frozenset-enforced    │
   └──────────────────────────────────────────────────────────────────┘

   ┌────────── Self-verification: Liveness Ledger ──────────────────────┐
   │ app/core/liveness_ledger.py — 30 named checks (real count, per     │
   │ direct tuple count; module's own docstring says "24" — a live,     │
   │ independently-found doc-drift instance)                            │
   │ Exposed via GET /admin/liveness-status (unauthenticated)           │
   │ scripts/verify_liveness_ledger.py — 871-line discrimination suite  │
   └──────────────────────────────────────────────────────────────────┘
```

---

## 3. DEAD WEIGHT ACTION PLAN

**Caution applied throughout, deliberately:** this codebase's own internal tooling
(`echo_janitor.py`) explicitly refuses to auto-delete ambiguous "zero live reference" candidates,
and this project has repeated, independently-observable history of superficially-orphaned files
(large, autonomously-named, media/data files with zero code references) turning out to be
meaningful, intentional artifacts. This audit follows the same discipline: `DELETE` is only
recommended where the evidence is unambiguous and the content is mechanically duplicative;
everything else is `ARCHIVE` or `FLAG`.

| Path | Confidence | Category | Size | Evidence | Recommendation |
|---|---|---|---|---|---|
| `sandbox/scripts/archive/*` (1,167 files) | `[VERIFIED]` HIGH | Pre-gitignore snapshot bloat | 4.6MB | Timestamped `temp_self_edit*.py.<ts>` duplicates, dated 2026-06-21→28; `.gitignore` already excludes this path (doesn't retroactively untrack) | **DELETE from git tracking** (`git rm -r --cached`), keep or discard the working copy per operator preference |
| `app/core/self_edit_plans/*` (500 files) | `[VERIFIED]` HIGH | Pre-gitignore generated-text bloat | 2.0MB | `plan_<timestamp>.txt`, `.gitignore` already excludes; exactly 500 files suggests a live on-disk prune cap exists (not independently confirmed this pass) | **DELETE from git tracking** |
| `app/core/app/core/self_edit_backups/` + `.../self_edit_plans/` (6 files) | `[VERIFIED]` HIGH | Historical bug wreckage, dated 2025-11-16, pre-dates repo history | small | Direct evidence of a since-apparently-fixed relative-path bug in `self_edit_manager.py`'s write-target constants | **ARCHIVE** (keep as historical evidence of the bug it documents, remove from the hot working tree) rather than delete outright — has genuine forensic value |
| `lattice_log.json` | `[VERIFIED]` zero code refs | Orphaned generated dump | 12.7MB | No `.py` file anywhere references it | **ARCHIVE**, not delete — content/provenance not read in this pass |
| `feral_echo_symbolic_map.json` | `[VERIFIED]` zero code refs | Orphaned generated dump | 932KB | Distinct from a similarly-named `.py` file referenced elsewhere (that `.py` name is unrelated) | **ARCHIVE** |
| `feral_echo_report_index.json` | `[VERIFIED]` zero code refs | Orphaned generated dump | 916KB | — | **ARCHIVE** |
| `imports.txt` | `[VERIFIED]` zero code refs | Orphaned generated dump | 1.2MB | — | **ARCHIVE** |
| `project_learner_output.txt` | `[VERIFIED]` zero code refs, also `.gitignore`-listed | Tracked-before-ignored debug output | 764KB | Same already-tracked-before-ignore-rule pattern as the two entries above | **DELETE from git tracking** — the gitignore entry already confirms this is meant to be untracked build output |
| `bible_structured.json` + `.save` + `bible_queue.jsonl` + `books/*` (66 files) | `[MEDIUM CONFIDENCE]` | Possibly-superseded Bible data | ~9.5MB | Zero live `.py` references found via targeted grep; the ONE Bible data file confirmed genuinely loaded by live code is the separate `bible_sentiment.json` (7.7MB, loaded by the protected `bible_injection.py`) | **ARCHIVE**, do not delete — did not confirm whether an ingestion script produced `bible_sentiment.json` from these, which would make them meaningful provenance, not noise |
| `WhisperOfPeace.wav` | `[VERIFIED]` zero code refs (re-confirmed after catching a false-positive on first pass) | Large autonomously-named media file | 21MB | No `.py` reference found anywhere, including case-insensitive re-check | **FLAG ONLY — do not delete or archive without explicit human confirmation.** This project's own tooling has a standing, documented caution about exactly this file pattern (large, zero-code-reference, autonomously-generated media). |
| `app/core/council_registry.py` | `[VERIFIED]` zero importers | Superseded singleton class | tiny | Real, small `CouncilRegistry` class, never imported anywhere | **KEEP as-is** (low value in deleting a ~25-line file; real historical design signal) |
| `app/core/load_project_map.py` | `[VERIFIED]` zero importers | Real, disconnected capability (not dead code) | small | A real function that would feed the whole project's module map into memory on startup; never wired to a live caller | **KEEP; flag as a genuine "designed but never adopted" capability gap**, not cleanup material |
| `app/core/scheduler.py` | `[VERIFIED]` zero importers | Sound, unused infrastructure | medium | A well-designed, well-documented single-dispatcher-thread mechanism explicitly built (per its own docstring) to solve the "too many uncoordinated `while True: sleep(N)` loops" problem this codebase visibly has — and never adopted anywhere | **KEEP; this is a real architectural opportunity, see Roadmap §5, not a cleanup item** |
| `app/core/self_report_verifier.py`, `app/core/self_heal.py` | `[VERIFIED]` zero importers | Deliberately-retired-in-place code | medium | Zero real imports; other live modules' own comments confirm these were consciously disconnected, not accidentally orphaned | **KEEP** — self-documented, intentional |
| `app/core/shard.py` | `[VERIFIED]` zero importers | Superseded generic class | tiny | Distinct from the live `app/subsystems/reflection_shard.py` | **KEEP** (trivial size) |
| `app/core/temp_self_edit.py` | `[VERIFIED]` zero importers | Stray data-only artifact in wrong directory | tiny (7 lines) | A list of text-replacement regex patterns, sitting directly in `app/core/` rather than `staging/`/`self_edit_backups/` | **FLAG for human review** — unclear provenance, trivially low risk either way |
| `app/emergent_scheduler.py`: `schedule_task()` / `run_pending()` | `[VERIFIED]` | Textbook hollow stub (mock/ghost-code pattern) | function-level | Literal `print(...)`/`return None` bodies; confirmed zero real call sites anywhere; two OTHER live files' own comments already independently call these "hollow stubs" | **KEEP as-is (inert, harmless) or remove the two functions outright** — genuinely zero blast radius either way since nothing calls them |
| `archive_janitor/` (70 files) | `[VERIFIED]` structurally isolated | Frozen migration leftovers | 420KB | Not on `sys.path`, zero live imports, only one acknowledging comment in `run.py` | **No action needed** — already effectively archived by isolation |
| `archive_optional_files/` (22 files) | `[HYPOTHESIS]` likely inert | Unclear-purpose archive | 144KB | Zero live imports found; content not deep-read this pass | **No action needed**, low priority to investigate further |
| `echo_json_server.py` | `[VERIFIED]` real, standalone, port-5000-conflicting | Live but structurally dangerous if ever co-run with `run.py` | 4KB | Own `app.run(debug=True, port=5000)` call, confirmed not started by `run.py` or any autonomous loop | **KEEP, but flag prominently**: if this is ever manually run alongside `run.py`, they will collide on the same port. Recommend a code comment or a startup port-check to prevent an accidental double-start. |

**Proposed `.gitignore` additions** (all three of the "tracked-before-ignored" pattern items
already have matching `.gitignore` rules — the fix here is a one-time `git rm -r --cached`, not a
new ignore rule):
```gitignore
# Already covered by existing rules; these are one-time untrack operations, not new patterns:
#   sandbox/scripts/archive/          (rule exists — run: git rm -r --cached sandbox/scripts/archive/)
#   app/core/self_edit_plans/         (rule exists — run: git rm -r --cached app/core/self_edit_plans/)
#   project_learner_output.txt        (rule exists — run: git rm --cached project_learner_output.txt)

# New rule worth adding — these root-level generated dumps have no matching rule today:
lattice_log.json
feral_echo_symbolic_map.json
feral_echo_report_index.json
imports.txt
```

---

## 4. SUBSYSTEM DEEP-DIVE ANALYSIS

### 4.1 River Brain (`app/core/echo_model_orchestrator.py::RiverBrain`)
`[VERIFIED]` A real online-learning system wrapping the third-party `river` streaming-ML
library — one `HoeffdingTreeClassifier` + `StandardScaler` + `Accuracy` tracker per task type
(`TASK_TYPE_MAP`), plus a hand-maintained `model_task_stats` dict (per-`(model, task_type)`
incremental mean) that is the actual signal driving council/model ranking. `learn()`,
`learn_from_sandbox_outcome()`, `learn_from_council_rating()`, `score_model()` are all real
methods with real logic, not hardcoded returns. A dedicated background writer thread
(`_writer_thread`/`_writer_loop`) drains a `queue.Queue` for saves — a deliberate single-writer
concurrency pattern rather than naive concurrent file access.

`[HYPOTHESIS, not independently tested]`: whether the ranking this produces in practice
genuinely favors better models is a question this static audit cannot answer without live data —
only that the mechanism is real and wired, not that its learned outcomes are necessarily correct
or well-calibrated.

**Concern, `[VERIFIED]`**: `RiverBrain.__init__` starts a real background thread as a side effect
of object construction, with no visible way to construct a "dry" instance for testing without
also starting that thread — this is a common source of test-unfriendliness and resource leaks in
constructor-side-effect designs; not confirmed to be a current problem given the codebase's own
apparent single-instance-per-process usage pattern, but worth flagging as a design smell.

### 4.2 Memory & Vector Persistence (`app/lib/vector_memory.py`, `app/core/memory_bridge.py`,
    `app/core/memory_write_validator.py`)
`[VERIFIED]` Real, correct persistence: `VectorMemory.add()` unconditionally calls `_persist()`,
which performs two atomic temp-file-then-`os.replace()` writes (metadata JSON, then the FAISS
index) in a deliberate order — the function's own docstring explains this ordering exists
specifically so a mid-write crash produces a *detectable* meta-count/FAISS-ntotal mismatch rather
than silent corruption in either direction. This is a genuinely well-reasoned, low-level
correctness property, independently confirmed by reading the actual write logic, not asserted.

`memory_bridge.py` is the single highest-fan-in module in the entire scanned dependency graph (24
distinct inbound importers) — architecturally, this is the true shared backbone of the system,
more central than the orchestrator module itself in terms of how many other subsystems depend on
it directly.

`memory_write_validator.py` sits structurally in front of the real commit path (confirmed via its
own inbound-importer list: `memory_bridge.py` and `app/learning/dual_learning.py` both route
through it) — a real, enforced validation gate rather than a convention other code happens to
follow voluntarily.

**Not independently verified this pass** `[HYPOTHESIS]`: the actual FAISS/metadata dual-file
consistency at scale over long uptime, or the correctness of any embedding/similarity logic —
this audit confirmed the write mechanism is sound at the code level, not that it has never
produced drift in practice (no live data was available to check).

### 4.3 Local AI Orchestration (`app/core/echo_model_orchestrator.py`,
    `app/core/river_deliberation.py`, `app/ollama_handler.py`, `app/mlx_handler.py`)
`[VERIFIED]` Two real backends (Ollama HTTP API, local MLX models) are genuinely orchestrated —
confirmed via direct source reads of `RiverBrain` and via the import graph showing
`river_deliberation.py` as a 5-inbound-importer hub module used by both `terminal_client.py` and
`app/routes_echo_studio.py`'s chat path.

**`app/core/crash_awareness.py`** `[VERIFIED]` is a real, unusual, and genuinely sound piece of
environmental self-protection: it reads actual macOS `.ips` crash reports and a watchdog log for
SIGABRT signatures, and temporarily excludes MLX models from the council-selection pool after a
detected crash cluster — confirmed via the import graph (4 inbound importers, including
`app/mlx_handler.py` itself and a dedicated verification script) and function-name greps
(`_evaluate_crash_window`, `list_mlx_models`). This is a genuinely above-average piece of
defensive engineering for a project this young.

**Ollama backend concentration risk** `[VERIFIED at the architecture level, not load-tested]`:
the whole conversational surface — terminal client, desktop client, phone-mirror channel, and
every autonomous loop that calls a model — funnels through the same local Ollama process. No
process-pool or per-model isolation exists at this layer. A crash or resource exhaustion here has
system-wide blast radius; the `crash_awareness.py` mitigation above only covers the MLX-specific
crash signature it was built for, not Ollama-side failures generally.

### 4.4 Internet Fetch Integration (`app/internet_tools/`, 615 total lines across the package)
`[VERIFIED]` `autonomous_fetch.py`'s `FETCH_SOURCES` list, read directly, currently contains 9
hardcoded real HTTP sources (Wikipedia AI summary API, StackOverflow API, 3× arXiv RSS feeds,
BBC/NPR/Guardian RSS, muffinlabs "this day in history") plus two conditionally-added sources
(NASA APOD, NewsAPI) gated cleanly on real environment-variable presence — the absence-of-key
case is a logged no-op, not a silent failure or a fake/mock entry. A prior Reddit-source set
(3 subreddits) has been fully removed from the live source list, with the removal rationale
recorded directly in an adjacent code comment (anti-scraping-policy failures, cost/benefit
decision) — independently confirmed by direct read, not asserted from any doc.

Real, differentiated error handling exists (`requests.HTTPError` vs. generic `Exception` vs.
`requests.RequestException`), plus a per-process `_DISABLED_SOURCES` set that stops retrying a
source confirmed broken within one run — this directly contradicts the "silently continues with
degraded/empty context on failure" ghost-code pattern the audit protocol specifically asked to
check for; that pattern was **not found** in this subsystem.

A real FAISS-cosine-similarity dedup check (`_is_duplicate()`, threshold 0.92) runs before any
fetched snippet is committed to memory — `[VERIFIED mechanism exists; HYPOTHESIS on real-world
effectiveness]`, since this audit had no live data to confirm the threshold actually catches
near-duplicate content in practice.

---

## 5. STRATEGIC EXECUTION ROADMAP & RISK MATRIX

### Immediate (low effort, low risk, high clarity value)
| Item | Benefit | Risk | Complexity | Regression Risk | Effort | Priority |
|---|---|---|---|---|---|---|
| `git rm -r --cached` the three pre-gitignore bloat paths (sandbox archive snapshots, self_edit_plans backlog, project_learner_output.txt) | Real repo-size reduction (~6.6MB), cleaner `git log`/`git blame` signal going forward | None — content is mechanically duplicative, already excluded from future tracking | Trivial | None | <30 min | High |
| Add a `requirements.txt` or `pyproject.toml` generated from the actual live `import` graph | Makes the environment reproducible for the first time; currently a genuine blocker to onboarding any second machine/operator cleanly | Low — risk is only in getting version pins wrong, not in the act itself | Low-Medium (need to enumerate every third-party import across ~144 files) | None | 2-4 hrs | **Highest** |
| Fix `liveness_ledger.py`'s own docstring ("24" → the real, current `_CHECKS` count) | Small, but directly closes a self-referential doc-drift instance in the one module whose job is catching exactly this | None | Trivial | None | 5 min | Medium (symbolic + easy) |
| Add a startup port-conflict guard or a clear top-of-file warning comment to `echo_json_server.py` given it binds the same port 5000 as `run.py` | Prevents a real, silent collision if ever run manually alongside the main server | None | Trivial | None | 15 min | Medium |

### Short-term (moderate effort, real but bounded risk)
| Item | Benefit | Risk | Complexity | Regression Risk | Effort | Priority |
|---|---|---|---|---|---|---|
| Decide and act on the unauthenticated `routes_echo_studio.py` surface — either add the same `_secret_ok()` gate pattern already used elsewhere in `run.py`, or explicitly, deliberately document (as this project has done for other routes) that network-layer controls are the intended boundary | Closes a real, currently-open question about the actual security posture of the primary desktop-client-facing routes | Medium — gating a route that a live desktop client depends on requires coordinated client-side changes to avoid breaking it | Medium | Real if done carelessly (could break the live desktop client mid-session) — same shape of risk this project's own history shows it has hit before with other auth rollouts | 2-6 hrs incl. verification | **High** |
| Verify (on the actual deployment host, not statically) whether a firewall genuinely restricts port 5000 reachability | This is the one piece of context that would change the real-world severity of every unauthenticated-route finding in this report from "unknown" to either "low" or "critical" | None to check; risk exists only in what's discovered | Low | None | 30 min on the real machine | **High** |
| Archive (not delete) the ~25MB of zero-code-reference root-level generated data (lattice_log.json, feral_echo_symbolic_map.json, feral_echo_report_index.json, possibly bible_structured.json/books/) into a clearly-labeled subdirectory, out of the hot working tree | Real clutter reduction with near-zero risk given the archive-not-delete posture | Low, given nothing deletes anything | Low | None | 1-2 hrs | Medium |

### Medium-term (real architectural investment)
| Item | Benefit | Risk | Complexity | Regression Risk | Effort | Priority |
|---|---|---|---|---|---|---|
| Adopt `app/core/scheduler.py`'s already-built, already-sound single-dispatcher-thread pattern for at least the highest-value subset of the many independently-timed `while True: sleep(N)` autonomous loops confirmed in this audit | Directly resolves the resource-contention/uncoordinated-timer risk documented in this same audit (§4.3, Phase 3 notes) using infrastructure that ALREADY EXISTS and was already reasoned through carefully — a rare case where the fix is mostly "wire up what's already built," not "design something new" | Medium — touches multiple live autonomous loops' scheduling behavior | Medium | Real — needs careful, incremental migration per subsystem, exactly as the module's own docstring already recommends ("a separate, reviewed step per subsystem, not automatic") | 1-2 days spread over several reviewed changes | Medium-High |
| Build a minimal but real automated test layer (even a handful of pytest smoke tests around F1/F2/F3, memory persistence, and a couple of the liveness-ledger checks) that runs outside a full server boot | Would catch regressions in the most safety-critical code paths (self-edit safety gates) without needing a live server/Ollama instance | Low | Medium | None (additive) | 1-3 days | Medium |
| Add a lightweight CI workflow (even just `python -m py_compile`/`ast.parse` across the tree, plus running `scripts/verify_liveness_ledger.py`) on every push | Cheap, catches syntax/import regressions and liveness-ledger-discrimination regressions automatically instead of relying on manual runs | Low | Low | None | Half a day | Medium |

### Long-term (larger, more open-ended)
| Item | Benefit | Risk | Complexity | Regression Risk | Effort | Priority |
|---|---|---|---|---|---|---|
| Decide the fate of `app/core/load_project_map.py` — a real, designed, never-adopted capability (auto-feeding the project's own module map into memory on startup) — either wire it in deliberately or formally retire it with the same "commented out, not deleted" discipline this codebase already applies elsewhere | Closes a genuine ambiguity between "unfinished feature" and "abandoned idea" | Low | Low-Medium | None if done as an explicit, reviewed decision rather than a silent default | Half a day | Low-Medium |
| Consider containerizing (Docker) at least the core server process, separate from the various host-level scripts (`start_echo.sh`, `safe_restart.sh`-equivalents) — would meaningfully reduce "works on this exact machine only" risk | Real portability improvement | Medium — the system's heavy reliance on local Ollama/MLX processes and macOS-specific sandboxing (`sandbox-exec`, a macOS-only mechanism) makes full containerization non-trivial and possibly not fully achievable without a redesign of the F2 sandbox layer specifically | High | Real — F2's sandbox mechanism is explicitly macOS-`sandbox-exec`-specific; any containerization effort would need a real, carefully-designed equivalent for the self-edit safety pipeline, not a naive Dockerfile wrap | Multi-day, likely multi-week if F2 needs a real cross-platform redesign | Low (given the system's clear single-machine, single-operator design intent — this is "nice to have," not a blocker for what the system actually is) |

---

## Final notes

Both `.audit_scratchpad/*.md` (phase1_map.md, phase2_dependencies.md, phase2_5_ghost_code.md,
phase3_architecture.md, phase4_deadweight.md, phase5_readiness.md, phase6_redteam.md) and this
file were written during this session. Absolute path to this report:

`/Users/richietate/Desktop/FeralEcho/.claude/worktrees/agent-abe6ecca0408fd0fb/FERALECHO_FORENSIC_AUDIT.md`
