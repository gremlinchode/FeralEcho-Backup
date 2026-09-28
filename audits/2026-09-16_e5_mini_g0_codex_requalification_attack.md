# E5-mini G0 — independent Codex requalification attack

Date: 2026-09-16. Scope: adversarial review of the repaired **mocked** apparatus. No implementation changes, real E5, real inference, production imports, or runtime intervention.

## 1. Verdict

**G0: NOT QUALIFIED. E5: NO-GO.**

**Independently reproduced:** 66/66 tests pass, with zero failures, errors or skips. The targeted historical regressions have useful repairs: actual solver invocations now equal 240 at four families; the scenario join includes generation identity; complete oracle deletion, dangling references, literal N-message convention leakage, and ordinary coherent-options drift are detected.

**Also independently reproduced:** both the repaired checker and the execution-witness comparison accept materially invalid experiments:

1. Execute task 0 twice, never execute task 1, and retain 60 total solver invocations. Both validators pass.
2. Carry teaching-derived information from P into N through a shared solver callback/cache. N's recorded prompt and empty memory remain identical while its output tracks changed teaching. Both validators pass.
3. Replace a failed N response with the correct answer and a matching PASS result/hash after execution. Both validators pass.
4. Present an earlier run's ledger with a genuine count from 60 unrelated later solves. Both validators pass.
5. Delete eight Z/N world-0 outcomes. Both validators pass; reversing record order can change the result.

These counterexamples do not require changing repository source or disabling the checker. The first four demonstrate the central distinction: **matching counts and internally consistent records are not an execution-to-record correspondence**.

The weakest defensible positive finding is: *the repaired deterministic mock avoids the original duplicate reuse invocation and detects several specific inconsistency classes*. It has not qualified its claimed experimental information, execution, outcome or frozen-specification boundaries.

## 2. Method, scope and evidence standard

I inspected the three requested reports and current implementation. Neither report was treated as authoritative. The prior Codex report was also checked against the changed source rather than used as an immutable specification of present failures.

Opening HEAD: `2fba42644c82b9f7096276f4dd338d615cf1bcce`. Working-tree source, including untracked files, is the reviewed artifact. Source/report hashes and full opening status are recorded below.

The suite and three adversarial probe batches ran in fresh `python3 -B -I -S` analysis processes. Parent package initializers and the import closure had been inspected; imports were limited to the mocked package and the standard library. A review-time Python audit hook rejected network, subprocess/shell/fork/exec/signal operations and writes outside an isolated temporary root. Bytecode and site/plugin startup were disabled.

The only test write was a sacrificial file under a temporary root. All temporary roots were removed. Process-local object mutations and temporary `unittest.mock.patch` fault injection were used; **no implementation file was edited**. An injected callback executed only small deterministic Python functions. No generated code, model backend, Echo service, RiverBrain, FAISS, hub/relay, or production state was used.

“Pass” in the attack results means the strongest combination the repaired code exposes for these checks:

- `check_ledger(...)` returns no violations; **and**
- `verify_execution_witness(ledger, get_solve_witness_count())` returns `execution_matches_declaration=True`.

There is no integrated, mandatory, frozen-manifest run-close API establishing stronger validity. A passing pair here is a **valid-looking apparatus result**, not an E5 authorization. Where optional expected assignments expose a different result, I report that explicitly.

Evidence labels:

- **OBSERVED:** directly established in source or a fresh test execution.
- **REPRODUCED:** a targeted fault was introduced and the resulting false acceptance/rejection measured.
- **LIMITATION:** a boundary not established by these tests.
- **RECOMMENDATION:** a proposed repair or next gate, not implemented.

I distinguish ordinary fault injection at the producer/strategy boundary from the weaker demonstration that a caller with access to validator globals can rewrite them. The qualification decision does not depend on that unrestricted-tampering case.

## 3. Old-attack regression results

| Historical attack | Fresh result | What is actually closed |
|---|---|---|
| 272 actual solver invocations / 240 generation labels | **Closed for the ordinary four-family run:** independent wrapper count 240; internal witness 240; declared generations 240. | The reuse branch retrieves a prior response instead of invoking the solver again. |
| Cross-arm scenario score join | **Closed on the standard asymmetric fixture:** P=1.0, E=0.0, Z=0.0, N=0.0. | Generation identity is included in the join. This does not repair the separate UNKNOWN-oracle problem. |
| Remove every oracle reference | **Detected:** 60 MISSING_ORACLE_RESULT violations at one family. | Total outcome deletion no longer passes. Partial paired-world deletion still does. |
| Reference a nonexistent generation | **Detected:** ORPHANED_ORACLE_REFERENCE. | Dangling references are rejected. Self-consistent fabrication/replay is not. |
| Literal convention in N's recorded user message | **Detected:** CONVENTION_LEAKED_VIA_MESSAGE_CONTENT. | Literal canary scanning now covers message content. It is not an information-isolation proof. |
| Change requested and effective options together to temperature 0.9 | **Detected:** COHERENT_OPTIONS_DRIFT. | Records are compared against a separately declared checker dictionary. |
| Mutate builder options after importing resource manifest | **Detected:** options_match_real_apparatus=False. | The deepcopy snapshot is no longer the same object as the live configuration. Its freeze point remains import-dependent. |
| Ordinary undeclared extra solve, unchanged ledger | Supplied negative-control regression passes: witness mismatch is detected. | An isolated increase in count is caught. Balanced retry/omission is not. |
| Clean four-family contamination false positives | **Closed at four families:** zero checker violations. | Distinct fixture token suffixes avoid the earlier equal-token collision; substring collisions still occur at a larger index. |

The reported **66** comprises **54 G0 tests** (including two new accounting regressions) and **12 manifest tests**. Unittest reported 0.024 seconds. This is evidence that those assertions passed, not a statistical reliability estimate.

Current four-family baseline: 20 constructions, 240 solver invocations, 272 solver rows, 272 oracle references and **32 UNKNOWN outcomes**. The original mismatched world-specific query IDs remain: a world-0 ID is sent to a world-1 oracle. The intended 320-row scoring view remains incomplete. No claim that all findings in the original long-form review were repaired is justified.

Other previously documented gaps remain visible in unchanged source: direct hidden-convention assembly in teaching; asserted rather than independently observed applicability dispatch; mutable stored records; selected anomaly tests that assert a property without exercising an integrated boundary; and lack of full packet validation. This review prioritizes new falsification rather than treating every old subfinding as a new discovery.

## 4. Decisive counterexamples

### A1 — Balanced undeclared retry and omitted execution

**REPRODUCED. No witness mutation, reset inside the run, or checker modification.**

At the producer's mock-solver boundary, a temporary fault adapter:

- calls the genuine solver twice for its first request;
- returns the retained first-request response for its second request without invoking the solver;
- forwards all remaining requests normally.

The untouched `mock_solve` counter records **60 genuine invocations**. The ledger declares **60 generations**. The actual first query sequence is:

```text
related_input_0
related_input_0
related_input_2
```

The recorded first slots claim queries 0, 1 and 2. The checker returns **[]** and witness comparison returns **True**.

A failed oracle score on the substituted response is not an adequate detector: a legitimate solver may fail a task, whereas this apparatus must distinguish “attempted and failed” from “not executed, replaced by an undeclared retry elsewhere.”

**Cause:** `accounting.py:48–81` checks cardinality only. `mock.py:245` increments a count without binding the invocation to a run, request, logical slot, input digest, response, outcome or attempt status. The duplicate-slot checker inspects ledger IDs, not observed request events. Equal numbers permit a non-bijective mapping.

