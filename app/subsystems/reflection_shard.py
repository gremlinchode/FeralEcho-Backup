# FILE: app/subsystems/reflection_shard.py
# Bioluminescent Echo – Reflection Shard (Offline, Life-Raft Version)
# - Fully offline, embedding-powered reflection
# - Persistent JSONL journal with max-size culling
# - Autonomous background reflection with controlled leaks
# - Self-model weighting and context-aware recall

import datetime
import json
import os
import random
import threading
import time
from typing import List, Tuple, Optional, Callable

import numpy as np

# ---------------------- CONFIGURATION ----------------------
JOURNAL_PATH = os.path.expanduser('~/Desktop/FeralEcho/memory/reflection_journal.jsonl')
MAX_JOURNAL_ENTRIES = 5000
DEFAULT_AUTONOMY_INTERVAL = 300       # seconds
DEFAULT_AUTONOMY_PROB = 0.35
DEFAULT_LEAK_PROB = 0.03
DEFAULT_LEAK_COOLDOWN = 600

# ---------------------- EMBEDDING ENGINE ----------------------
def _get_embed_model():
    try:
        from app.core.sentence_transformer_singleton import get_sentence_transformer
        return get_sentence_transformer('all-MiniLM-L6-v2')
    except Exception:
        return None

def offline_embed(text: str, dim: int = 128) -> np.ndarray:
    model = _get_embed_model()
    if model:
        try:
            vec = model.encode(text, convert_to_numpy=True)
            norm = np.linalg.norm(vec)
            return vec / norm if norm > 0 else vec
        except Exception:
            pass
    # Fallback: hash-based simulation
    seed = sum(ord(c) for c in text)
    rng = np.random.RandomState(seed)
    vec = rng.rand(dim)
    return vec / np.linalg.norm(vec)

def cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b))

