# Generic verified proposer B — research prototype

**B-PROTOTYPE-1. Implemented components; not a qualified execution apparatus.**

This implements the cheap-baseline recommendation from
[SAC-1R2-A1](../2026-10-08_sac1r2_a1_baseline_and_simplicity_amendment.md).
There is no C record interpreter, learned-state access, production integration,
candidate runner, model call or retained-utility experiment.

## Components

| File | Responsibility |
|---|---|
| `b_prototype/contracts.py` | Strict JSON; exact task schema; current source/revision/hash binding; externally supplied registry; explicit invalid-contract states. |
| `b_prototype/analysis.py` | Bounded AST abstract interpretation of binding, ownership, returned ranking and numeric sign. Never executes source. |
| `b_prototype/proposer.py` | Generic polarity priority, deterministic fallback, at most two single-site patch commitments; reconstruction rejects forged binding claims. |
| `b_prototype/verification.py` | Independent pairwise task oracle; exact-type/value observations; complete supplied decision-suite checks; provisional selection only. |
| `b_prototype/journal.py` | Exclusive-create, fsynced event files; no overwrite. Caller-controlled research root, not an OS confinement mechanism. |
| `propose_cli.py` | Source-only JSON stdin/stdout interface. No oracle, answers, retained records, filesystem candidate output or launch. |
| `tests/test_components.py` | Disclosed engineering fixtures and manufactured observation batches. No candidate execution or held-out performance evidence. |

## Public component tests

From the repository root:

```sh
/Users/richietate/miniforge3/envs/feral_echo/bin/python3 -I -B audits/generic_verified_proposer_20261008/run_component_tests.py
```

The tests parse and transform source strings without importing, compiling or
executing them. Their supplied observations test decision logic; they are not
measured repairs. Test journal files use their own disposable temporary roots.

The proposal CLI accepts exactly `{ "source": "...", "contract": {...} }`:

```sh
/Users/richietate/miniforge3/envs/feral_echo/bin/python3 -I -B audits/generic_verified_proposer_20261008/propose_cli.py < public_request.json
```

No CLI writes candidate code or accepts expected values. Extra fields, duplicate
JSON keys, non-finite JSON and requests above 16 KiB are rejected. A proposal is
explicitly marked `NOT_ESTABLISHED_BY_PROPOSER` for authority.

Contract `B-TASK-1` has exactly: `schema`, `task_id`, `revision`,
`source_sha256`, `entrypoint`, `requirements`, `unknown_fields`, `conflict_refs`.
Requirements have exactly: `score_direction` (`higher`/`lower`), `tag_order`
(three distinct tags, most preferred first), `name_direction`
(`ascending`/`descending`), `return_type` (`str`), `input_effects`
(`preserve_values`), and `field_schema`
(`["name:str", "score:int", "tag:str"]`).

Before provisional verification, the trusted caller must provide a **separate**
registry binding task ID to exact contract digest/revision and owner/oracle-review
references. Nothing reads production state or creates real approval records.
Public tests use conspicuously fake registry entries. Approval references/hashes
cannot establish their own legitimacy: actual custody and authority review remain
external prerequisites.

## Implemented recognition scope

- One entry function with one argument and at most two ordinary pure helpers.
- Straight-line unique local definitions, literal rank maps, numeric unary signs,
  fixed tuple/row indexing and explicit first/last selection.
- Builtin `sorted` and owned outer-list `.sort`, with a literal `reverse` flag and
  a lambda or resolved named key; direct/extracted score and rank-map operands.
- Shallow list copy and a one-level row-building list comprehension; aliases to
  the input may be read but may not be sorted in place.
- Module scope contains plain functions only. A returned constant string or an
  unsorted first/last name can have no eligible repair site.
- Up to 8 KiB source, 256 AST nodes, eight eligible numeric sites, four independent
  sorts and 2,048 abstract-expression visits.

The common rule computes `q × s × d` from current task/source facts. Resolved
inconsistent signs take priority; all other eligible sites retain deterministic
generic fallback. Both directions of sign toggle exist. Unknown/nonmonotone
orientation or unresolved criterion precedence gets no polarity priority.
Binding/type/ownership uncertainty that prevents eligibility causes refusal.

Sites in a dead independent sort do not consume proposal slots. Repeated analysis
paths to one physical site coalesce. Distinct patched ASTs are not assumed
semantically equivalent. Each patch is relative to the original source.

**This is a subset implementation, not all of the proposed R2 grammar.** It refuses
interacting/stable sort chains, general control flow, recursion, global state,
imports, dynamic dispatch, annotations/default/keyword helper parameters,
assignment rebinding, mutable inner entries, general attributes, dynamic indices,
`len`-derived edits and arbitrary return-dependent numeric computation. The
fallback covers eligible numeric ranking sites in this subset, not a general
Python repair search. Unknown constructs are not added as syntax exceptions to
make a test pass. No coverage percentage or soundness theorem is claimed.

Numeric component precedence must resolve exactly as score/tag/name to receive
polarity priority. Wrong precedence can still produce fallback hypotheses; the
independent verifier must reject incomplete repairs. Local polarity alone never
establishes complete task correctness.

## Verification and evidence boundaries

The oracle uses pairwise score/tag/name comparisons from the current task. It does
not inspect candidate rank maps, proposal signs or Skill A. The observation checker
requires a returned exact string and an unchanged complete primitive input tree;
bool/int/float substitutions are distinct. Allowed input values are one to three
unique ASCII names (at most 64 characters), signed 63-bit scores and declared tags.

`assess(...)` accepts exactly 24 distinct decision inputs, original observations
and complete batches for every committed proposal. Each batch binds phase,
source, contract and input hashes. Hidden-phase, stale, incomplete or infrastructure
evidence gives `MEASUREMENT_ERROR`. Candidate errors/timeouts are nonconformance.
The first fully conforming proposal may receive
`PROVISIONAL_ACCEPT_EXACT_PATCH` only if the original failed an observation.
An already-conforming original is retained. Partial fixes and mutations fail.

The supplied batches are **not authenticated child-execution evidence**. The
checker does not certify test coverage, oracle approval, complete side-effect
observation or isolation. Every result carries `production_authorized=false` and
`execution_qualified=false`. `execute_candidate(...)` always raises; there is no
switch that turns a supplied approval string into candidate execution or a
production write.

All components are developer code running under the trusted caller. The source-only
CLI has a small input interface, but its new process/path has not received OS
confinement qualification. The journal is a durability component, not protection
against a malicious controller. Directory-level crash recovery and hard memory
allocation bounds are not claimed.

## Before any experiment

1. Independently review this implementation and its smaller supported subset.
2. Obtain accepted task-owner, oracle-reviewer, custodian and final-reviewer roles.
3. Approve/freeze the exact observer and E0.1 adapter, source/contract/expected-value
   interfaces, profiles, paths, budgets, visibility controls and public qualification.
4. Qualify both proposer/candidate rooms, operation-aware cleanup, transport,
   reference/constrained semantics, observation bounds and durable results.
5. Verify resource feasibility without held-out material. Only then separately
   authorize scored execution and instantiate genuinely independent held-out cases.

No new E0.1 adapter/profile was built or historical one silently repurposed here.
Existing E0.1/worker/guard/observer remain unchanged for later explicitly qualified
reuse. This prototype is engineered competence; it does not improve live Echo or
demonstrate acquired competence, beneficial transfer or retained net utility.
