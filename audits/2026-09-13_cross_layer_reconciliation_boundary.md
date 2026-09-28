# Cross-Layer Provenance Reconciliation — Boundary & Epistemology

**Date:** 2026-09-13
**Type:** Architecture / epistemology / red-team-boundary research only. No reconciliation engine implemented. No production file modified. No commit/stage/Git mutation. PID 7644 read-only-inspected only (`ps`), never signaled/attached/instrumented.
**Method:** this mission is primarily a synthesis pass over evidence this session's own prior three missions already established empirically (Layer 1 implementation + red-team, Layer 2 implementation + red-team, Layer 3 feasibility investigation with five real experiments) — re-derivation was avoided where a fact was already settled; two new, narrow, decisive checks were run where a genuinely new question arose (see §6, §7).

---

## 1. Executive conclusion

**The correct architecture is deliberately conservative and leaves certain questions unresolved — this is the successful result, not a shortfall.**

No reconciliation algorithm can manufacture proof of module loading or execution from Layer 1 + Layer 2 evidence alone, because neither layer's schema contains a single field connecting a file path to a process (established in the Layer 3 report, re-confirmed here by direct schema inspection, §11). What reconciliation *can* legitimately do is narrower and still genuinely useful: compare independently-sourced facts, expose agreement and disagreement without collapsing either into a verdict, and — critically — refuse to let internal self-consistency, or agreement between two facts that share one underlying producer, be mistaken for independent triangulation. The strongest currently-defensible cross-layer conclusion is a conjunction of narrow, individually-true statements about file identity and process identity (§11); the strongest conclusion the system must refuse to make is any statement connecting those two domains to a code-loading or execution claim (§17).

---

## 2. Current Layer 1 capabilities

`working_tree_file_identity(path)` (commit `6e835bf`): regular-file existence, Git-index tracking of the literal queried path, current raw-byte SHA-256, HEAD blob SHA-256 for the literal path, and whether the two hashes differ — all for one path, at one point in time. Two independently-confined branches (filesystem-resolved vs. lexically-normalized-for-Git) prevent a symlink from silently substituting one Git object's identity for another (the 2026-09-13 red-team-then-fix in this session's own history). No field anywhere references a process, a module, or code execution.

## 3. Current Layer 2 capabilities

`runtime_process_identity_and_self_report(pid)` (commit `e03f598`): three structurally separate blocks — `external_process` (genuine OS observation via `psutil`: exists, create_time, cmdline, executable, cwd, status), `runtime_self_report` (literal contents of `memory/echo_server.pid` and `memory/echo_sentinel.json`, read verbatim, allowlist-filtered), and `correlation` (factual agreement comparisons only — `pid_match_*`, `start_time_match_sentinel`, the raw delta). No field anywhere references a module or code execution. The Layer 2 red-team (`audits/2026-09-13_provenance_layer2_red_team.md`) is the direct predecessor of this mission's §13 consumer-safety analysis — its two MODERATE findings are the concrete, already-proven instance of the exact hazard this mission is asked to generalize.

## 4. Layer 3 established limitation

`audits/2026-09-13_layer3_runtime_provenance_boundary.md`, conclusion `MORE RESEARCH REQUIRED`. Empirically demonstrated (not merely argued): a module's resident, executing code and the current on-disk content of the file it came from can diverge completely, with nothing in the current architecture able to detect the divergence (the file-mutation-after-load experiment). Also established: `sys.modules` is unobservable externally; `__code__.co_code` alone is insufficient for code-identity comparison (misses constant-only changes — `marshal.dumps()` is required); native-library observation via `lsof` is real but answers a different, narrower question (which compiled dependencies are mapped, not which FeralEcho `.py` module is loaded). No Layer 3 primitive exists to reconcile against yet — this mission's design must hold correctly with **zero** Layer 3 evidence available, not merely "should also work if Layer 3 existed."

---

## 5. Evidence model

Tested against the mission's own candidate dimension list by asking, for each, "does a real scenario from this session's own history actually require it, or does it just sound thorough":

