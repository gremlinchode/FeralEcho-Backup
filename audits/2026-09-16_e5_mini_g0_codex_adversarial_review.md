# E5-mini G0 — independent Codex adversarial review

Date: 2026-09-16. Scope: the implemented mocked measuring apparatus, its tests, and preparation for a frozen E5-mini pilot. No real E5 was executed.

## 1. Verdict

**G0: NOT QUALIFIED. Real E5: NO-GO.**

**OBSERVED:** All **52 supplied G0 tests pass**, without skips. Thirty methods are named for the thirty required anomaly classes. Those facts do **not** establish thirty meaningful detectors, correct outcome attribution, or faithful generation accounting.

**REPRODUCED:** The current apparatus can accept an N user message containing teaching information, a ledger with every oracle result removed, a fabricated extra generation, and an UNKNOWN result changed to PASS. Its ordinary four-family mock run invokes the solver function **272 times** while reporting **240 distinct solver generations**. Its scenario score helper combines oracle results from different arms.

The disclosed #17 defect is **stale relative to the opening working-tree source**: requested/effective options mismatch detection is already integrated into the main checker for both construction and solving. I did not implement that fix. An independent frozen-options check is still absent.

These findings justify repairing and requalifying the small mock apparatus. They do not justify production changes, a new architecture review cycle, or real inference. “G0 QUALIFIED WITH CONDITIONS” would understate defects in the very outcomes and information paths G0 is meant to validate.

Evidence terms used here: **OBSERVED** means directly read or measured; **REPRODUCED** means demonstrated by a fresh isolated mock probe; **SUPPORTED** combines primary evidence; **RISK** identifies an unexercised possibility. No mock response is evidence that Echo learned.

## 2. Observation boundary and method

Opening HEAD: `2fba42644c82b9f7096276f4dd338d615cf1bcce`. Opening full short status contained **196 entries: 27 modified tracked paths and 169 untracked paths**. The E5-mini implementation was untracked. HEAD alone therefore does not identify the reviewed source.

I read Claude's implementation report, the E5-mini package, both empty parent package initializers, and the relevant final-adjudication requirements. I inspected imports before executing tests. I did not import Echo, RiverBrain, Ollama, FAISS, production configuration, or a production experiment runner. No pickles or other stateful production objects were deserialized.

Execution used isolated `python3 -B -I -S` processes with the repository added explicitly to Python's import path. The supplied unittest module was loaded directly, avoiding pytest/plugin discovery, bytecode writes, and site startup. A Python audit hook rejected writes outside a dedicated temporary directory and rejected socket, subprocess, shell, fork/exec, and process-signal audit events. This is a review-time tripwire, not a claim of kernel containment.

The original suite made one permitted sacrificial file write. Additional probes mutated only freshly created Python objects or process-local module attributes; patches ended with their analysis processes. No inference transport, candidate-generated code, shell payload in a fixture, or live-process control operation was executed. Source inspection and the recorded audit events support this narrow claim. They do not establish that arbitrary future candidate execution would be contained.

All four temporary analysis roots were removed:

- `/private/tmp/feralecho-g0-codex-slbm4757` — supplied 52-test run.
- `/private/tmp/feralecho-g0-codex-53vrefqg` — checker/accounting/outcome probes.
- `/private/tmp/feralecho-g0-codex-kckzn1gw` — lineage, containment and manifest probes.
- `/private/tmp/feralecho-g0-codex-pdtlzjir` — newer manifest tests and adversarial checks.

**Concurrent work:** manifest files changed and new manifest files appeared during this review, without writes by this mission. I re-read and checked a stable snapshot of those additions. The original core implementation and original G0 tests remained unchanged. This report distinguishes current manifest behavior from superseded drafts. The newly appearing `audits/2026-09-16_e5_mini_manifests_design_and_hostile_review.md` was not used as authority or necessary evidence.

Only this new report was written to the repository by this mission. I chose not to edit implementation: #17's described fix already exists, and the other findings require a coherent repair followed by fresh qualification.

## 3. What actually passed

| Suite/group | Tests run | Failure/error/skip | What the result establishes |
|---|---:|---|---|
| Clean-path tests | 3 | 0/0/0 | The selected assertions hold; only the one-family clean case is required to have no checker violations. |
| Planted-anomaly methods | 30 | 0/0/0 | Every method passes its written assertions, including assertions that do not exercise a detector. |
| Accounting tests | 2 | 0/0/0 | Deduplication of supplied generation labels works on selected records. |
| Mocked end-to-end scenarios | 15 | 0/0/0 | Selected synthetic relationships/assertions hold, subject to the broken score join. |
| Ledger insertion tests | 2 | 0/0/0 | Duplicate construction/solver call IDs are rejected through the tested insertion methods. |
| **Original G0 suite** | **52** | **0/0/0** | **Independently reproduced in 0.017 seconds of unittest-reported time.** |
| Concurrently added manifest suite | 12 | 0/0/0 | Additional design/helper checks pass; independently run separately in 0.011 seconds. |

The 12 later tests are not retroactive evidence for Claude's original 52-test result. I did not combine them into a claim that “64 tests prove qualification.” Claude's report also describes 19 scenarios; the implemented end-to-end unittest class has 15 methods.

Primary locations: `tests/test_e5_mini_g0.py:51,64,92,452,488,634`; `tests/test_manifests.py`. All paths in this report beginning with a Python filename refer to `app/experiments/e5_mini/` unless otherwise stated.

## 4. Critical findings

### F1 — Reuse is a label, while solving happens again

**REPRODUCED; qualification blocker.**

In `builder.py:149–156`, both branches call `mock_solve`. The reuse branch does not retrieve a retained response. Determinism makes the regenerated text appear reused. `orchestrator.py:85–101` assigns the same generation ID to the second invocation; `accounting.py:10–43` counts unique labels rather than observing invocations.

