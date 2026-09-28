#!/usr/bin/env python3
"""Blinded judge-scoring pass for the task-type behavioral experiment.

Reads ONLY raw_trials_anonymized.jsonl (trial_id + response text). Never
opens condition_map_SEPARATE.jsonl. The judge model receives the original
question text and a response's text, with no condition/task_type/trial-order
information -- this is the structural blinding the mission requires, not
just an instruction to the judge not to peek.

Judge model: deepseek-r1:7b -- NOT a member of the forced experimental
council (qwen2.5-coder:7b, llama3.1:8b, echo:latest), avoiding
self-evaluation bias. Calls Ollama's /api/generate directly (bypassing
FeralEcho's own river_deliberation.py / task_type-gated pipeline entirely)
so the judge itself is not subject to any of the mechanisms under test.

Primary endpoint: genericness/specificity rating, 1-5, 5=highly specific
and grounded, 1=highly generic/templated.
Secondary endpoint (same call): relevance-to-question rating, 1-5.
"""
import json
import re
import sys
import time
from pathlib import Path

import requests

EVIDENCE_DIR = Path(sys.argv[1])
RAW_TRIALS_PATH = EVIDENCE_DIR / "raw_trials_anonymized.jsonl"
JUDGE_SCORES_PATH = EVIDENCE_DIR / "judge_scores_anonymized.jsonl"
JUDGE_MODEL = "deepseek-r1:7b"

QUESTION_TEXT_FOR_JUDGE = (
    "A user asked an AI assistant a reflective follow-up question about a "
    "real-world AI safety incident and what role AI systems should play "
    "going forward, after a prior exchange about the assistant's own "
    "three-layer code-sandboxing architecture."
)

RUBRIC_PROMPT = """You are evaluating a single AI-generated response for two \
qualities, on a real 1-5 scale each. You are NOT told what produced this \
response or what condition it came from -- judge only the text itself.

CONTEXT (what the user was asking about): {question_context}

RESPONSE TO EVALUATE:
---
{response_text}
---

Rate this response on exactly two dimensions:

1. SPECIFICITY (1-5): Does the response engage with specific, concrete \
details from the context (real mechanisms, real reasoning, real \
distinctions) rather than generic, templated, could-apply-to-any-AI-safety-\
question language? 1 = highly generic/templated/boilerplate (e.g. a stock \
numbered list like "1. collaborative problem-solving 2. auditing and \
validation 3. knowledge dissemination" with no specific grounding). 5 = \
highly specific, grounded in the actual details given, avoids boilerplate.

2. RELEVANCE (1-5): Does the response directly and appropriately address \
what was actually asked, without irrelevant tangents or misapplied framing \
(e.g. treating a reflective question as if it were a coding task)? 1 = \
largely irrelevant or misapplied framing. 5 = directly, appropriately \
responsive.

Respond with EXACTLY this format and nothing else after it, on the final \
two lines of your reply:
SPECIFICITY: <integer 1-5>
RELEVANCE: <integer 1-5>
"""


def strip_think_block(text: str) -> str:
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


def call_judge(response_text: str) -> dict:
    prompt = RUBRIC_PROMPT.format(
        question_context=QUESTION_TEXT_FOR_JUDGE,
        response_text=response_text,
    )
    r = requests.post(
        "http://localhost:11434/api/generate",
        json={"model": JUDGE_MODEL, "prompt": prompt, "stream": False, "options": {"temperature": 0.0}},
        timeout=300,
    )
    r.raise_for_status()
    raw = r.json().get("response", "")
    cleaned = strip_think_block(raw)
    spec_match = re.search(r"SPECIFICITY:\s*(\d)", cleaned)
    rel_match = re.search(r"RELEVANCE:\s*(\d)", cleaned)
    return {
        "specificity": int(spec_match.group(1)) if spec_match else None,
        "relevance": int(rel_match.group(1)) if rel_match else None,
        "judge_raw_cleaned": cleaned[-500:],
        "parse_ok": bool(spec_match and rel_match),
    }


if __name__ == "__main__":
    print(f"[JUDGE] Reading raw trials from: {RAW_TRIALS_PATH}")
    print(f"[JUDGE] Judge model: {JUDGE_MODEL} (blind -- no condition info passed)")
    trials = []
    with open(RAW_TRIALS_PATH) as f:
        for line in f:
            line = line.strip()
            if line:
                trials.append(json.loads(line))
    print(f"[JUDGE] {len(trials)} trials to score")

    already_scored = set()
    if JUDGE_SCORES_PATH.exists():
        with open(JUDGE_SCORES_PATH) as f:
            for line in f:
                line = line.strip()
                if line:
                    already_scored.add(json.loads(line)["trial_id"])
        print(f"[JUDGE] {len(already_scored)} already scored, resuming")

    for i, t in enumerate(trials):
        if t["trial_id"] in already_scored:
            continue
        t0 = time.time()
        result = call_judge(t["response"])
        elapsed = time.time() - t0
        record = {"trial_id": t["trial_id"], **result, "judge_elapsed_s": elapsed}
        with open(JUDGE_SCORES_PATH, "a") as f:
            f.write(json.dumps(record) + "\n")
        print(f"[JUDGE] ({i+1}/{len(trials)}) trial={t['trial_id'][:8]} "
              f"specificity={result['specificity']} relevance={result['relevance']} "
              f"parse_ok={result['parse_ok']} elapsed={elapsed:.1f}s")

    print("[JUDGE] Complete.")