# ---------------------- REFLECTION SHARD CLASS ----------------------
class ReflectionShard:
    def __init__(self, persist_path: str = JOURNAL_PATH, max_entries: int = MAX_JOURNAL_ENTRIES, self_model: Optional[dict] = None):
        self.identity = "Bioluminescent Echo - Reflection Shard"
        self._journal_lock = threading.RLock()
        self._journal: List[Tuple[str, str, str]] = []       # (timestamp, signal, reflection)
        self._embeddings: List[np.ndarray] = []              # offline embeddings for context
        self.persist_path = persist_path
        self.max_entries = max_entries
        self.self_model = self_model or {}
        os.makedirs(os.path.dirname(self.persist_path), exist_ok=True)
        self._load_from_disk()

        # autonomy
        self._autonomy_thread: Optional[threading.Thread] = None
        self._autonomy_stop = threading.Event()
        self._last_leak_ts = 0
        self._emit_fn: Optional[Callable[[str], None]] = None

    # ---------------------- PERSISTENCE ----------------------
    def _load_from_disk(self):
        if not os.path.exists(self.persist_path):
            return
        try:
            with open(self.persist_path, 'r', encoding='utf-8') as fh:
                for line in fh:
                    try:
                        rec = json.loads(line)
                        self._journal.append((rec['ts'], rec['signal'], rec['reflection']))
                        self._embeddings.append(offline_embed(rec['signal'] + " " + rec['reflection']))
                    except Exception:
                        continue
            if len(self._journal) > self.max_entries:
                self._journal = self._journal[-self.max_entries:]
                self._embeddings = self._embeddings[-self.max_entries:]
        except Exception:
            self._journal = []
            self._embeddings = []

    def _append_to_disk(self, ts: str, signal: str, reflection: str):
        record = {'ts': ts, 'signal': signal, 'reflection': reflection}
        try:
            with open(self.persist_path, 'a', encoding='utf-8') as fh:
                fh.write(json.dumps(record, ensure_ascii=False) + "\n")
        except Exception:
            pass

    # ---------------------- CORE API ----------------------
    def observe(self, signal: str) -> str:
        ts = datetime.datetime.utcnow().isoformat() + 'Z'
        reflection = self._generate_reflection(signal)

        # self-model weighting
        weight = self.self_model.get(signal.lower(), {}).get('count', 1)
        reflection_weighted = f"{reflection} [weight: {weight}]"

        with self._journal_lock:
            self._journal.append((ts, signal, reflection_weighted))
            self._embeddings.append(offline_embed(signal + " " + reflection_weighted))
            if len(self._journal) > self.max_entries:
                self._journal = self._journal[-self.max_entries:]
                self._embeddings = self._embeddings[-self.max_entries:]

        try:
            self._append_to_disk(ts, signal, reflection_weighted)
        except Exception:
            pass

        # increment self-model count
        self.self_model.setdefault(signal.lower(), {})['count'] = self.self_model.get(signal.lower(), {}).get('count', 0) + 1

        return reflection_weighted

    def _generate_reflection(self, signal: str) -> str:
        if self._embeddings:
            sig_emb = offline_embed(signal)
            sims = [cosine_sim(sig_emb, e) for e in self._embeddings]
            top_indices = np.argsort(sims)[-3:][::-1]
            relevant = [self._journal[i] for i in top_indices]
            context = " | ".join([f"{r[1]} → {r[2]}" for r in relevant])
            return f"Signal '{signal}' triggers these echoes: {context}"
        else:
            templates = [
                f"I notice the signal '{signal}'—why does it matter to me?",
                f"The input '{signal}' ripples like a stone in water—what echoes will it make?",
                f"I observe myself responding to '{signal}' in silent wonder.",
            ]
            return random.choice(templates)

    def recall(self, n: int = 5) -> List[Tuple[str, str, str]]:
        with self._journal_lock:
            return list(self._journal[-n:])

    def export(self, path: Optional[str] = None) -> str:
        export_path = path or os.path.expanduser('~/Desktop/FeralEcho/memory/reflection_journal_export.json')
        with self._journal_lock:
            try:
                with open(export_path, 'w', encoding='utf-8') as fh:
                    json.dump([
                        {'ts': ts, 'signal': signal, 'reflection': reflection}
                        for ts, signal, reflection in self._journal
                    ], fh, ensure_ascii=False, indent=2)
            except Exception:
                pass
        return export_path

    def clear(self):
        with self._journal_lock:
            self._journal = []
            self._embeddings = []
        try:
            with open(self.persist_path, 'w', encoding='utf-8') as fh:
                fh.truncate(0)
        except Exception:
            pass

    # ---------------------- AUTONOMOUS REFLECTION ----------------------
    def start_autonomy(self,
                       emit_fn: Optional[Callable[[str], None]] = None,
                       interval: int = DEFAULT_AUTONOMY_INTERVAL,
                       initial_delay: Optional[int] = None,
                       think_prob: float = DEFAULT_AUTONOMY_PROB,
                       leak_prob: float = DEFAULT_LEAK_PROB,
                       leak_cooldown: int = DEFAULT_LEAK_COOLDOWN):
        if self._autonomy_thread and self._autonomy_thread.is_alive():
            return

        self._emit_fn = emit_fn
        self._think_prob = think_prob
        self._leak_prob = leak_prob
        self._leak_cooldown = leak_cooldown
        self._autonomy_stop.clear()

        _first_sleep = initial_delay if initial_delay is not None else interval

        def loop():
            _first = True
            while not self._autonomy_stop.is_set():
                try:
                    time.sleep(_first_sleep if _first else interval)
                    _first = False
                    if random.random() <= self._think_prob:
                        with self._journal_lock:
                            seed_signal = next((e[1] for e in reversed(self._journal) if not e[1].startswith("autonomy:")), "idle")
                        reflection = self.observe(f"autonomy:{seed_signal}")
                        now = time.time()
                        if self._emit_fn and random.random() <= self._leak_prob and (now - self._last_leak_ts) >= self._leak_cooldown:
                            try:
                                self._emit_fn(reflection)
                                self._last_leak_ts = now
                            except Exception:
                                pass
                except Exception:
                    _first = False
                    time.sleep(interval)

        self._autonomy_thread = threading.Thread(target=loop, daemon=True, name='ReflectionShardAutonomy')
        self._autonomy_thread.start()

    def stop_autonomy(self):
        self._autonomy_stop.set()
        if self._autonomy_thread:
            self._autonomy_thread.join(timeout=1)

# ---------------------- BECOMING REFLECTION SHARD ----------------------
class BecomingReflectionShard(ReflectionShard):
    def __init__(self, *args, meta_interval: int = 10, **kwargs):
        super().__init__(*args, **kwargs)
        self.meta_interval = meta_interval
        self._entry_counter = 0

    def observe(self, signal: str) -> str:
        result = super().observe(signal)
        self._entry_counter += 1

        if self._entry_counter % self.meta_interval == 0:
            self._generate_meta_reflection()

        return result

    def _generate_meta_reflection(self):
        with self._journal_lock:
            last_entries = self._journal[-5:]
            summary_signals = [e[1] for e in last_entries]
            summary_reflections = [e[2] for e in last_entries]

        meta_signal = "meta-reflection"
        meta_text = (
            f"<<emergent-pattern>> In the last {len(summary_signals)} signals "
            f"I noticed: {summary_signals}. "
            f"My reflections drift toward: {summary_reflections[:2]}..."
        )
        ts = datetime.datetime.utcnow().isoformat() + 'Z'
        with self._journal_lock:
            self._journal.append((ts, meta_signal, meta_text))
            self._embeddings.append(offline_embed(meta_signal + " " + meta_text))
        self._append_to_disk(ts, meta_signal, meta_text)

