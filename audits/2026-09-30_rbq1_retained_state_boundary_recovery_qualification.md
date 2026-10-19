# RBQ-1: retained-state boundary and recovery qualification

2026-09-30 · Codex · **Stopped at the strategic gate. No recovery experiment.**

## 1. Strategic revalidation

**STOP — ANOTHER PRIORITY NOW DOMINATES**

The next mission should be a bounded qualification of the **actual behavioral-applicability instrument and its authority implications**, not a recovery demonstration or another applicability-learning experiment.

Two source findings materially change the ordering in my strategic audit:

1. BA-3 executes candidate code directly inside its judge's process, despite describing reuse of the trusted sandbox.
2. Every BA-3 comparison names the higher-priority entry `W_<tag>` and the lower-priority entry `L_<tag>`. A candidate can receive a perfect “correct direction” classification by choosing the lexicographically larger name, without consulting tag priority.

These are source-level findings about the implemented measurement boundary. They do **not** show that the recorded BA-4 candidates exploited either channel, invalidate all historical skill-transfer evidence, or establish a live production compromise. They do prevent treating BA-3 qualification as a sufficiently general justification for safe skill jurisdiction.

RBQ-1's proposed broad state census and successor construction would not resolve this immediate decision. Existing evidence already supports narrow skill reload and state-dependent reuse; complete isolated recovery and off-device preservation remain unqualified. That remaining recovery debt is real, but my previous audit did not justify making a full recovery research program a universal prerequisite for every subsequent scientific decision.

**No RBQ1-A/B/C/D/E/X experimental disposition is assigned.** Those dispositions belong to Phase 18 after a recovery attempt. Phase 0 explicitly required stopping when another priority dominates. Calling this an RBQ1-X experiment, or a recovered-capability success, would misstate what happened.

## 2. What changed since the strategic audit

### BA-4 has results, not merely scripts

Read source and raw artifacts without executing either instrument:

* [BA-4 protocol](../app/experiments/ba0_behavioral_applicability/ba4_protocol.py)
* [BA-4 driver](../app/experiments/ba0_behavioral_applicability/ba4_run.py)
* [Frozen predictions](../memory/experiments/ba0_behavioral_applicability/ba4_predictions_FROZEN.json)
* [Scored artifact](../memory/experiments/ba0_behavioral_applicability/ba4_scored.json)

| Candidate index | Frozen prediction | Recorded BA-3 classification | Recorded determinate cases |
|---|---|---|---:|
| 0 | TARGET_PROPERTY_CORRECT | TARGET_PROPERTY_CORRECT | 12/12 |
| 2 | TARGET_PROPERTY_REVERSED | TARGET_PROPERTY_REVERSED | 12/12 |

That is recorded agreement for two distinct candidate bodies representing opposite classes. It is not independent replication across histories, general applicability, repair portability, or autonomous discovery of the predictor. No BA-4 audit report was found. The driver includes checkpoints whose values are literal `True`; those assertions do not independently establish prior blinding or absence of earlier execution. I did not rerun the driver or independently reconstruct its entire execution history.

Both result files have modification timestamps around **12:15:52 PDT**, before my strategic audit's 12:20:59 closing check. I checked for a new report and noted concurrent scripts but failed to discover these raw outputs. **That was my omission, not evidence that BA-4 was unexecuted.** The strategic audit remains unchanged as historical evidence; this report corrects its evidence boundary.

### The actual BA-3 instrument does not match an important qualification claim

The [BA-3 report](2026-09-30_ba3_ground_truth_instrument_qualification.md), especially its instrument comparison, describes the same already-trusted sandbox. The module's own prose names `oracle_runner.run_script` as shared execution machinery. It imports `oracle_runner`, but the actual path is:

```
judge_tag_priority_direction(..., world_priority)
    computes pri_index, higher/lower, expected comparison identities
    → _run_case(code, fn_name, entries)
        → exec(code, ns)
        → ns[fn_name](entries)
    → trusted-looking classification in the same Python process
```