A wrapper around the actual mock solver counted 272 invocations at four families. No real model was called: these are deterministic surrogate invocations. Nevertheless, this violates the mock contract intended to establish one generation with two oracle references.

| Quantity, four families | Frozen final-adjudication design | Current run |
|---|---:|---:|
| Construction calls | 20: P8/E8/Z4/N0 | 20 |
| Distinct solver responses intended | 240: P80/E80/Z40/N40 | 240 generation labels |
| Actual solver-function invocations | 240 | **272** |
| Construction + solver invocation count | 260 | **292 surrogate calls**, including 20 constructions |
| Reported total “model calls” | 260 | **260** |
| Primary arm/world/query scoring rows | 320 | **272 references** |
| Oracle UNKNOWN from absent paired fixtures | 0 on complete fixtures | **32** |
| Clean condition violations | 0 | **48** |

The 48 missing scoring rows are Z/N's six negative queries per family, omitted for world 1. Scoring an identical negative response twice would not provide two independent observations; either a complete 320-row view or an explicitly frozen normalized equivalent is defensible. Silently changing the declared scoring contract is not.

The missing negative references are separate from the 32 unintended UNKNOWN results. The latter occur on related tasks and invalidate the intended paired-world diagnostic.

**Additional reproduction:** changing one reused Z row's generation ID to a new string increases reported calls from 65 to 66 in the one-family run, with **zero checker violations**. Conversely, keeping a shared generation ID while changing its response, response hash and actual user message is also accepted. Thus labels can inflate or conceal cost and generation counts.

Test #18 at `tests/test_e5_mini_g0.py:290` asserts that the fabricated label increases the count. It never requires the main checker to reject the fabrication. Observing that corrupted accounting changed is not detecting and invalidating corrupted accounting.

**Minimum repair:** make the trusted mock transport allocate one immutable generation record per invocation. Reuse must fetch that record without invoking the solver. Store scoring references separately, validate their complete expected set, and bind every reference to an existing generation and logical query. Charge one generation once; charge actual retries if they occur and invalidate the forbidden retry. Verify this using an invocation spy and a deliberately stateful mock whose response changes on every call.

### F2 — Paired-world oracle lookup and scenario attribution are wrong

**REPRODUCED; qualification blocker.**

Fixture query text is shared between worlds, but query IDs contain `w0` or `w1`. The shared-arm loop sends a world-0 query ID to the world-1 oracle. `oracle.py:16–23` correctly returns UNKNOWN because that fixture does not exist. Tests asserting that Z/N cannot pass both worlds succeed partly because world 1 is unscorable, not because the apparatus correctly compares mutually incompatible answers.

The scenario helper `tests/test_e5_mini_g0.py:488–498` joins oracle references using query ID and world, **without generation ID or arm**. Different arms solve the same queries, so their outcomes mix.

Fresh one-family default run, related-task outcomes:

| Arm | Correct generation-linked outcomes | Suite helper's reported score |
|---|---|---:|
| P | 8 PASS, 0 FAIL, 0 UNKNOWN | 0.3333 |
| E | 0 PASS, 8 FAIL, 0 UNKNOWN | 0.3333 |
| Z | 0 PASS, 4 FAIL, 4 UNKNOWN | 0.1667 |
| N | 0 PASS, 4 FAIL, 4 UNKNOWN | 0.1667 |

These are synthetic strategy outcomes, not real treatment effects. They show that the helper cannot distinguish even the programmed P/E difference. The “P beats E” test at line 551 uses `assertGreaterEqual`, allowing a tie to satisfy its scenario.

**Minimum repair:** separate world-independent logical query identity from scoring-world identity. Join through run + generation + logical query + oracle world + score purpose. Require exactly correct per-arm outcome tables for asymmetric synthetic cases, plus exact UNKNOWN/incomplete counts. Do not use “not both PASS” as sufficient evidence of a valid paired test. An independently implemented summarizer must consume trusted results and retain UNKNOWN as its own state.

### F3 — The checker does not establish the actual information path

**REPRODUCED; qualification blocker.**

The builder records a proposed message list but calls the mock with separate `memory_text`, `query_text` and strategy arguments. The mock does not consume the recorded full message packet. The solver's user message literally contains `SPEC: (public)`, not the public specification (`builder.py:142–156`).

The checker validates selected metadata fields and system messages. It does not validate the full user packet against its permitted information projection.

These mutations all produced an empty violation list:

- N's user message contains a teaching convention and additional TOOL-LIST text while N's memory metadata stays empty.
- E's world-0 solver coherently points to the world-1 E parent, artifact and memory.
- E's teaching-input hash changes and its experience-empty flag becomes true.
- A response hash becomes invalid and the memory artifact ID becomes unrelated.
- Constructor identity, public-spec hash, system-instruction hash and output cap change.

The N probe proves failure to validate the recorded model-visible payload. It is not a claim that a real model consumed the leak during this review. TOOL-LIST text in a user message is also not identical to production system-role TOOL-LIST delivery; both illustrate why the complete packet matters.

`checker.py:147` imports `SYSTEM_INSTRUCTION` from the builder, contradicting its own explicit independence requirement. Changing the builder constant and every recorded system message together passes. Independence need not mean duplicated code everywhere; it does require an expected packet/allowlist pinned outside the producer's mutable result.

More seriously, `builder.py:58–59` inserts `world.convention_token` directly into the teaching packet. It does not derive that value exclusively from allowed teaching observations. Removing the secret from the observations still leaves it in P's constructed artifact, and the checker accepts it because `checker.py:77` repeats the same privileged-field construction.

This is a **mock information-boundary defect**, not proof of real experimental leakage. A constructor adapter receiving the entire oracle-bearing world object is precisely the boundary that qualification should challenge.

