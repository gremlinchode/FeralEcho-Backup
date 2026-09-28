# TASK_TYPE_MAP Synchronization — Ground Truth → Minimal Invariant → Adversarial Qualification

Append-only investigation journal. Mission: independently establish whether the
`TASK_TYPE_MAP` "silent divergence" claim referenced by three prior missions
today is real ground truth, and whether a `task_type_map_sync` Liveness Ledger
invariant is the correct, sufficient, and actually-authoritative fix — not
assumed correct going in.

## Stage 0 — Integrity and provenance

Recorded before any substantive work:

- Opening Git HEAD: `2fba42644c82b9f7096276f4dd338d615cf1bcce`
- Opening `git status --short --untracked-files=all`: **231 paths** (modified +
  untracked). This is pre-existing, extensive, real concurrent work from other
  missions earlier today (E5-mini repair chain, Python capability audit,
  evaluator qualification, recursive learning investigation). None of it will
  be touched by this mission.
- Live processes, read-only inspection only:
  - `run.py` — PID 7644, running since Thursday 10PM, 1260:29 CPU time. **Not
    touched.**
  - `ollama serve` — PID 13534, running since Sep 2. **Not touched.**
  - No `llama-server` process observed at this check (may be intermittent;
    not relevant to this mission).
- Python: 3.12.13 (system-level check; FeralEcho's actual conda env not
  separately re-verified here since this mission does no environment work).

No production code, memory, model state, or Git history will be mutated
except the one new report file and (only if Stages 1-6 justify it) one
small, isolated addition to `liveness_ledger.py`.

---

## Stage 1 — Independent archaeology

Searched the repository independently — not starting from the proposed
`task_type_map_sync` design — for every representation of task-type
semantics. Full-repo `grep -rn "TASK_TYPE_MAP"` (excluding `__pycache__`)
found exactly two real, live *definitions*, everything else is either a
comment, a research script reading source text, or a dead worktree copy.

| Representation | Location | Definition location | Live? | Consumers | Authoritative / derived / duplicated / descriptive |
|---|---|---|---|---|---|
| Canonical map | `app/core/echo_model_orchestrator.py:717` | Module-level dict literal, 7 keys: `{"general":0,"coding":1,"creative":2,"personal":3,"reasoning":4,"self_edit_coding":5,"echo_projects_coding":6}` | Yes, imported by `run.py`'s call chain | `RiverBrain._init_classifiers()` (`for task_type in TASK_TYPE_MAP.keys()`, line 786 — the real source of "which task types exist" for classifier/scaler initialization); imported into `echo_model_orchestrator.py`'s own namespace and read at `learn()`/`score_model()`/etc. call sites (guarded with `if task_type not in self.classifiers: task_type = "general"` at each) | **Authoritative** — this is the actual enumeration RiverBrain initializes against. |
| Local copy | `echo_quality_scorer.py:495` | **Function-local**, not a module attribute — declared inside `_extract_quality_features_v2()`'s own body, re-created fresh on every call. Currently identical values to the canonical map. | Yes, called from `echo_model_orchestrator.py:61` (`from echo_quality_scorer import ... _extract_quality_features_v2 as _extract_quality_features`) and from `functional_quality.py`/`echo_optuna.py`/`self_model_updater.py`/`self_edit_manager.py`/`emergent_scheduler.py` (all confirmed via grep) | Feeds `task_type_id`, one feature in the vector `_extract_quality_features_v2()` returns, which flows into RiverBrain's quality scoring (an input to the row 1 authoritative mechanism above) | **Duplicated**, by explicit, stated intent (its own comment: "Kept in sync with echo_model_orchestrator.py's TASK_TYPE_MAP"), not by naming-coincidence inference. |
| `liveness_ledger.py:1680` (pre-existing) | Comment only, in `self_model_claims_integrity`'s check docstring | Not a definition | — | — | Descriptive — references "the identical CATEGORIES/TASK_TYPE_MAP failure shape" as a named precedent for a *different* mechanism's own design caution. Confirms this failure class was already treated as a known, citable pattern by an earlier 2026-09-08 session, independent of this mission. |
| `self_model_claims.py:70` (pre-existing) | Comment only | Not a definition | — | — | Same, descriptive citation of the pattern. |
| `claude_relay/relay.py`, `README.md`, `from_m5.md` | Prose mailbox entries, 2026-09-09/10 | Not definitions | — | — | **First-party, dated evidence of a second, structurally different divergence axis** — see Stage 5. |
| `audits/recursive_learning_ground_truth/{accumulation,probe,followup}.py` | `ast.literal_eval()` extraction of the canonical map's source text | Read-only, research tooling | N/A (not live/imported by `run.py`) | — | Descriptive/read-only; not a third live copy. |
| `.claude/worktrees/agent-abe6ecca0408fd0fb/{echo_quality_scorer.py, app/core/echo_model_orchestrator.py}` | A separate git worktree, branch `worktree-agent-abe6ecca0408fd0fb`, HEAD `a23b940`, confirmed via `git worktree list` | Stale: orchestrator copy has 6 keys (missing `echo_projects_coding`), scorer copy has 5 keys (missing `self_edit_coding` and `echo_projects_coding`) | **No** — not on `main`, not importable by `run.py`, a dormant agent scratch worktree | — | A real, third, currently-inert divergence instance. Not operationally relevant (nothing imports it), but worth naming: it demonstrates the same duplication pattern can silently re-occur in *any* checkout of this pair of files, not just the two already tracked. |

