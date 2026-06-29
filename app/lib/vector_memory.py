# vector_memory.py
from __future__ import annotations
import os
import json
import logging
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

import faiss
import numpy as np

# Limit FAISS threads on macOS for semaphore safety
faiss.omp_set_num_threads(1)

@dataclass
class MemoryItem:
    id: str
    text: str
    meta: Optional[Dict] = None

class VectorMemory:
    """
    FAISS-based vector memory with robust self-healing.
    Supports adding items with embeddings, searching, and saving/loading index + metadata.
    """

    DEFAULT_DIM = 384

    def __init__(
        self,
        dim: Optional[int] = None,
        index_path: str = "data/faiss.index",
        meta_path: str = "data/memory_meta.json",
    ):
        self.dim = dim
        self.index_path = index_path
        self.meta_path = meta_path
        self.index: Optional[faiss.IndexFlatIP] = None
        self.meta: Dict[str, Dict] = {}
        self.id_order: List[str] = []

        self._load_metadata()
        self._load_or_rebuild_index()

    def _load_metadata(self) -> None:
        """Load metadata from disk; start fresh if missing or corrupted."""
        if os.path.exists(self.meta_path):
            try:
                with open(self.meta_path, "r", encoding="utf-8") as f:
                    self.meta = json.load(f)
                    self.id_order = list(self.meta.keys())
                logging.info(f"Loaded memory metadata from {self.meta_path}")
            except Exception as e:
                logging.warning(f"Failed to load memory metadata, starting fresh: {e}")
                self.meta = {}
                self.id_order = []
        else:
            logging.info(f"Metadata file not found at {self.meta_path}, starting fresh.")

    def _load_or_rebuild_index(self) -> None:
        """Load FAISS index or rebuild if missing/corrupted."""
        try:
            if os.path.exists(self.index_path):
                self.index = faiss.read_index(self.index_path)
                if self.dim is None:
                    self.dim = self.index.d
                logging.info(f"Loaded FAISS index from {self.index_path} with dim {self.dim}")
            elif self.dim is not None:
                self.index = faiss.IndexFlatIP(self.dim)
                logging.info(f"Created new FAISS IndexFlatIP with dim {self.dim}")
        except Exception as e:
            logging.warning(f"Failed to load FAISS index, rebuilding: {e}")
            if self.dim is None:
                self.dim = self.DEFAULT_DIM
                logging.info(f"Dimension not set, using default dim={self.DEFAULT_DIM}")
            self.index = faiss.IndexFlatIP(self.dim)
            self._persist()
            logging.info(f"Rebuilt FAISS index with dim {self.dim}")

    def add(self, items: List[MemoryItem], embeddings: np.ndarray) -> None:
        """Add items with embeddings to FAISS index and metadata."""
        if embeddings.ndim == 1:
            embeddings = embeddings.reshape(1, -1)

        # Ensure index exists
        if self.index is None:
            logging.warning("VectorMemory index was None, rebuilding...")
            self._load_or_rebuild_index()

        # Set dim if missing
        if self.dim is None:
            self.dim = embeddings.shape[1]
            self.index = faiss.IndexFlatIP(self.dim)
            logging.info(f"VectorMemory dimension set to {self.dim} and index initialized.")

        if embeddings.shape[1] != self.dim:
            raise ValueError(
                f"Embedding dimension {embeddings.shape[1]} does not match VectorMemory dimension {self.dim}"
            )

        emb = embeddings.astype(np.float32)
        faiss.normalize_L2(emb)
        self.index.add(emb)

        for item in items:
            self.meta[item.id] = {"text": item.text, "meta": item.meta or {}}
            if item.id not in self.id_order:
                self.id_order.append(item.id)

        self._persist()
        logging.info(f"Added {len(items)} items to VectorMemory and persisted data.")

    def search(self, query_embedding: np.ndarray, k: int = 5) -> List[Tuple[str, float, Dict]]:
        """Return top-k results for a query embedding."""
        if self.index is None or self.index.ntotal == 0:
            logging.info("FAISS index empty or uninitialized, returning empty search results.")
            return []

        qe = query_embedding.astype(np.float32)
        if qe.ndim == 1:
            qe = qe.reshape(1, -1)

        if qe.shape[1] != self.dim:
            raise ValueError(
                f"Query embedding dimension {qe.shape[1]} does not match VectorMemory dimension {self.dim}"
            )

        faiss.normalize_L2(qe)
        D, I = self.index.search(qe, min(k, self.index.ntotal))

        results = []
        for j, idx in enumerate(I[0]):
            if idx == -1 or idx >= len(self.id_order):
                continue
            mem_id = self.id_order[idx]
            record = self.meta.get(mem_id, {})
            results.append((record.get("text", ""), float(D[0, j]), record.get("meta", {})))

        return results

    def _persist(self) -> None:
        """Persist FAISS index and metadata to disk safely."""
        try:
            os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
            os.makedirs(os.path.dirname(self.meta_path), exist_ok=True)

            if self.index is not None:
                faiss.write_index(self.index, self.index_path)

            with open(self.meta_path, "w", encoding="utf-8") as f:
                json.dump(self.meta, f, ensure_ascii=False, indent=2)

            logging.info(f"Persisted FAISS index to {self.index_path} and metadata to {self.meta_path}")
        except Exception as e:
            logging.error(f"Failed to persist VectorMemory data: {e}")