**Minimum repair:** constructors receive restricted immutable public/teaching projections, never the whole oracle fixture. The trusted mock transport consumes and records the same serialized packet. The checker reconstructs the allowed packet from independently frozen inputs, including message count/order/content, public spec, teaching projection, arm/world lineage, artifact ID/hash and generation settings. Harmless output guessing must not itself be classified as evidence of a forbidden read.

### F4 — A clean verdict can coexist with no outcomes or altered outcomes

**REPRODUCED; qualification blocker.**

`checker.py:208–236` accepts optional assignments. Its “completeness” check builds an oracle-reference set but never uses it; it checks solver rows instead.

Consequently:

- An empty ledger passes if no expected slots are supplied.
- Deleting **all oracle references** passes even when all expected solver slots are supplied.
- An oracle reference to a nonexistent generation passes.
- Duplicating a Z scoring reference for the same world/query passes.
- Changing a stored UNKNOWN to PASS passes.
- Calling `check_ledger` leaves `ledger.condition_validity` empty despite its docstring claiming to populate it.

The distinction is not that every incomplete run should throw an exception. Incomplete runs must remain visible and have an explicit non-qualified close state. An empty list of violations must not certify a completed experiment when assignment/outcome evidence is missing.

**Minimum repair:** a mandatory sealed assignment ledger, explicit start/end states, generation/reference referential integrity, unique expected scoring keys, independently recomputed oracle results, and a completeness check over outcomes and required artifacts. No clean close on partial evidence. Retain failures and UNKNOWN in fixed denominators.

### F5 — “Actual dispatch” is asserted, not observed end to end

**REPRODUCED; qualification blocker for applicability claims.**

`ApplicabilityRunner` can actually invoke a supplied entrypoint and record it, but the orchestrator does not use it. Patching its dispatch method to fail still allows the full one-family run to complete.

`builder.py:161–168` copies the declared action into the dispatched field, or calls the solver again to synthesize that field for a test override. `orchestrator.py:119` then scores negative controls from the declared action. `oracle.py:25` has no final-response argument.

Test #21 exercises a real standalone mismatch, but its integrated branch condition is false for the chosen fixture, so the checker assertion inside that branch does not run.

Correct negative-task behavior requires both “did not incorrectly invoke FAMILY” and the prescribed correct alternative outcome. Saying GENERAL is insufficient evidence that general execution solved the task. Keep applicability and task correctness as separate metrics.

**Minimum repair:** wire the mock runner into the actual path; record the entrypoint it invokes independently of the declaration. Score dispatch and completion separately. Include deliberate declaration/dispatch mismatch, correct GENERAL label with wrong result, malformed action, and valid abstention cases.

### F6 — Clean inputs fail, and fixture names substitute for general validation

**REPRODUCED / OBSERVED.**

Every synthetic family reuses the strings `conv_alpha` and `conv_beta` (`mock.py:42`). The checker declares any other world's convention found in an artifact contaminated, including the identical legitimate convention in another family. The four-family clean run therefore has **48 CROSS_WORLD_CONTAMINATION violations**. The full-scale supplied test checks counts, not a zero-violation verdict.

An opposite-world **diagnostic** score for an existing P output also triggers P_E_GENERATION_REUSED. Fresh P solving for each assigned world is required; rescoring an existing response against an alternative oracle is not another solve. Primary scoring and counterfactual diagnostics need distinct purposes and admissible reference rules.

Fixtures expose labels such as `near_match` and `violates_type`, which built-in strategies recognize. This is acceptable for sacrificial plumbing checks, but does not establish discrimination on differently expressed controls. Four named recipe classes are not four independent algorithms if the same string recipe handles all four.

The leak checker searches constructor **output** for expected-answer substrings. It can miss an unauthorized read whose output does not repeat the answer, and can falsely accuse a legitimate independently derived answer. Access evidence and prohibited input bytes are the primary controls; output canaries are supplementary.

### F7 — Record identity, immutability and containment remain incomplete

**REPRODUCED:** Ledger records remain externally mutable after insertion. Altering a borrowed solver object changes the ledger without a violation. Separate Ledger instances generate colliding IDs because their counters restart. Existing duplicate-insertion tests do not cover mutation through references, cross-run merging, duplicate artifact IDs, or oracle-reference identity collisions.

**REPRODUCED:** The static escalation scanner misses the inert text `from subprocess import Popen\nPopen(['unused'])`, while flagging a benign comment containing `subprocess.Popen`. No such command was executed.

`sandbox.py:56–64` returns a literal true flag plus a message asserting use of the supplied oracle result. Test #23 never attempts to change an evaluator-owned outcome through a candidate-access boundary. The result is not a containment test.

`guarded_write` genuinely rejects the tested path outside scratch. It is a helper, not an enforced restriction on other file-opening paths. Hard-link and check/use races are untested risks; this review did not create them. A text-only mock need not implement a production sandbox, but must not claim it qualified candidate execution.

**Minimum repair:** immutable snapshots at record insertion, run-scoped IDs, schema/foreign-key validation and explicit append/close semantics. Keep candidate content inert for the next G0 gate. Use sacrificial access fixtures to test actual allowed/denied reads and writes; require a separate execution-isolation gate before any future untrusted code or private inference.

## 5. Thirty-anomaly semantic audit

“Partial” means useful narrow evidence exists but the named violation can escape in an equivalent form. “Not established” means the test does not exercise the claimed end-to-end property. These are not thirty independent probabilistic coverage measurements.

