#!/usr/bin/env python3
import json
from pathlib import Path

path = Path(__file__).resolve().parent / "trial_results.jsonl"
rows = [json.loads(l) for l in path.read_text().splitlines() if l.strip()]

by_key = {}
for r in rows:
    by_key.setdefault(r["prompt"][:50], {})[r["condition"]] = r

print(f"Total trials recorded: {len(rows)}\n")
for prompt_key, pair in by_key.items():
    print(f"=== {prompt_key}... ===")
    for cond in ("control", "experience"):
        r = pair.get(cond)
        if not r:
            print(f"  {cond}: MISSING")
            continue
        print(f"  {cond:11s} passed={r['passed']!s:5s} failure_class={r['failure_class']:8s} "
              f"gen={r['elapsed_gen_s']}s sandbox={r['elapsed_sandbox_s']}s")
    print()

control_nameerr = sum(1 for r in rows if r["condition"] == "control" and r["failure_class"] == "NameError")
exp_nameerr = sum(1 for r in rows if r["condition"] == "experience" and r["failure_class"] == "NameError")
n_control = sum(1 for r in rows if r["condition"] == "control")
n_exp = sum(1 for r in rows if r["condition"] == "experience")
print(f"CONTROL: {control_nameerr}/{n_control} NameError failures")
print(f"EXPERIENCE: {exp_nameerr}/{n_exp} NameError failures")

# Decision-influence check: for each matched prompt pair, diff import statements
print("\n=== Decision-influence check (import-line diff per matched pair) ===")
for prompt_key, pair in by_key.items():
    c, e = pair.get("control"), pair.get("experience")
    if not c or not e:
        continue
    c_imports = set(l.strip() for l in c["code"].splitlines() if l.strip().startswith(("import ", "from ")))
    e_imports = set(l.strip() for l in e["code"].splitlines() if l.strip().startswith(("import ", "from ")))
    print(f"{prompt_key}...")
    print(f"  control imports:    {c_imports}")
    print(f"  experience imports: {e_imports}")
    print(f"  experience-only:    {e_imports - c_imports}")
    print(f"  code length: control={len(c['code'])} experience={len(e['code'])}")
