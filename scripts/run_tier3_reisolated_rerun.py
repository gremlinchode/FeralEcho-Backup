#!/usr/bin/env python3
"""
PENDING_DECISIONS.md #21 — cheap, clean re-run of Tier-3's two isolation-
tainted sub-results (dev-sanity: POTENTIALLY CONTAMINATED; held-out:
UNKNOWN), now that Finding 89/Tier-8's install_isolation() fix
(app.core.echo_model_orchestrator.RIVER_BRAIN_PATH redirected BEFORE the
first get_river_brain() call) is verified to hold even with a live,
actively-writing run.py process running concurrently -- confirmed
directly before this script was written (a live run.py, PID 54713, was
running at the time).

Reuses scripts/run_tier3_apparatus.py's real main()/main_heldout()
UNCHANGED -- only the two output-path constants are redirected (via
monkeypatch, before either function runs) to new, dated files, so this
re-run's genuinely clean data is never mixed into or overwrites the
original, already-analyzed (and already correctly labeled
POTENTIALLY CONTAMINATED / UNKNOWN) historical files.
"""
import sys
sys.path.insert(0, ".")
sys.path.insert(0, "scripts")

import run_tier3_apparatus as t3  # noqa: E402

_RERUN_SUFFIX = "_REISOLATED_RERUN_20260909"
t3.RESULTS_PATH = t3.RESULTS_PATH.replace(".jsonl", f"{_RERUN_SUFFIX}.jsonl")
t3.HELDOUT_RESULTS_PATH = t3.HELDOUT_RESULTS_PATH.replace(".jsonl", f"{_RERUN_SUFFIX}.jsonl")
print(f"[rerun-setup] dev-sanity output redirected to: {t3.RESULTS_PATH}")
print(f"[rerun-setup] held-out output redirected to:   {t3.HELDOUT_RESULTS_PATH}")

print("\n========== PHASE 1: dev-sanity re-run ==========")
t3.main()

print("\n========== PHASE 2: held-out re-run ==========")
pre_contention = t3._collect_contention_telemetry()
print(f"[rerun] contention check immediately before held-out phase: {pre_contention}")
t3.main_heldout()

print("\n[RERUN COMPLETE]")