**Dependency graph** (the two live nodes only, arrows = "reads/depends on"):

```
echo_model_orchestrator.TASK_TYPE_MAP (canonical, module-level)
        │
        ├─► RiverBrain._init_classifiers()  [enumerates task types that exist]
        ├─► RiverBrain.learn()/score_model()/learn_from_rating()/
        │   learn_from_council_rating()/observations_for()  [all guarded]
        │
        └── (no import edge to echo_quality_scorer.py's copy — see below)

echo_quality_scorer._extract_quality_features_v2()  [local TASK_TYPE_MAP,
        re-declared every call]
        │
        └─► task_type_id feature ─► RiverBrain.learn() (via
            echo_model_orchestrator.py's own import of
            _extract_quality_features_v2 as _extract_quality_features)
```

**Import-direction finding, load-bearing for Stage 6/9 below**:
`echo_model_orchestrator.py` already imports `_extract_quality_features_v2`
*from* `echo_quality_scorer.py` (line 61). `echo_quality_scorer.py` has no
import of `echo_model_orchestrator.py` anywhere (confirmed by grep — only a
comment reference). This is a one-directional dependency
(`orchestrator → scorer`), which matters for any future discussion of
eliminating the duplication via a shared import: a naive "scorer imports
the canonical map from the orchestrator" would create a genuine circular
import (the orchestrator already needs the scorer at its own import time).
The one live escape hatch — a third, dependency-free shared module both
files import from — was not built in this mission (out of scope per Stage
0's authorization, which permits only a `liveness_ledger.py` addition) but
is recorded here as a real, low-risk option for a future, separately-
authorized pass. Not attempted here.

Per the mission's own instruction not to infer "must match" from naming
similarity alone: this pair does not rest on inference — `echo_quality_scorer.py`'s
own in-repo comment explicitly states the two are intended to stay
identical, and both are read (never mutated) as a shared vocabulary for
"which task type is this," so divergence is dangerous, not legal, by the
system's own stated design.

---

## Stage 3 — Historical divergence: independently git-verified, not trusted from prior audits

Three prior artifacts, found during archaeology, all *claim* two real
historical divergence incidents:
- CLAUDE.md's Finding 35 (2026-07-17) and Finding 85 (2026-07-24)
- `audits/2026-09-07_temporal_authority_graph.md` (a prior session's own
  independent forensic pass, §7.2, found opportunistically during an
  unrelated authority-mapping mission)
- `claude_relay/from_m5.md`'s 2026-09-07 entry to Air, which describes the
  second incident as having "corrupted RiverBrain's real self_edit_coding
  training signal for 7 real days"

Per this mission's explicit discipline (do not treat any prior audit's
characterization as settled ground truth), every one of these claims was
re-derived directly from `git show`/`git log` in this session, not copied:

