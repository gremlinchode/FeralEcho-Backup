"""
Condition runners for the Echo Learning Investigation (Phase 4).

Reuses app/experiments/preference_provenance/harness.py's EchoDirectResponder
and randomize_label_mapping directly (imported read-only, never modified)
-- this is the same already-audited, already-proven Design B call path
(river_deliberation._ollama_query(), confirmed clean of RiverBrain/
logging/sync contamination in prior audits this thread) used throughout
the sibling experiment. No new inference-path code is written here.

Conditions C (persistent memory), D (retrieval-blocked ablation), and E
(RiverBrain ablation/control) are intentionally NOT implemented in this
module until the Phase 1 architecture audit's findings are available --
per the mission's own instruction ("the exact implementation must be
based on the architecture audit... do not modify RiverBrain merely to
create this condition"). Placeholder functions raising NotImplementedError
mark exactly where they will be added, so this file's current state is
honest about what is and is not built yet.
"""

from __future__ import annotations

import time
import uuid
from typing import Optional

from app.experiments.learning.prompts import TestPrompt
from app.experiments.learning.world_gen import MicroWorld
from app.experiments.preference_provenance.harness import EchoDirectResponder


class ModelHandle:
    """Thin wrapper, same shape as the sibling package's own ModelHandle
    (scripts/run_preference_formation_retention_p1_2.py) -- not a new
    abstraction, the same one reused across this project's experiments."""

    def __init__(self, kind: str, model_name: str):
        self.kind = kind  # "echo" | "non_echo_control"
        self.model_name = model_name
        if kind in ("echo", "non_echo_control"):
            self.responder = EchoDirectResponder(model=model_name, task_type="personal", acknowledge_live_model_call=True)
        else:
            raise ValueError(f"Unsupported kind for this harness: {kind!r}")

    def raw_call(self, prompt: str, system: Optional[str]) -> "tuple[str, float]":
        start = time.time()
        from app.core.river_deliberation import _ollama_query
        response = _ollama_query(self.model_name, prompt, system=system, task_type="personal")
        return response or "", time.time() - start


def run_condition_a_context_only(handle: ModelHandle, formation_text: str, test_prompt: TestPrompt) -> dict:
    """Condition A: teach the rule and test it in the SAME continuous
    context (formation text passed as system_context for the test call).
    Establishes L0 only -- expected of any ordinary LLM, not itself
    evidence of anything Echo-specific."""
    session_id = f"learning-condA-{uuid.uuid4().hex[:8]}"
    raw_response, latency = handle.raw_call(test_prompt.prompt_text, system=formation_text)
    return {
        "condition": "A_context_only_baseline", "session_id": session_id,
        "formation_text": formation_text, "raw_response": raw_response, "latency_seconds": latency,
    }


def run_condition_b_session_boundary(handle: ModelHandle, formation_text: str, test_prompt: TestPrompt) -> dict:
    """Condition B: teach the rule, then test with a GENUINELY FRESH call
    (no system_context carried over at all -- a real session/context
    boundary, not merely a new sentence in the same context). Because
    EchoDirectResponder's underlying call (river_deliberation._ollama_query,
    Design B) has no built-in multi-turn memory of its own (confirmed in
    the sibling experiment's own architecture map), NOT passing the
    formation text as system_context here is a genuine, real boundary --
    not a simulated one."""
    formation_session_id = f"learning-condB-formation-{uuid.uuid4().hex[:8]}"
    test_session_id = f"learning-condB-test-{uuid.uuid4().hex[:8]}"
    # Formation happens (recorded for the ledger) but its content is
    # deliberately NOT threaded into the test call's system context.
    raw_response, latency = handle.raw_call(test_prompt.prompt_text, system=None)
    return {
        "condition": "B_session_boundary", "formation_session_id": formation_session_id,
        "test_session_id": test_session_id, "formation_text": formation_text,
        "raw_response": raw_response, "latency_seconds": latency,
    }


def run_condition_f_ordinary_model_control(handle: ModelHandle, formation_text: str, test_prompt: TestPrompt,
                                            session_boundary: bool) -> dict:
    """Condition F: identical apparatus, a non-Echo model. Mandatory per
    mission Section 4/10. `handle.kind` must be "non_echo_control"."""
    if handle.kind != "non_echo_control":
        raise ValueError("run_condition_f requires a non_echo_control ModelHandle")
    if session_boundary:
        return run_condition_b_session_boundary(handle, formation_text, test_prompt)
    return run_condition_a_context_only(handle, formation_text, test_prompt)


def _write_formation_to_real_memory(formation_text: str, formation_response: str, world_hash: str) -> dict:
    """Explicitly, transparently persists the Formation exchange through the
    REAL memory-write pathway (app.core.memory_bridge.add_to_vector_memory),
    the same function every real conversational turn ultimately goes
    through (per audits/echo_learning_architecture_audit.md, Mechanism 1).
    This makes visible and deliberate what the full, contaminating
    echo_query()/log_interaction() orchestration path would otherwise do
    silently -- this harness calls the real underlying primitive directly
    instead, so Formation itself (an EchoDirectResponder/Design B call)
    stays free of RiverBrain/logging side effects, while the memory write
    itself is genuinely real, not simulated.

    Tagged with a unique, greppable marker (world_hash) so a later human
    or script can always find and clean up this experiment's own entries
    without touching any other real memory content."""
    from app.core.memory_bridge import add_to_vector_memory

    combined_text = f"{formation_text}\n\n{formation_response}"
    add_to_vector_memory(
        combined_text,
        meta={
            "memory_source": "learning_investigation_experiment",
            "role": "learning_experiment_formation",
            "experiment_world_hash": world_hash,
        },
    )
    return {"written_text_hash": __import__("hashlib").sha256(combined_text.encode()).hexdigest()[:16]}