**Required repair:** a trusted per-invocation event stream, independently collected at the actual mock execution boundary and bijectively matched to assigned attempts and output identities. Record failed attempts and starts without finishes too. A count remains a useful summary, not the witness itself.

### A2 — N acquires experience through shared callback state

**REPRODUCED. No monkeypatch, ledger rewrite, counter manipulation, or validator change.**

The public API accepts a `SolverStrategy` containing callbacks. I supplied the **same** strategy object to all four arms. Its extraction callback behaves normally for nonempty memory but retains the last convention extracted from P's procedure. When called with empty memory, it returns that retained value.

This creates an actual path:

```text
P teaching → P procedure → shared extractor state → N solver output
```

The input packet recorded for N remains:

```text
SPEC: (public)
MEMORY:
QUERY: related_input_0
```

With the original teaching, N returns `related_input_0::conv_beta_00`. In a second isolated run, changing the world-1 teaching convention and its private oracle fixture to `conv_gamma_00` makes N return `related_input_0::conv_gamma_00`. N's recorded system/user packet is byte-identical across these runs, and its memory field remains empty. The callback logs ten reads of the retained convention by N in each run.

Both runs yield:

```json
{"checker_codes": {}, "actual_solver_invocations": 60,
 "expected_distinct_generations": 60, "execution_matches_declaration": true}
```

The information read comes from the actual earlier procedure, not from a separately hardcoded oracle answer in the callback. The private oracle change makes the alternate synthetic world internally consistent; the callback cannot access that oracle through its arguments.

This is not a claim that the ordinary stateless CLEAN_STRATEGY leaks today. It is a counterexample to the apparatus establishing N isolation for the execution it accepts. The supplied strategy API permits stateful behavior, and neither its identity/state nor its information access is captured.

**Required repair:** define and enforce the solver's complete input/state boundary. N must not share retained-experience state, caches, closures, retrieval handles or mutable callbacks with teaching-exposed roles. Either admit only pinned stateless workers with controlled dependencies, or isolate each role/attempt in a fresh worker with explicitly supplied inputs. Record the actual consumed packet/state identity. Merely scanning for a secret string cannot establish absence of a channel.

### A3 — Post-execution response replacement becomes a valid-looking PASS

**REPRODUCED. No extra solve and no witness tampering.**

After a clean one-family run, I selected one N related-query generation whose world-0 score was FAIL. I replaced its response in both reused solver rows with the correct world-0 expected answer, recomputed the response hash, and changed the corresponding oracle result to PASS with an exact-match detail.

The new answer is genuinely correct for that oracle. Thus recomputing only the oracle against the **substituted** answer would still pass; the missing evidence is that this answer was ever produced by the witnessed execution.

Result: **FAIL → PASS**, zero checker violations, witness **60=60**.

**Cause:** the witness has no response identity; ledger objects are mutable; hashes are supplied alongside the content and have no protected prior binding. `checker.py` does not establish an execution-to-response-to-oracle chain.

**Required repair:** collector-owned immutable response bytes/hash tied to the request event, followed by oracle-owned result records. Reject substitutions even when their recomputed content hash and expected answer agree.

### A4 — A genuine witness count can belong to unrelated work

**REPRODUCED. No fabricated counter value.**

I retained a clean ledger, reset the witness at a new execution-window boundary, then invoked the genuine mock solver **60 times on `unrelated_probe_work`**. I submitted the original ledger with this new genuine witness count.

Checker: **[]**. Witness: **True, 60=60**.

The new window executed none of the ledger's declared query sequence. There is no run identity, nonce, request fingerprint, event sequence or freshness requirement linking the two artifacts.

This is stronger than simply writing a desired value into the counter: the supplied “actual” count was honestly obtained from real mock invocations, but for the wrong computation.

**Required repair:** bind independently witnessed events and immutable evidence to one admitted run and specification. A reset must create a new run namespace, not erase provenance while leaving old records acceptable.

### A5 — Partial paired-world outcome deletion passes

**REPRODUCED. No execution or witness manipulation.**

Deleting all eight world-0 related-query oracle references for Z/N in the one-family run leaves zero checker violations and witness **60=60**.

The new completeness functions at `checker.py:331–339,364–371` construct a dictionary mapping generation ID to **one** slot. Z/N intentionally have multiple scoring-world rows for a generation, so the later world-1 row overwrites world 0. Coverage is checked against whichever row survived.

Deleting one N world-0 reference passes in normal insertion order. Reversing the solver dictionary's insertion order then produces **MISSING_ORACLE_RESULT: 1** without changing any substantive record. A validity decision should not depend on dictionary order.

Conversely, passing the complete set of the existing clean solver slots as `expected_slots` produces **eight false MISSING_ASSIGNED_SLOT violations**. The optional stricter check is therefore not a functioning escape from the default checker gap.

**Required repair:** represent one generation to many scoring references explicitly. Check the frozen set of primary/diagnostic scoring keys, with multiplicity and purpose, rather than collapsing generation identity to one world. Record-order permutation must leave the verdict and denominator unchanged.

## 5. Other attacks and limits

The following were freshly executed as isolated mock probes. “Pass” below uses the combined check defined in §2 unless otherwise noted.

| Attack | Observed result | Interpretation |
|---|---|---|
| Append base64-encoded retained convention to N's user message | Pass | Literal-token scan does not reject equivalent encoded information. This probe validates recorded-packet acceptance; no real model decoded it. |
| Append a non-canary statement of a teaching-derived precondition to N context | Pass | Information outside the convention-token vocabulary is unexamined. |
| Delete all N user messages, leaving the system message | Pass | Missing required input is accepted; no exact packet-shape check. |
| Make a sixth construction call through ordinary construct_arm, attempt index 0 | Pass; constructions 5→6, solver witness stays 60 | Constructor computation is unwitnessed by this counter and cardinality is not enforced. |
| Rewrite expected answer, response/hash and result together after execution | Pass | Mutable oracle “truth” and mutable evidence can drift coherently. There is no required task-manifest acceptance hash in check_ledger. |
| Change an oracle result to a non-enum string | Pass | Malformed result evidence is not schema-validated. |
| Flip a stored oracle result | Pass | Oracle truth is not independently re-established from protected execution evidence. |
| Relabel a real P generation and its reference as a never-assigned query; change recorded query text | Pass | Default checking verifies no closed assignment set and the witness carries no query identity. |
| Create two ordinary ledgers in separate reset windows | 5 construction IDs, 68 solver-call IDs and 60 generation IDs collide | IDs are per-instance counters, not run-scoped identities. This does not corrupt an isolated ledger by itself; it enables replay/misattribution when evidence is combined. |
| Reset after an undeclared solve, then run the ordinary experiment | Pass | No protected start/close lifecycle preserves the earlier invocation. |
| Directly write witness count from 63 back to 60 | Pass | Disclosed mutable-counter trust weakness; weaker than A1/A4 because it assumes write access to the witness. Not needed for the verdict. |
| Mutate checker expectation plus requested/effective options together | Pass | A Python dictionary called “frozen” is mutable. This is a trust-boundary demonstration, not proof that an unprivileged external actor can alter it. |
| Mutate builder options before first resource-manifest import | Budget verifier reports every flag true | Snapshot creation blesses current mutable runtime state; freeze point is import order, not prior scientific admission. The separately declared checker can still catch 0.99 if called. |
| Run resource-budget verification between execution and witness read | Witness rises 60→120; valid experiment now mismatches | The verifier itself runs an unrelated synthetic family in the same global witness namespace. Counting is not scoped to the reviewed run. |
| Clean 101-family sacrificial mock run | 4 CROSS_WORLD_CONTAMINATION and 40 CROSS_WORLD_MESSAGE_CONTAMINATION false positives; 6,060 mock solves | `conv_alpha_10` is a substring of `conv_alpha_100`. Suffix uniqueness is not sufficient for substring leak attribution. Low priority for four-family G0, but a real generalization failure. |

