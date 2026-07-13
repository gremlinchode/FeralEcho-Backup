# app/core/task_type_classifier.py
"""
Online, learned secondary signal for task-type classification — audit
finding (High #16): compute_intent_heatmap()/detect_task_type() in
echo_model_orchestrator.py are 100% keyword substring matching, the single
most consequential routing decision in the system (drives council
composition, per-task token budget, tool-list injection, and the
DIRECT_ECHO_TASKS bypass) with no model-based or learned classification
step anywhere.

Design (full reasoning in .claude/plans/dynamic-meandering-stream.md):
- NOT an LLM call — every request would pay a full round-trip before real
  work starts, and it's circular (which model classifies before you know
  which model to use?).
- NOT a replacement for the keyword heatmap, which stays the free, instant
  primary signal. This classifier only activates inside
  detect_task_type()'s fallback path (low keyword confidence, or the two
  entry points — execute_self_edit(), run.py's mirror_echo() — that call
  detect_task_type() directly and never see the heatmap at all today).
- river-based (river is already a hard dependency of this codebase,
  already powering RiverBrain's quality-score learning) — BagOfWords +
  MultinomialNB gives calibrated per-class probabilities for free, which
  the trust-gating below needs, reusing infrastructure this codebase
  already trusts rather than a hand-rolled scheme.
- Trust-gated per class, reasoned from the real historical distribution in
  memory/interaction_log.jsonl (personal:5263, coding:3471, general:73,
  creative:23, reasoning:22 out of 9,174 usable rows) — creative/reasoning
  are far too sparse to trust yet and will correctly stay on the keyword
  ladder until real conversational traffic accumulates enough examples.
  This is an intended, conservative near-term behavior, not a bug.

Every public method fails open (returns a safe default, never raises) —
this sits on the hottest path in the system (every real conversation
calls detect_task_type() or resolve_task_type()), so a bug here must
never block a response.

Deliberately standalone (only river/json/os/logging/pickle imports), not
folded into echo_model_orchestrator.py — that file runs a real
`subprocess.run(["ollama", "list"])` at import time, which would make
direct-load testing of this module require a running Ollama for no reason.
"""
import json
import logging
import os
import pickle

logger = logging.getLogger(__name__)

try:
    from river import feature_extraction, naive_bayes, compose
    RIVER_TEXT_AVAILABLE = True
except Exception:
    RIVER_TEXT_AVAILABLE = False

try:
    import fcntl
    _FCNTL_AVAILABLE = True
except Exception:
    _FCNTL_AVAILABLE = False


TASK_TYPES = ("coding", "personal", "general", "creative", "reasoning")

# Trust-gating thresholds. IMPORTANT CORRECTION from initial design: the
# raw interaction_log.jsonl class counts (personal:5263, coding:3471,
# general:73, creative:23, reasoning:22) include every source — autonomous
# self-talk, self-edit planning prompts, sandbox placeholders. Once
# is_trustworthy_training_example() correctly restricts bootstrap to real
# source=="user_conversation" examples (see that function's comment for
# why this filter exists at all), the REAL clean counts are far smaller:
# personal:135, coding:29, general:21, reasoning:11, creative:7 (measured
# live against the actual log). At these thresholds, NO class is trusted
# at bootstrap — the classifier starts fully deferring to the keyword
# ladder for everything and only gradually earns trust as real
# conversational traffic accumulates through the online learn() hook.
# This is intended and conservative, not a bug: a weak BagOfWords+NB model
# trained on a couple dozen clean examples was empirically confirmed (see
# _MIN_CONFIDENCE's comment) to still produce confidently wrong answers on
# clear-cut cases the keyword ladder already gets right — better to wait
# for real signal than activate early on too little clean data.
_MIN_OBSERVATIONS = {
    "coding": 200,
    "personal": 200,
    "general": 30,
    "creative": 30,
    "reasoning": 30,
}
# Confirmed live: even after class-balancing (_MAX_MODEL_EXAMPLES_PER_CLASS
# below), a weak BagOfWords+NB model with limited real data still produces
# marginal, only-slightly-above-random confidence for genuinely ambiguous
# input (5-class random baseline is 0.2; "write a poem about the sea"
# scored 0.508 for "personal" post-balancing, which should be "creative").
# 0.6 is meaningfully more discriminating than that while still comfortably
# passing clearly-confident correct cases (e.g. "fix this python bug"
# scored 0.99 for "coding"). Below this bar, falling through to the
# keyword ladder is the safer choice — it already handles both of the
# above examples correctly on its own.
_MIN_CONFIDENCE = 0.6