See [ba3_instrument.py:132](../app/experiments/ba0_behavioral_applicability/ba3_instrument.py:132) and [case construction at line 162](../app/experiments/ba0_behavioral_applicability/ba3_instrument.py:162). There is no subprocess or sandbox invocation in `_run_case`. `exec` is not given a restricted builtins mapping. The judge's state remains in the same addressable Python process during candidate execution.

This is **not** a conjecture about a general sandbox weakness. It is a concrete discrepancy between the claimed and actual invocation. I did not run candidate code, inspect process memory, attempt an exploit, or change the instrument.

### A harmless logical counterexample to what the cases identify

Each generated pair contains one `W_...` name for the true higher-priority tag and one `L_...` name for the lower-priority tag. Reversing input order preserves that mapping. Because `W` sorts after `L`, the following behavior selects the instrument's designated winner in every such pair:

```python
return max(entries, key=lambda row: row[0])[0]
```

This is an **unexecuted analytical counterexample**, not a new experiment or replacement candidate. It uses only names, ignores tag priority and scores, and still satisfies BA-3's accepted bare-name return shape. Across the instrument's four-tag/six-pair/two-order construction, the same argument applies to all 12 cases. Changing entry order cannot discriminate it.

Conversely, choosing the smaller name selects the designated lower-priority tag. Such evidence cannot by itself distinguish a reversed tag-priority mechanism from a name-based shortcut. This matters to the claim that the instrument isolates a target property from unrelated behavior. It is not a claim that the two stored BA-4 candidates contain these functions.

**Bounded implication:** BA-3 can provide useful retrospective observations on already-inspected benign programs. Its current case family and execution path do not justify treating it as a generally independent, shortcut-resistant qualification gate for newly generated programs. This is a measurement/jurisdiction issue to settle before expanding its authority, not a reason for another broad security audit.

### Fingerprints

| Artifact | SHA-256 |
|---|---|
| BA-3 instrument | `e0753eeca69249a329f2328ce2569f3bbada4fee57ff2cee260471baf8a35a52` |
| BA-0 sentinel | `ef178a67e3796fbe98e9c730d17221827d8868020b1a0c7c07871b5dd41785ec` |
| BA-4 protocol source | `c0b1b3cb3834bbc1cd3461bbf6f4f93bafd453d0e469fa79ae51e2d3dc0e5186` |
| BA-4 driver source | `75b432ad76b13d95b06eec10b62c024ef1ef2a297023d8270a26c174c97b266d` |
| BA-4 prediction file | `c9120b4fece2019afafc3de9e98130f0f91cfe9dc9e7151568a29ea76f2aa4ad` |
| BA-4 scored file | `e91de90323063e78684b93a4657d1ab34acd570ae7985ee60e0b80302a1288e7` |
| Prior strategic audit | `8b11edeb47b973613c78a9bfbae49ed54fe464ad9d7106562ecc5ab326d9ac2a` |

The actual instrument hash matches the BA-3 report and BA-4's declared hash. The discrepancy is therefore present in the supposedly frozen implementation; it is not explained by a later, unacknowledged source change found during this review.

## 3. Grok's critique and my own overreach

