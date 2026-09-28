# Provenance Record: K2 Strategy-Characterization Protocol

This is the immutable provenance trail for the strategy-characterization protocol,
covering its original freeze, the adversarial review that found material defects in it,
and the corrected version now designated controlling. Per explicit instruction, this
record exists so the corrected document never obscures that the original was frozen,
found defective, and corrected — not silently rewritten.

**No experimental outcomes of any kind had been collected under any version of this
protocol before or during these corrections.** No model call, no code execution, no data
collection occurred at any point in the design/review/correction sequence below. This is
confirmed directly, not assumed: Phase 0 (the seed-determinism smoke test) is the first
authorized model call under this protocol, and it has not yet run as of this record.

---

## Chain of custody

| Step | Artifact | SHA-256 | Status |
|---|---|---|---|
| 1 | Original frozen protocol content (as first written, before any review) | `6d16142e1cbc31f9f7388d21c6a8f9ab96afb6d7c2a2424520a5f819e478aa2d` | **SUPERSEDED — NEVER EXECUTED.** Full text preserved verbatim, unmodified, at `audits/2026-09-27_strategy_characterization_protocol_design_v1_SUPERSEDED.md` (hash of that archive file, including its archival header, is `29a08187406f2a657ba29e5b8e60cdbd5c548bc00145c2d7a7e27e6951747427`; the hash above is of the original document text alone, starting at its own title line, to make it independently reproducible from the original file this preserves). |
| 2 | Adversarial pseudoreplication/power review of step 1 | `2f3bcf4d5fc03ca9bca98ebc2969891a8b09e0e8e5e174b12dfb90251cd3be18` | Filed at `audits/2026-09-27_strategy_characterization_protocol_adversarial_review.md`. Found two material defects (below). No model calls made during this review — read-only source inspection and exact combinatorial arithmetic only. |
| 3 | Corrected protocol, with the review's fixes applied in place | `9d6d26a09d709eb05d0d399bcf7adb666cd96a720b7d41bfd76913649e52053c` | **CONTROLLING FROZEN PROTOCOL.** Lives at `audits/2026-09-27_strategy_characterization_protocol_design.md`. This is the version Phase 0 and Stage 1 execute under. |

Any future edit to the controlling protocol (step 3) must itself be treated as a new,
dated, hashed revision in this same table — the controlling document is not to be
silently edited again without extending this record.

---

## Exact corrections made (step 1 → step 3), for the record

1. **Pseudoreplication in Q1.** Original design treated 18 (task, world) cells as fully
   independent blocks for the Friedman/Wilcoxon analysis. Corrected: task-template (n=6)
   is the properly independent unit (worlds are within-template replicates, not fresh
   templates); the template-level Friedman omnibus is now the primary, load-bearing Q1
   test. Established as a hard fact, not an estimate: at n=6, no pairwise Wilcoxon
   comparison can reach the pre-registered Bonferroni-corrected threshold (α=0.0167) at
   any effect size (exact minimum achievable p=0.03125 > 0.0167, even for a perfect
   unanimous 6/6 result) — pairwise tests are demoted to exploratory status at both n=6
   and the retained, explicitly-flagged anti-conservative pooled n=18 level.
2. **Q2 dimension eligibility.** `operation` (exactly 1 task per level, 6 levels) and
   `arg_count` (5-vs-1 split) reclassified from "underpowered" to **structurally
   untestable** — n=1 per level admits no within-level comparison at all, so any
   apparent effect is perfectly confounded with individual-task identity. `return_type`
   (2-vs-2-vs-1-vs-1) retained as the sole eligible Q2 dimension; the S-holdout's
   matching 2-vs-2 thinness is now disclosed as a ceiling on what any confirmed Outcome C
   could mean from this exact task registry.
3. **Section 8 power claim corrected** to state the n=6 significance ceiling as a fact,
   not a power estimate, and to re-scope the original "~30–40pp, n=18" claim as
   describing only the secondary/exploratory pooled analysis.
4. **Section 9 Stage-2 gate operationalized**: an explicit, itemized, timestamp-required
   freeze record (dimension value, predicted winner, comparator, exact one-sided test,
   exact α/threshold) added as a hard precondition for any Stage 2 generation.
5. **Section 10/14 interpretation matrix tightened**: Outcome C's claimed strength
   downgraded to "a candidate signal warranting further work," matching Q2's real
   evidentiary ceiling; one explicit sentence added guarding against a lone significant
   Q1 result being reported as evidence for adaptive routing.
6. **Minor, cost-free additions**: Q3 flip-rate now reported per-strategy as well as
   pooled; Q4's split-sample oracle-ceiling correction now explicitly flagged as noisy in
   its own selection step and reported at both analysis units.

**None of these changes touched data-collection mechanics** — the 216-generation budget,
task registry, strategy definitions, model, temperature, repeat count, world count,
grading pipeline, seed namespace, and randomization/counterbalancing scheme are
byte-for-byte identical between the superseded and controlling versions. Every correction
is to the analysis and interpretation plan.

---

## Authorization status

Per Gremlin's explicit instruction: **Stage 1 only is authorized**, executed under the
controlling protocol (step 3 above), gated on Phase 0 passing first. Stage 2 requires
separate authorization regardless of Stage 1's outcome. No production code, no
persistent-routing experiment file, and no Echo behavior is touched by any part of this
authorization.
