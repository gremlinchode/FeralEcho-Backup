"""
FeralEcho — Unified Learning Architecture Patch
Run from FeralEcho root: python patch_unified_learning.py

Changes:
  1. echo_core.py        — adds _init_river_brain, _init_optuna, _init_dual_learner,
                           get_river_brain(), report_learning_event()
  2. echo_model_orchestrator.py — makes RIVER_BRAIN lazy, delegates to EchoCore
  3. self_edit_manager.py      — routes get_river_brain() through EchoCore

Backs up all three files before touching them.
"""

import os
import shutil
import sys
from datetime import datetime

ROOT = os.path.dirname(os.path.abspath(__file__))

FILES = {
    "echo_core":        "app/core/echo_core.py",
    "orchestrator":     "app/core/echo_model_orchestrator.py",
    "self_edit":        "app/core/self_edit_manager.py",
}

# ─── helpers ──────────────────────────────────────────────────────────────────

def backup(path):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dst = path + f".bak_{ts}"
    shutil.copy2(path, dst)
    print(f"  backed up → {dst}")

def read(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def write(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def patch(path, old, new, label):
    content = read(path)
    if old not in content:
        print(f"  ✗ [{label}] anchor not found — skipping (already patched?)")
        return False
    write(path, content.replace(old, new, 1))
    print(f"  ✓ [{label}] patched")
    return True

def abort(msg):
    print(f"\nABORT: {msg}")
    sys.exit(1)

# ─── preflight ────────────────────────────────────────────────────────────────

print("\n=== FeralEcho unified learning patch ===\n")

for key, rel in FILES.items():
    full = os.path.join(ROOT, rel)
    if not os.path.exists(full):
        abort(f"{rel} not found. Are you running from the FeralEcho root?")

print("All target files found. Creating backups...\n")
for key, rel in FILES.items():
    backup(os.path.join(ROOT, rel))

# ─── PATCH 1: echo_core.py ────────────────────────────────────────────────────

print("\n[1/3] Patching echo_core.py ...")

CORE_PATH = os.path.join(ROOT, FILES["echo_core"])

# Anchor: the line after _init_query_fn call in __init__
CORE_OLD = "        self._init_query_fn(query_fn)\n\n        self.ready = True"

CORE_NEW = """\
        self._init_query_fn(query_fn)
        self._init_river_brain()
        self._init_optuna()
        self._init_dual_learner()

        self.ready = True"""

patch(CORE_PATH, CORE_OLD, CORE_NEW, "echo_core __init__")

# Add the four new methods before the _autonomous_scan method
CORE_METHODS_OLD = "    # --------------------------\n    # Autonomous dominion\n    # --------------------------\n    def _autonomous_scan(self):"

CORE_METHODS_NEW = """\
    # --------------------------
    # Learning system owners
    # --------------------------
    def _init_river_brain(self):
        try:
            from app.core.echo_model_orchestrator import RiverBrain
            self.river_brain = RiverBrain.load()
            logger.info("[EchoCore] RiverBrain loaded — single owner established.")
        except Exception as e:
            self.river_brain = None
            logger.warning(f"[EchoCore] Could not load RiverBrain: {e}")

    def get_river_brain(self):
        return self.river_brain

    def _init_optuna(self):
        try:
            import optuna
            optuna.logging.set_verbosity(optuna.logging.WARNING)
            self.optuna_study = optuna.create_study(
                study_name="echo_self_edit",
                storage="sqlite:///memory/optuna.db",
                load_if_exists=True,
                direction="minimize"
            )
            logger.info(
                f"[EchoCore] Optuna study loaded — "
                f"{len(self.optuna_study.trials)} trials on record."
            )
        except Exception as e:
            self.optuna_study = None
            logger.warning(f"[EchoCore] Could not initialize Optuna: {e}")

    def _init_dual_learner(self):
        try:
            from app.learning.dual_learning import get_dual_learner
            self.dual_learner = get_dual_learner()
            logger.info("[EchoCore] DualLearner wired in.")
        except Exception as e:
            self.dual_learner = None
            logger.warning(f"[EchoCore] Could not initialize DualLearner: {e}")

    def report_learning_event(self, source: str, text: str, metadata: dict = None):
        \"\"\"Single entry point for all learning events across subsystems.\"\"\"
        if self.dual_learner:
            try:
                self.dual_learner.log_event(source, text, metadata or {})
            except Exception as e:
                logger.warning(f"[EchoCore] DualLearner log_event failed: {e}")

    # --------------------------
    # Autonomous dominion
    # --------------------------
    def _autonomous_scan(self):"""

patch(CORE_PATH, CORE_METHODS_OLD, CORE_METHODS_NEW, "echo_core new methods")

# ─── PATCH 2: echo_model_orchestrator.py ──────────────────────────────────────

print("\n[2/3] Patching echo_model_orchestrator.py ...")

ORCH_PATH = os.path.join(ROOT, FILES["orchestrator"])

ORCH_OLD = """\
def get_river_brain():
    return RIVER_BRAIN

# Initialize brain at module load
RIVER_BRAIN = RiverBrain.load()"""

ORCH_NEW = """\
# Lazy singleton — avoids spawning independent instances on every import
_RIVER_BRAIN_INSTANCE = None

def get_river_brain():
    global _RIVER_BRAIN_INSTANCE
    # Prefer EchoCore's authoritative instance when running inside Flask
    try:
        from flask import current_app
        core = current_app.config.get('echo_core')
        if core is not None and getattr(core, 'river_brain', None) is not None:
            return core.river_brain
    except Exception:
        pass
    # Fallback: standalone process (e.g. rehab loop without Flask)
    if _RIVER_BRAIN_INSTANCE is None:
        _RIVER_BRAIN_INSTANCE = RiverBrain.load()
        logger.warning(
            "[Orchestrator] RiverBrain loaded locally — EchoCore not available. "
            "Avoid running concurrent processes to prevent pkl overwrites."
        )
    return _RIVER_BRAIN_INSTANCE

# Module-level alias — resolved lazily on first access
RIVER_BRAIN = get_river_brain()"""

patch(ORCH_PATH, ORCH_OLD, ORCH_NEW, "orchestrator lazy RiverBrain")

# ─── PATCH 3: self_edit_manager.py ────────────────────────────────────────────

print("\n[3/3] Patching self_edit_manager.py ...")

SE_PATH = os.path.join(ROOT, FILES["self_edit"])

SE_OLD = """\
from app.core.echo_model_orchestrator import (
    save_reflection, load_reflections, detect_task_type,
    rank_models, get_river_brain, choose_model
)"""

SE_NEW = """\
from app.core.echo_model_orchestrator import (
    save_reflection, load_reflections, detect_task_type,
    rank_models, choose_model
)

def get_river_brain():
    \"\"\"Route through EchoCore when inside Flask; fall back to orchestrator otherwise.\"\"\"
    try:
        from flask import current_app
        core = current_app.config.get('echo_core')
        if core is not None and getattr(core, 'river_brain', None) is not None:
            return core.river_brain
    except Exception:
        pass
    from app.core.echo_model_orchestrator import get_river_brain as _grb
    return _grb()"""

patch(SE_PATH, SE_OLD, SE_NEW, "self_edit_manager get_river_brain")

# ─── summary ──────────────────────────────────────────────────────────────────

print("""
=== Patch complete ===

What changed:
  • EchoCore now owns RiverBrain, Optuna (persistent), and DualLearner
  • Optuna trials persist to memory/optuna.db across sessions
  • get_river_brain() everywhere delegates to EchoCore inside Flask
  • Standalone processes (rehab loop) fall back gracefully with a warning

Next steps:
  1. Start run.py as normal — watch logs for:
       [EchoCore] RiverBrain loaded — single owner established.
       [EchoCore] Optuna study loaded — N trials on record.
       [EchoCore] DualLearner wired in.
  2. Run a short rehab cycle (--cycles 5) and verify obs count holds after:
       python river_creative_rehab.py --cycles 5 --delay 10
       python -c "
import pickle
with open('memory/river_brain.pkl','rb') as f: rb=pickle.load(f)
print('creative obs:', rb['observation_counts']['creative'])
"
  3. Orphaned pkls to deprecate when stable:
       new_directory/memory/river_brain.pkl
       echo_scripts/memory/river_brain.pkl
""")