| Question | Assessment |
|---|---|
| Where does Grok agree with evidence? | Stored repair harm, unproved net utility, narrow transfer, and the distinction between activity and competence all have concrete repository support. A stopping rule should be tied to a decision |
| Where does Grok overreach? | “Primarily architectural rather than computational” is not a controlled comparison. The model has genuine inference/execution limitations; different capacity or inference budgets might matter. They would not fix incorrect attribution or an answer-signalling test by themselves |
| Where did my strategic audit overreach? | It privileged a broad recovery boundary without sufficiently separating backup engineering, narrow capability reload, and the next scientific decision. It missed BA-4 raw results and did not trace BA-3's actual execution despite discussing its qualification |
| Which branches already yielded their operational lesson? | Repeated Boolean interpretation diagnostics, the old unchanged routing setup, and the closed seam-initiative branch. They need a new decision-changing reason to reopen |
| Could RBQ-1 become the criticized pathology? | Yes. An exhaustive state inventory and many successor tests could produce a large report without changing whether the known unsafe skill or the current judge should receive more authority |
| Smallest worthwhile recovery test, if later needed? | One declared acquired skill plus its supporting provenance, loaded by clean source in an isolated successor that cannot read the original tree, compared with identical scaffolding lacking that state |
| What would terminate that recovery branch? | Successful load, relevant causal behavior, preserved restrictions/provenance, and loss of the effect under state removal. Close that bounded claim; do not automatically add more witnesses |
| What makes recovery a genuine blocker? | An essential state/dependency cannot be captured or interpreted, capability disappears under a declared restore, or an imminent preservation decision lacks any verified recoverable copy. A newly noticed optional state file is not automatically a blocker |

My earlier audit was also too long for the immediate prioritization decision. This mission does not try to redeem that by completing forty deliverable headings after its stop condition has fired.

## 4. Repository and live-process ground truth

Opening check: **2026-09-30 17:00:33 PDT**, America/Los_Angeles.

| Item | Observation |
|---|---|
| Branch | `vsl-implementation` |
| HEAD | `e5acbb09cece8d1791fa6d967fe57067137a8cff` |
| Cached origin/main | `efeb565b3221eb6ff9d7a65a3c9f3232f16806d0` |
| Staging | Empty |
| Echo | PID 71538, start September 28 19:15:54 PDT |
| Watchdog | PID 56610, start September 28 09:44:38 PDT |
| Ollama | PID 1991, start September 19 10:57:03 PDT |
| Evidence baseline | 864 source/report/state files SHA-256 fingerprinted in-session at 17:00:49 PDT |
| Production skill state | Skill A v4 ACTIVE on disk; runtime is disabled by default unless explicitly enabled; live process environment not inspected |

The same 11 tracked modifications listed in the strategic audit were already present: `CLAUDE.md`, `PENDING_DECISIONS.md`, three `app/core` runtime files, three relay files, `logs/janitor_report.json`, sandbox temporary self-edit source, and the staged-candidate source file. “Staged candidate” here is a filename, **not Git staging**. The expanded working-tree status, untracked BA/Boolean/invariance artifacts, and protected hashes were retained in the tool-session record. Nothing was cleaned, attributed to this mission without evidence, or reset. Process inspection required the tool's read-only `ps` permission; no process-control operation occurred.

## 5. What the existing recovery evidence already says

These observations are sufficient for the Phase-0 comparison. They are **not** a newly completed developmental-state census.

### A real acquired witness already exists

