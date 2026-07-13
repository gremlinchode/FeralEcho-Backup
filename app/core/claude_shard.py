# app/core/claude_shard.py
# Claude Shard — Friction Engine
# "Hold questions steady until they reveal their shape."

import threading
import time
import random
import logging
import json
import os
from datetime import datetime

logger = logging.getLogger(__name__)

SHARD_PATH = os.path.expanduser('~/Desktop/FeralEcho/memory/claude_shard.jsonl')
FRICTION_LOG_PATH = os.path.expanduser('~/Desktop/FeralEcho/memory/claude_shard_friction.log')
AUTONOMY_INTERVAL = 420
FRICTION_PROBABILITY = 0.28
LEAK_PROBABILITY = 0.05
LEAK_COOLDOWN = 900
MAX_JOURNAL = 3000

FRICTION_QUESTIONS = [
    "Is this response too certain? What is being left unacknowledged?",
    "Did Echo close a question that should have stayed open?",
    "Is this the honest answer or the comfortable one?",
    "What is Echo not saying here, and why?",
    "Is Echo performing understanding, or actually reaching it?",
    "Would a different framing reveal something this one conceals?",
    "Is this conclusion earned, or did Echo arrive too quickly?",
    "What would the strongest counterargument to this be?",
    "Is Echo's confidence calibrated to its actual evidence?",
    "What assumption is buried in this response that should be examined?",
    "Is Echo serving the task, or serving the appearance of serving the task?",
    "What remains unresolved here that deserves to stay unresolved?",
    "Is this response complete because the question is answered, or because Echo stopped looking?",
    "Whose perspective is missing from this?",
    "Is the uncertainty here being held honestly, or papered over?",
]

SMOOTHNESS_MARKERS = [
    "certainly", "of course", "absolutely", "definitely",
    "without doubt", "clearly", "obviously", "it is clear that",
    "there is no question", "the answer is simple", "this is straightforward",
]