| Dimension | Necessary? | Why |
|---|---|---|
| **Subject** (what fact is this about — a path, a PID, a module name) | **Yes** | Without this, two facts about *different* subjects could be silently compared as if about the same one — exactly Layer 2's own pre-fix symlink defect, one layer up |
| **Source/producer** (which function/mechanism produced this fact) | **Yes** | Required to compute independence (§6) — two facts from the same producer are not two witnesses |
| **Observation time** (when was this specific fact gathered, wall-clock) | **Yes — and currently ABSENT from both shipped layers**, confirmed by direct grep of `provenance_check.py`: no field named `observation_time`/`observed_at`/`queried_at` exists anywhere in either schema. Layer 1's `mtime` and Layer 2's `create_time_utc`/`start_utc`/`last_heartbeat_utc` are all **subject** timestamps (when did the *file* change, when did the *process* start), never a **query** timestamp (when did *we* look). A caller who persists a returned dict without independently recording call time has already lost the evidence's own temporal anchor. This is a real, previously-unstated gap this mission surfaces new evidence for — not something Layer 1/2's existing red-teams were asked to check, since neither mission's scope was cross-call temporal reasoning. |
| **Independence class** (independent / self-reported / derived / heuristic) | **Yes** | Already used informally throughout Layer 2 and Layer 3's own reports; reconciliation is the first layer that actually needs to *compute* with this dimension rather than just label prose with it |
| **Epistemic status** (what this fact alone supports — see §9) | **Yes** | The entire point of the exercise |
| **Limitations** (free-text, what this fact does NOT establish) | **Yes, but only as a fixed enum reference, not free text** — free-text limitations are exactly how Layer 1/2's own extensive docstrings already communicate this, and duplicating that prose into every evidence *instance* would be redundant; a reconciliation-time fact should carry a reference to which documented limitation applies, not restate it |
| **Confidence score (numeric)** | **No — rejected explicitly** | Nothing in this entire research corpus's three prior missions ever produced or needed a numeric confidence value; every finding was expressed as a bounded categorical fact (`True`/`False`/`None`/a named conflict) precisely because a number invites false precision Layer 1/2's own design explicitly avoids (`in_scope`, never `confidence: 0.87`) |
| **Dependencies** (which other evidence items this one presupposes or was derived from) | **Yes, for derived/correlation facts only** — raw evidence (a hash, a PID) has no dependency; `correlation.pid_match_sentinel` inherently depends on both `external_process.exists`-adjacent data and `runtime_self_report.sentinel_file.pid` — this dependency is currently implicit (a reader must know the code) and reconciliation is exactly the layer that should make it explicit |
| **Process identity anchor** (which process/PID this fact concerns, if any) | **Partially — only for Layer 2/3-domain facts** | A Layer 1 fact (file identity) has no process anchor by design; forcing one onto it would be exactly the kind of premature cross-domain merge §11 warns against |
| **Artifact identity anchor** (which file/path this fact concerns, if any) | **Partially — only for Layer 1-domain facts** | Symmetric to the above |

**Minimal defensible model, stated positively**: `{subject, producer, observation_time, independence_class, value_or_state, limitation_ref, dependencies}`. Everything else considered and rejected above (numeric confidence, embedded free-text limitations) was rejected for a stated, evidence-grounded reason, not omitted by default.

---

## 6. Evidence independence/dependence model

**Scenario F, tested against real code, not assumed.** `memory/echo_server.pid`'s PID and `memory/echo_sentinel.json`'s PID are written by two textually separate `os.getpid()` calls (`run.py:1577` and `run.py:1119`, the latter inside `_write_sentinel()`), at different points in the same startup sequence (`_SERVER_PID_FILE.write_text()` runs first, then `start_background_threads()` internally calls `_write_sentinel("threads_starting")`, then `_write_sentinel("serving")` runs again after). **These are not independent evidence sources for triangulation purposes**, even though they are two different function calls, two different files, and two different lines of code: both derive from the *same process's own, trivially-always-self-consistent* belief about its own PID (`os.getpid()` cannot lie to itself; it is a syscall wrapper reading kernel state that is definitionally correct for the calling process). The real risk this dependence creates is not "os.getpid() might return different values" — it's that **the two files can fall out of sync with each other over time** if one gets overwritten by a later process instance (a restart) while the other doesn't (exactly Layer 2 red-team's disclosed shutdown-asymmetry finding: `echo_server.pid` is `unlink`'d on clean shutdown, `echo_sentinel.json` never is).

