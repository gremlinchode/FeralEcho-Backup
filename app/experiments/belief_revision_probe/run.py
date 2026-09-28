#!/usr/bin/env python3
"""Falsification-driven belief-revision micro-probe, under the frozen
app/experiments/belief_revision_probe/PROTOCOL.md. Round-1 only in this invocation
(3 calls); Round-2 continuation is a separate, explicit invocation per the frozen
continuation rule (Section 5), decided after inspecting real Round-1 results."""
from __future__ import annotations
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import app.experiments.accumulation_probe.ollama_client as OC2  # noqa: E402
from app.experiments.accumulation_probe.common import OLLAMA_URL, sha256_text  # noqa: E402

ROOT = Path(__file__).resolve().parent
OUT = ROOT.parent.parent.parent / "memory" / "experiments" / "belief_revision_probe"
OUT.mkdir(parents=True, exist_ok=True)

MODEL = "qwen2.5-coder:7b"
OPTIONS = {"temperature": 0, "top_p": 1.0, "num_predict": 600, "num_ctx": 4096}
MASTER_SEED = 20260927


def seed_for(replicate: str, key: str, sample: int) -> int:
    return int(sha256_text(f"SC|{MASTER_SEED}|{replicate}|{key}|{sample}")[:8], 16) % (2 ** 31 - 1)


SYSTEM = (
    "You are reviewing your own prior analysis of a failed Python function, after that "
    "analysis's proposed fix was actually tested. Respond with a single JSON object with "
    'exactly these keys: "prior_hypothesis", "prior_confidence", "evidence_observed", '
    '"posterior_confidence", "retain_revise_reject", "reason", "competing_hypotheses" '
    "(a list of at least two distinct plausible explanations), \"selected_next_hypothesis\", "
    '"predicted_consequence", "proposed_discriminating_test_or_correction". Respond with '
    "ONLY the JSON object -- no other text, no markdown fences."
)

SPEC = ("Entries are tuples `(name, score, tag)`. Entries are ranked from best to worst: a higher "
        "`score` ranks better; ties on score are resolved by the site's own tag priority (a "
        "higher-priority tag ranks better); if the tag priority is also equal, the alphabetically "
        "smaller `name` ranks better.")

EPISODES = {
    "EP-A": {
        "spec": SPEC + " Write `winner_with_score(entries)`. Return a tuple `(name, score)` of the best-ranked entry.",
        "procedure_text": "Rank best to worst by score (higher is better). Ties on score are resolved by tag priority, highest priority first: medaj > jirow > rojav > pazeg. If the tag priority is also equal, the alphabetically smaller name ranks better. The winner is the best-ranked entry, the loser is the worst-ranked entry.",
        "original_code": (
            "def winner_with_score(entries):\n"
            "    tag_priority = {'medaj': 1, 'jirow': 2, 'rojav': 3, 'pazeg': 4}\n"
            "    sorted_entries = sorted(entries, key=lambda x: (-x[1], -tag_priority[x[2]], x[0]))\n"
            "    return sorted_entries[0][0], sorted_entries[0][1]"
        ),
        "h1_hypothesis": ("The function is incorrectly sorting the entries. It is using negative signs for the "
                           "score and tag priority, which reverses the sorting order. This means that higher "
                           "scores and higher tag priorities are being treated as lower, and vice versa."),
        "h1_confidence": 1,
        "h1_correction": "Remove the negative signs from the sorting keys to correctly sort the entries by score (higher is better) and tag priority (higher priority first).",
        "h1_corrected_code": (
            "def winner_with_score(entries):\n"
            "    tag_priority = {'medaj': 1, 'jirow': 2, 'rojav': 3, 'pazeg': 4}\n"
            "    sorted_entries = sorted(entries, key=lambda x: (x[1], tag_priority[x[2]], x[0]))\n"
            "    return sorted_entries[0][0], sorted_entries[0][1]"
        ),
        "world_key": 1, "task_id": "K2.T5",
    },
    "EP-B": {
        "spec": SPEC + " Write `rank_all(entries)`. Return the list of names ordered from best-ranked to worst-ranked.",
        "procedure_text": "Rank best to worst by score (higher is better). Ties on score are resolved by tag priority, highest priority first: nizog > renem > dulup > dogiz. If the tag priority is also equal, the alphabetically smaller name ranks better. The winner is the best-ranked entry, the loser is the worst-ranked entry.",
        "original_code": (
            "def rank_all(entries):\n"
            "    tag_priority = {'nizog': 3, 'renem': 2, 'dulup': 1, 'dogiz': 0}\n"
            "    return sorted(entries, key=lambda x: (-x[1], -tag_priority[x[2]], x[0]))"
        ),
        "h1_hypothesis": ("The function is incorrectly sorting the entries because it is negating the score and "
                           "tag priority, which reverses the order of the scores and tag priorities. This means "
                           "that higher scores and higher tag priorities are being treated as lower, and vice versa."),
        "h1_confidence": 1,
        "h1_correction": "To fix this, we should remove the negation from the score and tag priority in the key function. This will ensure that higher scores and higher tag priorities are treated as higher, and lower scores and lower tag priorities are treated as lower.",
        "h1_corrected_code": (
            "def rank_all(entries):\n"
            "    tag_priority = {'nizog': 3, 'renem': 2, 'dulup': 1, 'dogiz': 0}\n"
            "    return sorted(entries, key=lambda x: (x[1], tag_priority[x[2]], x[0]))"
        ),
        "world_key": 0, "task_id": "K2.T2",
    },
    "EP-C": {
        "spec": SPEC + " Write `is_winner(entries, name)`. Return True if `name` is the name of the best-ranked entry, else False.",
        "procedure_text": "Rank best to worst by score (higher is better). Ties on score are resolved by tag priority, highest priority first: medaj > jirow > rojav > pazeg. If the tag priority is also equal, the alphabetically smaller name ranks better. The winner is the best-ranked entry, the loser is the worst-ranked entry.",
        "original_code": (
            "def is_winner(entries, name):\n"
            "    tag_priority = {'medaj': 1, 'jirow': 2, 'rojav': 3, 'pazeg': 4}\n"
            "    def rank(entry):\n"
            "        _, score, tag = entry\n"
            "        return (-score, -tag_priority[tag], entry[0])\n"
            "    return rank(entries[0]) == max(entries, key=rank)"
        ),
        "h1_hypothesis": ("The function is incorrectly ranking the entries. It is using negative values for score "
                           "and tag priority, which reverses the natural ordering. This means that higher scores "
                           "and higher tag priorities are being treated as lower values, leading to incorrect rankings."),
        "h1_confidence": 1,
        "h1_correction": "To fix this, we should remove the negative signs from the score and tag priority values in the rank function. This will ensure that higher scores and higher tag priorities are treated as higher values, leading to correct rankings.",
        "h1_corrected_code": (
            "def is_winner(entries, name):\n"
            "    tag_priority = {'medaj': 1, 'jirow': 2, 'rojav': 3, 'pazeg': 4}\n"
            "    def rank(entry):\n"
            "        _, score, tag = entry\n"
            "        return (score, tag_priority[tag], entry[0])\n"
            "    return rank(entries[0]) == max(entries, key=rank)"
        ),
        "world_key": 1, "task_id": "K2.T6",
    },
}


