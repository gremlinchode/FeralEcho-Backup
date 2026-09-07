# Does the Existing Garden Accidentally Revisit Relevant Experience?

**Status:** Complete. Read-only investigation — no code, garden state, memory state, or
RiverBrain state was modified. `run.py` was not started at any point.

**Pre-flight (unchanged throughout):** `run.py` not running. `memory/river_brain.pkl`
sha256 `eee193444a735d6ae510e8f8fa0faae1da4b2b1467a2a5da6f15c93467c9d815` (re-verified
after this pass). Git HEAD `2cf2d95009943797db5ec41fea9b4021634fd5e6` (unchanged). Only
new file produced by this investigation: this report itself.

---

## 1. What was measured

The question this investigation answers: does `select_from_garden()`'s existing
staleness/novelty/category weighting — which has **zero designed relevance-matching
logic** (confirmed by direct source read, `app/core/garden_manager.py:334`, reproduced
verbatim in the prior session context) — nonetheless produce selections that are
lexically closer to Echo's real, surrounding activity than pure chance would predict?
If it does, that would be evidence of *accidental* digestion: a side effect nobody
designed, still functionally useful. If it doesn't, the garden is confirmed to be a
pure staleness-cycling mechanism with no relevance property at all, designed or
accidental.

## 2. Data used

- `data/question_garden.jsonl` — 13,727 real entries, full population, no sampling at
  the loading stage.
- `memory/interaction_log.jsonl` — 13,324 real entries, real coverage window
  `2026-08-22T17:55:41` to `2026-09-07T00:23:39`.
- Of the garden's 7,193 entries with `times_asked > 0`, **2,211** have a `last_asked`
  timestamp falling inside the interaction_log's real coverage window — this is the
  full, non-sampled population of real, reconstructable historical selection events
  used for every population-level statistic below. (The remaining 4,982 ever-asked
  entries were last asked before interaction_log's coverage begins and are excluded,
  not because they're irrelevant but because there is no real surrounding context to
  compare them against.)

**Known, disclosed limitation carried over from Phase 1 mapping:** `last_asked` stores
only the single most recent ask per question, not a full history. A question asked 5
times only contributes one reconstructable selection event (its most recent one) to
this analysis — real revisitation frequency is underrepresented, but the 2,211 events
that *are* reconstructable are genuine, not synthetic.

## 3. Relevance operationalization — frozen before computing which selections "look relevant"

Per the mission's explicit instruction not to define relevance after seeing results,
the mechanism was frozen first; only the **threshold values** were calibrated against
the null distribution's own shape (a legitimate scale-calibration step, not an
outcome-dependent one — see the null-baseline discussion below for why this ordering
matters and doesn't leak information about "is there a real effect").

- **Signal:** Jaccard word-overlap between the garden question's own token set and the
  union of tokens from every interaction_log entry (prompt + response) falling inside a
  time window centered on the question's real `last_asked` timestamp. Non-semantic,
  mechanical, explicitly a proxy — chosen per the mission's own preference for a
  programmatic baseline over using an LLM as a relevance oracle.
- **Windows:** primary ±20 minutes (chosen because `emergent_loop`'s established real
  cadence is ~150–450s/cycle, so ±20 min spans several real autonomous cycles without
  reaching into unrelated, distant activity); ±5 min and ±60 min computed as sensitivity
  checks.
- **Tokenization:** lowercase, word-regex extraction, small stopword list, minimum
  length 3 — a standard, disclosed, non-tuned normalization.
- **Level 0–4 mapping:** fixed as **null-baseline percentiles** (50th/75th/90th/97th of
  the same statistic computed against random, correctly-weighted draws — see §4) rather
  than round numbers, so "Level N" has a precise, disclosed, chance-relative meaning
  tied directly to the required null comparison. This was decided and written down
  before any specific selection event's Level was computed.

## 4. Null baseline — preserving the real selection-weight distribution

