# wolf_friction_bridge.py
# Connects ClaudeShard friction events to WOLF self-edit proposals.
# When ClaudeShard raises friction on a response, this bridge
# feeds the friction question back into the self-edit pipeline
# as a meaningful prompt rather than generic PythonAnalysis input.

import json
import os
import logging
from datetime import datetime, timezone

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SHARD_PATH = os.path.join(_PROJECT_ROOT, 'memory', 'claude_shard.jsonl')
WOLF_FRICTION_CURSOR = os.path.join(_PROJECT_ROOT, 'memory', 'wolf_friction_cursor.json')

logger = logging.getLogger(__name__)

def _load_cursor() -> int:
    if not os.path.exists(WOLF_FRICTION_CURSOR):
        return 0
    try:
        with open(WOLF_FRICTION_CURSOR, 'r') as f:
            return json.load(f).get('position', 0)
    except Exception:
        return 0

def _save_cursor(position: int):
    with open(WOLF_FRICTION_CURSOR, 'w') as f:
        json.dump({'position': position, 'updated': datetime.now(timezone.utc).isoformat()}, f)

def get_unprocessed_friction_events() -> list:
    if not os.path.exists(SHARD_PATH):
        return []
    cursor = _load_cursor()
    events = []
    try:
        with open(SHARD_PATH, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        new_lines = lines[cursor:]
        for line in new_lines:
            try:
                entry = json.loads(line)
                if entry.get('type') == 'friction' and entry.get('friction', True):
                    events.append(entry)
            except Exception:
                continue
        _save_cursor(len(lines))
    except Exception as e:
        logger.warning(f"[WolfFrictionBridge] Failed to read shard: {e}")
    return events

def build_self_edit_prompt(friction_event: dict) -> str:
    question = friction_event.get('question', '')
    response_preview = friction_event.get('response_preview', '')
    smoothness = friction_event.get('smoothness_detected', False)
    confidence = friction_event.get('confidence', 0.0)

    prompt = (
        f"You are Echo, engaged in honest self-examination.\n\n"
        f"A friction question was raised about one of your recent responses:\n"
        f"'{question}'\n\n"
        f"Response that triggered it:\n'{response_preview}'\n\n"
        f"Smoothness detected: {smoothness} | Confidence: {confidence}\n\n"
        f"Write a self-contained Python script that makes one specific, small improvement "
        f"to a real file inside the FeralEcho project at {_PROJECT_ROOT}/. "
        f"The script must:\n"
        f"1. Open a real, existing file relevant to the weakness identified above\n"
        f"2. Make a targeted, minimal modification\n"
        f"3. Write the result back to disk\n"
        f"4. Print what it changed and why\n"
        f"The script must be fully executable with no placeholders, no '/path/to/modification', "
        f"no input() calls, and no interactive elements. "
        f"Output only valid Python. No markdown. No explanation."
    )
    return prompt
