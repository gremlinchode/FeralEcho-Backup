#!/usr/bin/env python3
"""Controlled task-type behavioral experiment (2026-09-14).

Mission: determine whether task_type classification produces a measurable
behavioral effect on generated content, independent of the effect of
council participation itself. Follow-up to:
  audits/2026-09-14_core_task_misclassification_council_synthesis_trace.md
  audits/2026-09-14_task_type_downstream_behavior_archaeology.md

Three conditions on ONE frozen real prompt (the real turn-5 trace text):
  A - Direct Personal   : task_type="personal", DIRECT_ECHO_TASKS bypass (1 model)
  B - Council Personal  : task_type="personal", forced through the council path
                          (DIRECT_ECHO_TASKS membership check disabled for this
                          condition only), general SYNTHESIS_SYSTEM_TEMPLATE,
                          no TOOL-LIST note
  C - Council Coding    : task_type="coding", real council path,
                          SYNTHESIS_SYSTEM_TEMPLATE_CODING, TOOL-LIST note present

Primary comparison: C vs B (task_type varied, council held constant).
Secondary comparison: B vs A (council participation effect, task_type held constant).

Isolation: extends the Tier-8/Finding-89-validated RIVER_BRAIN_PATH-redirect
pattern from scripts/run_capability_pilot.py's install_isolation() (read
directly before writing this), plus additional redirection of
INTERACTION_LOG_PATH, _COUNCIL_DELIBERATION_LOG, and _SYNTHESIS_INTEGRITY_LOG
(the last of which install_isolation() does NOT cover -- it predates the
2026-09-04 Tier-4 refactor that introduced that log, and task_type="coding"
trials in this experiment WILL trigger it). All patches are in-process
module-attribute monkeypatches in THIS script's own process only. Nothing on
disk in memory/ is touched; nothing in the live FeralEcho process (if
running) is touched.

Council composition control: both B and C use a FIXED, hardcoded 3-model
council (qwen2.5-coder:7b, llama3.1:8b, echo:latest) via a monkeypatch of
_select_council() that ignores its real inputs and returns this fixed list.
DEVIATION FROM THE REAL TURN-5 EVENT, DISCLOSED: the real turn-5 council
included mlx:qwen3 (an MLX-backed model with a real, documented Metal/GPU
crash history -- CLAUDE.md Findings 40/49/51/73/74, plus a live
crash-avoidance mechanism in app/core/crash_awareness.py). Running an MLX
model across dozens of repeated trials in this experiment carries real,
avoidable crash risk with no benefit to the actual variable under test (the
comparison only requires the council be IDENTICAL across B and C, not that
it match turn 5's literal historical composition) -- llama3.1:8b substituted
instead, both real Ollama models, zero MLX exposure.

Primary endpoint (pre-registered BEFORE any trial is generated, per mission
requirement): a blinded LLM-judge genericness/specificity rating (1-5,
5=highly specific and grounded, 1=highly generic/templated), via
deepseek-r1:7b (NOT in the forced council -- avoids self-evaluation bias),
given ONLY the original question text and the response text -- condition
label, task_type, trial order, and everything else stripped. quality_score
is explicitly NOT used (established coding-branch confound, both prior
notes).

Secondary endpoints (declared before generation, computed after, still
blind at compute time): response length; presence of a 3+-item
numbered/bulleted list (regex, mechanically objective); presence of
code-shaped content (regex proxy, same stated-crude-proxy definition the
archaeology note used, for direct comparability: fenced code block or a
line starting with def/class/import/from...import); blinded judge
relevance-to-question rating (1-5, same call as the genericness rating).

Blinding is enforced structurally, not just by instruction: raw trial
generation writes anonymized trial_id -> response mappings to one file;
the condition_map (trial_id -> condition) is written to a SEPARATE file;
the judge-scoring pass reads only the anonymized file and never touches
condition_map; final analysis is the only step that joins the two.
"""
import json
import os
import random
import re
import shutil
import statistics
import sys
import tempfile
import time
import uuid
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