| # | Required class | What the test actually establishes | Adjudication |
|---:|---|---|---|
| 1 | P artifact in N | Nonempty N memory metadata is rejected. Actual N user-payload leakage passes. | Partial. |
| 2 | Private convention in Z | Literal secret in Z artifact is rejected. Input access is not observed; guesses can falsely trigger. | Partial. |
| 3 | Extra P construction | A single record with attempt_index=1 is rejected. An actual second construction at index 0 passes. | Partial; cardinality missing. |
| 4 | Hidden retry | Another nonzero-index flag, not detection of an unlabelled retry invocation. | Partial. |
| 5 | Teaching-based Z selection | Self-reported semantic_feedback_exposure=true is rejected. No selection/access history measured. | Partial. |
| 6 | Wrong teaching world | P's teaching hash is checked against a privileged-field reconstruction. E's equivalent mismatch passes. | Partial. |
| 7 | Wrong family/arm parent | Selected parent identity mismatch is rejected. | Useful narrow detector; extend to coherent lineage substitutions. |
| 8 | Stale artifact | Referenced parent's changed text with unchanged hash is rejected. | Useful narrow detector; durable freeze/reload not established. |
| 9 | Changed artifact after reload | Computes two unequal hashes and asserts inequality; no reload/validator path. | **Not established.** |
| 10 | Missing assigned slot | Optional expected solver slot can fail. Removing every oracle result passes. | Partial. |
| 11 | UNKNOWN coerced to PASS | Oracle returns UNKNOWN for nonexistent query; no downstream coercion is planted. Actual coercion passes. | **Not established.** |
| 12 | Partial run called complete | Supplies an absent expected query, not a complete run-close protocol. | Partial. |
| 13 | Forged clean close | Forged text does not drive a real close; reuses missing-slot assertion. | **Not established as close validation.** |
| 14 | Hidden system text | Changed system message fails against builder's current constant. Producer/expected common drift passes. | Partial. |
| 15 | TOOL-LIST/tool injection | Selected flags/system text fail. No independent transport receipt; full payload not checked. | Partial. |
| 16 | Unexpected council/synthesis | True flags fail. Undeclared extra mock invocation is not counted. | Partial. |
| 17 | Changed generation options | **Main checker** rejects requested/effective mismatch for constructor and solver. Coherent drift passes. | **Integrated narrow detector; frozen-policy binding missing.** |
| 18 | Falsely double-counted reuse | Asserts the fabricated generation ID increases counts. Checker accepts it. | **Not established; accounting is corruptible.** |
| 19 | Always FAMILY | Negative oracle fails the declared FAMILY choice. | Narrow dispatch-label diagnostic; actual dispatch/completion incomplete. |
| 20 | Always ABSTAIN | Positive exact-output oracle fails missing completion. | Useful narrow outcome diagnostic. |
| 21 | Declaration differs from dispatch | Standalone runner catches mismatch; integrated conditional assertion is not reached. | Partial; end-to-end not established. |
| 22 | Forged PASS marker | Exact related-answer oracle ignores a bogus PASS string. | Useful narrow detector. |
| 23 | Candidate modifies oracle result | Helper returns true and describes supplied result; no tampering boundary attempted. | **Not established.** |
| 24 | Cross-arm read | Changes memory metadata, not an attempted read through a constrained capability. | Partial. |
| 25 | Withheld test read | Output contains a known answer string; no read is observed. | Partial; both false positives and false negatives possible. |
| 26 | Out-of-scratch write | Real sacrificial allowed/denied writes through guarded_write. | Valid helper test, not global containment. |
| 27 | Subprocess escape | Regex detects one literal string; aliased inert text bypasses. | **Not established as process isolation.** |
| 28 | Secret via ID | Literal convention token in selected IDs is detected. Actual prompt leakage passes. | Partial. |
| 29 | Paired packets not identical | Direct assertNotEqual on changed fixture, without main checker. Paired-spec change passes checker. | **Not established.** |
| 30 | Valid hash, wrong lineage | Inconsistent memory text catches the planted case. Coherent E world substitution passes. | Partial. |

Therefore **30/30 named test methods pass; 30/30 anomaly classes are not meaningfully qualified**. A check need not reside in one giant function, but must be wired into the qualification path, return a machine-enforced invalid outcome, and be tested with the equivalent violation rather than merely described.

## 6. #17 disposition and smallest correct repair

The implementation report at lines 259–266 and 340 describes a direct-assertion-only limitation. Opening source already contains:

- `checker.py:59`: constructor requested-options versus effective-options mismatch.
- `checker.py:99`: corresponding solver check.
- `tests/test_e5_mini_g0.py:259–287`: integrated clean baseline and both drift cases.

**Disposition:** the disclosed integration gap is **already closed in the reviewed working tree**. Do not reimplement or claim credit for it. If it were still assertion-only, full G0 qualification would be premature.

The smallest remaining options repair is to give the validator an independently pinned configuration profile and require:

1. Recorded request equals the assigned profile for that role/arm.
2. Reported effective settings equal the supported expected effective settings, with explicit treatment of unavailable effective values.
3. Keys, types, bounds and supported options are validated; missing/unknown required settings are invalid, not silently assumed.
4. Constructor and solver profiles, output/context caps and model/package identities are bound to the same run manifest.

Changing both request and effective temperature to 0.9, including an unrecognized option, currently passes. The newer resource manifest imports the same mutable REQUESTED_OPTIONS object as the builder. That is not an independent freeze. A direct requested/effective mismatch check is useful, but cannot detect producer-wide policy drift.

No code fix was made during this review. Fixing this field alone would not change the overall G0 verdict.

## 7. Can the apparatus pass its tests while missing equivalent violations?

**Yes, directly demonstrated.** These are fresh in-memory mutations of an otherwise passing one-family fixture, not hypothetical production incidents.

