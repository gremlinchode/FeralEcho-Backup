"""
Isolated, observation-only driver for the "Establish Real Trace -> F2
Provenance" mission's Phase 2. NOT part of production; not imported by
anything. Run directly: python app/experiments/real_trace_f2_provenance/run_real_self_edit.py

Safety design (verified live in this same run, not just asserted):
  1. RIVER_BRAIN_PATH is redirected to a scratch copy BEFORE the RiverBrain
     singleton is ever instantiated (closes the Finding-89/Tier-8 background
     -writer-thread gap: RiverBrain.__init__() starts a ~60s persist thread
     unconditionally, so a method-level patch alone is not sufficient).
  2. RiverBrain.learn / learn_from_sandbox_outcome / learn_from_council_rating
     / save / _do_save are ALSO patched to no-ops at the class level, applied
     before the first get_river_brain() call anywhere in the process.
  3. uuid.uuid4 is wrapped (pass-through, zero behavior change) purely so the
     real trace_id minted inside execute_self_edit() can be observed from
     outside, since it is not currently written to any log unless the
     attempt reaches the full production-deploy success path.
  4. No retries. Exactly one perform_self_edit() call, with prompt=None so
     every part of what gets attempted (target task type, prompt text,
     temperature) is chosen by the real, unmodified production logic -- this
     script does not select or shape the candidate in any way.
"""
import os
import sys
import shutil
import time
import uuid as uuid_module
import hashlib
import json

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

sys.path.insert(0, os.getcwd())

REAL_RIVER_PATH = "memory/river_brain.pkl"
SCRATCH_DIR = "app/experiments/real_trace_f2_provenance/_scratch"
SCRATCH_RIVER_PATH = os.path.join(SCRATCH_DIR, "river_brain_scratch.pkl")

os.makedirs(SCRATCH_DIR, exist_ok=True)


def sha256(path):
    if not os.path.exists(path):
        return None
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


report = {"phase": "setup"}
report["real_river_brain_sha256_before"] = sha256(REAL_RIVER_PATH)

# --- Step 1: copy real river_brain.pkl to scratch so reads inside this
# process see real, current data (read-fidelity preserved), but every write
# (including the background writer thread's unconditional persist) lands on
# the scratch copy instead. ---
shutil.copy2(REAL_RIVER_PATH, SCRATCH_RIVER_PATH)
report["scratch_river_seeded_from_real_sha256"] = sha256(SCRATCH_RIVER_PATH)
assert report["scratch_river_seeded_from_real_sha256"] == report["real_river_brain_sha256_before"]

# --- Step 2: import the orchestrator module and redirect its RIVER_BRAIN_PATH
# global BEFORE anything touches get_river_brain()/RiverBrain(). ---
import app.core.echo_model_orchestrator as emo  # noqa: E402

assert emo.RIVER_BRAIN_PATH == "memory/river_brain.pkl", (
    f"Unexpected RIVER_BRAIN_PATH default: {emo.RIVER_BRAIN_PATH!r} -- "
    "aborting, module structure has drifted from what this script assumes."
)
emo.RIVER_BRAIN_PATH = os.path.abspath(SCRATCH_RIVER_PATH)
report["river_brain_path_redirected_to"] = emo.RIVER_BRAIN_PATH

# --- Step 3: patch RiverBrain's mutating/persisting methods to no-ops at the
# CLASS level, before any instance exists. ---
_patch_calls = {"learn": 0, "learn_from_sandbox_outcome": 0,
                 "learn_from_council_rating": 0, "save": 0, "_do_save": 0}


def _noop_learn(self, *a, **k):
    _patch_calls["learn"] += 1


def _noop_learn_sandbox(self, *a, **k):
    _patch_calls["learn_from_sandbox_outcome"] += 1


def _noop_learn_council(self, *a, **k):
    _patch_calls["learn_from_council_rating"] += 1


def _noop_save(self, *a, **k):
    _patch_calls["save"] += 1


