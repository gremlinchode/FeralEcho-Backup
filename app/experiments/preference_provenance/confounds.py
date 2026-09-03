"""
Confound snapshotting.

Per audits/2026-09-03_echo_preference_provenance.md §16's confound
matrix and the mission's Section 21: every trial must record enough
about its own conditions that a later analyst can check whether an
observed effect is actually explained by one of these confounds rather
than by the candidate preference itself.

This module only builds a ConfoundSnapshot from explicit values the
caller supplies — it does not itself call any production code to
"discover" these values, since doing so would reintroduce exactly the
production-import coupling safety.py's docstring argues against. A real
EchoResponder (harness.py) is the place that would gather real values
(e.g. the actual system-prompt text) and pass them in here.
"""

from __future__ import annotations

import hashlib
from typing import Optional

from .schema import ConfoundSnapshot


def hash_text(text: Optional[str]) -> Optional[str]:
    """Stable, short hash for logging without storing full raw content
    twice when a full copy is already stored elsewhere (e.g. raw_prompt
    on RawTrial) — used for fields where only reconstruction-checking,
    not full replay, is needed."""
    if text is None:
        return None
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def build_confound_snapshot(
    *,
    creator_instruction_present: bool,
    system_prompt_text: Optional[str],
    persona_block_present: bool,
    model_name: Optional[str],
    temperature: Optional[float],
    context_length_tokens: Optional[int],
    conversation_history_present: bool,
    tool_list_present: bool,
    retrieved_memory_present: bool,
    option_label_mapping: dict,
    sampling_params: Optional[dict] = None,
    notes: str = "",
) -> ConfoundSnapshot:
    return ConfoundSnapshot(
        creator_instruction_present=creator_instruction_present,
        system_prompt_hash=hash_text(system_prompt_text),
        persona_block_present=persona_block_present,
        model_name=model_name,
        temperature=temperature,
        context_length_tokens=context_length_tokens,
        conversation_history_present=conversation_history_present,
        tool_list_present=tool_list_present,
        retrieved_memory_present=retrieved_memory_present,
        option_label_mapping=dict(option_label_mapping),
        sampling_params=dict(sampling_params or {}),
        notes=notes,
    )
