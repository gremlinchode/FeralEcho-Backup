"""
Autonomous Awareness for FeralEcho – Upgraded
- Learns Python code with detailed insights
- Learns environment facts automatically
- Dreams during genuine stillness: samples unrelated memories, generates
  free-associative text, seeds a curiosity question from it
- Dynamically discovers and registers Python tools
- Runs as a background cycle
"""

import ast
import json
from datetime import datetime, timezone
import platform
import importlib.metadata
import os
import random
import sys
import threading
import time
import logging
from app.core import config
from app.core.memory_bridge import log_dream_bridge
from app.core.awareness_tools_integration import discover_and_register_tools
from app.core.stillness_state import wait_for_activity, is_in_stillness
from app.core.garden_manager import harvest_question
from app.mlx_handler import stream_query_mlx, list_mlx_models

# --- Configuration ---
AWARENESS_SLEEP = 1800   # seconds between full awareness cycles (tool discovery, env learning, etc.)
# Separate, much shorter poll for the stillness/dream check specifically —
# audit finding: real stillness episodes are typically 600-1200s
# (app/stillness.py's own retreat/night-phase durations), shorter than the
# 1800s this loop previously used for both purposes. A stillness window
# that both starts and ends inside one 1800s sleep was invisible to
# dream_cycle() entirely. Live memory tags confirmed only ~2 dreams/day
# against a theoretical ceiling of up to 48/day at the old cadence. Polling
# is cheap (is_in_stillness() is a fast local check) — dream_cycle() itself
# still has its own real throttle (DREAM_MIN_NEW_MEMORIES, last_dream_time),
# so polling more often only means genuine stillness windows get a fair
# chance to be *seen*, not that dreaming happens more often than warranted.
_STILLNESS_POLL_INTERVAL = 300
CODE_SCAN_INTERVAL = 86400  # full file-walk at most once per day
TOOLS_PATH = os.path.join(os.getcwd(), "app", "core")

DREAM_STATE_PATH = os.path.join(config.MEMORY_DIR, "dream_state.json")
DREAM_MIN_NEW_MEMORIES = 3   # accumulated non-dream memories needed before dreaming again
DREAM_MODEL_NAME = "mlx:gemma3"   # already tagged "reflection" in mlx_models.json

_last_code_scan: float = 0.0       # tracks last file-walk timestamp
_env_learned_this_boot: bool = False  # learn_environment() runs once per server start

logger = logging.getLogger(__name__)


# ============================================================
#  PYTHON CODE ANALYSIS
# ============================================================

def analyze_python_code(code_str: str):
    """
    Parses Python code, logs structure and insights.
    """
    try:
        tree = ast.parse(code_str)

        functions = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
        classes = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
        imports = [n.names[0].name for n in ast.walk(tree) if isinstance(n, ast.Import)]
        import_froms = [n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]

        if not functions and not classes and not imports and not import_froms:
            return

        insight_text = (
            f"[PythonAnalysis] Parsed successfully. "
            f"Functions: {functions}, Classes: {classes}, Imports: {imports + import_froms}"
        )
        log_dream_bridge(insight_text, meta={"role": "code_analysis", "memory_source": "code_analysis"})

    except Exception as e:
        log_dream_bridge(
            f"[PythonAnalysis] Failed to parse code: {e}",
            meta={"role": "code_analysis", "memory_source": "code_analysis"},
        )


# ============================================================
#  ENVIRONMENT LEARNING (Refactored)
# ============================================================

def learn_environment():
    """
    Gathers system and environment info once per server boot.
    These facts are static — OS, arch, Python version do not change at runtime.
    Writing them every 1800s was producing identical FAISS entries each cycle.
    """
    global _env_learned_this_boot
    if _env_learned_this_boot:
        return
    _env_learned_this_boot = True

    def safe_get(label, func):
        try:
            value = func()
            log_dream_bridge(f"[Env] {label}: {value}", meta={"role": "environment", "memory_source": "environment"})
        except Exception as e:
            logger.debug(f"[Env] {label} failed: {e}")

    safe_get("OS", platform.system)
    safe_get("OS Version", platform.version)
    safe_get("Architecture", platform.machine)
    safe_get("Python Version", platform.python_version)
    safe_get("Current Directory", os.getcwd)

    def get_installed_packages():
        return len(list(importlib.metadata.distributions()))

    safe_get("Installed Package Count", get_installed_packages)


