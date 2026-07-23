# Memory Retrieval Ablation Experiment — 2026-07-23

Direct follow-up to `audits/2026-07-23_systems_physiology_audit.md` §7 ("Memory
Influence Analysis"), which flagged "does retrieved memory context change
actual LLM output" as the single biggest unmeasured question in that audit
(confidence 15-20%, explicitly not estimated further without a live
experiment). This is that experiment.

**Result, stated plainly up front:** the measured difference between
responses generated with real memory retrieval and the identical prompts with
retrieval forced empty is **not statistically distinguishable from ordinary
sampling noise** (Mann-Whitney U p=0.48, Welch's t-test p=0.37, n=30
treatment pairs vs. n=5 noise-floor pairs). This does not prove memory has
zero effect — it means this experiment's noise floor is comparable to or
larger than whatever effect exists, so a real effect smaller than that floor
would be invisible to this design. Full reasoning and honest limitations
below, including a real, unplanned scope narrowing (see §3) that this report
does not paper over.

---

## 1. Method

Reused the real, unmodified production pipeline —
`app.routes_echo_studio._build_full_prompt()` +
`app.core.echo_model_orchestrator.echo_query()`, exactly what `/chat/stream`
(mode: full) calls — rather than a reimplemented copy, so the experiment
measures what the live system actually does.

- **Test set**: 30 real prompts drawn from `memory/interaction_log.jsonl`,
  filtered to conversational-shaped entries (task_type in
  coding/personal/creative/reasoning/general, prompt length < 2000 chars,
  self-edit meta-prompts excluded), then further filtered to only those where
  the real (unablated) retrieval pipeline actually returned a non-empty
  memory block — otherwise the experiment would just compare a prompt to
  itself.
- **Ablation**: a pure in-process `unittest.mock.patch` of
  `app.core.memory_bridge.retrieve_relevant_memories` → `[]` for the duration
  of one call. No source file was edited — `memory_bridge.py` is on
  `EDIT_FORBIDDEN_TARGETS`, and a monkeypatch scoped to one script's process
  achieves the same experimental control with zero production code change.
- **Session state**: always a fresh, empty `{"conv_history": [],
  "history_summaries": []}` for both modes, so conversation-history content
  never varies between control and ablation — isolating the memory-retrieval
  effect specifically, not conflating it with session history.
- **Scoring**: embedding distance via the system's own embedding model
  (`memory_bridge.embed_text`, sentence-transformers all-MiniLM-L6-v2 — the
  same model FAISS retrieval itself uses, not an external API), reported as
  `1 − cosine_similarity`. Quality delta via the system's own
  `echo_quality_scorer._score_response_quality()`.
- **Noise-floor calibration (addition beyond the original spec, disclosed
  here rather than silently added)**: for 5 of the 30 prompts, ran **control
  mode twice** (same prompt, memory present both times) instead of
  control-vs-ablation, to measure the distance attributable to ordinary LLM
  sampling stochasticity alone, independent of any manipulation. Without this,
  a raw "distance > 0.2" reading has no way to distinguish a real effect from
  plain noise — and the results below show this distinction was decisive, not
  academic.

**Production side-effect handling** (checked before running, not assumed):
`echo_query()` never commits to FAISS vector memory on this path (confirmed
by grep — that only happens via `run.py`'s `/mirror_echo` route and
`emergent_scheduler.py`'s autonomous loop, neither of which this experiment
touches). It does unconditionally call `RiverBrain.learn()`/`.save()` on
every real generation, which is irrelevant to what this experiment measures —
`RiverBrain.learn`/`.save`/`._do_save` were monkeypatched to no-ops at the
class level for the whole script process (a smoke test first found that
patching only the singleton *instance* wasn't sufficient — `.save()` only
enqueues onto an already-running background writer thread that calls the
real `._do_save()` on its own periodic timer, independent of `.save()`
itself; class-level patching closed that gap). A `river_brain.pkl` backup was
also taken as defense-in-depth. **Verified after the run**: zero `[RIVER]`
log lines of any kind appear anywhere in the full run log — the
neutralization held for all 70 real generations, not just the smoke test.
`river_brain.pkl` did grow in size and mtime over the run's ~12.5-hour
wall-clock span, but that's the live production server's own legitimate,
concurrent real activity (confirmed running throughout, PID 5569) — not this
experiment.

`memory/interaction_log.jsonl` unavoidably gained 151 real lines (one flat
journal write per generation is not gated), each tagged
`source="memory_ablation_experiment"` — distinct from `"user_conversation"`,
so this data is forensically excluded from the task-type-classifier's
online-learning hook and the user-rating attribution path (both gated
exactly on `source=="user_conversation"`, `echo_model_orchestrator.py:236,333`)
and stays cleanly filterable out of any future audit of real usage.

---

## 2. Results

**Sanity check (did the manipulation actually work every time?):** control
mode had a real, non-empty memory block present in 30/30 pairs (by
construction — that's the selection filter). Ablation mode had the memory
block present in 0/30 pairs. The experimental manipulation was clean and
reliable across all 30 pairs, with zero exceptions.

**Embedding distance, control vs. ablation (n=30):**
- mean = 0.3040, median = 0.2524, std = 0.1528, range 0.1028–0.6726
- 21/30 (70.0%) exceed the originally-proposed "significant" threshold (>0.2)
- 0/30 (0.0%) fall below the originally-proposed "negligible" threshold (<0.05)

Taken alone, this reads as strong evidence of a large effect. It isn't —
see the noise floor below.

**Noise floor, control vs. control, same prompt run twice (n=5):**
- mean = 0.2537, median = 0.2021, std = 0.0883, range 0.1710–0.3657
- individual values: 0.2021, 0.1734, 0.3657, 0.1710, 0.3564

The noise floor's mean (0.2537) and median (0.2021) sit almost exactly on top
of the treatment group's mean (0.3040) and median (0.2524). **The originally
proposed ">0.2 = significant" threshold is not usable as stated in this
system** — ordinary sampling noise alone, with zero manipulation of any kind,
regularly exceeds it.

**Statistical comparison (treatment vs. noise floor):**
- Mann-Whitney U = 91.00, p = 0.4767
- Welch's t-test: t = 0.959, p = 0.3665

Neither test comes close to a conventional significance threshold. The
treatment distances are not distinguishable from the noise-floor distances
with this sample.

**Quality score delta (ablation − control), n=30:**
- mean = −0.0667, median = 0.0000, on the system's real 0–4 scale
- 24/30 pairs show exactly zero quality difference; only 6/30 show any
  nonzero delta at all, and those are small and mixed in sign

No systematic quality effect, in either direction, survives this sample.

**Elapsed time (real model latency, not part of the research question but
worth recording):** control mean 286.8s / median 66.1s / max 4940.9s (~82
min); ablation mean 194.0s / median 77.3s / max 1890.1s (~31.5 min). The wide
gap between mean and median in both indicates a handful of unusually slow
individual calls (likely a slower model getting selected, or resource
contention with the live production server sharing the same Ollama instance)
dominating the total wall-clock time — this is why the run took roughly 12.5
hours rather than the originally estimated 1-2.

---

## 3. A real, unplanned scope limitation — stated directly, not glossed over

**29 of the 30 selected prompts were `task_type="personal"`; only 1 was
`"coding"`, and none were creative/reasoning/general.** This was not a
selection bug — it's a genuine, if unplanned, discovery about *when* real
memory retrieval actually fires in this system: `personal`-task
conversational prompts (naturally about continuity, "what have we discussed,"
identity, relationships) are, empirically, far more likely to semantically
match prior FAISS-stored content than one-off technical/creative/task
prompts are. The "find real memory-retrieval hits" filter simply reflects
that real distribution back.

**Consequence: this experiment almost entirely tested the single-model
direct-response path** (`river_deliberation.py`'s `DIRECT_ECHO_TASKS`
bypass), not the multi-model council-deliberation path
(`deliberate_and_learn()`'s full 3-councillor + synthesis flow) that
`coding`/`creative`/`reasoning`/`general` prompts go through. **The
conclusion below is scoped to the `personal`/direct-response path — it
should not be generalized to claim memory retrieval has no measurable effect
in council-deliberated responses, which this experiment did not meaningfully
exercise (n=1).**

---

## 4. Conclusion

**For the `personal`-task, direct-response path specifically:** the
measured effect of removing retrieved memory context on final response
content and quality is not distinguishable from ordinary LLM sampling
noise, at this sample size (n=30 treatment, n=5 noise-floor). This is a
real, evidence-backed finding, not a null result being spun as one — but it
answers a narrower question than "does memory matter at all," and it does
not rule out a real effect smaller than the noise floor (roughly 0.17–0.37
in this embedding-distance metric), nor does it say anything about the
council-deliberation path.

Combined with the physiology audit's independent, code-level finding that
memory retrieval never touches model selection, task-type classification, or
self-edit targeting under any code path (§7 of that audit) — the overall
picture for `personal`-task conversations is that retrieved memory context's
demonstrated causal footprint is narrower than its architectural prominence
would suggest: real for the two scheduling-gate branches already identified,
unproven (not disproven) for shaping the actual words in a direct response.

---

## 5. What would sharpen this, if it's worth doing again

1. **Reduce sampling noise directly**: run both modes at `temperature=0`
   (deterministic decoding) instead of the system's normal sampling
   temperature. This would isolate the true causal effect of memory content
   almost entirely from confounding stochastic variance — likely the single
   highest-value, cheapest fix to this design, since the noise floor found
   here is the main reason the result is inconclusive rather than definitive.
2. **Force task-type diversity** in prompt selection (e.g., require at least
   6-8 real memory-hit prompts per task_type) rather than letting the natural
   hit-rate distribution decide — this would let a future run actually say
   something about the council-deliberation path, which this one couldn't.
3. **Larger noise-floor sample** — n=5 is thin for a baseline this
   consequential to the conclusion; 15-20 would meaningfully tighten the
   comparison.
4. **A larger treatment n** would help too, but given how close the two
   distributions already sit (means within ~0.05 of each other, p-values far
   from significance), more samples are unlikely to flip this conclusion
   without also addressing the noise floor directly (item 1).

---

## 6. Artifacts

- `scripts/memory_ablation_experiment.py` — the harness (kept, not a
  throwaway script; reusable for a future, sharper run per §5).
- `scripts/memory_ablation_test_set_2026-07-23.json` — the 30 selected
  prompts with metadata.
- `scripts/memory_ablation_results_2026-07-23.json` — full results (30
  treatment pairs + 5 noise-floor pairs, including complete control/ablation
  responses, embedding distances, quality scores, elapsed times).
- `memory/memory_ablation_run.log` — the full run's console output.
- `memory/river_brain.pkl.pre_ablation_backup_20260722T190227Z` — defense-in-
  depth backup, confirmed unnecessary (RiverBrain writes were neutralized and
  held for the entire run, verified by zero `[RIVER]` log lines) but kept
  rather than deleted, in case it's ever wanted.
