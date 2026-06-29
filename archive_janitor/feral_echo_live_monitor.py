#!/usr/bin/env python3
"""
feral_echo_live_monitor.py
Monitor FeralEcho background loops safely:
- ReflectionShard signals
- Self-edit attempts
- NightCycle dreams
"""

import os
import time
import json
from datetime import datetime

# ---- paths ----
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
REFLECTION_LOG = os.path.join(PROJECT_DIR, "memory/reflection_journal.jsonl")
SELF_EDIT_LOG = os.path.join(PROJECT_DIR, "app/core/self_edit_log.jsonl")
NIGHTCYCLE_LOG = os.path.join(PROJECT_DIR, "memory/night_cycle.log")

def tail_json_lines(filepath):
    """Yield new JSON lines safely."""
    if not os.path.exists(filepath):
        return
    seen = set()
    while True:
        with open(filepath, "r", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if line and line not in seen:
                    seen.add(line)
                    try:
                        yield json.loads(line)
                    except Exception:
                        continue
        time.sleep(2)

def tail_plain_lines(filepath):
    """Yield new plain text lines safely."""
    if not os.path.exists(filepath):
        return
    seen = set()
    while True:
        with open(filepath, "r", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if line and line not in seen:
                    seen.add(line)
                    yield line
        time.sleep(2)

def monitor():
    reflection_gen = tail_json_lines(REFLECTION_LOG)
    self_edit_gen = tail_json_lines(SELF_EDIT_LOG)
    night_gen = tail_plain_lines(NIGHTCYCLE_LOG)

    reflection_count = 0
    self_edit_count = 0
    night_count = 0

    print("[Monitor] Starting live observation of FeralEcho loops...")
    try:
        while True:
            # Reflections
            for _ in range(2):
                try:
                    r = next(reflection_gen)
                    ts = r.get("timestamp", datetime.utcnow().isoformat())
                    reflection_count += 1
                    print(f"[Reflection {reflection_count}] {ts}: {r.get('signal', r.get('reflection', ''))[:100]}")
                except StopIteration:
                    break

            # Self-edit attempts
            for _ in range(2):
                try:
                    s = next(self_edit_gen)
                    ts = s.get("timestamp", datetime.utcnow().isoformat())
                    self_edit_count += 1
                    print(f"[Self-Edit {self_edit_count}] {ts}: {s.get('params', s.get('note', ''))}")
                except StopIteration:
                    break

            # NightCycle dreams
            for _ in range(2):
                try:
                    n = next(night_gen)
                    night_count += 1
                    print(f"[NightCycle {night_count}] {n[:100]}")
                except StopIteration:
                    break

            # Summary every 10 iterations
            if (reflection_count + self_edit_count + night_count) % 10 == 0:
                print(f"\n[Summary] Reflections: {reflection_count}, Self-Edits: {self_edit_count}, NightCycle Dreams: {night_count}\n")

            time.sleep(3)
    except KeyboardInterrupt:
        print("\n[Monitor] Stopped live observation.")

if __name__ == "__main__":
    monitor()

