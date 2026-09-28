# Reconciliation Primitive — Implementation Design

**Date:** 2026-09-13
**Type:** Read-only implementation specification. No reconciliation function, class, schema, validator, decorator, or test created. No production file modified. PID 7644 inspected read-only only (`ps`).
**Authoritative baseline**: all five predecessor reports — `audits/2026-09-13_cross_layer_reconciliation_boundary.md`, `audits/2026-09-13_observation_time_contract_research.md`, `audits/2026-09-13_observation_time_placement_architecture.md`, `audits/2026-09-13_observation_time_enforcement_research.md`, `audits/2026-09-13_reconciliation_primitive_architecture.md`. This report does not reopen any epistemic question those five already settled — it converts the last one's architectural sketch into a concrete, buildable specification.

---

## Executive Conclusion

The primitive belongs in `app/core/provenance_check.py`, as a fourth section appended after Layer 2 (matching the module's own header comments, which already anticipate `reconcile()` as one of "the four primitives," confirmed present in source, not assumed). Function name: `reconcile_process_and_selfreport(layer2_result: dict) -> dict`. The specification below fixes every field name, every state-derivation rule, every dependence-group declaration, and every stop condition precisely enough that a later implementation mission needs to make no further semantic decisions — only write code matching this document. The one deliberately open area (future observation-time relationship semantics) is fixed as a **named, always-`UNKNOWN`-today placeholder** in the output schema, not left ambiguous, so a future schema extension is additive, never a breaking redesign.

---

## 1. Starting State

```
HEAD (verified fresh): e03f5984bb86d36ade51ed8f0753a3b8264c0f9f
git status --porcelain=v1 | wc -l: 108
```
Matches the exact end-state of the reconciliation-primitive-architecture report — no discrepancy. Same 19 pre-existing modified files present, unmodified. PID 7644 confirmed present, `Thu Sep 10 22:41:53 2026`, `ps` only. All five predecessor reports re-confirmed as the design baseline; none re-derived or reopened.

---

## 2. Implementation Home

Searched directly, this session: `app/core/provenance_check.py`'s own module map (traced by function/constant, not assumed) shows two existing sections — Layer 1 (`_find_project_root` through `working_tree_file_identity`) and Layer 2 (`_SERVER_PID_FILE_RELPATH` through `runtime_process_identity_and_self_report`) — and the module's own header comment, present in source today, already reads *"runtime_self_reported_module_origin(), or reconcile(). Those are..."*, naming `reconcile()` as an anticipated, not-yet-built third/fourth primitive in this exact file. **A repo-wide search for existing "reconcil"-named code found zero real hits** — one unrelated prose comment in `river_deliberation.py` (about council-opinion synthesis, unconnected to provenance), and the module's own two forward-looking comments in `provenance_check.py` itself. **No competing existing module claims this responsibility.**

**Decision: `app/core/provenance_check.py`, as a third top-level section**, immediately following Layer 2, mirroring the exact structural pattern already established twice in this same file (a module-level docstring section header, then pure helper functions, then a pure composition function, then the public entry point). **Justification**: avoids a new module for a single ~30-line pure function; keeps the file's own existing "LEAF PRIMITIVE N OF 4" numbering scheme internally consistent (this becomes the anticipated third primitive, distinct from the still-unbuilt `runtime_self_reported_module_origin()`); imports nothing new (the function's only "dependency" is the shape of the dict Layer 2 already produces, not a live import of Layer 2 itself — see §21). **A dedicated module is not justified** — the function has no state, no I/O, and no reason to be reachable independently of the file that already defines the evidence it reconciles.

---

## 3. Current Layer 2 Schema

Field-by-field, traced from source (`provenance_check.py:601-812`), not from report prose:

| Layer 2 field | Producer | Underlying witness | Semantic meaning | Dependence group |
|---|---|---|---|---|
| `pid` (top-level) | caller-supplied argument, echoed | N/A (input, not evidence) | The PID being queried | N/A |
| `external_process.exists` | `_external_process_observation()`, `psutil.Process(pid)` construction | **W1 (independent)** | Does an OS process with this PID currently exist | independent |
| `external_process.create_time_utc` | same function, `proc.create_time()` | **W1** | OS-recorded process creation instant | independent |
| `runtime_self_report.server_pid_file.pid` | `_read_server_pid_file()`, reading `memory/echo_server.pid` | **W2 (dependent)** | What the process wrote about its own PID at startup (`run.py:1577`, `os.getpid()`) | `process_self_report` group |
| `runtime_self_report.sentinel_file.pid` | `_read_sentinel_file()`, reading `memory/echo_sentinel.json` | **W3 (dependent)** | What the process wrote about its own PID, separately, inside `_write_sentinel()` (`run.py:1119`, a second `os.getpid()` call) | `process_self_report` group (same as W2) |
| `runtime_self_report.sentinel_file.start_utc` | same reader | **W3** | When Python's import machinery reached `run.py`'s `_SENTINEL_START = datetime.utcnow()` line — a proxy for, not identical to, process start | `process_self_report` group |
| `correlation.pid_match_server_file` / `pid_match_sentinel` / `start_time_match_sentinel` / `start_time_delta_seconds` | `_compose_correlation()`, already pure | **derived**, not a witness itself | Layer 2's own existing pairwise comparisons | N/A — these are themselves relationship-shaped facts the new primitive may re-express, not re-derive from scratch (§5) |

