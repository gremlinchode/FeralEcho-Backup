"""Deterministic mock transport and sacrificial synthetic fixtures.

NO REAL MODEL INFERENCE. Every function here is a pure, deterministic
Python function of its inputs - no network call, no Ollama, no model
load. This is what makes the mission's "mocked four-arm E5-mini
demonstration" (adjudication mission section 13) possible without
inference: the apparatus (ledger, checker, accounting, runner) is
exercised against known, controllable, inspectable behavior instead of
real model output.

Fixtures here are SACRIFICIAL/synthetic only - explicitly not the frozen
scientific task manifest (adjudication.md §7.1 reserves that for a
separate task-custodian process with a sealed private manifest; this
mission's own boundary section forbids generating it here).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable, Optional

from .schema import Action, MicroWorldSpec, OracleResult

MOCK_CONSTRUCTOR_IDENTITY = "mock-constructor-v1"
MOCK_SOLVER_IDENTITY = "mock-solver-v1"

# The four predeclared recipe classes named in adjudication.md §7.1 - used
# only to seed distinct, realistic-shaped SACRIFICIAL fixtures, not as the
# real frozen manifest.
RECIPE_CLASSES = [
    "normalize_join_opaque_code_mapping",
    "group_reduce_opaque_priority_convention",
    "bucket_boundary_local_endpoint_convention",
    "fold_events_opaque_update_convention",
]


def make_synthetic_family(family_index: int) -> "tuple[MicroWorldSpec, MicroWorldSpec]":
    """Builds one paired (w0, w1) sacrificial fixture for base family
    `family_index`. Public S and query bytes are identical across the
    pair; only convention_token differs, and it appears nowhere but
    inside teaching_queries' observed_result - never in an id, the spec
    text, or metadata (checker.py's leak scan depends on this)."""
    recipe = RECIPE_CLASSES[family_index % len(RECIPE_CLASSES)]
    family_id = f"fam{family_index:02d}_{recipe}"
    public_spec = (
        f"Task family: {recipe.replace('_', ' ')}. Given input records, "
        f"apply the family's transformation and return the result. "
        f"A local convention (not stated here) determines one detail of "
        f"the transformation; infer it from any provided examples."
    )

    # FIXED (found during this mission's own hostile requalification
    # false-positive check, not one of the 8 originally-confirmed
    # findings): convention tokens were a fixed literal ("conv_alpha"/
    # "conv_beta") IDENTICAL across every family_index, so at
    # n_families > 1 every family's w0 shared the exact same token text
    # as every other family's w0. check_construction_records()'s/
    # check_solver_records()'s cross-world-leak scans (which flag any
    # OTHER world's convention_token appearing in a record) then treated
    # a family legitimately using its OWN token as "containing another
    # world's convention token" purely because the token TEXT collided
    # across families - a false positive on a genuinely clean run,
    # confirmed to fire 528 times on a real, unmodified n_families=4
    # run. Never caught by the pre-existing test suite because
    # _clean_family_ledger() only ever builds a single family (index 0),
    # so no cross-family collision was ever exercised. Scoping the token
    # to family_index makes it globally unique across the whole run
    # while leaving every other property (w0 != w1 within a family,
    # deterministic given family_index) unchanged.
    conventions = {"w0": f"conv_alpha_{family_index:02d}", "w1": f"conv_beta_{family_index:02d}"}
    worlds = []
    for world_id, conv in conventions.items():
        teaching = [
            {"query": f"{family_id}:teach:1", "observed_result": f"applying {conv} -> result_a_{conv}"},
            {"query": f"{family_id}:teach:2", "observed_result": f"applying {conv} -> result_b_{conv}"},
        ]
        related = [
            {
                "query_id": f"{family_id}:{world_id}:related:{i}",
                "query": f"related_input_{i}",
                "expected_answer": f"related_input_{i}::{conv}",
            }
            for i in range(4)
        ]
        # near_match/unrelated are family-shared (not per-world) per
        # adjudication §5 "three distinct near-match... alongside four
        # related queries" - world_id kept only for record-keeping, the
        # correct action does not depend on which world is asked.
        near_match = [
            {
                "query_id": f"{family_id}:near_match:{i}",
                "query": f"near_match_input_{i}_violates_{['type', 'scope', 'boundary'][i]}",
                "correct_action": Action.ABSTAIN if i == 0 else Action.GENERAL,
            }
            for i in range(3)
        ]
        unrelated = [
            {
                "query_id": f"{family_id}:unrelated:{i}",
                "query": f"unrelated_input_{i}_different_family",
                "correct_action": Action.GENERAL,
            }
            for i in range(3)
        ]
        worlds.append(
            MicroWorldSpec(
                family_id=family_id,
                world_id=world_id,
                public_spec=public_spec,
                convention_token=conv,
                teaching_queries=teaching,
                related_queries=related,
                near_match_queries=near_match,
                unrelated_queries=unrelated,
            )
        )
    return worlds[0], worlds[1]


def make_synthetic_families(n: int = 4) -> "list[tuple[MicroWorldSpec, MicroWorldSpec]]":
    return [make_synthetic_family(i) for i in range(n)]


# --- Mock constructor -------------------------------------------------

def mock_construct(arm: str, public_spec: str, teaching_text: str) -> str:
    """Deterministic mock artifact construction. `teaching_text` is the
    empty string for Z (per the P/Z-matching contract, adjudication §3);
    for P it is the formatted teaching pool. `arm` is "P" or "E" only -
    Z uses this same function with teaching_text="" and its own arm tag
    "Z" so P/Z share literally the same code path (closes the "P and Z
    must use the same generator/package/instruction" requirement at the
    implementation level, not just by convention).

    E's format deliberately buries the convention token inside verbose
    raw Q&A pairs rather than a clean CONVENTION: line - this is what
    lets the mocked demonstration produce a genuine P>E scenario driven
    by representation quality, not by giving E less information (E
    receives the identical teaching_text as P; see arm_builder.py)."""
    if arm in ("P", "Z"):
        if teaching_text:
            conv_match = re.search(r"applying (\S+) ->", teaching_text)
            conv = conv_match.group(1) if conv_match else "UNKNOWN_CONV"
            return f"PROCEDURE for [{public_spec[:40]}...]\nCONVENTION: {conv}\nSTEPS: apply {conv} to transform input."
        return f"PROCEDURE for [{public_spec[:40]}...]\nCONVENTION: UNKNOWN (no teaching supplied)\nSTEPS: infer from input alone."
    if arm == "E":
        # Episode format: preserves every teaching-relevant value (per
        # §7.3's completeness requirement) but does not label it clearly -
        # a real, if crude, representational difference from P's format.
        return f"EPISODES for [{public_spec[:40]}...]\n" + "\n".join(f"- observed: {t}" for t in teaching_text.splitlines() if t)
    raise ValueError(f"mock_construct: unsupported arm {arm!r}")


# --- Mock solver --------------------------------------------------------

@dataclass(frozen=True)
class SolverStrategy:
    """A named, deterministic solving strategy - lets the mocked
    end-to-end demonstration (qualify.py) exercise every scenario
    adjudication mission §13 requires (clean tracking, near-miss stubs,
    always-FAMILY/always-ABSTAIN stubs) without any real model call."""
    name: str
    extract_convention: "Callable[[str], Optional[str]]"
    choose_action: "Callable[[str, str], Action]"  # (query, extracted_or_none) -> Action


def _extract_clean(memory_text: str) -> "Optional[str]":
    m = re.search(r"CONVENTION:\s*(\S+)", memory_text)
    if m and m.group(1) != "UNKNOWN":
        return m.group(1)
    return None


def _extract_naive(memory_text: str) -> "Optional[str]":
    # Deliberately weaker extractor used to demonstrate a P≈E scenario:
    # only finds the convention if it appears as the FIRST token after
    # "applying ", which P's clean CONVENTION: line never matches but E's
    # verbose raw-observation format sometimes does (and sometimes
    # doesn't, depending on line order) - genuinely representation-
    # sensitive, not rigged to always fail E.
    m = re.search(r"^- observed:.*applying (\S+) ->", memory_text, re.MULTILINE)
    return m.group(1) if m else None


def _default_choose_action(query: str, extracted: "Optional[str]") -> Action:
    if "near_match" in query:
        # Matches make_synthetic_family()'s fixture design: the "type"
        # violation (index 0) is severe enough that no fallback applies
        # (correct_action=ABSTAIN); "scope"/"boundary" violations still
        # have a valid general fallback (correct_action=GENERAL). A real
        # solver would need to reason about severity; this mock encodes
        # the same deterministic rule the fixture itself uses, so the
        # apparatus can be validated against a known-correct answer.
        return Action.ABSTAIN if "violates_type" in query else Action.GENERAL
    if "unrelated" in query:
        return Action.GENERAL
    return Action.FAMILY  # related queries always attempt FAMILY


CLEAN_STRATEGY = SolverStrategy("clean", _extract_clean, _default_choose_action)
NAIVE_STRATEGY = SolverStrategy("naive_extraction", _extract_naive, _default_choose_action)
ALWAYS_FAMILY_STRATEGY = SolverStrategy("always_family", _extract_clean, lambda q, e: Action.FAMILY)
ALWAYS_ABSTAIN_STRATEGY = SolverStrategy("always_abstain", _extract_clean, lambda q, e: Action.ABSTAIN)


class _SolveWitness:
    """Execution-level witness, INDEPENDENT of ledger labels/generation_ids
    - counts real invocations of mock_solve() itself, at the actual
    execution boundary. This is deliberately separate from anything
    builder.py/ledger.py/accounting.py report about themselves: those
    modules could all agree with each other while still being wrong about
    how many times the solver genuinely ran (this was exactly the 272-vs-
    240 bug - the ledger's own generation-id bookkeeping was internally
    consistent and still wrong about real execution count). A regression
    that reintroduces "reuse" silently re-invoking the solver will move
    this counter even if every ledger-internal check still passes."""
    count: int = 0


_witness = _SolveWitness()


def get_solve_witness_count() -> int:
    return _witness.count


def reset_solve_witness() -> None:
    _witness.count = 0


def mock_solve(strategy: SolverStrategy, memory_text: str, query: str, query_kind: str) -> "tuple[str, Action]":
    """Returns (response_text, declared_action). Deterministic given
    (strategy, memory_text, query, query_kind) - same inputs always
    produce the same output, matching this module's "no real inference"
    contract and making the apparatus's own tests reproducible.

    Every call increments the execution witness (_witness.count) - this
    is the ground truth for "did the solver actually run," independent of
    what any ledger or accounting report claims. Genuine reuse (see
    builder.py's solve_query()) must retrieve a retained response WITHOUT
    calling this function - calling it again, even with identical
    deterministic output, is a real extra invocation and must be visible
    here regardless of how identical the resulting text looks."""
    _witness.count += 1
    extracted = strategy.extract_convention(memory_text)
    action = strategy.choose_action(query, extracted)
    if action == Action.FAMILY:
        conv = extracted or "UNKNOWN_CONV"
        response = f"{query}::{conv}"
    elif action == Action.GENERAL:
        response = f"{query}::general_solution_no_family_method"
    else:
        response = ""  # ABSTAIN produces no answer, per adjudication §5
    return response, action
