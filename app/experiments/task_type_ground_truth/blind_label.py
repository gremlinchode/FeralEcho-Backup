"""
Mission 34 — blinding-compliant label storage (app/experiments/task_type_ground_truth/).

Hard rule from Mission 33, Section 11, made checkable rather than just
documented: this module must be importable and usable WITHOUT ever
importing anything from app.core.echo_model_orchestrator or
app.core.task_type_classifier. assert_blinding_intact() makes that a real,
runtime-checkable assertion instead of an assumption.

Labels are collected interactively (this mission's actual labeling channel
was a direct, blind conversational exchange with the human labeler — see
the Mission 34 report for exactly how each example was presented, with no
heuristic/classifier output shown) and then written here, once, as a
locked batch — mirroring the "write once, then the label file is closed"
discipline Mission 33 specified.
"""
import json
import sys
from dataclasses import asdict
from app.experiments.task_type_ground_truth.schema import GoldLabel

_LABELS_PATH = "app/experiments/task_type_ground_truth/gold_labels.jsonl"

_FORBIDDEN_MODULES = (
    "app.core.echo_model_orchestrator",
    "app.core.task_type_classifier",
)


def assert_blinding_intact():
    """Raises if either forbidden module has been imported into this
    process before labels are finalized. A real, checkable guard, not
    just a documented intention."""
    violations = [m for m in _FORBIDDEN_MODULES if m in sys.modules]
    if violations:
        raise RuntimeError(
            f"BLINDING VIOLATION: {violations} already imported — the "
            f"heuristic/classifier may have been consulted before labels "
            f"were finalized. Labels collected in this process are suspect."
        )


def save_labels(labels: list[GoldLabel], path: str = _LABELS_PATH, append: bool = False) -> None:
    """Write-once by default (append=False truncates). Never touches
    memory/task_type_classifier.pkl or memory/interaction_log.jsonl."""
    mode = "a" if append else "w"
    with open(path, mode, encoding="utf-8") as f:
        for label in labels:
            f.write(json.dumps(asdict(label)) + "\n")


def load_labels(path: str = _LABELS_PATH) -> list[GoldLabel]:
    labels = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            labels.append(GoldLabel(**d))
    return labels
