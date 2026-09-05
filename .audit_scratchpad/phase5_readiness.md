# Phase 5: Production Readiness & Architectural Evaluation (raw notes)

## Maintainability
- No dependency manifest (requirements.txt/pyproject.toml/environment.yml) anywhere in the
  tracked repo -- confirmed via git ls-files. All third-party deps must be inferred from `import`
  statements; there is no single source of truth for "what needs to be installed." [VERIFIED]
- No CI/CD config (no .github/workflows, no Dockerfile, no ci.yml of any kind). [VERIFIED]
- 30,356+ LOC across real (non-archive) .py source (app/ + root scripts), no formal test suite
  beyond 4 sandbox concurrency/smoke tests and one substantial (871-line) bespoke discrimination
  harness for one specific subsystem (liveness_ledger). [VERIFIED]
- The codebase shows strong EVIDENCE of active, disciplined self-maintenance at the process level
  (bug-hunt passes, a self-verifying "liveness ledger" concept, protected-file lists, atomic
  writes with documented ordering rationale) -- this is unusual and noteworthy: the *practice*
  of catching and fixing real bugs is clearly present and sophisticated, even though the
  *tooling* (tests, CI, dependency pinning) that would normally embody that practice is largely
  absent or improvised. [VERIFIED via direct code reads across many files]
