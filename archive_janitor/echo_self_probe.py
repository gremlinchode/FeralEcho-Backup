# archive_janitor/echo_self_probe.py
# ============================================================
# ECHO SELF-PROBE — CLI diagnostic for Echo's ground-truth state
# ============================================================
# Repurposed from the original tool-name scanner (which read
# registered ToolManager names and was never wired to anything).
# Now reads from the same sources as echo_ground_truth.py and
# prints a full structural snapshot of Echo's current state.
#
# Run from the FeralEcho root:
#   python archive_janitor/echo_self_probe.py
#
# Shows: self-edit history, River quality scores, ClaudeShard
# friction window, stillness log, and curiosity garden.
# No LLM calls. No writes. Safe to run while server is live.
# ============================================================

import os
import sys

# Allow imports from the project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

from app.core.echo_ground_truth import (
    get_structural_self_facts,
    _is_introspective,
    _relevant_slices,
    _backup_count,
    _read_json,
    _read_jsonl_tail,
    _SELF_MODEL_PATH,
    _INTROSPECTION_PATH,
    _SILENCE_LOG,
    _GARDEN_PATH,
)
import json
from datetime import datetime, timezone


def probe_self_state():
    """Print Echo's full structural state from disk."""
    print("=" * 60)
    print("ECHO SELF-PROBE — ground truth from disk")
    print(f"Run at: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)
    print()

    # File freshness check
    for label, path in [
        ("self_model.json", _SELF_MODEL_PATH),
        ("introspection_state.json", _INTROSPECTION_PATH),
        ("silence.jsonl", _SILENCE_LOG),
        ("question_garden.jsonl", _GARDEN_PATH),
    ]:
        try:
            mtime = os.path.getmtime(path)
            age_s = (datetime.now(timezone.utc).timestamp() - mtime)
            age_str = f"{int(age_s)}s ago" if age_s < 3600 else f"{age_s/3600:.1f}h ago"
            print(f"  {label}: last modified {age_str}")
        except FileNotFoundError:
            print(f"  {label}: NOT FOUND")
    print()

    output = get_structural_self_facts(prompt="")  # empty = all slices
    print(output if output else "[EMPTY — all reads failed]")

    # Additional: backup file timestamps (most recent 5)
    print("Self-edit backup files (most recent 5):")
    backup_dir = os.path.join("app", "core", "self_edit_backups")
    try:
        files = sorted(
            [f for f in os.listdir(backup_dir) if f.endswith(".py")],
            reverse=True
        )[:5]
        for f in files:
            print(f"  {f}")
        print(f"  ... ({_backup_count()} total)")
    except Exception as e:
        print(f"  Error reading backup dir: {e}")
    print()


def probe_slice(prompt: str):
    """Show what slices a prompt would trigger and the injected context."""
    print(f"Prompt: \"{prompt}\"")
    print(f"Is introspective: {_is_introspective(prompt)}")
    slices = _relevant_slices(prompt)
    print(f"Relevant slices: {slices or 'none'}")
    print()
    result = get_structural_self_facts(prompt)
    print(result if result else "[no context injected]")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Usage: python echo_self_probe.py "your question here"
        # Shows what context would be injected for that prompt
        prompt = " ".join(sys.argv[1:])
        probe_slice(prompt)
    else:
        # No args: full state dump
        probe_self_state()
