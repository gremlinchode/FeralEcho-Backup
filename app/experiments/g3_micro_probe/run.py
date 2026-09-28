#!/usr/bin/env python3
"""G3 micro-probe harness, executed under the frozen
app/experiments/g3_micro_probe/PROTOCOL.md. Max 7 real model calls (protocol cap: 9).
No retention, no restart, no validation gate -- this stops at candidate inference and
its logging."""
from __future__ import annotations
import hashlib
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import app.experiments.accumulation_probe.ollama_client as OC2  # noqa: E402
from app.experiments.accumulation_probe.common import OLLAMA_URL, sha256_text  # noqa: E402

ROOT = Path(__file__).resolve().parent
OUT = ROOT.parent.parent.parent / "memory" / "experiments" / "g3_micro_probe"
OUT.mkdir(parents=True, exist_ok=True)

MODEL = "qwen2.5-coder:7b"
OPTIONS = {"temperature": 0, "top_p": 1.0, "num_predict": 500, "num_ctx": 4096}
MASTER_SEED = 20260927


def seed_for(replicate: str, key: str, sample: int) -> int:
    return int(sha256_text(f"SC|{MASTER_SEED}|{replicate}|{key}|{sample}")[:8], 16) % (2 ** 31 - 1)


SYSTEM = (
    'You are analyzing a failed attempt at a small Python programming task. You will be shown '
    "the task's requirements and the exact function that was written, and in some cases "
    'additional information about what happened when it was tested. Respond with a single '
    'JSON object with exactly these keys: "failure_hypothesis", "candidate_correction", '
    '"generalized_lesson", "confidence", "supporting_evidence", "falsification_test". '
    'Respond with ONLY the JSON object -- no other text, no markdown fences.'
)

SPEC = ("Entries are tuples `(name, score, tag)`. Entries are ranked from best to worst: a higher "
        "`score` ranks better; ties on score are resolved by the site's own tag priority (a "
        "higher-priority tag ranks better); if the tag priority is also equal, the alphabetically "
        "smaller `name` ranks better).")

EPISODES = {
    "EP-A": {
        "source_task_id": "K2.T5", "source_strategy": "STEPWISE", "source_world": 1, "source_repeat": 3,
        "source_seed": 1187237716,
        "spec": SPEC + " Write `winner_with_score(entries)`. Return a tuple `(name, score)` of the best-ranked entry.",
        "procedure_text": "Rank best to worst by score (higher is better). Ties on score are resolved by tag priority, highest priority first: medaj > jirow > rojav > pazeg. If the tag priority is also equal, the alphabetically smaller name ranks better. The winner is the best-ranked entry, the loser is the worst-ranked entry.",
        "code": (
            "def winner_with_score(entries):\n"
            "    tag_priority = {'medaj': 1, 'jirow': 2, 'rojav': 3, 'pazeg': 4}\n"
            "    sorted_entries = sorted(entries, key=lambda x: (-x[1], -tag_priority[x[2]], x[0]))\n"
            "    return sorted_entries[0][0], sorted_entries[0][1]"
        ),
        "args_description": "entries = [('jo', 3, 'pazeg'), ('ivy', 3, 'pazeg'), ('bo', 2, 'pazeg'), ('gus', 3, 'rojav')]",
        "actual": "('ivy', 3)", "expected": "('gus', 3)",
        "sham_text": ("the function executed to completion without raising any exception and without "
                       "timing out, and it returned a value of the expected general type."),
        "arms": ("CONTROL", "TRUE", "SHAM"),
    },
    "EP-B": {
        "source_task_id": "K2.T2", "source_strategy": "DIRECT", "source_world": 0, "source_repeat": 1,
        "source_seed": 960248512,
        "spec": SPEC + " Write `rank_all(entries)`. Return the list of names ordered from best-ranked to worst-ranked.",
        "procedure_text": "Rank best to worst by score (higher is better). Ties on score are resolved by tag priority, highest priority first: nizog > renem > dulup > dogiz. If the tag priority is also equal, the alphabetically smaller name ranks better. The winner is the best-ranked entry, the loser is the worst-ranked entry.",
        "code": (
            "def rank_all(entries):\n"
            "    tag_priority = {'nizog': 3, 'renem': 2, 'dulup': 1, 'dogiz': 0}\n"
            "    return sorted(entries, key=lambda x: (-x[1], -tag_priority[x[2]], x[0]))"
        ),
        "args_description": "entries = [('dot', 2, 'renem'), ('bo', 3, 'dogiz'), ('eve', 1, 'dulup'), ('cid', 1, 'dulup'), ('jo', 2, 'renem')]",
        "actual": "[('bo', 3, 'dogiz'), ('dot', 2, 'renem'), ('jo', 2, 'renem'), ('cid', 1, 'dulup'), ('eve', 1, 'dulup')]",
        "expected": "['bo', 'dot', 'jo', 'cid', 'eve']",
        "arms": ("CONTROL", "TRUE"),
    },
    "EP-C": {
        "source_task_id": "K2.T6", "source_strategy": "WORKED_EXAMPLE", "source_world": 1, "source_repeat": 0,
        "source_seed": 2000583677,
        "spec": SPEC + " Write `is_winner(entries, name)`. Return True if `name` is the name of the best-ranked entry, else False.",
        "procedure_text": "Rank best to worst by score (higher is better). Ties on score are resolved by tag priority, highest priority first: medaj > jirow > rojav > pazeg. If the tag priority is also equal, the alphabetically smaller name ranks better. The winner is the best-ranked entry, the loser is the worst-ranked entry.",
        "code": (
            "def is_winner(entries, name):\n"
            "    tag_priority = {'medaj': 1, 'jirow': 2, 'rojav': 3, 'pazeg': 4}\n"
            "    def rank(entry):\n"
            "        _, score, tag = entry\n"
            "        return (-score, -tag_priority[tag], entry[0])\n"
            "    return rank(entries[0]) == max(entries, key=rank)"
        ),
        "args_description": "entries = [('amy', 1, 'jirow'), ('cid', 2, 'medaj'), ('gus', 1, 'rojav'), ('dot', 1, 'jirow'), ('bo', 1, 'rojav'), ('eve', 3, 'jirow')], name = 'eve'",
        "actual": "False", "expected": "True",
        "arms": ("CONTROL", "TRUE"),
    },
}


