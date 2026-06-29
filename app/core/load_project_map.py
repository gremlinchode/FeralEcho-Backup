from app.core.project_learner import ProjectLearner
import logging
import os

# Resolve project root from this file's location: app/core/ → project root
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def load_project_map(echo_instance, project_path=None):
    """
    Automatically scans the FeralEcho project and feeds all modules
    into Echo's memory_bridge on startup.
    """
    if project_path is None:
        project_path = _PROJECT_ROOT

    logging.info(f"[PROJECT_MAP] Loading project map from {project_path}")
    learner = ProjectLearner(project_path)
    learner.learn(write_out=False)

    items = learner.to_memory_items()
    for item in items:
        echo_instance.memory_bridge.add(item)

    logging.info(f"[PROJECT_MAP] Loaded {len(items)} modules into memory_bridge")