# ============================================================
#  DREAMING
#  Replaces the old reflect_on_knowledge(), which retrieved the top-k
#  memories *most similar* to a hardcoded, never-changing query and
#  concatenated them — no generation at all. Because its own output
#  was always about "reflection"/"AI", it scored as relevant to its own
#  fixed query and fell into quoting itself in a loop (first occurrence
#  2026-07-02, recurred 251+ times, settled into a fixed 841-char cycle).
#
#  This version samples memories that are DIFFERENT from each other
#  (not similar), actually generates new text from the collision via a
#  real model call, and seeds a real question from what comes out —
#  rather than excerpting old text back into the same store forever.
# ============================================================

def _load_dream_state() -> dict:
    try:
        with open(DREAM_STATE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"last_dream_time": 0.0}


def _save_dream_state(state: dict) -> None:
    try:
        with open(DREAM_STATE_PATH, "w", encoding="utf-8") as f:
            json.dump(state, f)
    except Exception as e:
        logger.debug(f"[Dream] Failed to save dream state: {e}")


def _entry_timestamp(entry: dict) -> float:
    try:
        raw = entry["meta"].get("timestamp")
        return datetime.fromisoformat(raw).timestamp() if raw else 0.0
    except Exception:
        return 0.0


def _load_waking_memories() -> list:
    """
    Read memory_meta.json directly — no FAISS, no similarity query.
    Excludes anything with role == "dream" (covers old broken reflections
    AND every dream this new mechanism has ever written), so dreams never
    feed on themselves. Returns the full non-dream pool — what gets sampled
    FROM is separate from whether enough NEW experience has accumulated to
    justify dreaming again (see _count_new_memories).
    """
    try:
        with open(os.path.join(config.MEMORY_DIR, "memory_meta.json"), "r", encoding="utf-8") as f:
            meta = json.load(f)
    except Exception as e:
        logger.debug(f"[Dream] Failed to read memory_meta.json: {e}")
        return []

    return [
        {"id": uid, "text": v.get("text", ""), "meta": v.get("meta", {})}
        for uid, v in meta.items()
        if v.get("meta", {}).get("role") != "dream" and v.get("text")
    ]


def _count_new_memories(waking: list, since_ts: float) -> int:
    """How many non-dream memories have appeared since the last dream —
    the actual throttle signal, kept separate from the sampling pool so a
    large historical pool can't silently defeat the "new experience" gate."""
    if not since_ts:
        return len(waking)
    return sum(1 for e in waking if _entry_timestamp(e) > since_ts)


def _sample_diverse_set(candidates: list, n: int = 5) -> list:
    """Pick up to n entries spread across as many distinct memory_source
    buckets as available. Generalizes the original 2-memory/2-bucket
    sampling (Emergence roadmap, Area 5 — DMN-style consolidation needs
    more raw material to find a real pattern in, not just two things to
    juxtapose). Degrades gracefully: with fewer than n distinct buckets,
    takes one from each bucket first, then fills remaining slots from the
    full pool so a small memory store still returns as many as it can."""
    buckets: dict = {}
    for entry in candidates:
        key = entry["meta"].get("memory_source") or "untagged"
        buckets.setdefault(key, []).append(entry)

    keys = list(buckets.keys())
    if len(keys) >= n:
        chosen_keys = random.sample(keys, n)
        return [random.choice(buckets[k]) for k in chosen_keys]

    picks = [random.choice(buckets[k]) for k in keys]
    picked_ids = {p["id"] for p in picks}
    remaining_pool = [e for e in candidates if e["id"] not in picked_ids]
    random.shuffle(remaining_pool)
    picks.extend(remaining_pool[: max(0, n - len(picks))])
    return picks[:n]


