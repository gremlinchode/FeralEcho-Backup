#!/usr/bin/env python3
"""Split the 84 verified tier4_task_pool.py tasks into two disjoint,
category-balanced 42-task confirmatory suites (Stage 1 / Stage 2), write
them in the same schema as audits/tier3_apparatus/held_out_task_suite.json
(task_id, tier, category, prompt, test_code -- NO reference_solution, NO
answer key of any kind), and hash both. Deterministic split (alternating
by within-category declaration order), not randomized -- there is no
outcome yet to influence, so a fixed, auditable split is preferable to
adding an unnecessary random-seed dependency.
"""
import hashlib
import json
import os
import sys

sys.path.insert(0, "scripts")
from tier4_task_pool import TASKS  # noqa: E402

OUT_DIR = "audits/tier4_apparatus"
os.makedirs(OUT_DIR, exist_ok=True)

by_category = {}
for t in TASKS:
    by_category.setdefault(t["category"], []).append(t)

stage1_tasks = []
stage2_tasks = []
for category, tasks in by_category.items():
    assert len(tasks) == 14, f"expected 14 tasks in {category}, got {len(tasks)}"
    # Alternate: even declaration-order index -> stage 1, odd -> stage 2.
    # 14 tasks per category -> exactly 7/7.
    for i, t in enumerate(tasks):
        target = stage1_tasks if i % 2 == 0 else stage2_tasks
        target.append({
            "task_id": t["task_id"],
            "tier": 3,
            "category": t["category"],
            "prompt": t["prompt"],
            "test_code": t["test_code"],
        })

assert len(stage1_tasks) == 42, len(stage1_tasks)
assert len(stage2_tasks) == 42, len(stage2_tasks)
assert not (set(t["task_id"] for t in stage1_tasks) & set(t["task_id"] for t in stage2_tasks)), \
    "Stage 1 and Stage 2 must be fully disjoint"

for stage_num, stage_tasks in [(1, stage1_tasks), (2, stage2_tasks)]:
    suite = {"tasks": stage_tasks}
    raw = json.dumps(suite, indent=2, sort_keys=False).encode("utf-8")
    path = f"{OUT_DIR}/tier4_stage{stage_num}_task_suite.json"
    with open(path, "wb") as f:
        f.write(raw)
    digest = hashlib.sha256(raw).hexdigest()
    hash_path = f"{OUT_DIR}/tier4_stage{stage_num}_task_suite.hash.txt"
    with open(hash_path, "w") as f:
        f.write(f"sha256: {digest}\nfile: {path}\nn_tasks: {len(stage_tasks)}\n"
                 f"frozen_at: 2026-09-04 (before any confirmatory generation call)\n")
    print(f"Stage {stage_num}: {len(stage_tasks)} tasks written to {path}")
    print(f"  sha256 = {digest}")
    from collections import Counter
    print(f"  category counts: {dict(Counter(t['category'] for t in stage_tasks))}")

print("\nDone. Both suites written and hashed.")