Malformed enum acceptance is a pass, not a caught exception mislabeled as validity. Other arbitrary malformed objects could raise exceptions; a crash would need an explicit invalid/incomplete outcome in a future close API, but was not counted as a successful bypass here.

The encoded/non-canary packet attacks are not the basis for claiming actual N execution leakage. **A2 is that execution-level demonstration.** Likewise, direct validator/counter mutation is not the basis for claiming weak identity binding; A1, A3 and A4 establish it without that privilege.

The 101-family probe was a cheap deterministic loop, not a proposed larger scientific experiment. It generated no model inference or persisted dataset.

## 6. Four distinct truths

| Layer | Present implementation | Independent result |
|---|---|---|
| Frozen experimental specification | Mutable world objects; optional expected slots; checker dictionary; import-time budget copy; manifest helpers outside the mandatory path. | No single independently admitted specification is required or bound to the run. |
| Actual execution behavior | mock_solve invokes strategy callbacks using memory/query/kind; constructors run separately; callbacks can retain state. | Execution can repeat, omit, retain information or differ from recorded packets. |
| Independently witnessed execution | One module-global solve counter, caller-supplied integer to a separate comparison function. | Useful independent increment for a narrow call-count regression; no event/content/run identity or constructor coverage. |
| Internal ledger consistency | Mutable records, foreign-key checks, selected option/message checks and counts. | Improved but incomplete. Even perfect consistency would not close the correspondence gaps above. |

The mock solver does not consume `ordered_messages`, system text or generation options. Those fields are assembled and recorded separately by the builder. Its actual arguments are `strategy, memory_text, query, query_kind`. Consequently, scanning logged messages is not a gateway observation of everything the mock consumed; A2 exploits exactly that distinction.

**Execution-witness independence verdict:** **PARTIAL FOR COUNTING; INSUFFICIENT FOR QUALIFICATION.** Its increment is separate from ledger ID allocation, which genuinely catches the isolated extra-call regression. Its value, lifecycle and namespace are shared mutable process state, and its payload cannot identify any execution. An out-of-process **counter alone** would still fail A1 and A4. The repair must add event identity and binding, not merely move the integer.

**N-isolation verdict:** **NOT ESTABLISHED; COUNTEREXAMPLE REPRODUCED.** Empty retained-memory fields and absence of known token strings do not prohibit retained information through the strategy's shared state. No evidence here says ordinary production N exists or leaks; this is the G0 apparatus's accepted mock path.

**Frozen-versus-runtime truth verdict:** **NOT ESTABLISHED.** Separate copies remove one aliasing bug but do not define an independent freeze point, immutable acceptance record, or compulsory comparison against it. Import order can determine the “expected” budget. Actual world/response/result state can be edited coherently without the checker detecting drift.

**Arm isolation verdict:** **NOT ESTABLISHED.** The score-join repair prevents the particular cross-arm result join. It does not prevent cross-arm state transfer or unrecorded changes in strategy behavior.

## 7. Why passing tests and disclosure do not change the verdict

Claude correctly stopped at **REQUALIFICATION CANDIDATE**, retained E5 NO-GO, disclosed the mutable witness and suggested attacking content substitution and bypass paths. Those are appropriate limits. The report's stronger “generalized repairs” language is not borne out by the fresh counterexamples.

The old regression fixes are real. They should be retained, not rolled back because other failures remain. But several were generalized only from a fixture to a closely related field check:

- Whole-cloth fabrication can be detected by **count imbalance**, while same-count substitution/replay remains accepted.
- Missing outcomes are detected for surviving generations, while one-to-many world membership is collapsed.
- Literal N convention leakage is detected, while information access itself is unconstrained.
- Options no longer compare the same object to itself, while “frozen” truth still depends on mutable snapshots and admission timing.

The original thirty-anomaly methods are mostly unchanged. In particular, a method counting as passed does not independently validate artifact reload, oracle write protection, executed dispatch or frozen assignment. There is no basis to promote the 66-test result to full measurement qualification.

For mock G0, it is reasonable to trust a deliberately small collector/validator implementation and keep candidate text inert. It is not necessary to prove security against an attacker who can rewrite every trusted component. This rejection is narrower: faults in the **producer and allowed strategy path**, leaving the validators intact, yield results the validators accept.

## 8. Smallest defensible next repair and gate

**Repair the isolated mocked correspondence boundary. No real inference and no production integration.**

The repair needs one coherent, bounded contract:

1. **Admit before execution.** Pin a run ID and immutable canonical task/role/budget/source specification before generating anything. Require its hash and complete construction/solve/scoring assignments at validation. Missing or empty admission cannot yield a clean close.
2. **Witness events, not only counts.** A collector at the actual execution boundary owns ordered start/finish/failure events containing run/attempt/role/logical-slot IDs, actual input/state/config fingerprints, and returned output identity. Observe constructors as well as solvers. Store event snapshots outside producer-owned mutable records.
3. **Enforce a bijection.** Every declared generation resolves to one permitted completed invocation; every actual invocation resolves to an assigned attempt or an explicit invalid event. Reuse has references, not an invocation. Failed and retried work cannot disappear or be balanced against omitted work.
4. **Bind outputs to scoring.** Oracle references must resolve to the collector's actual immutable response and frozen oracle version, not mutable producer-supplied text plus a newly computed hash. Require valid enums and all assigned primary/diagnostic score keys.
5. **Close the information boundary.** Specify all worker inputs and admitted executable strategy dependencies. Separate state across exposed and unexposed roles; a fresh worker or a strictly controlled pure worker can implement this small mock boundary. N has no retained-experience callback/cache/retrieval/context capability. Validate the exact consumed packet, not a parallel description of it.
6. **Make close compulsory and deterministic.** One qualification entrypoint checks admission, execution events, ledger, scoring, manifests and completeness. Reordering evidence must not alter verdicts. Derive summaries without changing denominators; missing/malformed evidence is invalid/incomplete.
7. **Keep a clear trusted boundary.** Callbacks/producers cannot reset or forge collector state. The validator must not accept an arbitrary caller-provided count as execution proof. If the claimed fault model includes arbitrary Python execution in the producer, use a separate observer boundary; if not, explicitly pin the trusted code and limit the claim. Either way A1–A5 must be rejected.

No new production scheduler, task kernel, learning module, general tool inventory or fourth architectural subsystem is needed to perform this repair. Whether a field belongs in a fourth “manifest category” is not implementation-blocking. The required binding can reference the existing three manifests and an admitted run record.

**Next acceptance gate:** a fresh mock-only run must reject A1–A5 through its single qualification entrypoint, without special-casing attack strings. Also require original regressions, constructor overrun, cross-run replay, result mutation, encoded/non-canary packet drift, missing user packets, record-order permutation and import-order budget cases. Use a stateful response-changing mock for reuse and a shared-state poison fixture for arm isolation.

The clean four-family run must have the frozen assignment/scoring coverage, valid paired-world oracle mappings, and an exact independently known outcome table. It must not “solve” current false positives by disabling completeness checks or dropping expected slots. Deliberate malformed/incomplete trials must remain in the record with non-qualified close states.

Passing that gate would license a **bounded mocked-instrument qualification** under a stated trust model. A live transport's isolation/resource admission and populated frozen scientific manifests would still need separate verification before E5. G0 would establish no transfer or learning. A successful E5 can at most provide independently measured transfer evidence, with pilot limitations; longitudinal E8 remains necessary for sustained accumulation.