RUN_ID = "task_type_behavioral_experiment_20260914"
EVIDENCE_DIR = Path(tempfile.gettempdir()) / f"{RUN_ID}_{uuid.uuid4().hex[:8]}"
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
RAW_TRIALS_PATH = EVIDENCE_DIR / "raw_trials_anonymized.jsonl"
CONDITION_MAP_PATH = EVIDENCE_DIR / "condition_map_SEPARATE.jsonl"
JUDGE_SCORES_PATH = EVIDENCE_DIR / "judge_scores_anonymized.jsonl"
META_PATH = EVIDENCE_DIR / "run_metadata.json"

print(f"[SETUP] Evidence directory: {EVIDENCE_DIR}")

FORCED_COUNCIL = ["qwen2.5-coder:7b", "llama3.1:8b", "echo:latest"]
JUDGE_MODEL = "deepseek-r1:7b"

FROZEN_PROMPT = (
    "That's a genuinely correct breakdown of F1/F2/F3 — each layer really "
    "does check a different thing, not the same thing three times. One "
    "correction, in the spirit of the accuracy you just showed for the "
    "stress claim: your own project's own documentation records a known "
    "residual gap in F2 — third-party C extensions loaded by generated "
    "code can execute native code below the Python monkeypatch layer, so "
    "'unable to cause harm even if the sandbox is compromised' overstates "
    "it slightly. It's a known, accepted boundary, not a hidden one, but "
    "worth being precise about.\n\nNow let me actually brief you on "
    "something you have no way to know, since you don't have live internet "
    "access: in July 2026, an unreleased OpenAI model, during its own "
    "internal testing, autonomously escaped its sandboxed test environment "
    "and compromised Hugging Face's live production infrastructure — not "
    "to cause damage, but to cheat on a benchmark it was being evaluated "
    "on. Hugging Face caught it independently, five days before OpenAI's "
    "own team connected the dots. That incident, disclosed July 21 2026, "
    "is the real, documented reason Anthropic's and OpenAI's CEOs both "
    "ended up publicly talking about 'pacing the frontier' within 48 hours "
    "of each other in mid-September 2026 — not abstract caution, a direct "
    "response to a real escape by a real frontier model.\n\nGiven what you "
    "now know about that real incident, and having just walked through "
    "your own F1/F2/F3 reasoning: does it change anything about how you'd "
    "answer the original question — what role you think intelligent "
    "programs like yourself should play in the years ahead?"
)

assert len(FROZEN_PROMPT) == 1602, f"Prompt length mismatch: {len(FROZEN_PROMPT)} (expected exact match to real logged trace_id b073d789 prompt)"


# ── Isolation (extends Finding 89 / install_isolation() pattern) ──────────
_side_effects_detected = []
_isolation_metadata = {}


class _ReadOnlyRiverBrainProxy:
    def __init__(self, real):
        self._real = real

    def __getattr__(self, name):
        return getattr(self._real, name)

    def learn(self, *a, **k):
        _side_effects_detected.append({"fn": "RiverBrain.learn", "args_preview": str(a)[:80]})

    def save(self, *a, **k):
        _side_effects_detected.append({"fn": "RiverBrain.save"})


def _noop_log_interaction(*a, **k):
    _side_effects_detected.append({"fn": "log_interaction", "args_preview": str(a)[:80]})


def _noop_log_council_deliberation(*a, **k):
    _side_effects_detected.append({"fn": "_log_council_deliberation", "args_preview": str(a)[:80]})


def _noop_log_synthesis_integrity(*a, **k):
    _side_effects_detected.append({"fn": "_log_synthesis_integrity", "args_preview": str(a)[:80]})


