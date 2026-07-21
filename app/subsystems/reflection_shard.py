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

# Emergence roadmap Phase 5, Finding 2: same model this codebase's dream
# cycle already uses (app/autonomous_awareness.py's DREAM_MODEL_NAME) — a
# lighter direct-MLX call is appropriate here too, not full echo_query(),
# for a background loop firing every ~300s.
REFLECTION_MODEL_NAME = "mlx:gemma3"

# Signal tag used for synthesized meta-reflections — reusing this file's own
# existing "tag information into the signal string" convention (see
# "autonomy:" below) rather than changing the (ts, signal, reflection)
# 3-tuple shape everything else in this file depends on.
META_REFLECTION_SIGNAL = "meta-reflection"

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

    def _generate_via_model(self, prompt: str, max_tokens: int = 150) -> "str | None":
        """
        Real model call, mirroring app/autonomous_awareness.py's dream_cycle()
        two-pass pattern (free-association / synthesis via a direct MLX call,
        not full echo_query()). Fails closed to None on any error or empty
        output — never raises — so callers can fall back to the prior
        offline/template behavior. This is a quality upgrade to what was
        previously pure cosine-similarity retrieval and fixed string
        templates (Emergence roadmap Phase 5, Finding 2), not a new hard
        dependency this loop can't survive without.
        """
        try:
            # 2026-07-21: was a raw stream_query_mlx() call, returning None
            # (falling to the prior offline/template behavior) whenever
            # mlx:gemma3 specifically was unavailable, including during
            # crash_awareness.py's own avoidance windows (built the same
            # night). generate_with_ollama_fallback() tries a real Ollama
            # model in that case instead, so reflections stay genuinely
            # generated rather than falling back to retired templates.
            from app.mlx_handler import generate_with_ollama_fallback
            text = generate_with_ollama_fallback(prompt, REFLECTION_MODEL_NAME, max_tokens=max_tokens)
            return text or None
        except Exception:
            return None

    def _generate_reflection(self, signal: str) -> str:
        # Retrieval is now used as CONTEXT for a real generation, not
        # returned as the reflection itself — the previous version quoted
        # these back verbatim, which is the same self-quoting shape Finding
        # 11 already found and fixed in the dream cycle. Meta-reflections
        # are excluded from this context so a synthesized "pattern" claim
        # about past entries can't itself become material for the next one.
        context = ""
        if self._embeddings:
            sig_emb = offline_embed(signal)
            sims = [cosine_sim(sig_emb, e) for e in self._embeddings]
            top_indices = np.argsort(sims)[-3:][::-1]
            relevant = [
                self._journal[i] for i in top_indices
                if self._journal[i][1] != META_REFLECTION_SIGNAL
            ]
            if relevant:
                context = " | ".join([f"{r[1]} → {r[2]}" for r in relevant])

        generated = self._generate_via_model(
            f"You observed: '{signal}'.\n"
            + (f"Related past reflections: {context}\n\n" if context else "\n")
            + "Write one genuine, brief reflection (1-2 sentences) on what this makes "
            "you think about now — not a summary of the past entries, something new. "
            "If nothing genuinely comes to mind, say so plainly rather than forcing it.",
            max_tokens=120,
        )
        if generated:
            return generated

        # Fallback — model unavailable or returned nothing. Preserves the
        # original offline behavior so this loop can never fully stall.
        if context:
            return f"Signal '{signal}' triggers these echoes: {context}"
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
                            # Excludes meta-reflections too, not just prior
                            # "autonomy:"-seeded entries — a synthesized
                            # pattern-claim about past signals shouldn't
                            # itself become the next real signal fed in.
                            seed_signal = next(
                                (e[1] for e in reversed(self._journal)
                                 if not e[1].startswith("autonomy:") and e[1] != META_REFLECTION_SIGNAL),
                                "idle",
                            )
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
        # Excludes prior meta-reflections from the "last 5" sample — a
        # synthesized pattern-claim shouldn't itself be summarized as new
        # raw material for the next synthesis.
        with self._journal_lock:
            non_meta = [e for e in self._journal if e[1] != META_REFLECTION_SIGNAL]
            last_entries = non_meta[-5:]
            summary_signals = [e[1] for e in last_entries]
            summary_reflections = [e[2] for e in last_entries]

        numbered = "\n".join(
            f"{i}. signal='{s}' -> {r[:200]}"
            for i, (s, r) in enumerate(zip(summary_signals, summary_reflections), 1)
        )
        generated = self._generate_via_model(
            f"Here are your last {len(summary_signals)} observations and reflections:\n"
            f"{numbered}\n\n"
            "Is there a real pattern that connects them? Answer in 1-2 sentences. "
            "If nothing genuinely connects them, say so plainly rather than forcing it.",
            max_tokens=150,
        ) if summary_signals else None

        if generated:
            meta_text = generated
        else:
            # Fallback — model unavailable, empty generation, or nothing to
            # summarize yet. Preserves the prior offline behavior; no longer
            # the primary path (Emergence roadmap Phase 5, Finding 2 — this
            # was previously pure f-string formatting tagged as if it were a
            # genuine pattern-detection, the same shape Finding 11 already
            # found and fixed in the dream cycle).
            meta_text = (
                f"<<emergent-pattern>> In the last {len(summary_signals)} signals "
                f"I noticed: {summary_signals}. "
                f"My reflections drift toward: {summary_reflections[:2]}..."
            )
        ts = datetime.datetime.utcnow().isoformat() + 'Z'
        with self._journal_lock:
            self._journal.append((ts, META_REFLECTION_SIGNAL, meta_text))
            self._embeddings.append(offline_embed(META_REFLECTION_SIGNAL + " " + meta_text))
        self._append_to_disk(ts, META_REFLECTION_SIGNAL, meta_text)