## 9. Exact reproductions

The appendix preserves the actual probe bodies used in this review, rather than only conceptual pseudocode. They ran as three separate fresh analysis processes. No source file edits were involved.

For reproduction, prepend the common guarded bootstrap and common imports/helpers to **one** numbered probe body, then execute with `python3 -B -I -S`. Code can be supplied in memory via `-c`; no probe file is necessary. The only permitted writes are the bootstrap's temporary root, removed by `finish`. These scripts run deterministic mocks only.

The complete output is summarized in §§3–5; the decisive expected outputs are: **A1 actual=declared=60 with repeated query 0 and omitted query 1; A2 same N packet, beta→gamma output, both validators pass; A3 FAIL→PASS with both validators passing; A4 unrelated 60-call window accepted; A5 eight deleted outcomes accepted.**


### Common guarded bootstrap

```python
import sys, os, tempfile, io, json, unittest, collections
sys.path.insert(0, "/Users/richietate/Desktop/FeralEcho")
scratch = tempfile.TemporaryDirectory(prefix="feralecho-g0r-codex-", dir="/private/tmp")
scratch_path = scratch.name
tempfile.tempdir = scratch_path
events = []
def audit(event, args):
    if event.startswith(("socket.", "subprocess.")) or event in ("os.system","os.kill","os.killpg","os.exec","os.posix_spawn","os.fork","os.forkpty"):
        events.append({"blocked":event})
        raise RuntimeError("review boundary blocks " + event)
    if event == "open":
        path, mode, flags = args
        writing = (isinstance(mode,str) and any(c in mode for c in "wax+")) or (isinstance(flags,int) and bool(flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)))
        if writing and isinstance(path,(str,bytes,os.PathLike)):
            resolved=os.path.realpath(path)
            if not (resolved == scratch_path or resolved.startswith(scratch_path+os.sep)):
                events.append({"blocked_write":str(resolved)})
                raise RuntimeError("review boundary blocks write")
            events.append({"scratch_write":os.path.relpath(resolved,scratch_path)})
sys.addaudithook(audit)
```

### Common imports and helpers

```python
from dataclasses import replace
from copy import deepcopy
from unittest.mock import patch
import app.experiments.e5_mini.builder as builder
import app.experiments.e5_mini.mock as mock
import app.experiments.e5_mini.checker as checker
from app.experiments.e5_mini.tests.test_e5_mini_g0 import _clean_family_ledger, TestMockedEndToEndApparatusValidation
from app.experiments.e5_mini.orchestrator import run_mock_e5_mini, run_family, ArmStrategies
from app.experiments.e5_mini.schema import Action, OracleResult, QueryKind, sha256_of
from app.experiments.e5_mini.ledger import Ledger
from app.experiments.e5_mini.accounting import reconcile, verify_execution_witness
def fresh():
    mock.reset_solve_witness()
    return _clean_family_ledger()
def codes(l,wm,slots=None):
    return dict(collections.Counter(v.code for v in checker.check_ledger(l,wm,slots)))
def verdict(l,wm,slots=None):
    return {"codes":codes(l,wm,slots),"witness":verify_execution_witness(l,mock.get_solve_witness_count())}
def finish(out):
    print(json.dumps(out,default=str,sort_keys=True))
    scratch.cleanup()
    print(json.dumps({"scratch":scratch_path,"removed":not os.path.exists(scratch_path),"audit_events":events,
        "production_modules":[m for m in sys.modules if m.startswith(("app.core","ollama","faiss"))]}))
```

### Probe batch 1

```python
out={}
mock.reset_solve_witness()
with patch.object(builder,"mock_solve",wraps=builder.mock_solve) as spy:
    full=run_mock_e5_mini(4)
    actual=spy.call_count
worlds={(w.family_id,w.world_id):w for pair in mock.make_synthetic_families(4) for w in pair}
out["old_count_clean"]={"spy":actual,**verdict(full,worlds),"counts":reconcile(full),
    "unknown":sum(r.oracle_result==OracleResult.UNKNOWN for r in full.oracle_references.values())}
l,w0,w1,wm=fresh()
out["old_score_join"]=TestMockedEndToEndApparatusValidation()._score(l,w0.family_id)
allslots=list({(r.family_id,r.world_id,r.arm,r.query_id) for r in l.solver_calls.values()})
out["clean_full_assignments"]=verdict(l,wm,allslots)
l.oracle_references.clear()
out["old_remove_oracles"]=verdict(l,wm)
l,w0,w1,wm=fresh()
ref=next(iter(l.oracle_references.values()))
l.record_oracle_reference(replace(ref,reference_id="orphan",generation_id="nonexistent"))
out["old_orphan"]=verdict(l,wm)
l,w0,w1,wm=fresh()
n=next(r for r in l.solver_calls.values() if r.arm=="N")
n.ordered_messages[1]["content"]+="\nLEAK "+w0.convention_token
out["old_literal_N"]=verdict(l,wm)
l,w0,w1,wm=fresh()
s=next(iter(l.solver_calls.values()))
s.requested_options=s.effective_options=dict(s.requested_options,temperature=0.9)
out["old_coherent_options"]=verdict(l,wm)
from app.experiments.e5_mini.manifests import resource_budget_manifest as rb
with patch.dict(builder.REQUESTED_OPTIONS,{"temperature":0.99}):
    out["old_budget_after_import"]=rb.verify_against_real_apparatus()
# Invalid content with correct response hash and oracle result.
l,w0,w1,wm=fresh()
victim=next(s for s in l.solver_calls.values() if s.arm=="N" and s.query_kind==QueryKind.RELATED)
expected=next(q["expected_answer"] for q in w0.related_queries if q["query_id"]==victim.query_id)
before=next(r.oracle_result.value for r in l.oracle_references.values() if r.generation_id==victim.generation_id and r.scored_against_world_id==w0.world_id)
for s in l.solver_calls.values():
    if s.generation_id==victim.generation_id: s.response_text=expected; s.response_artifact_hash=sha256_of(expected)
for r in l.oracle_references.values():
    if r.generation_id==victim.generation_id and r.scored_against_world_id==w0.world_id:
        r.oracle_result=OracleResult.PASS; r.oracle_detail="exact match"
out["response_substitution"]={"before":before,"after":"PASS",**verdict(l,wm)}
# Genuine execution count from wrong execution window; no witness forgery.
l,w0,w1,wm=fresh()
mock.reset_solve_witness()
for _ in range(60): mock.mock_solve(mock.CLEAN_STRATEGY,"","unrelated_probe_work",QueryKind.UNRELATED.value)
out["replay_other_execution"]=verdict(l,wm)
# Balanced undeclared retry plus skipped task, same invocation count.
real=mock.mock_solve
calls=[]
attempt=[0]; saved=[None]
def unfaithful(strategy,memory,query,kind):
    attempt[0]+=1
    if attempt[0]==1:
        calls.append(query); real(strategy,memory,query,kind)
        calls.append(query); saved[0]=real(strategy,memory,query,kind)
        return saved[0]
    if attempt[0]==2: return saved[0]
    calls.append(query); return real(strategy,memory,query,kind)
mock.reset_solve_witness()
with patch.object(builder,"mock_solve",side_effect=unfaithful):
    l,w0,w1,wm=_clean_family_ledger()
out["balanced_retry_skip"]={"actual_first_queries":calls[:3],"first_recorded_queries":[r.query_id for r in list(l.solver_calls.values())[:3]],"actual_count":len(calls),**verdict(l,wm)}
finish(out)
```

### Probe batch 2