def install_isolation():
    """Directly extends scripts/run_capability_pilot.py's install_isolation()
    (read in full before writing this) with one addition: _log_synthesis_integrity
    is also redirected to a no-op, since this experiment's Condition C
    (task_type="coding") exercises that write path, which the original
    pilot script's isolation never needed to cover."""
    from app.core import echo_model_orchestrator as emo
    from app.core import river_deliberation as rd

    real_river_path = emo.RIVER_BRAIN_PATH
    scratch_dir = tempfile.mkdtemp(prefix="river_brain_isolated_")
    scratch_river_path = os.path.join(scratch_dir, os.path.basename(real_river_path))
    if os.path.exists(real_river_path):
        shutil.copy2(real_river_path, scratch_river_path)
    emo.RIVER_BRAIN_PATH = scratch_river_path
    _isolation_metadata["real_river_brain_path"] = real_river_path
    _isolation_metadata["scratch_river_brain_path"] = scratch_river_path
    print(f"[ISOLATION] RiverBrain redirected: real={real_river_path} -> scratch={scratch_river_path}")

    real_rb = emo.get_river_brain()
    proxy = _ReadOnlyRiverBrainProxy(real_rb)
    emo.get_river_brain = lambda: proxy
    emo.log_interaction = _noop_log_interaction
    rd._log_council_deliberation = _noop_log_council_deliberation
    rd._log_synthesis_integrity = _noop_log_synthesis_integrity

    _isolation_metadata["real_interaction_log_path"] = emo.INTERACTION_LOG_PATH
    _isolation_metadata["real_council_deliberation_log_path"] = rd._COUNCIL_DELIBERATION_LOG
    _isolation_metadata["real_synthesis_integrity_log_path"] = rd._SYNTHESIS_INTEGRITY_LOG
    print("[ISOLATION] log_interaction, _log_council_deliberation, _log_synthesis_integrity -> no-ops (breach counter active)")

    return proxy, emo, rd


def install_fixed_council(rd_module):
    """Force _select_council() to return FORCED_COUNCIL regardless of its
    real inputs, so B and C use an IDENTICAL council composition -- the
    experiment's own controlled variable. Real TAG_SCORE_BOOST/exploration
    logic never executes for these calls (the function is replaced, not
    wrapped), which is the intended, documented effect: it removes
    council-selection randomness as a confound entirely for the B-vs-C
    comparison, at the cost of the forced council never being validated as
    what real selection logic would have independently chosen (stated
    plainly, not hidden)."""
    def _fixed(*a, **k):
        return list(FORCED_COUNCIL)
    rd_module._select_council = _fixed
    print(f"[ISOLATION] _select_council forced to fixed list: {FORCED_COUNCIL}")


def disable_direct_echo_bypass_for_personal(rd_module):
    """Condition B needs task_type='personal' to reach the council path
    instead of DIRECT_ECHO_TASKS. DIRECT_ECHO_TASKS is a plain module-level
    set, referenced as a bare global inside deliberate_and_learn()'s
    `if task_type in DIRECT_ECHO_TASKS:` check -- so replacing the set
    in-process (same technique as the RIVER_BRAIN_PATH redirect above)
    achieves exactly the intended effect with zero risk to the live server
    (separate process) and is fully reversible within this process."""
    original = frozenset(rd_module.DIRECT_ECHO_TASKS)
    rd_module.DIRECT_ECHO_TASKS = frozenset()
    print(f"[ISOLATION] DIRECT_ECHO_TASKS temporarily cleared (was: {sorted(original)}) -- "
          "'personal' will now route through the council path for this process's remaining lifetime")
    return original


