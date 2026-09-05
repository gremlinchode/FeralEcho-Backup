"""
Safety guards for the learning-investigation experimental harness.

Mirrors app/experiments/preference_provenance/safety.py's proven design
exactly (same path-confinement + independent-forbidden-list pattern),
but as a genuinely SEPARATE module with its OWN state root -- this
package's persisted evidence must never be coupled to, or confused
with, the other experiment's own state, per this investigation's
explicit "do not modify existing preference experiment... frozen
artifacts" constraint. The two packages share no runtime state; only
read-only utility imports (choice_parser, harness.randomize_label_mapping)
cross the boundary.

Deliberate design choice, same reasoning as the sibling module: this
imports NOTHING from app.core.self_edit_manager -- an independent,
redundant copy of the forbidden basenames is maintained instead (a
second, lower-trust guard, not a claimed source of truth).
"""

from __future__ import annotations

import os

_PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

EXPERIMENT_STATE_ROOT = os.path.join(_PROJECT_ROOT, "memory", "experiments", "learning")
EXPERIMENT_RESET_ARCHIVE_ROOT = os.path.join(EXPERIMENT_STATE_ROOT, "_reset_archive")

# Independent, redundant copy -- see module docstring. Kept identical in
# shape to preference_provenance/safety.py's own list; not re-derived
# from it via import, so drift between the two would have to be caught
# by re-reading real self_edit_manager.py source directly (same
# discipline the sibling module's own verification script uses).
_INDEPENDENT_FORBIDDEN_BASENAMES = frozenset({
    "run.py",
    "echo_principles.json",
    "Modelfile",
    "echo_model_orchestrator.py",
    "river_deliberation.py",
    "echo_core.py",
    "memory_bridge.py",
    "introspection_channel.py",
    "self_model_updater.py",
    "bible_injection.py",
    "reflection_shard.py",
    "touch_sense.py",
    "vision_sense.py",
    "hearing_sense.py",
})

_GENESIS_HASH_ADJACENT = frozenset({"genesis_hash.txt", "council_hash.txt"})


class ExperimentSafetyError(RuntimeError):
    """Raised whenever an operation in this package would touch something
    outside its own confined subtree, or a name on the forbidden list."""


def assert_confined_to_experiment_root(path: str) -> str:
    resolved = os.path.abspath(path)
    root = os.path.abspath(EXPERIMENT_STATE_ROOT)
    if not (resolved == root or resolved.startswith(root + os.sep)):
        raise ExperimentSafetyError(
            f"Refusing to touch path outside the experiment's own subtree: "
            f"{resolved!r} is not under {root!r}."
        )
    return resolved


def assert_not_forbidden_target(path: str) -> None:
    basename = os.path.basename(path)
    if basename in _INDEPENDENT_FORBIDDEN_BASENAMES:
        raise ExperimentSafetyError(f"Refusing to write to a protected production target: {basename!r}.")
    if basename in _GENESIS_HASH_ADJACENT:
        raise ExperimentSafetyError(f"Refusing to write to a genesis-hash-adjacent file: {basename!r}.")


def assert_safe_experiment_write(path: str) -> str:
    resolved = assert_confined_to_experiment_root(path)
    assert_not_forbidden_target(resolved)
    return resolved


def assert_safe_reset_target(path: str) -> str:
    return assert_safe_experiment_write(path)
