"""
Adversarial test for Finding 22 — FAISS split-brain atomicity fix.

Two scenarios:
  T1: Crash between meta write and FAISS index write.
      Meta has N+1 entries; FAISS has N vectors.
      Reload must detect mismatch (warning) and leave existing N entries searchable.

  T2: Crash during meta.tmp write (before os.replace).
      Original meta and index must be byte-for-byte unchanged.

Run with:
    conda activate feral_echo
    python -m pytest sandbox/experiments/test_faiss_atomicity.py -v
"""

import json
import logging
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("OMP_NUM_THREADS", "1")

from app.lib.vector_memory import VectorMemory, MemoryItem


def _make_vm(tmp_dir, dim=4):
    meta_path  = os.path.join(tmp_dir, "test_meta.json")
    index_path = os.path.join(tmp_dir, "test_faiss.index")
    return VectorMemory(dim=dim, index_path=index_path, meta_path=meta_path)


def _add(vm, text, uid):
    rng = np.random.default_rng(abs(hash(uid)) % (2**31))
    vec = rng.standard_normal((1, vm.dim)).astype(np.float32)
    vm.add([MemoryItem(uid, text, {})], vec)


class TestFaissAtomicity(unittest.TestCase):

    def test_crash_between_meta_and_faiss_write(self):
        """Crash after meta committed but before FAISS index rename.

        Expected state on reload:
          - meta has 4 entries (uid-4 committed to meta before crash)
          - FAISS has 3 vectors (uid-4 FAISS write never completed)
          - ntotal mismatch warning fires
          - existing 3 entries still searchable
        """
        tmp = tempfile.mkdtemp()
        vm = _make_vm(tmp)

        _add(vm, "alpha", "uid-1")
        _add(vm, "beta",  "uid-2")
        _add(vm, "gamma", "uid-3")

        # Confirm clean state before injecting crash
        self.assertEqual(vm.index.ntotal, 3)
        self.assertEqual(len(vm.meta), 3)

        original_replace = os.replace
        call_count = [0]

        def patched_replace(src, dst):
            call_count[0] += 1
            if call_count[0] == 2:
                # First os.replace = meta commit (allowed).
                # Second os.replace = FAISS index commit — simulate crash here.
                raise OSError("simulated crash before FAISS index rename")
            original_replace(src, dst)

        with patch("os.replace", side_effect=patched_replace):
            try:
                _add(vm, "delta", "uid-4")
            except OSError:
                pass

        # os.replace was called exactly twice (meta succeeded, FAISS failed)
        self.assertEqual(call_count[0], 2, "expected exactly 2 os.replace calls")

        # Reload from disk and capture warning
        with self.assertLogs(level="WARNING") as log_ctx:
            vm2 = _make_vm(tmp)

        meta_count  = len(vm2.meta)
        faiss_count = vm2.index.ntotal if vm2.index else 0

        self.assertEqual(meta_count,  4, f"meta should have 4 entries, got {meta_count}")
        self.assertEqual(faiss_count, 3, f"FAISS should have 3 vectors, got {faiss_count}")

        mismatch_warnings = [m for m in log_ctx.output if "ntotal mismatch" in m]
        self.assertTrue(mismatch_warnings, "expected ntotal mismatch WARNING in log")

        # Existing 3 entries still searchable
        qvec = np.random.randn(1, vm2.dim).astype(np.float32)
        results = vm2.search(qvec, k=5)
        self.assertEqual(len(results), 3, f"expected 3 searchable entries, got {len(results)}")

    def test_crash_during_meta_tmp_write_leaves_files_intact(self):
        """Crash while writing meta.tmp — before os.replace is called.

        Original meta and index files must be byte-for-byte unchanged.
        """
        tmp = tempfile.mkdtemp()
        vm = _make_vm(tmp)

        _add(vm, "alpha", "uid-1")

        meta_path  = vm.meta_path
        index_path = vm.index_path

        with open(meta_path,  "rb") as f:
            meta_before = f.read()
        with open(index_path, "rb") as f:
            index_before = f.read()

        original_open = open

        def patched_open(path, mode="r", **kwargs):
            if isinstance(path, str) and path.endswith(".tmp") and "w" in mode:
                raise OSError("simulated crash during tmp write")
            return original_open(path, mode, **kwargs)

        with patch("builtins.open", side_effect=patched_open):
            try:
                _add(vm, "beta", "uid-2")
            except OSError:
                pass

        with open(meta_path,  "rb") as f:
            meta_after = f.read()
        with open(index_path, "rb") as f:
            index_after = f.read()

        self.assertEqual(meta_before,  meta_after,  "meta should be unchanged after tmp-write crash")
        self.assertEqual(index_before, index_after, "index should be unchanged after tmp-write crash")

    def test_no_tmp_files_left_after_successful_persist(self):
        """After a clean add(), no .tmp files should remain on disk."""
        tmp = tempfile.mkdtemp()
        vm = _make_vm(tmp)
        _add(vm, "alpha", "uid-1")

        tmp_files = [f for f in os.listdir(tmp) if f.endswith(".tmp")]
        self.assertEqual(tmp_files, [], f"stale .tmp files found: {tmp_files}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
