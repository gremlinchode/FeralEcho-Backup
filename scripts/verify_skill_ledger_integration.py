#!/usr/bin/env python3
"""Integration-readiness regression suite for the Verified Skill Ledger (Phase 17/20
of audits/2026-09-28_vsl_integration_readiness.md). Every check here is either
synthetic-but-isolated (a scratch root, never touching real production or
experimental state) or a direct, real invocation of the actual production pipeline
with cleanup performed immediately after -- same discipline as
verify_diff_extract.py/verify_liveness_ledger.py's own synthetic-discrimination
convention, extended to a real end-to-end integration.

Run: python3 -B scripts/verify_skill_ledger_integration.py
"""
from __future__ import annotations
import os
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

_checks = []


def check(name, cond):
    _checks.append((name, bool(cond)))
    print(f"[{'OK' if cond else 'FAIL'}] {name}")


def main():
    # Keep the real environment's VSL_ENABLED/VSL_MODE untouched after this run.
    orig_env = {k: os.environ.get(k) for k in ("VSL_ENABLED", "VSL_MODE")}

    try:
        _run_all()
    finally:
        for k, v in orig_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    print()
    n_fail = sum(1 for _, ok in _checks if not ok)
    print(f"{len(_checks) - n_fail}/{len(_checks)} checks passed.")
    if n_fail:
        sys.exit(1)
    print("verify_skill_ledger_integration.py: ALL CHECKS PASSED.")


