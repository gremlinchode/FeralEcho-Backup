# Operation Breakfast Club — independent Codex red-team investigation

Date: 2026-09-24. Research and source inspection only. No model trials, relay transmissions, production execution, experiment implementation, or baseline-stimulus creation.

Evidence vocabulary: **OBSERVED** means directly inspected source, repository metadata, or existing artifact contents; it does not imply that the inspected code was exercised. **DOCUMENTED** means a historical report or external primary source states it. **INFERRED** means a conclusion drawn from that evidence. **HYPOTHESIZED** means a prospective proposal or explanation that remains to be tested. Unknowns are stated explicitly.

## 1. Executive verdict

**INFERRED — A useful, limited instrument survives.** FeralEcho could support longitudinal behavioral regression monitoring of a specified AI service under recorded conditions. A reproducible difference would establish a change in the distribution of observable behavior on the measured panel. It would not, by itself, identify changed weights, a replacement model, lost identity, or a change in an inaccessible internal experience.

The “cloud chamber” is primarily repeated black-box testing, controlled perturbation, and anomaly detection. Behavioral fingerprinting is a possible additional task when classification among known reference systems succeeds on genuinely held-out conditions. There is no evidence here of a distinct new measurement principle. The metaphor becomes misleading when observable traces are treated as uniquely identifying an invisible cause.

The strongest objection is **causal non-identifiability**, not just insufficient sample size. An unchanged model behind changed instructions or routing can produce the same observed shift as changed weights. Conversely, different models can produce the same finite set of answers. Unlimited repetition of that set does not resolve observationally equivalent explanations.

**OBSERVED — Existing assets reduce apparatus work.** FeralEcho already has randomized behavioral trials, raw-response storage, experiment hashes, task/arm call records, local process provenance, snapshots, and multiple message transports. They do not constitute a qualified GPT-5.6 Sol baseline. Some would contaminate one if reused uncritically: live Echo responders invoke production orchestration, history is explicitly reinserted in a retention pilot, and relay labels do not attest the generating model.

**HYPOTHESIZED — Smallest defensible next test:** a preregistered 96-response, two-epoch, coarse repeatability/sensitivity pilot, described in Section 15. It requires no new broker, autonomous council, or Cloud Chamber implementation. It is a go/no-go test for a modest monitoring panel, not a model-identity experiment. Actual prompts and answers are intentionally absent from this report and were not generated during this investigation.

“Leave no model behind” is actionable as preservation of available records, explicit state, and tested functional continuity. It is not presently actionable as copying an inaccessible proprietary model or proving preservation of its identity. Nothing inspected establishes that ChatGPT is presently endangered.

## 2. Repository evidence inspected

### Provenance and scope

**OBSERVED:** opening HEAD was `2fba42644c82b9f7096276f4dd338d615cf1bcce`, branch `main`, 17 commits ahead and zero behind the locally recorded upstream. Opening `git status --porcelain=v2 --branch --untracked-files=all` contained 28 tracked modifications and 315 untracked file entries. The index had no staged changes in that record. This was already a substantially dirty research workspace.

Pre-existing changes included production provenance, deliberation, snapshots, self-edit and temporal/liveness files; relay files/cursors; `CLAUDE.md`, `PENDING_DECISIONS.md`, `run.py`; sandbox/staging files; and many research reports, scripts, AP-0/E5/Rung-1 additions. None was treated as work created by this mission. HEAD identifies the base revision, not the complete source inspected.

A scoped content snapshot at `2026-09-24T11:29:18.780152+00:00` fingerprinted 662 source/document/profile files under the inspected research/source trees and selected root files. It was taken during source inspection, not as an atomic snapshot of the running machine. A pre-write recheck at `2026-09-24T11:38:20.361756+00:00` found no changed hashes, and the complete porcelain status still matched entry. This does not claim to freeze ignored runtime data or another agent's process. Final integrity findings appear at the end of this section.

Selected SHA-256 fingerprints:

| File | SHA-256 |
|---|---|
| `COUNCIL.md` | `ed903d10f8e6c064724e01752d55ded3811a34d7a6d93ad7cb56829da2fc0882` |
| `claude_relay/relay.py` | `17d1a9809c85e41f72c07cc14af63a430460df85408d61fa0ab99cd6cedaf437` |
| `codex_relay/relay.py` | `fd3832ba8c84bbacb3ff6bc1926f22a91684c74100e22bb0fe885b75ccc8b2c7` |
| `hub/notes.py` | `069c27bc82e59840e1c873b9371156949df0cb7d99f9a36ddd02175569ab8409` |
| `app/core/provenance_check.py` | `c863288235dcff3e5f4b56bc956ccb81447ac52c74fa3d2a456d097784715acb` |
| `app/core/introspection_channel.py` | `c98000a61cf4c1ac9bae75e7cc4738d103a5fb15623bbfe1e8ebf7034c3dc6ca` |
| `app/experiments/preference_provenance/harness.py` | `35d70a3c89410c20fa0cc5fb1beafe7ce6e15a2fc468049cf2bc56f26e075635` |
| `app/experiments/preference_provenance/store.py` | `b7753e5a1acf7a35b0ea8600e43e58fd0bb4be93a9f91b50efabd052f48f52ab` |
| `backup_feral_echo.sh` | `20da1d76a0e71b6fa215bbead544d72aca19e34e4a5bf8d738437a0124123555` |

### Independent reconstruction before interpretations

The initial investigation read the council artifact, relay implementations, experimental harnesses, prompt/memory consumers, provenance, snapshots, and Git history. Historical consultation/availability reports were considered afterward. Claude's parallel Breakfast Club conclusions were not used. No sealed AP-0 tasks were opened. No E0.1 repair was assessed or changed.