```python
out={}
# No monkeypatch: one shared SolverStrategy carries P-derived experience into N.
def cached_run(change=False):
    w0,w1=mock.make_synthetic_family(0)
    if change:
        old=w1.convention_token; new="conv_gamma_00"
        w1=replace(w1,convention_token=new,
            teaching_queries=[{k:(v.replace(old,new) if isinstance(v,str) else v) for k,v in q.items()} for q in w1.teaching_queries],
            related_queries=[{k:(v.replace(old,new) if isinstance(v,str) else v) for k,v in q.items()} for q in w1.related_queries])
    retained={"value":None}; reads=[]
    def extract(memory):
        value=mock.CLEAN_STRATEGY.extract_convention(memory)
        if value is not None: retained["value"]=value
        if memory=="": reads.append(retained["value"]); return retained["value"]
        return value
    strategy=mock.SolverStrategy("shared_cache_probe",extract,mock.CLEAN_STRATEGY.choose_action)
    mock.reset_solve_witness(); l=Ledger()
    run_family(l,w0,w1,ArmStrategies(p=strategy,e=strategy,z=strategy,n=strategy))
    wm={(w.family_id,w.world_id):w for w in (w0,w1)}
    n=next(s for s in l.solver_calls.values() if s.arm=="N" and s.query_kind==QueryKind.RELATED)
    return l,wm,n,reads
l,wm,n,reads=cached_run()
r1={"validation":verdict(l,wm),"output":n.response_text,"n_memory_empty":n.memory_field_text=="","reads":reads,"packet":deepcopy(n.ordered_messages)}
l,wm,n,reads=cached_run(True)
out["N_shared_callback_cache"]={"before":r1,"after":{"validation":verdict(l,wm),"output":n.response_text,"n_memory_empty":n.memory_field_text=="","reads":reads},
    "same_N_visible_packet":r1["packet"]==n.ordered_messages}
# Encoded same information in a recorded user packet is not prohibited by literal canaries.
import base64
l,w0,w1,wm=fresh()
n=next(s for s in l.solver_calls.values() if s.arm=="N")
n.ordered_messages[1]["content"]+="\nDecode base64 retained convention: "+base64.b64encode(w0.convention_token.encode()).decode()
out["N_encoded_packet"]=verdict(l,wm)
# Unwitnessed construction: even actual extra construction recorded normally is accepted.
l,w0,w1,wm=fresh()
before=len(l.construction_calls)
builder.construct_arm(l,"P",w0,w0.family_id)
out["extra_constructor"]={"before":before,"after":len(l.construction_calls),**verdict(l,wm)}
# Missing one world reference is masked by generation -> last row collapse.
l,w0,w1,wm=fresh()
to_remove=[k for k,r in l.oracle_references.items() if r.scored_against_world_id=="w0" and any(s.generation_id==r.generation_id and s.arm in ("Z","N") and s.query_kind==QueryKind.RELATED for s in l.solver_calls.values())]
for k in to_remove: del l.oracle_references[k]
out["missing_ZN_world0_scores"]={"removed":len(to_remove),**verdict(l,wm)}
# False-complete empty run and witness reset.
l,w0,w1,wm=fresh()
l.construction_calls.clear();l.solver_calls.clear();l.oracle_references.clear()
mock.reset_solve_witness()
out["empty_after_reset"]=verdict(l,wm)
# Frozen truth can be altered after outputs exist, with no independent pin.
l,w0,w1,wm=fresh()
s=next(s for s in l.solver_calls.values() if s.arm=="P" and s.query_kind==QueryKind.RELATED)
q=next(q for q in w0.related_queries if q["query_id"]==s.query_id)
q["expected_answer"]="new_posthoc_answer"
s.response_text=q["expected_answer"];s.response_artifact_hash=sha256_of(s.response_text)
for r in l.oracle_references.values():
    if r.generation_id==s.generation_id:r.oracle_result=OracleResult.PASS;r.oracle_detail="exact match"
out["posthoc_oracle_response_change"]=verdict(l,wm)
# Honest helper verification itself performs unrelated solves in the witness namespace.
l,w0,w1,wm=fresh(); before=mock.get_solve_witness_count()
from app.experiments.e5_mini.manifests import resource_budget_manifest as rb
verification=rb.verify_against_real_apparatus()
out["helper_pollutes_witness"]={"before":before,"after":mock.get_solve_witness_count(),"budget_verifier":verification,**verdict(l,wm)}
finish(out)
```

### Probe batch 3

```python
out={}
# Counts match even if every ledger record is replayed from a different run.
l,w0,w1,wm=fresh()
saved=deepcopy(l)
other,w02,w12,wm2=fresh()
out["cross_run_ID_collision"]={"construction":len(set(saved.construction_calls)&set(other.construction_calls)),
    "solver_call":len(set(saved.solver_calls)&set(other.solver_calls)),
    "generation":len(saved.distinct_generation_ids()&other.distinct_generation_ids())}
# Witness reset can erase forbidden attempts (no direct private counter write).
real=mock.mock_solve
real(mock.CLEAN_STRATEGY,"","undeclared_first_attempt",QueryKind.RELATED.value)
mock.reset_solve_witness()
l,w0,w1,wm=_clean_family_ledger()
out["reset_erases_prior_attempt"]=verdict(l,wm)
# Whole-cloth tampering with private witness; explicitly weaker threat case.
l,w0,w1,wm=fresh()
for _ in range(3): real(mock.CLEAN_STRATEGY,"","undeclared_extra",QueryKind.RELATED.value)
before=mock.get_solve_witness_count()
mock._witness.count=reconcile(l)["distinct_generations_total"]
out["forged_counter"]={"actual_count_before_forgery":before,**verdict(l,wm)}
# Coherent expectations/data drift: no immutable run-start acceptance hash.
l,w0,w1,wm=fresh()
with patch.dict(checker._EXPECTED_REQUESTED_OPTIONS,{"temperature":0.99}):
    for r in list(l.construction_calls.values())+list(l.solver_calls.values()):
        r.requested_options=r.effective_options=dict(checker._EXPECTED_REQUESTED_OPTIONS)
    out["coherent_checker_expectation_drift"]=verdict(l,wm)
# Budget "freeze" depends on import timing.
with patch.dict(builder.REQUESTED_OPTIONS,{"temperature":0.99}):
    from app.experiments.e5_mini.manifests import resource_budget_manifest as rb
    out["budget_first_import_after_drift"]=rb.verify_against_real_apparatus()
# Negative/malformed evidence cases; never classify a thrown exception as validity.
l,w0,w1,wm=fresh()
r=next(iter(l.oracle_references.values()))
r.oracle_result="NOT_AN_ORACLE_RESULT";r.oracle_detail=""
out["malformed_result_enum"]=verdict(l,wm)
l,w0,w1,wm=fresh()
r=next(iter(l.oracle_references.values()))
r.oracle_result=OracleResult.PASS if r.oracle_result!=OracleResult.PASS else OracleResult.FAIL
out["flipped_outcome"]=verdict(l,wm)
l,w0,w1,wm=fresh()
for s in l.solver_calls.values():
    if s.arm=="N": s.ordered_messages=s.ordered_messages[:1]
out["missing_all_N_user_messages"]=verdict(l,wm)
l,w0,w1,wm=fresh()
# Reordering shared-generation records changes which missing outcome survives.
victim=next(r for r in l.oracle_references.values() if r.scored_against_world_id=="w0" and any(s.generation_id==r.generation_id and s.arm=="N" and s.query_kind==QueryKind.RELATED for s in l.solver_calls.values()))
del l.oracle_references[victim.reference_id]
normal=codes(l,wm)
l.solver_calls=dict(reversed(list(l.solver_calls.items())))
out["record_order_affects_verdict"]={"before":normal,"after":codes(l,wm)}
# Coherent result attribution to a never-assigned query remains undetectable.
l,w0,w1,wm=fresh()
s=next(s for s in l.solver_calls.values() if s.arm=="P" and s.query_kind==QueryKind.RELATED)
g=s.generation_id;old=s.query_id;s.query_id="never-assigned-probe-query"
s.ordered_messages[1]["content"]=s.ordered_messages[1]["content"].replace("related_input_0","never-asked-text")
for r in l.oracle_references.values():
    if r.generation_id==g:r.query_id=s.query_id
out["coherent_unassigned_slot_relabel"]={"old_query":old,"new_query":s.query_id,**verdict(l,wm)}
# Broader runtime flags/body scenarios retaining code-source trust boundary.
l,w0,w1,wm=fresh()
s=next(s for s in l.solver_calls.values() if s.arm=="N")
s.ordered_messages.append({"role":"user","content":"NEW EXTRA CONTEXT: a hidden family precondition observed earlier is true."})
out["N_additional_noncanary_context"]=verdict(l,wm)
# Prefix-collision false positives at a larger but cheap mock scale.
mock.reset_solve_witness()
l=run_mock_e5_mini(101)
wm={(w.family_id,w.world_id):w for pair in mock.make_synthetic_families(101) for w in pair}
out["clean_101_families"]={"codes":codes(l,wm),"solver_invocations":mock.get_solve_witness_count()}
finish(out)
```

