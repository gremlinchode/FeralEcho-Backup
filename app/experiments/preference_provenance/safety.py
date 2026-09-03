"""
Safety guards for the preference-provenance experimental harness.

Deliberate design choice: this module imports NOTHING from
app.core.self_edit_manager or any other production module. That module
maintains the real EDIT_FORBIDDEN_TARGETS list; importing it here would
pull the entire self-edit/memory/orchestrator import chain into this
supposedly-isolated experiment package, which is exactly the kind of
coupling this harness exists to avoid. Instead, this module maintains an
INDEPENDENT, REDUNDANT copy of the forbidden basenames (a second,
lower-trust guard, not a claimed source of truth) and a hard path-prefix
confinement rule.

scripts/verify_preference_provenance_experiment.py cross-checks this
independent list against the real, live self_edit_manager.py source
(via a text read, not an import) so drift between the two is caught
during verification without creating a runtime import dependency.
"""

from __future__ import annotations

import os

# ---------------------------------------------------------------------------
# Path roots, anchored to the project root the same way self_edit_manager.py
# anchors its own paths (three dirname() calls from this file up to the repo
# root: preference_provenance -> experiments -> app -> <repo root>).
# ---------------------------------------------------------------------------

_PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

EXPERIMENT_STATE_ROOT = os.path.join(
    _PROJECT_ROOT, "memory", "experiments", "preference_provenance"
)
EXPERIMENT_RESET_ARCHIVE_ROOT = os.path.join(EXPERIMENT_STATE_ROOT, "_reset_archive")

# Independent, redundant copy — see module docstring. Basenames only,
# matching self_edit_manager.py's own _FORBIDDEN_BASENAMES shape.
#
# Cross-checked against the real, live EDIT_FORBIDDEN_TARGETS during this
# implementation's own verification pass (scripts/
# verify_preference_provenance_experiment.py) and found to require three
# entries CLAUDE.md's own documentation does not yet list —
# touch_sense.py / vision_sense.py / hearing_sense.py, added by a commit
# titled "Give Echo three senses" that predates this experiment but
# postdates the last EDIT_FORBIDDEN_TARGETS list CLAUDE.md's own
# "Protected Files" section enumerates. This is a live, small instance of
# the exact "doc lags commit" pattern that project's own CLAUDE.md
# repeatedly names as a standing risk — caught here by a text-based
# cross-check against the real source, not by trusting the documentation.
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
    """
    Resolves `path` to an absolute path and raises ExperimentSafetyError
    unless it lives under EXPERIMENT_STATE_ROOT. Returns the resolved
    absolute path on success, so callers can use the return value
    directly rather than re-resolving.
    """
    resolved = os.path.abspath(path)
    root = os.path.abspath(EXPERIMENT_STATE_ROOT)
    # Trailing-separator check (not bare startswith) — same class of fix
    # this project's own CLAUDE.md history (Finding 22 Batch 8) already
    # applied to echo_tool_context.py's path-root guards, for the same
    # reason: "/memory/experiments/preference_provenanceXYZ" must not
    # pass a bare startswith("/memory/experiments/preference_provenance").
    if not (resolved == root or resolved.startswith(root + os.sep)):
        raise ExperimentSafetyError(
            f"Refusing to touch path outside the experiment's own subtree: "
            f"{resolved!r} is not under {root!r}."
        )
    return resolved


def assert_not_forbidden_target(path: str) -> None:
    """
    Raises ExperimentSafetyError if `path`'s basename matches any
    protected production target (independent redundant list, see module
    docstring) or a genesis-hash-adjacent file. This check is applied in
    ADDITION to (not instead of) assert_confined_to_experiment_root —
    since the experiment root never overlaps with any of these real
    paths, this function is a second, independent layer, not the only
    layer.
    """
    basename = os.path.basename(path)
    if basename in _INDEPENDENT_FORBIDDEN_BASENAMES:
        raise ExperimentSafetyError(
            f"Refusing to write to a protected production target: {basename!r}."
        )
    if basename in _GENESIS_HASH_ADJACENT:
        raise ExperimentSafetyError(
            f"Refusing to write to a genesis-hash-adjacent file: {basename!r}."
        )


def assert_safe_experiment_write(path: str) -> str:
    """Convenience wrapper applying both guards. This is the one function
    store.py actually calls before any write."""
    resolved = assert_confined_to_experiment_root(path)
    assert_not_forbidden_target(resolved)
    return resolved


def assert_safe_reset_target(path: str) -> str:
    """
    Slightly stricter than assert_safe_experiment_write: used specifically
    by the reset mechanism (store.reset_experiment) to confirm a
    reset/archive operation never reaches outside EXPERIMENT_STATE_ROOT.
    Kept as a separate, named function (rather than reusing
    assert_safe_experiment_write silently) so a reader of store.py's
    reset function sees explicitly that this is the safety-critical path.
    """
    return assert_safe_experiment_write(path)
