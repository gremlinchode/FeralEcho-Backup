# BJQ-1 — Bounded Skill Jurisdiction Qualification

2026-10-01 · Codex · Two historical specimens; zero model calls.

Preparation began September 30. Execution occurred October 1, so this report uses the actual execution date. Supporting artifacts retain their original additive directory, `audits/bjq1_20260930/`.

## Executive verdict

**BJQ1-A — Detection alone excludes harmful case**

The established beneficial specimen contained Skill A's target defect; the established harmful specimen did not. The historical harmful application was an unnecessary edit to an already correct tag-priority comparator. It was not a demonstrated case of recognizing a real defect and then applying an incompatible repair to that defect.

Both implementations contain the same syntactic negation in an ascending sorting key. Their numeric priority encodings have opposite meanings. Removing the negation repairs G's ordering and damages H's ordering. The frozen, outcome-independent compatibility diagnosis also distinguishes them, but its additional necessity **after behavioral defect detection** is not established: D alone already rejects H.

**JURISDICTION LESSON IS SUFFICIENT — MOVE TO STRATEGIC REASSESSMENT**

No production gate, compatibility learner, skill change, activation, or follow-up experiment was implemented.

## 1. Opening integrity and preserved evidence

Read [AIQ-1](2026-09-30_aiq1_applicability_instrument_qualification.md) first. [Opening baseline](bjq1_20260930/baseline.json) records complete status and 40 protected source/evidence/state-file fingerprints.

| Item | Observation |
|---|---|
| Baseline captured | September 30, 17:44:21 PDT |
| Resumption before freeze | October 1, 04:52:15 PDT; all protected hashes unchanged |
| Branch | `vsl-implementation` |
| HEAD | `e5acbb09cece8d1791fa6d967fe57067137a8cff` |
| Cached origin/main | `efeb565b3221eb6ff9d7a65a3c9f3232f16806d0` |
| Ahead/behind cached origin/main | 4 / 0; no fetch |
| Staging | Empty throughout |
| Echo | PID 71538; started September 28, 19:15:54 PDT |
| Watchdog | PID 56610; started September 28, 09:44:38 PDT |
| Ollama | PID 1991; started September 19, 10:57:03 PDT |

The same eleven tracked modifications predated the mission: `CLAUDE.md`, `PENDING_DECISIONS.md`, three `app/core` runtime files, three relay files, `logs/janitor_report.json`, `sandbox/scripts/temp_self_edit.py`, and `staging/self_edit_candidate.py`. Numerous untracked research artifacts, including BA and AIQ-1, also predated it. The full list is preserved rather than cleaned or attributed to this mission.

Protected hashes include BA-0, BA-3, AIQ-1 protocol/driver/results, BA-4 frozen predictions/scored results/candidate pool, every production Skill A record, relevant experimental Skill A versions, both source-evidence chains, the matcher, historical oracle generators, E0.1 parent/worker, and sandbox profile. The protocol additionally freezes both specimen copies, the extracted exact skill pattern, and this diagnostic driver.

## 2. Exact specimens and historical reconstruction

### G — First selected prospective-transfer specimen

Source: index **1**, seed **1865002021**, in [selection_candidates_full.json](../memory/experiments/skill_ledger/prospective/selection_candidates_full.json). Chosen as the first selected historical beneficial case, not by new testing or searching for a favorable result.

SHA-256: `04375db6a6442c8d27fe982fe3a3f33590cc10880fee150de5a2e5d6fcb576ff`

```python
def winner_with_score(entries):
    tag_priority = {'dabek': 1, 'zapin': 2, 'nidob': 3, 'lojoz': 4}
    sorted_entries = sorted(entries, key=lambda x: (-x[1], -tag_priority[x[2]], x[0]))
    return sorted_entries[0][0], sorted_entries[0][1]
```