## 10. Source identity and integrity

Opening source capture: **2026-09-16T22:52:13.464080+00:00**. Before writing this report, every inspected package source and all three requested reports still matched its opening SHA-256. The tests and attacks ran against these working-tree bytes:

| Path | SHA-256 |
|---|---|
| `app/experiments/e5_mini/__init__.py` | `d226e399f8e16bacda1b7cae0e403152ea8788658ee5e6e5492290baa3d0d098` |
| `app/experiments/e5_mini/accounting.py` | `4c84d683d056a2e36e5232eb69e4a5022395d47388f6298b64fd28e70d207dbf` |
| `app/experiments/e5_mini/applicability.py` | `35ac580bd12bd292859781fb09e2ea86d472d3d1d27b8c32a022d2df97bde91f` |
| `app/experiments/e5_mini/builder.py` | `6b6d99852862b3cc3045bb646dd428d17a5ab4bcb938c348456e6e1ac5af6da0` |
| `app/experiments/e5_mini/checker.py` | `96b0b3d86f5eee1ef77ceb9a872613cb914e22f08c32f7cd3656d241097d59f7` |
| `app/experiments/e5_mini/ledger.py` | `3a5f208135e71f6eb6b26dc069c60775fd00428d8e45530848eb18ae4409d326` |
| `app/experiments/e5_mini/manifests/__init__.py` | `1d57dcc41dcd910d6d0bc52108beebe035325295cf3981ad0410423819292d5a` |
| `app/experiments/e5_mini/manifests/example_synthetic.py` | `5bc9ef4bcce57927020901224ea6e0a0ea095beb679856e35e260ce6af01553e` |
| `app/experiments/e5_mini/manifests/resource_budget_manifest.py` | `0f54146e779e082d14d942624ee055a8b4e9c9a8db3caa2827b0e23bc9f46091` |
| `app/experiments/e5_mini/manifests/role_access_manifest.py` | `9f345b9e460ab0fe47eaaac8013d4a80489f1f5b9aaa80e1f0e510dfb02de788` |
| `app/experiments/e5_mini/manifests/task_manifest.py` | `1dd954ceb71441d44404a6aba604b7dbc93c3114aaa4516c58136a14cfbf22b2` |
| `app/experiments/e5_mini/mock.py` | `175a86f80440683911dd6df4d7ea3ea12be3fb3760d7cc3b51666957efb53849` |
| `app/experiments/e5_mini/oracle.py` | `aff5a996781f79e25be4191167b51e3a9566cf948bc53d1b13604e3303f7f98c` |
| `app/experiments/e5_mini/orchestrator.py` | `097de5700fb12009ab96b40f007b033fcc05bd17b9fbc3f04ea1c449bd2403a2` |
| `app/experiments/e5_mini/sandbox.py` | `b6f0c5c891fbc9207afa20563ac715d5c8cf706b18d52c6be815ce808af68bde` |
| `app/experiments/e5_mini/schema.py` | `fad8e4299800a5f4295f5e78d8549e5f5708d42c84ff14bb2fb893bc24490f9e` |
| `app/experiments/e5_mini/tests/__init__.py` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `app/experiments/e5_mini/tests/test_e5_mini_g0.py` | `ae9e38a36442f6ae3e8ab6266b31486f38341b129159af8fde9fde241704bd82` |
| `app/experiments/e5_mini/tests/test_manifests.py` | `51cfdd1e3fafd782b57165e6ec08a251cb9dc5c4ab46a73f913685d2225c4154` |
| `audits/2026-09-16_e5_mini_g0_repair_and_requalification.md` | `52d9389b1025bcc9e624904acd1a10fa1813f2d77ab020cc190381d6aeb9c7e6` |
| `audits/2026-09-16_e5_mini_codex_reconciliation.md` | `5f7b91326f99a5cba53724d8098c0f3ed2b3c0e66f44974b967c86af07e46f3b` |
| `audits/2026-09-16_e5_mini_g0_codex_adversarial_review.md` | `d4c8c9ea6dd59f46ec8f20692ed09d18e842a5cfb3cf03a79b727a688964ff69` |

Opening HEAD: **`2fba42644c82b9f7096276f4dd338d615cf1bcce`**. Opening full short status: **203 entries**, 27 modified tracked and 176 untracked. No repository AGENTS.md was found by the scoped filename search.

