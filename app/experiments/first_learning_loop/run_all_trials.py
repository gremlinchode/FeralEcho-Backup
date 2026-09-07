#!/usr/bin/env python3
"""Runs the full CONTROL/EXPERIENCE trial set for the First Real Learning
Loop experiment. Read-only w.r.t. production state (RiverBrain neutralized,
never calls execute_self_edit()/perform_self_edit()). Appends each trial's
full result to trial_results.jsonl as it completes, so partial progress is
never lost if this process is interrupted."""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.experiments.first_learning_loop.harness import neutralize_river_brain_writes, run_trial
from app.experiments.first_learning_loop.lesson_mining import mine_lessons, build_experience_sentence

neutralize_river_brain_writes()
lessons = mine_lessons()
SENTENCE = build_experience_sentence(lessons)
print("LESSON SENTENCE:", SENTENCE, flush=True)

# Real, fresh self-edit-style prompts -- none drawn from the pre-cutoff
# historical corpus mined above; these are new prompts constructed tonight,
# so no chronological overlap with the lesson corpus is possible.
PROMPTS = [
    "Autonomous self-edit targeting coding task performance. Modify app/core/self_edit_generated.py only. "
    "Output must be headless Python with no interactive elements. Focus: write a small decorator function "
    "that logs when the wrapped function is called, and apply it to a simple example function.",

    "Autonomous self-edit targeting coding task performance. Modify app/core/self_edit_generated.py only. "
    "Output must be headless Python with no interactive elements. Focus: write a helper class that tracks "
    "how many times each of its methods has been called, using a shared counting utility.",

    "Autonomous self-edit targeting coding task performance. Modify app/core/self_edit_generated.py only. "
    "Output must be headless Python with no interactive elements. Focus: write a function that generates "
    "and returns code, then applies a post-processing step to the generated code before returning it.",
]

results = []
for i, prompt in enumerate(PROMPTS):
    for condition in ("control", "experience"):
        print(f"\n[{i+1}/{len(PROMPTS)}] condition={condition} starting...", flush=True)
        t0 = time.time()
        try:
            r = run_trial(prompt, condition, lesson_sentence=SENTENCE)
            print(f"  done in {round(time.time()-t0,1)}s | passed={r['passed']} | "
                  f"failure_class={r['failure_class']} | error={(r['error'] or '')[:150]!r}", flush=True)
            results.append(r)
        except Exception as e:
            print(f"  [ERROR] trial failed: {e}", flush=True)

print(f"\nDone. {len(results)} trials completed.")
