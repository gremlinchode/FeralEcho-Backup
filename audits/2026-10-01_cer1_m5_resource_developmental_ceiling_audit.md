# CER-1 — Compute, engineering and developmental resource ceiling

October 1, 2026 · America/Los_Angeles · Read-only audit with additive evidence files.

## 1. Decision

**CER1-LEARNING**

**SPEND $0 — EXHAUST EXISTING HEADROOM**

The dominant **developmental** constraint is the incomplete conversion of experience into reliably useful retained competence. FeralEcho can acquire and reuse narrowly scoped executable changes. It has not established that increasing its experience budget predictably increases useful competence after harmful applications, non-matches, failed acquisition, retention and cost are counted.

The M5 is nevertheless imposing a **real operational memory constraint today**. The machine has 24 GiB of physical unified memory; passive samples showed about 22 GiB in use, compression, swap traffic and repeated memory-driven Ollama model evictions. It is wrong to describe the whole machine as mostly unused merely because CPU samples show substantial idle time. It is equally wrong to infer from paging that a hardware upgrade would close the learning chain.

No reviewed result identifies a next justified acquired capability that is prevented specifically by this machine. Memory expansion would plausibly improve model residency, concurrency and some latency. Stronger models might improve induction or code generation. Neither has yet demonstrated a corresponding improvement in **retained net capability** here.

**Next action:** one bounded, independently scored net-utility comparison of existing retained-state use against the same capable local model without that state, on an unselected workload. Count fixes, regressions, abstentions/non-matches, timeouts and total inference cost. Keep it disposable; do not activate production repairs. Stop expanding acquisition or applicability research until this comparison changes a decision.

This disposition is a **STRONG INFERENCE**, with moderate confidence in ranking learning above the closely coupled architecture/evaluation constraints. It is not a randomized hardware ablation or proof that compute is irrelevant. Confidence is high that the inspected measurement defects and harmful AST edit would not be repaired by faster execution.

## 2. Evidence and opening integrity

Evidence categories throughout: **DIRECT** means current source/artifact/OS observation; **DOCUMENTED** means a historical report, qualified where not independently reconstructed; **INFERENCE** and **SPECULATION** are distinguished explicitly.

| Item | Observation |
|---|---|
| Opening observation | 2026-10-01 05:04:25 PDT |
| Branch | `vsl-implementation` |
| HEAD | `e5acbb09cece8d1791fa6d967fe57067137a8cff` |
| Cached `origin/main` | `efeb565b3221eb6ff9d7a65a3c9f3232f16806d0` |
| Ahead/behind cached remote | 4 / 0; no fetch or remote mutation |
| Staging | Empty |
| Echo | PID 71538; started September 28, 19:15:54 PDT |
| Watchdog | PID 56610; started September 28, 09:44:38 PDT |
| Ollama server | PID 1991; started September 19, 10:57:03 PDT |
| Ollama application | PID 1984; started September 19, 10:57:01 PDT |

Eleven tracked modifications already existed: `CLAUDE.md`, `PENDING_DECISIONS.md`, `app/core/self_edit_convergence.json`, `app/core/self_edit_generated.py`, `app/core/temporal_environment.py`, three relay files (`.last_seen_from_air.json`, `.last_seen_from_air_hub.json`, `from_m5.md`), `logs/janitor_report.json`, `sandbox/scripts/temp_self_edit.py`, and `staging/self_edit_candidate.py`. Numerous untracked research directories and reports also pre-existed. They were not cleaned, rewritten or attributed to CER-1. Full status and protected source/VSL hashes are in the [baseline](cer1_20261001/baseline.json).

Primary audit evidence:

* [Opening observations/model metadata](cer1_20261001/opening_observations.json), [second passive observations](cer1_20261001/second_observations.json), and closing integrity record in the same directory.
* [Historical timing extraction](cer1_20261001/historical_timings.json), with source hashes and every timing row; no new inference.
* [Filtered Ollama telemetry](cer1_20261001/ollama_passive_excerpt.json), [event recount](cer1_20261001/log_counts.json), [state/storage sizes](cer1_20261001/storage.json), [result recount](cer1_20261001/evidence_recount.json).
* [Strategic audit](2026-09-30_feralecho_strategic_research_audit.md), [RBQ-1](2026-09-30_rbq1_retained_state_boundary_recovery_qualification.md), [AIQ-1](2026-09-30_aiq1_applicability_instrument_qualification.md), [BJQ-1](2026-10-01_bjq1_bounded_skill_jurisdiction_qualification.md), their raw results, VSL acquisition/transfer/accumulation artifacts, and the older ceiling investigations cited below.

No production module was imported to inspect its state. No pickle was deserialized. No Echo request, learner, candidate execution, benchmark or recovery experiment was run. Ollama requests were metadata-only: version, installed/loaded models and model descriptions. **Additional inference calls: 0.**

## 3. Strategic revalidation: what is actually demonstrated?