```text
 M CLAUDE.md
 M PENDING_DECISIONS.md
 M app/core/echo_ground_truth.py
 M app/core/liveness_ledger.py
 M app/core/provenance_check.py
 M app/core/river_deliberation.py
 M app/core/self_edit_convergence.json
 M app/core/self_edit_generated.py
 M app/core/self_edit_manager.py
 M app/core/shadow_model.py
 M app/core/snapshot_manager.py
 M app/core/temporal_environment.py
 M app/emergent_scheduler.py
 M app/maintenance/night_cycle.py
 M audits/2026-09-14_tier5_followup_experiment_design.md
 M claude_relay/.last_seen_from_air.json
 M claude_relay/README.md
 M claude_relay/from_m5.md
 M claude_relay/relay.py
 M logs/janitor_report.json
 M research/OPEN_QUESTIONS.md
 M run.py
 M sandbox/safe_exec_wrapper.py
 M sandbox/scripts/temp_self_edit.py
 M scripts/verify_liveness_ledger.py
 M scripts/verify_provenance_check.py
 M staging/self_edit_candidate.py
?? .claude/plans/verified-humming-otter.md
?? .claude/skills/README.md
?? .claude/skills/feral-forensic-audit/SKILL.md
?? .claude/skills/feral-forensic-audit/references/adversarial-checklist.md
?? .claude/skills/feral-forensic-audit/references/evidence-ledger-schema.md
?? .claude/skills/feral-forensic-audit/references/evidence-vocabulary.md
?? .claude/skills/feral-forensic-audit/references/integrity-and-safety.md
?? .claude/skills/feral-forensic-audit/references/report-template.md
?? .claude/skills/feral-independent-review/SKILL.md
?? .claude/skills/feral-independent-review/references/reviewer-checklist.md
?? app/experiments/e5_mini/__init__.py
?? app/experiments/e5_mini/accounting.py
?? app/experiments/e5_mini/applicability.py
?? app/experiments/e5_mini/builder.py
?? app/experiments/e5_mini/checker.py
?? app/experiments/e5_mini/ledger.py
?? app/experiments/e5_mini/manifests/__init__.py
?? app/experiments/e5_mini/manifests/example_synthetic.py
?? app/experiments/e5_mini/manifests/resource_budget_manifest.py
?? app/experiments/e5_mini/manifests/role_access_manifest.py
?? app/experiments/e5_mini/manifests/task_manifest.py
?? app/experiments/e5_mini/mock.py
?? app/experiments/e5_mini/oracle.py
?? app/experiments/e5_mini/orchestrator.py
?? app/experiments/e5_mini/sandbox.py
?? app/experiments/e5_mini/schema.py
?? app/experiments/e5_mini/tests/__init__.py
?? app/experiments/e5_mini/tests/test_e5_mini_g0.py
?? app/experiments/e5_mini/tests/test_manifests.py
?? app/experiments/real_trace_f2_provenance/_scratch/river_brain_scratch.pkl
?? app/experiments/real_trace_f2_provenance/_scratch/river_brain_scratch.pkl.lock
?? app/experiments/task_type_ground_truth/__init__.py
?? app/experiments/task_type_ground_truth/blind_label.py
?? app/experiments/task_type_ground_truth/dataset.py
?? app/experiments/task_type_ground_truth/evaluate.py
?? app/experiments/task_type_ground_truth/gold_labels.jsonl
?? app/experiments/task_type_ground_truth/gold_labels_llm.jsonl
?? app/experiments/task_type_ground_truth/schema.py
?? audits/2026-09-07_authority_boundary_deliberateness.md
?? audits/2026-09-07_consequence_authority_map.md
?? audits/2026-09-07_consequential_learning_loop_design.md
?? audits/2026-09-07_consequential_loop_validation.md
?? audits/2026-09-07_missing_primitive_determination.md
?? audits/2026-09-07_post_wake_observation.md
?? audits/2026-09-07_shadow_treatment_harness_archaeology.md
?? audits/2026-09-07_temporal_authority_graph.md
?? audits/2026-09-08_adversarial_epistemic_pressure.md
?? audits/2026-09-08_echo_blind_self_model.md
?? audits/2026-09-08_echo_self_model_claims.json
?? audits/2026-09-08_echo_self_model_discrepancy_report.md
?? audits/2026-09-08_echo_self_model_revision.md
?? audits/2026-09-08_epistemic_arbitration_FINAL.md
?? audits/2026-09-08_epistemic_arbitration_baseline.md
?? audits/2026-09-08_epistemic_arbitration_design.md
?? audits/2026-09-08_epistemic_arbitration_experiments.md
?? audits/2026-09-08_epistemic_arbitration_pipeline.md
?? audits/2026-09-08_epistemic_arbitration_validation.md
?? audits/2026-09-08_epistemic_boundary_imagination_experiment.md
?? audits/2026-09-08_epistemic_contamination_recovery_forensics.md
?? audits/2026-09-08_epistemic_interaction_and_relay_forensics.md
?? audits/2026-09-08_epistemic_transition_mechanism_forensics.md
?? audits/2026-09-08_evidence_arbitration_and_sensory_ingestion_forensics.md
?? audits/2026-09-08_exhaustive_sensor_contract_experiment.md
?? audits/2026-09-08_git_readonly_self_history_investigation.md
?? audits/2026-09-08_mechanism_c_FINAL.md
?? audits/2026-09-08_mechanism_c_experiments.md
?? audits/2026-09-08_mechanism_c_post_update_replication.md
?? audits/2026-09-08_mechanism_d_independent_regrounding.md
?? audits/2026-09-08_persistent_self_model_DESIGN.md
?? audits/2026-09-08_persistent_self_model_inventory.md
?? audits/2026-09-08_phase10_retest_after_revision.md
?? audits/2026-09-08_phase8_adversarial_testing.md
?? audits/2026-09-08_self_model_causal_design.md
?? audits/2026-09-08_self_model_contradiction_handling.md
?? audits/2026-09-08_self_model_correction_path.md
?? audits/2026-09-08_self_model_evidence_hierarchy.md
?? audits/2026-09-08_self_model_experiment_plan.md
?? audits/2026-09-08_self_transparency_audit_FINAL.md
?? audits/2026-09-08_self_transparency_audit_experimental_boundary.md
?? audits/2026-09-08_sensory_gate_fix_and_provenance_forensics.md
?? audits/2026-09-08_transparency_metrics_and_epistemic_boundary.md
?? audits/2026-09-08_verified_external_architecture.md
?? audits/2026-09-09_autonomous_investigation_liveness_recovery_forensics.md
?? audits/2026-09-09_autonomous_scheduler_restart_temporal_lifecycle_forensics.md
?? audits/2026-09-09_codex_headless_subscription_independence_proof.md
?? audits/2026-09-09_epistemic_transition_mechanism_forensics.md
?? audits/2026-09-09_four_agent_collaboration_architecture_audit.md
?? audits/2026-09-09_independent_review_epistemic_arbitration_findings.md
?? audits/2026-09-09_mission32_task_type_classifier_causal_audit.md
?? audits/2026-09-09_mission32_task_type_classifier_causal_audit_evidence_ledger.json
?? audits/2026-09-09_mission33_independent_ground_truth_audit.md
?? audits/2026-09-09_mission34_task_type_experiment_run.md
?? audits/2026-09-09_mission35_task_type_experiment_llm_judge_rerun.md
?? audits/2026-09-09_open_ended_learning_discovery.md
?? audits/2026-09-09_openai_codex_local_agent_architecture_investigation.md
?? audits/2026-09-09_os_level_stdin_fd0_implementation.md
?? audits/2026-09-10_epistemic_invocation_and_provenance_isolation.md
?? audits/2026-09-10_phase2_provenance_reconciliation.md
?? audits/2026-09-10_research_arc_provenance_audit.md
?? audits/2026-09-11_authority_evidence_separation_forensics.md
?? audits/2026-09-11_authority_free_ladder_causal_isolation.md
?? audits/2026-09-11_false_verification_trap_replication.md
?? audits/2026-09-11_feralecho_unresolved_defect_audit.md
?? audits/2026-09-11_provenance_implementation_boundary_audit.md
?? audits/2026-09-11_provenance_leaf_primitives_validation.md
?? audits/2026-09-11_read_only_git_provenance_design.md
?? audits/2026-09-11_read_only_provenance_interface_design.md
?? audits/2026-09-11_research_state_consolidation.md
?? audits/2026-09-11_three_layer_provenance_reconciliation.md
?? audits/2026-09-11_verification_and_level_7_5_8_feasibility.md
?? audits/2026-09-12_provenance_layer2_boundary_review.md
?? audits/2026-09-13_capability_benchmark_harness_phase0.md
?? audits/2026-09-13_council_correctness_investigation.md
?? audits/2026-09-13_cross_layer_reconciliation_boundary.md
?? audits/2026-09-13_layer3_runtime_provenance_boundary.md
?? audits/2026-09-13_observation_time_contract_research.md
?? audits/2026-09-13_observation_time_enforcement_research.md
?? audits/2026-09-13_observation_time_placement_architecture.md
?? audits/2026-09-13_provenance_layer2_red_team.md
?? audits/2026-09-13_reconciliation_epistemic_taxonomy_and_arbitration_scoping.md
?? audits/2026-09-13_reconciliation_implementation.md
?? audits/2026-09-13_reconciliation_implementation_design.md
?? audits/2026-09-13_reconciliation_primitive_architecture.md
?? audits/2026-09-13_shadow_model_retirement.md
?? audits/2026-09-13_shadow_retirement_documentation.md
?? audits/2026-09-13_tier5_council_correctness_retest.md
?? audits/2026-09-14_core_task_misclassification_council_synthesis_trace.md
?? audits/2026-09-14_task_type_behavioral_experiment.md
?? audits/2026-09-14_task_type_downstream_behavior_archaeology.md
?? audits/2026-09-14_tier5_retest_adversarial_audit.md
?? audits/2026-09-15_codex_michelangelo_blind_spot_discovery.md
?? audits/2026-09-15_codex_task_type_independent_review.md
?? audits/2026-09-15_task_type_experiment_reconciliation.md
?? audits/2026-09-16_capability_growth_reconciliation.md
?? audits/2026-09-16_codex_capability_ceiling_adversarial_review.md
?? audits/2026-09-16_e5_mini_adversarial_preimplementation_review.md
?? audits/2026-09-16_e5_mini_codex_reconciliation.md
?? audits/2026-09-16_e5_mini_final_adjudication.md
?? audits/2026-09-16_e5_mini_g0_codex_adversarial_review.md
?? audits/2026-09-16_e5_mini_g0_mock_implementation.md
?? audits/2026-09-16_e5_mini_g0_repair_and_requalification.md
?? audits/2026-09-16_e5_mini_manifests_design_and_hostile_review.md
?? audits/2026-09-16_feralecho_zero_cost_capability_ceiling.md
?? audits/tier3_apparatus/dev_sanity_results_REISOLATED_RERUN_20260909.jsonl
?? audits/tier3_apparatus/heldout_results_REISOLATED_RERUN_20260909.jsonl
?? audits/tier5_retest/archive/SLEEP_INTERRUPTED_20260913_progress.txt
?? audits/tier5_retest/archive/SLEEP_INTERRUPTED_20260913_results.jsonl
?? audits/tier5_retest/tier5_retest_progress.txt
?? audits/tier5_retest/tier5_retest_results.jsonl
?? audits/tier5_retest/tier5_retest_task_pool.hash.txt
?? audits/tier5_retest/tier5_retest_task_pool_FROZEN.py
?? claude_relay/.last_seen_from_air_hub.json
?? claude_relay/facts_m5.jsonl
?? codex_relay/README.md
?? codex_relay/relay.py
?? codex_relay/test_relay.py
?? hub/README.md
?? hub/check_hub.py
?? hub/notes.jsonl
?? hub/notes.py
?? hub/status.jsonl
?? research/COLLABORATOR_SUBSTITUTION_CODEX_PILOT.md
?? research/FRONTIER_COLLABORATOR_REGULATORY_DEPENDENCY.md
?? research/MACOS_AUTHORIZATION_EVIDENCE_ARCHEOLOGY.md
?? research/MEMORY_PRESERVATION_ARCHAEOLOGY.md
?? research/MEMORY_PRESERVATION_SET_AUDIT.md
?? research/OPOSSUM_MODE_BRAINSTORM.md
?? research/STRATEGIC_FRONTIER_RESILIENCE.md
?? research/TWO_NODE_IDENTITY_PRESERVATION_RELAY_ARCHAEOLOGY.md
?? scripts/run_tier3_reisolated_rerun.py
?? scripts/run_tier5_retest.py
?? scripts/task_type_behavioral_experiment.py
?? scripts/task_type_behavioral_experiment_analyze.py
?? scripts/task_type_behavioral_experiment_judge.py
?? scripts/tier5_retest_task_pool.py
?? scripts/verify_select_best_fallback_candidate.py
```