```
44e7a8e  2026-06-28  Initial commit. Canonical map already has
                     "reasoning":4 from day one. Scorer's copy has only
                     4 keys (general/coding/creative/personal) — no
                     "reasoning" at all. Confirmed via direct `git show
                     44e7a8e -- echo_quality_scorer.py`.
3e241862 2026-07-12  Scorer's copy gains "reasoning":4 — first fix.
                     Confirmed via `git show 3e241862`, date confirmed
                     via `git show -s --format="%ad"`.
                     --> Incident 1 window: 2026-06-28 to 2026-07-12,
                         14 real days, present since the very first
                         commit (not "canonical added it, scorer
                         missed it" — both should have matched from
                         day one and didn't).
47ccbcd  2026-07-16  "self_edit_coding":5 added to the CANONICAL map
                     ONLY. Confirmed via `git show 47ccbcd -- echo_quality_scorer.py`
                     returning nothing (scorer file untouched in this commit).
6d98e18  2026-07-23  "self_edit_coding":5 AND "echo_projects_coding":6
                     added to the scorer's copy in the same commit —
                     closing a gap that had existed since 47ccbcd.
                     --> Incident 2 window: 2026-07-16 to 2026-07-23,
                         7 real days, confirmed via commit dates
                         "Jul 16 20:32:30 2026" and "Jul 23 19:29:42 2026".
```

**Independent refinement beyond what the prior audit stated**: the prior
temporal-authority audit characterized Incident 1 only by "reasoning was
added at some point... and the scorer's copy is not updated" without
quantifying the window. Direct verification here found the real window is
**14 days**, and — more importantly — is a different *shape* than Incident
2: Incident 1 is "both copies started under-specified together and one was
fixed 14 days later," not "canonical gained a key first." Incident 2 is
the cleaner "new producer arrives, one consumer misses it" shape the
mission's own Stage 1 asked to distinguish. Both are real, both are
git-provable, and both independently confirm the mission's premise: this
divergence claim is not folklore, it is ground truth, confirmed by direct
commit inspection rather than inherited narrative.

**A third, currently-inert instance** exists in the dormant
`.claude/worktrees/agent-abe6ecca0408fd0fb` worktree (Stage 1 above) — not
counted as a third "incident" since nothing imports it, but it is live
proof the pattern is structural (recurs in any independent checkout of
this file pair), not a fluke specific to the two already-documented dates.

---

## Stage 4 — Impact assessment

During each incident's window, every real call to
`_extract_quality_features_v2(response, task_type=<missing key>, ...)`
executed `TASK_TYPE_MAP.get(task_type, 0)`, which returns `0` — the same
numeric feature value as a genuine `"general"`-task response — with **no
exception, no log line, no metric**. This silently misrepresented the
`task_type_id` feature RiverBrain trains on for every affected response
during the window:

- Incident 1 (14 days): every `reasoning`-task quality-scored response had
  its `task_type_id` feature silently recorded as `0` (general) instead of
  `4`.
- Incident 2 (7 days): every `self_edit_coding`-task quality-scored
  response — i.e., real self-edit candidate-generation scoring, per
  Finding 35's own stated purpose for adding this bucket in the first
  place ("giving RiverBrain a genuinely separate... bucket for self-edit's
  own code generation... deliberately not merged into 'coding'") — had its
  `task_type_id` silently recorded as `0` instead of `5`, defeating the
  exact separation Finding 35 was built to create, for the entire window.

This is a real, if narrow, instance of exactly the "phantom authority"
class of defect named repeatedly elsewhere in this session's own prior
missions: a mechanism (the `self_edit_coding` bucket) that was built,
deployed, and believed to be separating two skills, while one of its two
real inputs was silently feeding it misclassified data for 7 of its first
~9 days of life. **Magnitude honestly bounded, not overstated**: this
mission did not attempt to quantify how many real `self_edit_coding`- or
`reasoning`-scored responses actually occurred inside either window (that
would require a `git log`-timestamped replay against
`memory/interaction_log.jsonl`/`self_edit_reflections.log` history, which
is out of scope for this mission's read-only, non-destructive mandate and
was not attempted). The claim supported by direct evidence is *qualitative
and structural* (a real, silent, days-long feature-corruption window
occurred, twice, by this exact mechanism), not a quantified estimate of
how many training observations were actually corrupted.

---

## Stage 5 — The cross-machine divergence axis (structurally distinct, investigated separately)

Archaeology surfaced a second, real divergence — found by M5 "by accident"
on 2026-09-09 while checking an unrelated claim — that is **not** the
same failure as Stages 3-4 above: M5's fork of `TASK_TYPE_MAP` had 7 keys;
Air's fork (a separately-running FeralEcho instance on different
hardware, per `claude_relay/README.md`) had 4. This is fork/branch
divergence across two independently-operated repositories, not
duplicate-file divergence within one repository.