| Claimed limitation or capability | Strongest relevant evidence | Current explanation | Would more compute plausibly help? |
|---|---|---|---|
| Experience-derived repair is possible | Skill A prospective selected cases: 4/4 repaired versus 0/4 without state; only two distinct saved bodies | Real narrow system-level acquisition/reuse; selected coverage, not broad competence | More candidates could find more pairs; benefit is conditional, not established scaling |
| A second retained repair exists | Skill B 2/2 versus 0/2; matching hash in restart record | Persistent executable transformation; not proof A caused B's acquisition | More inference is unnecessary to replay the demonstrated capability |
| Accumulation | A-present 4/8 versus 3/8 without A; one repaired case; B extracted from unaided candidates | Some reuse, no established learning-to-learn or broad accumulated advantage | Larger sample could resolve uncertainty, but cannot change B's historical causal provenance |
| Harmful Skill A application | BJQ-1: G 6/20→20/20; H 20/20→9/20 | H never had the target defect. Identical syntax hid opposite numeric priority encodings | No: faster execution of the same edit preserves the harm |
| Applicability measurement | AIQ-1: correct/reversed controls separated; five trivial shortcuts rejected under opaque names and isolated execution | A bounded measurement concept is qualified; arbitrary repair authority is not | No additional model compute was needed |
| BA-4 | Two frozen predictions have historical BA-3 agreement, per preserved raw artifacts examined in RBQ-1 | Finite evidence still carries the original BA-3 boundary caveat; AIQ/BJQ did not remeasure BA-4 | More predictions would not remove the caveat |
| Equality/relational induction | Original qualification oracle 87.5%, below 90%; short prompts and complete outputs | Model/presentation/representation limitations, not established context exhaustion | A different, stronger model might help; faster identical inference does not fix the semantics |
| Natural persistent adaptation | [Natural-learning hunt II](2026-09-29_natural_learning_event_hunt_ii.md): rolling statistics survive an actual restart; no demonstrated new improvement | Adaptive statistics are real; improved routing or acquired competence was not established in that window | More observations may update the same weak signals faster |
| Full developmental recovery | RBQ-1 stopped before a recovery experiment | Narrow reload evidence exists; complete successor/off-device recovery remains unqualified | Not shown to be compute-blocked |
| Current whole-system net advantage | No inspected unselected, cost-matched retained-state utility result closes this claim | Missing decision-grade evidence and safe-use closure | Existing hardware can conduct the next bounded comparison |

Counts were independently re-read from the [prospective](../memory/experiments/skill_ledger/prospective/true_result.json) and [accumulation](../memory/experiments/skill_ledger/accumulation/a_present_result.json) outputs and their absent-state controls. [B extraction](../memory/experiments/skill_ledger/accumulation/qualify_b_result.json) names unaided failing/passing bodies; [the driver](../app/experiments/skill_ledger/accumulation.py:185) extracts their AST difference. [B restart](../memory/experiments/skill_ledger/accumulation/restart_check_b_result.json) preserves the same content hash. These are stronger evidence than stored prose instructions, but a few selected cases do not supply a learning curve.

BJQ-1 changes the strategic interpretation: **this counterexample does not demand inventing another compatibility architecture**. Behavioral defect detection already excludes H. The broader distinction between detection and repair authority remains valid, but the two-case operational lesson is sufficient. Do not automatically fund BJQ-2, more Boolean explanation searches, or fresh accumulation runs.

### Historical “no sustained competence growth” reassessment

The older conclusion was an evidence boundary, not a measured silicon limit. [Phase 1.5](2026-09-06_phase1.5_capability_ceiling.md) found functional outcomes discarded before relevant decisions and weak scoring. The [September 17 investigation](2026-09-17_recursive_learning_ground_truth_investigation.md:875) identified reward/decision, task-context, benchmark and memory-identity failures and explicitly left sustained growth unproven. Neither establishes that a faster chip would close those missing causal connections.

Later VSL evidence narrows older statements that no acquired executable competence exists. It **does not overturn** the absence of demonstrated sustained useful growth. Nor should historical project failure rates, dead pathways or previously fixed defects be presented as current measurements without revalidation.

The older [hardware audit](echo_capability_ceiling_hardware.md) overreached in four places:

1. “Every model is context-starved” is false as a universal statement: `echo:latest` and its Llama 3 parent advertise 8,192 native context, matching the current configured window. Larger advertised windows elsewhere do not demonstrate a task that benefits from using them.
2. Unused concurrency was attributed entirely to an environment variable. Current source also queries councillors serially; memory admission actually evicts models. More server slots alone do not parallelize that Python loop or make memory free.
3. The absolute 8B practical limit was not measured. A 12B MLX model is cached and historically used, though now retired for reliability. This does not prove it can run usefully alongside today's workload; it does invalidate an unsupported universal cutoff.
4. No thermal warning is not a sustained thermal benchmark.

These reports remain unchanged as historical evidence.

## 4. Verified M5 envelope and live utilization

### Hardware, CPU and acceleration

**DIRECT:** `sysctl` and filtered `system_profiler` identify Apple M5, MacBook Air, `Mac17,3`, ten physical/logical CPU cores (four performance, six efficiency), ten integrated GPU cores, Metal support, and **25,769,803,776 bytes = 24 GiB** unified memory. The root/data APFS container reports 926 GiB, consistent with the nominal 1 TB drive. No serial numbers or machine UUIDs were preserved.

The preserved `top` snapshots showed **75% CPU idle** at 05:04:57 and **60–85% idle** at 05:16:32–33. These are snapshots, not a duty-cycle profile. GPU utilization percentage and memory bandwidth saturation were **not measured**. CPU idleness does not imply idle GPU capacity.