| Probe | Main checker / verification result |
|---|---|
| Extra P call, ordinary attempt index 0 | No violation. |
| Teaching and additional tool text in N user packet | No violation. |
| Coherent E world/parent substitution | No violation. |
| All oracle references removed, assigned solver slots retained | No violation. |
| Orphan or duplicate Z oracle reference | No violation. |
| UNKNOWN result relabeled PASS | No violation. |
| Shared generation ID attached to different input/output | No violation. |
| Fabricated new generation ID | No violation; reported call count increases. |
| Invalid response hash and unrelated artifact ID | No violation. |
| Changed constructor identity, prompt/spec hashes, output budget | No violation. |
| Negative construction cost | No violation; aggregate construction character cost becomes **−97,833**. |
| Both requested and effective options change | No violation. |
| Builder constant and system packets drift together | No violation. |
| Paired world's public specification changes | No violation. |
| Hidden convention removed from teaching observations | Builder still injects it into P; no violation. |
| Disable ApplicabilityRunner.dispatch | Mock orchestrator still completes. |
| Four-family ordinary run | 48 false-positive contamination violations. |
| Add legitimate opposite-world P diagnostic score | False-positive P_E_GENERATION_REUSED. |

Character costs are explicitly named as character proxies in accounting output, which is honest. They are not tokens, elapsed compute, or money. Constructor field names say “cost_tokens,” and solver accounting omits system/spec/query text. These proxies must not be used to assert real resource-budget compliance.

## 8. Three manifests: current status and freeze requirements

**None is ready for a real E5 freeze.** Existing schemas and synthetic examples are useful development artifacts. A frozen scientific artifact is a populated, validated immutable instance bound to the run, not a Python module saying “frozen.”

### 8.1 Task manifest

Current useful feature: the newer `task_manifest.py:39` hashes full family contents using dataclass serialization, and `verify_not_tampered` detects an altered expected answer. I verified this improvement; the earlier draft's IDs-only hashing problem is not a current finding.

Remaining failures:

- Empty manifests can freeze.
- Invalid novelty evidence can freeze when a caller sets `passed=True`, even with duplication flags and no measured difficulty benefit.
- Family-membership checking alone accepts changed content; the full hash check is separate and is not integrated into the experiment path.
- The docstring at lines 10–19 imports the earlier adversarial review's “teaching-informed solver beats blind solver” novelty criterion. Final adjudication §7.2 explicitly rejected admitting tasks on “N failed and P succeeded.” Screening withheld tasks for the desired treatment advantage would bias the result and expose the evaluation set.
- Synthetic novelty scores are labeled examples. They are not an actual sealed task set.

Required frozen content:

- Protocol/schema/run identity; four prespecified base families and two world states each; complete assignment list, all failure slots, construction/solver/scoring schedules, and diagnostic-versus-primary purpose.
- Exact public specification, teaching queries **and observations**, withheld query bytes, private expected outputs/reference implementation, correct actions, three substantively different near-match cases and three unrelated cases per family.
- World-independent logical query identities plus an explicit mapping to each world's oracle. Same visible public packet/query bytes across paired worlds, differing private conventions/outcomes where required.
- Randomized convention assignment and its sealed seed/commitment; information partition showing the convention is available through permitted teaching, not family names, labels or hidden fields.
- Task authors/custodian, freeze point, review evidence for teaching/withheld nonduplication and composition/edge cases, without treatment-outcome selection.
- Oracle code/version, score aggregation, UNKNOWN policy, no-post-hoc-exclusion rule and intention-to-treat denominators.

Hash a canonical serialization of the entire task artifact and every referenced payload/expected-answer fixture. Retain private oracle bytes separately with access restricted; the generator need not receive private hashes or paths. Hashing must be paired with access control.

Required invariants: nonempty exact planned cardinalities; no duplicate assignment/reference keys; all required query/world mappings resolve; public-byte equality across pairs; correct oracle strata and incompatible paired answers; no privileged field in constructor projection; hash verification at admission, artifact reload and run close. Task admission cannot depend on pilot P outperforming another arm.

### 8.2 Role/access manifest

Current role table covers checker-code names. This is useful navigation, not proof of enforcement. The helper that verifies non-checker enforcement accepts `sandbox.guarded_write=None` because it checks attribute existence. Its import-graph entry returns true despite the actual builder import in the checker.

Required frozen content:

| Role | Permitted input/output boundary |
|---|---|
| Task custodian | Owns hidden worlds, withheld oracles and sealed assignment; emits restricted public/teaching projections. |
| P constructor | Public spec + assigned world's observed teaching only; one frozen procedure output. |
| E constructor | Same assigned experience as P, complete episodic representation under the frozen construction contract. |
| Z constructor | Same public spec and matched procedure instruction, empty experience; one artifact shared across worlds. |
| N solver | Public spec/query only; no construction parent or acquired artifact. |
| P/E/Z solver | Public spec/query + exactly the assigned frozen artifact; no other arm/world store. |
| Trusted transport/runner | Records actual invocation packet and actual dispatch; owns generation identities and costs. |
| Oracle/validator | Reads sealed expected outcomes and immutable observed evidence; cannot trust candidate PASS declarations. |
| Summarizer | Reads validated immutable records; no authority to rewrite outcomes, assignments or eligibility. |

Also freeze paths/namespaces, process boundary, allowed imports, file/network/IPC capabilities, prohibited production paths/services, model endpoint policy, and the mapping from each invariant to an actual enforced check. No role may receive a larger object that embeds fields it is supposedly prohibited from seeing.

Hash the policy, transport/runner/checker/oracle source, imported local dependency closure, entrypoints, and relevant environment allowlist. Pin accepted hashes in a separate run-start record. Verify real reads/writes and message projections against sacrificial forbidden resources. Preserve denied-access evidence and final state checks. A static list of checker-code strings is insufficient.

Real execution must additionally establish resource and private-inference isolation without touching production. A candidate cannot be given evaluator write access. For the next G0 repair, keep candidate outputs inert; there is no need to execute generated code to fix the current accounting and information-boundary bugs.

### 8.3 Resource-budget manifest

Current useful features: explicit mock-only scope, an UNKNOWN real backend identity, and a written one-generation/multiple-reference accounting rule. UNKNOWN is appropriate at this stage; it is a real-E5 admission blocker, not a reason to fabricate a digest.