- Documentation: CLAUDE.md (the project's main internal doc) is enormous (per Phase 1 stat,
  ~430KB) and admits to its own drift in multiple independently-observed places (the liveness
  ledger's own check-count docstring saying "24" against a real, counted 30 is a fresh, directly-
  observed example, not sourced from the doc's own text). A doc this large, updated this
  frequently, for a single-operator/AI-assisted project, is itself a maintainability signal --
  valuable as an audit trail, but a real risk that any given specific claim in it may be stale.

## Scalability
- Flask `threaded=True`, single process, single Ollama backend (1 concurrent generation slot by
  Ollama's own default `-np` behavior, referenced by several file comments though not
  independently load-tested this pass). No process manager, no horizontal scaling story, no
  message queue, no external cache. This is architecturally a single-machine, single-operator
  system by design (matches its own `.env.example`'s `OLLAMA_URL=http://localhost:11434` local
  default) -- NOT built for multi-tenant or high-concurrency use, and nothing in the code
  suggests it was meant to be. [VERIFIED via config defaults + architecture]
- Real, in-process background thread count is high (self-edit loop, emergent scheduler,
  autonomous_loop, model-guided orchestrator, DMN guardian, introspection channel, council rater,
  reflection shard autonomy, and more -- confirmed via the `__main__`/thread-start grep in
  Phase 1) -- a real resource-contention risk on a single process, partially mitigated by the
  `autonomy_coordinator.py` shared throttle/stillness gate (confirmed 8 inbound importers) but
  NOT confirmed to cover every loop (see Phase 3 honest-gaps note).

## Observability
- Real, structured internal introspection exists: `app/core/introspection_channel.py` (a 120s-
  cadence collector writing a live JSON state file) and `app/core/liveness_ledger.py` (30 named,
  independently-evaluated checks, each producing pass/fail + evidence, exposed via a real
  `/admin/liveness-status` GET route). [VERIFIED via direct reads/grep] This is a genuinely
  above-average observability posture for a project with no formal test suite or CI -- the
  liveness-ledger concept in particular (checking a subsystem's *actual effect*, not just whether
  it imports) is a real, sound engineering idea, independently confirmed as functioning code, not
  just aspirational design.
- Logging: standard Python `logging.basicConfig` in run.py (confirmed), no structured/JSON
  logging, no external log aggregation, no metrics/tracing (no Prometheus, no OpenTelemetry, no
  StatsD references found anywhere in a targeted grep). Root-level plain-text log files
  (`memory/*.log`, gitignored, not present in this checkout) are the primary observability
  surface at runtime -- adequate for a single-operator system, would not scale to a team.

## Security
- See Phase 2.5 for the full auth-surface table. Summary: a real, working shared-secret HMAC
  auth pattern (`_secret_ok()`, fails closed) protects the state-mutating/admin-heavy POST routes
  in run.py; a large surface of GET routes (dashboard/health, memory/search, memory/browse,
  activity/log, projects/tree, projects/file, settings/view, and all of `/admin/*`'s read-only
  GET endpoints) and the two chat-streaming POST routes (`/chat/stream`, `/chat/regenerate`) are
  confirmed to have ZERO application-layer authentication. [VERIFIED, no before_request/WSGI
  middleware exists to compensate -- confirmed absent]. Whether this is an acceptable risk
  depends entirely on network-layer controls (host firewall / VPN-only reachability) that a
  static, git-only audit cannot verify one way or the other -- this is a REAL, UNRESOLVED
  UNKNOWN, not a claim of "it's fine because of Tailscale" or "it's broken because of the
  internet" -- [STATUS: INSUFFICIENT EVIDENCE on the network boundary specifically].
- File-serving endpoint (`/projects/file`) has real, multi-layered hardening (path-containment,
  directory-name blocklist, .env-suffix filename block, content-based secret-pattern scanning) --
  confirmed via direct read, a genuinely well-built defense-in-depth implementation for what it
  covers. [VERIFIED]
- `/nuke` route (immediate hard process kill on a matching secret) exists and is confirmed gated
  by the same fail-closed `_secret_ok()` helper -- confirmed NOT independently exploitable via an
  unset-secret bypass (the `if not GREMLIN_SECRET: return False` fail-closed logic was directly
  re-verified in Phase 2.5's red-team check). [VERIFIED]
- No secret material found in any currently-tracked file via a targeted regex sweep (API-key/
  token/AWS-key/PEM-header shaped strings). [VERIFIED, not exhaustive -- a full-history git-log
  secret scan across all 114 commits was not performed in this pass, only a working-tree sweep]
- F1/F2/F3 self-edit safety pipeline: confirmed real and load-bearing (Phase 2.5). A real,
  fixed-in-current-code aliased-import AST-bypass hardening exists
  (`_resolve_import_aliases`/`_is_blocked_module_attr`), suggesting active, iterative security
  hardening of this specific mechanism over the project's short history.

## Offline operation
- Primary conversational path is fully local (Ollama on localhost, optional local MLX models) --
  confirmed via `.env.example` defaults and the import graph (no cloud-LLM import on the primary
  chat path). One optional, explicitly rate-limited outbound Anthropic API call exists in
  `app/internet_tools/claude_research.py`, structurally separate from the main conversational
  flow (not imported by `echo_model_orchestrator.py`). [VERIFIED via import graph]
- Autonomous background loops DO make real outbound HTTP calls (Wikipedia, StackOverflow, arXiv,
  BBC, NPR, Guardian, muffinlabs, optionally NASA/NewsAPI) -- confirmed real, with real
  per-source failure isolation (`_DISABLED_SOURCES`) so one broken source doesn't take down the
  whole fetch cycle. Offline/air-gapped operation of the CORE chat loop is real; full autonomous-
  background-loop operation is not (by clear design, not a bug).

## Error handling
- See Phase 2.5: zero bare `except: pass` swallow patterns found at scale; one legitimate bare
  `except:` with a safe, logged-equivalent fallback. Multiple modules show evidence of iterative
  hardening against real concurrency races (documented lock additions, atomic temp-file-then-
  rename write patterns) -- a genuinely mature error-handling posture for a project this young
  (first commit ~25 days before the audit's reference date).

## Test coverage
- Confirmed minimal by conventional standards (4 files, no pytest infra) but PARTIALLY offset by
  a real, substantial custom discrimination-test script for the liveness ledger (871 lines,
  genuinely exercising real evaluator functions against known-good/known-degraded synthetic
  cases) -- this is unconventional test infrastructure, not the complete absence the raw file
  count alone would suggest, but it covers ONE subsystem, not the ~600-file `app/` tree broadly.

## Overall readiness characterization
This is NOT a project ready for multi-tenant, team-maintained, or high-availability production
deployment (no CI, no dependency pinning, no containerization, single-process/single-machine
architecture, meaningful unauthenticated attack surface pending an unverified network boundary).
It IS a genuinely sophisticated, actively-and-carefully-maintained SINGLE-OPERATOR research/
personal system, with above-average-for-its-category internal self-verification tooling (the
liveness ledger concept specifically) and real evidence of iterative security/correctness
hardening over a short but intense development history. The right lens for evaluating it is
"personal research system with unusually mature internal self-checks," not "production SaaS
codebase" -- treating gaps like missing CI/tests as damning would misjudge what the system is
actually for. That said, the unauthenticated route surface and the missing dependency manifest
are real, concrete, fixable gaps regardless of deployment context.