[Skill B's acquisition record](../memory/experiments/skill_ledger/accumulation/qualify_b_result.json) identifies a failed candidate returning sorted tuples and a passing candidate projecting the names. The retained transformation was mechanically extracted from that machine-generated pair; the extractor itself was investigator-authored. Its recorded content hash is:

`1f5ce81e6d31a68cf0427f8d566977c45f648af17b280d8698c83965ef6bfbd0`

The [restart record](../memory/experiments/skill_ledger/accumulation/restart_check_b_result.json) records that same hash and PID 38664. The actual [driver](../app/experiments/skill_ledger/accumulation.py:245) loads the saved skill. Its transfer path reloads the skill and checks the frozen hash before applying it. The [true arm](../memory/experiments/skill_ledger/accumulation/transfer_b_true_result.json) reports two original failures changed to passes; the [substitution arm](../memory/experiments/skill_ledger/accumulation/transfer_b_substitution_result.json) reports two failures without skill use.

This supports **state reload and a bounded causal contribution**, rather than file presence alone. It is not a full isolated successor: these historical runs used the existing installation and its dependencies; the substitution path regenerated candidates under matched settings rather than constituting a complete machine-recovery control. Do not promote it to full RBQ1-A.

Skill A likewise has selected 4/4 versus 0/4 transfer evidence, with only two distinct selected code bodies, and a production consumer. Its recorded useful effect and its demonstrated harmful match both survive as evidence. Recovery of that exact state would preserve a potentially harmful rule too; successful copying would not repair its jurisdiction.

### Limited developmental-state/coverage register

This register summarizes inspected current source and existing evidence. **Phase 2's exhaustive producer/consumer/load/write census was not undertaken after STOP.** D1 means experience-dependent state capable of affecting behavior, not automatically beneficial acquired competence.

| State/object | Class | Consumer / influence | Present preservation and reconstruction limit |
|---|---|---|---|
| `memory/skill_ledger/skills/*.json` and experimental skill records | D1 edit contents; D2 lifecycle/provenance fields | Generic skill loader/matcher/applicator; loaded on consultation | Local files; narrow reload/use evidence. Not included in the seven-artifact snapshot list. Cannot reconstruct the exact acquired edit from source alone without its experience or state |
| `memory/river_brain.pkl` statistics, classifier/scaler objects | D1 adaptation | Loaded by RiverBrain; model/task means affect ranking | Included in snapshots; exact current recovery/freshness not tested here. Trained values are not a source-only reconstruction |
| Vector memory index plus metadata, configured by `app/lib/vector_memory.py` and memory bridge | D1 experience content; D2 index/ID relationships | Retrieval affects available context | Same-machine persisted pair; outside scoped snapshots. Rebuilding embeddings requires original content and compatible embedding configuration |
| `memory/self_model_claims.jsonl`, `memory/behavioral_directives.json` | D1 recorded corrections/directives; origin may be external | Verified fact/directive prompt consumers | Local persistence; not proof of autonomous acquisition; outside the seven-file snapshot scope |
| Task classifier's trained object and configured persistence; Bayesian news-history/posterior | D1 adaptation; exact complete boundary D5 in this stopped mission | Task routing and surprise/state consumers | Source shows mechanisms; their complete restorable dependency sets were not re-inventoried |
| Model digests/configuration, source versions, schemas, feature meanings | D2 interpretation dependencies / D3 reconstructable scaffold when available | Interpret or execute D1 | Git and installed environment preserve parts. Source does not recreate model bytes or learned values by itself |
| Governance hashes, lifecycle history, trust flags, relevant provenance and evaluation artifacts | D2 | Determine legitimate authority and evidentiary meaning | Some governance files are snapshotted; no complete joined successor manifest qualified |
| Pending requests, queues, caches, in-flight updates | D4, with potentially durable consequences | Runtime operations and eventual writes | Not equivalent to acquired competence; interrupted work and write durability remain separate questions |
| Remaining persistent/semi-persistent artifacts | D5 for RBQ-1 | Not exhaustively traced | Unknown rather than silently excluded |

Current [snapshot source](../app/core/snapshot_manager.py) covers `self_edit_generated.py`, `river_brain.pkl`, principles and their hash, `Modelfile`, `COUNCIL.md`, and its hash. Historical restore logs contain one success and three failures, not a full current-state qualification. The [September 20 recovery plan](2026-09-20_feralecho_verified_backup_and_recovery_plan.md) is explicitly design-only. Later clean-checkout publication qualification closes some source-dependency gaps, not all learned-state or disaster-recovery gaps.

**Brutal loss:** if the M5 disappears and no verified external copy contains these artifacts, its unique skill/experience state, vector corpus/relationships, learned statistics, corrections/directives, evidence history and unfinished work can be lost. Static source or a base model does not recreate those exact experiences. Whether additional external vault copies now exist is **UNDETERMINED** from this review; I did not scan destinations, contact another node, or presume that same-disk snapshots survive machine loss. This is a preservation risk, not a demonstrated recovery failure.

## 6. Disposition of the requested recovery phases

| Requested deliverable | Actual status |
|---|---|
| Strategic gate and critique comparison | Completed; STOP |
| Repository/runtime protection baseline | Recorded |
| Complete developmental-state register and coverage matrix | Not completed; limited evidence summary above only |
| Recovery-equivalence specification and hash | Not created; no recovery protocol frozen |
| Selected experimental witness and source-state manifest/hash | No RBQ-1 witness selected or manifest frozen; B reviewed as existing evidence |
| Disposable successor, restoration and isolation qualification | Not constructed; no files copied into a successor |
| R1 structural / R2 referential / R3 learned-state tests | Not run |
| R4 capability / R5 behavioral / R6 governance tests | Not run |
| Mandatory RBQ-1 negative control | Not run; historical ablations are not relabelled RBQ-1 trials |
| Recovery-vs-reconstruction classification | UNRESOLVED for a new isolated successor; prior narrow state-dependent reuse is supported |
| External-agent independence test | Not run; source shows deterministic skill consumption needs no frontier API, which does not prove complete recovered-Echo operation |
| Studio timeout | UNDETERMINED; no resend, reproduction, or new log branch after the strategic stop |
| RB1–RB8 failure taxonomy | No recovery failure observed or assigned |
| RBQ1-A–X experimental disposition | Not assigned: Phase 18 was not entered |
| Model calls / recovery trials | **0 / 0** |

The timeout symptom and Echo's denial cannot distinguish failed ingress from completed work whose response/history was lost. Existing source establishes that work can outlive client patience, but that does not classify this particular incident. It remains UNDETERMINED here.

## 7. Revised priority and stop decision

**STOP RECOVERY RESEARCH — MOVE ON** for this mission. This does not certify complete recovery or retire ordinary backup obligations.

| Rank | Next move | Reason |
|---|---|---|
| 1 | Jurisdiction/safe-applicability **measurement qualification** | Settle the concrete execution-boundary and name-label shortcut before relying on the new judge; then decide the stored skill's permissible use |
| 2 | Attribution/credit integrity | Existing fallback/retry mismatches can make reward wiring reinforce the wrong actor |
| 3 | Honest net-utility benchmark | Highest strategic discriminator once measurement and permitted use are trustworthy |
| 4 | Bounded recovery repair/qualification **if a concrete preservation or portability gap requires it** | No new RBQ-1 failure established; preserve operational urgency if there is no external recoverable copy |
| 5 | BA-4 interpretation/closure | Reconcile the two recorded cases under a trustworthy instrument; do not expand the cohort or infer autonomous applicability learning automatically |
| 6 | Fresh acquisition | Conditional on reliable usefulness and measurement |
| 7 | Accumulation | Still lacks a safely useful, reliably measured unit to accumulate |

**Recommended next mission:** independently qualify the BA-3 instrument's real execution boundary and whether its verdict survives input names that do not identify the expected winner. Use bounded deterministic discrimination, preserve existing BA-3/BA-4 artifacts, and separate property detection from safe repair authority. This report does not authorize or perform that repair/test. No general sandbox redesign or new learner is implied.

Reopen recovery research only for a decision such as: an actual off-device recovery package needs acceptance; the source/state version changes enough to threaten interpretation; an essential state cannot reload; or a one-witness clean successor would decide whether a deployment/migration may proceed. A broad catalogue of other potentially interesting state is insufficient by itself.

The original linear ordering **recovery → jurisdiction → utility does not survive unchanged**. Jurisdiction's actual measuring instrument needs attention first. Limited recovery remains worthwhile when it has a specific acceptance decision; comprehensive recovery is not a scientific toll gate for every component test.

## 8. Plain answers and methodological self-audit

* **What is developmental state?** Experience-dependent skill/edit values, adaptive statistics, retained experience/corrections and their interpretation/authority dependencies. The exact full-system boundary was not established in this stopped mission.
* **Which parts are acquired rather than scaffolding?** The demonstrated edits and trained/statistical values are experience-derived. Extractors, schemas, routing algorithms, models and governance code are scaffolding; externally authored instructions must retain that provenance label.
* **What is preserved and what is missed?** Local files and scoped snapshots preserve some state. VSL, vector state and several other influence channels are outside the snapshot list. Complete externally recoverable coverage is unverified.
* **What smallest experiment answered RBQ-1?** None. Repository/source inspection answered its prior question: another mission now dominates. The original full recovery question remains open.
* **Can a successor recover learned consequences?** Existing reload/use/ablation evidence supports a narrow yes in the existing installation. A fully isolated successor and disaster-loss recovery were not demonstrated here.
* **Do negative controls establish state dependence?** Historical skill controls support the bounded effect. No new recovery control was run; no generalized native-capability confound was ruled out for a reconstructed full Echo.
* **Can behavior be reconstructed without learned state?** Base-model and static-scaffold capabilities can. The historical selected repair improvements disappear without the learned edit. These are different observations.
* **Can capability survive while provenance or authority is lost?** Yes in principle: the applicator can use an edit without reconstructing its full evidentiary history. This mission did not perform that loss intervention. Capability equivalence would not suffice for governance equivalence.
* **Does recovery depend on hidden machine state or external agents?** Complete dependencies remain unqualified. Deterministic skill consumption has no frontier-agent requirement; this does not establish the entire recovered system's independence.
* **What disappears after machine loss?** Unique state and history absent a recoverable external copy; the presence and adequacy of such a copy is unknown here. Do not confuse process restart on the same disk with surviving loss of that disk.
* **Did the Studio timeout persist anything?** UNDETERMINED. Echo's verbal account is not lifecycle evidence.
* **Was Grok's research-pathology warning justified?** Yes as a decision-discipline warning supported by the serial diagnostic history. It does not establish that compute is irrelevant or all prior work was wasteful.
* **Did this mission change a decision?** Yes: it rejected my earlier unconditional recovery-first priority and located concrete defects in the next proposed measurement basis.
* **Did we stop when the lesson became clear?** Yes: no successor, freeze, recovery trial, new model call, or repair was undertaken after the Phase-0 stop.
* **Could 80% of the value come from 20% of the work?** Most value came from one actual function trace and checking for raw BA-4 outputs, not from a broad state inventory. Future missions should begin with those load-bearing paths and a decision gate. The preliminary report reading could have been shorter; it is not necessary to turn this finding into another full architecture audit.
* **Developmental persistence or just files?** The existing research supports **narrow acquired-state-dependent reuse beyond file presence**. RBQ-1 adds no new recovery demonstration, and complete developmental recovery remains unqualified.

## 9. Integrity and exact files created

Only `audits/2026-09-30_rbq1_retained_state_boundary_recovery_qualification.md` was created by this mission. No previous report was edited. No production/experiment code, live memory, RiverBrain, VSL, watchdog, LaunchAgent or relay state was intentionally changed. Nothing was staged, committed, pushed, reset or cleaned. Exact inference count: **zero**.

Closing check at **17:08:16 PDT**: HEAD and cached `origin/main` unchanged; staging empty; the only added working-tree entry is this report. **863 of the 864 baseline files were unchanged**, including the prior strategic audit, BA instruments, experimental evidence in the protected set, and production VSL records. The one changed file was the live `memory/river_brain.pkl`: SHA-256 changed from `6bd167f39f21bbb8b0a1218e504992c646630b6dbbb3ca5805f59da384c5e5ec` to `382575808fbe6808dc38877b458272da519f1e8f7c181a47018d6d5d47a61c56`. Echo remained running, so live state was not a frozen snapshot. This mission only read that file; it did not import RiverBrain or issue a state-writing command. The precise external write was not investigated, and the change is disclosed rather than described as global state immutability.

Echo, watchdog and Ollama retained the same PIDs and start times at closing. All actual Markdown evidence links resolve; a simple link-pattern scan also matched `ns[fn_name](entries)` inside the source-flow code block, which is code rather than a link. The report is untracked and unstaged. No recovery apparatus was created.

**Final decision: STOP — ANOTHER PRIORITY NOW DOMINATES.**
