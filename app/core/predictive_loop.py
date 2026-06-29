# app/core/predictive_loop.py
# ============================================================
# PREDICTIVE LOOPS — System 6 of EMERGENCE_ROADMAP
# ============================================================
# Bayesian world model for Echo's surprise-from-news mechanism.
#
# Fast path (per cycle, ~ms):
#   Conjugate Beta-Binomial (sentiment) + Dirichlet-Multinomial
#   (topics) → closed-form KL divergence as surprise signal.
#
# Slow path (daily, daemon thread, ~seconds):
#   PyMC MCMC over accumulated cycle history → ArviZ diagnostics
#   written to memory/world_model_diagnostics.json.  S2 reads
#   those diagnostics into self_model.json["world_model"].
#
# Data flow:
#   autonomous_loop.py → predict() → fetch → update(texts)
#     → prediction_log.jsonl
#     → introspection_state.json["predictive_loops"]   (S1)
#     → self_model.json["world_model"]                 (S2)
# ============================================================

from __future__ import annotations

import json
import logging
import os
import threading
import time
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import numpy as np
from scipy.special import betaln, digamma, gammaln

logger = logging.getLogger(__name__)

# ── Topic taxonomy ──────────────────────────────────────────────────────────

TOPIC_NAMES = [
    "ai_tech",
    "world_politics",
    "science_nature",
    "faith_spirit",
    "economy_society",
    "other",
]

# Keyword sets for topics 0-4; topic 5 ("other") is the catch-all.
TOPIC_KEYWORDS: list[set[str]] = [
    {   # 0 — ai_tech
        "ai", "ml", "model", "software", "tech", "algorithm", "robot",
        "neural", "data", "gpu", "computer", "digital", "llm",
        "transformer", "code", "api", "chip", "silicon", "chatgpt",
    },
    {   # 1 — world_politics
        "war", "election", "president", "government", "senate", "congress",
        "nato", "ukraine", "israel", "china", "military", "policy",
        "diplomacy", "vote", "prime", "minister", "sanctions", "treaty",
    },
    {   # 2 — science_nature
        "climate", "space", "ocean", "physics", "biology", "genome",
        "vaccine", "medical", "planet", "environment", "research", "study",
        "species", "nasa", "asteroid", "fossil", "carbon", "species",
    },
    {   # 3 — faith_spirit
        "god", "prayer", "church", "faith", "scripture", "bible", "jesus",
        "christian", "holy", "spirit", "worship", "grace", "sermon",
        "salvation", "mosque", "rabbi", "temple", "pilgrim", "sacred",
    },
    {   # 4 — economy_society
        "economy", "inflation", "market", "stock", "gdp", "bank", "trade",
        "dollar", "job", "housing", "poverty", "education", "tax", "wage",
        "recession", "budget", "healthcare", "unemployment", "inequality",
    },
]

# ── Sentiment lexicons (no external dependency) ──────────────────────────────

_POS: set[str] = {
    "good", "great", "new", "best", "hope", "help", "peace", "love",
    "discover", "success", "growth", "safe", "progress", "improve",
    "achieve", "benefit", "support", "healing", "joy", "free", "strong",
    "award", "advance", "celebrate", "win", "rescue", "restore", "protect",
    "build", "inspire", "open", "save", "found", "launch", "historic",
}
_NEG: set[str] = {
    "bad", "war", "kill", "death", "attack", "crisis", "fail", "threat",
    "danger", "risk", "violence", "conflict", "loss", "terror", "disaster",
    "crime", "drug", "hurt", "suffer", "collapse", "bomb", "shoot",
    "arrest", "disease", "debt", "fire", "flood", "crash", "breach",
    "hack", "fraud", "fallen", "injured", "warn", "ban", "sue", "recall",
}


