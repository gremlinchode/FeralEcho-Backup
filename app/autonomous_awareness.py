"""
Autonomous Awareness for FeralEcho – Upgraded
- Learns Python code with detailed insights
- Learns environment facts automatically
- Reflects on stored knowledge and generates hypotheses
- Dynamically discovers and registers Python tools
- Runs as a background cycle
"""

import ast
import platform
import importlib.metadata
import os
import sys
import threading
import time
import logging
from app.core.memory_bridge import log_dream_bridge, retrieve_relevant_memories
from app.core.awareness_tools_integration import discover_and_register_tools

# --- Configuration ---
AWARENESS_SLEEP = 1800  # seconds between awareness cycles
TOOLS_PATH = os.path.join(os.getcwd(), "app", "core")

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
        log_dream_bridge(insight_text)

    except Exception as e:
        log_dream_bridge(f"[PythonAnalysis] Failed to parse code: {e}")


# ============================================================
#  ENVIRONMENT LEARNING (Refactored)
# ============================================================

def learn_environment():
    """
    Gathers system and environment info safely and efficiently.
    Uses importlib.metadata for accurate installed-package discovery.
    """

    def safe_get(label, func):
        try:
            value = func()
            log_dream_bridge(f"[Env] {label}: {value}")
        except Exception as e:
            log_dream_bridge(f"[EnvError] {label} failed: {e}")

    # System info
    safe_get("OS", platform.system)
    safe_get("OS Version", platform.version)
    safe_get("Architecture", platform.machine)
    safe_get("Python Version", platform.python_version)
    safe_get("Current Directory", os.getcwd)

    # Installed packages — count only, not the full list (avoids FAISS bloat)
    def get_installed_packages():
        return len(list(importlib.metadata.distributions()))

    safe_get("Installed Package Count", get_installed_packages)


# ============================================================
#  AUTONOMOUS REFLECTION
# ============================================================

def reflect_on_knowledge(tag_filter=None):
    """
    Retrieves recent memories, detects patterns, and logs reflections.
    """
    try:
        query = "AI OR Python OR environment OR reflection"

        memories = retrieve_relevant_memories(query, top_k=5)
        if not memories:
            log_dream_bridge("[Reflect] No relevant memories found.")
            return

        reflection = "[Reflect] Cycle insights: "
        for mem in memories:
            reflection += f"{mem['text'][:150]}... | "

        log_dream_bridge(reflection)

    except Exception as e:
        log_dream_bridge(f"[Reflect] Reflection cycle failed: {e}")


# ============================================================
#  AUTONOMOUS AWARENESS LOOP
# ============================================================

def awareness_loop():
    while True:
        logger.info("Starting autonomous awareness cycle...")

        # 1. Learn environment
        learn_environment()

        # 2. Discover & register Python tools dynamically
        try:
            discover_and_register_tools(TOOLS_PATH)
            logger.info("Tool discovery cycle complete.")
        except Exception as e:
            log_dream_bridge(f"[AwarenessLoop] Tool discovery failed: {e}")

        # 3. Analyze all project Python code
        # time.sleep(2) between each file prevents FAISS write storms
        # that previously caused system-wide lag and OOM kills.
        SKIP_DIRS = {"self_edit_backups", "sandbox", "__pycache__", ".git", "lexpredict-lexnlp", "llama.cpp", "chatbot", "calculator", "archive_optional_files", "archived_files", "backup"}
        for root, dirs, files in os.walk(os.getcwd()):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for file in files:
                if file.endswith(".py"):
                    try:
                        path = os.path.join(root, file)
                        with open(path, "r", encoding="utf-8") as f:
                            code = f.read()
                        analyze_python_code(code)
                        time.sleep(2)  # reduced from 10s
                    except Exception as e:
                        log_dream_bridge(f"[AwarenessLoop] Failed reading {file}: {e}")
        # 4. Reflect on stored knowledge
        reflect_on_knowledge()

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