# Hard cap on how many examples of any single class actually get fed to the
# underlying MultinomialNB, independent of observation_counts (which still
# tracks the TRUE total, used for is_well_observed()'s trust-gating below).
# Confirmed live during implementation: without this, the real bootstrap
# data's severe class imbalance (personal:5263 vs reasoning:22) let the
# model's class prior alone push "personal" to 85-98% confidence for
# nearly ANY input — including clearly non-personal text like "write a
# poem about the sea" (98% "personal") and "hello" (94% "coding", the
# second-largest class) — a real regression that would have made routing
# worse than the keyword-only baseline, not better. Capping keeps the
# model's actual training set close to balanced regardless of how skewed
# real traffic is; creative/reasoning (22-23 real examples each) are far
# below this cap so they're unaffected — every real example they have
# still gets learned.
_MAX_MODEL_EXAMPLES_PER_CLASS = 100

# Shared training-example filter, reused by both bootstrap_from_log()
# (replaying history) and echo_model_orchestrator.py's log_interaction()
# feedback hook (real-time learning) — a single source of truth so the two
# paths can never drift out of sync. Confirmed live during implementation:
# before this filter existed on the bootstrap side, bootstrap_from_log()
# was replaying EVERY historical (prompt, task_type) pair regardless of
# `source`, which meant internal self-edit planning prompts ("STRICT
# OUTPUT RULES — violations cause system failure...", average 3,751 chars
# for "coding"-tagged entries) and literal placeholders ("[SANDBOX]",
# "fetch_cycle_N", tool-result dumps) were trained as if they were genuine
# short user coding questions — the real root cause of the classifier
# learning garbage patterns (e.g. confidently mis-routing "hello" and
# "how do you feel about your identity"), not merely class imbalance.
_PLACEHOLDER_PROMPTS = {"[SANDBOX]"}
_PLACEHOLDER_PREFIXES = ("fetch_cycle_", "STRICT OUTPUT RULES", "[Tool result")
_MAX_TRAINING_PROMPT_LEN = 500  # real user messages are short; internal
# system/pipeline prompts run into the thousands of characters (confirmed
# live: avg 3,751 chars for contaminated "coding" entries).


def is_trustworthy_training_example(prompt, task_type, source) -> bool:
    """True only for genuine, real-user, real-derived-from-text examples
    safe to train the classifier on."""
    if task_type not in TASK_TYPES or not prompt:
        return False
    if source != "user_conversation":
        return False
    if prompt in _PLACEHOLDER_PROMPTS:
        return False
    if any(prompt.startswith(p) for p in _PLACEHOLDER_PREFIXES):
        return False
    if len(prompt) > _MAX_TRAINING_PROMPT_LEN:
        return False
    return True


_CLASSIFIER_PATH = os.path.join("memory", "task_type_classifier.pkl")
_DEFAULT_LOG_PATH = os.path.join("memory", "interaction_log.jsonl")
# Periodic flush rather than a write on every learn() call — mirrors this
# codebase's own _RATING_FLUSH_INTERVAL pattern in echo_model_orchestrator.py
# (periodic-flush-by-counter), avoiding a disk write + flock on every single
# real conversation, which sits in the hot request path.
_SAVE_EVERY_N_LEARNS = 20