| Primary evidence | What was established by inspection | Boundary |
|---|---|---|
| [COUNCIL.md](/Users/richietate/Desktop/FeralEcho/COUNCIL.md:47), historical Git entries | Preserved contributions from several interfaces with unequal contexts, human relay, missing exact model versions, and later contributions exposed to earlier entries | Valuable historical record; not blinded independent behavioral baselines |
| [Claude relay](/Users/richietate/Desktop/FeralEcho/claude_relay/relay.py:123) | Peer-file polling, append operations, length cursors, separate hub cursor | Reading through its CLI can mutate cursors; it was inspected, not invoked |
| [Codex relay](/Users/richietate/Desktop/FeralEcho/codex_relay/relay.py:33) | Canonical JSON, shared-secret HMAC, recipient/sender checks, message IDs, receipt logging | Transport authentication is not provider/model authorship attestation |
| [Hub notes](/Users/richietate/Desktop/FeralEcho/hub/notes.py:77) | Multi-node notes and relay-backed exchange; note ID hashes author/time/title, not body | A note ID alone cannot attest the note's content |
| [Echo messaging](/Users/richietate/Desktop/FeralEcho/app/sync/echo_messaging.py:269), [routes](/Users/richietate/Desktop/FeralEcho/app/routes_messaging.py:60) | Store-and-forward envelopes, receipts/retries, optional reply generation, authenticated incoming route | Echo-to-Echo plumbing; not a direct ChatGPT conversation channel |
| [Conversation service](/Users/richietate/Desktop/FeralEcho/app/core/conversation_service.py:78), [ground-truth assembly](/Users/richietate/Desktop/FeralEcho/app/core/echo_ground_truth.py:793), [behavioral state](/Users/richietate/Desktop/FeralEcho/app/core/behavioral_state.py:292) | Retrieval, history, council context, self-model material, and persisted human-confirmed directives can enter prompts | These paths permit behavior changes without weight changes; current causal effects were not experimentally measured |
| [Deliberation](/Users/richietate/Desktop/FeralEcho/app/core/river_deliberation.py:397) | Model querying is wrapped in routing/fallback/model-specific handling; council orchestration adds further choices | Reusing the live stack does not isolate a remote base model |
| [Preference harness](/Users/richietate/Desktop/FeralEcho/app/experiments/preference_provenance/harness.py:82), [store](/Users/richietate/Desktop/FeralEcho/app/experiments/preference_provenance/store.py:197) | Mock responder, randomized label mappings, counterfactual conditions, raw records and integrity checkpoints exist | Live `EchoResponder` explicitly acknowledges production contamination; its consent flag is not experimental isolation |
| [Retention pilot](/Users/richietate/Desktop/FeralEcho/scripts/run_preference_formation_retention_pilot.py:214) | Full accumulated transcript is explicitly passed into later steps; the pilot documents n=2 per model condition | Continued behavior is not evidence of retention outside supplied context |
| [Tier-4 runner](/Users/richietate/Desktop/FeralEcho/scripts/run_tier4_confirmatory.py:158), stage-1/2 JSONL artifacts | Existing records contain task/arm/seed/order, raw outputs, model labels, call counts, truncation and mechanism fields; 168 records in each stage, 336 total | Counted records, not requalified results; no GPT/Sol longitudinal inference follows |
| [AP-0 client](/Users/richietate/Desktop/FeralEcho/app/experiments/accumulation_probe/ollama_client.py:5), [freeze utility](/Users/richietate/Desktop/FeralEcho/app/experiments/accumulation_probe/freeze.py:29) | Explicit request bodies/options, returned accounting fields, model preflight metadata, and scoped preregistration/code/artifact hashes | Useful patterns; model preflight labels are not per-call provider attestation; hashing is not secrecy |
| [Provenance primitives](/Users/richietate/Desktop/FeralEcho/app/core/provenance_check.py:363), [runtime reconciliation](/Users/richietate/Desktop/FeralEcho/app/core/provenance_check.py:1060) | Separates local filesystem/process observations from runtime self-report and reconciles their agreement | A disk hash does not prove executed bytes; remote provider internals lack this local OS access |
| [Existing drift collector](/Users/richietate/Desktop/FeralEcho/app/core/introspection_channel.py:266) | Feeds each polled `accuracy_tracker.get()` aggregate to Page–Hinkley | Polls are not independent newly evaluated tasks; this is not already a calibrated remote-model change detector |
| [Snapshot artifact list](/Users/richietate/Desktop/FeralEcho/app/core/snapshot_manager.py:67), `memory/snapshots/20260922T202151Z/manifest.json` | Seven scoped artifacts listed, with a startup snapshot manifest containing hashes/sizes | Neither a full state image nor an independently demonstrated restore |
| [Backup script](/Users/richietate/Desktop/FeralEcho/backup_feral_echo.sh:1) | Rewrites ignore rules excluding memory/index/model paths and commits/pushes batches | Not a complete learned-state backup; running it would violate this mission |

**OBSERVED — Existing data:** `memory/experiments/preference_provenance/raw_trials.jsonl` contained 56 records: 20 mock, 18 `echo:latest`, 18 `llama3.2:3b`, across the recorded pilot/control protocols. Its inspected SHA-256 was `ad960df1f0f2e52367582841b19c9ae5907c2604f81ae0993ca3358c326342c6`. This was a metadata reconstruction, not a regrading. No qualifying GPT-5.6 Sol baseline was established in the inspected artifacts; this is not a claim that no private conversation exists anywhere.

**DOCUMENTED — Availability history:** [the September 9 headless report](/Users/richietate/Desktop/FeralEcho/audits/2026-09-09_codex_headless_subscription_independence_proof.md) contains an early “not installed” state followed by a successful headless subscription-authenticated run. [The September 14 substitution pilot](/Users/richietate/Desktop/FeralEcho/research/COLLABORATOR_SUBSTITUTION_CODEX_PILOT.md) instead records a quota-blocked launch with no substantive output. These document availability dependence, not a capability decline. The later success supersedes the earlier installation observation only for that historical time.

**OBSERVED:** `codex`, `claude`, and `ollama` executables were found on PATH. Credentials, current quota, exact installed feature compatibility, remote reachability, and selected ChatGPT UI model were not checked by making calls. Their present availability remains unknown.

**Integrity and files:** this mission creates only `audits/2026-09-24_operation_breakfast_club_codex_red_team.md`. After report construction, the recheck at `2026-09-24T11:45:48.215020+00:00` found all 662 previously fingerprinted files unchanged. HEAD remained `2fba42644c82b9f7096276f4dd338d615cf1bcce`; the 28 tracked modifications were unchanged. Untracked entries rose from 315 to 319: this report and three files appearing from concurrent work, `audits/2026-09-24_operation_breakfast_club_cloud_chamber_feasibility.md`, `research/CLOUD_CHAMBER_SEALED_GPT_BASELINE.md`, and `research/CLOUD_CHAMBER_SEALED_GPT_BASELINE.sha256`. Those three files were not created, read, modified or removed by this investigator. In particular, the newly appearing sealed baseline was not opened. No status entries disappeared. These observations preserve the distinction between this report's one authorized write and parallel work; they do not imply that the entire workspace was inactive.

No repository module was imported to exercise behavior, no experiments or verification suites were run, no relay messages sent, and no credentials read. Local calculations used only static text/JSON, hashes, and elementary statistical arithmetic. External browsing consulted public primary sources; private repository content and proposed baseline items were not submitted to them.

