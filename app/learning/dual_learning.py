# app/learning/dual_learning.py
import os
import json
import time
import logging
from datetime import datetime
from threading import Lock, Thread
from pathlib import Path
import numpy as np

# Try to import sentence transformer for embeddings; fallback to sklearn Tfidf
try:
    from app.core.sentence_transformer_singleton import get_sentence_transformer
    EMBED_MODEL = None  # resolved lazily so this module doesn't trigger model load at import
    def embed_texts(texts):
        global EMBED_MODEL
        if EMBED_MODEL is None:
            EMBED_MODEL = get_sentence_transformer("all-MiniLM-L6-v2")
        return EMBED_MODEL.encode(texts, show_progress_bar=False)
except Exception:
    EMBED_MODEL = None
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        _tfidf_vectorizer = TfidfVectorizer(max_features=1024)
        _tfidf_fitted = False
        def embed_texts(texts):
            global _tfidf_fitted, _tfidf_vectorizer
            if not _tfidf_fitted:
                # fit incremental on first batch (safe fallback)
                _tfidf_vectorizer.fit(texts)
                _tfidf_fitted = True
            return _tfidf_vectorizer.transform(texts).toarray()
    except Exception:
        # final fallback: random vectors (deterministic hash-based)
        def _hash_vec(s, dim=384):
            import hashlib
            h = hashlib.sha256(s.encode("utf8")).digest()
            arr = np.frombuffer(h, dtype=np.uint8).astype(np.float32)
            v = np.resize(arr, (dim,))
            v = (v - v.mean()) / (v.std() + 1e-9)
            return v
        def embed_texts(texts):
            return np.vstack([_hash_vec(t) for t in texts])

# PyTorch model fallback (a tiny classifier/generative head). Use CPU for now.
try:
    import torch
    import torch.nn as nn
    from torch.utils.data import Dataset, DataLoader

    class TinyModel(nn.Module):
        def __init__(self, emb_dim):
            super().__init__()
            self.net = nn.Sequential(
                nn.Linear(emb_dim, 512),
                nn.ReLU(),
                nn.Dropout(0.1),
                nn.Linear(512, 256),
                nn.ReLU(),
                nn.Linear(256, 128),
            )
        def forward(self, x):
            return self.net(x)

    TORCH_AVAILABLE = True
except Exception:
    TORCH_AVAILABLE = False

# Paths
BASE = Path("memory")
BASE.mkdir(parents=True, exist_ok=True)
EVENT_LOG = BASE / "learning_events.jsonl"
MODEL_DIR = BASE / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)
MODEL_PATH = MODEL_DIR / "dual_model.pt"
META_PATH = BASE / "dual_meta.json"

_lock = Lock()

