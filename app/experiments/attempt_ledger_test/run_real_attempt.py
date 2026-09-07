"""
ISOLATED TEST HARNESS — Attempt-Level Ledger implementation mission,
audits/2026-09-07_attempt_ledger_implementation.md, Phase 5.

Runs exactly one real, unforced self-edit attempt through the actual
production pipeline (execute_self_edit()/perform_self_edit()), with
RiverBrain writes neutralized two ways (class-level no-op patch, and a
redirected RIVER_BRAIN_PATH before first RiverBrain instantiation — closes
the background-writer-thread gap the earlier "Tier-8" forensic pass found)
so the real hash of memory/river_brain.pkl is provably untouched.

No candidate is shaped, no error is manufactured, no outcome is forced.
Whatever the pipeline naturally produces is the real test result.
"""
import hashlib
import json
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

RIVER_PATH = "memory/river_brain.pkl"


def sha256(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def main():
    before_hash = sha256(RIVER_PATH)

    # --- Step 1: redirect RIVER_BRAIN_PATH BEFORE first instantiation ---
    import app.core.echo_model_orchestrator as emo
    scratch_dir = tempfile.mkdtemp(prefix="river_scratch_")
    scratch_path = os.path.join(scratch_dir, "river_brain_scratch.pkl")
    shutil.copy2(RIVER_PATH, scratch_path)
    emo.RIVER_BRAIN_PATH = scratch_path

    # --- Step 2: class-level no-op patch, belt-and-suspenders ---
    _real_learn = emo.RiverBrain.learn
    _real_learn_sbo = emo.RiverBrain.learn_from_sandbox_outcome
    _real_save = emo.RiverBrain.save
    _real_do_save = emo.RiverBrain._do_save

    calls = {"learn": 0, "learn_sbo": 0, "save": 0, "_do_save": 0}

    def _noop_learn(self, *a, **kw):
        calls["learn"] += 1
        return None

    def _noop_learn_sbo(self, *a, **kw):
        calls["learn_sbo"] += 1
        return None

    def _noop_save(self, *a, **kw):
        calls["save"] += 1
        return None

    def _noop_do_save(self, *a, **kw):
        calls["_do_save"] += 1
        return None

    emo.RiverBrain.learn = _noop_learn
    emo.RiverBrain.learn_from_sandbox_outcome = _noop_learn_sbo
    emo.RiverBrain.save = _noop_save
    emo.RiverBrain._do_save = _noop_do_save

    # --- Step 3: pre-flight probe — confirm neutralization actually holds ---
    river = emo.get_river_brain()
    river.learn("probe_model", "coding", "def f(): pass")
    river.save()
    assert calls["learn"] == 1 and calls["save"] == 1, "neutralization probe failed"
    assert sha256(RIVER_PATH) == before_hash, "PROBE ALREADY MUTATED REAL FILE — ABORTING"
    print("[PROBE] Neutralization confirmed live before real attempt.")

    # --- Step 4: the real, unforced attempt ---
    from app.core.self_edit_manager import perform_self_edit

    result = perform_self_edit(prompt=None)

    after_hash = sha256(RIVER_PATH)

    out = {
        "result": list(result),
        "river_calls_during_real_attempt": dict(calls),
        "river_brain_pkl_hash_before": before_hash,
        "river_brain_pkl_hash_after": after_hash,
        "river_brain_pkl_unchanged": before_hash == after_hash,
    }
    with open(
        os.path.join(os.path.dirname(__file__), "real_attempt_result.json"), "w"
    ) as f:
        json.dump(out, f, indent=2, default=str)

    print(json.dumps(out, indent=2, default=str))

    # restore (defensive; script never wrote to the module attr on disk,
    # only in-process, but restore methods in case anything else in this
    # process imports emo again)
    emo.RiverBrain.learn = _real_learn
    emo.RiverBrain.learn_from_sandbox_outcome = _real_learn_sbo
    emo.RiverBrain.save = _real_save
    emo.RiverBrain._do_save = _real_do_save

    shutil.rmtree(scratch_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
