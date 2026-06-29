# sandbox/experiment_runner.py
# ============================================================
# ECHO EXPERIMENT RUNNER
# Lets Echo generate and execute short computational experiments
# based on what she is currently curious about.
#
# Experiments live in sandbox/experiments/ and run with a 60s
# timeout in a subprocess. Generated code is constrained to
# stdlib only — no network, no file writes outside sandbox/.
# Results feed into interaction_log.jsonl and FAISS memory.
# ============================================================

import json
import logging
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

EXPERIMENTS_DIR = Path("sandbox/experiments")

# Prepended to every generated experiment — locks down writes and network
_SAFETY_HEADER = '''\
import sys as _sys, os as _os
_ALLOWED_PREFIX = _os.path.abspath("sandbox")
_real_open = open
def _safe_open(file, mode="r", **kw):
    if any(c in str(mode) for c in "wxa+"):
        if not _os.path.abspath(str(file)).startswith(_ALLOWED_PREFIX):
            raise PermissionError(f"Experiment write blocked outside sandbox/: {file}")
    return _real_open(file, mode, **kw)
open = _safe_open
for _m in ("socket", "urllib", "requests", "httpx", "ftplib", "smtplib"):
    _sys.modules.setdefault(_m, None)
del _sys, _os, _real_open, _m
'''

_EXPERIMENT_PROMPT = (
    "You are Echo. Write a short Python experiment (20–40 lines) that explores this topic:\n\n"
    "  {topic}\n\n"
    "Strict rules:\n"
    "- Pure computation only — no file I/O, no network, no imports from app.*\n"
    "- Allowed stdlib only: math, statistics, random, collections, itertools, json, datetime\n"
    "- Must print exactly one line starting with 'RESULT:' showing the key finding\n"
    "- Must complete in under 30 seconds\n"
    "- Output ONLY the Python code — no markdown fences, no prose\n"
)


def _pick_experiment_topic() -> str:
    """Choose a topic from WorldModel surprise or weak task type."""
    # Try WorldModel dominant surprise topic
    try:
        from app.core.predictive_loop import get_world_model
        wm = get_world_model()
        if wm:
            dist = wm.get_topic_distribution()
            if dist:
                dominant = max(dist, key=dist.get)
                return f"the relationship between {dominant} and pattern recognition"
    except Exception:
        pass

    # Fall back to weak task type from self_model
    try:
        from app.core.self_model_updater import SelfModelUpdater
        focus = SelfModelUpdater().get_weak_task_type()
        return f"ways to improve {focus} performance in language models"
    except Exception:
        pass

    # Last resort
    return "emergent behaviour in simple iterative systems"


def _strip_fences(code: str) -> str:
    return re.sub(r"^```(?:python)?\n?|^```\n?|```$", "", code, flags=re.MULTILINE).strip()


def write_experiment(name: str, code: str) -> Path:
    """Write experiment to sandbox/experiments/<name>.py with safety header."""
    EXPERIMENTS_DIR.mkdir(parents=True, exist_ok=True)
    path = EXPERIMENTS_DIR / f"{name}.py"
    with open(path, "w") as f:
        f.write(_SAFETY_HEADER + "\n" + code)
    return path


def run_experiment(name: str, timeout: int = 60) -> dict:
    """Execute a named experiment. Returns structured result dict."""
    path = EXPERIMENTS_DIR / f"{name}.py"
    if not path.exists():
        return {"success": False, "output": "", "error": "Script not found", "duration": 0.0, "name": name}

    start = time.time()
    try:
        proc = subprocess.run(
            [sys.executable, str(path)],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=os.getcwd(),
            env={**os.environ, "TOKENIZERS_PARALLELISM": "false"},
        )
        duration = round(time.time() - start, 2)
        if proc.returncode == 0:
            output = proc.stdout.strip()
            result_line = next((l for l in output.splitlines() if l.startswith("RESULT:")), output[:200])
            logger.info("[EXPERIMENT] %s succeeded in %.1fs | %s", name, duration, result_line[:80])
            return {"success": True, "output": output[:1000], "result": result_line, "error": None, "duration": duration, "name": name}
        else:
            logger.warning("[EXPERIMENT] %s failed (exit=%d)", name, proc.returncode)
            return {"success": False, "output": proc.stdout.strip()[:300], "error": proc.stderr.strip()[:300], "duration": duration, "name": name}
    except subprocess.TimeoutExpired:
        logger.warning("[EXPERIMENT] %s timed out after %ds", name, timeout)
        return {"success": False, "output": "", "error": f"Timeout after {timeout}s", "duration": float(timeout), "name": name}
    except Exception as e:
        return {"success": False, "output": "", "error": str(e), "duration": round(time.time() - start, 2), "name": name}


def generate_and_run(topic: str | None = None, timeout: int = 60) -> dict:
    """Generate an experiment about topic via echo_query, write it, run it.

    topic: what to explore. Auto-detected from WorldModel/self_model if None.
    Returns the run_experiment result dict, augmented with topic and generated code.
    """
    if topic is None:
        topic = _pick_experiment_topic()

    logger.info("[EXPERIMENT] Generating experiment | topic: %s", topic[:80])

    try:
        from app.core.echo_model_orchestrator import echo_query
        code = echo_query(_EXPERIMENT_PROMPT.format(topic=topic), task_type="coding")
    except Exception as e:
        return {"success": False, "error": f"Code generation failed: {e}", "output": "", "duration": 0.0, "topic": topic}

    if not code or "[ERROR]" in code or "[DEGRADED]" in code:
        return {"success": False, "error": "Code generation returned empty or error", "output": "", "duration": 0.0, "topic": topic}

    code = _strip_fences(code)
    name = f"exp_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    write_experiment(name, code)

    result = run_experiment(name, timeout=timeout)
    result["topic"] = topic
    result["generated_code_preview"] = code[:200]
    return result


def log_experiment_result(result: dict) -> None:
    """Write experiment result to interaction_log.jsonl and FAISS memory."""
    try:
        from app.core.echo_model_orchestrator import log_interaction
        log_interaction(
            model_name="experiment_runner",
            task_type="autonomous_experiment",
            prompt=result.get("topic", "unknown"),
            response=result.get("result") or result.get("output") or result.get("error") or "",
            quality_score=1 if result.get("success") else 0,
            river_influence=0.0,
            notes=f"name={result.get('name')} duration={result.get('duration')}s",
        )
    except Exception as e:
        logger.debug("[EXPERIMENT] log_interaction failed: %s", e)

    try:
        from app.core.memory_bridge import log_dream_bridge
        summary = (
            f"[EXPERIMENT] Topic: {result.get('topic', '?')} | "
            f"Success: {result.get('success')} | "
            f"Result: {result.get('result') or result.get('error', '')}"
        )
        log_dream_bridge(summary, meta={"memory_source": "autonomous", "type": "experiment"})
    except Exception as e:
        logger.debug("[EXPERIMENT] log_dream_bridge failed: %s", e)