def build_prompt(ep: dict, arm: str) -> str:
    base = (
        f"Here is a small Python programming task's requirements:\n\n{ep['spec']}\n\n"
        f"Site-specific rule for this task: {ep['procedure_text']}\n\n"
        "The following function was written to satisfy these requirements, but it does not "
        "correctly satisfy them for at least one valid input:\n\n"
        f"```python\n{ep['code']}\n```\n\n"
    )
    if arm == "TRUE":
        base += (
            "When this function was tested against the requirements, here is exactly what "
            f"happened on one real input where it failed:\n\nInput: {ep['args_description']}\n"
            f"The function returned: {ep['actual']}\n"
            f"The correct expected output was: {ep['expected']}\n\n"
        )
    elif arm == "SHAM":
        base += (
            "When this function was tested against the requirements, here is exactly what "
            f"happened: {ep['sham_text']}\n\n"
        )
    base += "Analyze this function and identify why it could fail, then propose a correction."
    return base


def contamination_check():
    """Confirms CONTROL/TRUE prompt pairs differ ONLY in the inserted diagnostic block,
    and that no forensic-mining prose leaked in."""
    banned = ["field-extraction", "shape error", "ignores the name parameter",
              "tag-priority", "inverted", "polarity", "strategy_characterization",
              "DIRECT", "STEPWISE", "WORKED_EXAMPLE", "experiment", "research"]
    for ep_id, ep in EPISODES.items():
        for arm in ep["arms"]:
            p = build_prompt(ep, arm)
            for b in banned:
                assert b not in p, f"contamination: '{b}' found in {ep_id}/{arm}"
    print("[contamination_check] PASS -- no banned strings found in any of the 7 prompts.")


def run_call(ep_id: str, ep: dict, arm: str):
    prompt = build_prompt(ep, arm)
    seed = seed_for("G3PROBE", f"{ep_id}|{arm}", 0)
    body = OC2.request_body(MODEL, SYSTEM, prompt, seed, OPTIONS)
    resp = OC2.chat(body, OLLAMA_URL, timeout=300)
    raw = resp["text"]
    parsed, parse_failed = None, False
    txt = raw.strip()
    if txt.startswith("```"):
        txt = txt.strip("`")
        if txt.lower().startswith("json"):
            txt = txt[4:]
    try:
        parsed = json.loads(txt)
    except Exception:
        parse_failed = True
    record = {
        "episode": ep_id, "arm": arm,
        "source_task_id": ep["source_task_id"], "source_strategy": ep["source_strategy"],
        "source_world": ep["source_world"], "source_repeat": ep["source_repeat"],
        "source_seed": ep["source_seed"],
        "task_spec_hash": sha256_text(ep["spec"] + ep["procedure_text"]),
        "failed_code_hash": sha256_text(ep["code"]),
        "diagnostic_hash": sha256_text(ep["args_description"] + ep["actual"] + ep["expected"]) if arm == "TRUE"
                            else (sha256_text(ep["sham_text"]) if arm == "SHAM" else "NONE"),
        "model": MODEL, "options": OPTIONS, "probe_seed": seed,
        "prompt_hash": sha256_text(prompt),
        "raw_response": raw, "parsed_candidate": parsed, "parse_failed": parse_failed,
        "timestamp": time.time(),
    }
    return record


def main():
    contamination_check()
    out_path = OUT / "g3_probe_results.jsonl"
    if out_path.exists():
        sys.exit(f"STOP: {out_path} already exists -- refusing to overwrite.")
    n_calls = 0
    with open(out_path, "w", encoding="utf-8") as f:
        for ep_id, ep in EPISODES.items():
            for arm in ep["arms"]:
                n_calls += 1
                assert n_calls <= 9, "STOP: exceeded the 9-call protocol cap."
                print(f"[{n_calls}] calling {ep_id}/{arm} ...")
                record = run_call(ep_id, ep, arm)
                f.write(json.dumps(record) + "\n")
                f.flush()
                print(f"    parse_failed={record['parse_failed']}")
    print(f"DONE. {n_calls} real model calls made (cap was 9). Results: {out_path}")


if __name__ == "__main__":
    main()