Per `claude_relay/facts_m5.jsonl` (a structured, append-only, dated fact
ledger — real, first-party evidence, not a narrative summary), the
*specific consequence* initially feared from this — that Air's fork might
be missing a guard against a `reasoning`-KeyError landmine in
`RiverBrain`'s functions — was **investigated directly and retracted**:
both forks were independently confirmed to already carry equivalent
protection (M5 via the 7-key map itself pre-populating
`self.classifiers["reasoning"]`; the specific function in question is
hardcoded-safe by construction rather than guarded). The retraction is
itself a real, disclosed instance of this project's own standing
discipline: a relayed, plausible-sounding risk claim was checked against
real source on both sides before being trusted, and turned out not to
hold. Status in the facts ledger: `"confirmed"` for the retraction.

**Relevant to this mission's central question**: a `task_type_map_sync`
Liveness Ledger check running inside M5's own process structurally cannot
observe Air's filesystem. It has no way to detect or prevent the 7-vs-4
cross-machine divergence, and was never proposed as a fix for it — the
temporal-authority audit's own recommendation (§14, item 2, quoted in full
in Stage 6) was scoped specifically to "detect a future TASK_TYPE_MAP
divergence the moment it happens," in the context of that same audit's own
intra-repository finding. Conflating the two axes would be a scope error;
this report keeps them separate throughout, and the check built in Stage 8
is explicitly scoped to the intra-repository axis only, with that scoping
stated directly in its own source comment.

---

## Stage 6 — Placement and authority analysis