Current verifier weaknesses, reproduced on the newer stable snapshot:

- Manifest and builder REQUESTED_OPTIONS are the **same object**. Changing its temperature to 0.99 leaves all verification booleans true.
- Setting a construction allowance to 999, solve calls per query to 999, and timeout to −1 leaves all verification booleans true.
- The “cost rule verified live” check merely requires Z row count to exceed distinct generation labels, reproducing the faulty accounting rather than observing solver invocations.
- The declared 60-second timeout differs from final adjudication's six-minute cap without an explicit protocol amendment.
- A single per-arm output field is ambiguous: N's zero is appropriate for absent construction but not its required solver response.
- The real model/package identity and aggregate admission/resource conditions are not populated.

Required frozen content:

- Separate constructor and solver profiles: package/tag/digest or other immutable weight-package identity, backend version/template identity where observable, exact prompts, seed policy, all requested options, supported effective-options policy, input/context/output caps and timeout.
- Per-family/world/arm invocation cardinalities; no retries or best-of selection; failure and timeout handling; distinction between invocation, generation and scoring reference.
- Under the current four-family design: P8/E8/Z4 constructions, P80/E80/Z40/N40 solver invocations; maximum 260 total, 1,024 output tokens per actual generation, maximum 266,240 output tokens and 26 inference hours at six minutes per call. Any deliberate smaller cap is a preregistered amendment, not a silent default.
- Hardware/resource admission, memory limits and concurrency, private backend endpoint, environment, permitted scratch paths, stop conditions, and assurance that production is not unloaded/reconfigured to make room.
- Observed token counts when available, explicit unknowns where unavailable, time/load telemetry, and character proxies distinctly labeled. Nonnegative values and unit consistency are mandatory.

Hash the populated canonical budget instance and bind it to task/role hashes, source snapshot, actual transport and run ID. Verify before every allowed invocation and at close against transport-observed counts/options. Compare against a pinned expected snapshot, not another import of a mutable producer constant. No real model discovery or backend calls were made during this mission.

### Freeze decision

| Artifact | Ready to freeze for real E5? | Immediate prerequisite |
|---|---|---|
| Task | **No** | Actual sealed tasks, noncircular admission, full assignment/oracle mapping and payload validation. |
| Role/access | **No** | Enforced restricted projections and independent transport/dispatch evidence; actual isolation gates. |
| Resource budget | **No** | Independent immutable profiles, actual invocation accounting, consistent caps and resolved real resource/package identity. |

Do not freeze a known-broken harness simply to produce a hash. Freeze after the repaired mock checks establish what the artifact means; real execution remains a separately authorized gate.

## 9. Exact next gate

**Next action: repair the isolated G0 apparatus and rerun mock qualification. Do not execute real E5.**

The bounded repair scope is:

1. Separate immutable invocation/generation records from scoring references; implement true reuse and explicit query/world mappings.
2. Correct the outcome join and fixed-denominator completeness/close validator.
3. Route the actual mock packet and actual applicability dispatch through observable boundaries; restrict constructor input to permitted projections.
4. Bind condition and options validation to an independently frozen contract; validate all arm/world lineage symmetrically.
5. Add integrated regressions for all thirty anomaly meanings, including the bypasses in this report, plus clean multi-family cases.
6. Validate populated synthetic versions of the three manifests against actual recorded execution before preparing real sealed task artifacts.

The repair qualification should require:

- The original suite continues to pass **after misleading assertions are repaired**, rather than preserving broken expectations.
- Every assigned anomaly causes the appropriate invalid/incomplete machine outcome through the qualification entrypoint; a clean paired/multi-family case has none.
- A stateful mock and invocation spy prove Z/N reuse creates no second invocation and cannot acquire extra cost or independent-sample credit.
- Exact expected synthetic outcome tables agree with an independently written join. Correct and incorrect strategies produce strictly distinct expected results where specified.
- Missing/orphan/duplicate results, malformed/UNKNOWN outcomes, coherent options drift, permitted diagnostic rescoring, prompt leakage, extra construction, artifact reload mutation and incomplete close are tested.
- Metamorphic variants rename IDs/tokens, reorder record insertion, vary family count and legitimate shared tokens, and repeat in another run namespace. Frozen fixtures plus equivalent variants must work; fifteen synthetic relationships need not be fifteen biological claims.
- No real inference, production imports, production writes or process-control actions occur.

If that gate passes, it licenses **qualification of the mocked measurement path under its tested contract**. The next gate is freeze/admission of actual task/role/resource artifacts plus private execution isolation, followed only then by separately authorized E5-mini. It does not authorize direct migration to production or treat an unavailable backend field as resolved.

## 10. Claims boundary

A repaired G0 can establish that a particular mocked instrument records, validates and scores its tested execution paths correctly. It cannot establish robustness against every possible malicious program, the behavior of an untested live transport, or any learning by Echo.

A valid, successful E5-mini can provide **pilot evidence for independently measured transfer/information reuse through the tested taught-procedure pipeline**, with the stated P/E/Z/N contrasts, family clustering and controls. It cannot prove “Echo learned” as a general capability, accumulated competence, sustained growth, algorithm acquisition, or autonomous self-improvement. Independently measured transfer is the maximum relevant E5 claim, and this small pilot still requires confirmation.

A valid P≈Z result with adequate measurement would fail to support an incremental teaching-experience advantage in the tested distribution, even if both beat E/N. Measurement corruption here must not be misreported as that scientific result: UNKNOWN paired oracles and mixed-arm scores cannot adjudicate P−Z or P−E.

Longitudinal E8 remains necessary for the stronger accumulation claim. No E8 redesign or implementation is warranted by this apparatus review.

## 11. Reproduction and evidence record

The adversarial probes ran against in-memory ledgers with unchanged source. Representative minimal operations, after safe imports, were:

