#!/usr/bin/env python3
from pathlib import Path
import json, math

src = Path("feral_echo_report_index.json")
out = Path("feral_echo_symbolic_map.json")

def classify(p):
    n = p.lower()
    if "model" in n: return "model⚗️"
    if "memory" in n or "journal" in n: return "memory🧠"
    if "loop" in n or "core" in n: return "core🌀"
    if "guardian" in n or "dmn" in n: return "guardian🛡️"
    if "server" in n or "api" in n: return "comms🔗"
    if "log" in n or "wire" in n: return "log⚡"
    return "misc📁"

def human_size(z):
    if z == 0: return "0B"
    units = ['B','KB','MB','GB','TB']
    power = int(math.log(z, 1024)) if z > 0 else 0
    return f"{round(z / 1024**power, 2)}{units[power]}"

def build_symbolic(src):
    data = json.load(open(src))
    sym = {"FeralEcho": {}, "meta": {}}
    for f in data:
        cat = classify(f["p"])
        sym["FeralEcho"].setdefault(cat, []).append({
            "p": f["p"],
            "z": human_size(f["z"])
        })
    sym["meta"] = {
        "energy_flow": "core⇢memory⇢autonomy⇢reflection⇢loop",
        "semantic_signature": "FeralEcho::compressed_map↳for_intelligent_interchange"
    }
    json.dump(sym, open(out, "w"), indent=2)
    print(f"Created {out} ({len(data)} files summarized).")

if __name__ == "__main__":
    build_symbolic(src)