The proposed placement (a Liveness Ledger check, evaluated on
`introspection_channel.py`'s existing ~120s collector cycle) is the
correct *category* of mechanism for this problem, for three independently-
checked reasons:

1. **It matches the failure's own shape.** The defect is "a fact silently
   stops being true and nothing observes it" — precisely the disease the
   Liveness Ledger module's own header comment says it exists to catch
   ("mechanisms that look wired because they report themselves as
   working, verified by nothing outside their own reporting").
2. **No existing mechanism already covers this.** Confirmed directly:
   `grep -rln "TASK_TYPE_MAP" scripts/verify_*.py` returns zero files
   (re-confirmed in this session, matching the prior audit's own finding).
   No pytest, no smoke test, no other liveness check reads either
   representation.
3. **The recommendation traces to a real, dated origin**, not an
   unsourced assumption: `audits/2026-09-07_temporal_authority_graph.md`
   §14 item 2, verbatim: *"Whether a cheap, purely-observational liveness
   check... could detect a future `TASK_TYPE_MAP` divergence the moment it
   happens, rather than waiting for an unrelated audit to stumble onto it
   7 days later a third time."* This is explicitly framed as a *proposed
   next question*, not a proposed fix — the prior session's own discipline
   already withheld judgment on whether to build it. This mission is the
   first to actually evaluate and act on that proposal.

**Whether it is *sufficient* is a separate question**, addressed in Stage
7 below — placement and design-category correctness do not by themselves
establish sufficiency.

---

## Stage 7 — Critiquing the proposed mechanism itself (adversarial, not confirmatory)

Before implementing anything, the most natural first design — "import both
`TASK_TYPE_MAP` objects and compare them for equality" — was **tried
directly against real source and found to be silently, permanently
broken**: `echo_quality_scorer.py`'s `TASK_TYPE_MAP` (line 495) is not a
module-level constant at all. It is declared **inside**
`_extract_quality_features_v2()`'s own function body, re-created fresh on
every call. `from echo_quality_scorer import TASK_TYPE_MAP` raises
`ImportError` unconditionally — confirmed by direct execution:

```
ImportError: cannot import name 'TASK_TYPE_MAP' from 'echo_quality_scorer'
```

Had this been shipped as designed, the check would have been **permanently
red from the moment it deployed** — failing closed on every single
introspection cycle, forever, regardless of whether the two representations
actually agreed. This is, precisely, "another mechanism that looks
authoritative" without being one: a liveness check that never actually
evaluates the real invariant it claims to guard, indistinguishable from a
genuine incident in its own output, and — per this project's own
repeatedly-stated concern about alert fatigue — actively worse than no
check at all, since a permanently-failing check trains anyone watching
`/admin/liveness-status` to stop trusting or checking it. **This was
caught during this mission's own construction, not glossed over or
discovered post-hoc** — the same discipline this whole session's earlier
missions (E5-mini's `checker.check_ledger()` never being called; the
"phantom authority" pattern found independently in two other subsystems)
already established as the single most important thing to watch for.

**The corrected design** (implemented in Stage 8) instead calls the real,
live `_extract_quality_features_v2()` once per canonical task type with a
trivial, side-effect-free synthetic input, and compares its real returned
`task_type_id` against the canonical map's value — a genuine *behavioral*
canary against the real function, not a source-text or import-based
check. This is strictly more robust: it is immune to the function-local
variable's scope entirely, and it tests the actual consequential
computation (the value RiverBrain would really receive) rather than a
structural proxy for it.

---

## Stage 8 — Implementation and verification

Built `_evaluate_task_type_map_sync()` (pure, testable) and
`_check_task_type_map_sync()` (the import/IO wrapper, fail-closed on any
import error) in `app/core/liveness_ledger.py`, registered as the 53rd
check (`task_type_map_sync`) in `_CHECKS` and the `runners` dict. Full
source-level rationale, including the Stage 7 finding, is preserved as an
in-file comment directly above the implementation (matching this
codebase's own established convention of recording *why*, not just *what*,
for every Liveness Ledger check).

Design specifics:
- Iterates the **canonical** map's keys only (one direction), reasoned
  explicitly in-source: `RiverBrain._init_classifiers()` treats the
  canonical map as the real authority on "which task types exist," and
  both real historical incidents were the canonical map gaining a key the
  scorer's copy didn't know about yet — never the reverse.
- Fails closed (returns `pass: False`) on: either import failing, the
  canonical map not being a non-empty dict, the scorer function raising
  for any task type, or any task type's returned `task_type_id` not
  matching the canonical value bit-for-bit (`!=` on `float(expected)`).
- Evidence text names the specific mismatched task type(s) and their
  actual-vs-expected values, not just "mismatch found" — verified this
  holds via a dedicated discrimination case (below) asserting the real
  historically-affected task type names appear in the failure evidence.

**Verified four ways, not assumed correct from reading the code alone:**

1. **Direct call against real, live, current source** (both files as they
   exist on `HEAD` right now): `pass: True`, all 7 task types agree —
   confirming both copies are currently in sync (expected — 6d98e18 closed
   the last known gap, over a month ago).
2. **7 new discrimination cases** added to
   `scripts/verify_liveness_ledger.py`, mirroring this codebase's
   established pattern (reconstruct the real historical fake, confirm it's
   flagged; reconstruct good data, confirm it passes): a reconstruction of
   the exact real 2026-07-16..07-23 incident (scorer missing
   `self_edit_coding`) correctly fails, with evidence naming both affected
   keys; a raising-function case; both-inputs-`None`; an empty-dict
   canonical map (fails closed rather than vacuously passing); and the
   real function called against real current source (passes). **All 7
   pass**, plus the full pre-existing 100+-case suite remains clean — zero
   regressions (`scripts/verify_liveness_ledger.py` exits 0).
3. **Full `run_liveness_checks()` invocation** against the real, live
   codebase (with the same `KMP_DUPLICATE_LIB_OK`/`OMP_NUM_THREADS`
   environment guard `run.py` itself sets before any native import, per
   CLAUDE.md's own documented startup requirement): `task_type_map_sync`
   correctly appears among 53 total checks, reports `pass: True` with
   accurate evidence, and is not among the (single, pre-existing,
   unrelated — `self_model_drift`, expected outside the real server
   process per this project's own established precedent for that specific
   check) failing checks.
4. **Syntax-checked** (`ast.parse`) after every edit to
   `liveness_ledger.py` and `scripts/verify_liveness_ledger.py`.

No other production file was modified. `echo_model_orchestrator.py` and
`echo_quality_scorer.py` — the two files that actually contain the
duplication — were read but not touched, consistent with Stage 0's
authorization (only `liveness_ledger.py`, plus this report).

---

## Stage 9 — Adversarial (hostile) self-qualification

Attempting to falsify the check just built, rather than defend it:

- **Could this check itself silently degrade into a phantom, the same way
  the first draft did?** The Stage 7 failure mode (a broken import) is
  specifically what the "both inputs `None`" and "canonical map not
  importable" discrimination cases exist to catch — if a future refactor
  ever renames `_extract_quality_features_v2` or moves `TASK_TYPE_MAP`
  again, the check fails closed and loudly, rather than silently always-passing.
  Verified: forcing `feature_fn=None` produces `pass: False` with an
  explicit "failing closed" evidence string, not a silent skip.
- **Could it be gamed by a shortcut that makes the function *return* the
  right value without actually using the real map?** E.g., a future
  refactor of `_extract_quality_features_v2()` could hardcode
  `task_type_id` per-call to whatever value happens to match, without any
  real dict backing it. This is a real, if narrow, residual gap — the
  check verifies *behavioral output equivalence*, not that the underlying
  implementation is structurally a synchronized dict. Judged acceptable:
  the actual harm this whole mission is about (silently wrong `task_type_id`
  values reaching RiverBrain) is fully prevented either way — if the
  function's output is correct, the real consequence this check protects
  against cannot occur, regardless of *how* the function produces that
  correct output internally.
- **Does it cover a divergence in the opposite direction** (scorer gaining
  a key the canonical map doesn't have)? No — explicitly, by design (Stage
  8). This is a real, disclosed scope limit, not an oversight: no
  historical incident of this shape was found, and `RiverBrain`'s own
  classifier initialization treats the canonical map, not the scorer's
  copy, as authoritative for "which task types exist" at all — a
  scorer-only key would be inert on the RiverBrain side regardless (it
  would never reach `_init_classifiers()`), so this direction has no
  known consequential failure mode to protect against. If one is ever
  found, the check's own one-directional iteration would need widening —
  flagged here rather than silently assumed sufficient forever.
- **Does building this check repair the reward→consumer wire, integrate
  `river.bandit`, redesign RiverBrain, modify task classification
  semantics, repair `_ast_complexity()`, modify E5-mini, or touch any
  other explicitly out-of-scope item from this mission's own non-goals?**
  No — confirmed directly: the only files touched are
  `app/core/liveness_ledger.py` and `scripts/verify_liveness_ledger.py`,
  both explicitly liveness-ledger-adjacent tooling, and no other module's
  behavior changed (verified via the full discrimination suite's zero
  regressions across every other check).
- **Trying to defeat my own earlier conclusion from Stage 6**: is a
  Liveness Ledger check actually the *best* place for this, or merely *a*
  valid place? The genuinely superior fix — eliminating the duplication at
  its root via a third, dependency-free shared module both files import
  from (Stage 1's dependency-graph finding shows this is possible without
  a circular import) — was deliberately **not** built in this mission,
  because it exceeds Stage 0's stated mutation authorization (limited to
  one `liveness_ledger.py` addition) and because `echo_model_orchestrator.py`
  is an `EDIT_FORBIDDEN_TARGETS`/human-edit-with-diff-shown file by this
  project's own established precedent — not something to modify inside an
  autonomous forked mission without that separate confirmation step. This
  is the honest, load-bearing limitation of this mission's output: **the
  check built here is real, correct, and non-phantom, but it is a
  detection mechanism, not a cure.** The underlying duplication — the
  actual root cause that has already produced two real incidents — still
  exists on disk, unchanged, after this mission.

---

## Stage 12 — Final verdict

**Claim reconciliation**: the "TASK_TYPE_MAP silent divergence" premise
referenced by three prior missions today is **real, ground-truth-confirmed,
independently re-derived from `git show` in this session** (not merely
re-asserted from a prior audit) — two genuine incidents, 14 and 7 real
days respectively, both silently corrupting a real RiverBrain training
feature with zero exception, log line, or test coverage, plus a third,
currently-inert instance in a dormant worktree proving the pattern is
structural. A separate, structurally distinct cross-machine divergence
axis also exists (Stage 5), real but out of scope for any single-process
liveness check by construction, and its own specific feared consequence
was independently investigated and retracted by a prior session — recorded
here, not re-litigated.

**Stopping condition: A (QUALIFIED), with an explicit, load-bearing
amendment, not a clean pass.** `task_type_map_sync` now exists, is
correctly placed, is genuinely behavioral (a functional canary against the
real live function, not a source-text or import-based proxy — the
original, more obvious design was tried, found to be a would-be permanent
phantom check, and replaced before being trusted), is verified via 7 new
discrimination cases reconstructing the real historical incident plus a
live run against real current source, and introduces zero regressions
across 100+ pre-existing discrimination cases. It provides genuine,
non-phantom, immediate (next ~120s collector cycle) detection of a
recurrence of exactly the failure that has already happened twice.

It is **not, by itself, a complete fix**, and this report does not
overstate it as one: the root cause (two independently-maintained
representations of the same fact, one of them a function-local variable
with no shared source of truth) still exists in the codebase after this
mission. The check converts "silently wrong for up to 14 days, discovered
only by accident" into "flagged within minutes, requiring a human or a
future session to act on the alert" — a real, substantial improvement, but
still a monitor, not a cure. The genuinely superior fix — extracting
`TASK_TYPE_MAP` into one shared, dependency-free module both files import,
which Stage 1's dependency-graph analysis confirms is structurally
possible without a circular import — was deliberately not attempted here,
both because it exceeds this mission's own stated mutation authorization
and because it would touch an `EDIT_FORBIDDEN_TARGETS`-precedent file
without the separate, explicit confirmation step that precedent requires.

**Answering the mission's own closing question directly**: *does
`task_type_map_sync` now provide real protection against a demonstrated
FeralEcho integrity failure, or have we merely created another mechanism
that looks authoritative?* — **Real protection, but partial, and honestly
scoped.** It is not phantom (it was directly tested against the exact
historical failure shape and correctly flagged it; it fails closed on
every input-unavailability case tried; it survived an adversarial attempt
to defeat its own design in Stage 9). It is not the whole fix (the
duplication that caused both real incidents is still physically present in
the source, and a future edit to *both* copies in a way that happens to
produce matching `task_type_id` output — however unlikely — would still
pass this check without actually eliminating the underlying architectural
risk). The honest, complete answer is: this mission leaves FeralEcho
strictly better off than it found it — a real, verified, zero-regression
detector now exists where none did — while explicitly flagging, rather
than silently completing, the separate, larger structural fix a future,
separately-authorized session should consider.

**Recommended next step, not attempted here per this mission's own
scope**: a small, isolated pass extracting `TASK_TYPE_MAP` into a
dependency-free shared module (e.g. a new `app/core/task_types.py`) that
both `echo_model_orchestrator.py` and `echo_quality_scorer.py` import from
— confirmed safe from a circular-import standpoint (Stage 1) and from a
mutation-safety standpoint (neither current copy is ever mutated at
runtime, confirmed via a full-repo grep for `TASK_TYPE_MAP[` /
`.update(`/`.pop(`/`.setdefault(` against both files, all empty) — which
would make this exact divergence structurally impossible rather than
merely detected, with `task_type_map_sync` kept in place afterward as a
permanent regression guard against any future third copy.
