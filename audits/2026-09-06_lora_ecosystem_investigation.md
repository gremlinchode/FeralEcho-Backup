# LoRA Ecosystem Investigation — Read-Only Architecture, Feasibility & Experimental Design

Read-only. No production code modified, no packages installed, no models downloaded, no training run,
no RiverBrain state changed. This investigation builds on six completed investigations from earlier in
this same session (Phase 0 reward-signal verification, Phase 1 functional-quality experiment, Phase 1A
adversarial verifier audit, the Findings-91-93 forensic re-validation, the architecture/liveness map, the
system-wide adversarial attack pass, and the Phase 1.5 capability-ceiling synthesis) — cited as
`[inherited]` where used directly, and independently verified where a new conclusion depends on it.

---

## 1. Executive Conclusion

**FeralEcho has zero existing LoRA/fine-tuning/adapter infrastructure** — confirmed by direct repo-wide
grep, not assumed (every apparent hit was a false positive: "exploration"/"exploratory" contains the
substring "lora"; the one real "fine-tune" mention describes `vicuna:latest`, an unrelated pre-existing
Ollama model, not FeralEcho's own capability). This would be entirely new engineering, not an extension
of something partially built.

**LoRA/QLoRA is technically feasible on this exact hardware**, using a dependency already installed and
live in this codebase (`mlx_lm`, already powering `mlx:qwen3`) — no new framework required. `echo:latest`,
the single most identity-central model in the whole system, is built `FROM llama3:instruct` — directly
confirmed from the real `Modelfile` — placing it squarely in the best-supported LoRA→GGUF→Ollama
conversion path (current authoritative sources confirm MLX's GGUF export is reliable specifically for
Llama/Mistral/Mixtral-family models, §5).

**The central finding, and the one this report's own governing question (§19) depends on**: this
session's own Phase 1.5 synthesis already proved, from direct source code, that FeralEcho's real
ground-truth learning signals — genuine sandbox execution outcomes, genuine explicit human ratings — are
computed, persisted, and then read by nothing that affects any decision (Phase 1.5 §4, independently
re-confirmed here by re-reading the same source). **Adding LoRA on top of this topology, without first
repairing it, would not fix that problem — it would create a seventh place for real signal to go in and
never come out.** This is not a hypothetical risk; it is the same shape of failure this session has
independently found and proven at least six times tonight, in six different subsystems.

---

## 2. Where LoRA Would Sit in FeralEcho's Causal Architecture

```
INPUT (a real interaction, a real self-edit attempt)
   ↓                                                    [EXISTS, LIVE]
EXPERIENCE (interaction_log.jsonl, self-edit reflection_shard.jsonl)
   ↓                                                    [EXISTS, LIVE]
MEMORY (FAISS retrieval)
   ↓                                                    [EXISTS, LIVE — but Finding 76 (inherited) found
                                                          no measurable behavioral effect distinguishable
                                                          from noise on the one path tested]
EVALUATION (AST-only quality score; functional_quality.py exists, adversarially validated, disconnected)
   ↓                                                    [EXISTS — REACHABLE — NOT STATE-CHANGING for the
                                                          real ground-truth half, per Phase 1.5 §4]
DATA CURATION (a labeled, deduplicated, contamination-filtered training corpus)
   ↓                                                    [DOES NOT EXIST AT ALL — confirmed, §4 below]
TRAINING (LoRA/QLoRA fine-tuning run)
   ↓                                                    [DOES NOT EXIST — no code, no scheduled job, no
                                                          triggering mechanism]
ADAPTER STATE CHANGE (a persisted, versioned adapter file)
   ↓                                                    [DOES NOT EXIST — no adapter lifecycle anywhere]
MODEL BEHAVIOR CHANGE (Ollama/MLX serving the adapted weights)
   ↓                                                    [DOES NOT EXIST — no mechanism to select base vs.
                                                          adapted model; MODEL_POOL has no such concept]
FUTURE EXPERIENCE → FUTURE EVALUATION
   ↓                                                    [Cannot close — nothing upstream of this exists]
```

**Precise classification, per the mission's required distinction**: the first three links
(experience/memory/some evaluation) **exist, are reachable, are active, and change state**. Starting at
"data curation," every subsequent link **does not exist in any form** — not disconnected, not dormant,
simply absent. LoRA would not be "wiring up a dead end" the way five other things in this system are
(§3) — it would be building a genuinely new five-stage pipeline from nothing.

---

## 3. Existing Learning Topology — A. RiverBrain

`[inherited: Phase 1.5 §4, independently re-confirmed by fresh source read this pass]`. Full topology
already resolved with precision: `.learn()` (AST-heuristic score) and `learn_from_council_rating()`
(peer ratings, gated on trust) are the only two of five real pathways that write `model_task_stats`, the
signal `rank_models()`/`_select_council()` actually consume. `learn_from_sandbox_outcome()` (real
execution ground truth) and `learn_from_rating()` (real explicit human 1-5 ratings, described in this
codebase's own comments as "high-trust") both train a classifier whose only real consumer feeds
`accuracy_trackers`, itself confirmed dead-ended (two readers, neither drives a decision). **This is the
single most load-bearing fact for this entire LoRA investigation** — it is direct proof that this
system's architecture, independent of any specific mechanism, has a demonstrated pattern of computing
real signal and discarding it before a decision point.

## 3B. Human Rating Learning

Directly re-confirmed (`echo_model_orchestrator.py:898-918`): `learn_from_rating()` receives real
1-5 ratings from `terminal_client.py`'s bare-digit prompt, applies a 3x-weighted label to the
classifier — and never touches `model_task_stats`. **A human explicitly telling the system "this
was bad" currently has zero verified effect on which model gets selected next time, for any task
type.** This is worse than "sparse data" — it's structurally inert regardless of volume.

## 3C. Sandbox Outcome Learning

Directly re-confirmed (`echo_model_orchestrator.py:870-896`): `learn_from_sandbox_outcome()` is called
from exactly two real sites in `self_edit_manager.py` (the primary attempt and the retry-on-failure
path) — genuinely reached by the live self-edit path, not dead code. It receives real `code`/`error`
from a real sandbox run. It writes `scalers`/`classifiers`/`sandbox_observation_counts` — confirmed by
grep, `sandbox_observation_counts` is read by exactly one consumer, a log line
(`echo_model_orchestrator.py:1092`), never a decision. **Real, live, reached, state-changing — and
behaviorally inert**, the precise "active learning with no verified behavioral feedback" case the
mission's own example describes.

## 3D. Memory / Interaction Data — Source Classification

| Source | Trustworthy? | Contamination risk | Suitable for training as-is? |
|---|---|---|---|
| Raw `interaction_log.jsonl` | Mixed | High — self-referential quality scoring, historical cross-training contamination (`[inherited: CLAUDE.md Finding 3]`, already remediated once, no guarantee against recurrence) | **No** |
| Self-edit candidates (unfiltered) | Low | Very high — `[inherited: this session's own Phase 0/1 work]` 64% of the real 25-file retained-deploy corpus is functionally broken despite scoring at the AST ceiling | **No** |
| Sandbox execution outcomes (pass/fail) | **High** — this is genuine, mechanically-verified ground truth | Low, for the pass/fail label itself | **Yes, as a label** — but see §3E, the underlying code samples still need filtering |
| Explicit human ratings | **High** | Low (real human judgment) but **sparse** — `[inherited: this session's Council Peer Rating section, CLAUDE.md]` real volume never independently re-measured this pass | Yes, but low volume |
| Peer/council ratings | Medium-high — real, trust-gated (`is_council_trusted()`) | Low | Yes |
| Successful self-edit code (AST-scored only) | **Low** — directly disproven by tonight's own functional-verifier work | High | **No, not without functional re-verification first** |
| Failed self-edit code | High as a *negative* example, if paired with its real error | N/A (used as a negative signal, not imitated) | Only as part of a failure→correction pair (§11) |
| Autonomous/self-talk interactions | Low-medium | `[inherited: Findings 11/35]` — documented historical self-quoting/retrieval-loop contamination in this exact category, multiple distinct instances found and fixed over this project's history | No, without the same exclusion filters those fixes already established |

---

## 4. Does FeralEcho Currently Have a Trustworthy Training Corpus?

**No — DISPROVEN, not merely unconfirmed.** `interaction_log.jsonl` is a real, growing log, but §3D
establishes every one of its component sources carries a real, independently-documented contamination
risk this project has already had to fix at least twice (Finding 3, Findings 11/35). None of those fixes
were designed with "will this data later train model weights" in mind — they were designed to protect
RiverBrain's classifier-level online learning, a much lower-stakes target than a LoRA adapter that
durably changes model behavior.

**Hypothetical pipeline, none of which currently exists:**

```
RAW EXPERIENCE (interaction_log.jsonl + self-edit reflection_shard.jsonl)
   ↓
FILTER (exclude autonomous self-talk per existing memory_source tagging conventions;
        exclude any entry already known-contaminated per Findings 3/11/35's own exclusion logic)
   ↓
DEDUPLICATE (exact + near-duplicate, given this project's own documented history of both — Finding 51's
             `52 near-duplicate "This Day History" entries`, Finding 75's 15% reflection near-duplicate rate)
   ↓
VALIDATE (re-run functional_quality.py — once its two known defects are fixed, §5/§14 of Phase 1.5,
          inherited — against every code sample; discard anything that doesn't pass)
   ↓
LABEL (real sandbox pass/fail + real human/peer rating where available; never the AST score alone)
   ↓
QUALITY CONTROL (a frozen, human-reviewed sample check — this project's own `spot_check.py` precedent
                 already exists for a different purpose and could plausibly be adapted, not reused as-is)
   ↓
TRAIN/VALIDATION SPLIT (temporal split, not random — a random split on time-series interaction data
                        risks near-duplicate leakage across the split, given the documented duplication rate)
   ↓
TRAINING CORPUS → LoRA
```

**Every stage above is a real design proposal, not existing code.** This is the single largest piece of
net-new engineering LoRA would require — larger, by volume of new code needed, than the training step
itself.

---

## 5. LoRA / QLoRA Feasibility on This Hardware

**Hardware**: Apple M5, 10 cores, 24GB total unified RAM `[confirmed earlier this session via
sysctl hw.memsize]`.

**Framework**: `mlx-lm`'s `mlx_lm.lora` module — **already installed and live in this codebase**
(`app/mlx_handler.py` imports `mlx_lm` directly for `mlx:qwen3`). Supports LoRA, DoRA, and full
fine-tuning; **QLoRA is automatic** when the target model is already quantized — no separate
implementation needed (Source: ml-explore/mlx-lm's own `LORA.md`, and corroborating current guides,
via WebSearch this session).

**Memory**: a 4-bit-quantized 7B model's LoRA fine-tune fits comfortably in ~7-8GB of working memory
(current sourced figures: "brings a 7B fine-tune comfortably into 8GB of working memory"; a real
Mistral-7B/5,000-example run measured ~7GB peak on a 32GB M2 Max). **This machine's 24GB total is
sufficient in isolation** — but FeralEcho's own live process already runs under real, documented memory
pressure (`[inherited: this session's own live checks tonight, 75-89% RAM pressure at various points]`).
**Training would need to run either with the live server paused, or on a smaller/more aggressively
quantized model** — not a blocker, but a real scheduling constraint worth stating precisely rather than
glossing over.

**Time**: ~90 minutes for a 5,000-example Mistral-7B run on a slower/lower-RAM machine (M2 Max, 32GB) —
a reasonable, if rough, ceiling estimate for this machine given comparable or better specs.

**Model family compatibility — the most consequential feasibility constraint found this pass**: current
sourced documentation states MLX's GGUF export (needed to make a fused, LoRA-adapted model consumable by
Ollama) is **reliable specifically for Mistral/Mixtral/Llama-family models**; Qwen/Gemma-family
conversion compatibility is explicitly described as uncertain in current community documentation
("it remains unclear whether the adapter_config.json generated by MLX is compatible with what llama.cpp
expects" for non-Llama families). **Directly consequential for FeralEcho**: `echo:latest` — confirmed
via direct `Modelfile` read, `FROM llama3:instruct` — sits squarely in the well-supported path.
`mistral:latest`, `llama3.2:3b`, `llama3.1:8b` are also real, already-pulled pool members in the same
family. `qwen2.5-coder:7b` (arguably the model most relevant to coding/self-edit capability specifically)
and `gemma3:4b` sit in the *less*-certain conversion path — a real, evidence-based reason to target
`echo:latest` specifically for any first experiment, not a generic "pick the biggest model" choice.

**Adapter lifecycle capability**: `mlx_lm.fuse` (bakes an adapter into a standalone model directory)
and Ollama's own `Modelfile`-based import (which handles GGUF conversion internally on `ollama create`)
together provide a real, minimal mechanical path from "trained adapter" to "a new, separately-named
Ollama model" — meaning multiple adapters *could* coexist as distinct named models in `MODEL_POOL`,
version-controlled the same way any two Ollama models already are (by tag name). **This is a real,
positive finding**: FeralEcho's existing `MODEL_POOL`/`rank_models()` architecture (§3A) would not need
fundamental redesign to *route between* a base and an adapted model once both exist as named Ollama
entries — the routing mechanism already exists and already works for competing models. What's missing
is everything upstream of "the adapter file exists" (§4) and the specific *policy* for when to prefer
one over the other (§12).

Sources: [Fine-Tuning LLMs Locally Using MLX LM - DZone](https://dzone.com/articles/fine-tuning-llms-locally-using-mlx-lm-guide) ·
[LoRA Fine-Tuning On Your Apple Silicon MacBook - Towards Data Science](https://towardsdatascience.com/lora-fine-tuning-on-your-apple-silicon-macbook-432c7dab614a/) ·
[mlx-lm LORA.md, ml-explore/mlx-lm](https://github.com/ml-explore/mlx-lm/blob/main/mlx_lm/LORA.md) ·
[Converting LoRA adapters.safetensors to GGUF, ml-explore/mlx Discussion #1507](https://github.com/ml-explore/mlx/discussions/1507) ·
[From LoRA Adapter to One File — Ollama/LM Studio packaging, 2026](https://www.jocheojeda.com/2026/08/22/one-file-model-ollama-lmstudio/) ·
[Does llama.cpp Support LoRA Adapters in GGUF, ggml-org/llama.cpp Discussion #7785](https://github.com/ggml-org/llama.cpp/discussions/7785)

---

## 6. External Memory vs. Behavioral Adaptation vs. Parameter Adaptation

Three genuinely distinct mechanisms already coexist in FeralEcho, and this report is careful not to
conflate them:

- **External memory** (FAISS retrieval): real, live — `[inherited: Finding 76]` measured effect not
  distinguishable from noise on the one path tested.
- **Behavioral adaptation** (RiverBrain-driven model selection, self-edit targeting): real, live, proven
  closed-loop for model selection specifically (§3A) — but driven by a proxy signal, not ground truth.
- **Parameter adaptation** (what LoRA would add): **does not exist in any form today.**

**How to experimentally distinguish them, concretely**: freeze the orchestration layer (fixed model
selection, fixed retrieval-on/off flag, fixed temperature) and vary only whether the served model has an
adapter applied. Any behavioral difference under that frozen configuration cannot be explained by
retrieval, model selection, or prompting — only by the weights themselves. §7 designs this precisely.

---

## 7. The Scientific Experiment (Design Only — Not Run)

**Condition A** — untouched base model (e.g. `llama3:instruct`, no FeralEcho orchestration at all).
**Condition B** — base model + real FeralEcho orchestration/memory, no adapter.
**Condition C** — base model + LoRA adapter (trained on curated FeralEcho experience), no orchestration.
**Condition D** — base model + adapter + full orchestration.

- A vs. B isolates the *system's* contribution independent of any weight change — this is close to what
  `[inherited: Finding 87]`'s capability-ceiling research already partially measured for the self-edit
  pipeline specifically (and found could be a net *negative*, not just neutral).
- A vs. C isolates the *adapter's* contribution independent of the surrounding system — the cleanest
  test of "did the weights actually learn something," and the one this investigation's own §19 needs.
- C vs. D isolates whether system and adapter effects compose, cancel, or interact.
- B vs. D is the one most people would intuitively want to show for a demo — and is explicitly the
  *weakest* comparison for causal interpretation, since two things changed at once. **A defensible
  showcase demonstration should lead with A vs. C, not B vs. D.**

---

## 8. Preventing Evaluation Contamination

**Training corpus**: only data passing §4's full pipeline (deduplicated, functionally re-verified,
temporally split before the freeze date).
**Validation corpus**: a small held-out slice from the *same* time window, used only for hyperparameter
choices (LoRA rank, learning rate, epoch count) — never touched for the final reported number.
**Held-out test corpus**: tasks with zero temporal or textual overlap with anything in training —
`[inherited]` this session's own Tier-4 capability-ceiling task suite is a real, already-frozen,
independently-verified candidate for this role, since it predates this LoRA investigation entirely and
was built for an unrelated purpose (lower risk of unconscious construction bias toward LoRA-favorable
tasks).
**Adversarial test corpus**: constructed *after* training completes, specifically targeting the failure
modes this session's own adversarial passes already catalogued (Phase 1A's no-op/exception-swallowing
gaming, the Phase 6 pass's hallucinated-self-knowledge and prompt-injection categories) — reusing the
project's own already-proven attack shapes rather than inventing new ones from scratch.

---

## 9. Generalization Testing

For coding specifically, per the mission's own required distinction, and explicitly **not** reusing the
AST-only metric as a correctness measure (`[inherited: Findings 91-93 forensic pass]`'s own r=0.206,
not-significant correlation between AST complexity and real functional correctness is direct evidence
against doing so): syntax validity (cheap, necessary, not sufficient) → execution success (via the
*fixed* version of `functional_quality.py`, not its current two-defect state) → expected output (where
a real test contract exists — Tier-4's own task suite already has this) → held-out task performance
(never seen in training) → paraphrased-task performance (same underlying problem, different wording —
tests whether the adapter learned the *pattern* or memorized the *text*) → regression on unrelated
capabilities (a real risk given this project's own repeated finding that narrow interventions can have
unexpected system-wide effects, e.g. Finding 39's preferential-attachment discovery) → catastrophic
forgetting (compare pre/post adapter performance on tasks explicitly *outside* the training
distribution's category set).

---

## 10. What Should Actually Be Trained — Comparison

| Target | Assessment |
|---|---|
| A. Raw conversations | Confirmed noisy (§3D) — not recommended without heavy filtering |
| B. Human-corrected conversations | No mechanism currently captures "human corrected this" as a distinct, labeled event — would need new instrumentation |
| C. Human-rated examples | Real signal, but §3B proves it's currently disconnected from *everything*, including any potential export path — the raw ratings exist in the log, just never extracted for this purpose |
| D. Successful self-edit examples (independently verified) | Only viable **after** §14/Phase 1.5's `functional_quality.py` fixes ship — using the current AST-only "success" would train toward exactly the failure mode this whole investigation exists to avoid |
| E. Failed → corrected self-edit pairs | **The most concretely promising target found this pass — see §11** |
| F. Problem → reasoning → verified solution | Plausible, but this project has no existing "reasoning trace" capture distinct from the final answer — would need new instrumentation, same gap as B |
| G. Preference pairs | Real infrastructure exists for *conversational* preference (peer/council ratings) but is architecturally distinct from supervised fine-tuning — would need a genuinely separate training objective (DPO-style), not LoRA-SFT reusing the same pipeline |
| H. "Echo's personality" | **Explicitly not recommended as a training target** — this project's own Modelfile-based `SYSTEM` prompt already encodes persona cheaply and reversibly; spending LoRA's actual capacity on style rather than capability would be a clear instance of the mission's own "training theater" category (§16) |

## 11. Learning From Failure — The Most Interesting Finding This Pass

**A failed→corrected pipeline already exists, as a byproduct of normal self-edit operation, and is
currently discarded.** Direct re-confirmation, `self_edit_manager.py`'s `execute_self_edit()` (read in
full earlier this session by the parent, re-verified here): on a sandbox failure, the function builds a
`retry_prompt` containing the *original code's real error text* and asks for a corrected version; if the
retry succeeds, `reflection_entry["sandbox_feedback"] = "success_on_retry"` and both the original failing
attempt and the corrected, verified-passing result are already present in the same log entry's
lifecycle. **This is a real, already-occurring (original, error, corrected) triple, generated by the
system's own existing retry logic — not a new mechanism to build, an existing one to start capturing.**

This is more valuable than raw successful examples for the same reason this entire session's evidence
argues: it pairs a genuine failure with a genuine, sandbox-verified fix, which is closer to what a
useful adapter would need to learn (how to recognize and repair a specific class of mistake) than an
undifferentiated pile of "things that worked." **Not assumed to be true — flagged as PLAUSIBLE, not
PROVEN**, since no experiment in this codebase's history has actually measured whether training on
failure-correction pairs outperforms training on successes alone; this is a real, motivated hypothesis
from real existing data, not a settled finding.

---

## 12. Adapter Lifecycle (Hypothetical Design)

```
BASE MODEL (echo:latest / llama3:instruct)
  ↓
EXPERIENCE ACCUMULATION (existing logs, once §4's curation pipeline exists)
  ↓
CORPUS FREEZE (a versioned, hashed snapshot — this project already has a real precedent for this exact
               pattern, echo_principles.json's genesis-hash mechanism, reusable in spirit)
  ↓
DATA VALIDATION (§8's held-out/adversarial split, established before training, not after)
  ↓
LoRA TRAINING (mlx_lm.lora, real, local, already-installed)
  ↓
ADAPTER EVALUATION (§9's generalization suite against the frozen held-out set)
  ↓
ADVERSARIAL TESTING (§8's adversarial corpus, reusing this session's own proven attack shapes)
  ↓
PROMOTION / REJECTION (a real, human-reviewed gate — NOT an automatic promotion, per the mission's own
                        explicit "an adapter must never silently replace the baseline model")
  ↓
DEPLOYMENT (mlx_lm.fuse → Ollama import as a distinctly-named model, e.g. echo-lora-v1 — coexists with
            echo:latest in MODEL_POOL rather than replacing it, using the existing routing mechanism §5
            already confirmed doesn't need fundamental redesign)
  ↓
MONITORING (a real, natural fit for this project's own Liveness Ledger pattern — a new check verifying
            the adapter model is still being selected at a sane rate and its RiverBrain score hasn't
            collapsed)
  ↓
ROLLBACK (trivial at the routing layer — remove the adapter's entry from MODEL_POOL/rank_models'
          eligible set; the base model was never modified, so there's no "restore" step needed the way
          a self-edit deploy rollback requires)
```

**Required new infrastructure, named precisely**: a corpus-freeze/versioning mechanism (none exists),
an adapter metadata/provenance record (none exists — this project's own snapshot system is the closest
precedent but tracks a different kind of artifact), a promotion gate (closest precedent:
`propose_core_edit()`'s human-review-only pattern, `[inherited: CLAUDE.md's Dissent Log/Finding 9]` —
directly reusable in spirit, not code), and a new Liveness Ledger check category this project has never
had before (adapter-health monitoring, as opposed to code-health monitoring).

---

## 13. Could LoRA Become "Self-Improvement"?

Precise level-by-level assessment, per the mission's own required distinction:

- **Level 0** (human manually trains): **achievable now**, with the engineering from §4/§5/§12 built.
- **Level 1** (FeralEcho auto-constructs training data): achievable *after* §4's curation pipeline is
  real — currently does not exist.
- **Level 2** (FeralEcho auto-launches training): mechanically simple once Level 1 exists (a scheduled
  job, matching this project's existing autonomous-loop pattern) — but **not recommended before Level 3
  exists**, since an unevaluated adapter auto-promoted would be a real, novel risk category this project
  has not faced before (its self-edit pipeline, for comparison, never touches model *weights*, only its
  own generated code).
- **Level 3** (FeralEcho auto-evaluates): requires §9's generalization suite to be real, automated
  infrastructure, not a one-off manual test — does not exist.
- **Level 4** (FeralEcho decides promotion): **should not be built at all in the near term** — this is
  the closest analogue to the exact WOLF failure this project's own history already lived through
  (`[inherited: CLAUDE.md's "A Standing Principle" section]` — a mechanism that appears to evaluate and
  auto-approves, discovered hollow after auto-approving a keylogger's raw keystrokes into a protected
  file). A LoRA adapter silently promoted by the system that trained it is a strictly higher-stakes
  version of the same failure shape, since it changes model *weights*, not one generated file.
- **Level 5/6** (continuous accumulation, regression detection, auto-rollback): not realistically
  reachable without Levels 1-4 first being real, tested, and trusted over a real track record — this
  project's own Liveness Ledger took 20+ checks and months of iteration to earn the trust it has;
  adapter-level automation should expect a comparable, not shorter, trust-building period.

**Do not call any of this "autonomous self-improvement" until at minimum Level 3 is real** — even
Level 2 alone (auto-training without auto-evaluation) would be indistinguishable, from the outside, from
"the system quietly does something to itself periodically," which is not evidence of improvement, only
of activity.

---

## 14. Threat Model

- **Poisoned training examples**: real risk, `[inherited]` §3D's contamination sources are the direct
  vector — mitigated only by the curation pipeline in §4, which does not yet exist.
- **Secret leakage into weights — directly connects to today's confirmed sandbox finding.**
  `GREMLIN_SECRET` is confirmed readable by sandboxed candidate processes (a real, already-verified
  vulnerability found and independently confirmed earlier this same session, not re-derived here). **If
  any future training corpus is ever built from sandbox execution logs or captured stdout/stderr
  (§10's "successful self-edit examples" target specifically), a secret that leaked into a candidate's
  own output during that window could be captured in the raw log and subsequently enter a training
  corpus** — a realistic, non-hypothetical path from today's confirmed environment-exposure bug to a
  much harder-to-remediate future problem (a secret baked into model weights cannot be rotated the way a
  leaked value in a log file can be deleted). **This is the single strongest argument in this entire
  report for fixing the environment-variable exposure before any LoRA-adjacent data pipeline work
  begins** — not because LoRA makes the vulnerability worse, but because it upgrades the *cost* of the
  same vulnerability from "delete a log line and rotate a secret" to "an adapter may need to be
  retrained or discarded entirely."
- **Reward hacking / evaluator contamination**: directly connects to Phase 1A's already-proven finding
  (`[inherited]`) that `verified_success` is gameable by no-op/exception-swallowing candidates — training
  on unfiltered `verified_success`-labeled examples would risk *teaching* the model to produce exactly
  that gaming pattern, since it would appear in the corpus as a labeled "success."
- **Training on hallucinated self-reports**: directly connects to this session's own fresh adversarial
  finding (`[inherited: Phase 6 attack pass]`) — a live-tested confabulation about a fabricated
  "Tier-3 Consensus Verification Layer." Any corpus built from Echo's own self-descriptive text without
  filtering risks training the adapter to confabulate more fluently, not less.
- **Catastrophic forgetting / model collapse**: standard risk, addressed by §9's regression testing —
  no evidence either way yet, correctly UNRESOLVED.
- **Backdoors / malicious training-data instructions**: low probability given this project's current
  scale and closed data sources, but not zero — worth a line-item in any future corpus's validation
  step, not a blocking concern today.

---

## 15. Cost and Locality

Training itself: **fully local**, using an already-installed dependency, zero new packages, zero cloud
compute. `[inherited: architecture liveness map]`'s existing finding — `claude_research.py` is the one
real, small, already-budgeted paid dependency in the current ecosystem — is unaffected either way by
this investigation; LoRA training itself introduces no new monetary cost. **The one real, non-monetary
cost this investigation adds**: real wall-clock time and real memory contention with the live production
server (§5), which is an engineering-scheduling cost, not a financial one, and should be named as such
rather than glossed into "no cost."

---

## 16. Red-Team List — Fake LoRA Success Criteria to Explicitly Avoid

Derived from this session's own already-demonstrated failure patterns, not a generic checklist:

- Training on benchmark questions and re-testing the same questions — the exact class of leakage §8's
  frozen held-out split exists to prevent.
- Measuring only stylistic similarity to Echo's existing voice — the Modelfile already does this
  cheaply; an adapter "succeeding" at this alone would be indistinguishable from doing nothing.
- Training on self-edit examples selected because they already scored well on the **current, disproven**
  AST-only metric — this would directly reproduce Findings 91-93's own already-proven r=0.206
  non-significant-correlation problem, one layer deeper.
- Using `echo:latest` as both the model generating training candidates *and* the model being fine-tuned
  on them, with no independent evaluator — a direct instance of the "circular validation" pattern this
  project's own CLAUDE.md history has repeatedly found and named (Finding 3's cross-training
  contamination is the closest precedent).
- Measuring only loss or perplexity and reporting that as "learning" — neither has any established
  relationship to the functional-correctness or generalization questions §9 actually cares about.
- Claiming "self-improvement" at any automation level before Level 3 (§13) is real.
- Auto-promoting an adapter with no held-out or adversarial evaluation — the direct LoRA-era analogue of
  Finding 19's own already-fixed self-edit bug (deploying any candidate that merely *passed*, without
  checking it was actually *better*).

---

## 17. The Single Highest-Value LoRA Experiment

**Not a production pipeline. A small, decisive, honestly-reported proof of concept**, matching the
mission's own preference for small/local/reversible/strongly-controlled:

1. Hand-curate (not auto-curate — §4's pipeline doesn't exist yet, and building it fully is out of scope
   for a first experiment) a small set (order of 50-200) of real §11-style failure→correction pairs,
   independently re-verified by the *fixed* version of `functional_quality.py`, not the current one.
2. Train a single LoRA adapter on `echo:latest`/`llama3:instruct` using `mlx_lm.lora`, QLoRA-mode on the
   already-quantized base.
3. Evaluate strictly via Condition A vs. Condition C (§7) — base model vs. adapter, orchestration held
   completely out of the comparison — against Tier-4's own already-frozen, already-independent task
   suite (`[inherited]`, never touched by this LoRA investigation, lowest-risk held-out set available
   in this codebase today).
4. Report the result honestly regardless of direction — a clean null is exactly as valuable to this
   investigation's own governing question (§19) as a clean positive, per this whole session's standing
   discipline.

This deliberately does **not** attempt Level 1+ automation (§13), does **not** touch the live
`MODEL_POOL`/routing layer, and does **not** require §4's full corpus-curation pipeline — it substitutes
a small, honest, hand-built dataset specifically to get a real answer to "can this architecture turn
verified experience into durable parameter-level change at all" without first building months of
infrastructure whose value depends on that question's answer.

---

## 18. LoRA vs. Alternative Learning Mechanisms

| Mechanism | Capability gain | Engineering complexity | Compute cost | Scientific value | Risk | Reversibility | Time to evidence |
|---|---|---|---|---|---|---|---|
| **Fix RiverBrain reward topology** (`[inherited: Phase 1.5 §17 Tier 1]`) | High — directly closes an already-proven gap | Low-medium (already scoped) | Near-zero | High — directly tests this session's own central finding | Low | High | Fast (days) |
| Improved retrieval | Unknown — Finding 76's own null result suggests this may not be the bottleneck | Low-medium | Near-zero | Medium | Low | High | Fast |
| Better preference learning (DPO-style) | Plausible, unmeasured | Medium — needs new objective, not just new data | Low | Medium | Low-medium | High | Medium |
| Improved self-edit verification (§5/§14 of Phase 1.5, already scoped) | High — directly the identified bottleneck | Low (two specific, already-designed fixes) | Near-zero | High | Low | High | Fast |
| **LoRA (minimum experiment, §17)** | Unknown until measured — that's the point | Medium-high (new pipeline, even for the minimal version) | Low-medium (real but bounded) | **High specifically because it's currently unknown** | Medium (§14) | Medium (an adapter is a new artifact, not free to discard, but doesn't touch the base model) | **Slow** (days-weeks for a defensible result) |
| LoRA (full production pipeline) | Unknown | Very high | Medium | High if reached, but gated on everything above | High (§13, §14) | Medium | Very slow (well beyond 27 days) |
| Model routing improvements | Low-medium — largely already exists and works (§3A) | Low | Near-zero | Low | Low | High | Fast |

**Ranking, by evidence-per-effort**: fixing the reward topology and self-edit verification (already
scoped in Phase 1.5, not new work) rank highest — cheap, fast, directly tested, and a genuine
prerequisite for LoRA to mean anything anyway. The minimal LoRA experiment (§17) ranks next — genuinely
higher scientific value than anything else on this list specifically *because* the answer is currently
unknown, but slower and costlier than the topology fixes. A full LoRA production pipeline ranks lowest
for the 27-day window specifically — not because it's a bad idea, but because its value is entirely
gated on questions this report cannot yet answer.

---

## 19. The Critical Question — Answered Directly

> Does adding LoRA address the actual capability bottleneck, or would it merely create another
> disconnected learning subsystem?

**As currently architected, and without the Phase 1.5-identified topology fixes landing first: it would
create another disconnected learning subsystem.** This is not speculation — it is the same, now
six-times-independently-proven pattern this session has found across RiverBrain's `accuracy_trackers`,
`learn_from_sandbox_outcome()`, `learn_from_rating()`, `functional_quality.py`, the self-edit fitness
gate, and (per Finding 76) even memory retrieval's own measured effect. A system with a demonstrated,
structural habit of computing real signal and routing it nowhere would need a specific, deliberate reason
to expect a seventh new pipeline to behave differently — and no such reason was found in this
investigation. **Conversely**: LoRA genuinely *is* the one mechanism on this list capable of producing
durable, parameter-level change rather than another orchestration-layer proxy — which is exactly why the
minimal experiment (§17) has real, high scientific value, *conditional on* being fed a corpus built from
already-verified (not AST-only) ground truth. Building that corpus well is itself most of the value;
the LoRA training step, mechanically, is the easy part (§5).

---

## 20-22. Deliverables, Evidence Standard, Operational Constraints

Addressed throughout — every major claim above is tagged `[inherited]` (verified earlier this session,
cited rather than re-derived) or independently re-confirmed in this pass (direct source reads: RiverBrain
pathways, the Modelfile's base model, the repo-wide LoRA/adapter grep). External claims (§5's memory/time
figures, GGUF family-compatibility limits) are sourced to real, current documentation via WebSearch this
session, linked inline. No claim in this report rests on trusting a prior audit's conclusion without a
verification step that mattered to a *new* conclusion this report reaches.

**Working-tree check, per the mission's own requirement**: `git status` at the start of this
investigation showed the same set of untracked audit files and modified sandbox files already present
from this session's earlier work (`sandbox/safe_exec_wrapper.py`, `sandbox/scripts/temp_self_edit.py`
modified; `app/core/functional_quality.py` and six prior audit reports untracked). The only new file
this investigation adds is this report itself. No other file was touched.

---

## FINAL REQUIRED JUDGMENT

**1. What LoRA would add to FeralEcho**: the one thing currently missing from every other learning
mechanism in this system — a real path from verified experience to durable, parameter-level behavioral
change. Everything else in this system (RiverBrain, self-edit's targeting, memory retrieval) operates at
the orchestration layer, never touching model weights.

**2. What LoRA would NOT solve**: the actual, already-identified bottleneck (Phase 1.5 §4/§12,
inherited) — a reward-signal topology that discards real ground truth before it reaches any decision.
LoRA is a new *destination* for signal; it does nothing about the fact that signal currently never
leaves the pipe. It also would not solve memory's unproven behavioral effect (Finding 76), and would not
by itself provide the corpus-curation, evaluation, or adapter-lifecycle infrastructure this report found
entirely absent (§4, §12).

**3. Does FeralEcho currently have the infrastructure for trustworthy LoRA training?** **No — DISPROVEN.**
Zero existing LoRA code, no curated corpus, no functional (non-AST) evaluator wired to anything, no
adapter lifecycle, and one directly-relevant, already-confirmed security gap (§14) that specifically
raises the stakes of building a training pipeline before it's fixed.

**4. Should LoRA be pursued during the remaining 27-day showcase window?** **Not as a production
pipeline — NO-GO on that specifically; too much genuinely new infrastructure, most of it higher-value
built for other purposes first (§18).** **CONDITIONAL GO on the single minimal experiment in §17**,
specifically because it is small, local, honestly falsifiable, and directly answers this report's own
central question with real evidence rather than architectural argument alone — matching this whole
27-day mission's own stated preference for a small number of decisive demonstrations over broad,
shallow feature work. The condition: it should run *after*, not instead of, the already-scoped
reward-topology fixes (Phase 1.5 §17 Tier 1), since those are faster, cheaper, and a genuine prerequisite
for the experiment's own corpus to be trustworthy.

**5. The single highest-leverage next experiment**: not LoRA training itself — **first, fix the two
already-designed `functional_quality.py` defects and the sandbox environment-variable exposure (both
already in front of the parent session for review as this investigation runs)**. Those two changes are
cheap, fast, and are the actual prerequisite for *any* future training corpus — LoRA or otherwise — to
be built on ground truth instead of a proxy that has now been proven, six separate times tonight, not to
reach the decisions it should.