**Missing-field behavior, traced precisely**: every Layer 2 sub-field that could not be established is `None` (never a sentinel string, never `False` standing in for absence) — confirmed for `external_process` (each of the 5 per-field getters degrades independently, `provenance_check.py:626-648`), for `server_pid_file`/`sentinel_file` (each field defaults `None` in its base `result` dict before any read is attempted, `provenance_check.py:660-667`, `690-700`). **Malformed-field behavior**: `server_pid_file.malformed: True` for non-integer PID-file content; `sentinel_file.malformed: True` for invalid JSON or a non-object top-level value — both leave the corresponding value field(s) `None` rather than a best-effort guess. **No existing timestamp field describes observation time** — confirmed again, this session, by the same grep already run in the observation-time contract research: zero hits for `observed_at`/`captured_at`/`collected_at` anywhere in this file.

---

## 4. Witness Model

**Implementation-ready representation, fixed exactly** (not the architecture report's illustrative sketch, refined into buildable form):

```python
_WITNESS_INDEPENDENT = "os_process_observation"       # W1
_WITNESS_DEPENDENT_GROUP = "process_self_report"       # {W2, W3}
_WITNESS_MEMBERS = {
    _WITNESS_DEPENDENT_GROUP: ("server_pid_file", "sentinel_file"),
}
```
Represented in the output as a fixed, always-identical block (not computed per-call — this is architectural metadata about Layer 2's own producer structure, known a priori, exactly as the reconciliation-primitive-architecture report's §3 established):
```json
"witnesses": {
  "independent": ["os_process_observation"],
  "dependent_groups": {"process_self_report": ["server_pid_file", "sentinel_file"]}
}
```
**This block is identical on every call** — it describes the architecture, not the specific evidence instance — and is included in every output regardless of whether the underlying evidence was present, so a caller never has to separately look up "which witnesses does this system know about."

---

## 5. Relationship Contract

**Exact enum, fixed spelling** (Python `str` constants, not a formal `Enum` class — matching this codebase's own established convention, e.g. `provenance_check.py`'s `in_scope`/`error` string-code fields, never a class-based enum anywhere in Layer 1/2):
```python
RELATIONSHIP_AGREE = "AGREE"
RELATIONSHIP_DISAGREE = "DISAGREE"
RELATIONSHIP_ONE_SIDED = "ONE_SIDED"
RELATIONSHIP_NEITHER = "NEITHER"
```

**Operational definition, per relationship, for two compared values `a` (from witness X) and `b` (from witness Y)**:
```
if a is None and b is None:            NEITHER
elif a is None or b is None:            ONE_SIDED
elif a == b (or |a - b| <= tolerance):  AGREE
else:                                    DISAGREE
```
For PID comparisons: exact integer equality, no tolerance. For the start-time comparison: reuse Layer 2's own existing `_START_TIME_MATCH_TOLERANCE_SECONDS = 120` constant directly (imported/referenced, never re-declared with a new value — a second, drifted copy of this constant would be exactly the class of silent-vocabulary-fragmentation bug this project's own history, cited across the observation-time reports, has already found and fixed twice elsewhere). **Malformed-data handling**: a `malformed: True` sub-field (e.g. `sentinel_file.malformed`) causes the corresponding value to already be `None` at the Layer 2 level (§3) — reconciliation therefore does not need its own separate malformed-detection logic; it inherits Layer 2's own already-correct "malformed degrades to `None`, not a guess" behavior by construction, simply by reading the already-`None` field.