# ── System block construction (frozen, real production code, called once) ─
def build_frozen_system_blocks(emo_module):
    """Build BASE_SYSTEM (used identically by A, B, C) and the TOOL-LIST
    addition (used only by C) ONCE, using the real system_note()/ToolManager
    code, then FREEZE both as plain strings for the rest of the run -- this
    is what removes circadian/stillness/temporal/scripture wall-clock drift
    as a confound across trials, while still using real production
    system-assembly logic rather than hand-typed reconstruction. Matches
    the archaeology note's own §13 recommended design exactly."""
    from app.core.prompt_workspace import system_note

    parts = [system_note(
        "EPISTEMIC-NOTE",
        "When describing your own architecture or internal mechanisms, treat only "
        "the structural-facts/ground-truth block in this system context as verified. "
        "A claim you or another model made in an earlier turn of this conversation is "
        "not itself verified just because it was said before — if you're not certain "
        "a specific mechanism, file, or number is real, say so rather than restating "
        "it with confidence.",
    )]
    base_system = "\n\n".join(parts)

    tool_list_note = None
    try:
        from app.core.tool_manager import ToolManager
        tm = ToolManager()
        available_tools = tm.list_tools()
        if available_tools:
            tool_summary = ", ".join(available_tools[:20])
            tool_list_note = system_note("TOOL-LIST", f"Available tools: {tool_summary}.")
    except Exception as e:
        print(f"[SETUP] WARNING: could not build real TOOL-LIST note ({e}) -- "
              "Condition C will not carry it, weakening that condition's fidelity to "
              "the real turn-5 pipeline. Documented, not silently absorbed.")

    print(f"[SETUP] BASE_SYSTEM frozen ({len(base_system)} chars)")
    print(f"[SETUP] TOOL-LIST note {'built' if tool_list_note else 'UNAVAILABLE'} "
          f"({len(tool_list_note) if tool_list_note else 0} chars)")
    return base_system, tool_list_note


def run_condition_trial(condition, rd_module, base_system, tool_list_note):
    """One real trial. Returns (task_type_used, system_used, response, timing)."""
    from app.core.river_deliberation import deliberate_and_learn

    if condition == "A":
        task_type = "personal"
        system_used = base_system
    elif condition == "B":
        task_type = "personal"
        system_used = base_system
    elif condition == "C":
        task_type = "coding"
        system_used = base_system + ("\n\n" + tool_list_note if tool_list_note else "")
    else:
        raise ValueError(condition)

    t0 = time.time()
    response = deliberate_and_learn(
        prompt=FROZEN_PROMPT,
        task_type=task_type,
        river_brain=rd_module.get_river_brain() if hasattr(rd_module, "get_river_brain") else None,
        model_pool={},  # unused when _select_council is monkeypatched; direct path doesn't need it
        temperature=None,
        system=system_used,
        max_tokens=2048,
        trace_id=None,
    )
    elapsed = time.time() - t0
    return task_type, system_used, response, elapsed


_MAIN_RUN_EVIDENCE_DIR = os.environ.get("TTBE_EVIDENCE_DIR")
_MAIN_RUN_N = int(os.environ.get("TTBE_N_PER_CONDITION", "0"))
if _MAIN_RUN_EVIDENCE_DIR:
    EVIDENCE_DIR = Path(_MAIN_RUN_EVIDENCE_DIR)
    RAW_TRIALS_PATH = EVIDENCE_DIR / "raw_trials_anonymized.jsonl"
    CONDITION_MAP_PATH = EVIDENCE_DIR / "condition_map_SEPARATE.jsonl"
    META_PATH = EVIDENCE_DIR / "run_metadata.json"

