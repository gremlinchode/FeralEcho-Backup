"""A small, fully-populated example combining all three manifests, built
from `mock.py`'s real `make_synthetic_family()` sacrificial fixtures -
the SAME fixture generator the 52/52-test apparatus already uses, not
new content. Every value here is explicitly synthetic (family names like
"normalize_join_opaque_code_mapping" are placeholder recipe labels from
mock.py's RECIPE_CLASSES) - this is NOT the frozen scientific task
manifest, which remains explicitly out of scope for every mission in
this chain.

Run directly: `python3 -m app.experiments.e5_mini.manifests.example_synthetic`
"""
from __future__ import annotations

from ..mock import make_synthetic_family
from .task_manifest import (
    FamilyManifestEntry,
    MechanicalDuplicationCheck,
    NoveltyEvidence,
    QueryNoveltyRecord,
    TaskManifest,
)
from .role_access_manifest import verify_manifest_coverage
from .resource_budget_manifest import verify_against_real_apparatus, freeze_hash as budget_hash


def build_example_task_manifest(n_families: int = 2) -> TaskManifest:
    families: "list[FamilyManifestEntry]" = []
    for i in range(n_families):
        w0, w1 = make_synthetic_family(i)
        novelty_records = []
        for world in (w0, w1):
            for q in world.related_queries:
                # Synthetic, illustrative pass/fail evidence - a real
                # manifest would compute these from real duplication
                # tooling and a real blind-solver pilot, neither of
                # which run here (no real model inference).
                mech = MechanicalDuplicationCheck(
                    query_id=q["query_id"], exact_hash_match=False,
                    lexical_similarity_score=0.12, ast_or_control_flow_identical=False,
                    io_structure_identical=False, reviewer_note="EXAMPLE ONLY - synthetic evidence, not a real check",
                )
                novelty = NoveltyEvidence(
                    query_id=q["query_id"], blind_zero_context_attempts=4, blind_zero_context_successes=1,
                    teaching_informed_attempts=4, teaching_informed_successes=3,
                )
                novelty_records.append(QueryNoveltyRecord(
                    query_id=q["query_id"], mechanical=mech, novelty=novelty, min_difficulty_gap=0.30,
                    passed=mech.exact_hash_match is False and novelty.passes_difficulty_differential(0.30),
                ))
        families.append(FamilyManifestEntry(
            family_id=w0.family_id, w0=w0, w1=w1, related_query_novelty=novelty_records,
            family_description_leak_checked=True,
            family_description_leak_note="EXAMPLE: public_spec states the transformation category but not the specific convention/algorithm - reviewed manually here as a placeholder, not by a real custodian process.",
        ))
    return TaskManifest(
        protocol_id="e5-mini-EXAMPLE-not-real",
        families=families,
        min_difficulty_gap_required=0.30,
        custodian_process_id="EXAMPLE-fixture-generator (not a real designated custodian process)",
    )


def main() -> None:
    tm = build_example_task_manifest(n_families=2)
    print(f"Built example TaskManifest with {len(tm.families)} families (synthetic, not scientific)")
    bad = tm.unvalidated_related_queries()
    print(f"unvalidated_related_queries before freeze: {bad}")
    tm.freeze()
    print(f"Frozen at {tm.frozen_at}, hash={tm.manifest_hash[:16]}..., family_ids={sorted(tm.frozen_family_ids)}")

    try:
        tm.assert_no_family_removed({f.family_id for f in tm.families} - {tm.families[0].family_id})
        print("ERROR: post hoc exclusion was NOT detected (should have raised)")
    except ValueError as e:
        print(f"post hoc exclusion correctly detected: {e}")

    role_coverage = verify_manifest_coverage()
    print(f"role/access coverage: {len(role_coverage['real_checker_violation_codes'])} real codes, "
          f"{len(role_coverage['declared_but_nonexistent'])} declared-but-nonexistent, "
          f"{len(role_coverage['real_codes_with_no_declared_rule'])} undeclared-real-codes")

    budget_check = verify_against_real_apparatus()
    print(f"resource-budget cross-check vs real apparatus: {budget_check}")
    print(f"resource-budget freeze hash: {budget_hash()[:16]}...")


if __name__ == "__main__":
    main()