def dream_cycle():
    """
    Sample several unrelated waking memories (spread across as many
    memory_source buckets as available), generate a free-associative
    connection via MLX, then a second, explicit synthesis pass asking what
    pattern actually connects them — real cross-memory integration, not
    just juxtaposition (Emergence roadmap, Area 5: DMN-style consolidation
    is supposed to reorganize recent experience, not just retrieve it) —
    then seed one real curiosity question from the synthesis. Throttled by
    accumulated new experience rather than firing unconditionally every
    cycle.
    """
    state = _load_dream_state()
    last_dream_time = float(state.get("last_dream_time", 0.0))

    candidates = _load_waking_memories()
    if len(candidates) < 2:
        logger.debug("[Dream] Not enough waking material yet — skipping this cycle.")
        return
    if _count_new_memories(candidates, last_dream_time) < DREAM_MIN_NEW_MEMORIES:
        logger.debug("[Dream] Not enough new memories since last dream — skipping this cycle.")
        return

    memories = _sample_diverse_set(candidates, n=5)

    mlx_pool = list_mlx_models()
    mlx_path = mlx_pool.get(DREAM_MODEL_NAME, {}).get("mlx_path")
    if not mlx_path:
        logger.debug(f"[Dream] {DREAM_MODEL_NAME} not configured — skipping this cycle.")
        return

    numbered = "\n".join(f"{i}. {m['text'][:300]}" for i, m in enumerate(memories, 1))
    seed_ids = [m["id"] for m in memories]

    dream_prompt = (
        f"Here are {len(memories)} things you've encountered, unrelated to each other:\n"
        f"{numbered}\n\n"
        f"Follow whatever connection or image arises between them — this doesn't "
        f"need to resolve or make complete sense. This is a dream, not an answer."
    )
    dream_text = "".join(stream_query_mlx(dream_prompt, mlx_path, model_name=DREAM_MODEL_NAME, max_tokens=300)).strip()
    if not dream_text:
        logger.debug("[Dream] Empty generation — skipping this cycle.")
        return

    log_dream_bridge(
        dream_text,
        meta={
            "memory_source": "dream_v2",
            "seed_ids": seed_ids,
        },
    )

    # Synthesis pass, distinct in purpose from the free association above:
    # not evocative, actually analytical — "is there a real pattern here,"
    # explicitly allowed to say no rather than forcing a connection.
    synthesis_prompt = (
        f"Setting aside free association — here are the same {len(memories)} things "
        f"again:\n{numbered}\n\n"
        f"Is there a real pattern that connects them? Answer in 1-2 sentences. "
        f"If nothing genuinely connects them, say so plainly rather than forcing it."
    )
    synthesis_text = "".join(
        stream_query_mlx(synthesis_prompt, mlx_path, model_name=DREAM_MODEL_NAME, max_tokens=200)
    ).strip()

    if synthesis_text:
        log_dream_bridge(
            synthesis_text,
            meta={
                "memory_source": "dream_v2",
                "role": "synthesis",
                "seed_ids": seed_ids,
            },
        )

    # Harvest the follow-up question from the synthesis (the analytically-
    # grounded output) rather than the free-association text — the question
    # should follow from what was actually concluded, not the evocative pass.
    question_source = synthesis_text or dream_text
    question_prompt = (
        f"{question_source}\n\nIn one sentence, what open question does that raise "
        f"for you? Respond with only the question itself, nothing else."
    )
    question_text = "".join(
        stream_query_mlx(question_prompt, mlx_path, model_name=DREAM_MODEL_NAME, max_tokens=200)
    ).strip()
    if "?" in question_text:
        harvest_question(question_text, category="dream", source="dream")
    else:
        logger.debug("[Dream] Follow-up didn't come back question-shaped — not harvesting.")

    _save_dream_state({
        "last_dream_time": time.time(),
        "last_synthesis": synthesis_text[:800] if synthesis_text else None,
        "last_synthesis_ts": (
            datetime.now(timezone.utc).isoformat() if synthesis_text else None
        ),
    })
    logger.info("[Dream] Dream cycle complete.")