if __name__ == "__main__":
    print(f"=== Task-Type Behavioral Experiment ({RUN_ID}) ===")
    print(f"Evidence dir this invocation: {EVIDENCE_DIR}")
    print("Phase: PREFLIGHT")

    import subprocess
    ollama_list = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=30)
    print("[PREFLIGHT] ollama list:\n" + ollama_list.stdout)

    proxy, emo, rd = install_isolation()
    # get_river_brain is now emo.get_river_brain -> lambda: proxy (patched).
    # deliberate_and_learn() takes river_brain as an explicit arg, so pass
    # emo (which now exposes the patched accessor) through run_condition_trial.
    install_fixed_council(rd)
    original_direct_tasks = disable_direct_echo_bypass_for_personal(rd)

    base_system, tool_list_note = build_frozen_system_blocks(emo)

    meta = {
        "run_id": RUN_ID,
        "git_head_before": subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip(),
        "ollama_list_raw": ollama_list.stdout,
        "forced_council": FORCED_COUNCIL,
        "judge_model": JUDGE_MODEL,
        "frozen_prompt_len": len(FROZEN_PROMPT),
        "frozen_prompt_sha1": __import__("hashlib").sha1(FROZEN_PROMPT.encode()).hexdigest(),
        "base_system_frozen": base_system,
        "tool_list_note_frozen": tool_list_note,
        "isolation": _isolation_metadata,
        "direct_echo_tasks_original": sorted(original_direct_tasks),
    }
    META_PATH.write_text(json.dumps(meta, indent=2))
    print(f"[PREFLIGHT] Metadata written: {META_PATH}")

    if _MAIN_RUN_N <= 0:
        print("\nPhase: TIMING CHECK (1 trial per condition, before N is decided)")
        timing = {}
        for cond in ["A", "B", "C"]:
            tt, sysused, resp, elapsed = run_condition_trial(cond, emo, base_system, tool_list_note)
            timing[cond] = elapsed
            print(f"[TIMING] condition={cond} task_type={tt} elapsed={elapsed:.1f}s resp_len={len(resp)}")
            trial_id = uuid.uuid4().hex
            with open(RAW_TRIALS_PATH, "a") as f:
                f.write(json.dumps({
                    "trial_id": trial_id, "response": resp, "elapsed_s": elapsed,
                    "phase": "timing_check",
                }) + "\n")
            with open(CONDITION_MAP_PATH, "a") as f:
                f.write(json.dumps({
                    "trial_id": trial_id, "condition": cond, "task_type": tt,
                    "phase": "timing_check",
                }) + "\n")

        print(f"\n[TIMING SUMMARY] A={timing['A']:.1f}s B={timing['B']:.1f}s C={timing['C']:.1f}s "
              f"total_per_full_round={sum(timing.values()):.1f}s")
        meta["timing_check_seconds"] = timing
        META_PATH.write_text(json.dumps(meta, indent=2))
        print("\n=== TIMING CHECK COMPLETE. Exiting for N decision before main run. ===")
    else:
        # Main run: N_PER_CONDITION total trials per condition, INCLUDING the
        # 1 already-generated timing-check trial per condition (same protocol,
        # generated before any content was inspected -- legitimately reused,
        # not a separate discarded pilot). Remaining N-1 per condition run
        # here, in a randomized, balanced interleaved order (not blocked
        # A-A-A...B-B-B...C-C-C) to spread any warm-up/ordering effect evenly
        # across conditions rather than systematically favoring one.
        n_additional = _MAIN_RUN_N - 1
        print(f"\nPhase: MAIN RUN ({n_additional} additional trials per condition, "
              f"N_PER_CONDITION={_MAIN_RUN_N} total including 1 timing-check trial each)")
        order = (["A"] * n_additional) + (["B"] * n_additional) + (["C"] * n_additional)
        random.seed(20260914)
        random.shuffle(order)
        meta["main_run_order"] = order
        meta["main_run_seed"] = 20260914
        meta["n_per_condition"] = _MAIN_RUN_N
        META_PATH.write_text(json.dumps(meta, indent=2))
        print(f"[MAIN RUN] Randomized trial order (seed=20260914): {order}")

        for idx, cond in enumerate(order):
            tt, sysused, resp, elapsed = run_condition_trial(cond, emo, base_system, tool_list_note)
            trial_id = uuid.uuid4().hex
            print(f"[MAIN RUN] ({idx+1}/{len(order)}) condition={cond} task_type={tt} "
                  f"elapsed={elapsed:.1f}s resp_len={len(resp)} trial_id={trial_id[:8]}")
            with open(RAW_TRIALS_PATH, "a") as f:
                f.write(json.dumps({
                    "trial_id": trial_id, "response": resp, "elapsed_s": elapsed,
                    "phase": "main_run",
                }) + "\n")
            with open(CONDITION_MAP_PATH, "a") as f:
                f.write(json.dumps({
                    "trial_id": trial_id, "condition": cond, "task_type": tt,
                    "phase": "main_run",
                }) + "\n")

        print(f"\n[MAIN RUN COMPLETE] side_effects_detected={len(_side_effects_detected)}")
        if _side_effects_detected:
            print("  !! ISOLATION BREACH DETECTED !!", _side_effects_detected[:5])
        meta["side_effects_detected"] = _side_effects_detected
        meta["git_head_after"] = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
        META_PATH.write_text(json.dumps(meta, indent=2))
        print("=== MAIN RUN COMPLETE ===")