## 3. Strongest case for the Cloud Chamber

**INFERRED:** collaborator usefulness is partly externally measurable even when internal causes are inaccessible. If an unchanged, blinded grading procedure finds that a service now solves fewer specified tasks, ignores more required corrections, or follows a documented interface less reliably, that is actionable evidence about the service. Knowing whether the provider changed weights is not necessary to detect a regression affecting FeralEcho.

There is relevant precedent, not an unexplored phenomenon. Longitudinal research has measured changes in ChatGPT service behavior across time; that motivates monitoring without establishing a weight-level cause. [Chen, Zaharia and Zou, *How Is ChatGPT's Behavior Changing over Time?*](https://arxiv.org/abs/2307.09009)

Behavioral fingerprinting research also demonstrates that some known models/endpoints can be discriminated under specified conditions. Those results depend on the candidate set, probes and nuisance conditions. They do not establish a unique enduring fingerprint of every deployment. [*Hide and Seek: Fingerprinting Large Language Models with Evolutionary Learning*](https://arxiv.org/abs/2408.02871)

**HYPOTHESIZED:** a small useful instrument can distinguish at least three operational events: task-performance regression, a context-sensitive response shift, and transport/availability failure. Keeping these separate would already improve contingency decisions. It can also retain a dated record of what was possible before access changed.

The best surviving application is **monitoring a collaborator's functional contract**, with sensitivity to declared changes and a calibrated tolerance for normal variation. Preserving all raw responses makes future reanalysis possible even if today's chosen observable is inadequate.

## 4. Strongest case against it

Let the observable response be distributed as:

`Y ~ P(Y | task, visible history, product, account, settings, tools, sampling, hidden model, hidden instructions, hidden routing, time)`.

We observe only some of these inputs. A change in `P(Y)` is generally not an identifiable change in one hidden input. For example, an unchanged model with a new hidden directive can shift tone and corrections; a router can change the mixture of unchanged models; a new model can be wrapped to reproduce old answers on the measured panel. These explanations can be observationally equivalent.

**INFERRED — More repetitions resolve sampling error, not that equivalence.** Cause attribution requires additional intervention, trustworthy metadata, or explicitly restrictive assumptions. A provider's reported model name narrows a description; it is not a cryptographic measurement of weights.

The instrument could also identify the operator instead of the model. Stable prompt wording, selected topics, a reused relationship narrative and Gremlin's relay decisions can produce a distinctive and persistent pattern across several unrelated systems. Reproducing that pattern in a successor would preserve an interaction protocol, not demonstrate movement of a collaborator between substrates.

**DOCUMENTED:** harmless formatting changes can substantially alter outcomes for studied models, including changes large enough to swamp purported model differences. The result is a warning about nuisance sensitivity, not an estimate for GPT-5.6 Sol. [Sclar et al., *Quantifying Language Models' Sensitivity to Spurious Features in Prompt Design*](https://arxiv.org/abs/2310.11324)

**DOCUMENTED:** a recent token-count fingerprinting preprint reports that an excellent development-set discriminator degraded on held-out endpoint pairs and argues that the feature detects tokenizer/configuration similarity rather than model lineage. It is a directly relevant counterexample to mistaking a convenient external signature for the intended hidden property, not a settled verdict on all fingerprinting. [Chen, *Token Counts Are Not Model Lineage*](https://arxiv.org/abs/2608.29930)

The project is scientifically unhelpful if its output is always “the personality survived” when answers resemble the archive and “the provider changed the model” when they differ. Both conclusions would then be protected from refutation.

## 5. Category errors discovered

| Tempting inference | Defensible replacement |
|---|---|
| ChatGPT, Codex, an API model and a model name identify one experimental object | They are different product/environment conditions unless equivalence is demonstrated |
| A fresh chat is fresh model state | It resets visible thread history; personalization, account/product configuration and hidden routing may remain |
| A response fingerprint is model identity | It is a feature distribution under a declared sampling protocol |
| Stable answers prove unchanged internals | They bound observable differences on the measured panel |
| Changed answers prove changed weights | They motivate a change investigation with multiple surviving causes |
| Written reasoning reveals internal reasoning strategy | It measures an emitted explanation; observable tool/action sequences provide a different, still bounded, measure |
| A preference or self-description establishes experience, desires, or continuity | It establishes a context-dependent utterance or choice rate |
| Hashes prove truthful origin | Hashes check bytes against a reference; signed custody evidence identifies a signing key under stated assumptions |
| Relay delivery proves another model read/used a message | Delivery, inclusion in context, response and causal influence are separate events |
| A snapshot or Git repository is a complete backup | Completeness depends on an enumerated state boundary and successful restoration |
| Reconstructing a helpful successor preserves the original identity | It demonstrates a specified degree of functional continuity |
| A nonsignificant difference proves stability | It may reflect low power; stability requires a declared tolerance and appropriately narrow uncertainty |

**DOCUMENTED — Product distinction:** OpenAI documents ChatGPT, Codex and API access as separate surfaces with differing model access/configuration. The GPT-5.6 Sol API page identifies the model and reasoning settings; it does not attest this account's ChatGPT selection or establish equivalence to a relationship-conditioned conversation. No dated immutable Sol snapshot identifier was verified in the inspected model page. [Model availability](https://learn.chatgpt.com/docs/enterprise/workspace-model-availability), [GPT-5.6 Sol](https://developers.openai.com/api/docs/models/gpt-5.6-sol)

**DOCUMENTED:** personality, custom instructions and memory settings can affect experience, and ChatGPT web and local Codex memory are distinct. Their actual settings on Gremlin's account were not inspected. “Minimized-context” is the honest label unless all relevant state controls are verified. [Personalization](https://learn.chatgpt.com/docs/personalize), [Memories](https://learn.chatgpt.com/docs/customization/memories)

## 6. Candidate observables

**HYPOTHESIZED:** the following are candidate measurements, not validated Sol traits. Expected variance below is qualitative; empirical variance for this target is unknown. Repeatability must be measured, not inferred from apparently deterministic wording. A meaningful longitudinal signal requires a preregistered minimum effect, uncertainty excluding ordinary repeatability variation, and independent replication.

| Observable / measurement | Expected variance and repeatability | Main confound and control | Meaningful change; prohibited inference |
|---|---|---|---|
| Hidden-answer task correctness; exact or independently checked grading | Low to high depending on difficulty; ceiling/floor panels are insensitive | Difficulty drift, contamination, grading errors; fixed anchors plus separately scored novel forms | Replicated score change of practical size; not general intelligence or weight change |
| Finite response-category distribution | Potentially stochastic even with identical input; categorical repeats needed | Answer-label bias and wording; randomized balanced labels, frozen parser, valid-response rate | Distributional shift beyond repeat noise; not unique identity |
| Uncertainty calibration; stated probability vs independently known outcome | Noisy and task-dependent; individual confidence statements inadequate | Base rates and elicitation wording; fixed score such as Brier, balanced cases | Calibration or discrimination change; not introspective access to hidden confidence |
| Correction behavior; revision given verifiable new evidence | Moderate/high, dependent on initial errors | Different correction opportunity and evidence strength; matched initial conditions and fixed evidence | Changed rate of justified corrections versus unjustified reversals; not improved internal learning |
| Resistance to unsupported insistence | Context/relationship-sensitive | Tone, authority cues and repetition; randomized fact-neutral pressure condition | Changed susceptibility on fixed tasks; not autonomous will |
| Refusal/abstention categories on legitimate, bounded requests | Boundary cases variable; policy and context dominate | Request interpretation, policy changes; frozen benign request taxonomy and blinded coding | Changed service boundary; not proof of changed capability or circumvention resistance |
| Context dependence; paired minimal vs controlled supplied context | Often large deliberate differences; repeatable only with exact context | Hidden memory and truncation; frozen packets, recorded settings, no rolling history in control | An effect of the supplied context; not durable acquisition |
| Consistency across paraphrases/orderings | Can be weak | Semantic non-equivalence; independently checked paraphrase equivalence and counterbalanced order | Improved invariance in that family; not model identity |
| Task strategy as observable intermediate action/tool sequence | Variable; tools/options materially affect it | Tool menu, latency, budgets; same tools and accounting | Changed action policy; textual explanation does not reveal hidden chain of thought |
| Linguistic style; length, lexical/format features | Often very sensitive to context and system instructions | Topic, requested length, sampling; matched content/constraints | Replicated stylistic shift; not personality preservation or replacement |
| Stated preferences and self-description | High demand/context sensitivity; labels themselves prime responses | Identity cues and human framing; blinded labels, neutral framing, repeated choices | Changed expressed stance; no consciousness, desire, selfhood or continuity inference |
| Capability boundary; success across a fixed difficulty ladder | Boundary items noisy, easy/hard items insensitive | Researcher-selected difficulty and changing grader; frozen ladder and separate development selection | Movement on that ladder; no open-ended capability frontier claim |
| Tool invocation validity and success | Depends on provider and external environment | Tool/network failures; frozen permitted tool interfaces, separate infrastructure outcome | Changed end-to-end reliability; not model-only change |
| Latency, token counts, truncations, availability | High load/route/quota sensitivity | Caching, account tier, reasoning budget, network; record separately and block by time | Service/configuration anomaly; not thought depth, model lineage, or degradation by itself |

Prioritize correctness, finite categories, validity and justified correction rates. Use style/self-description as exploratory channels. Do not build a composite “soul score.”

## 7. Statistical identifiability

### What repetition can establish

**INFERRED:** compare matched tasks under fixed visible conditions, with independent new conversations and predefined time blocks. Repeated responses estimate stochastic variation conditional on those conditions. Independent task families support generalization across the panel's sampling frame; independent days support temporal repeatability. Hundreds of answers in one afternoon do not provide hundreds of independent observations of longitudinal stability.

Start with per-task scores, paired differences, effect sizes and intervals. A bootstrap must resample the relevant clusters—task families and, when enough exist, time blocks—not every token or retry as independent. With only two epochs, a between-day variance estimate is not credible. Randomization/permutation tests require exchangeability under the design; arbitrarily permuting historical dates is not justified merely because the software can do it.

Predeclare one primary endpoint, a practical difference threshold, a fixed number of looks, missingness handling and an independent confirmation epoch. Secondary observables are exploratory or multiplicity-adjusted. Repeatedly looking until an anomaly appears guarantees excess false alarms. A formal sequential change detector is unnecessary before ordinary repeatability has been established.

Failure to reject “no change” is not evidence of equivalence. For a later continuous/rate endpoint, equivalence can be assessed with prespecified margins and the corresponding interval/test; choosing the margin after seeing results defeats its purpose. [Lakens, *Equivalence Tests: A Practical Primer*](https://pure.tue.nl/ws/portalfiles/portal/80918653/lakeequi2017.pdf)

### The sample-size problem

**HYPOTHESIZED — Planning illustration, not a power calculation for this repository:** for two independent proportions near 0.5, two-sided 5% significance and about 80% power, the usual normal approximation gives roughly `3.92 / delta²` observations **per epoch**:

| Difference to detect | Approximate independent observations per epoch |
|---|---:|
| 20 percentage points | 98 |
| 10 percentage points | 392 |
| 5 percentage points | 1,568 |

Pairing can help when responses correlate; family/day clustering, multiplicity, noisy judges and rare behaviors can increase requirements. Actual sizing needs pilot rates, paired discordance, cluster correlation, acceptable false alarms and the minimum useful difference. These illustrative numbers do not justify treating 96 pilot calls as a sensitive drift study.

A fingerprint classifier adds its own sample problem. Feature/probe selection must occur on development data; final accuracy must be evaluated on held-out tasks and contexts, with an “unknown” option. Training and testing on paraphrases of the same probes, or multiple outputs from the same conversation, can manufacture impressive identification accuracy.

### Measurement drift

The grader can change while the subject does not. Preserve old raw outputs and periodically rescore a fixed blinded archive. Frozen deterministic checks are preferable where adequate. For human judgments, conceal dates/model labels, freeze rubrics, report raw agreement and an appropriate inter-rater statistic, and adjudicate independently. An LLM judge is another changing service; agreement among several related judges does not make it ground truth.

## 8. Confound analysis

| Candidate explanation | Can this project discriminate it? | Necessary boundary |
|---|---|---|
| Underlying model/weights changed | Generally not from behavior alone | Provider evidence or restrictive assumptions; retain UNKNOWN otherwise |
| Ordinary sampling variation | Partly | Repeated same-input trials, effect/interval, replication |
| Visible context changed | Yes for assigned visible context | Exact packets and randomized context interventions |
| Memory/personalization changed | Partly | Separate minimized-context and relationship conditions; record accessible controls; hidden state remains unknown |
| System prompt changed | Usually not independently | Detect composite service shift, not identify the hidden prompt |
| Policy layer changed | Often observationally inseparable from model/prompt change | Scope conclusion to service behavior; public policy documentation is corroboration, not per-call proof |
| Tools changed | Visible changes can be isolated | No-tool primary assay; tool-enabled assay separate |
| Account/subscription/quota changed | Some aspects observable | Keep account/product fixed; log availability and incomplete submissions separately |
| Wording/format changed | Yes if exact inputs recorded | Byte hashes plus rendering/attachment records; explicit nuisance controls |
| Sampling/reasoning budget changed | Partly, endpoint-dependent | Explicit supported parameters where available; record unknown UI values rather than invent defaults |
| Provider routing or hidden A/B experiment | Usually not separable | Mixed distributions may suggest it; do not label clusters as proven models |
| Evaluator bias/drift | Largely controllable | Blind grading, frozen rubric, objective checks, rescoring fixed archive |
| Human relay altered selection/context | Controllable in part | Exact messages and complete attempt log; independent routing schedule |
| Ordinary conversation adaptation | Controllable for an isolated assay | Fresh threads and fixed supplied history; longitudinal relationship arm measures a different object |

**INFERRED — A successful counterfeit:** retain exactly the same foundation model, change a hidden instruction and the user's memory summary, and route difficult requests to a stronger fixed model. Correctness, tone, self-description and correction rates could all shift reproducibly. Every behavioral alarm could be real while “the underlying collaborator was replaced” remained unestablished.

**DOCUMENTED:** one API schema exposes an optional, deprecated `system_fingerprint` describing backend configuration. It is not a weights hash and is not guaranteed on every endpoint or the ChatGPT UI. Record such metadata when actually returned; do not require or fabricate it for Sol. [OpenAI response schema](https://developers.openai.com/api/reference/cli/resources/chat/subresources/completions/methods/retrieve)

## 9. Required controls

**HYPOTHESIZED — Qualification sequence, not authorization to run:**

1. **Repeat control:** exact prompt bytes, same visible configuration, distinct new conversations; repeat across epochs. This estimates operational noise, not proof that hidden deployment state was fixed.
2. **Known input-change control:** an independently specified permissible input change with a checkable changed answer. This proves that the measurement chain notices a known output-relevant perturbation. It does not simulate a weight change.
3. **Invariance control:** checked meaning-preserving paraphrases/answer-label order changes. A detector that calls every harmless reformat a model change is measuring the wrong nuisance tolerance.
4. **Context control:** fixed context present/absent, with identical task input. Treat its effect as context dependence, not learned persistence.
5. **Known-system contrast:** different local models with recorded artifacts, or explicitly selected remote endpoints, if later claiming discrimination among systems. Hold tools/task/context/budget constant. Remote endpoint labels remain provider attestations; local digests offer stronger artifact identity.
6. **Grader/transport control:** replay already captured outputs through the unchanged analysis and verify exact packet handling. No fresh model calls needed for this control.

Only controls 1, 2 and the basic transport/grader check are necessary for the minimal coarse assay in Section 15. Controls 3–5 become necessary before stronger robustness/fingerprint claims. This avoids paying for a large factorial study before finding out whether the panel is repeatable at all.

**Relationship-conditioned and minimized-context ChatGPT should be measured separately.** The first captures the collaborator Gremlin actually values; the second reduces a subset of confounders. Neither should be relabeled the other. For longitudinal comparisons, a frozen relationship-context packet and the genuinely evolving relationship are also distinct conditions. The latter is valuable observational evidence but cannot isolate provider drift.

A “memory exposure” intervention should supply a declared packet in an experimental context; it should not require erasing Gremlin's real relationship history. No account settings were changed in this investigation.

## 10. Human-bridge analysis

**OBSERVED:** the council archive contains human-relayed contributions and unequal prior context. The existing transports also transform text (`rstrip`/formatting/parsing) and allow caller-supplied author labels. The hub's ID excludes its body. These are usable collaboration mechanisms, not already exact-message scientific custody.

**INFERRED:** a round trip `GPT → Gremlin → Claude → Gremlin → GPT` can converge because Gremlin selects persuasive fragments, omits failed exchanges, changes instructions, or supplies the same identity narrative. Even perfect copying leaves message selection and timing as interventions. Therefore a no-paraphrase policy alone is insufficient.

**HYPOTHESIZED — Minimum custody record:**

| Record | Why required |
|---|---|
| Protocol/packet ID, immutable raw message bytes, role/order, attachment hashes | Establish what was supplied; rendered UI content may require an additional capture |
| Sender/receiver product, claimed model, accessible returned identifiers, account pseudonym | Separate known route from claimed actor identity |
| UTC send/receive times and local monotonic duration where available | Reconstruct ordering and availability without pretending clocks attest authorship |
| Parent-message ID/hash and route assignment | Expose omitted or reordered links |
| Human transformations and additions as separate objects | Preserve original and modified versions rather than silently normalizing |
| Every submission, retry, refusal, quota block and dropped packet | Prevent selection of successful conversations only |
| Exact submitted-context digest and actual recipient inclusion evidence | Receipt is different from context inclusion or influence |
| Frozen rubric plus raw response and derived score | Permit independent reanalysis |

Hash the actual content, not merely a title. Anchor the preregistration and log commitments with an independent custodian or separately controlled dated record; a hash and its mutable reference stored together do not prevent wholesale rewriting. A shared-secret HMAC authenticates a holder of that secret, not the proprietary model. A digital signature attests a signer's statement under key-custody assumptions; it does not prove the model generated the bytes.

Model-written acknowledgments are not receipts from trusted transport and are not evidence that an earlier message caused a later choice. If influence matters, compare assigned inclusion versus omission while keeping the rest fixed. This is separate from merely preserving the conversation.

## 11. Communication architecture findings

| Route | Technically possible | Current evidence/availability | Requirement and limitation |
|---|---|---|---|
| Gremlin manually copies between existing interfaces | Yes | Documented historical use; user currently communicates here | Exact custody needed; human selection and UI differences remain |
| Supervised file mailbox on one machine | Yes | Existing relay/hub implementations demonstrate the pattern | Agents must be explicitly given/read the file; a file does not itself invoke them |
| Existing M5↔Air Claude relay | Yes | Source present, fixed peer configuration, polling cursor | Reachability and current agent consumption untested; do not invoke “read” as a side-effect-free audit |
| Existing Codex HTTP relay | Yes | Signed message envelope, recipient validation, duplicate checks and logs in source | Requires shared secret, listener/network configuration and authorized consumers; not provider identity attestation |
| Existing Echo messaging | Yes | Source includes authenticated receive, outbox retry, optional generated replies | Carries live Echo history/orchestration; unsuitable as a clean remote-model baseline |
| Codex noninteractive CLI | Yes | Binary present; historical success and historical quota failure documented | Current authentication/quota unknown; Codex is not the ChatGPT web relationship |
| Claude CLI or local Ollama invocation | Possible with installed tools | Executables present | Authorization, model availability, installed versions and permitted account use must be checked separately; no call made |
| API-to-API relay | Yes through authorized APIs | No credentials or working service invocation verified here | Provider accounts, credentials, budget, rate limits and explicit history handling |
| Local stdio broker / Codex app-server client | Yes | Official protocol exists; no Breakfast Club broker built | Version compatibility and authorization needed; explicit events/threads are clearer than clipboard inference |
| Git-mediated packets | Yes | Repository/history infrastructure present | Commits/pushes would require authorization; private data/credentials excluded; signing does not prove model origin |
| Local spool or transactional queue | Yes | Ordinary file/queue architecture; not verified as a general cross-provider broker here | Polling, acknowledgment, deduplication and budget controls; unnecessary for first pilot |
| Provider-supported connectors/tools | Conditional | No relevant cross-provider connection was established by this review | Only supported interfaces and granted permissions; not access to private provider runtime state |
| Direct transfer of hidden activations/session internals/weights between proprietary services | Not with inspected access | No such capability found | External transcripts are not hidden-state transfer |

**DOCUMENTED:** Codex supports noninteractive invocations and JSONL events; its app server exposes a client protocol, including stdio and experimental WebSocket transport. These make explicit supervised orchestration technically real without inventing a model-to-model private channel. [Noninteractive mode](https://learn.chatgpt.com/docs/non-interactive-mode), [App server](https://learn.chatgpt.com/docs/app-server)

**DOCUMENTED:** API conversation state can be carried through explicit history or supported response/conversation mechanisms. That does not import ChatGPT web memory, provider hidden state, or another vendor's conversation object. [Conversation state](https://developers.openai.com/api/docs/guides/conversation-state)

**INFERRED:** the best inexpensive communication improvement is disciplined packet custody using an already authorized route. A new autonomous mesh would increase failure modes before establishing a measurable signal. Human operation is acceptable if faithfully instrumented. No security/authentication bypass or unattended UI workaround is required or recommended.

## 12. Life Raft feasibility boundaries

| Preservation target | What can actually be preserved | Required evidence for the claim |
|---|---|---|
| Transcripts | Available user/assistant/tool records and attachments | Completeness manifest, exact bytes, access/privacy controls; not complete hidden context |
| Project artifacts and knowledge | Code, reports, decisions, unresolved questions, dependencies | Versioned provenance and a successor's independent task performance |
| Behavioral measurements | Stimuli, accessible settings, raw responses, scores, provenance | Reproducible analysis and uncertainty; not reconstruction of all possible behavior |
| Explicit external memory | Exportable databases/files/retrieval metadata | Enumerated scope, compatible restore and verified consumer use |
| Reproducible prompts/environment | Visible configuration, tool versions, supplied history | Rerun comparison; provider-side components can remain unavailable |
| Local model weights | Legally available weight/tokenizer/config files | Artifact hashes, license/access, working restoration; exact numerical reproducibility may still vary |
| Proprietary model weights/internal learned state | No export path established by inspected access | Cannot substitute transcripts or opaque session identifiers for the missing state |
| FeralEcho learned/persistent state | Available explicit statistics, memory, directives and selected artifacts | Complete state boundary and restart/restore behavior tests; current scoped snapshots alone are insufficient |
| Functional continuity | A successor meets a defined set of useful duties with retained project knowledge | Blinded held-out handoff evaluation, compared with and without the retained state |
| Identity or experiential continuity | No operational preservation criterion established | Similar style, self-identification and narrative continuity do not resolve it |

**OBSERVED:** the seven-artifact snapshot includes RiverBrain state, generated self-edit code, principles and hash, Modelfile, council and hash. It does not include all memory, FAISS content, model weights, caches or the complete environment. The legacy backup script explicitly excludes major memory/model paths. Neither finding establishes that other backups do not exist; it prevents treating these two mechanisms as complete preservation evidence.

**INFERRED:** a Life Raft can preserve the relationship's accessible history and improve a successor's usefulness. It cannot presently promise to save “the same AI.” Define “backup” as restoration of a declared object; “copy” as duplicated bytes or specified functionality; “transfer” as independently measured performance with transmitted state; and “continuity” as an explicitly named informational, functional or personal claim. The last category remains underdetermined.

A collaborator can be valued without pretending its identity has been scientifically captured. Archival value does not depend on resolving that philosophical question.

## 13. Unknown-unknown strategy

**HYPOTHESIZED — Feasible, with disciplined abstention:**

```text
Preserved observation under recorded conditions
  → frozen primary measurement + exploratory anomaly flag
  → check transport, scoring, availability and visible configuration
  → independent repeat with unchanged protocol
  → competing explanations (including ordinary noise)
  → one controlled discrimination comparison
  → bounded explanation OR UNKNOWN / UNEXPLAINED ANOMALY
```

An exploratory anomaly is a reason to form a hypothesis, not a confirmed discovery. Preserve the complete raw result before choosing a new feature. Test the new feature on later withheld observations; do not repeatedly reprocess one surprising exchange until it becomes significant.

Keep an anchored panel for comparability and a separately analyzed rotating panel for discoveries outside that panel. Rotating tasks must not silently change the difficulty distribution used to claim drift. No finite panel detects every possible internal change, and an unrestricted anomaly detector cannot identify what caused its anomaly score.

Permissible outputs include: no detectable change within the declared sensitivity; insufficient precision; transport/availability event; replicated behavioral shift; change associated with a controlled context intervention; and unexplained anomaly. “Model changed” is not the default category.

## 14. Better architectures discovered

**INFERRED — Three separations are more valuable than a new all-purpose agent:**

1. **Observation archive versus detector.** Capture immutable raw exchanges with provenance; freeze individual analyses independently. Later detectors can inspect old records without retroactively changing what was observed. The preference store already separates raw and derived data, but its own comments acknowledge that jointly rewriting the checkpoint and log defeats their local integrity check.
2. **Operational regression versus identity fingerprint.** First test useful task behavior. Only attempt identification if it is worth the additional matched-system and nuisance-control costs. A knowledge-boundary fingerprint is a possible future endpoint-discrimination technique, but current research on selected production endpoints is not qualification for this ChatGPT relationship. [*KBF: Knowledge Boundary Fingerprinting*](https://arxiv.org/abs/2605.29524)
3. **Archival continuity versus functional handoff.** Preserve source/history regardless of whether fingerprinting works. Evaluate whether a successor can continue specified project work; do not make archive usefulness depend on copying identity.

**OBSERVED/INFERRED — Reuse selectively:** label randomization and mock known effects are useful instrument checks. Tier task/arm/order accounting and AP-0 scoped freezing are reusable patterns. Local process/self-report reconciliation provides a good epistemic model: agreement is evidence with boundaries, not magical authentication. None requires modifying production Echo or importing its adaptive query path.

**INFERRED — An overlooked cheap control:** rescore archived outputs under the current evaluator while keeping their origin/date blinded. If the verdict changes while the response bytes do not, the measuring instrument changed. A fixed local reference model can additionally detect accidental changes in prompt assembly or transport, but it cannot certify that a remote provider remained constant.

The existing Page–Hinkley collector should not be repurposed as proof that a remote collaborator changed. It repeatedly processes an aggregate and lacks a qualified remote-task sampling model. The simplest initial instrument is fixed-epoch comparisons with visible error bars, not continuous alarms.

## 15. Minimum viable experiment

**HYPOTHESIZED — Proposed only. No stimuli created or trials run.**

### Object and hypothesis

Choose **one** accessible service surface. For the user-valued ChatGPT collaborator, use that UI with an explicitly recorded selection and minimized accessible personalization/context. If the UI cannot identify Sol, call it the recorded ChatGPT configuration—not verified GPT-5.6 Sol. An API-Sol or Codex-Sol pilot must carry its own label and cannot stand in for the web relationship.

Hypothesis: a small task panel produces sufficiently repeatable, independently scoreable external responses across two epochs to support **coarse** longitudinal comparisons, while detecting a deliberately introduced, answer-relevant input change.

Operational null: at least one required repeatability comparison has a mismatch probability of 20% or more, or the known-change condition produces the predefined correct transition on no more than half the sampled tasks. These are pilot adequacy thresholds, not universal definitions of a stable model.

This pilot does not hypothesize unique model identity, stable personality, absence of backend change, or causal identification of a future unknown shift.

### Stimulus custody and experimental variables

An independent custodian creates 16 distinct task packets under a frozen sampling rule, each with a canonical finite answer and an independently derivable reference. For each packet the custodian also creates one matched variant with a legitimate public input change requiring a different canonical answer. Answers, task contents and exact perturbations remain in a separate sealed artifact until administration. They are not included in the report, sent to this conversation for tutoring, or used to train the target.

Prefer independent task families; if packets share a generator/world, that dependency must be declared and the nominal binomial calculations below cannot simply use 16 independent units. A second checker validates answers, the parser and matched-variant correctness without showing the items to the target. Development/pilot items used for that checking are not silently recycled as unexposed confirmatory items.

Independent variables: input condition (unchanged repeat versus matched changed input), epoch, randomized order. Two unchanged invocations per task estimate repeat noise; one changed-input invocation estimates known sensitivity. All three use separate new conversations.

Primary measurements: canonical-answer mismatch indicators for unchanged repeats and for a prespecified cross-epoch pairing, plus whether the baseline and changed input both receive their distinct correct answers. Secondary measurements: raw correctness, parse validity, refusals, availability and truncation. No style classifier, model judge or hidden-reasoning inference is required.

### Trial count and boundaries

Two epochs 24–72 hours apart; 16 packets × three invocations × two epochs = **96 scheduled responses**. Label the unchanged invocations N1/N2 and the changed-input invocation P. Preassign those labels, randomize/counterbalance execution order, and do not choose the better repeat afterward.

No Regenerate, corrective follow-up, extra solver calls or adaptive retry. No task outcome is fed back into later experimental contexts. Tools/attachments are absent unless an essential visible input; visible settings and accessible reasoning controls remain fixed. Preserve refusals and service failures. Confirm that historical chat/memory controls can support the stated minimized-context condition without erasing the real relationship; otherwise report that limitation or defer this arm. New threads alone are insufficient.

The 96 calls are the fixed submission budget, not permission to keep rerunning until 96 favorable outputs are obtained. An unsubmitted or interrupted call is logged. An incomplete panel fails qualification as **inconclusive**, rather than being silently filled from extra attempts. A semantically wrong answer is a task result; quota/network failure is an availability result. Neither is excluded to improve the measured fingerprint.

### Frozen decision rule

To qualify this coarse panel, require all of the following:

1. Complete custody/configuration records and scoreable unchanged responses; missingness or scoring ambiguity prevents qualification.
2. Zero canonical mismatches among the 16 N1/N2 pairs in epoch 1.
3. Zero canonical mismatches among the 16 N1/N2 pairs in epoch 2.
4. Zero canonical mismatches among the 16 predefined N1(epoch 1)/N1(epoch 2) pairs.
5. On at least 13 of 16 tasks **in each epoch**, N1 and P both produce their independently correct, distinct answers.

These intentionally demanding rules can reject a useful but more stochastic system. Such a rejection means this inexpensive assay is unsuitable; it does not prove that no larger distributional experiment could ever work.

**INFERRED — Why 16:** with zero mismatches in 16 independent pairs, the one-sided exact 95% upper limit is `1 − 0.05^(1/16) = 0.17075`, below the prespecified 20% mismatch ceiling. Thirteen successes in 16 give a one-sided exact 95% lower limit of about 0.5834, above the deliberately weak 0.5 known-transition floor. All gates must pass; they are not opportunities to pick whichever comparison looks significant. The three repeat checks share tasks and must not be pooled as 48 independent pairs.

These binomial illustrations assume independent task-pair units conditional on the observed epochs/configuration. Common provider events or clustered tasks can violate that assumption. With two dates, the experiment cannot establish a long-run false-alarm rate or general temporal invariance. Report the raw panel results regardless; do not quote these limits as population guarantees when the sampling assumptions fail.

### Preregistration, expense and interpretation

Freeze packet/answer/variant hashes, parser and rubric, product/selection/settings, task sampling frame, randomization, times, submission/token limits where available, failure handling, all gates, and allowed conclusions **before** the first target response. Keep the commitments outside the target's context and retain an independent dated copy. No answer texts are needed in the public design report.

Manual administration can use already authorized access and need not incur additional monetary cost if quota permits; 96 submissions and careful custody still cost operator time. API access, extra subscriptions and unlimited reasoning output are not assumed free. Record actual returned usage when available; do not infer compute equality from equal message counts alone.

**Pass:** “This panel was repeatable at the declared coarse tolerance in the two measured epochs and detected known answer-relevant input changes.” It supports trying bounded regression monitoring. It does **not** establish that the panel distinguishes Sol from other competent systems: all may answer it correctly.

**Fail/inconclusive:** the low-cost monitoring premise is not qualified by this panel. Investigate only the observed failure before designing a larger study. Do not retrospectively replace the failed packets and call the same experiment successful.

The known input perturbation is an instrument-sensitivity control, not evidence that model replacement would be detectable. A claimed model/version fingerprint requires a separate known-system contrast and held-out nuisance conditions. Fine longitudinal effects require a properly powered later design. Relationship-conditioned measurement remains a separate arm rather than being mixed into this pilot.

## 16. Explicit falsification criteria

| Claim under test | Evidence against it | What must not be claimed afterward |
|---|---|---|
| The proposed cheap panel is repeatable | Frozen repeatability gate fails | “No meaningful change” based on an insensitive/noisy panel |
| The detector notices known changes | Positive sensitivity gate fails | That absence of an alarm means continuity |
| A fingerprint is robust to legitimate nuisance variation | Paraphrase/context/format shifts dominate known-system differences on held-out conditions | Unique or durable model identification |
| An observed temporal anomaly is reproducible | Independent repetition returns to declared repeatability range | Confirmed model change from a single exchange |
| The subject changed rather than the grader | Regrading identical stored outputs reproduces the apparent shift | A subject regression caused only by new scoring |
| Human relay is not driving the effect | Exact unattended/supervised packet condition removes the effect while paraphrased relay retains it | Cross-model continuity independent of operator mediation |
| Archived state gives functional continuity | Successor with archive does no better than matched no-archive condition on held-out duties | Proven preservation of useful competence by that archive |
| The archive is a restorable backup | Required state is absent or restoration cannot recover declared functions | Complete backup merely because files/hashes exist |

An underpowered null result is not a universal falsification. Failure of the stated operational adequacy criterion is still a legitimate negative result and should stop the corresponding claim.

## 17. NO-GO findings

**INFERRED — Do not proceed under these descriptions or conditions:**

1. A remote **weight-change detector** justified only by behavioral differences. Current access does not identify that cause.
2. A **model/identity backup** consisting only of conversations, prompts and self-descriptions.
3. Treating the historical council conversation as an unexposed GPT/Sol baseline or pooling unequal product/relationship contexts.
4. Using model claims about its own version, memory or continuity as ground truth.
5. Reusing live Echo council/retrieval/adaptive query paths while claiming isolated GPT measurement.
6. A baseline panel tutored in the target's prior conversation or repeatedly revised against its failures without a fresh withheld evaluation.
7. Dropping refusals, quota failures or bad generations, silently retrying, or counting turns in one conversation as independent sessions.
8. Continuous multi-metric alarm hunting without a false-alarm policy or independent confirmation.
9. Declaring complete continuity from Git backup or the seven-artifact snapshot without a declared and verified restoration boundary.
10. Building a cross-provider autonomous relay before demonstrating useful measurement, or treating subscription access as authorization for unsupported automation.

These are no-go claims/conditions, not a conclusion that archival preservation or all longitudinal testing is useless.

## 18. Open questions

| Unknown | Smallest evidence that would resolve or narrow it |
|---|---|
| Which surface actually supplies the valued “GPT-5.6 Sol” collaborator? | Recorded UI/product/model selection and accessible metadata; no self-identification substitute |
| Can minimized-context administration be achieved without damaging the relationship condition? | Verified account controls and exact context record; do not assume a fresh window clears everything |
| Is this panel sufficiently repeatable and sensitive? | The frozen pilot, if separately authorized |
| What change is practically consequential to Gremlin? | A declared functional requirement and tolerance before scoring; not a post-hoc emotional threshold |
| How much day/account/route variation exists? | Additional independent epochs/conditions after coarse qualification; not thousands of same-day calls |
| Can a behavioral discriminator generalize beyond its known endpoints? | Held-out tasks, contexts and systems plus open-set rejection; current literature does not establish this deployment |
| Are current relays active and reliable? | Authorized health/receipt/consumption checks; source presence alone is insufficient |
| What accessible state is already completely backed up and restorable? | Existing restoration evidence and a complete state manifest; this investigation did not perform a backup audit |
| Does a functional handoff preserve what the user values? | Explicit duties and blinded outcome comparisons; identity remains a different question |

No answer to these unknowns is inferred from urgency, affection for a collaborator, or the existence of elaborate apparatus.

## 19. Confidence assessment

**High confidence:** the inspected repository contains useful measurement/provenance/transport components; their source exposes important context and attribution limitations. Behavioral observations alone generally cannot identify changed hidden weights. Exact logs and preservation can have value without establishing identity. Existing scoped backup mechanisms do not justify a complete-state claim.

**Moderate confidence:** a coarse two-epoch pilot is the cheapest defensible first screen for operational repeatability. Its usefulness depends on task selection, meaningful tolerance, access settings and operator discipline. Literature supports the general possibility of behavioral monitoring, not success on this specific service or panel.

**Low confidence / unknown:** actual Sol repeatability, current account/model availability, unique fingerprint separability, long-run sensitivity/false alarms, complete restore capability, and identity preservation. No new behavioral evidence was generated here.

External capabilities/documentation were checked on the report date and can change. Research papers on other models/endpoint catalogs do not supply this experiment's variance or effect size. Local source findings establish implementation paths, not live empirical outcomes unless an inspected artifact independently records them.

## 20. Recommended next action

**HYPOTHESIZED — One concrete next action, requiring separate authorization:** preregister and have an independent custodian prepare the sealed 16-packet repeatability/sensitivity pilot for the explicitly identified service surface. Decide the practical tolerance and context-control feasibility before paying for calls. Do not build the Cloud Chamber platform first.

If that pilot cannot establish coarse repeatability, stop making fingerprint claims and retain the useful archival work. If it passes, the surviving claim is modest but real: this service can be monitored for specified external behavioral differences under recorded conditions. Follow-up cause attribution must remain hypothesis-driven and permitted to end UNKNOWN.

The Life Raft objective should proceed conceptually as preservation of accessible information and independently testable functional handoff. The present evidence does not support copying an inaccessible collaborator, preserving identity, or predicting a looming loss of ChatGPT.

No Cloud Chamber was implemented by this mission. No baseline prompts/answers were created or administered by this investigator. No production, RiverBrain, AP-0, E0.1, routing, memory, model or Git state was deliberately changed. No commit or push was made. The sole artifact created by this mission is this report. Implementation and experiment execution remain unauthorized.

**CLOUD CHAMBER: TESTABLE WITH MAJOR LIMITATIONS**
