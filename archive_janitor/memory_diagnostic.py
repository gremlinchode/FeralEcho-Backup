#!/usr/bin/env python3
"""
safe_faiss_test.py – FAISS Vector Memory Dry Run for FeralEcho
- Does NOT overwrite existing index or metadata
- Tests embeddings, vector add, and search safely
"""

import logging
import numpy as np
import sys

try:
    import faiss
except ImportError:
    faiss = None

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

# Configuration
TEST_TEXTS = [
    "Echo is learning to understand memory safely.",
    "This is a temporary test for vector embeddings."
]
EMBED_DIM = 384
MODEL_NAME = "all-MiniLM-L6-v2"

def safe_encode(model, texts):
    try:
        embeddings = model.encode(texts, normalize_embeddings=True)
        embeddings = np.array(embeddings, dtype=np.float32)
        return embeddings
    except Exception as e:
        logging.error(f"Failed to generate embeddings: {e}")
        return None

def safe_faiss_add(index, embeddings):
    try:
        faiss.normalize_L2(embeddings)
        index.add(embeddings)
        logging.info(f"Added {index.ntotal} vectors to temporary index.")
    except Exception as e:
        logging.error(f"Failed to add vectors to FAISS index: {e}")

def safe_faiss_search(index, query_emb, k=2):
    try:
        faiss.normalize_L2(query_emb)
        D, I = index.search(query_emb, k)
        return D, I
    except Exception as e:
        logging.error(f"FAISS search failed: {e}")
        return None, None

def main():
    if faiss is None:
        logging.error("FAISS not installed. Cannot test vector memory.")
        return
    if SentenceTransformer is None:
        logging.error("SentenceTransformer not installed. Cannot generate embeddings.")
        return

    # Load model
    try:
        logging.info("Initializing embedding model...")
        model = SentenceTransformer(MODEL_NAME)
    except Exception as e:
        logging.error(f"Failed to load embedding model: {e}")
        return

    # Generate embeddings
    logging.info("Generating embeddings...")
    embeddings = safe_encode(model, TEST_TEXTS)
    if embeddings is None:
        return
    logging.info(f"Embeddings shape: {embeddings.shape}")

    # Create temporary FAISS index
    try:
        logging.info("Creating temporary FAISS index...")
        index = faiss.IndexFlatIP(EMBED_DIM)
    except Exception as e:
        logging.error(f"Failed to create FAISS index: {e}")
        return

    # Add embeddings
    safe_faiss_add(index, embeddings)

    # Test search
    logging.info("Performing a test search...")
    query_emb = safe_encode(model, ["memory test for Echo"])
    if query_emb is None:
        return

    D, I = safe_faiss_search(index, query_emb, k=2)
    if D is None or I is None:
        return

    logging.info("Search results:")
    for i, idx in enumerate(I[0]):
        if idx != -1:
            logging.info(f"  Match {i+1}: '{TEST_TEXTS[idx]}' with similarity {D[0,i]:.4f}")

    logging.info("FAISS dry-run test complete. Existing index and metadata untouched.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        sys.exit(1)