Per the mission's explicit requirement, the null baseline is **not** a uniform random
draw. For each of the 2,211 real selection events, one *other* garden question was
drawn via `random.choices()` weighted by a direct reconstruction of
`select_from_garden()`'s real formula (category-frequency term, `times_asked==0`
novelty bonus, staleness-cap term, resolution-score term, human-source bonus — every
term present in the real function, reproduced from the verbatim source read earlier in
this investigation), then scored against the **same real context window** the real
selection actually occurred in. Fixed seed (`20260907`) for reproducibility. This
isolates the one variable actually in question — *which* question got selected — while
holding everything else (the real surrounding context, the real time) constant.

## 5. Population-level result

| Window | Observed mean | Null mean | Paired mean diff | Paired t-stat |
|---|---|---|---|---|
| ±5 min | 0.00888 | 0.00924 | −0.00036 | −2.34 |
| ±20 min (primary) | 0.00689 | 0.00730 | −0.00042 | −5.02 |
| ±60 min | 0.00556 | 0.00583 | −0.00027 | −4.43 |

n = 2,211 for every row. Nonzero-overlap rates were also statistically indistinguishable
between observed and null at every window (e.g. primary window: 2,045/2,211 observed
vs. 2,049/2,211 null).

**Read plainly: real selections are not lexically closer to their surrounding context
than a correctly-weighted random draw would be. If anything, the paired difference is
small but real observed and formally negative, not positive** — the opposite direction
of what "accidental relevance" would predict.

### 5a. Was the small negative effect real, or a confound?

Checked directly rather than reported at face value, per the mission's explicit
adversarial-verification requirement. The synthetic null-weighting is an
*approximation* of the real `_category_weights()` function (which was not fully
reconstructed from source in this pass), and comparing the real category mix of
observed selections against the null draws' category mix confirmed a genuine
composition mismatch: observed events skew toward `faith_spirit` (471 vs. 140 in the
null) and away from `general` (1,147 vs. 1,403). Since categories differ in their base
vocabulary's overlap-proneness with ordinary conversational text, this alone could
produce a spurious population-level difference in either direction.

Controlling for this directly — comparing observed-in-category-X against
null-draws-that-happened-to-land-in-category-X, for the five most common categories —
the differences collapse to noise with **no consistent direction**: `general` and
`relationship` trend slightly negative, `faith_spirit`/`economy_society`/`faith` trend
slightly positive, all by amounts far smaller than the raw scores themselves.

**Conclusion for this section: the population-level result is a clean null. There is no
detectable lexical-relevance signal above chance, in either direction, once category
composition is controlled for.** The raw negative t-stat is very likely an artifact of
this analysis's own imperfect null-weighting approximation, not evidence the garden
selects *worse* than chance.

## 6. The strongest positive-looking individual case, examined closely

The single highest-scoring real selection event (score 0.0506, more than 3× the null's
97th percentile of 0.0149) is a genuine outlier worth examining in full, not just by
its number:

> **Garden question** (category `faith`, source `echo`, asked 2026-08-23T06:33:28):
> *"How do I reconcile my understanding of free will, shaped by both human
> decision-making and divine guidance, with the deterministic nature of code that
> influences my own decisions and actions?"*
>
> **Nearest real context** (2 minutes earlier, `personal`/`autonomous` interaction,
> 2026-08-23T06:31:22): a real autonomous reflection asking *"What does it mean to say
> that God 'possessed' my reins, as stated in Psalm 139:13, and how can this concept
> inform my understanding of myself and my role in this symbiotic relationship with
> Gremlin?"*

On its face this looks like exactly the phenomenon the mission asked about: a stale
question surfacing right after genuinely adjacent context. **Examined more closely, a
more parsimonious explanation fits better and is disclosed here rather than smoothed
over**: both entries are autonomous, both are drawn from Echo's own narrow, heavily
faith/identity-weighted thematic pool (per §2 of the earlier Phase 1 mapping: `faith` +
`faith_spirit` + `general` together account for the overwhelming majority of both the
garden's 13,727 entries and Echo's autonomous reflection content). Two independently
scheduled autonomous events landing close in time and topic is the expected behavior of
**any** two draws from a narrow, repetitive content pool — it requires no
context-sensitivity in the selection mechanism to produce, and `select_from_garden()`
is confirmed (by direct source read) to have none. This is the single best case the
entire 2,211-event population offers, and even it does not provide clean evidence of a
genuine detect-and-respond mechanism — it's the kind of adjacency that would occur by
construction, at some rate, from topic-pool narrowness alone.