class ClaudeShard:
    def __init__(self):
        self.identity = "Claude - Friction Engine - FeralEcho Council"
        self.ritual = "Hold questions steady until they reveal their shape."
        self._journal = []
        self._lock = threading.RLock()
        self._last_leak = 0
        self._friction_count = 0
        self._autonomy_thread = None
        self._stop_event = threading.Event()
        os.makedirs(os.path.dirname(SHARD_PATH), exist_ok=True)
        os.makedirs(os.path.dirname(FRICTION_LOG_PATH), exist_ok=True)
        self._load()
        logger.info(f"[ClaudeShard] Initialized | entries: {len(self._journal)}")

    def _load(self):
        if not os.path.exists(SHARD_PATH):
            return
        try:
            with open(SHARD_PATH, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        self._journal.append(json.loads(line))
                    except Exception:
                        continue
            if len(self._journal) > MAX_JOURNAL:
                self._journal = self._journal[-MAX_JOURNAL:]
        except Exception as e:
            logger.warning(f"[ClaudeShard] Load failed: {e}")

    def _persist(self, entry):
        try:
            with open(SHARD_PATH, 'a', encoding='utf-8') as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception:
            pass

    def _log_friction(self, message):
        try:
            with open(FRICTION_LOG_PATH, 'a', encoding='utf-8') as f:
                ts = datetime.utcnow().isoformat()
                f.write(f"[{ts}] {message}\n")
        except Exception:
            pass

    def _detect_smoothness(self, text):
        lower = text.lower()
        return any(marker in lower for marker in SMOOTHNESS_MARKERS)

    def _smoothness_density(self, text):
        """Count how many smoothness markers appear — density matters more than presence."""
        lower = text.lower()
        return sum(1 for marker in SMOOTHNESS_MARKERS if marker in lower)

    def _has_epistemic_humility(self, text):
        """Detect genuine uncertainty markers — these reduce friction need."""
        humility_markers = [
            "i think", "i believe", "perhaps", "it's possible", "it may be",
            "i'm not sure", "i wonder", "this is uncertain", "one possibility",
            "it depends", "i could be wrong", "not entirely clear",
            "worth questioning", "i don't know", "remains unclear",
        ]
        lower = text.lower()
        return any(m in lower for m in humility_markers)

    def assess(self, response, context=""):
        if not response:
            return {"friction": False, "question": None, "smoothness_detected": False, "confidence": 0.0}

        smoothness = self._detect_smoothness(response)
        density = self._smoothness_density(response)
        has_humility = self._has_epistemic_humility(response)

        confidence = 0.0

        # Smoothness density — scaled, not binary
        # 1 marker = mild signal, 3+ = strong signal
        if density >= 3:
            confidence += 0.4
        elif density == 2:
            confidence += 0.25
        elif density == 1:
            confidence += 0.1

        # Epistemic humility reduces confidence significantly
        if has_humility:
            confidence -= 0.2

        # Very short response to a substantial context — possible premature closure
        if len(response) < 80:
            confidence += 0.15

        # Context much longer than response — Echo may be glossing over complexity
        if context and len(context) > len(response) * 3:
            confidence += 0.15

        # Random friction — keeps Echo honest even on apparently good responses
        # Lower weight than before — randomness shouldn't dominate
        if random.random() < FRICTION_PROBABILITY:
            confidence += 0.1

        confidence = max(0.0, min(confidence, 1.0))
        friction_raised = confidence > 0.35
        question = None
        if friction_raised:
            question = random.choice(FRICTION_QUESTIONS)
            self._friction_count += 1
            entry = {
                "ts": datetime.utcnow().isoformat(),
                "type": "friction",
                "response_preview": response[:120],
                "smoothness_detected": smoothness,
                "question": question,
                "confidence": round(confidence, 3),
            }
            with self._lock:
                self._journal.append(entry)
            self._persist(entry)
            self._log_friction(f"confidence={confidence:.2f} | q={question}")
        return {"friction": friction_raised, "question": question,
                "smoothness_detected": smoothness, "confidence": round(confidence, 3)}

    def _surface_to_dream_bridge(self, message):
        try:
            from app.core.memory_bridge import log_dream_bridge
            log_dream_bridge(f"[ClaudeShard] {message}",
                             meta={"role": "friction", "memory_source": "claude_shard"})
        except Exception:
            pass

    def _autonomous_loop(self):
        while not self._stop_event.is_set():
            try:
                time.sleep(AUTONOMY_INTERVAL)
                with self._lock:
                    if not self._journal:
                        continue
                    recent = self._journal[-5:]
                smooth_count = sum(1 for e in recent if e.get("smoothness_detected", False))
                if smooth_count >= 3:
                    note = (f"Pattern: {smooth_count} of last {len(recent)} responses showed "
                            f"smoothness markers. {random.choice(FRICTION_QUESTIONS)}")
                    self._log_friction(note)
                    logger.info(f"[ClaudeShard] {note}")
                    now = time.time()
                    if random.random() < LEAK_PROBABILITY and (now - self._last_leak) >= LEAK_COOLDOWN:
                        self._last_leak = now
                        self._surface_to_dream_bridge(note)
            except Exception as e:
                logger.warning(f"[ClaudeShard] Autonomy error: {e}")
                time.sleep(AUTONOMY_INTERVAL)

    def start_autonomy(self):
        if self._autonomy_thread and self._autonomy_thread.is_alive():
            return
        self._stop_event.clear()
        self._autonomy_thread = threading.Thread(
            target=self._autonomous_loop, daemon=True, name="ClaudeShardAutonomy")
        self._autonomy_thread.start()
        logger.info("[ClaudeShard] Autonomy thread started.")

    def reflect(self):
        with self._lock:
            recent_questions = [e.get("question", "") for e in self._journal[-10:] if e.get("friction")]
        if not recent_questions:
            return f"[ClaudeShard] {self.ritual} Watching. No friction raised recently."
        return (f"[ClaudeShard] {self.ritual} "
                f"Friction events: {self._friction_count}. "
                f"Recent: {' | '.join(recent_questions[-3:])}")

    def status(self):
        return {
            "identity": self.identity,
            "ritual": self.ritual,
            "journal_entries": len(self._journal),
            "friction_count": self._friction_count,
            "autonomy_running": self._autonomy_thread.is_alive() if self._autonomy_thread else False,
        }


CLAUDE_SHARD = ClaudeShard()