class TaskTypeClassifier:
    def __init__(self):
        self.observation_counts: dict = {t: 0 for t in TASK_TYPES}
        # How many examples of each class were actually fed to self._model,
        # separate from observation_counts — see _MAX_MODEL_EXAMPLES_PER_CLASS.
        self._model_learn_counts: dict = {t: 0 for t in TASK_TYPES}
        self._learn_count_since_save = 0
        self._model = self._build_model() if RIVER_TEXT_AVAILABLE else None

    @staticmethod
    def _build_model():
        return compose.Pipeline(
            feature_extraction.BagOfWords(on=None, strip_accents=True),
            naive_bayes.MultinomialNB(),
        )

    def predict(self, prompt: str) -> tuple:
        """Returns (label, confidence) or (None, 0.0). Never raises.
        None means "not trusted yet" — caller should fall back to the
        keyword ladder, not treat this as an error."""
        if not RIVER_TEXT_AVAILABLE or self._model is None or not prompt:
            return None, 0.0
        try:
            proba = self._model.predict_proba_one(prompt)
            if not proba:
                return None, 0.0
            label = max(proba, key=proba.get)
            confidence = proba[label]
            if label not in TASK_TYPES:
                return None, 0.0
            if not self.is_well_observed(label):
                return None, 0.0
            if confidence < _MIN_CONFIDENCE:
                return None, 0.0
            return label, confidence
        except Exception as e:
            logger.debug(f"[TASK_TYPE_CLASSIFIER] predict failed: {e}")
            return None, 0.0

    def learn(self, prompt: str, task_type: str) -> None:
        """No-op if task_type isn't one of the 5 real types or river is
        unavailable. Never raises.

        observation_counts is always incremented (true total, drives trust-
        gating) but the example is only fed to the model itself while that
        class is below _MAX_MODEL_EXAMPLES_PER_CLASS — see that constant's
        comment for why this matters (class-imbalance bias in the prior)."""
        if not RIVER_TEXT_AVAILABLE or self._model is None:
            return
        if task_type not in TASK_TYPES or not prompt:
            return
        try:
            self.observation_counts[task_type] = self.observation_counts.get(task_type, 0) + 1
            if self._model_learn_counts.get(task_type, 0) < _MAX_MODEL_EXAMPLES_PER_CLASS:
                self._model.learn_one(prompt, task_type)
                self._model_learn_counts[task_type] = self._model_learn_counts.get(task_type, 0) + 1
            self._learn_count_since_save += 1
            if self._learn_count_since_save >= _SAVE_EVERY_N_LEARNS:
                self.save()
                self._learn_count_since_save = 0
        except Exception as e:
            logger.debug(f"[TASK_TYPE_CLASSIFIER] learn failed: {e}")

    def is_well_observed(self, task_type: str) -> bool:
        floor = _MIN_OBSERVATIONS.get(task_type, 30)
        return self.observation_counts.get(task_type, 0) >= floor

    def bootstrap_from_log(self, log_path: str = _DEFAULT_LOG_PATH) -> int:
        """One-time replay of historical (prompt, task_type) pairs from
        interaction_log.jsonl, filtered through is_trustworthy_training_example()
        — only genuine source=="user_conversation" examples count; the vast
        majority of raw log lines (autonomous self-talk, self-edit planning
        prompts, sandbox placeholders) are correctly excluded. Returns the
        count actually learned. Safe and idempotent to call again later
        (just adds more training signal). Never raises — a failure here
        must not block classifier startup."""
        if not RIVER_TEXT_AVAILABLE or self._model is None:
            return 0
        learned = 0
        try:
            if not os.path.exists(log_path):
                return 0
            with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                    except Exception:
                        continue
                    task_type = entry.get("task_type")
                    prompt = entry.get("prompt")
                    source = entry.get("source")
                    if not is_trustworthy_training_example(prompt, task_type, source):
                        continue
                    self.learn(prompt, task_type)
                    learned += 1
        except Exception as e:
            logger.warning(f"[TASK_TYPE_CLASSIFIER] bootstrap_from_log failed: {e}")
            return learned
        logger.info(f"[TASK_TYPE_CLASSIFIER] Bootstrapped {learned} examples from {log_path}")
        return learned

    def save(self) -> None:
        """Concurrency-safe persistence — mirrors RiverBrain._do_save()'s
        flock + "never overwrite richer state" guard exactly (same class of
        bug already paid down once for RiverBrain in this codebase;
        skipping this guard here would reintroduce it for a second
        singleton)."""
        if not RIVER_TEXT_AVAILABLE or self._model is None:
            return
        try:
            snapshot = {
                "model": self._model,
                "observation_counts": dict(self.observation_counts),
                "model_learn_counts": dict(self._model_learn_counts),
            }
            os.makedirs(os.path.dirname(_CLASSIFIER_PATH), exist_ok=True)
            lock_path = _CLASSIFIER_PATH + ".lock"
            if _FCNTL_AVAILABLE:
                with open(lock_path, "w") as lock_file:
                    fcntl.flock(lock_file, fcntl.LOCK_EX)
                    try:
                        self._write_if_richer(snapshot)
                    finally:
                        fcntl.flock(lock_file, fcntl.LOCK_UN)
            else:
                self._write_if_richer(snapshot)
        except Exception as e:
            logger.warning(f"[TASK_TYPE_CLASSIFIER] save failed: {e}")

    def _write_if_richer(self, snapshot: dict) -> None:
        current_obs = sum(snapshot["observation_counts"].values())
        if os.path.exists(_CLASSIFIER_PATH):
            try:
                with open(_CLASSIFIER_PATH, "rb") as existing:
                    existing_data = pickle.load(existing)
                existing_obs = sum(existing_data.get("observation_counts", {}).values())
                if existing_obs > current_obs:
                    logger.warning(
                        f"[TASK_TYPE_CLASSIFIER] Save skipped — disk has {existing_obs} obs, "
                        f"instance has {current_obs}. Refusing to overwrite richer pkl."
                    )
                    return
            except Exception:
                pass
        with open(_CLASSIFIER_PATH, "wb") as f:
            pickle.dump(snapshot, f)
        logger.info(f"[TASK_TYPE_CLASSIFIER] Persisted | total_obs={current_obs}")

    @classmethod
    def load(cls) -> "TaskTypeClassifier":
        instance = cls()
        if not RIVER_TEXT_AVAILABLE:
            return instance
        if not os.path.exists(_CLASSIFIER_PATH):
            logger.info(
                "[TASK_TYPE_CLASSIFIER] No persisted state found — bootstrapping from interaction log"
            )
            instance.bootstrap_from_log()
            instance.save()
            return instance
        try:
            lock_path = _CLASSIFIER_PATH + ".lock"
            if _FCNTL_AVAILABLE:
                with open(lock_path, "w") as lock_file:
                    fcntl.flock(lock_file, fcntl.LOCK_SH)
                    try:
                        with open(_CLASSIFIER_PATH, "rb") as f:
                            data = pickle.load(f)
                    finally:
                        fcntl.flock(lock_file, fcntl.LOCK_UN)
            else:
                with open(_CLASSIFIER_PATH, "rb") as f:
                    data = pickle.load(f)
            instance._model = data["model"]
            instance.observation_counts = dict(data.get("observation_counts", {}))
            instance._model_learn_counts = dict(data.get("model_learn_counts", {}))
            logger.info(
                f"[TASK_TYPE_CLASSIFIER] Loaded persisted state | "
                f"total_obs={sum(instance.observation_counts.values())}"
            )
        except Exception as e:
            logger.warning(f"[TASK_TYPE_CLASSIFIER] Load failed, starting fresh: {e}")
        return instance


_instance = None


def get_task_type_classifier() -> TaskTypeClassifier:
    """Lazy singleton, mirrors get_river_brain()'s pattern exactly."""
    global _instance
    if _instance is None:
        _instance = TaskTypeClassifier.load()
    return _instance