**General rule derived from this, applicable beyond this one pair**: two evidence items share a *dependence group* if they are ultimately grounded in the same underlying fact-source (here: "what does this process believe its own PID is"), regardless of how many separate code paths or files carry that belief forward. Agreement within a dependence group proves internal consistency, not truth — `external_process.exists` (genuinely independent — a separate observer, `psutil`, querying the OS's own process table) is the *only* fact in Layer 2's current schema that belongs to a different dependence group than the self-report pair. This means Layer 2's real triangulation strength today is **one independent witness against one (internally-consistent-but-dependent) self-report pair** — not "three independent confirmations" merely because there are three PID-shaped fields in the output.

---

## 7. Temporal/freshness model

Building on §5's finding (no observation-time field exists today):

- **Subject timestamps** (file `mtime`, process `create_time`, self-report `start_utc`/`last_heartbeat_utc`) describe *when the thing itself changed*, independent of when anyone looked.
- **Observation timestamps** (currently absent) would describe *when the evidence-gathering code ran*.
- A composed call like `runtime_process_identity_and_self_report()` performs its sub-observations **sequentially, not atomically** — `_external_process_observation()`, then `_read_server_pid_file()`, then `_read_sentinel_file()`, confirmed by direct source order in `provenance_check.py`. Real wall-clock time elapses between them (measured in this session's own live tests as sub-millisecond in practice, but architecturally unbounded — a slow filesystem, GC pause, or OS scheduling delay could widen this). **Two facts returned by the same function call must never be treated as simultaneous observations** — they are observations made moments apart, in a fixed order, and the order itself is a real (if usually negligible) source of skew.

**Minimum defensible temporal semantics for a future reconciliation layer**: every evidence item must carry its own observation timestamp, captured at the moment that specific sub-observation was made (not once for the whole composed call); reconciliation comparing two items must compute and expose their observation-time delta, the same way `correlation.start_time_delta_seconds` already discloses a *subject*-time delta today; and reconciliation must never claim two facts are "as of the same moment" without that delta being small and explicit.

---

## 8. Conflict model

Four real conflict shapes, drawn directly from this session's own prior red-teams plus the mission's own examples, with the vocabulary each actually requires:

1. **Direct value disagreement** (Git hash A vs. filesystem hash B) — Layer 1 already has this exact shape (`modified_vs_head`), and already gets it right: both raw facts (`sha256`, `head_blob_sha256_or_none`) are preserved in the output; the comparison is a *third*, separate field, never a replacement for either side.
2. **Existence disagreement** (`external_process.exists = false` vs. self-report implying `true`) — already produced, unmodified, by Layer 2 today (Layer 2 red-team's Finding 1, Case A). The correct representation, already in place: both raw facts stay visible; no field anywhere asserts a merged "exists" verdict.
3. **Partial-match disagreement** (`pid_match_sentinel = true`, `start_time_match_sentinel = false`) — already produced by Layer 2 (red-team Finding 2). This is the conflict shape most likely to be *misread* as agreement if a consumer only checks one of the two fields (§13).
4. **Cross-domain non-comparability** (`runtime reports module path A` vs. `filesystem currently contains path B`) — this shape **does not exist yet anywhere in the shipped architecture**, because no self-report of a module path exists (Layer 3's finding). Recorded here as the conflict shape a future Layer 3 would need to produce correctly, not one reconciliation can currently exercise.

**Minimum useful conflict vocabulary, derived from what the four real shapes above actually needed** — not invented in the abstract:
```
AGREE       -- both sources report the same value for the same subject
DISAGREE    -- both sources report values for the same subject, and they differ
ONE_SIDED   -- one source has a value, the other has no evidence at all (None)
NEITHER     -- neither source has a value
```
Each of these is a *relationship* between two named facts, never a replacement for either fact — matching exactly what `_compose_correlation()` already does structurally (its four output fields are all relationship facts; the two raw facts they're computed from remain separately visible one level up in the returned dict).

---

## 9. Unknown/undetermined model

Four states, tested for whether each is genuinely distinct or collapses into another, using real examples from this session:

- **`UNKNOWN`** — evidence was sought and the mechanism could not produce a value (e.g., `_git_tracked()` returning `None` when git itself is unavailable — real, tested, Layer 1's Case 10). Distinct from:
- **`FALSE`** — evidence was sought, the mechanism succeeded, and the answer is negative (e.g., `tracked: False` for a genuinely untracked file — a real, positive, successful determination of absence). Layer 1's entire "unknown ≠ false" discipline is precisely the boundary between these two, and both Layer 1's and Layer 2's red-teams spent real effort proving no code path silently converts the first into the second.
- **`CONFLICTING`** — two sources both produced values, and they disagree (§8's `DISAGREE`). This is not the same as `UNKNOWN`: conflicting evidence is *more* informative than no evidence at all (it tells you something real is inconsistent), and collapsing it into `UNKNOWN` would discard that.
- **`UNSUPPORTED_BY_AVAILABLE_EVIDENCE`** — the question asked is one no *currently implemented* mechanism can answer at all (e.g., "is module X loaded in PID 7644" — Layer 3's own central finding). This is categorically different from `UNKNOWN`: `UNKNOWN` means "the mechanism ran and came back empty"; this state means "no mechanism exists to run in the first place." Collapsing these would hide the difference between a Layer 2 self-report file that happens to be missing today (`UNKNOWN`, recoverable by a future observation) and a fact no primitive in the current architecture can ever produce without new code (`UNSUPPORTED_BY_AVAILABLE_EVIDENCE`, not recoverable without building something new).

All four are genuinely distinct, evidenced by four different real code paths across this session's own three prior missions — none of the four collapses cleanly into another without losing real information a consumer would need.

---

## 10. Candidate reconciliation architecture

Not designed as a full engine (explicitly out of scope) — only its required *shape*, derived from §5–§9:

A reconciliation function should be a **pure, read-only comparison over already-gathered evidence** (mirroring Layer 1's `_compose_identity()` and Layer 2's `_compose_correlation()` — both already zero-I/O, directly testable against synthetic inputs, a pattern this whole corpus has independently arrived at three times now, worth treating as an established convention rather than a coincidence). Its input is a set of evidence items shaped per §5's model; its output is a set of §8-vocabulary relationship facts plus §9-vocabulary state labels — **never** a single merged verdict. It must refuse to compare two evidence items without knowing their §6 dependence-group membership (comparing two same-group items should be labeled differently — e.g. `CONSISTENT_SELF_REPORT`, not `AGREE` — from comparing two genuinely independent items, since the epistemic weight is not the same). It must carry each compared item's own §7 observation timestamp and expose the delta, never assert simultaneity. **No part of this shape requires Layer 3 to exist** — it is fully specifiable and (later) buildable against Layer 1 + Layer 2 alone; Layer 3 evidence, whenever it exists, would enter through the identical shape, not a special case.

---

## 11. Strongest conclusions currently possible

Concrete, drawn from real, already-observed data in this session (not hypothetical):

1. *"`app/core/provenance_check.py` at HEAD `e03f598` is tracked, and its current working-tree bytes match HEAD's blob exactly."* — a real Layer 1 fact, directly checkable right now.
2. *"A process with PID 7644 currently exists, with OS-recorded creation time `2026-09-11T05:41:53.357916 UTC`."* — a real Layer 2 `external_process` fact, independently corroborated a third way this session via `vmmap`'s `Launch Time` field (Layer 3 report §5, §7).
3. *"The self-report files `memory/echo_server.pid` and `memory/echo_sentinel.json` both claim PID 7644, and the sentinel's `start_utc` is within 4.43 seconds of the externally-observed creation time."* — a real Layer 2 `correlation` fact, live-tested.
4. *"Facts 2 and 3 agree with each other."* — the strongest defensible **conjunction**: one independent observation (fact 2) and one internally-dependent self-report pair (fact 3, per §6) agree on PID and approximate start time. This is real, non-trivial corroboration — it is meaningfully stronger than either fact alone, because it shows the self-report is not simply stale or fabricated relative to the one independent check available.

**Immediately, explicitly appended, per the mission's own required framing**: *"This does not establish that any specific FeralEcho module is loaded in this process, that any function has executed, or that the code currently resident in memory matches the file described in Fact 1."* This is not a hedge — it is the literal, demonstrated truth: Layer 3's own mutation experiment proves fact 1's currency says nothing about what a *different* already-running process loaded before the file last changed.

---

## 12. Conclusions that remain impossible

Restated precisely from the Layer 3 report, not re-derived: whether any named module is in PID 7644's `sys.modules`; whether any function has been called, is being called, or was called recently; whether the code currently resident in memory matches current disk content (without new, not-yet-built, in-process self-report code); whether two files sharing a module name in different `sys.path` locations resolve to the one a live process actually loaded (§14 of the Layer 3 report, empirically demonstrated this session).

---

## 13. Consumer-safety analysis

The Layer 2 red-team already found the concrete instance of this hazard (`pid_match_sentinel: true` alongside `external_process.exists: false`). Evaluated against the mission's own candidate mechanisms, using "does this actually stop the specific, already-demonstrated misreading" as the test, not "does this sound rigorous":

| Mechanism | Would it have prevented the actual Layer 2 red-team finding? | Cost |
|---|---|---|
| Structured evidence objects (typed, not bare dicts) | **No, by itself** — a consumer can still read one field off a typed object just as easily as off a dict; typing prevents a *different* class of bug (wrong-type access), not selective reading | Real implementation cost, no proven benefit for this specific hazard |
| Explicit dependency relationships (§6) attached to each fact | **Partially** — surfaces *that* `pid_match_sentinel` depends on `external_process.exists` existing and being checked, but does not force a consumer to actually look | Low cost (a metadata field), real but partial benefit |
| Constrained conclusion APIs (a function that *requires* both facts as arguments before returning anything) | **Yes, directly** — if the only way to get a "does this look like the same process" answer is a function whose signature forces both `external_process` and `correlation` in as required arguments, cherry-picking one field becomes structurally harder, not just discouraged by documentation | Real design cost (a new function per composite question), but this is exactly what reconciliation-as-a-layer already implies — not new scope, just naming what §10 already requires |
| Provenance requirements (a consumer must declare which facts it used before a conclusion is accepted) | **Yes, in principle, but heavier than needed for the demonstrated hazard** — this is closer to an audit trail than a prevention mechanism |
| Typed states (§9's four-state enum instead of bare bool/None) | **Partially** — makes the *category* of a fact visually distinct from a plain `True`, nudging a reader to ask "what kind of true is this," but does not force cross-field reading either |
| Evidence bundles (grouping related facts so they can't be destructured apart) | **Yes, if the bundle is the only thing ever returned to a consumer** — this is functionally identical to "constrained conclusion APIs," just described as a data shape instead of a function signature |

**Smallest, strongest approach, per the mission's own request**: a **constrained reconciliation function**, not a data-modeling change to Layer 1/2 themselves (which stay exactly as they are — correctly narrow, evidence-only primitives). The function's signature itself becomes the safety mechanism: it must require the *full* relevant evidence bundle as input (not a single field), and its own output uses §9's typed states rather than a bare boolean, so a downstream consumer of *its* output inherits the same discipline one level up. This is smaller than typed evidence objects or a provenance-audit system, and it is the one mechanism in this table directly proven (by construction) to prevent the exact, already-demonstrated hazard rather than merely discourage it.

---

## 14. Epistemic arbitration implications

The mission's four candidate labels (`I KNOW`, `I HAVE EVIDENCE`, `I DON'T KNOW`, `THE EVIDENCE CONFLICTS`), tested against §9's four states and §11/§12's real examples:

- **"I know"** must never mean "multiple things agreed" (the mission's own explicit warning, and directly demonstrated as a real risk by §6: two agreeing self-report fields can be the *same* dependence group agreeing with itself). A defensible reading of "I know" would require at minimum one *independent* (§6) source, and even then only for the narrow, specific fact actually checked — never a composite claim (module loading, execution) no mechanism has ever verified.
- **"I have evidence"** is the honest description of nearly everything this architecture currently produces — a real, bounded fact, correctly scoped, never elevated further. This maps cleanly onto §11's four numbered conclusions.
- **"I don't know"** must distinguish §9's `UNKNOWN` (a mechanism ran, came back empty) from `UNSUPPORTED_BY_AVAILABLE_EVIDENCE` (no mechanism exists) — collapsing these, per §9's own analysis, would make "I don't know whether module X is loaded" (permanently true today, a structural fact about this architecture) indistinguishable from "I don't know whether this specific file exists" (transiently true, resolved by simply calling Layer 1 again). Echo's own future self-reports should be able to say *which* kind of not-knowing applies.
- **"The evidence conflicts"** maps directly onto §8's `DISAGREE` — already real, already produced today (Layer 2's PID-reuse scenario), and already correctly never auto-resolved in either direction by existing code.

**No numeric threshold is proposed or defensible** — consistent with §5's rejection of a confidence score, an epistemic-arbitration layer built on top of this evidence should reason in the same bounded, categorical terms the evidence itself is expressed in, not compress it into a single number that would itself become a new, unearned claim.

---

## 15. Adversarial scenario results

Each scenario addressed precisely — cited to real evidence where this session's own prior work already settled it; reasoned through where genuinely new (marked *reasoned*):

| # | Scenario | Result |
|---|---|---|
| A | File matches Git + process exists + self-report agrees + module may still not be loaded | **Confirmed structurally impossible to rule out** — `self_heal.py` (Layer 2/3 reports) satisfies exactly this conjunction while genuinely dormant |
| B | File changed after module load | **Empirically demonstrated** (Layer 3 §7 item 1) |
| C | Stale self-report, no live process | **Empirically demonstrated** (Layer 2 red-team Finding 1) |
| D | PID reuse, same PID, different start time | **Empirically demonstrated** (mocked; Layer 2 red-team Finding 2) |
| E | Self-report internally consistent but false | *Reasoned, this mission*: covered by §6 — internal consistency within a dependence group is not independent corroboration; a self-report can be perfectly self-consistent (PID matches across both files, timestamps line up) while still being stale or wrong relative to reality, exactly because both fields trace to the same source |
| F | Two evidence sources share the same underlying producer | **New finding this mission, real code cited** (§6) |
| G | Evidence observations occur at materially different times | **New finding this mission** (§7) — no observation-time field exists today; sub-observations within one composed call are sequential, not atomic |
| H | Module imported but function never called | *Reasoned*: directly covered by Layer 3's own execution-evidence ladder (§10 of that report) — "initialized" (top-level ran) does not imply anything about functions defined within it being called |
| I | Function called before source file changes | *Reasoned*: symmetric to J; no mechanism exists to timestamp a function call at all (Layer 3 §11), so this ordering question is unanswerable regardless of file-change timing |
| J | Source file changed while process remains alive | **Empirically demonstrated** (same experiment as B) |
| K | Source path and runtime path disagree | *Reasoned*: this is Layer 3's `__spec__.origin`-vs-Layer-1-resolved-path case (§14 of that report) — genuinely possible, currently only checkable in-process, unbuilt |
| L | Same module name in multiple locations | **Empirically demonstrated** (Layer 3 §7 item 3, the `shadow_mod` experiment) |
| M | Evidence source unavailable | **Extensively tested** (Layer 1 Case 10, Layer 2 red-team's `not_a_repo`/missing-file cases) |
| N | Evidence fields malformed | **Extensively tested** (Layer 2 red-team, 11 corruption shapes) |
| O | Evidence technically true but insufficient for the consumer's requested conclusion | **The central, already-demonstrated finding of this entire cross-layer investigation** — `pid_match_sentinel: true` is technically, completely true, and insufficient, alone, to answer "is this the same process" (Layer 2 red-team Finding 1/2); this mission's own §13 exists specifically to address this scenario architecturally |

No scenario required touching PID 7644 to evaluate — every one was either already settled by prior read-only experiments or answerable by reasoning from already-established, cited facts.

---

## 16. Candidate minimal reconciliation primitive/API

**Not implemented.** Specified per the mission's required shape, as the one concrete artifact this report proposes for a *future*, separately-authorized mission:

```
reconcile_process_and_selfreport(layer2_result: dict) -> dict
```

- **Inputs**: the full, unmodified output of `runtime_process_identity_and_self_report()` — deliberately the *whole* dict, never a caller-selected subset, per §13's own finding that a constrained signature is the one mechanism proven to prevent the demonstrated hazard.
- **Outputs**: a small set of §8/§9-vocabulary facts — e.g. `{process_identity_relationship: AGREE|DISAGREE|ONE_SIDED|NEITHER, dependence_note: "server_pid_file and sentinel_file share one producer (run.py's own os.getpid())", epistemic_state: I_HAVE_EVIDENCE|UNKNOWN|CONFLICTING}` — never a bare boolean, never a field named `verified`/`live`/`connected`.
- **Evidence dependencies**: `external_process.exists`, `correlation.pid_match_sentinel`, `correlation.start_time_match_sentinel` — all three required, matching §13's constrained-signature finding.
- **Possible states**: exactly the §8/§9 vocabulary already derived from real scenarios, not invented fresh for this primitive.
- **Failure modes**: an incomplete/malformed `layer2_result` (e.g., missing keys) must degrade to `epistemic_state: UNKNOWN`, never raise, matching Layer 1/2's own established discipline.
- **Attack surface**: none new — it is a pure function over already-gathered, already-red-teamed evidence; it makes no new OS calls, no new file reads, no new subprocess calls.
- **What it proves**: whether the three named Layer 2 facts are mutually consistent, and precisely how (agreement, disagreement, or insufficient evidence) — nothing about module loading or execution, since none of its inputs carry that information.
- **What it explicitly does NOT prove**: anything about Layer 1 (file identity) — composing Layer 1 into this same shape is a distinct, later, equally-scoped function, not folded in here to keep this primitive's dependence graph honest and minimal.

---

## 17. Anti-claims

The future reconciliation/arbitration system MUST NOT generate:

1. `verified_runtime = true` or any single boolean merging evidence streams — already forbidden by both prior missions, restated here as it applies one layer higher.
2. "Module X is loaded" or "code is executing" from any combination of Layer 1 + Layer 2 evidence — structurally impossible, no field bridges the two domains (§11, §12).
3. "I know" from two facts that share a dependence group (§6) — this must be labeled `CONSISTENT_SELF_REPORT` or equivalent, never conflated with genuine independent triangulation.
4. Any claim of simultaneity between two evidence items without an explicit, small observation-time delta attached (§7).
5. A collapse of `UNKNOWN` (mechanism ran, no answer) into `UNSUPPORTED_BY_AVAILABLE_EVIDENCE` (no mechanism exists) or vice versa (§9) — these must remain visibly distinct states.
6. A numeric confidence score of any kind, anywhere in the reconciliation output (§5, §14) — no evidence in this entire three-mission corpus was ever expressed this way, and introducing one here would manufacture false precision the underlying facts do not support.
7. A conflict represented by discarding either side and keeping only one value labeled `FALSE` (§8) — both `FACT A` and `FACT B` must always remain visible alongside the relationship between them.

---

## 18. Recommended next step

```
MORE RESEARCH REQUIRED
```

Not `IMPLEMENT`: while §16 specifies a genuinely small, safe, well-bounded candidate primitive, this mission's own instruction was explicitly to establish the reasoning boundary before writing code — and §7's finding (no observation-time field exists in either shipped layer today) is a real, load-bearing gap that a reconciliation primitive built *before* it's addressed would inherit silently. A future implementation mission should first resolve whether observation-time fields belong in Layer 1/2 themselves (a small, additive change to already-shipped, already-committed primitives) or are computed fresh by the reconciliation layer at call time (avoiding touching Layer 1/2 at all) — this is a real, undecided design choice this report deliberately leaves open rather than defaulting.

Not `NOT FEASIBLE AT THIS BOUNDARY`: §16's primitive is concretely specified and provably safe (no new attack surface, pure function over already-red-teamed evidence) — feasibility is not in question, sequencing is.

Not `BLOCKED`: nothing in this research was blocked by PID 7644's own constraints; every scenario was answerable read-only, and the two genuinely new findings (§6, §7) were confirmed by direct, safe source inspection.

---

## Integrity

```
Starting HEAD:  e03f5984bb86d36ade51ed8f0753a3b8264c0f9f
Ending HEAD:    e03f5984bb86d36ade51ed8f0753a3b8264c0f9f   (unchanged)
Files modified: none
Files created:  audits/2026-09-13_cross_layer_reconciliation_boundary.md (this file)
Staged:         nothing
Committed:      nothing
Pushed:         nothing
Scratch experiments: none required this mission beyond two read-only grep/source
                 checks against already-committed code (no new scratch files or
                 directories were created)
PID 7644:       unchanged throughout -- same start time (Thu Sep 10 22:41:53 2026)
                 confirmed via ps at mission start and end; never signaled,
                 attached to, or instrumented
```
