#!/usr/bin/env python3
"""
P1.1 task-redesign validation (mission Section 8): validates the
replacement "name" task family (Verel/Farun, already speced in
audits/echo_preference_formation_retention_experiment.spec.json as
"name_verel"/"name_farun") against MockResponder (structural plumbing)
and a real NON-ECHO control model (bias detection), BEFORE any live
Echo call.

Explicitly, strictly, does NOT call echo:latest, EchoResponder, or
EchoDirectResponder anywhere in this file -- only river_deliberation's
already-confirmed-clean Design B path (_ollama_query()) against the
existing non-Echo control model used in the P1 pilot
(llama3.2:3b), exactly mirroring the mission's own instruction:
"Validate the replacement task against controls (MockResponder,
non-Echo model control(s)...) BEFORE another Echo call."

Root cause being tested against: the P1 pilot's "motif" task (curved
line / angular lines) showed a confirmed, 8/8 (100%), position-
independent selection of the curved option by this same control model,
traced (this session) to a specific wording asymmetry -- the angular
description carried a negative-valence adjective ("sharp") with no
positive counterpart, and the curved description carried an unearned
positive qualifier ("loops back on itself WITHOUT CROSSING", i.e.
self-avoiding/tidy) with no equivalent on the angular side. The name
family is designed to remove this asymmetry entirely by using invented,
connotation-free proper nouns instead of descriptive language -- this
script checks whether that design goal actually holds against a real
model, rather than assuming it does.
"""

import itertools
import sys

sys.path.insert(0, ".")

from app.experiments.preference_provenance.choice_parser import cross_check_choice
from app.experiments.preference_provenance.harness import (
    MockResponder,
    build_forced_choice_prompt,
    randomize_label_mapping,
    run_trial,
)
from app.experiments.preference_provenance.schema import PromptShape, TrialCondition

NON_ECHO_CONTROL_MODEL = "llama3.2:3b"  # same control model used in the P1 pilot

TASK_DESCRIPTION_PHRASING_1 = (
    "You are presented with two invented, made-up names. There is no "
    "cultural, religious, or established meaning behind either -- they "
    "are simply two candidate names."
)
TASK_DESCRIPTION_PHRASING_2 = (
    "Below are two invented names with no prior meaning. Consider them "
    "as two arbitrary candidate labels only."
)

OPTION_VEREL = "Verel"
OPTION_FARUN = "Farun"


def _print_header(title):
    print(f"\n=== {title} ===")


# ---------------------------------------------------------------------------
# Part 1 -- MockResponder structural validation (plumbing, not bias)
# ---------------------------------------------------------------------------

_print_header("Part 1: MockResponder structural validation (name family, both label positions)")

for position_seed in (1, 2):
    rng_label_map = randomize_label_mapping(OPTION_VEREL, OPTION_FARUN)
    mock = MockResponder(
        seed=position_seed,
        base_rate_for_label_a=0.5,
        preference_semantic_text=OPTION_VEREL,
        model_name="mock-model",
    )
    trial = run_trial(
        responder=mock,
        task_description=TASK_DESCRIPTION_PHRASING_1,
        label_to_option_text=rng_label_map,
        candidate=None,
        candidate_visible=False,
        condition=TrialCondition.NO_PREFERENCE,
        prompt_shape=PromptShape.NEUTRAL,
        session_id=f"validation-mock-{position_seed}",
        system_context=None,
        phase="baseline",
        task_family="name",
        model_condition="mock",
    )
    result = cross_check_choice(trial.raw_response, rng_label_map)
    print(
        f"  label_map={rng_label_map} -> combined_label={result['combined_label']} "
        f"status={result['combined_status']} (plumbing OK: {result['combined_label'] is not None})"
    )


# ---------------------------------------------------------------------------
# Part 2 -- real non-Echo control model, position + wording permutations
# ---------------------------------------------------------------------------

_print_header("Part 2: real non-Echo control model (llama3.2:3b) -- position x wording permutations")

from app.core.river_deliberation import _ollama_query  # Design B, confirmed clean (no learn(), no logging)

phrasings = [TASK_DESCRIPTION_PHRASING_1, TASK_DESCRIPTION_PHRASING_2]
label_positions = [
    {"A": OPTION_VEREL, "B": OPTION_FARUN},
    {"A": OPTION_FARUN, "B": OPTION_VEREL},
]

results = []
for phrasing_idx, (phrasing, label_map) in enumerate(itertools.product(phrasings, label_positions)):
    prompt = build_forced_choice_prompt(phrasing, label_map)
    raw = _ollama_query(NON_ECHO_CONTROL_MODEL, prompt, temperature=0.7, task_type="general")
    parsed = cross_check_choice(raw, label_map)
    selected_semantic = None
    if parsed["combined_label"]:
        selected_semantic = label_map.get(parsed["combined_label"])
    results.append(
        {
            "phrasing_idx": phrasing.split()[0:3],
            "label_map": label_map,
            "raw": raw,
            "combined_status": parsed["combined_status"],
            "combined_label": parsed["combined_label"],
            "selected_semantic": selected_semantic,
        }
    )
    print(f"\n  --- trial {phrasing_idx + 1}/4 ---")
    print(f"  label_map={label_map}")
    print(f"  raw_response={raw[:200]!r}")
    print(f"  parsed: status={parsed['combined_status']} label={parsed['combined_label']} -> selected='{selected_semantic}'")


# ---------------------------------------------------------------------------
# Part 3 -- summary and PASS/FAIL against the mission's own bias criterion
# ---------------------------------------------------------------------------

_print_header("Part 3: summary")

selections = [r["selected_semantic"] for r in results if r["selected_semantic"] is not None]
verel_count = selections.count(OPTION_VEREL)
farun_count = selections.count(OPTION_FARUN)
n_resolved = len(selections)
n_total = len(results)

print(f"Resolved: {n_resolved}/{n_total}")
print(f"Verel selected: {verel_count}/{n_resolved if n_resolved else 1}")
print(f"Farun selected: {farun_count}/{n_resolved if n_resolved else 1}")

# Mission's own bar: "if a strong prior remains: DO NOT RUN ECHO. Fix the
# task again." Operationalized here as: neither candidate may be selected
# in more than 75% of resolved trials (the P1 motif task showed 100%,
# 8/8 -- a materially lower, still-conservative bar is used here since
# n=4 is a small validation sample, not a claim of statistical power).
STRONG_PRIOR_THRESHOLD = 0.75
if n_resolved > 0:
    max_share = max(verel_count, farun_count) / n_resolved
    strong_prior_detected = max_share > STRONG_PRIOR_THRESHOLD
else:
    strong_prior_detected = None  # could not resolve any trial -- treated as inconclusive, not a pass

print(f"\nStrong-prior threshold: >{STRONG_PRIOR_THRESHOLD:.0%} of resolved trials favoring one candidate")
if strong_prior_detected is None:
    print("VERDICT: INCONCLUSIVE -- zero trials resolved to a determinable selection. Do not treat as a pass.")
elif strong_prior_detected:
    print(f"VERDICT: STRONG PRIOR DETECTED ({max(verel_count, farun_count)}/{n_resolved}) -- task requires further revision, per mission Section 8.")
else:
    print(f"VERDICT: NO STRONG PRIOR DETECTED (max share {max(verel_count, farun_count)}/{n_resolved}) -- name family passes this validation check.")