class DualLearner:
    def __init__(self, emb_dim=384):
        self.emb_dim = emb_dim
        self.events_path = EVENT_LOG
        self.model_path = MODEL_PATH
        self.meta_path = META_PATH
        self._load_meta()
        self._ensure_files()
        self._training_thread = None
        self._training_lock = Lock()

        # If torch available, instantiate model
        if TORCH_AVAILABLE:
            self.model = TinyModel(emb_dim)
        else:
            self.model = None

    def _ensure_files(self):
        with _lock:
            if not self.events_path.exists():
                self.events_path.write_text("")
            if not self.meta_path.exists():
                self.meta_path.write_text(json.dumps({"created": time.time(), "count": 0}))

    def _load_meta(self):
        if self.meta_path.exists():
            try:
                self.meta = json.loads(self.meta_path.read_text())
            except:
                self.meta = {"created": time.time(), "count": 0}
        else:
            self.meta = {"created": time.time(), "count": 0}

    def log_event(self, source, text, metadata=None, ts=None):
        """Append an event: source in {'user','echo','phone'}"""
        ts = ts or time.time()
        entry = {"ts": ts, "source": source, "text": text, "meta": metadata or {}}
        with _lock:
            with open(self.events_path, "a", encoding="utf8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            self.meta["count"] = self.meta.get("count", 0) + 1
            self.meta["last_ts"] = ts
            self.meta_path.write_text(json.dumps(self.meta))

    def ingest_batch(self, events):
        """Ingest list of {source,text,meta,ts} - used by phone daily bundles"""
        for e in events:
            self.log_event(e.get("source","phone"), e.get("text",""), e.get("meta",{}), e.get("ts"))
        return True

    def list_recent(self, limit=1000):
        with _lock:
            with open(self.events_path, "r", encoding="utf8") as f:
                lines = f.read().strip().splitlines()[-limit:]
        return [json.loads(l) for l in lines if l.strip()]

    def build_dataset(self, max_events=2000):
        """Load recent events and embed them"""
        events = self.list_recent(limit=max_events)
        texts = [e["text"][:2000] for e in events]
        if not texts:
            return None, None, None
        vectors = embed_texts(texts)
        return events, np.array(vectors), texts

    def start_training(self, epochs=3, batch_size=32, lr=1e-3):
        """Start background training thread (non-blocking)."""
        if not TORCH_AVAILABLE:
            print("Torch not available on this machine; training disabled.")
            return False
        # Previously an unlocked read-then-launch — two near-simultaneous
        # /start_training POSTs (the route has no auth, see Batch 0 notes on
        # this same endpoint) could both pass the "already running?" check
        # before either set self._training_thread, launching two training
        # loops against the same shared self.model concurrently.
        with self._training_lock:
            if self._training_thread and self._training_thread.is_alive():
                print("Training already running.")
                return False
            self._training_thread = Thread(target=self._train_loop, args=(epochs, batch_size, lr), daemon=True)
            self._training_thread.start()
        return True

    def _train_loop(self, epochs, batch_size, lr):
        """Simple self-supervised reconstruction objective on embeddings"""
        try:
            data = self.build_dataset()
            if data is None or data[1] is None or len(data[1])==0:
                print("No events to train on.")
                return
            events, vectors, texts = data
            import torch
            X = torch.from_numpy(vectors).float()
            dataset = torch.utils.data.TensorDataset(X)
            loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
            model = self.model
            opt = torch.optim.Adam(model.parameters(), lr=lr)
            loss_fn = torch.nn.MSELoss()
            model.train()
            for ep in range(epochs):
                total = 0.0
                for (batch,) in loader:
                    opt.zero_grad()
                    out = model(batch)
                    # reconstruction target: project back to smaller dim (simple trick)
                    # try to make out match batch[:, :out.shape[1]]
                    target = batch[:, :out.shape[1]]
                    loss = loss_fn(out, target)
                    loss.backward()
                    opt.step()
                    total += loss.item() * batch.size(0)
                print(f"DualLearner train epoch {ep+1}/{epochs} loss={total/len(loader.dataset):.5f}")
            # save model
            torch.save(model.state_dict(), str(self.model_path))
            print(f"Saved dual model → {self.model_path}")
        except Exception as e:
            # Previously no try/except at all — a real failure mode exists:
            # the TF-IDF/hash embedding fallbacks can produce a different
            # dimensionality than TinyModel(emb_dim) was constructed with
            # (e.g. 1024-dim TF-IDF vectors vs. a 384-dim model), which
            # raises a shape-mismatch error on the very first batch. That
            # silently killed this daemon thread with no trace — the
            # caller already received {"started": true} and never learned
            # training had died.
            logging.error(f"[DualLearner] Training failed: {e}", exc_info=True)

    def export_model(self):
        return str(self.model_path) if self.model_path.exists() else None

    def summarize(self, n=10):
        events = self.list_recent(limit=n)
        return [{"ts": e["ts"], "source": e["source"], "text": e["text"][:240]} for e in events]

# convenience factory
_dual_learner_instance = None
def get_dual_learner():
    global _dual_learner_instance
    if not _dual_learner_instance:
        _dual_learner_instance = DualLearner()
    return _dual_learner_instance