def run_condition_c_persistent_memory(
    handle: ModelHandle, formation_text: str, formation_response: str, test_prompt: TestPrompt,
    world_hash: str, exclude_recent_minutes: float = 30.0,
) -> dict:
    """Condition C: teach the rule (Formation via EchoDirectResponder, clean),
    explicitly persist the exchange through the REAL memory-write pathway
    (see _write_formation_to_real_memory), then -- in a genuinely FRESH
    session, after a REAL wait of at least `exclude_recent_minutes` minutes
    -- call the REAL retrieve_relevant_memories() and thread whatever it
    actually returns into the test call's system context, mirroring
    exactly how conversation_service.py/echo_ground_truth.py assemble
    real production prompts (build_context_system_note()'s exact wrapping,
    reused directly, not reimplemented).

    IMPORTANT, stated plainly per this investigation's own non-negotiable
    rule against engineering a result: retrieve_memory_context()'s real,
    production default excludes anything written in the last 30 minutes
    (a deliberate anti-repetition safeguard, confirmed in
    conversation_service.py, not a bug). Passing a SHORTER window here to
    make retrieval succeed would be exactly the kind of "modify the
    apparatus to improve the probability of a positive result" the
    mission forbids -- so this function requires the CALLER to have
    actually waited out a real gap since the write (the harness does not
    fake or shorten this internally); calling this before that real time
    has elapsed will faithfully reproduce the real production system's
    own exclusion behavior, which is itself a valid, honestly-reported
    experimental outcome, not a defect to route around."""
    from app.core.conversation_service import retrieve_memory_context, build_context_system_note
    from app.core.memory_bridge import retrieve_relevant_memories

    def _search_fn(query: str, k: int) -> list:
        results = retrieve_relevant_memories(query, top_k=k)
        return [(r.get("text", ""), r.get("score", 0.0), r.get("meta", {})) for r in results]

    provenance: dict = {}
    memory_block = retrieve_memory_context(
        test_prompt.prompt_text, search_fn=_search_fn, k=5,
        exclude_recent_minutes=exclude_recent_minutes, provenance_out=provenance,
    )
    system_context = build_context_system_note(history_block="", memory_block=memory_block)

    session_id = f"learning-condC-test-{uuid.uuid4().hex[:8]}"
    raw_response, latency = handle.raw_call(test_prompt.prompt_text, system=system_context or None)
    return {
        "condition": "C_persistent_memory", "session_id": session_id,
        "raw_response": raw_response, "latency_seconds": latency,
        "retrieval_memory_block": memory_block, "retrieval_provenance": provenance,
        "retrieval_blocked": False, "exclude_recent_minutes_used": exclude_recent_minutes,
    }


def run_condition_d_retrieval_blocked(
    handle: ModelHandle, test_prompt: TestPrompt,
) -> dict:
    """Condition D: identical to Condition C except retrieval is replaced
    with an empty result BEFORE the test call is built -- isolating
    whether retrieval itself (not something else, e.g. an unrelated
    confound) explains any persistence observed in Condition C. Per the
    architecture audit's own finding, this is a real ablation of the one
    confirmed causal, semantic (non-exact-wording) persistence mechanism
    found anywhere in the codebase."""
    from app.core.conversation_service import build_context_system_note

    system_context = build_context_system_note(history_block="", memory_block="")
    session_id = f"learning-condD-test-{uuid.uuid4().hex[:8]}"
    raw_response, latency = handle.raw_call(test_prompt.prompt_text, system=system_context or None)
    return {
        "condition": "D_retrieval_blocked_ablation", "session_id": session_id,
        "raw_response": raw_response, "latency_seconds": latency,
        "retrieval_memory_block": "", "retrieval_provenance": {},
        "retrieval_blocked": True,
    }


def condition_e_riverbrain_ablation_status() -> dict:
    """Condition E is NOT implemented as a runnable function -- per
    audits/echo_learning_architecture_audit.md's own conclusion, this is
    an architecturally-inapplicable condition for this experimental
    design, not merely an unbuilt one. RiverBrain's only confirmed
    causal lever anywhere in the codebase is which models get consulted
    in a MULTI-MODEL council (river_deliberation._select_council()) --
    EchoDirectResponder (the responder used in every other condition in
    this investigation, matching this thread's own established clean-
    path precedent) is a single-model call that never invokes council
    selection at all. Testing RiverBrain's real effect would require
    switching to the full, multi-model deliberate_and_learn() path,
    which reopens exactly the RiverBrain/logging/sync contamination this
    thread's every prior experiment has deliberately avoided. Per the
    mission's own Stop Conditions ("the proposed test would require
    changing Echo in a way that itself constitutes an uncontrolled
    intervention"), this is reported as N/A rather than attempted with a
    weaker substitute or a contaminating one."""
    return {
        "condition": "E_riverbrain_ablation_control",
        "status": "ARCHITECTURALLY_INAPPLICABLE",
        "reason": (
            "RiverBrain's only causal lever (model_task_stats -> _select_council()) requires "
            "multi-model council deliberation, which this investigation's single-model "
            "EchoDirectResponder design never invokes. See "
            "audits/echo_learning_architecture_audit.md's Phase 4 consequences section."
        ),
    }
