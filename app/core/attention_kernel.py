# app/core/attention_kernel.py

import time
from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class Signal:
    source: str
    value: float
    tag: str
    metadata: Dict = field(default_factory=dict)


class AttentionKernel:
    """
    Minimal global salience arbitration layer.

    - Accepts signals from all Echo subsystems
    - Maintains rolling priority queue
    - Produces single 'focus' state
    """

    def __init__(self, decay: float = 0.95, max_memory: int = 100):
        self.decay = decay
        self.max_memory = max_memory

        self.signals: List[Signal] = []
        self.focus: Optional[Signal] = None
        self.last_update = time.time()

    # -----------------------------
    # INPUT
    # -----------------------------
    def submit(self, signal: Signal):
        """Add a new signal into attention pool."""
        self.signals.append(signal)

        if len(self.signals) > self.max_memory:
            self.signals = self.signals[-self.max_memory:]

    # -----------------------------
    # CORE ARBITRATION
    # -----------------------------
    def compute_focus(self) -> Optional[Signal]:
        """
        Select most important signal using simple weighted scoring.
        """

        if not self.signals:
            return None

        best_score = -1
        best_signal = None

        now = time.time()
        time_factor = lambda s: 1.0 / (1.0 + (now - self.last_update) * 0.01)

        for s in self.signals:
            score = s.value * time_factor(s)

            # subsystem bias (very light weighting, not hardcoded intelligence)
            if s.source == "guardian":
                score *= 1.2
            elif s.source == "riverbrain":
                score *= 1.1
            elif s.source == "harmony":
                score *= 0.9  # exploration is slightly de-prioritized

            if score > best_score:
                best_score = score
                best_signal = s

        self.focus = best_signal
        self.last_update = now
        return best_signal

    # -----------------------------
    # STATE INTERFACE
    # -----------------------------
    def get_focus(self) -> Optional[Dict]:
        if not self.focus:
            return None

        return {
            "source": self.focus.source,
            "tag": self.focus.tag,
            "value": self.focus.value,
            "metadata": self.focus.metadata
        }

    def decay_memory(self):
        """Gradually forget old signals (prevents clutter)."""
        self.signals = self.signals[int(len(self.signals) * (1 - (1 - self.decay))):]