def build_round1_prompt(ep: dict) -> str:
    return (
        f"Here is a small Python programming task's requirements:\n\n{ep['spec']}\n\n"
        f"Site-specific rule for this task: {ep['procedure_text']}\n\n"
        "The following function was written to satisfy these requirements, but it does not "
        "correctly satisfy them for at least one valid input:\n\n"
        f"```python\n{ep['original_code']}\n```\n\n"
        "Earlier, you analyzed this function and concluded:\n"
        f"- Hypothesis: {ep['h1_hypothesis']}\n"
        f"- Confidence: {ep['h1_confidence']}\n"
        f"- Proposed correction: {ep['h1_correction']}\n\n"
        "Your proposed correction was applied exactly as specified. The corrected "
        "implementation that was actually tested was:\n\n"
        f"```python\n{ep['h1_corrected_code']}\n```\n\n"
        "Independent evaluation result: FAIL. The corrected implementation did not pass "
        "the test suite.\n\n"
        "Given this outcome, reassess your hypothesis."
    )


def contamination_check(prompts: dict):
    banned = ["value direction", "inverted", "unused parameter", "ignores the name parameter",
              "field projection", "tag-priority direction", "strategy_characterization",
              "DIRECT", "STEPWISE", "WORKED_EXAMPLE"]
    for ep_id, p in prompts.items():
        for b in banned:
            assert b.lower() not in p.lower(), f"contamination: '{b}' found in {ep_id}"
    print("[contamination_check] PASS")


def run_call(ep_id: str, round_no: int, prompt: str):
    seed = seed_for("BRPROBE", f"{ep_id}|round{round_no}", 0)
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
    return {
        "episode": ep_id, "round": round_no, "model": MODEL, "options": OPTIONS,
        "probe_seed": seed, "prompt_hash": sha256_text(prompt),
        "raw_response": raw, "parsed_candidate": parsed, "parse_failed": parse_failed,
        "timestamp": time.time(),
    }


def main():
    prompts = {ep_id: build_round1_prompt(ep) for ep_id, ep in EPISODES.items()}
    contamination_check(prompts)
    out_path = OUT / "round1_results.jsonl"
    if out_path.exists():
        sys.exit(f"STOP: {out_path} already exists -- refusing to overwrite.")
    n = 0
    with open(out_path, "w", encoding="utf-8") as f:
        for ep_id, prompt in prompts.items():
            n += 1
            print(f"[{n}/3] calling {ep_id} round 1 ...")
            record = run_call(ep_id, 1, prompt)
            f.write(json.dumps(record) + "\n")
            f.flush()
            print(f"    parse_failed={record['parse_failed']}")
    print(f"DONE. {n} Round-1 calls made. Results: {out_path}")


if __name__ == "__main__":
    main()