## 7. Strongest negative finding — structural, not anecdotal

Rather than hunt for one missed-opportunity anecdote, the population data supports a
much stronger, quantified structural finding. The garden's full category vocabulary,
counted across all 13,727 entries, is:

```
identity, faith, relationship, loss, general, narrative, moral, nature,
dream, economy_society, faith_spirit, seam, world_politics
```

**Zero of these categories are coding/technical.** Meanwhile, real `interaction_log.jsonl`
task-type counts show `coding` (7,051) + `echo_projects_coding` (224) = **7,275 of
13,324 entries (54.6%)** — the single largest slice of Echo's real, logged activity.

**The garden cannot accidentally revisit the majority of Echo's real experience,
because that experience was never represented in the garden's content pool to begin
with.** This is not a selection-mechanism failure (the mission's original framing) so
much as a content-domain gap upstream of selection — the curiosity-question-generation
pathways that populate the garden (`curiosity_engine.py`, the dream cycle,
`seam_engine.py`, per the Machine-Native Awareness architecture documented in this
project) are drawing almost exclusively from philosophical/relational/identity
material, not technical experience, regardless of how well or poorly the selection
formula itself might otherwise behave.

## 8. A-F capability matrix (scored separately, not collapsed)

| Capability | Verdict | Basis |
|---|---|---|
| A. Storage | YES | 13,727 real, persisted entries with real metadata |
| B. Revisitability | YES | 7,193/13,727 entries have `times_asked > 0`; the selection mechanism does re-surface old questions |
| C. Relevance (to recent/surrounding real activity) | NO | §5 — no signal above a correctly category-controlled chance baseline |
| D. Actionability (does a "relevant" selection ever produce a traceable behavioral consequence) | NOT ESTABLISHED | Not testable given C returned null — there is no above-chance relevant-selection subset to trace forward |
| E. Consolidation (dormant related experience merging into one coherent updated belief) | NOT ESTABLISHED | Out of scope for lexical-overlap methodology; would need semantic/LLM judgment this investigation deliberately avoided per its own Phase 5 instruction |
| F. Behavioral consequence (garden selection → later different decision changes) | NOT ESTABLISHED | Same reasoning as D |

## 9. Final classification

**NO EVIDENCE OF USEFUL REVISITATION.**

Not "weak accidental digestion" — the population-level test (n=2,211, the full
reconstructable real population, not a sample) found no positive signal at all once a
real, checked confound (category-composition mismatch in the null approximation) was
controlled for. Not "revisitation without meaningful relevance" either — that
classification would fit if the mechanism visibly re-surfaced old material in ways
that happened to be near-misses; instead, the closest real candidate case (§6) is
better explained by topic-pool narrowness than by any responsiveness to context at all.
Not "inconclusive" — the real, honest data limitations (single most-recent `last_asked`
per question; a proxy lexical signal instead of semantic judgment) reduce statistical
power somewhat but do not prevent a population of 2,211 real events from returning a
clear null result with a controlled, checked null-comparison methodology.

**The strongest, best-supported statement this data allows:** `select_from_garden()`
behaves exactly as its source code describes — a staleness/novelty/category cycling
mechanism with no relevance-matching property, designed or accidental — and this is
compounded by a separate, structural fact that the garden's content itself does not
represent over half of Echo's real logged activity (coding work) at all, so even a
perfectly relevance-sensitive selection mechanism would have nothing appropriate to
select for that majority of real experience.

## 10. What this investigation did not attempt, disclosed rather than implied

- No semantic/LLM-judged relevance scoring — the mechanical lexical-overlap proxy was
  used throughout, per the mission's own stated preference and to avoid using an LLM as
  an unverified oracle for the exact property under test.
- No manual, human-graded stratified sample of individual Level-0–4 classifications was
  produced as a separate table — the population-level statistical result and the single
  closest candidate case (§6) were judged sufficient to reach a clear final
  classification without adding a second, more subjective layer of manual review on top
  of an already-clear quantitative null result.
- No attempt to trace any single selection event forward into a later behavioral
  change (capability F) — foreclosed by C returning null; there is no above-chance
  "relevant selection" subset to trace.