def _noop_do_save(self, *a, **k):
    _patch_calls["_do_save"] += 1


emo.RiverBrain.learn = _noop_learn
emo.RiverBrain.learn_from_sandbox_outcome = _noop_learn_sandbox
emo.RiverBrain.learn_from_council_rating = _noop_learn_council
emo.RiverBrain.save = _noop_save
emo.RiverBrain._do_save = _noop_do_save

report["riverbrain_methods_patched"] = [
    n for n in _patch_calls
    if getattr(emo.RiverBrain, n).__name__.startswith("_noop")
]

# --- Step 4: wrap uuid.uuid4 (pass-through, observational only) so the real
# trace_id minted inside execute_self_edit() is recoverable regardless of
# whether the attempt reaches a durable log line. ---
_observed_uuids = []
_real_uuid4 = uuid_module.uuid4


def _observing_uuid4():
    v = _real_uuid4()
    _observed_uuids.append(str(v))
    return v


uuid_module.uuid4 = _observing_uuid4

# --- Step 5: confirm neutralization actually engaged before doing anything
# real -- instantiate the singleton and directly exercise each patched
# method once, confirming the counters move and confirming the scratch file
# (not the real one) is what changes. ---
river = emo.get_river_brain()
river.learn("verification-probe-model", "coding", "probe text, discarded")
river.learn_from_sandbox_outcome("verification-probe-model", success=True, code="pass")
river.save()

report["neutralization_verification_calls"] = dict(_patch_calls)
report["real_river_brain_sha256_after_probe_calls"] = sha256(REAL_RIVER_PATH)
report["real_river_unaffected_by_probe"] = (
    report["real_river_brain_sha256_after_probe_calls"] == report["real_river_brain_sha256_before"]
)

if not report["real_river_unaffected_by_probe"]:
    print(json.dumps(report, indent=2))
    print("\n!!! NEUTRALIZATION VERIFICATION FAILED -- ABORTING BEFORE PHASE 2 !!!")
    sys.exit(3)

if not all(v == 1 for v in _patch_calls.values() if v > 0) or sum(_patch_calls.values()) < 3:
    print(json.dumps(report, indent=2))
    print("\n!!! PATCH COUNTERS DID NOT MOVE AS EXPECTED -- ABORTING BEFORE PHASE 2 !!!")
    sys.exit(3)

report["neutralization_confirmed"] = True
report["phase"] = "neutralization_confirmed"
print("=== NEUTRALIZATION VERIFIED ===")
print(json.dumps(report, indent=2))

# --- Step 6: reset probe-call counters (so the real Phase-2 attempt's own
# call counts are cleanly attributable, not mixed with the verification
# probe above), then run exactly one real self-edit. ---
for k in _patch_calls:
    _patch_calls[k] = 0

print("\n=== PHASE 2: ONE REAL SELF-EDIT ATTEMPT (perform_self_edit, prompt=None) ===")
t0 = time.time()
from app.core.self_edit_manager import perform_self_edit  # noqa: E402

success, result_msg = perform_self_edit(prompt=None)
elapsed = time.time() - t0

report["phase2_result"] = {
    "success": success,
    "result_msg": result_msg,
    "elapsed_s": round(elapsed, 2),
    "observed_uuids_during_attempt": list(_observed_uuids),
    "riverbrain_calls_during_attempt": dict(_patch_calls),
}
report["real_river_brain_sha256_after_phase2"] = sha256(REAL_RIVER_PATH)
report["real_river_unaffected_by_phase2"] = (
    report["real_river_brain_sha256_after_phase2"] == report["real_river_brain_sha256_before"]
)

print(json.dumps(report["phase2_result"], indent=2))
print("\nreal river_brain.pkl unaffected by Phase 2:", report["real_river_unaffected_by_phase2"])

out_path = "app/experiments/real_trace_f2_provenance/phase2_run_report.json"
with open(out_path, "w") as f:
    json.dump(report, f, indent=2, default=str)
print(f"\nWrote {out_path}")