**Exactly five relationships computed on every call, fixed list, not caller-configurable**:
1. `pid: os_process_observation vs server_pid_file`
2. `pid: os_process_observation vs sentinel_file`
3. `pid: server_pid_file vs sentinel_file` (the intra-dependent-group comparison — computed and shown, per §17, never omitted merely because both sides share a witness group)
4. `start_time: os_process_observation vs sentinel_file` (re-expressing Layer 2's own `correlation.start_time_match_sentinel`/`start_time_delta_seconds`, not re-deriving it independently — see §7)
5. `observation_time: os_process_observation vs sentinel_file` — **always `NEITHER` today** (§9), reserved for future use, never omitted from the output even though it currently has a fixed, uninformative result — its presence in every output, even as `NEITHER`, is itself the honest signal that this dimension exists conceptually but has no data yet, rather than silently absent as if the question had never been considered.

Each relationship record's exact shape:
```json
{"subject": "pid", "compared": ["os_process_observation", "server_pid_file"],
 "state": "AGREE", "values": {"os_process_observation": 7644, "server_pid_file": 7644}}
```

---

## 6. Epistemic Contract

**Three states, confirmed sufficient by direct derivation-rule specification** (not merely asserted):
```python
EPISTEMIC_EVIDENCE_AGREES = "EVIDENCE_AGREES"
EPISTEMIC_EVIDENCE_CONFLICTS = "EVIDENCE_CONFLICTS"
EPISTEMIC_INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
```
**Exact derivation rule, computed once, after all 5 relationships are built**:
```
if any relationship.state == DISAGREE:      EPISTEMIC_EVIDENCE_CONFLICTS
elif any relationship.state == AGREE:        EPISTEMIC_EVIDENCE_AGREES
else (all ONE_SIDED/NEITHER):                 EPISTEMIC_INSUFFICIENT_EVIDENCE
```
**Precise, load-bearing property of this rule**: `DISAGREE` always wins, regardless of how many `AGREE`s exist alongside it — this directly implements the reconciliation-primitive-architecture report's own PID-reuse finding (§8/§9 there): a stale self-report that happens to still agree on bare PID but disagrees on start-time must never read as overall agreement. **"No contradiction" (zero `DISAGREE` relationships) is explicitly distinguished from "positive corroboration" (at least one real `AGREE`) by this rule's own two-branch structure** — a result with zero `AGREE` and zero `DISAGREE` (all `ONE_SIDED`/`NEITHER`) correctly falls to `INSUFFICIENT_EVIDENCE`, never silently defaulting to `EVIDENCE_AGREES` merely because nothing contradicted.

---

## 7. Input Contract

**Signature**: `reconcile_process_and_selfreport(layer2_result: dict) -> dict`. **Exactly one positional argument**, the complete, unmodified return value of `runtime_process_identity_and_self_report()` — never individual fields, per the architecture report's own already-settled §6/§13/§15 finding, restated here as a hard implementation requirement, not a style preference.

**Complete input**: all 5 relationships computed normally, per §5's rules.

**Missing fields** (e.g. `layer2_result["runtime_self_report"]` is `None`, matching Layer 2's own real `in_scope: False` shape, `provenance_check.py:888-895`): every relationship touching the missing sub-structure becomes `ONE_SIDED` or `NEITHER` per §5's rule — **never omitted from the output, never causing the whole function to raise**. This directly answers §7 of the mission brief: the function does not reject incomplete input; it represents the incompleteness explicitly, in the same relationship it would otherwise have computed, exactly matching Layer 1/2's own established "never collapse unknown into absence-of-output" convention.

**Malformed top-level input** (e.g. `layer2_result` is not a dict at all, or is `None`, or lacks the `in_scope` key entirely — a genuinely malformed argument, not merely Layer 2's own honest `in_scope: False` shape): **the function must not raise.** It should return a result whose every relationship is `NEITHER` (no evidence obtainable from an unparseable input) and whose top-level carries an explicit `input_error` field (a short machine-readable string, e.g. `"malformed_layer2_result"`), matching Layer 1/2's own universal "fail closed to an honest, structured result, never an exception" contract (`working_tree_file_identity`'s and `runtime_process_identity_and_self_report`'s own outer `try/except Exception` wrappers are the direct precedent — this function needs the identical belt-and-suspenders wrapper).

---

## 8. Validation Contract

**Minimum validation, performed inline, not delegated to a separate validator module** (avoiding exactly the kind of new abstraction the architecture reports have repeatedly declined to introduce without demonstrated need):
- `isinstance(layer2_result, dict)` — if false, degrade per §7's malformed-input path.
- Presence of the specific nested keys each of the 5 relationships needs (`external_process`, `runtime_self_report.server_pid_file`, `runtime_self_report.sentinel_file`) — accessed defensively (`.get()` chains, never bare `[...]` indexing that could raise `KeyError`), each absence flowing into the corresponding relationship's `ONE_SIDED`/`NEITHER` outcome rather than a validation-layer rejection.
- **No type-checking of individual leaf values beyond what §5's comparison logic already handles gracefully** (e.g. a `pid` field that's a string instead of an int simply fails the `==` equality check, correctly producing `DISAGREE` rather than a coerced, potentially-wrong match — already the behavior confirmed empirically in the Layer 2 red-team's type-mismatch test, reused here rather than re-solved).

**Validation belongs entirely inside the primitive** — there is no upstream validator to defer to (Layer 2 itself already validates its own output shape; there is no third module positioned to validate reconciliation's *input* before reconciliation runs), and duplicating Layer 2's own internal validation here would be exactly the kind of redundant, drift-prone duplication this project's own history (the `CATEGORIES`/`TASK_TYPE_MAP` precedent cited in the placement-architecture report) has already learned to avoid.

---

## 9. Timestamp Compatibility

**Current behavior, fixed precisely**: relationship #4 (`start_time`) is computed by directly reusing Layer 2's own already-computed `correlation.start_time_match_sentinel`/`correlation.start_time_delta_seconds` fields (re-expressed into the relationship-record shape, e.g. `AGREE` if `start_time_match_sentinel is True`, `DISAGREE` if `False`, `ONE_SIDED`/`NEITHER` if `None`) — **never independently re-parsed or re-derived from the raw `create_time_utc`/`start_utc` strings**, since Layer 2 has already correctly done this parsing (including its own tolerance and malformed-timestamp handling) and re-implementing it here would be a second, potentially-diverging copy of the identical logic. Relationship #5 (`observation_time`) is **hard-coded to always return `NEITHER`** today, since no `observed_at` field exists anywhere in the real input (§3) — this is not a runtime check that happens to always fail; it is a structurally guaranteed `NEITHER` for as long as the input schema lacks the field, made explicit in code (e.g. a comment citing this exact design document) rather than left to be accidentally discovered as "always empty" by a future reader.

**Future compatibility, specified precisely, not left vague**: when/if Layer 1 and Layer 2 eventually gain `observed_at`/`clock_source` fields (per the placement-architecture report's own still-open recommendation), relationship #5's computation changes from a hard-coded `NEITHER` to a real `§5`-style comparison between `external_process`'s own future `observed_at` and `sentinel_file`'s own future `observed_at` — **the relationship's `subject` name (`"observation_time"`) and its position in the fixed 5-relationship list do not change**, only its internal computation does, meaning this is a forward-compatible, additive change to the function's implementation, never a schema-breaking one for any consumer already depending on this function's output shape.

**Subject time usage, confirmed already correctly scoped**: relationship #4 uses `create_time_utc`/`start_utc`, both genuinely subject-time fields (§3) — this is exactly what the current architecture permits (the placement-architecture report's own §4 finding) and nothing more.

**Missing observation time**: remains `NEITHER`, permanently, until the field exists — **never fabricated from `create_time_utc`, file mtime, Git time, report-generation time, or reconciliation's own execution time** — this exact list of forbidden substitutions is copied verbatim from the mission brief into this specification precisely so the later implementation mission has no discretion to "helpfully" approximate it.

---

## 10. Purity Contract

**Explicit, exhaustive list, to be enforced by direct code review against this document, not by tooling** (per the enforcement-research report's own finding that this codebase has no mechanical purity-checking infrastructure):
- Reads only its single `layer2_result` argument.
- Performs zero filesystem access (no `open()`, no `os.stat()`, no `os.path.*` calls beyond, at most, pure string operations on already-present dict values).
- Performs zero process inspection (no `psutil` import, no `subprocess` import).
- Performs zero network access.
- Consults `datetime.now()`/`time.time()` **nowhere** — this is the one explicit exception the mission brief asks to be evaluated, and it is **not justified**: nothing in the §5/§6/§9 derivation rules needs "now," since every comparison is between two values already present in the input; a future implementer reaching for `datetime.now()` "just to log when reconciliation ran" should treat that impulse as **exactly the Model-C mistake the placement-architecture report already rejected outright** (§5 there) — restated here as a hard prohibition, not a style note.
- Does not mutate `layer2_result` (returns a new dict; never `layer2_result[...] = ...`).
- Does not mutate any module-level or global state (no caching, no counters, no writes to any `memory/*` file).
- **No justified exception exists for any of the above** — this function's entire value proposition, per the architecture report's own §14, depends on being a pure re-expression of already-gathered evidence.

---

## 11. Layer 1 Boundary

**Exact rule**: the function's parameter type is `layer2_result: dict`, documented (in its own docstring, matching Layer 1/2's own established convention of stating exactly what a function does and does not accept) as specifically the return value of `runtime_process_identity_and_self_report()` — **no Layer 1 field name appears anywhere in this specification's relationship list (§5), witness model (§4), or output schema (§14)**. If a caller passes a dict containing Layer 1-shaped keys (e.g. a merged Layer1+Layer2 object of the caller's own construction), those keys simply fall outside every relationship this function knows how to compute and are recorded, unread, in an `unrecognized_input_fields` list (§13) — **never silently ignored without a trace, and never accidentally incorporated into a relationship**, since no relationship-computation code path references any Layer-1-shaped key by name. **A future Layer 1+2 joint reconciliation primitive must be a distinct function** (a different name, e.g. `reconcile_file_and_process(layer1_result, layer2_result)`, not designed here) — this specification explicitly does not extend to cover that case, per the architecture report's own §19 finding that broadening scope for convenience is exactly the failure mode to avoid.

---

## 12. Scope Statement

**Decision: a fixed, constant string, included in every output, never varying per-call** — the smallest defensible solution, per the mission's own instruction to avoid unnecessary structure. Not an enum (there is only ever one value, since this function only ever reconciles one thing), not omitted (the reconciliation-primitive-architecture report's own §12 finding was that the *type* already structurally prevents the file/execution claim — but an explicit, human-and-machine-readable string restates this for any consumer who only reads the output, never the source):
```python
_SCOPE_STATEMENT = (
    "This result reconciles Layer 2 process/self-report evidence only. "
    "It establishes no claim about source-file identity, module loading, "
    "or code execution."
)
```
Included verbatim, unchanged, in every returned dict's `scope_statement` key.

---

## 13. Anti-Cherry-Picking

**Input-side protection, already fully specified (§7)**: the whole-`layer2_result` requirement. **Additional protection specified here, concretely**: an `unrecognized_input_fields: list[str]` top-level output key, populated by comparing the input's actual top-level and known-nested keys against the fixed set this function's 5 relationships reference — any key present in the input but never touched by any relationship computation is listed by its dotted path (e.g. `"external_process.status"`, a real Layer 2 field this function's 5 relationships never compare, since no self-report field carries an equivalent "status" to compare it against). **This is not a completeness *requirement*** — the function does not reject input for having unrecognized fields — **it is a completeness *disclosure***, so a careful consumer (or a future audit of this function's own behavior) can see exactly what evidence existed but was not part of any relationship, rather than that evidence silently vanishing with no trace. **No input fingerprinting, schema versioning, or evidence-source inventory beyond this is warranted** — per the mission's own instruction not to add complexity merely to make misuse theoretically harder, and per the architecture report's own honest acknowledgment (§15 there) that caller-side input cherry-picking is already structurally prevented by the single-dict-argument signature; nothing more is needed to close that specific gap further.

---

## 14. Output Contract

**Complete, exact schema**:
```json
{
  "input_error": null,
  "witnesses": {
    "independent": ["os_process_observation"],
    "dependent_groups": {"process_self_report": ["server_pid_file", "sentinel_file"]}
  },
  "relationships": [
    {"subject": "pid", "compared": ["os_process_observation", "server_pid_file"],
      "state": "AGREE", "values": {...}},
    {"subject": "pid", "compared": ["os_process_observation", "sentinel_file"],
      "state": "AGREE", "values": {...}},
    {"subject": "pid", "compared": ["server_pid_file", "sentinel_file"],
      "state": "AGREE", "values": {...}},
    {"subject": "start_time", "compared": ["os_process_observation", "sentinel_file"],
      "state": "AGREE", "values": {"delta_seconds": 4.43, "tolerance_seconds": 120}},
    {"subject": "observation_time", "compared": ["os_process_observation", "sentinel_file"],
      "state": "NEITHER", "values": {}, "note": "no observed_at field exists in current Layer 2 schema"}
  ],
  "aggregate": {
    "raw_agreeing_relationship_count": 4,
    "independent_corroboration_count": 1,
    "epistemic_summary": "EVIDENCE_AGREES"
  },
  "unrecognized_input_fields": ["external_process.cmdline", "external_process.executable",
                                  "external_process.cwd", "external_process.status",
                                  "external_process.access_denied",
                                  "runtime_self_report.sentinel_file.stage",
                                  "runtime_self_report.sentinel_file.uptime_s"],
  "scope_statement": "This result reconciles Layer 2 process/self-report evidence only. It establishes no claim about source-file identity, module loading, or code execution."
}
```

**`independent_corroboration_count`'s exact derivation, fixed, not left to implementer judgment**: `1` if the independent witness (`os_process_observation`) has an `AGREE` relationship with *at least one* member of the dependent group, else `0` — **capped at 1 regardless of how many dependent-group members individually agree with it**, since W2 and W3 together still constitute only one corroborating source beyond W1 itself (architecture report §11's exact rule). **Word choice, attacked directly per the mission's own instruction**: "corroboration" is used here deliberately for the *count* of independent-plus-dependent-group agreement (a real, meaningful, if modest, form of support), but **the term is never applied to the dependent-group's own internal agreement alone** (relationship #3, W2-vs-W3) — that relationship is labeled only `AGREE`/`DISAGREE`, never counted toward "corroboration" in isolation, since two manifestations of one self-belief agreeing with each other is not corroboration in any sense worth the word. **If only the independent witness were present (no self-report at all), `independent_corroboration_count` would be `0`, not `1`** — a single witness, however independent, corroborates nothing by itself; corroboration requires at least two genuinely distinct sources agreeing, one of which must be independent. This is the mission's own explicitly-flagged concern (§6 there), resolved precisely: **one independent witness alone is never called corroboration.**

**Absent, per the mission's explicit prohibition, confirmed by design**: no `verified`, no `verification`, no boolean verdict field, no numeric confidence score anywhere in this schema.

---

## 15. PID Reuse Semantics

| Case | Relationship states | `epistemic_summary` |
|---|---|---|
| Same PID + same start time | pid: `AGREE`×3, start_time: `AGREE` | `EVIDENCE_AGREES` |
| Same PID + different start time | pid: `AGREE`×3, start_time: `DISAGREE` | `EVIDENCE_CONFLICTS` (this is the reuse case — bare PID agreement is correctly overridden) |
| Different PID + same start time | pid relationships involving the differing side: `DISAGREE`; start_time: `AGREE` if computable | `EVIDENCE_CONFLICTS` |
| Different PID + different start time | all relevant: `DISAGREE` | `EVIDENCE_CONFLICTS` |
| Missing start time (either side `None`) | start_time relationship: `ONE_SIDED` | Depends on the 3 pid relationships alone |
| Malformed start time | Already degrades to `None` at Layer 2 (§3) before reaching this function — treated identically to "missing" | Same as missing |

**PID equality alone never, under any row of this table, produces `EVIDENCE_AGREES` if the start-time relationship disagrees** — the derivation rule in §6 guarantees this structurally, not by convention.

---

## 16. Stale Self-Report Semantics

**Case 1** (self-report PID matches, self-report start is old, OS start is current — a real reuse/staleness scenario): pid relationships `AGREE`×3, start_time `DISAGREE`, `epistemic_summary: EVIDENCE_CONFLICTS`.

**Case 2** (self-report PID matches, self-report start matches OS start — this is, in fact, exactly what real live PID 7644 data shows today, §14's worked example): all `AGREE`, `epistemic_summary: EVIDENCE_AGREES`. **This result remains, by construction, strictly a Layer 2 process/self-report consistency finding** — the output's `scope_statement` (§12) and the complete absence of any file/module/execution-shaped field in the schema (§14) together make it structurally impossible for this specific case's output to be read, by anything relying only on the returned data, as an execution claim.

---

## 17. Dependence Rules

**Encoding mechanism, decided precisely per the mission's own explicit question**: `_WITNESS_MEMBERS` (§4) is **hard-coded architectural metadata, a module-level constant in `provenance_check.py`, never caller-supplied and never derived from the input data at call time.** Justification, direct: the mission brief itself already flags the risk of caller-manipulable dependence metadata — if `layer2_result` (or any future parameter) could declare its own witness/dependence structure, a caller could falsely claim independence for two actually-dependent sources, precisely defeating the whole purpose of this design. **Known architectural truth (hard-coded) is strictly preferred over caller-supplied declaration**, exactly per the mission's own stated preference — this is not a close call.

**The critical invariant restated as an implementation-testable rule**: `server_pid_file` and `sentinel_file` must never, under any input, be treated as two separate entries in `independent_corroboration_count`'s computation — only as the fixed pair named in `_WITNESS_MEMBERS[_WITNESS_DEPENDENT_GROUP]`.

---

## 18. Adversarial Cases

| # | Case | Expected relationships | Expected `epistemic_summary` |
|---|---|---|---|
| 1 | Perfect PID agreement | pid ×3 `AGREE` | contributes toward `EVIDENCE_AGREES` |
| 2 | PID disagreement | at least one pid `DISAGREE` | `EVIDENCE_CONFLICTS` |
| 3 | Start-time disagreement | start_time `DISAGREE` | `EVIDENCE_CONFLICTS` |
| 4 | PID reuse | per §15 row 2 | `EVIDENCE_CONFLICTS` |
| 5 | Stale self-report | per §16 case 1 | `EVIDENCE_CONFLICTS` |
| 6 | Missing self-report (`runtime_self_report` fields all `None`) | pid relationships involving W2/W3: `ONE_SIDED`; W2-vs-W3: `NEITHER` | `INSUFFICIENT_EVIDENCE` if `external_process` also absent, else depends on remaining relationships |
| 7 | Malformed self-report (`malformed: True`, values already `None` at Layer 2) | same as 6 — malformed degrades identically to missing at this function's own boundary (§3, §5) | Same |
| 8 | Dependent duplicate witnesses | W2-vs-W3 `AGREE`, but `independent_corroboration_count` still capped correctly per §14's exact rule | Whatever the other 4 relationships independently determine |
| 9 | Layer 1 file matching Git | **not representable — Layer 1 is outside this function's input domain entirely (§11)** | N/A to this function |
| 10 | Layer 1 file dormant | Same — **not representable, by design, not by omission** | N/A |
| 11 | All available Layer 2 evidence agrees | pid ×3 `AGREE`, start_time `AGREE`, observation_time `NEITHER` (§9) | `EVIDENCE_AGREES` |
| 12 | Future observation timestamps absent (today's reality) | observation_time `NEITHER`, always | Does not affect the overall summary, since `NEITHER` never triggers either branch of §6's rule |
| 13 | Future observation timestamps present (hypothetical, post-schema-change) | observation_time computed per §9's forward-compatible rule — `AGREE`/`DISAGREE`/`ONE_SIDED` depending on real values | Participates in `epistemic_summary` exactly as any other relationship would |
| 14 | Timestamp present but semantically untrustworthy (e.g. derived from the wrong clock, per the enforcement-research report's own confirmed-undetectable finding) | Computed normally, **this function cannot and does not attempt to detect this case** — stated as an explicit, inherited limitation, not silently assumed solved | Whatever the raw comparison yields; the function has no mechanism to flag semantic untrustworthiness, matching the enforcement-research report's own conclusion exactly |
| 15 | Caller cherry-picks output | **Not preventable by this function** — the whole-dict output (§14) makes the complete evidence available, but nothing forces a downstream reader to consult `epistemic_summary` rather than, say, only `aggregate.raw_agreeing_relationship_count` (§13/§15 of the architecture report's own already-disclosed residual risk, restated here as unsolved by implementation, not newly solved by it) | N/A — a caller-side risk, not a function-behavior question |

---

## 19. Test Specification

*(Specified for a later implementation mission — none created here.)* Tests must be added to `scripts/verify_provenance_check.py`, extending its existing `CASES` list (matching Layer 1/2's own established convention, per the enforcement-research report's own confirmed shape — never a new, separate test file for one more function in the same module), covering, at minimum:

| Test | What it proves | What it does NOT prove |
|---|---|---|
| Happy path (real, current-live-shaped input, all agree) | The function correctly classifies a genuinely healthy, agreeing input | Nothing about whether the underlying process is "correct" — only that the classification logic works on this one input shape |
| PID disagreement (synthetic input) | `DISAGREE` is correctly produced and correctly forces `EVIDENCE_CONFLICTS` even alongside other `AGREE`s | Nothing about real-world PID-disagreement frequency |
| Missing self-report (synthetic, `runtime_self_report: None`) | Relationships degrade to `ONE_SIDED`/`NEITHER`, never crash, never silently default to `AGREE` | — |
| Malformed self-report (synthetic, `malformed: True` fields) | Malformed data is treated identically to missing, never coerced into a false match | — |
| Dependence (synthetic: W2/W3 agree, W1 absent) | `independent_corroboration_count` is `0`, not `1` or `2`, when the independent witness itself is missing — directly tests §14's exact rule | — |
| Dependence (synthetic: W1, W2, W3 all agree) | `independent_corroboration_count` is exactly `1`, never `3` — directly tests §11/§14's central invariant | — |
| PID reuse (synthetic: PID agrees, start-time disagrees) | `EVIDENCE_CONFLICTS`, not `EVIDENCE_AGREES` — directly tests §6's "`DISAGREE` always wins" rule | — |
| Timestamp compatibility — current schema (real-shaped input, no `observed_at`) | `observation_time` relationship is always `NEITHER` today | Does not prove anything about future schema versions |
| Purity (call the function twice with the identical input, assert byte-identical output; call with a copy of the input, assert the original is unmutated) | Determinism and non-mutation, directly | Does not prove the absence of I/O by inspection alone — see next row |
| No external I/O (mock/patch `open`, `os.stat`, `subprocess.run`, `psutil.Process` for the duration of a call; assert none are invoked) | Genuinely, directly proves zero I/O occurs during a real call — not merely asserted from reading the code | — |
| Layer 1 exclusion (pass a `layer2_result` containing extraneous, Layer-1-shaped keys, e.g. `{"sha256": "..."}` at top level) | Such keys appear in `unrecognized_input_fields` and influence no relationship — directly tests §11/§13 | — |
| `self_heal.py` false-positive scenario (real Layer 2 data for PID 7644, all agreeing — the actual live shape confirmed in §3/§14) | The output contains no field naming any file, confirming §17's central claim empirically against real data, not merely by code inspection | Does not prove `self_heal.py` is or isn't loaded — correctly, since this function cannot answer that question |
| Complete-input requirement (attempt to call with individual fields instead of the whole dict — a signature-level test, e.g. asserting the function accepts exactly one positional parameter) | The interface itself structurally forbids field-selection calls | Does not prove a caller can't destructure the *output* afterward (§13's own disclosed limit) |
| Output relationship completeness (assert exactly 5 relationship records are always present, regardless of input completeness) | The fixed relationship list (§5) is never shortened when evidence is missing — missing evidence produces `ONE_SIDED`/`NEITHER` records, not absent ones | — |

---

## 20. Naming Review

Every candidate name in this specification, attacked directly per the mission's own required term list:

- **`reconcile_process_and_selfreport`**: retained from the architecture report — accurately scoped (names its two real inputs, process and self-report, not a general "verify" concept).
- **`EVIDENCE_AGREES`/`EVIDENCE_CONFLICTS`/`INSUFFICIENT_EVIDENCE`**: retained — each names a fact about the *evidence*, never the *subject* ("process agrees" would have wrongly implied the process itself, not the evidence about it, is the thing agreeing).
- **`AGREE`/`DISAGREE`/`ONE_SIDED`/`NEITHER`**: retained — plain relationship words, no epistemic overclaim latent in any of them.
- **`independent_corroboration_count`**: retained, but its exact derivation (§14) is deliberately more conservative than the word alone might suggest — attacked directly per the mission's instruction, and the word survives only because §14 pins its meaning precisely (capped at 1, never inflating a lone independent witness into "corroboration"). **If this precise derivation rule is ever weakened in a future revision, this name must be reconsidered** — flagged explicitly as conditional, not unconditionally safe.
- **`witnesses`**: retained — a neutral, accurate term for "sources of evidence," carries no verification connotation.
- **`scope_statement`**: retained — plainly descriptive.
- **Rejected during this design pass, explicitly, with reasons**: `verified_relationship` (rejected — "verified" is banned outright per every predecessor report); `confidence` (rejected — no numeric score is proposed anywhere, per §14); `truth`/`ground_truth` (never proposed, would falsely imply this function can adjudicate which side of a `DISAGREE` is correct — it cannot, per §5); `process_identity` as a bare top-level boolean (rejected in favor of the full relationship list — a single collapsed boolean would be exactly the "generic verification verdict" every predecessor report has already prohibited); `running`/`executing`/`loaded` (do not appear anywhere in this schema, confirmed by the schema itself containing no such field, §14).

---

## 21. Dependencies and Placement

**Exact module**: `app/core/provenance_check.py`.
**Exact function name**: `reconcile_process_and_selfreport`.
**New imports required**: none beyond what the file already imports (`hashlib`, `json`, `os`, `subprocess`, `datetime`, `timezone`, `Optional`, `psutil`) — this function needs none of them; it is pure dict manipulation and string/number comparison, confirmed by §10's purity contract having no I/O of any kind.
**Dependencies allowed**: only Python's own built-in types (`dict`, `list`, `str`, comparison operators) — no third-party import, no intra-project import (it does not even need to *import* `runtime_process_identity_and_self_report`, since it only ever receives that function's *output* as a plain dict, never calls it itself — confirmed as correct per §10's "no evidence gathering" rule).
**Dependencies forbidden, explicitly**: `psutil` (would violate purity), `subprocess` (same), `os.stat`/`open` (same), `datetime.now()`/`time.time()` (§10's explicit prohibition).
**A new module is not required** — justified in §2, restated here as the final placement decision.
**Existing abstractions reused, not reinvented**: Layer 2's own `_START_TIME_MATCH_TOLERANCE_SECONDS` constant (§5), Layer 2's own already-computed `correlation.start_time_match_sentinel`/`start_time_delta_seconds` (§9), Layer 1/2's own established "fail closed to a structured dict, never raise" convention (§7), and `scripts/verify_provenance_check.py`'s own existing test-suite structure (§19) — no new testing infrastructure proposed.

---

## 22. Implementation Sequence

*(For the next mission — not performed here.)*
1. Add the fixed constants: `RELATIONSHIP_*`, `EPISTEMIC_*`, `_WITNESS_INDEPENDENT`, `_WITNESS_DEPENDENT_GROUP`, `_WITNESS_MEMBERS`, `_SCOPE_STATEMENT`, to `provenance_check.py`, immediately after the Layer 2 section.
2. Add a pure `_compare_values(a, b, tolerance=None) -> str` helper implementing §5's operational rule exactly, directly unit-testable in isolation.
3. Add the pure `reconcile_process_and_selfreport(layer2_result: dict) -> dict` function, composing §5's five fixed relationships via `_compare_values`, §6's epistemic-summary rule, §14's `independent_corroboration_count` rule, §13's `unrecognized_input_fields` computation, and §7's outer `try/except` malformed-input guard.
4. Add the docstring, stating precisely what the function can and cannot establish, matching the exhaustive style already established by `working_tree_file_identity()`'s and `runtime_process_identity_and_self_report()`'s own docstrings — not a shorter, less careful one merely because this function is newer.
5. Add the §19 test cases to `scripts/verify_provenance_check.py`, extending the existing `CASES` list — the existing 39 cases must remain passing, unweakened, exactly matching this project's own established regression discipline across every prior mission in this thread.
6. Run the full suite; require the new total (39 + the §19 count) to pass at 100%, exit code 0.
7. A dedicated epistemic-semantics review (not a code-quality review) confirming this specification's own §6/§14 derivation rules were implemented exactly as written, not approximated — recommended as a discrete step distinct from ordinary code review, given how much of this specification's value lies in precise rule-following rather than general code quality.

---

## 23. Stop Conditions

The later implementation mission must stop and return to research, not guess, if any of the following hold:

1. The actual, live Layer 2 schema (re-verified at implementation time, not assumed from this document) differs materially from §3 — e.g. a field renamed, removed, or a new field added that changes the witness model.
2. The dependence relationship between `server_pid_file` and `sentinel_file` can no longer be represented safely under §17's hard-coded-metadata approach — e.g. if a future Layer 2 revision adds a third self-report artifact with unclear dependence status.
3. Any of the 5 relationships' required fields turn out to have ambiguous semantics not already resolved by §3's field-by-field mapping.
4. Implementing any part of this specification would require accepting a Layer 1 field as input — this would mean the specification itself was wrong about the Layer 2-only boundary and needs re-review, not silent expansion.
5. Implementing any part of this specification would require the function to gather new evidence (any I/O of any kind) — this would violate §10's purity contract and must not be worked around by relaxing it unilaterally.
6. The observation-time placement question (still open per the enforcement-research report) resolves in a way that contradicts §9's forward-compatibility assumption (e.g., if observation time is decided to live somewhere other than directly on Layer 1/2's own output dicts) — §9 would need to be redesigned, not patched.
7. **Any existing or new caller appears to need a single boolean "verified" result to integrate cleanly** — this must trigger a stop, not an exception to §14's prohibition; per every predecessor report's own repeated finding, a caller's convenience need is never sufficient justification for reintroducing exactly the overclaim this entire research thread exists to prevent.

---

## 24. Explicit Non-Claims

1. That this specification, once implemented, would let reconciliation say anything about file identity, module loading, or execution — restated one final time, precisely because it is the single most important boundary in this entire five-plus-one-report research thread.
2. That `independent_corroboration_count` reaching `1` constitutes "verification" of anything — it means exactly what §14 defines: one independent witness and one dependent group agree, nothing stronger.
3. That the §19 test specification, once built, would prove the implementation correct for all future inputs — tests prove the specific cases they cover, never universal correctness (the enforcement-research report's own already-established limit, restated here as it applies to this function's own eventual test suite).
4. That this document constitutes permission to begin implementation — it is a specification for a *future*, separately-authorized mission, exactly as every predecessor report in this thread has maintained the same boundary.
5. That the placement decision in §2, or the dependency list in §21, forecloses a future decision to relocate this function if a genuinely new architectural need arises — this is the best-evidenced placement given today's codebase, not a permanent commitment.

---

## Verification

Reviewed directly against this mission's own required term list:

- `verified`/`verification`: appear only in explicitly rejected contexts (§20's naming review, §24's non-claims) — never asserted as an achieved property of this design's output.
- `confidence`/`corroboration`: `confidence` never appears as a proposed field (§14 confirms none exists); `corroboration` is used exactly once, in `independent_corroboration_count`, with its meaning pinned precisely and conservatively (§14) rather than left to imply more than one independent-plus-dependent-group agreement.
- `running`/`executing`/`loaded`: appear only in restatements of the prohibition (§11, §14, §24), never as an output the design produces.
- `identity`: used descriptively throughout (e.g. "process identity," "PID identity") in the narrow sense already established by the predecessor reports — never inflated into "verified identity" or similar.
- `timestamp`/`observed_at`: used with the exact subject-vs-observation distinction maintained throughout §9, consistent with every predecessor report.

---

## Integrity

```
Starting HEAD:  e03f5984bb86d36ade51ed8f0753a3b8264c0f9f
Ending HEAD:    e03f5984bb86d36ade51ed8f0753a3b8264c0f9f   (unchanged)
Files modified: none
Files created:  audits/2026-09-13_reconciliation_implementation_design.md (this file)
Staged:         nothing
Committed:      nothing
Pushed:         nothing
Scratch artifacts: none created -- entirely read-only grep/source inspection of
                 already-committed code
Tests created:  none
Implementation created: none
PID 7644:       unchanged throughout -- same start time (Thu Sep 10 22:41:53 2026)
                 confirmed via ps at mission start and end, read-only only
```