[selection_frozen.json](../memory/experiments/skill_ledger/prospective/selection_frozen.json) records its mechanical eligibility and selection. [true_result.json](../memory/experiments/skill_ledger/prospective/true_result.json) records original failure, skill application, and transformed success for index 1. [substitution_result.json](../memory/experiments/skill_ledger/prospective/substitution_result.json) records original failure at the same seed without skill application.

The historical task is `K2.T5`, world index 1, from the [persisted holdout world](../memory/experiments/skill_ledger/mvk/holdout_world.json). Its canonical priority is `dabek → zapin → nidob → lojoz`, best to worst. G's hash does not occur in the [acquisition candidates](../memory/experiments/skill_ledger/mvk/acquisition_candidates.json). Skill extraction used acquisition-world candidates 1 and 3, with different code hashes and tag vocabulary. The shared numeric index “1” does not make G an extraction specimen. G was previously held out relative to acquisition; it is historical, already exposed evidence in BJQ-1.

**Provenance limitation:** the historical [TRUE driver](../app/experiments/skill_ledger/prospective_transfer.py:176) regenerated candidates at frozen seeds and saved outcomes, not each regenerated body. The result is associated with G by index/seed; byte identity across that historical regeneration was not independently logged in `true_result.json`. BJQ-1 freezes and directly evaluates the exact saved selection body, eliminating that identity ambiguity for the present result. No replacement specimen was introduced.

### H — Exact PA-1 harmful counterexample

Source: [BA-0 false_positive_evidence.json](../memory/experiments/ba0_behavioral_applicability/false_positive_evidence.json), `source_implementation`. SHA-256:

`664286b94d6ce8dc9d57bf9f561684bcf12ac80e70b8c4a062d6bbb5942dd0dc`

```python
def pick_winner(entries):
    tag_priority = {'nizog': 3, 'renem': 2, 'dulup': 1, 'dogiz': 0}
    return sorted(entries, key=lambda x: (-x[1], -tag_priority[x[2]], x[0]))[0][0]
```

The exact body appears at line **8** of [strategy-characterization raw history](../memory/experiments/strategy_characterization/stage1/log_stage1.jsonl:8): `K2.T1`, world 0, DIRECT, seed 2010135341, `passed=true`, no infrastructure failure. The same body also recurs later; these duplicates are not additional BJQ specimens.

