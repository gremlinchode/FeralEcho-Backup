"""app/core/skill_ledger -- the production-facing Verified Skill Ledger core.

Extracted from app/experiments/skill_ledger/ (Operation Skillforge, 2026-09-27/28),
per the integration-readiness mission's Phase 1/12 instruction: the experimental
package is the scientific reference implementation and must remain runnable and
byte-for-byte behavior-equivalent; this package is the reusable core the production
Echo adapter (app/core/skill_ledger/echo_adapter.py) actually imports.

Governing documents, in order:
  audits/2026-09-27_feralecho_learning_architecture_deep_dive.md
  audits/2026-09-27_verified_skill_ledger_build_decision.md
  audits/2026-09-27_vsl_prospective_causal_transfer_protocol.md
  audits/2026-09-27_vsl_accumulated_competence_protocol.md
  audits/2026-09-28_vsl_integration_readiness.md  (this integration pass)

Modules:
  matcher.py   -- pure, I/O-free AST diff/match/apply logic. Moved verbatim from
                  app/experiments/skill_ledger/diff_extract.py -- zero logic changes.
  schemas.py   -- the Skill record (identity/version/provenance/lifecycle). Moved
                  from app/experiments/skill_ledger/ledger.py's Skill class, with the
                  original status/held_out_verdict/is_eligible() contract preserved
                  byte-for-byte (existing serialized skill files must keep loading
                  correctly), PLUS an additive `lifecycle_state` field and explicit
                  transition functions for the fuller production state machine.
  store.py     -- persistence (write-once versioned files, provenance log), generalized
                  to a configurable root directory so production skills
                  (memory/skill_ledger/) and the historical experiment's own skills
                  (memory/experiments/skill_ledger/) never collide.
  runtime.py   -- the production consumption API: match/apply/record_outcome, gated by
                  VSL_ENABLED and VSL_MODE (disabled/shadow/active).
  echo_adapter.py -- the one narrow hook into a real Echo generation path
                  (app/core/echo_projects.py).

THE LEDGER MUST NOT BE ITS OWN VERIFIER. Nothing in this package ever treats a
model's own claim, a skill's own metadata, or a precondition match as proof of
correctness by itself -- every real "did this help" claim in this codebase's history
came from an external oracle (a real test suite) or a real held-out substitution
comparison, never from the ledger's own self-report.
"""