def _run_all():
    # ---- 1. Core imports cleanly; historical experiment suite unaffected. ----
    import subprocess
    result = subprocess.run(
        [sys.executable, "-B", "app/experiments/skill_ledger/verify_diff_extract.py"],
        capture_output=True, text=True, cwd=str(Path(__file__).resolve().parents[1]),
    )
    check("historical VSL unit suite (verify_diff_extract.py) still 15/15",
          result.returncode == 0 and "15/15 checks passed" in result.stdout)

    from app.core.skill_ledger import matcher, schemas, store, runtime, echo_adapter
    check("production core (matcher/schemas/store/runtime/echo_adapter) imports cleanly", True)

    # ---- 2. Real legacy skill files load with unchanged content hashes. ----
    a = schemas.Skill.load("memory/experiments/skill_ledger/skills/K2.T5.tag_priority_direction.v5.json")
    check("real Skill A (v5) content_hash unchanged under new schema",
          a.content_hash() == "a5408f732897df353eb9ad6c6d8d2390794319910dd2ff5a4bd9da28a833501d")
    b = schemas.Skill.load("memory/experiments/skill_ledger/skills/K2.T2.discovered_via_accumulation_test.v1.json")
    check("real Skill B (v1) content_hash unchanged under new schema",
          b.content_hash() == "1f5ce81e6d31a68cf0427f8d566977c45f648af17b280d8698c83965ef6bfbd0")

    # ---- 2b. Adversarial-review fixes (2026-09-28), dedicated regression coverage. ----
    import os as _os
    _marker = "/tmp/vsl_eval_escape_regression_marker.txt"
    if _os.path.exists(_marker):
        _os.remove(_marker)
    escape_expr = (
        "[c for c in ().__class__.__base__.__subclasses__() if c.__name__=='catch_warnings'][0]()"
        f"._module.__builtins__['__import__']('os').system('echo PWNED > {_marker}')"
    )
    r1 = matcher._rehydrate(escape_expr, {})
    check("SECURITY: _rehydrate() no longer executes arbitrary content via eval() "
          "(the exact escape found in the 2026-09-28 adversarial review)",
          r1 is None and not _os.path.exists(_marker))
    r2 = matcher.apply_skill("def target_fn():\n    return 1", "target_fn",
                              {"precondition": "Constant(value=1)", "transformation": escape_expr,
                               "node_type": "Constant", "enclosing_call": None})
    check("SECURITY: apply_skill() (the real production entry point) is unaffected by the same payload",
          r2 is None and not _os.path.exists(_marker))
    check("legitimate reconstruction still works after the eval() fix (negative-number literal)",
          getattr(matcher._rehydrate("Constant(value=-5)", {}), "value", None) == -5)

    with tempfile.TemporaryDirectory() as _td:
        _corrupt_dir = Path(_td) / "skills"
        _corrupt_dir.mkdir(parents=True)
        (_corrupt_dir / "TEST.corrupted.v1.json").write_text('{"feature_key": "TEST.corrupted"}')  # missing required keys
        _orig_schemas_dir = schemas.SKILLS_DIR
        _prior_vsl_enabled, _prior_vsl_mode = _os.environ.get("VSL_ENABLED"), _os.environ.get("VSL_MODE")
        schemas.SKILLS_DIR = _corrupt_dir
        _os.environ["VSL_ENABLED"] = "true"
        _os.environ["VSL_MODE"] = "shadow"
        try:
            listed = runtime._list_active_feature_keys()
            check("SECURITY: a corrupted/malformed skill file degrades to being skipped, "
                  "not an unhandled exception out of _list_active_feature_keys()",
                  listed == [])
            r3 = runtime.consult("def f(): pass", "f")
            check("SECURITY: consult()'s default (no explicit feature_keys) path -- the one "
                  "echo_adapter.py actually uses in production -- fails closed against a "
                  "corrupted store instead of raising",
                  r3.mode != "disabled" and r3.applied is False and r3.matched_feature_key is None)
        finally:
            schemas.SKILLS_DIR = _orig_schemas_dir
            for _k, _v in (("VSL_ENABLED", _prior_vsl_enabled), ("VSL_MODE", _prior_vsl_mode)):
                if _v is None:
                    _os.environ.pop(_k, None)
                else:
                    _os.environ[_k] = _v

    check("FIXED: monkeypatching schemas.SKILLS_DIR now correctly affects runtime.py's "
          "own default (no-feature_keys) lookup path too (the aliasing gap the review found)",
          runtime.schemas.SKILLS_DIR is schemas.SKILLS_DIR)

    # ---- 3. Lifecycle machinery, in an isolated scratch root. ----
    buggy_code = (
        "def winner_with_score(entries):\n"
        "    tag_priority = {'p': 1, 'q': 2, 'r': 3, 's': 4}\n"
        "    sorted_entries = sorted(entries, key=lambda x: (-x[1], -tag_priority[x[2]], x[0]))\n"
        "    return sorted_entries[0][0], sorted_entries[0][1]"
    )
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        skills_root = root / "skills"
        apps_log = root / "applications.jsonl"

        # Dedicated feature_key for this lifecycle-only test block, deliberately
        # DISTINCT from a.feature_key -- section 4 below needs a.feature_key's own
        # skill to remain ACTIVE, untouched by the quarantine/collision tests here.
        s = schemas.Skill("TEST.lifecycle_chain", a.precondition, a.transformation, dict(a.provenance),
                           held_out_verdict=None, status="candidate", version=1)
        s.save_new_version(root=skills_root)
        check("a fresh, genuinely unverified skill derives CANDIDATE",
              s.effective_lifecycle() == "CANDIDATE")

        v2 = s.promote_to_verified("scratch test evidence", root=skills_root)
        v3 = v2.promote_to_qualified("scratch test evidence", root=skills_root)
        v4 = v3.promote_to_active("scratch test evidence", root=skills_root)
        check("promote chain reaches ACTIVE via the full, guarded CANDIDATE->VERIFIED->QUALIFIED->ACTIVE sequence",
              v4.effective_lifecycle() == "ACTIVE")

        # ---- 3b. Lifecycle order guards (2026-09-28 fix, adversarial review finding). ----
        try:
            fresh = schemas.Skill("TEST.lifecycle_chain", a.precondition, a.transformation, {})
            fresh.promote_to_active("should be rejected -- not QUALIFIED first", root=skills_root / "other")
            check("promote_to_active from CANDIDATE is rejected", False)
        except ValueError:
            check("promote_to_active from CANDIDATE is rejected", True)

        try:
            fresh2 = schemas.Skill("TEST.skip_verified", "P", "T", {})
            fresh2.promote_to_qualified("should be rejected -- skips VERIFIED", root=skills_root / "other2")
            check("promote_to_qualified from CANDIDATE (skipping VERIFIED) is rejected", False)
        except ValueError:
            check("promote_to_qualified from CANDIDATE (skipping VERIFIED) is rejected", True)

        retired_skill = v4.quarantine("scratch test: simulate a real safety concern", root=skills_root)
        try:
            retired_skill.promote_to_qualified("should be rejected -- QUARANTINED, not VERIFIED", root=skills_root)
            check("re-qualifying a QUARANTINED skill is rejected", False)
        except ValueError:
            check("re-qualifying a QUARANTINED skill is rejected", True)

        # A stale in-memory Skill object (v4, still says ACTIVE in its own fields)
        # attempting a transition AFTER the real skill was already quarantined (a
        # real v5 written above): the state guard itself would incorrectly allow
        # this (it only checks the in-memory object, not a fresh disk read) -- but
        # the underlying write-once persistence layer independently catches it,
        # since both the guard's stale success and the real quarantine both try to
        # write version 5. Verified directly (not assumed) before writing this
        # check: this raises FileExistsError, never silently overwrites or
        # corrupts the real, already-quarantined state.
        try:
            v4.mark_degraded("stale in-memory object, real skill already quarantined", root=skills_root)
            check("stale-object write-once collision is caught, not silently corrupting state", False)
        except FileExistsError:
            check("stale-object write-once collision is caught, not silently corrupting state", True)

        # ---- 3c. A fresh, dedicated skill for the shadow/active mode tests below,
        # under a.feature_key -- untouched by the lifecycle-chain tests above. ----
        real_s = schemas.Skill(a.feature_key, a.precondition, a.transformation, dict(a.provenance),
                                held_out_verdict=None, status="candidate", version=1)
        real_s.save_new_version(root=skills_root)
        real_v2 = real_s.promote_to_verified("scratch test evidence", root=skills_root)
        real_v3 = real_v2.promote_to_qualified("scratch test evidence", root=skills_root)
        real_v4 = real_v3.promote_to_active("scratch test evidence", root=skills_root)
        check("a.feature_key's own scratch skill independently reaches ACTIVE",
              real_v4.effective_lifecycle() == "ACTIVE")

        # ---- 4. Disabled / shadow / active modes, against the scratch ACTIVE skill. ----
        for k in ("VSL_ENABLED", "VSL_MODE"):
            os.environ.pop(k, None)
        r_disabled = runtime.consult(buggy_code, "winner_with_score", feature_keys=[a.feature_key])
        check("disabled mode: no match, no side effects",
              r_disabled.mode == "disabled" and r_disabled.matched_feature_key is None)

        # point consult()/Skill.load_latest at the scratch skills_root by feature_keys +
        # a monkeypatch of schemas.SKILLS_DIR (the same pattern the historical
        # serialization test already uses) -- isolated, restored immediately after.
        orig_skills_dir = schemas.SKILLS_DIR
        schemas.SKILLS_DIR = skills_root
        try:
            os.environ["VSL_ENABLED"] = "true"
            os.environ["VSL_MODE"] = "shadow"
            r_shadow = runtime.consult(buggy_code, "winner_with_score", feature_keys=[a.feature_key])
            check("shadow mode: matches the ACTIVE skill", r_shadow.matched_feature_key == a.feature_key)
            check("shadow mode: never applies (applied=False)", r_shadow.applied is False)
            check("shadow mode: computes the proposed patch without returning it as real output",
                  r_shadow.proposed_code is not None and "-tag_priority[x[2]]" not in r_shadow.proposed_code.replace(" ", ""))

            os.environ["VSL_MODE"] = "active"
            r_active = runtime.consult(buggy_code, "winner_with_score", feature_keys=[a.feature_key])
            check("active mode: matches and applies", r_active.applied is True)
            check("active mode: proposed code is a genuine, correct fix",
                  "-tag_priority[x[2]]" not in r_active.proposed_code.replace(" ", "")
                  and "tag_priority[x[2]]" in r_active.proposed_code.replace(" ", ""))

            # ---- 5. Provenance: every application traceable to skill ID/version. ----
            runtime.record_outcome("integration-test-task", r_active, buggy_code,
                                    {"f1_passed": True, "f2_passed": True}, "f1_f2_safety_only",
                                    code_after=r_active.proposed_code, applications_log=apps_log)
            import json
            rows = [json.loads(l) for l in apps_log.read_text().strip().splitlines()]
            check("provenance: application record traceable to feature_key and version",
                  len(rows) == 1 and rows[0]["matched_feature_key"] == a.feature_key
                  and rows[0]["matched_skill_version"] == real_v4.version)

            # ---- 6. Rollback: quarantine removes the skill from future consultation. ----
            real_v5 = real_v4.quarantine("integration test: simulated safety concern", root=skills_root)
            r_after_quarantine = runtime.consult(buggy_code, "winner_with_score", feature_keys=[a.feature_key])
            check("rollback: a quarantined skill is no longer matched/applied",
                  r_after_quarantine.applied is False and r_after_quarantine.matched_feature_key is None)

            # ---- 7. Degradation threshold, real function, isolated data. ----
            fake_result = runtime.ConsultResult(mode="active", matched_feature_key="TEST.degrade_check",
                                                 matched_skill_version=1, proposed_code="x", applied=True)
            s2 = schemas.Skill("TEST.degrade_check", "P", "T", {}, held_out_verdict=None, status="candidate", version=1)
            s2.save_new_version(root=skills_root)
            s2v2 = s2.promote_to_verified("t", root=skills_root)
            s2v3 = s2v2.promote_to_qualified("t", root=skills_root)
            s2v3.promote_to_active("t", root=skills_root)
            for i in range(5):
                runtime.record_outcome(f"degrade-{i}", fake_result, "before", {"passed": False},
                                        "full_oracle", applications_log=apps_log)
            stats = runtime.evaluate_degradation("TEST.degrade_check", applications_log=apps_log, skills_root=skills_root)
            after_degrade = schemas.Skill.load_latest("TEST.degrade_check", root=skills_root)
            check("degradation: 5/5 full_oracle failures crosses threshold and degrades the skill",
                  stats["action"] == "degraded" and after_degrade.effective_lifecycle() == "DEGRADED")

            weak_only_result = runtime.ConsultResult(mode="active", matched_feature_key="TEST.weak_only",
                                                      matched_skill_version=1, proposed_code="x", applied=True)
            for i in range(10):
                runtime.record_outcome(f"weak-{i}", weak_only_result, "before", {"f1_passed": False},
                                        "f1_f2_safety_only", applications_log=apps_log)
            stats_weak = runtime.evaluate_degradation("TEST.weak_only", applications_log=apps_log, skills_root=skills_root)
            check("degradation: f1_f2_safety_only-only evidence never triggers degradation (weak signal excluded)",
                  stats_weak["action"] == "none" and stats_weak["n_full_oracle_applications"] == 0)
        finally:
            schemas.SKILLS_DIR = orig_skills_dir

    # ---- 8. Full real pipeline: VSL disabled == true pass-through. ----
    for k in ("VSL_ENABLED", "VSL_MODE"):
        os.environ.pop(k, None)
    import app.core.echo_projects as EP
    real_apps_log_existed_before = runtime.APPLICATIONS_LOG.exists()
    files = {"main.py": "import helper\nprint(helper.add(1, 2))\n", "helper.py": "def add(a, b):\n    return a + b\n"}
    result = EP.generate_project("integration-test: disabled pass-through", dict(files))
    check("disabled pipeline: status ok, F1/F2 pass exactly as pre-VSL",
          result["status"] == "ok" and result["f1_results"] == {"main.py": "OK", "helper.py": "OK"})
    check("disabled pipeline: VSL made zero writes to the real production log",
          runtime.APPLICATIONS_LOG.exists() == real_apps_log_existed_before)
    shutil.rmtree(result["project_dir"], ignore_errors=True)

    # ---- 9. Full real pipeline: VSL active, real Skill A, real F1/F2 re-verification. ----
    os.environ["VSL_ENABLED"] = "true"
    os.environ["VSL_MODE"] = "active"
    buggy_files = {"main.py": buggy_code + "\nprint(winner_with_score([('a', 5, 'p'), ('b', 5, 's')]))\n"}
    result2 = EP.generate_project("integration-test: active real Skill A repair", dict(buggy_files))
    staged = (Path(result2["project_dir"]) / "main.py").read_text()
    check("active real pipeline: staged file has the negation removed",
          "-tag_priority[x[2]]" not in staged.replace(" ", ""))
    check("active real pipeline: F1/F2 both pass on the VSL-corrected code",
          result2["status"] == "ok")
    shutil.rmtree(result2["project_dir"], ignore_errors=True)
    if runtime.APPLICATIONS_LOG.exists():
        runtime.APPLICATIONS_LOG.unlink()  # clean up this test's own real production application records
    prov = runtime.PRODUCTION_ROOT / "provenance.jsonl"
    if prov.exists():
        prov.unlink()

    # ---- 10. The two pre-existing echo_projects Liveness Ledger invariants still hold. ----
    from app.core.liveness_ledger import _check_echo_projects_isolation, _check_echo_projects_no_escalation
    check("echo_projects_isolation liveness check still passes after this integration",
          _check_echo_projects_isolation()["pass"] is True)
    check("echo_projects_no_escalation liveness check still passes after this integration",
          _check_echo_projects_no_escalation()["pass"] is True)

    # ---- 11. Real production Skill A is genuinely ACTIVE (not left in a test-polluted state). ----
    real_a = schemas.Skill.load_latest(a.feature_key)
    check("real production Skill A is ACTIVE with the expected clean version",
          real_a is not None and real_a.effective_lifecycle() == "ACTIVE" and real_a.version == 4)


if __name__ == "__main__":
    main()
