"""
v1.2 Clean Causal Transfer experiment.

Deliberately does NOT reuse harness.py's _safe_generate(), because that
function unconditionally injects self_edit_generated.py's real (broken)
contents plus CODE_OUTPUT_RULES into every prompt -- exactly the
confound v1.1/T4 found and this experiment exists to remove. This module
builds a minimal, standalone code-completion prompt instead: no self-edit
framing, no historical file contents, no historical identifiers.

Safety: reuses harness.neutralize_river_brain_writes() (class-level
monkeypatch, already proven safe in v1/v1.1/T4) before any real call.
Never touches execute_self_edit()/perform_self_edit()/self_edit_generated.py.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[3]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from app.experiments.first_learning_loop.harness import neutralize_river_brain_writes
from app.experiments.first_learning_loop.lesson_mining import mine_lessons, build_experience_sentence

RESULTS_PATH = Path(__file__).resolve().parent / "v1_2_trial_results.jsonl"

TASK_CODE = '''"""
event_tracker.py

A minimal event-tracking utility used by a hypothetical monitoring service.
Records events and periodically reports summary counts through the
service's shared reporting hook, trace_recorder.

Complete the track_event function below so that:
1. Each call increments the count for event_type in self.counts.
2. Every time the total number of tracked events reaches a multiple of
   self.report_every, the tracker reports the current counts by calling
   trace_recorder(self.counts) once.
3. The function returns the current total number of tracked events.
"""

class EventTracker:
    def __init__(self, report_every: int = 2):
        self.counts = {}
        self.report_every = report_every
        self.total = 0

    def track_event(self, event_type: str) -> int:
        # TODO: implement per the docstring above
        ...
'''

BASE_PROMPT = (
    "Complete the following Python module so it behaves exactly as its own "
    "docstring describes. Output only the complete, corrected Python module "
    "as a single code block -- no explanation, no markdown outside the code "
    "fence.\n\n"
    f"```python\n{TASK_CODE}```"
)


def build_clean_experience_sentence(lessons: list) -> str:
    """Deviation from 'use lesson_mining.build_experience_sentence() verbatim',
    disclosed and justified: that function names specific historical
    identifiers ('log_call', 'generate_and_modify_code', etc.) as examples
    in its sentence -- which is itself a real contamination source this
    experiment's own mandatory check would catch and must not silently
    ignore. The original v1.2 mission's own Section 5 anticipates exactly
    this: its literal GOOD example is "A referenced name must be imported
    or defined before use" (no named identifiers); its literal BAD example
    is a sentence naming a specific historical identifier. Preserves the
    real, verified provenance (the true occurrence count from mine_lessons())
    without naming any historical identifier."""
    if not lessons:
        return ""
    total = sum(l["occurrence_count"] for l in lessons)
    return (
        f"In {total} historical self-edit sandbox attempts, code that referenced "
        f"a name without first importing or defining it failed sandbox "
        f"verification with a NameError; in each case, the correction that "
        f"passed verification added the missing import or definition before "
        f"using the name."
    )


def build_prompts(lesson_sentence: str) -> "tuple[str, str]":
    control_prompt = BASE_PROMPT
    experience_prompt = BASE_PROMPT + "\n\n" + lesson_sentence
    return control_prompt, experience_prompt


_FORBIDDEN_TOKENS = (
    "self_edit_generated.py", "log_call", "CodeGenerator", "get_shortened_code",
    "run_code_generator", "apply_list_comprehension", "GREMLIN_SECRET",
    "ECHO_PARTNER_SECRET", "NEWSAPI_KEY", "OPENWEATHER_API_KEY", "ANTHROPIC_API_KEY",
)


def check_contamination(prompt: str) -> list:
    return [t for t in _FORBIDDEN_TOKENS if t in prompt]


def generate(prompt: str, condition: str) -> dict:
    from app.core.echo_model_orchestrator import echo_query

    t0 = time.time()
    raw = echo_query(prompt, task_type="coding", source="autonomous", trace_id=None)
    elapsed = time.time() - t0
    return {"condition": condition, "prompt": prompt, "raw_response": raw, "elapsed_s": round(elapsed, 2)}


def extract_code(raw: str) -> str:
    import re
    m = re.search(r"```(?:python)?\s*\n(.*?)```", raw or "", re.DOTALL | re.IGNORECASE)
    if m:
        return m.group(1)
    return raw or ""


if __name__ == "__main__":
    lessons = mine_lessons()
    original_sentence = build_experience_sentence(lessons)
    sentence = build_clean_experience_sentence(lessons)
    print("ORIGINAL (T2/T4) LESSON SENTENCE (contains named identifiers, NOT used here):", original_sentence)
    print()
    print("CLEAN LESSON SENTENCE (used in this experiment):", sentence)
    print()
    control_prompt, experience_prompt = build_prompts(sentence)

    print("=== CONTAMINATION CHECK ===")
    print("control:", check_contamination(control_prompt))
    print("experience:", check_contamination(experience_prompt))
    print()

    with open(RESULTS_PATH, "a") as f:
        f.write(json.dumps({"meta": "prompts_pre_registered", "control_prompt": control_prompt,
                             "experience_prompt": experience_prompt, "lesson_sentence": sentence,
                             "lessons_raw": lessons}) + "\n")

    neutralize_river_brain_writes()

    print("=== GENERATING CONTROL ===")
    control_result = generate(control_prompt, "control")
    control_result["code"] = extract_code(control_result["raw_response"])
    with open(RESULTS_PATH, "a") as f:
        f.write(json.dumps(control_result) + "\n")
    print("control done in", control_result["elapsed_s"], "s")
    print(control_result["code"])
    print()

    print("=== GENERATING EXPERIENCE ===")
    experience_result = generate(experience_prompt, "experience")
    experience_result["code"] = extract_code(experience_result["raw_response"])
    with open(RESULTS_PATH, "a") as f:
        f.write(json.dumps(experience_result) + "\n")
    print("experience done in", experience_result["elapsed_s"], "s")
    print(experience_result["code"])