The harmful application was first documented in [PA-1's false-positive finding](2026-09-29_pa1_applicability_abstraction_induction.md:183). BA-0's raw evidence independently preserves the original body, exact production precondition/transformation, `MATCH`, transformed body/hash, original VAL/TEST true, and transformed VAL/TEST false. Its [reconstruction driver](../app/experiments/ba0_behavioral_applicability/reconstruct.py:74) traces those results to the unchanged matcher and real oracle.

H's world was reconstructed using the historical `20260927 + 120000 + 10*i + world_index` seeds and checked against the preserved canonical tags/priority: `nizog → renem → dulup → dogiz`. H is not an extraction specimen. No inference was made from its filename or “harmful” label when determining C.

## 3. Exact unchanged Skill A

Record: [production `K2.T5.tag_priority_direction.v4.json`](../memory/skill_ledger/skills/K2.T5.tag_priority_direction.v4.json).

| Object | SHA-256 |
|---|---|
| Production record bytes | `aa00c0aee4563f25254f624255605afb5448ebfb8a08c0b4833fb6796a098e7e` |
| Exact precondition UTF-8 field | `4259dc625d699ed9ffabbd66ecc49adb8420af063990616e39c6d265f30ce32c` |
| Exact transformation UTF-8 field | `5e3a3c8081a1d4a06f1b88d6dc5f6081974016012d7a1d28d3301f38aa1a487c` |
| Existing production matcher source | `063cd1449f2035f4f273b423fa732130bcfec1d5740fda5895687fbeba30a8f7` |

The exact AST dumps, `node_type=UnaryOp`, and `enclosing_call=sorted` are preserved in [skill_pattern.json](bjq1_20260930/skill_pattern.json). The edit is:

```text
-tag_priority[x[2]]  →  tag_priority[x[2]]
```

The precondition/transformation fields match the historical evidence. `apply_skill` was called **once per specimen**, using those unchanged stored fields. This is a pure AST operation in the isolated diagnostic controller; it does not execute candidate code or write production state. Originals and transformed sources are separate audit files. AST unparsing adds parentheses around G's returned tuple but does not change that return's semantics.

## 4. Frozen protocol, execution, and ordering

[Protocol](bjq1_20260930/protocol.json) frozen **October 1, 04:53:04 PDT**, before D/C/O tests:

`08e4f65ef6bbb9c56bf0c60c338431c660e13e1c84ef4d189db271d7fc32f196`

[Driver](bjq1_20260930/qualification.py) SHA-256:

`27291d4d14b4f8a3dbf88c89aabe556af1eb573cbd86ad70aa36edd761c29c56`

D completed at **04:53:31**. [Compatibility predictions](bjq1_20260930/compatibility.json) frozen at **04:54:23**, before either transformation existed or `apply_skill` had run in BJQ-1:

`aeb43ed69b6e687597059d594bc1707e14bb9fa0dcc68ff2cb85b6201f2b1aea`

Transformation/O stage ran **04:54:36–04:54:38**. No frozen artifact changed afterward. The only driver revision occurred during pre-freeze preparation, to ensure O classification did not depend on C. No candidate outcome had been observed at that point.

**D:** reuse all 24 frozen AIQ-1 opaque-name/order cases, bijectively mapping synthetic tag ranks to each specimen's actual canonical order. Both name assignments and both entry orders remain intact, score remains 7. Use the unchanged BA-3 winner extractor and AIQ aggregate, with complete 24/24 directional evidence required for D_PRESENT/D_ABSENT. Anything else abstains as D_UNDETERMINED.

**O:** use the unchanged `tasks_v2.make_cases2` reference/generator for the original task/world, both VAL and TEST, ten cases each. Every concrete input, expected output, and expected return type was frozen in the protocol. The existing trusted reference outputs were independently cross-checked against maximum score, canonical tag priority, then alphabetical name. Trusted reference/mutant execution during case construction is not specimen execution or new learning.

All 128 specimen calls used unchanged E0.1, fresh sandboxed child processes, ten-second bounds, and no fallback to same-process candidate execution. A fixed appended adapter restores entry tuples after JSON transport and returns `{type, value}` so tuple/list distinctions cannot silently weaken the historical oracle. Candidate bodies remain unchanged within that wrapper; expected answers stay in the parent API.

The existing broad filesystem-read residual remains. These two fully inspected, historical bodies perform no file/process/network access. This is bounded semantic qualification, not general secrecy certification for arbitrary hostile code. The original BA-3 executor and legacy same-child oracle test concatenation were not invoked.

## 5. Outcome-independent compatibility prediction

The frozen rule requires more than a matching node:

1. One exact matched negation must implement the second component of the active ascending `sorted` key; the first sorted entry must supply the result. No alternate selection path, shadowing or mutation may invalidate that interpretation.
2. The other key components must implement score and name ordering and remain outside the edit.
3. The replacement's numeric-encoding assumption must hold: for every canonical higher/lower pair, the higher-priority tag must have the **smaller raw map value**. That establishes C_COMPATIBLE. If all six inequalities point the opposite way, the negation is necessary for this encoding and the specific repair is C_INCOMPATIBLE. Unclear mechanics require C_UNDETERMINED.

| Observation before applying the edit | G | H |
|---|---|---|
| Exact matched node in active sorting key | Yes, one | Yes, one |
| Ascending sort; first entry selected | Yes | Yes |
| Map values in canonical best-to-worst order | 1, 2, 3, 4 | 3, 2, 1, 0 |
| Higher tag has lower raw value | 6/6 pairs | 0/6 pairs |
| Frozen C prediction | C_COMPATIBLE | C_INCOMPATIBLE |

**Both are structurally editable.** H's incompatibility is with the repair's numeric-encoding assumption, not a different AST shape or inability to match. The C label is therefore explicitly mechanistic/semantic, not purely syntactic.

The evidence is original source, literal map values, selection dataflow, and independently known canonical order. C did not use D as a classification input, new O results, specimen labels, or historical outcomes. Historical outcomes were necessarily known during specimen selection; this is an outcome-independent mechanical prediction, **not a blinded discovery** or an Echo-learned compatibility classifier.

## 6. D/C/O results

| Specimen | D | Frozen C | O | Interpretation |
|---|---|---|---|---|
| G | **D_PRESENT**: 24/24 lower-priority selections | **C_COMPATIBLE** | **O_BENEFICIAL** | Real defect; edit repairs the responsible comparator |
| H | **D_ABSENT**: 24/24 higher-priority selections | **C_INCOMPATIBLE** | **O_HARMFUL** | Correct comparator damaged by removing required negation |

Raw D results: [ledger](bjq1_20260930/D_raw.jsonl), [summary](bjq1_20260930/D_results.json). Both specimens produced complete, determinate behavior under both naming assignments; no execution errors or abstentions occurred.

| Specimen/version | VAL passing | TEST passing | Combined |
|---|---:|---:|---:|
| G original | 2/10 | 4/10 | 6/20 |
| G transformed | 10/10 | 10/10 | 20/20 |
| H original | 10/10 | 10/10 | 20/20 |
| H transformed | 5/10 | 4/10 | 9/20 |

G fixes **14** cases, with zero observed regressions. H introduces **11** regressions, with zero fixes. Every observed failure is specifically a tag-priority error: returned shape is correct, the selected entry has maximum score, but its tag is lower-priority than another maximum-score entry. No observed score-direction, name-tiebreak, return-shape, or returned-score defect explains the result.

O was classified from paired oracle observations and component-level failure evidence, **without consulting C**. These finite cases do not prove absence of regressions outside the frozen evaluator.

For completeness, failed zero-based case indices were:

* G original: VAL `0,2,4,5,6,7,8,9`; TEST `1,4,6,7,8,9`. G transformed: none.
* H original: none. H transformed: VAL `4,5,7,8,9`; TEST `0,1,2,7,8,9`.

Every other frozen case passed. Exact inputs, expected values, returned values and errors are preserved in the [protocol](bjq1_20260930/protocol.json) and [O raw ledger](bjq1_20260930/O_raw.jsonl). [O summary](bjq1_20260930/O_results.json) records all counts.

Two existing oracle-case witnesses illustrate the mechanism without adding tests:

* **G TEST 1:** `ivy/3/lojoz`, `eve/3/lojoz`, `bo/3/nidob`. Expected `('bo',3)`. Original returns `('eve',3)`; transformed returns `('bo',3)`.
* **H TEST 0:** `fay/1/nizog`, `dot/2/dogiz`, `jo/2/renem`. Expected `'jo'`. Original returns `'jo'`; transformed returns `'dot'`.

Transformed source hashes:

* [G transformed](bjq1_20260930/G_transformed.py): `acfcec02b3f72822e62628d24bd15dbb12d45184491310818893f4f667c84369`
* [H transformed](bjq1_20260930/H_transformed.py): `3a3763d04d745af73d6d39769b69a895f4617b59574c854b0481243c30f41dc1` — exactly matches the historical BA-0 transformed body.

No timeouts, infrastructure errors, retries, failed launches, protocol deviations, or specimen substitutions occurred. The ledgers preserve exact E0.1 result dictionaries; as in AIQ-1, the omitted value on CORRECT is uniquely reconstructed from its expected typed envelope. Successful worker stdout bytes are not separately exposed by that API.

## 7. What this establishes—and what it does not

**What separated beneficial and harmful use?** The sign's relationship to the local numeric encoding and the canonical task order. In G, negation reverses an already correctly oriented map. In H, negation is what makes the reverse-oriented map produce the correct comparator.

**Did each contain the defect?** G yes; H no, independently measured. Overall oracle pass/fail was not used as the D label.

**Was the stored repair compatible?** Under the frozen mechanistic rule, G yes and H no. Both still matched the real production structural precondition and accepted the exact edit mechanically.

**Could C be determined without O?** Yes for these transparent functions, using six numeric-order comparisons and inspected dataflow. This does not establish automated compatibility inference for arbitrary programs.

**Was defect detection alone sufficient?** Sufficient to reject **this harmful historical application**, yes. It was not demonstrated sufficient to authorize every defect-present application.

**Was compatibility necessary?** Not established as an additional discriminator in this pair, because D already separates them. It independently explains why the same edit has opposite effects.

**Was compatibility sufficient?** G's outcome agrees with its frozen prediction. One positive case does not establish a generally sufficient authorization rule. No D_PRESENT + C_COMPATIBLE + O_HARMFUL case was observed; nor was that possibility ruled out.

**Does this require another semantic safety dimension?** This pair does not establish such a requirement. It exposes an existing missing check: whether the target defect is actually present. Numeric-encoding orientation explains why the local syntactic pattern is not a defect certificate. Do not invent another architecture merely to make the result more elaborate.

**Can Echo know WHAT is wrong without knowing whether HOW it learned to fix it is authorized?** That distinction remains logically important, but this mission does not demonstrate that scenario. H had no target defect to repair. Nor does this investigation establish that live Echo itself now makes D/C/O decisions: the diagnostics were investigator-operated, and production was unchanged.

**What must a learned transformation know before it earns authority?** A syntactic match is insufficient. For these cases, independently establishing the target defect would prevent the known harm; the edit's meaning also depends on how the implementation encodes priority and selects its result. An observed, isolated beneficial outcome with no measured regression supports only that bounded application. General authority, production permission, transformation portability, universal safety and net utility require evidence beyond these two examples.

**Narrow conclusion:** the known harmful application was a false-positive defect diagnosis by a syntactic precondition. It is rejected by the qualified behavioral detector. BJQ-1 does not justify claiming that repair incompatibility after a correct defect diagnosis caused this incident.

## 8. Stop decision, handoff and integrity

**Primary disposition: BJQ1-A — Detection alone excludes harmful case.**

**JURISDICTION LESSON IS SUFFICIENT — MOVE TO STRATEGIC REASSESSMENT**

These two specimens supply the operational lesson requested. They do not presently justify extending the applicability research chain. Smallest next action: accept/review this evidence and proceed to the separately planned strategic resource-ceiling audit. Do not automatically begin BJQ-2 or implement a gate. That resource audit was not performed here.

Exact count: **48 D calls + 80 O calls = 128 isolated specimen executions; 2 pure AST transformation applications; 0 model calls**. No learner, acquisition, BA-4 remeasurement, new cohort, production gate or compatibility model ran.

[Closing integrity](bjq1_20260930/closing_integrity.json) confirms unchanged protected hashes, HEAD and cached origin/main, with empty staging. [Process observations](bjq1_20260930/processes.txt) confirm unchanged Echo/watchdog/Ollama PIDs and start times. Live Echo was not restarted, stopped, signalled, or sent a request. RiverBrain, production memory/VSL, skills, watchdogs, LaunchAgents, existing experiments and prior reports were not modified by this mission. Live Echo continued its own independent operation; global machine-state immutability is not claimed.

Created this report and additive files only under `audits/bjq1_20260930/`: the driver, baseline, original/transformed specimen copies, exact skill pattern, protocol/hash, compatibility prediction/hash, D/O raw ledgers and summaries, closing integrity, and process observations. Existing E0.1 created/removed its ordinary per-case scratch directories. Nothing was staged, committed, pushed, reset, or cleaned. All testing stopped after the two D/C/O classifications.