Ollama telemetry directly records **33/33** or **29/29 layers offloaded to the GPU**, Metal allocations, `n_seq_max=1`, and one slot per sampled runner. This is actual GPU execution, not merely availability of an accelerator. The backend uses Metal; no inspected path schedules the LLM onto the Neural Engine. Unused Neural Engine capacity is therefore not a demonstrated free speedup. [Ollama's hardware documentation](https://docs.ollama.com/gpu) corroborates Metal as its Apple GPU path.

### Memory and processes

| Observation | Value and interpretation |
|---|---|
| `top` physical memory | About 22 GiB used; approximately 1.4–1.7 GiB unused in the sampled intervals |
| Wired memory | Roughly 8.5–8.8 GiB in those `top` samples |
| Compression | About 2.2 GiB in the first `top` sample, 5.5 GiB later; values fluctuate substantially |
| Swap allocation | 4 GiB; used 2,912.75 MiB at 05:04:57 and 2,640.75 MiB at 05:14:34 |
| Actual paging, 05:04:57→05:16:33 | Counter deltas: **1,065.00 MiB swap-in and 2,662.38 MiB swap-out** over 696 seconds, using 16 KiB pages |
| `memory_pressure -Q` | Reported “memory free percentage” 34%, later 31%; not interchangeable with free physical pages or guaranteed admission headroom |
| Echo RSS | Approximately 1.5–2.05 GiB in the 05:00-hour observations; 1.18 GiB at the later 11:29 integrity check. CPU varied from 0.1% to 76.8% of one core in sampled `ps` records |
| Ollama runner RSS | About 6.18 GiB initially, 5.61 GiB in a later runner; different model-loading episodes |
| Ollama server / watchdog RSS | About 25 MiB / 320 KiB in targeted later observations |

RSS, mapped model files, Metal allocations, compressed pages and unified memory must not be summed as if independent. These are sampled footprints, not measured lifetime peaks. Historical peak working set: **UNMEASURED — REQUIRES FOLLOW-UP only if a justified workload needs it**.

The filtered recent Ollama slice spans approximately **03:27–05:12 PDT**. A mechanical recount identifies **37 explicit memory-eviction events** and **20 “fits alongside” events**. Seven explicit evictions occurred after the audit's 05:04:25 opening and before the excerpt ended. The scheduler repeatedly reports `system_limited=true`; for example, at 05:07:56 it sought about 4.8 GiB while reporting only 3.6 GiB system availability. Occasional successful coexistence means “multiple models can never fit” is also too strong.

**Conclusion:** 24 GiB is consequential for current model residency and paging. The system is not continuously failing to operate; it accommodates demand by loading, evicting and compressing. This audit does not isolate how much elapsed latency is due to paging versus token generation, nor establish a user-defined acceptable latency threshold.

### Thermals

Privileged `pmset -g therm` reported no recorded thermal/performance warning and no CPU power status. That does **not** establish absence of frequency reduction or a sustained fanless performance ceiling. No temperature/frequency time series, controlled cold/hot comparison or load-normalized throughput history was available in the inspected evidence.

**C10: UNKNOWN.** Variation in live tokens/second is not thermal evidence: models, prompt lengths, output lengths, caching and concurrent activity differ. No stress test was justified because it would not change the immediate $0 decision. Historical MLX GPU errors are not proof of thermal throttling.

## 5. Installed model and inference envelope

Ollama reports **0.34.2**, not the older audit's 0.30.10. Metadata below is current; advertised context is not an observed useful operating point.

| Installed model | Parameters / quantization | Artifact size, approximately GiB | Advertised context |
|---|---|---:|---:|
| `echo:latest` | 8.0B / Q4_0; Llama 3 Instruct parent | 4.34 | 8,192 |
| `llama3:instruct` | 8.0B / Q4_0 | 4.34 | 8,192 |
| `llama3.1:8b` | 8.0B / Q4_K_M | 4.58 | 131,072 |
| `qwen2.5-coder:7b` | 7.6B / Q4_K_M | 4.36 | 32,768 |
| `deepseek-r1:7b` | 7.6B / Q4_K_M | 4.36 | 131,072 |
| `mistral:latest` | 7.2B / Q4_K_M | 4.07 | 32,768 |
| `gemma3:4b` | 4.3B / Q4_K_M | 3.11 | 131,072 |
| `llama3.2:3b` | 3.2B / Q4_K_M | 1.88 | 131,072 |
| `qwen2.5:3b` | 3.1B / Q4_K_M | 1.80 | 32,768 |

These are artifact sizes, not full working sets; shared Ollama blobs must not be counted twice. At 05:06:21, `/api/ps` showed one resident DeepSeek runner: **4.92 GiB**, all reported in `size_vram`, allocated context **8,192**. On unified memory, this is not a separate physical VRAM pool.

Additional cached MLX weights: Qwen3-8B-4bit about **4.31 GiB** of blobs; Gemma-3-12B-4bit about **7.51 GiB**. [Configuration](../mlx_models.json) lists both. [MLX source](../app/mlx_handler.py:30) retains an 8 GiB Metal allocation cap, one global generation lock and a model cache; Gemma 12B is explicitly retired after historical GPU reliability problems. Cache presence is not a current successful 12B capability test. The documented natural restart on September 28 also involved an MLX-signature crash; allocation, implementation and workload contributions remain unresolved, so more RAM is not a proven cure.

### Actual inference times, without new calls

Two **complete existing cohorts**, chosen by mission provenance rather than speed, were recounted:

| Historical cohort, `qwen2.5-coder:7b` | Calls | Wall time median / range | Decode rate median / range | Load time median / maximum |
|---|---:|---|---|---|
| Original qualification, `20260929_resume_v1` | 9 | 1.84 s / 1.81–4.57 s | 25.16 / 23.81–25.90 tok/s | 0.005 s / 1.602 s |
| Same-value diagnostic, `20260929_codex_v1` | 24 | 1.64 s / 0.43–2.46 s | 25.92 / 18.74–28.31 tok/s | 0.001 s / 0.850 s |

All returned `done_reason=stop`. The nine calls totaled **21.02 seconds** recorded wall time, 264 generated tokens; the 24 totaled **40.03 seconds**, 239 tokens. Prompt counts were approximately 635–661 and 499–561. Both diagnostic configurations used temperature 0, `top_p=1`, **4,096 context** and a 768-token output cap; the original qualification used its frozen per-call seeds and the same-value diagnostic used seed 881010. These research configurations are distinct from production's common 8K context. The [same-value driver](../app/experiments/same_value_prior/diagnostic.py:20) supplies the latter options; its requests are embedded in its protocol rather than individual `.request.json` files. These tiny outputs are **not a sustained generation benchmark**, and cached inputs/loads change timing. The nine-call semantic qualification failure was not caused by days of infeasible computation, prompt overflow or incomplete output.

During normal live activity around 05:06–05:09, server logs show roughly **16–24 generated tokens/second** and **260–324 prompt tokens/second** in inspected slots. One 1,016-token generation took **62.76 seconds** decoding, plus **9.29 seconds** prompt evaluation. This explains how several serial opinions, synthesis, retries and queueing can create appreciable user latency even though small diagnostics are cheap. It does not assign a uniform throughput to all models or prove thermal degradation.

### Context and concurrency are coupled costs

Production calls commonly specify `num_ctx=8192` ([handler](../app/ollama_handler.py:176)); [deliberation](../app/core/river_deliberation.py:58) also budgets/truncates to that window. More server memory alone would not enlarge these explicit application budgets. Echo's native model window would still need a compatible model or a separately justified change.

Observed KV allocations were **1,024 MiB** for the sampled 32-layer Llama runner and **448 MiB** for the 28-layer Qwen-family runner at 8,192 context. Under the same full-attention/F16 assumptions, four times context would require roughly four times KV storage, before scratch space and weights; 131,072-context Llama 3.1 would imply about **16 GiB of KV alone**. This is illustrative memory arithmetic, not a promise of useful long-context execution or a recommendation to enlarge Echo's native window.

Ollama documents that parallel sequences increase context memory, and concurrent model admission depends on available memory. [Official FAQ](https://docs.ollama.com/faq). Current observed runners already provide the more relevant local fact: one sequence slot, with frequent memory-driven admissions/evictions. Blindly enabling parallelism, increasing context or changing cache quantization could worsen contention or change reproducibility. None was changed.

## 6. Storage, I/O and recovery cost

**DIRECT:** about **671 GiB free**, with Data using about **210 GiB** in the 926 GiB APFS container. Root and Data share space; their capacities must not be added.

| Stored material | Approximate size |
|---|---:|
| Ollama unique model directory (`du`) | 28.51 GiB |
| Named MLX model blobs, combined | 11.82 GiB |
| `memory/`, including research/state/history | 1.33 GiB |
| `memory/experiments/`, already included above | 66.3 MiB |
| Live FAISS index / metadata | 200 MiB / 104 MiB |
| RiverBrain pickle | 4.5 MiB |
| Source `app/` / `.git/` | 14.9 MiB / 36.1 MiB |

The preserved second-window one-second disk sample was **0.93 MB/s**. The first `iostat` row is a since-boot aggregate and was not used as current throughput. No storage-capacity ceiling is visible; there is no benchmark proving the disk's bandwidth ceiling or ruling out bursts.

There is a relevant architecture scaling issue: [VectorMemory](../app/lib/vector_memory.py:181) rewrites full metadata and index on persistence, called after additions. At present sizes that represents roughly 304 MiB of logical serialization/write content per full persist, not necessarily that many physical NAND bytes each time. Its search is a single-threaded exact inner-product index. These facts justify watching write/recall latency as state grows, **not replacing storage now**. No per-component profile establishes retrieval or writes as the current dominant wait.

Recovery is chiefly a **boundary/verification problem**, not a volume problem at these state sizes. RBQ-1 did not qualify an off-device successor; free space does not prove developmental recoverability. Extra SSD capacity would not decide which values, provenance and authority must survive. Conversely, a backup on the same lost machine is not an off-device backup. No backup was created or changed here.

## 7. Where resources go

No exact percentage attribution is claimed: this was not a profiler run. The source and sampled runtimes support this map.

| Workload | Implemented path / observed cost | Current limiting factor |
|---|---|---|
| Local generation | Ollama Metal; measured token/load times; cached MLX backend | Model quality, GPU inference, residency/queue latency |
| Council and synthesis | [Serial councillor loop](../app/core/river_deliberation.py:1288), then synthesis; independent background callers | Request multiplication and scheduling as well as inference; speed does not prove ensemble value |
| Candidate generation | Local inference in experiments/projects/self-edit | Cost per useful evaluated candidate; model quality and failure handling |
| Embedding | Shared [MiniLM singleton](../app/core/sentence_transformer_singleton.py); no explicit device selected there | Small model, actual device/utilization unmeasured; duplicate-load optimization already exists |
| Retrieval | 384-dimensional `IndexFlatIP`, one FAISS thread; metadata filtering | State quality/applicability and potential size scaling; not shown CPU-bound now |
| Memory writes | Full index/JSON persistence plus journals | Potential write amplification and coherence; no causal latency profile |
| RiverBrain | Online trees/scalers, rolling task/model means; writer coalesces saves | Quality/attribution of feedback, not an expensive training job |
| VSL matching/application | Stored JSON and AST traversal/edits | Jurisdiction, trusted labels, retained-state provenance; compute small in these cases |
| Independent evaluation | E0.1 child executions | AIQ-1 **192 calls in 7.26 s**; BJQ-1 O **80 calls in 2.07 s**, from timestamps; semantics/isolation dominate qualification |
| Orchestration/autonomy | Several Python background loops, shared stillness/pressure checks and conversation yielding | Coordination, repeated low-yield attempts and investigator decisions; not evidence of productive CPU parallelism |
| Persistence/watchdog | Small state files; periodic/coalesced writes; watchdog process | Recovery correctness and failure attribution; watchdog footprint negligible in sample |
| Studio/API | Threaded serving; synchronous deliberation before response content | End-to-end request lifecycle, serial inference and client wait; extra CPU does not implement cancellation or persistence semantics |
| Frontier-agent collaboration | Research design, code/evidence review, occasional relays | Availability and human interpretation; more local FLOPs do not replace that function automatically |

The [Studio lifecycle report](2026-09-28_echo_studio_timeout_information_fate.md) traces a 300-second client read timeout around synchronous deliberation. This is evidence of a latency-sensitive path, not proof of the exact fate of the later strategic-report incident. More speed could reduce timeout frequency, but cannot itself correct cancellation/receipt/provenance semantics. No live request was sent to investigate it.

Two source-level limits on “more experience” matter:

* [RiverBrain.learn](../app/core/echo_model_orchestrator.py:810) commonly derives its label from `echo_quality_scorer`, not independent task correctness. A faster stream of outputs trains the same proxy faster. There are also sandbox-informed paths; do not describe every update as purely stylistic.
* The ordinary council path learns internally and the [caller also invokes `learn`](../app/core/echo_model_orchestrator.py:1585). Observation counts therefore cannot be treated as independent validated experiences. This source fact is not a measured marginal harm estimate.

Production VSL's [gate](../app/core/skill_ledger/runtime.py:44) defaults disabled, with shadow as the enabled default. No production `applications.jsonl` was present at inspection. That is evidence against claiming a demonstrated active lifetime skill-use loop, not proof of every live environment variable or of no possible alternate activity. Research-acquired Skill B and promoted metadata must not be conflated with natural production acquisition.

## 8. Historical failure counterfactuals

Question answered in each cell: would that resource change address the **identified failure mechanism**, not merely change a candidate or finish a run sooner? Fixed code/evaluator/state is held fixed except in the explicitly stronger-model column. `NO` is used where the defect is invariant to the resource change; `UNKNOWN` where causal evidence is absent.

| Historical limitation | 2× compute | 4× memory | Stronger model | Faster inference | Larger context | Mechanistic reason |
|---|---|---|---|---|---|---|
| BA-3 W/L answer channel and same-process execution | NO | NO | NO | NO | NO | The judge inputs and execution boundary remain defective |
| BA-1/2 aggregate pass/fail mislabeled as target property | NO | NO | NO | NO | NO | More samples do not correct a label definition |
| BJQ-1 harmful H edit | NO | NO | NO | NO | NO | Already-correct code plus unchanged deterministic sign removal still regresses |
| VECT externally authored P / reused underlying training content | NO | NO | NO | NO | NO | Historical authorship and overlap are provenance facts |
| A→B accumulation attribution | NO | NO | NO | NO | NO | B was derived from unaided outputs; that historical claim cannot be rescued by hardware |
| Original equality→AND generation | UNLIKELY | UNLIKELY | PLAUSIBLY | NO | UNLIKELY | Complete small-context outputs; model/representation behavior may change with different weights |
| Feedback-recoding/order sensitivity | UNLIKELY | UNLIKELY | PLAUSIBLY | NO | UNLIKELY | Evidence changes interpretation under short presentations, not capacity exhaustion |
| Natural self-edit failure statistics without improvement | UNLIKELY | UNKNOWN | PLAUSIBLY | UNLIKELY | UNKNOWN | More rejected attempts alone do not supply an acquired correction mechanism |
| Historical synthesis loses a correct candidate | UNLIKELY | UNLIKELY | PLAUSIBLY | NO | PLAUSIBLY | Selection/content budgeting can matter; model speed alone does not preserve correctness |
| New-world qualification's Ollama timeout | PLAUSIBLY | PLAUSIBLY | UNKNOWN | PLAUSIBLY | UNLIKELY | Could finish an interrupted measurement; does not make its semantic controls pass |
| Current memory-driven model eviction | UNLIKELY | PLAUSIBLY | UNLIKELY | PLAUSIBLY | NO | More capacity can reduce eviction; faster serving may shorten contention; longer context consumes more RAM |
| Historical MLX GPU crash | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNLIKELY | GPU error does not uniquely identify OOM, thermal, driver or concurrency cause |
| Unqualified full developmental recovery | NO | UNLIKELY | NO | NO | NO | Declaring/capturing/interpreting the correct boundary is the missing evidence |

None of the artifact-level `NO` rows implies a larger model can never produce better code. It means producing different code would be a different comparison and would leave the historical measurement/authority flaw intact. Faster completion of a timeout is an infrastructure improvement, not a positive learning result.

## 9. Compute-to-competence conversion

| Link | Present evidence | Remaining barrier |
|---|---|---|
| More inference → more outputs/experience | Established operationally | Need useful, sufficiently varied experience rather than duplicates |
| Experience → valid feedback | Works for some deterministic tasks; weak proxies elsewhere | Correct independent labels, actor credit, no leaked answers |
| Feedback → acquired representation | Narrow AST diff extraction demonstrated | Extraction depends on suitable passing/failing pairs and representable edits; no general learning rule established |
| Representation → persistent state | VSL files/hashes and River statistics | State is not synonymous with useful competence |
| Persistent state → fresh-process recovery | Narrow reload/ablation evidence | Full developmental boundary/off-device recovery unqualified |
| Recovered state → correct novel use | Selected A/B transfers | Harmful false matches; unselected coverage and rejection not established broadly |
| Use → net useful improvement | Selected positive cases; one clear harmful case | No appropriate workload-wide, cost-aware estimate |
| More cycles → accumulated improvement | Not established | Retention under interference and improved acquisition efficiency not demonstrated |

**Current break point:** the system has no demonstrated, reliable path from *additional ordinary evaluated experience* to *appropriately scoped retained changes that improve unselected later work*. It is not broken everywhere: narrow acquisition, persistence and transfer genuinely work. The failure is in treating those finite successes as a productive scalable developmental loop.

If local inference doubled tonight, current code could generate more candidates, opinions and observations, and some queues might drain faster. It would not automatically add independent correctness labels, derive a repair's jurisdiction, fix actor credit, activate a trustworthy acquisition pipeline, or prevent repeated bad learning. A frozen set of additional samples might find a useful diff pair; that is a plausible opportunity, **not a measured compute-to-competence conversion rate**.

A learning curve plotting retained held-out net utility against cumulative **validated** experience and total cost is absent. “Tokens/day,” a larger ledger, a higher River observation count, and more experiments cannot substitute for it.

## 10. $0 headroom: ranked, conditional opportunities

These are follow-up choices, not implemented optimizations. “$0” means no acquisition/service spend; engineering and attention remain costs.

| Priority / intervention | Bottleneck and evidence | Expected benefit | Engineering cost / integrity risk | Validation needed | Retained competence or just speed? |
|---|---|---|---|---|---|
| 1. One existing-state net-utility comparison | Selected gains and known harm leave utility unknown | Decide whether to preserve/extend this mechanism | Low–medium; medium risk if cases selected by outcome | Independent task oracle, same model/budget control, include all failures | Establishes value or lack of value; does not itself teach Echo |
| 2. Prefer deterministic assessment where already sufficient | AIQ/BJQ solved concrete questions in seconds, no LLM | Less inference expenditure and interpretation ambiguity | Low; no new universal evaluator implied | Reuse only within qualified property/boundary | Protects selection/retention quality; no automatic new acquisition |
| 3. Qualify bounded use/rejection of existing repairs, only if utility supports it | H harm was unnecessary application to defect-absent code | Avoid known class of false-positive harm | Medium; authority changes are consequential and separately authorized | G/H regression plus independent prospective useful cases, abstention counted | Could increase net useful retained performance without acquiring another skill |
| 4. Schedule approved research away from interactive/background contention | Actual eviction and serial multi-model traffic | Fewer cold loads/queues, cleaner timings | Low–medium; ordering affects reproducibility and needs freezing | Compare end-to-end elapsed time and exact outcomes under declared load | Primarily speed/reliability |
| 5. Compare existing smaller/direct routes before adding models | Installed 3B–8B pool; council overhead and superiority not established | Potentially equal quality at lower memory/time cost | Low–medium; route/model is a treatment, not an invisible optimization | Paired useful-task accuracy, harm and latency | Better inference efficiency unless acquired-state contribution is separately shown |
| 6. Test a larger window only on a demonstrated truncation-limited task | Explicit 8K budgets; some installed models allow more | Potential additional usable context | Medium; added KV, prompt changes, cache/state controls | First prove lost task-relevant information; compare fixed answers/utility | Potential inference gain; retained learning remains separate |

Do **not** presently prioritize parallel GPU requests, huge context, new quantization, a new vector store, extra model downloads or general CPU batching. Memory already constrains admission. Deterministic case execution already takes seconds. Embedding singleton reuse is already implemented. Caching may save repeated prompts but can contaminate timing/independence claims if undeclared. Full-index persistence may become important, but there is no measured per-call I/O bottleneck justifying a rewrite now.

**How much meaningful capability is available for $0?** No defensible percentage or number of future skills can be estimated. Existing hardware demonstrably supports the next discriminating utility/safe-use/reload measurements with small workloads. Avoiding H's known harmful edit is a concrete available improvement in net behavior, subject to separately qualified integration. Broad future competence growth remains unknown. This is decision-level headroom, not a claim that another 20 GiB of RAM is idle.

## 11. Existing Intel Mac

No Intel machine was contacted, awakened or queried. Its 2020 designation comes from the user; current CPU, RAM, storage, thermal state, dependencies and available capacity are **UNVERIFIED** here. The preserved [two-node forensic record](2026-09-24_feralecho_two_node_relay_stalemate_forensic.md:181) reports an older Air Echo instance, stale/different repository state and a historical pressure indicator of 1.0. That application indicator is not current OS telemetry.

**Do not integrate it into live inference or the acquisition path now.** The measured deterministic jobs take seconds on the M5; network scheduling, dependency parity and evidence synchronization could cost more attention than they save. MLX/MPS paths do not transfer as equivalent acceleration to an Intel machine; x86 versus arm execution must be treated as a new environment, not an identical worker.

Potentially worthwhile later: an **offline independent verifier or off-device restore witness**, receiving a frozen source/state package with hashes, producing separate outputs, and sharing no writable learned state. That buys fault-domain independence rather than raw throughput. First verify its suitability without restarting its existing Echo. Acquisition cost $0 does not imply operational cost $0. No distributed service or relay dependency is justified by CER-1.

## 12. Cost ladder, rent versus buy, and explicit dollar answers

No vendor shortlist, purchase, rental or speculative price quote is needed. All prices below are **budget tiers supplied by the mission**, not verified market offers.

| Budget tier | Capability that could justify spending | Present evidence / decision |
|---|---|---|
| $0 | Measure net utility, retain negative results, use existing deterministic controls, test current mechanisms in isolation | Enough for the next decision; recommended |
| ~$1–$100 | A bounded, protocol-frozen external compute comparison that local runs cannot answer, or a verified off-device preservation gap | Neither resource requirement/costed remedy established here; spend nothing now |
| ~$100–$500 | Occasional required model/workload exceeds local admission or a genuine backup medium is missing after checking existing resources | No demonstrated blocked developmental capability; no spend now |
| ~$500–$1,500 | Recurrent validated workloads make burst rental expensive, or verified recovery reliability requires dedicated capacity | Frequency, useful yield and alternative cost not established |
| ~$1,500–$3,000+ | A proven learning/utility advantage requires capacity or sustained service the M5 cannot deliver; ownership wins total-cost comparison | None of these gates has yet been met |

**Next $100:** NO CURRENT EVIDENCE JUSTIFIES THIS EXPENDITURE for developmental compute. A later capped comparison could justify it only after naming the blocked task, treatment and measurable outcome.

**Next $500:** NO CURRENT EVIDENCE JUSTIFIES THIS EXPENDITURE. More simultaneous residents alone is an operational convenience, not yet an independently valued developmental gain.

**Next $1,000:** NO CURRENT EVIDENCE JUSTIFIES THIS EXPENDITURE. A repeated successful workload and its acceptable latency/cost must exist first.

**Next $3,000:** NO CURRENT EVIDENCE JUSTIFIES THIS EXPENDITURE. “Run a bigger model” is insufficient; require demonstrated useful retained gain unavailable locally and recurrent demand.

These judgments concern the mission's developmental objective. Gremlin may value faster conversation or less waiting independently; this audit has not assigned that preference a dollar value.

For **rare research bursts**, a capped temporary model/compute comparison is ordinarily the lower-commitment way to test the missing premise. For **occasional validated bursts**, compare measured per-job cost and setup/transfer burden with ownership. For **continuous justified service**, more owned memory or sustained cooling may eventually be rational. A remote stronger model changes the inference treatment and may alter provenance/privacy constraints; do not use an external teacher while claiming autonomous local lesson acquisition. Core Echo operation must remain independent of the rental or frontier subscription.

Break-even must use observed demand: over a declared horizon, compare `purchase − residual value + energy + maintenance + operator time` against `useful burst count × all-in burst cost + transfer/setup time`. Count failed jobs. No useful job frequency or defensible all-in prices were established here, so a numerical break-even date would be fabricated. Twice-yearly work is not an argument for permanent ownership without a contrary cost/privacy requirement.

## 13. Measurable upgrade triggers

Thresholds below are **proposed decision gates**, not retroactive experimental pass criteria or established user latency requirements.

1. **Capacity:** an independently valid, useful workload requires a particular model/context/retained working set; repeated isolated attempts cannot fit without unacceptable paging or failure, while an otherwise matched larger-memory run succeeds. Record exact model/digest, context, concurrency and background state. Demonstrate that scheduling or an already installed model does not achieve the same useful outcome.
2. **Latency/throughput:** set an acceptable completion/interactive wait budget *before* measuring. At matched useful accuracy, at least three representative runs exceed it materially—e.g. by more than 2×—after low-cost scheduling is evaluated. Attribute the excess to measured token throughput/load/paging, rather than retries, unnecessary councils or a broken client lifecycle.
3. **Model quality linked to development:** a stronger model repeatedly produces independently validated retained-state gain on unseen cases after a clean boundary and ablation, within matched acquisition/selection budgets. If it only improves one-shot answers, classify and price that different benefit honestly.
4. **Sustained thermals:** a justified long workload shows repeatable load-normalized throughput decay or reliability loss linked to thermal telemetry; the resulting runtime violates the previously set budget. No such evidence currently exists.
5. **Economics:** useful workload frequency makes measured rental plus operational cost exceed ownership over a declared horizon, or independently specified offline requirements rule rental out. Hardware age or installed model size is not a trigger.

Gremlin's “now the M5 is the problem” event is the conjunction: **a useful validated capability, a measured resource-caused failure/latency violation on this M5, and a controlled demonstration that removing that resource limit enables the capability**. Current eviction satisfies part of the resource diagnosis; it does not yet satisfy the developmental-benefit test.

## 14. Separate distance-to-ceiling estimates

For nonhardware rows, “ceiling” means the boundary of the **current implemented/validated mechanism**, not an immutable limit on the project. No fake overall percentage is supplied.

| Dimension | Estimate | Evidence and qualification |
|---|---|---|
| CPU compute | MODERATE HEADROOM | Short samples mostly idle; seconds-scale deterministic tests. Sustained maximum unmeasured |
| GPU compute | UNKNOWN | Actual Metal offload established; utilization/bandwidth/saturation not measured |
| Unified memory / residency | NEAR CEILING for concurrent current workload | Compression, paging and repeated admission evictions; occasional coexistence still possible |
| Inference throughput | UNKNOWN relative to meaningful ceiling | ~16–28 tok/s observed in different workloads; no justified workload/SLO shown impossible |
| Useful model size | UNKNOWN | 3B–8B used, cached/retired 12B; no controlled largest-useful-model or stronger-model benefit test |
| Context | UNKNOWN as developmental limit | 8K production configuration; some longer-capable models; core diagnostics far below 8K; no demonstrated needed larger window here |
| Storage capacity / sampled I/O | FAR FROM CEILING in capacity | 671 GiB free and low sampled interval throughput; write bursts/latency not profiled |
| Thermals | UNKNOWN | No recorded warning; no sustained controlled telemetry |
| Architecture exploitation | NEAR CEILING of presently justified use | More concurrent outputs have no proven net benefit; serial/routing/state semantics constrain use |
| Learning mechanism | AT CEILING of currently validated scope | Narrow acquired changes work; predictable safe net growth beyond that scope not established. Not proof further growth is impossible |
| Evaluation methodology | NEAR CEILING of current claim authority | AIQ/BJQ qualified bounded questions; unselected utility and compute-to-learning attribution remain missing |
| Economic efficiency | UNKNOWN quantitatively | No cost per retained useful capability or workload-frequency accounting; enough local capacity for the next decision |

Taxonomy: **C6 is the primary developmental ceiling**; C5/C7/C8/C12 contribute. C3 is an observed operational constraint; C4 causes real waiting but is not established as the next capability blocker. C1 is not established for that next capability. C2 is plausible in narrow inference failures, not ranked dominant without a stronger-model comparison. C9 counsels against ownership before workload evidence. C10 is unresolved; C11 is not presently a demonstrated capacity blocker.

**Which comes first if development succeeds?** Scope-correct retained-state use and trustworthy net-utility measurement come first scientifically. If those succeed and demand grows, **unified memory/model residency and end-to-end inference latency** are the most evidenced hardware candidates, before disk capacity or deterministic CPU evaluation. Thermal limits could then matter, but their rank is unknown.

## 15. Counterfactual machines

| Machine/resource change | Faster existing work / larger experiments | Stronger inference or new capability | Additional retained competence |
|---|---|---|---|
| H1: same memory/software, 2× compute | Some acceleration; not necessarily 2× because memory bandwidth, loads, queueing and serial stages remain | Same weights/inputs/repair semantics; no automatic new capability | No established conversion mechanism at that scale; narrow additional sampling might help |
| 4× or 10× compute, still same state/architecture | More throughput if the bottleneck actually scales; could generate larger volumes of weakly evaluated work | Historical leakage, incorrect labels and deterministic harmful edits survive | No warranted proportional gain; amplification of bad selection is also possible |
| H2: same compute, 2×–4× memory | Plausibly fewer evictions, more resident models/KV, less paging; actual benefit needs controlled timing | Could admit larger contexts/models if software is changed and qualified; no automatic per-token speedup | Unproved; larger memory stores more state, including useless or harmful state |
| H3: substantially stronger machine and larger local models | Faster or larger approved work; better throughput depends on model chosen | Plausible stronger induction/code generation; might avoid some Boolean failures | Must demonstrate autonomous extraction, retention, selective use and ablation. Better answers alone do not establish this |

A stronger model could solve a demonstrated **inference** bottleneck, such as mishandling a short equality task. No reviewed controlled comparison establishes that it repairs the **developmental** bottleneck. It cannot remove an evaluator's answer channel or change the sign of an unchanged stored AST edit. A model which solves the task natively may also reduce the remaining measurable contribution of learned state; that is useful capability, with a different provenance.

## 16. Research economics and the shortest path forward

The scarce resource is presently **trusted conversion and decision capacity**: choosing useful experiments, qualifying outcomes, assigning credit and deciding when enough has been learned. Investigator availability, human review and debugging are qualitatively expensive, but no reliable time ledger permits percentage or dollar estimates. Inference latency is a real recurring operational cost; storage is not comparably scarce.

The timing contrast is instructive without pretending to measure human labor: the original nine development calls totaled 21 seconds, AIQ discrimination took seven seconds, and BJQ's outcome executions took two seconds. The surrounding qualification, attribution and interpretation were the substantive work. A 10× faster processor could not compress all of that work 10×. Repeatedly producing new explanation experiments after the operational lesson is known is C8/C12 consumption, not necessarily progress.

### PATH_TO_MEANINGFUL_M5_SATURATION

1. **Current blocker: unknown net value of retained-state use beyond selected successes.** Run one bounded, preregistered existing-state versus absent-state utility comparison with a competent identical-model control, independent evaluation and all failures/costs included. No new learning architecture is a prerequisite.
2. **Decision:** if retained state does not improve net utility, stop expanding it. Diagnose only the specific demonstrated mechanism or retire that application. Buying hardware would be premature.
3. **If useful, address the smallest demonstrated scope/credit/recovery gap.** A scoped safe-use change must beat the unchanged system without concealing abstentions or regressions. Narrow restart/off-device verification remains necessary before broad developmental continuity claims, but do not restart a giant recovery program by default.
4. **Measure a prospective learning curve under a fixed budget only after that closure.** Retained useful performance must improve with additional evaluated experience and survive restart/ablation and later learning. Stop on a valid null. This establishes whether extra experience has marginal developmental value.
5. **Then price the bottleneck in obtaining that experience.** Use fixed work and outcomes to compare load/scheduling, an already installed model and a justified context size. Preserve seeds, ordering, state and model identity. If faster work has no useful marginal gain, stop optimization.
6. **Only then cross the hardware gate.** If a reproducibly useful workload cannot meet the declared resource/latency bound locally, use a capped larger-memory/model comparison. Rent first for intermittent work; buy only if repeated useful demand and economics justify it.

The smallest recommended next mission is step 1, **not another ceiling audit, model-size benchmark, BA extension, or hardware purchase**. It should end with a retain/limit/retire decision for the existing mechanism. No such experiment was run here.

## 17. Explicit answers and claim limits

**Is the M5 holding FeralEcho back today?** Yes for model coexistence and some operational efficiency; **not demonstrated as the dominant blocker to the next useful acquired capability**. No specifically demonstrated developmental capability was found that this M5 cannot support while a stronger machine can.

**Is 24 GiB consequential?** Yes: actual admission evictions and swap traffic, not hypothetical model-size arithmetic. **Are thermals consequential?** Unresolved. **How much headroom?** CPU/deterministic work and disk have room; concurrent unified-memory workloads do not have abundant free capacity. Useful-developmental headroom is unquantified but sufficient to investigate the current bottleneck without a purchase.

**Can more compute currently become retained competence?** In narrow tasks there is a real extraction→persistent-repair→transfer mechanism. There is no established reliable marginal conversion from doubling ordinary inference to increased net competence tomorrow. The weak connection is validated acquisition and scope-correct reuse on meaningful new work, followed by cost-aware measurement.

**Which historical failures would change on a stronger computer?** Timeout completion and residency plausibly; some model errors with changed weights plausibly. None is guaranteed from the existing evidence. W/L leakage, same-process execution, mistaken labels, external authorship attribution and the exact harmful sign edit remain the same defects. More memory does not make those measurements valid.

**Should the Intel Air join the system?** Not for live distributed compute now. Possibly useful later as a frozen-package independent verifier/recovery target, after checking its actual capacity and without frontier-agent relays as life support.

**What is the cheapest path?** Demonstrate net retained utility with existing hardware, close only the demonstrated scope/credit gaps, then measure the marginal benefit and cost of additional experience. Extra inference quality, more artifacts and more model residents must each earn their own claim; none is automatically developmental progress.

**Are we nearing the M5 ceiling or our ability to turn resources into learning?** We already encounter its **memory-residency limit**, but the dominant developmental boundary is still our system's ability to turn available computation into correctly acquired, retained and appropriately used competence. Both facts can be true. CER-1 supports spending **$0 on additional developmental compute now**, with explicit reopening triggers rather than a permanent “never upgrade” position.

## 18. Integrity, limitations and files created

Production Echo, RiverBrain, memory, VSL, watchdog and LaunchAgents were not modified or signalled by CER-1. Live-owned files continued to evolve naturally; no claim of a frozen live filesystem is made. Echo/watchdog/Ollama server PIDs and start times remained unchanged in the targeted closing observation. Ollama runner processes changed during normal model loading, which is part of the observed workload, not an audit restart.

Passive resource observations were collected around 05:04–05:17 PDT, with another process observation at 05:25. Finalization resumed after an interruption; the **11:29 PDT** integrity/process check again confirmed the same protected PIDs/start times, unchanged protected hashes and empty staging. The intervening hours were **not** a continuous measurement or thermal test. Resource figures describe their stated observation windows, not guaranteed utilization at every later moment.

No stage, commit, push, download, purchase, configuration change, optimization, model inference or active benchmark occurred. The report and its supporting directory are additive and unstaged. Current source was inspected; no sandbox, matcher, evaluator or learned state was repaired.

Limitations: brief passive OS samples; a bounded historical log slice; no whole-system cost profile; short-output timing cohorts; no prospective larger-model comparison; no Intel OS measurement; no controlled thermals; no ownership/rental quotations; no full recovery qualification. Short CPU-idle intervals are not a throughput guarantee. File hashes record inspected identities, not external timestamp attestation. Historical outcome counts preserve their original sampling/provenance limitations.

Analysis bookkeeping is explicit: the first recount script stopped because BJQ's D summary lacks a start timestamp; D elapsed time is left null, and only the remaining read-only recount was completed. The log's `system_limited=true` marker includes both fit and eviction records; the corrected separate recount is **37 evictions / 20 fits**, not 57 evictions. Full process-table tool output was truncated, so a targeted process query was used for identity confirmation. These did not change source evidence or execute additional trials.

Created files: this report and `audits/cer1_20261001/` containing `baseline.json`, `opening_observations.json`, `second_observations.json`, `historical_timings.json`, `ollama_passive_excerpt.json`, `log_counts.json`, `storage.json`, `evidence_recount.json`, `measure_existing.py`, `closing_integrity.json`, and `artifact_manifest.json`. No pre-existing evidence file was modified.

**Primary disposition: CER1-LEARNING.**

**Spending decision: SPEND $0 — EXHAUST EXISTING HEADROOM.**