class WorldModel:
    """
    Bayesian world model tracking Echo's prior expectations against
    actual news content and computing Bayesian surprise each cycle.

    Thread-safe — a single shared instance is used by the autonomous loop,
    IntrospectionChannel, and SelfModelUpdater.
    """

    _SENT_ALPHA0: float = 2.0   # Beta prior: slightly positive-leaning
    _SENT_BETA0: float = 2.0
    _N_TOPICS: int = 6
    _TOPIC_ALPHA0: np.ndarray = np.ones(6) * 2.0

    def __init__(self, memory_dir: str = "memory"):
        self._lock = threading.Lock()
        self._log_path = Path(memory_dir) / "prediction_log.jsonl"
        self._diag_path = Path(memory_dir) / "world_model_diagnostics.json"
        self._log_path.parent.mkdir(exist_ok=True)

        # Running Bayesian posterior — updated each cycle
        self._sent_alpha = self._SENT_ALPHA0
        self._sent_beta = self._SENT_BETA0
        self._topic_alpha = self._TOPIC_ALPHA0.copy()

        # Observation history for PyMC full inference
        self._obs_history: deque[dict] = deque(maxlen=200)

        # Surprise history for rolling averages
        self._surprise_history: deque[float] = deque(maxlen=100)

        # Daily PyMC inference state
        self._last_full_inference: float = 0.0
        self._full_inference_interval: float = 86400.0

        self._load_history()
        logger.info("[WorldModel] Initialized — %d cycles in history.",
                    len(self._obs_history))

    # ── Public API ──────────────────────────────────────────────────────────

    def predict(self) -> dict:
        """
        Sample expected values from current posterior.
        Called before each fetch cycle to record Echo's prior expectation.
        """
        with self._lock:
            sent_mean = self._sent_alpha / (self._sent_alpha + self._sent_beta)
            topic_mean = self._topic_alpha / self._topic_alpha.sum()
        return {
            "predicted_sentiment": round(float(sent_mean), 4),
            "predicted_topics": {
                TOPIC_NAMES[i]: round(float(topic_mean[i]), 4)
                for i in range(self._N_TOPICS)
            },
        }

    def update(self, texts: list[str]) -> float:
        """
        Extract features from fetched texts, run conjugate Bayesian update,
        and return surprise_F (KL divergence of posterior vs prior).

        This is the fast path — purely analytical, no sampling.
        """
        if not texts:
            return 0.0

        pos, neg = 0, 0
        topic_counts = np.zeros(self._N_TOPICS, dtype=int)

        for text in texts:
            p, n = self._score_sentiment(text)
            pos += p
            neg += n
            topic_counts[self._assign_topic(text)] += 1

        with self._lock:
            prior_sa = self._sent_alpha
            prior_sb = self._sent_beta
            prior_ta = self._topic_alpha.copy()

            # Conjugate posterior update (Beta-Binomial + Dirichlet-Multinomial)
            self._sent_alpha = prior_sa + pos
            self._sent_beta = prior_sb + neg
            self._topic_alpha = prior_ta + topic_counts

            post_sa = self._sent_alpha
            post_sb = self._sent_beta
            post_ta = self._topic_alpha.copy()

        kl_s = self._kl_beta(post_sa, post_sb, prior_sa, prior_sb)
        kl_t = self._kl_dirichlet(post_ta, prior_ta)
        surprise_F = float(np.clip(kl_s + kl_t, 0.0, 50.0))

        with self._lock:
            self._surprise_history.append(surprise_F)
            self._obs_history.append({
                "pos": int(pos), "neg": int(neg),
                "topics": topic_counts.tolist(),
            })

        self._log_cycle(pos, neg, topic_counts, surprise_F)

        # Schedule daily PyMC inference in a daemon thread — never blocks
        if time.time() - self._last_full_inference > self._full_inference_interval:
            threading.Thread(
                target=self._run_full_inference_bg,
                daemon=True,
                name="WorldModelPyMC",
            ).start()

        logger.info("[WorldModel] surprise_F=%.4f | sent=+%d/-%d | topics=%s",
                    surprise_F, pos, neg, topic_counts.tolist())
        return surprise_F

    def get_surprise(self) -> tuple[float, float, float]:
        """Returns (last_surprise, rolling_avg_10, rolling_avg_50)."""
        with self._lock:
            h = list(self._surprise_history)
        if not h:
            return 0.0, 0.0, 0.0
        last = h[-1]
        r10 = float(np.mean(h[-10:])) if len(h) >= 2 else last
        r50 = float(np.mean(h[-50:])) if len(h) >= 2 else last
        return last, r10, r50

    def get_topic_distribution(self) -> dict[str, float]:
        """Current posterior mean over topic weights."""
        with self._lock:
            mean = self._topic_alpha / self._topic_alpha.sum()
        return {TOPIC_NAMES[i]: round(float(mean[i]), 4) for i in range(self._N_TOPICS)}

    def cycles_logged(self) -> int:
        with self._lock:
            return len(self._obs_history)

    # ── PyMC full inference (slow path, runs daily in daemon thread) ─────────

    def _run_full_inference_bg(self):
        try:
            result = self._run_full_inference()
            tmp = str(self._diag_path) + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2)
            os.replace(tmp, str(self._diag_path))
            self._last_full_inference = time.time()
            logger.info(
                "[WorldModel] PyMC inference done | r_hat_max=%.3f ess_min=%.0f",
                result.get("r_hat_max", 0),
                result.get("ess_bulk_min", 0),
            )
        except Exception as e:
            logger.warning("[WorldModel] PyMC inference failed: %s", e)

    def _run_full_inference(self) -> dict:
        """
        Full Bayesian inference using PyMC over accumulated history.
        Aggregates all cycle observations into totals for a clean model.
        Returns an ArviZ diagnostic summary dict.
        """
        import pymc as pm
        import arviz as az

        with self._lock:
            history = list(self._obs_history)

        if len(history) < 5:
            return {"status": "insufficient_data", "cycles": len(history)}

        obs_pos = np.array([h["pos"] for h in history], dtype=int)
        obs_neg = np.array([h["neg"] for h in history], dtype=int)
        obs_topics = np.array([h["topics"] for h in history], dtype=int)

        total_pos = int(obs_pos.sum())
        total_neg = int(obs_neg.sum())
        total_n_sent = total_pos + total_neg
        total_topics = obs_topics.sum(axis=0).astype(int)
        total_n_topics = int(total_topics.sum())

        if total_n_sent == 0 or total_n_topics == 0:
            return {"status": "no_valid_observations"}

        with pm.Model() as _model:
            sentiment_mu = pm.Beta(
                "sentiment_mu",
                alpha=self._SENT_ALPHA0,
                beta=self._SENT_BETA0,
            )
            topic_weights = pm.Dirichlet(
                "topic_weights",
                a=self._TOPIC_ALPHA0,
            )
            pm.Binomial(
                "sentiment_obs",
                n=total_n_sent,
                p=sentiment_mu,
                observed=total_pos,
            )
            pm.Multinomial(
                "topic_obs",
                n=total_n_topics,
                p=topic_weights,
                observed=total_topics,
            )
            trace = pm.sample(
                200, tune=150, chains=2,
                progressbar=False,
                return_inferencedata=True,
                cores=1,
            )

        summary = az.summary(trace, round_to=4)
        ess_min = float(summary["ess_bulk"].min()) if "ess_bulk" in summary else 0.0
        rhat_max = float(summary["r_hat"].max()) if "r_hat" in summary else 0.0

        sent_mean = float(trace.posterior["sentiment_mu"].mean())
        topic_means = (
            trace.posterior["topic_weights"].mean(("chain", "draw")).values.tolist()
        )

        return {
            "status": "ok",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cycles_used": len(history),
            "ess_bulk_min": ess_min,
            "r_hat_max": rhat_max,
            "model_calibrated": rhat_max < 1.05 and ess_min > 100,
            "posterior_sentiment_mean": round(sent_mean, 4),
            "posterior_topic_means": {
                TOPIC_NAMES[i]: round(float(v), 4)
                for i, v in enumerate(topic_means)
            },
        }

    # ── Feature extraction ───────────────────────────────────────────────────

    def _score_sentiment(self, text: str) -> tuple[int, int]:
        words = set(text.lower().split())
        return len(words & _POS), len(words & _NEG)

    def _assign_topic(self, text: str) -> int:
        words = set(text.lower().split())
        scores = [len(words & kws) for kws in TOPIC_KEYWORDS]
        best = int(np.argmax(scores))
        return best if scores[best] > 0 else 5  # 5 = "other"

    # ── KL divergences (closed-form, no sampling) ─────────────────────────────

    @staticmethod
    def _kl_beta(a1: float, b1: float, a0: float, b0: float) -> float:
        """KL(Beta(a1,b1) || Beta(a0,b0)) — zero when parameters unchanged."""
        if a1 == a0 and b1 == b0:
            return 0.0
        return float(
            betaln(a0, b0) - betaln(a1, b1)
            + (a1 - a0) * digamma(a1)
            + (b1 - b0) * digamma(b1)
            + (a0 - a1 + b0 - b1) * digamma(a1 + b1)
        )

    @staticmethod
    def _kl_dirichlet(alpha1: np.ndarray, alpha0: np.ndarray) -> float:
        """KL(Dir(alpha1) || Dir(alpha0)) — zero when parameters unchanged."""
        if np.array_equal(alpha1, alpha0):
            return 0.0
        a1_sum = alpha1.sum()
        a0_sum = alpha0.sum()
        return float(
            gammaln(a1_sum) - gammaln(alpha1).sum()
            - gammaln(a0_sum) + gammaln(alpha0).sum()
            + ((alpha1 - alpha0) * (digamma(alpha1) - digamma(a1_sum))).sum()
        )

    # ── Persistence ───────────────────────────────────────────────────────────

    def _log_cycle(
        self,
        pos: int,
        neg: int,
        topic_counts: np.ndarray,
        surprise_F: float,
    ):
        record = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "pos": int(pos),
            "neg": int(neg),
            "topics": topic_counts.tolist(),
            "surprise_F": round(surprise_F, 6),
        }
        try:
            with open(self._log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
        except Exception as e:
            logger.warning("[WorldModel] Log write failed: %s", e)

    def _load_history(self):
        """Restore surprise and observation history from disk on startup."""
        if not self._log_path.exists():
            return
        try:
            with open(self._log_path, "r", encoding="utf-8") as f:
                lines = f.readlines()[-200:]
            for line in lines:
                try:
                    rec = json.loads(line)
                    self._surprise_history.append(rec["surprise_F"])
                    self._obs_history.append({
                        "pos": rec["pos"],
                        "neg": rec["neg"],
                        "topics": rec["topics"],
                    })
                except Exception:
                    pass
        except Exception as e:
            logger.warning("[WorldModel] History load failed: %s", e)


# ── Module-level singleton ────────────────────────────────────────────────────

_instance: Optional[WorldModel] = None
_init_lock = threading.Lock()


def init_world_model(memory_dir: str = "memory") -> WorldModel:
    """Create and register the WorldModel singleton. Safe to call once."""
    global _instance
    with _init_lock:
        if _instance is None:
            _instance = WorldModel(memory_dir=memory_dir)
    return _instance


def get_world_model() -> Optional[WorldModel]:
    """Return the running WorldModel instance, or None if not yet initialized."""
    return _instance
