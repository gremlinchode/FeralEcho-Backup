"""Discrimination tests for hub/check_hub.py's truthful `checked_by`
attribution (audits/2026-09-29_relay_hub_reliability_repair.md, Phase 5/6 —
closing the hardcoded "claude-m5" defect
audits/2026-09-29_relay_hub_reliability_semantics_audit.md Section 11 found).
"""
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import check_hub


class AttributionTests(unittest.TestCase):
    def test_a1_explicit_claude_identity_is_truthful(self):
        self.assertEqual(
            check_hub.resolve_checked_by(argv=["--checked-by", "claude-m5"], env={}),
            "claude-m5",
        )

    def test_a2_explicit_codex_identity_is_truthful(self):
        self.assertEqual(
            check_hub.resolve_checked_by(argv=["--checked-by", "codex-m5"], env={}),
            "codex-m5",
        )

    def test_a3_no_identity_supplied_is_honest_unknown(self):
        # The exact case that used to silently become "claude-m5" no matter
        # who or what actually ran the check.
        self.assertEqual(check_hub.resolve_checked_by(argv=[], env={}), "unknown")

    def test_a4_identity_field_grants_no_authority_anywhere(self):
        # Governance safety check (Phase 6): checked_by must have zero
        # consumers anywhere in the tracked codebase -- otherwise an
        # unauthenticated, self-reported string could silently become a
        # decision input. Re-derived by grep every time this test runs,
        # not asserted once and trusted forever.
        repo_root = Path(__file__).resolve().parent.parent
        result = subprocess.run(
            ["grep", "-rn", "checked_by", "--include=*.py", str(repo_root)],
            capture_output=True, text=True,
        )
        hits = [
            line for line in result.stdout.splitlines()
            if ".claude/worktrees" not in line and "__pycache__" not in line
        ]
        non_definition_hits = [
            line for line in hits
            if "hub/check_hub.py" not in line and "hub/test_check_hub.py" not in line
        ]
        self.assertEqual(
            non_definition_hits, [],
            "checked_by must remain read nowhere outside hub/check_hub.py itself; "
            "if this fails, something now CONSUMES this field and Phase 6's "
            "'informational only' finding needs re-verifying before trusting it "
            f"for anything authoritative. Found: {non_definition_hits}",
        )

    def test_a5_historical_default_callers_no_longer_silently_become_claude_m5(self):
        # The literal historical bug: calling resolve_checked_by with
        # whatever a bare, un-augmented environment/argv looks like must
        # never resolve to "claude-m5" specifically -- that was the
        # hardcoded value, and it must not survive as an accidental default.
        self.assertNotEqual(check_hub.resolve_checked_by(argv=[], env={}), "claude-m5")

    def test_cli_flag_takes_priority_over_env_var(self):
        result = check_hub.resolve_checked_by(
            argv=["--checked-by", "codex-air"], env={"HUB_CHECKED_BY": "claude-m5"},
        )
        self.assertEqual(result, "codex-air")

    def test_env_var_used_when_no_cli_flag(self):
        result = check_hub.resolve_checked_by(argv=[], env={"HUB_CHECKED_BY": "codex-m5"})
        self.assertEqual(result, "codex-m5")


if __name__ == "__main__":
    unittest.main()
