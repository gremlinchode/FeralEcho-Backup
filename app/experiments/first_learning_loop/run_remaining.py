#!/usr/bin/env python3
import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from app.experiments.first_learning_loop.harness import neutralize_river_brain_writes, run_trial
from app.experiments.first_learning_loop.lesson_mining import mine_lessons, build_experience_sentence

neutralize_river_brain_writes()
SENTENCE = build_experience_sentence(mine_lessons())
print("LESSON SENTENCE:", SENTENCE, flush=True)

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

TASKS = [(0, "experience"), (1, "control"), (1, "experience"), (2, "control"), (2, "experience")]

for idx, condition in TASKS:
    prompt = PROMPTS[idx]
    print(f"\n[prompt {idx+1}] condition={condition} starting...", flush=True)
    t0 = time.time()
    try:
        r = run_trial(prompt, condition, lesson_sentence=SENTENCE)
        print(f"  done in {round(time.time()-t0,1)}s | passed={r['passed']} | "
              f"failure_class={r['failure_class']} | error={(r['error'] or '')[:150]!r}", flush=True)
    except Exception as e:
        print(f"  [ERROR]: {e}", flush=True)

print("\nAll remaining trials done.", flush=True)