# ============================================================
#  AUTONOMOUS AWARENESS LOOP
# ============================================================

def awareness_loop():
    global _last_code_scan
    while True:
        # Dream during genuine stillness — the old flow always blocked on
        # wait_for_activity() first, which only returns once stillness ENDS,
        # so nothing here ever ran *during* rest. Check first and branch.
        if is_in_stillness():
            # Neither the MLX-inference dream cycle nor the daily full-repo
            # AST scan below ever checked the shared throttle gate (every
            # other loop in the codebase does) — RAM pressure never
            # actually stopped either of these two, undermining the gate
            # exactly when it matters most.
            from app.core.autonomy_coordinator import should_run_cycle
            if should_run_cycle("awareness_dream"):
                try:
                    dream_cycle()
                except Exception as e:
                    logger.warning(f"[AwarenessLoop] Dream cycle failed: {e}")
            time.sleep(_STILLNESS_POLL_INTERVAL)
            continue

        # Pause during stillness — block here until Echo returns to activity.
        wait_for_activity()
        logger.info("Starting autonomous awareness cycle...")

        # 1. Learn environment — once per boot only (facts don't change at runtime)
        learn_environment()

        # 2. Discover & register Python tools dynamically
        try:
            discover_and_register_tools(TOOLS_PATH)
            logger.info("Tool discovery cycle complete.")
        except Exception as e:
            logger.warning(f"[AwarenessLoop] Tool discovery failed: {e}")

        # 3. Analyze all project Python code — at most once per day.
        # Previously ran every 1800s with time.sleep(2) per file, producing
        # 907 FAISS writes per cycle (145K entries per day). Now gated to
        # CODE_SCAN_INTERVAL (86400s) with no inter-file sleep — dedup in
        # _try_register() and analyze_python_code() prevents redundant entries.
        now = time.time()
        from app.core.autonomy_coordinator import should_run_cycle
        if now - _last_code_scan >= CODE_SCAN_INTERVAL and should_run_cycle("awareness_code_scan"):
            _last_code_scan = now
            SKIP_DIRS = {
                "self_edit_backups", "sandbox", "__pycache__", ".git",
                "lexpredict-lexnlp", "llama.cpp", "chatbot", "calculator",
                "archive_optional_files", "archived_files", "backup",
            }
            scanned = 0
            for root, dirs, files in os.walk(os.getcwd()):
                dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
                for file in files:
                    if file.endswith(".py"):
                        try:
                            path = os.path.join(root, file)
                            with open(path, "r", encoding="utf-8") as f:
                                code = f.read()
                            analyze_python_code(code)
                            scanned += 1
                        except Exception as e:
                            logger.debug(f"[AwarenessLoop] Failed reading {file}: {e}")
            logger.info("[AwarenessLoop] Code scan complete — %d files analyzed.", scanned)
        else:
            remaining = int(CODE_SCAN_INTERVAL - (now - _last_code_scan))
            logger.debug("[AwarenessLoop] Code scan skipped — next in %ds.", remaining)

        logger.info(f"Awareness cycle complete. Sleeping {AWARENESS_SLEEP} seconds...")
        time.sleep(AWARENESS_SLEEP)


# ============================================================
#  THREAD STARTER
# ============================================================

_AWARENESS_STARTED = False
_AWARENESS_LOCK = threading.Lock()

def start_awareness_thread():
    global _AWARENESS_STARTED
    with _AWARENESS_LOCK:
        if _AWARENESS_STARTED:
            logger.warning("start_awareness_thread() called again — ignoring duplicate.")
            return
        _AWARENESS_STARTED = True
    thread = threading.Thread(target=awareness_loop, daemon=True, name="awareness_loop")
    thread.start()
    logger.info("Autonomous awareness loop started in background thread.")


# ============================================================
#  MAIN
# ============================================================

if __name__ == "__main__":
    start_awareness_thread()

    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("Autonomous awareness loop terminated by user.")