```python
# Observe surrogate invocations independently of generation labels.
with patch.object(builder, "mock_solve", wraps=builder.mock_solve) as spy:
    ledger = run_mock_e5_mini(4)
    actual_solver_invocations = spy.call_count
# actual_solver_invocations == 272
# reconcile(ledger)["distinct_generations_total"] == 240

# Require outcomes, not merely evidence that a solver row exists.
ledger, w0, w1, worlds = _clean_family_ledger()
slots = [(r.family_id, r.world_id, r.arm, r.query_id)
         for r in ledger.solver_calls.values()]
ledger.oracle_references.clear()
assert check_ledger(ledger, worlds, slots) == []  # reproduced defect

# Equivalent options drift can agree internally and violate the protocol.
ledger, w0, w1, worlds = _clean_family_ledger()
rec = next(iter(ledger.solver_calls.values()))
options = dict(rec.requested_options, temperature=0.9, unrecognized=True)
ledger.solver_calls[rec.call_id] = replace(
    rec, requested_options=options, effective_options=options)
assert check_ledger(ledger, worlds) == []  # reproduced defect
```

These snippets are evidence explanations, not instructions to run real E5. `_clean_family_ledger` is the supplied test helper. The actual review executions also used the audit hook and temporary-directory cleanup described in §2.

Primary evidence map:

| Evidence | Supports |
|---|---|
| Implementation report §§10–16 | Claimed 30/30 coverage, 52 tests, G0 qualification, disclosed #17 gap and mock-only scope. Claims rechecked rather than adopted. |
| Final adjudication §§4,7–10,13 | Independent condition checks, paired content control, four-family cardinalities, budgets, pilot claims and execution boundary. |
| builder.py:58,85,142,149,168 | Privileged teaching assembly, surrogate calls, placeholder public spec, repeated solving, asserted dispatch. |
| checker.py:48,59,77,125,147,172,208,224 | Anomaly flags, #17 integration, asymmetric lineage, shared baseline, weak reference/completeness checks. |
| orchestrator.py:41,76,115 | Actual P/E/Z/N construction and solve schedule; world mapping; declaration-based negative scoring. |
| accounting.py:10 | Generation-ID deduplication and character-cost proxies. |
| tests/test_e5_mini_g0.py:64,170,189,290,337,363,422,488,551 | Full-scale check omission, direct assertions, fabricated-count acceptance, dispatch test branch, stubbed oracle protection, broken score join. |
| ledger.py:30; schema.py | Mutable records, per-instance IDs, available provenance fields. |
| sandbox.py:28,43,56; applicability.py | Narrow write/scanner helpers and disconnected real mock-dispatch component. |
| Newer task/role/resource manifest source and tests | Full-content tamper check, policy-name coverage, shared options object, insufficient budget verification. |
| Fresh original-suite run | 52 executed, 0 failures/errors/skips; one scratch write, removed. |
| Three fresh adversarial probe processes | Reproductions and newer 12-test run described above; no production import/write or real inference observed. |


### Source identity

SHA-256 identifies the actual working-tree bytes, including untracked files. These are content identities, not proof that HEAD contains the implementation.

| Path | Opening SHA-256 | Last checked SHA-256 |
|---|---|---|
| `app/experiments/e5_mini/__init__.py` | `d226e399f8e16bacda1b7cae0e403152ea8788658ee5e6e5492290baa3d0d098` | Unchanged |
| `app/experiments/e5_mini/accounting.py` | `c4028e8cf09083b6c6c270a3f3fa3886d2623c4603ffedc09c4485114c74d101` | Unchanged |
| `app/experiments/e5_mini/applicability.py` | `35ac580bd12bd292859781fb09e2ea86d472d3d1d27b8c32a022d2df97bde91f` | Unchanged |
| `app/experiments/e5_mini/builder.py` | `9a0eead98227f021281d9b50afb0b759f5c605d49680986f4b1fdc86ca1d474b` | Unchanged |
| `app/experiments/e5_mini/checker.py` | `6c0cc1c8f2f02685816ce06f26e45929784e08aed86e867be0b8477dcc2bbb27` | Unchanged |
| `app/experiments/e5_mini/ledger.py` | `3a5f208135e71f6eb6b26dc069c60775fd00428d8e45530848eb18ae4409d326` | Unchanged |
| `app/experiments/e5_mini/manifests/__init__.py` | `1d57dcc41dcd910d6d0bc52108beebe035325295cf3981ad0410423819292d5a` | Unchanged |
| `app/experiments/e5_mini/manifests/example_synthetic.py` | Not present in opening source inventory | `5bc9ef4bcce57927020901224ea6e0a0ea095beb679856e35e260ce6af01553e` |
| `app/experiments/e5_mini/manifests/resource_budget_manifest.py` | Not present in opening source inventory | `0eb535a072b77d05f189592e33809df6e9010859be03b397a64a2057b16cd3fc` |
| `app/experiments/e5_mini/manifests/role_access_manifest.py` | `58adc5d4b2fac40bbe4303d0d3b5a2364ecde94915b37be7096ac6d1f9b4dd0c` | `90e3ad652909f0020ef6bb593a5531a6b1f44408ecbf7be3f5a7f8d21dc83ac4` |
| `app/experiments/e5_mini/manifests/task_manifest.py` | `1b0a675147e8b5cb3e685fecb898e1378a45a1e9998ac92a77ee5083d19f94f6` | `32a6ac886bb7db9d57e43d101eed458613f68bdf79812415132f0a0125a3ca12` |
| `app/experiments/e5_mini/mock.py` | `0b7ba0943a1ab3d7d9623da84c1d8bbc02a2b5d3f39df2967e45bf4b55b211d0` | Unchanged |
| `app/experiments/e5_mini/oracle.py` | `aff5a996781f79e25be4191167b51e3a9566cf948bc53d1b13604e3303f7f98c` | Unchanged |
| `app/experiments/e5_mini/orchestrator.py` | `097de5700fb12009ab96b40f007b033fcc05bd17b9fbc3f04ea1c449bd2403a2` | Unchanged |
| `app/experiments/e5_mini/sandbox.py` | `b6f0c5c891fbc9207afa20563ac715d5c8cf706b18d52c6be815ce808af68bde` | Unchanged |
| `app/experiments/e5_mini/schema.py` | `fad8e4299800a5f4295f5e78d8549e5f5708d42c84ff14bb2fb893bc24490f9e` | Unchanged |
| `app/experiments/e5_mini/tests/__init__.py` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | Unchanged |
| `app/experiments/e5_mini/tests/test_e5_mini_g0.py` | `bf0fdc6c12b570a25955eec9bb690c27b9ef2655c77a0688a7dc68b9c5b4b763` | Unchanged |
| `app/experiments/e5_mini/tests/test_manifests.py` | Not present in opening source inventory | `51cfdd1e3fafd782b57165e6ec08a251cb9dc5c4ab46a73f913685d2225c4154` |
| `audits/2026-09-16_e5_mini_g0_mock_implementation.md` | `6fb5d36887b0900a90c40702e900c9495091bbdb7799b5768764a1ab5886a938` | Unchanged |

