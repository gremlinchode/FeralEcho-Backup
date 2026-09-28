"""Lookup-table selector (PREREG_ADDENDUM.md 'Blocker 2') -- a standalone
object with NO shared state with production RiverBrain, ever (confirmed by
this module never importing anything from app.core). State:
{feature_signature_str: {strategy: {"count": int, "mean": float}}}.

update() receives ONLY (feature_signature, strategy_used, outcome: bool) --
the sanitized-feedback contract from the frozen design's §6. It is a
TypeError, not a silent ignore, to pass anything else, so a future call
site accidentally threading through error text or expected values fails
loudly rather than leaking quietly.

Persistence is a single JSON file, content-hashed on every save -- the
hash is what Section 10's U (update) records and Section 13's restart-
boundary intervention actually compare, not file mtimes."""
from __future__ import annotations
import json
import random
from pathlib import Path

from .common import EPSILON, DEFAULT_STRATEGY, STRATEGIES, sha256_text


def _key(feature_signature: "tuple[str, str]") -> str:
    # tuples aren't valid JSON object keys; a fixed, reversible string form
    return f"{feature_signature[0]}|{feature_signature[1]}"


class Selector:
    def __init__(self):
        self.state: dict = {}  # _key(sig) -> {strategy: {"count":int, "mean":float}}

    @classmethod
    def load(cls, path: str) -> "Selector":
        s = cls()
        p = Path(path)
        if p.exists():
            s.state = json.loads(p.read_text(encoding="utf-8"))
        return s

    def content_hash(self) -> str:
        # canonical: sorted keys, no whitespace -- identical bytes for
        # identical logical state regardless of dict insertion order
        return sha256_text(json.dumps(self.state, sort_keys=True, separators=(",", ":")))

    def save(self, path: str) -> str:
        """Writes state to `path` (atomic replace) and returns its content
        hash. Called explicitly by the harness controller, never implicitly
        inside select()/update() -- so a caller controls exactly when a
        checkpoint is taken (needed for S0/S1 semantics in §13)."""
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(p.suffix + ".tmp")
        tmp.write_text(json.dumps(self.state, sort_keys=True, separators=(",", ":")), encoding="utf-8")
        tmp.replace(p)
        return self.content_hash()

    def select(self, feature_signature: "tuple[str, str]", *, explore: bool, rng: random.Random) -> "tuple[str, float]":
        """Returns (strategy_name, selection_probability). explore=True is
        the PROSPECTIVE-phase epsilon-greedy rule; explore=False is the
        HOLDOUT-phase pure-greedy rule (no exploration -- measures the
        policy's real performance, not further learning), per the frozen
        design's own §14 requirement."""
        k = _key(feature_signature)
        bucket = self.state.get(k, {})
        observed = {s: v for s, v in bucket.items() if v.get("count", 0) > 0}

        if not observed:
            return DEFAULT_STRATEGY, 1.0

        best = max(observed.items(), key=lambda kv: kv[1]["mean"])[0]

        if not explore:
            return best, 1.0

        if rng.random() < EPSILON:
            choice = rng.choice(STRATEGIES)
            prob = EPSILON / len(STRATEGIES) + (1 - EPSILON if choice == best else 0.0)
            return choice, prob
        return best, (1 - EPSILON) + EPSILON / len(STRATEGIES)

    def update(self, feature_signature: "tuple[str, str]", strategy_used: str, outcome: bool) -> "tuple[str, str]":
        """Sanitized-feedback contract, enforced by signature: outcome MUST
        be a plain bool. Returns (pre_state_hash, post_state_hash) -- the
        exact pair Section 10's U record needs, and the exact mechanism
        that makes a no-op update (Arm B) mechanically verifiable as
        pre==post for every call, not merely asserted from a 'disabled'
        flag."""
        if not isinstance(outcome, bool):
            raise TypeError(
                f"update() requires a plain bool outcome (sanitized-feedback contract, "
                f"PREREG §6) -- got {type(outcome).__name__}. This is a hard failure, not "
                f"a silent coercion, because any richer value here would be a real leak."
            )
        pre = self.content_hash()
        k = _key(feature_signature)
        bucket = self.state.setdefault(k, {})
        cell = bucket.setdefault(strategy_used, {"count": 0, "mean": 0.5})
        cell["count"] += 1
        score = 1.0 if outcome else 0.0
        cell["mean"] += (score - cell["mean"]) / cell["count"]
        post = self.content_hash()
        return pre, post


def extract_sanitized_outcome(grade_result: dict) -> bool:
    """The ONE place `oracle_runner.grade()`'s real return dict is touched
    before anything reaches update() -- pulls `passed` only, discards
    output_tail/error_tail/duration/everything else. A future call site
    that tries to pass the raw grade dict to Selector.update() gets a
    TypeError (above), not a silent leak -- this function is the required
    detour."""
    return bool(grade_result["passed"])