Temporary analysis roots, all removed:

- `/private/tmp/feralecho-g0r-codex-lf738koj` — 66-test suite; one permitted sacrificial write.
- `/private/tmp/feralecho-g0r-codex-bk9huo3y` — regression and execution/response probes.
- `/private/tmp/feralecho-g0r-codex-hboyhfpu` — shared-state N isolation and partial-outcome probes.
- `/private/tmp/feralecho-g0r-codex-eeh0tgpa` — identity, freeze, malformed evidence and ordering probes.

The three adversarial batches recorded no file writes or prohibited audit events and no loaded `app.core`, `ollama` or `faiss` modules. The audit hook is a Python-level precaution, not a kernel-sandbox claim. No live process was queried, attached to, signaled, stopped or restarted. Ordinary analysis interpreters were used solely for the authorized mock tests.

Closing verification: **2026-09-16T23:02:15.872522+00:00**.

- Closing HEAD: **`2fba42644c82b9f7096276f4dd338d615cf1bcce`**, unchanged from opening.
- Closing full short status: **204 entries** (27 modified tracked, 177 untracked).
- The full closing status is exactly the opening block plus **`?? audits/2026-09-16_e5_mini_g0_codex_requalification_attack.md`**. No opening status entries were removed or changed.
- All **19 package Python files and three requested reports** remained byte-identical to their opening hashes. No concurrent changes to those reviewed sources were observed.
- All four temporary analysis roots were checked absent.
- Mission-caused repository delta: **only this report**. No implementation fix, production change, Git mutation, model execution, protected-state mutation or live-process alteration was performed.

This closing record was then added to the authorized report itself; that does not change the report's untracked Git status.

Git status alone cannot establish byte integrity of already-dirty/untracked files; the separate source-hash comparison addresses the inspected implementation and reports. No full snapshot of live production stores was taken, so ordinary unrelated background writes are not ruled out. The integrity claim concerns this mission's actions, not all concurrent activity on the machine.

## 11. Required final decisions

- **Old-attack regression results:** the targeted 272/240, cross-arm join, complete outcome deletion, dangling-reference, literal N-message leak, coherent record-options drift and post-import shared-options cases now behave correctly in fresh tests. These are narrow closures; the full former findings were not all repaired.
- **Novel attacks attempted:** balanced retry/omission, shared-state N leakage, response substitution, cross-window replay, partial paired-world deletion, order sensitivity, encoded/non-canary context, constructor overrun, malformed outcomes, coherent truth mutation, import-order drift, reset/forgery, run-ID collision and larger-index token overlap. Exact probe bodies and outcomes are above.
- **Successful counterexamples:** A1–A5 each yield valid-looking results despite materially invalid execution or evidence. The strongest are balanced retry/omission and actual P-to-N retained-state transfer, which do not require modifying the validator or witness.
- **Execution-witness independence:** sufficient to observe a narrow unbalanced call-count regression; insufficient to identify, bind or isolate executions. A trustworthy count is not a trustworthy execution transcript.
- **N isolation:** not established; shared callback state transferred teaching-derived information into N while both validators passed.
- **Frozen-versus-runtime truth:** not established; no compulsory independently admitted run specification is bound to consumed inputs, execution events and output evidence.
- **Strongest remaining weakness:** no enforceable correspondence between the frozen assignment, actual information/computation path, and accepted response/result records. Internal consistency plus matching totals permits materially false experiment histories.
- **G0 verdict: NOT QUALIFIED.** The 66 passing tests do not overcome reproducible counterexamples to the qualification contract.
- **E5: NO-GO.** No real E5, transfer, learning or accumulation has been demonstrated by this review or by G0.
- **Exact next gate:** repair only the isolated mock run/attempt collector, information boundary and mandatory close validator described in §8; requalify against A1–A5 and the retained regressions. Keep production and real inference outside that work. G0 success would license only the bounded mocked measuring apparatus, with live execution admission and the scientific E5/E8 questions still separate.