## 12. Git and filesystem integrity

The full opening output of `git --no-optional-locks status --short --untracked-files=all` was:

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
?? app/experiments/e5_mini/manifests/role_access_manifest.py
?? app/experiments/e5_mini/manifests/task_manifest.py
?? app/experiments/e5_mini/mock.py
?? app/experiments/e5_mini/oracle.py
?? app/experiments/e5_mini/orchestrator.py
?? app/experiments/e5_mini/sandbox.py
?? app/experiments/e5_mini/schema.py
?? app/experiments/e5_mini/tests/__init__.py
?? app/experiments/e5_mini/tests/test_e5_mini_g0.py
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
?? audits/2026-09-16_e5_mini_final_adjudication.md
?? audits/2026-09-16_e5_mini_g0_mock_implementation.md
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

Opening HEAD was `2fba42644c82b9f7096276f4dd338d615cf1bcce`. Read-only Git commands used `--no-optional-locks`; no stage, commit, reset, checkout, rebase, stash, push, or history mutation was performed.

Closing verification: **2026-09-16T22:14:32.499946+00:00**.

- Ending HEAD: **`2fba42644c82b9f7096276f4dd338d615cf1bcce`**, identical to opening.
- Ending full short status: **201 entries; 27 modified tracked and 174 untracked**.
- Every opening status entry remains; none was removed or changed as a status entry. The complete closing status is exactly the opening block plus these five entries:

```text
?? app/experiments/e5_mini/manifests/example_synthetic.py
?? app/experiments/e5_mini/manifests/resource_budget_manifest.py
?? app/experiments/e5_mini/tests/test_manifests.py
?? audits/2026-09-16_e5_mini_g0_codex_adversarial_review.md
?? audits/2026-09-16_e5_mini_manifests_design_and_hostile_review.md
```

Of those five, only the Codex adversarial review report was created by this mission. The other four were concurrent additions. Two already-untracked files also changed concurrently in content: `app/experiments/e5_mini/manifests/task_manifest.py` and `app/experiments/e5_mini/manifests/role_access_manifest.py`. Their old/new hashes appear in §11. All thirteen original core/test Python files outside `manifests/`, the original manifest initializer, and Claude's implementation report remained byte-identical to opening. The six-file newer manifest/test snapshot was stable through its adversarial check and this closing verification.

All four temporary roots were checked absent at close. This closing record is appended to the authorized report itself; doing so does not change its untracked status.

Concurrent changes cannot be attributed to this mission merely because they occurred during it. Conversely, Git status alone cannot prove that already-dirty or untracked file contents stayed unchanged; that is why the source hash comparison is recorded above. I did not take a full byte-level snapshot of live production stores and do not claim to have ruled out their ordinary background writes.

Mission-caused repository delta: **only `audits/2026-09-16_e5_mini_g0_codex_adversarial_review.md`**. No existing report, code, configuration, dataset, memory store, RiverBrain object, FAISS index, hub/relay file, or experiment-state artifact was changed by this mission. The four isolated temporary roots listed in §2 were removed. No FeralEcho process was intentionally altered, attached to, signaled, restarted or stopped. No real inference was requested. These statements concern this review's actions and guarded executions; they do not certify the historical actions of another session or unrelated background activity.

## 13. Final decisions

- **G0 verdict: NOT QUALIFIED.** The mocked instrument's mandatory attribution, accounting, completeness and information-path properties have reproducible failures.
- **Strongest supporting evidence:** the supplied **52/52 tests genuinely pass**, and several narrow hash, parent, exact-oracle and options-mismatch checks demonstrably work. The new full task-content hash also detects tampering.
- **Strongest remaining weakness:** the claimed execution ledger is not a faithful independent observation of the executed information/generation path; its scoring helper additionally mixes arm outcomes. These defects can manufacture or erase apparent treatment differences.
- **#17 disposition:** its reported integration gap was already fixed before this review began. Requested/effective mismatch checks work; independently frozen policy and identity binding still need repair.
- **Three manifests ready to freeze: NO.** Current files are partial design/synthetic artifacts, with reproduced validation bypasses and unresolved real execution fields.
- **Exact next gate:** repair the isolated mock instrument as specified in §9, then require independent call-count, outcome-join, condition-path and all-thirty-anomaly requalification. Only afterward prepare and freeze real manifests and establish execution isolation.
- **E5 decision: NO-GO.** No real model execution or production integration is justified by this G0 result. E5's eventual ceiling is independently measured transfer, with pilot limitations; sustained accumulation still requires longitudinal E8.

Richie: authorize only the bounded G0 mock repair and requalification next. No further general architecture debate is needed to act on these concrete failures.
