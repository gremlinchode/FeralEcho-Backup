"""Rung-1 research apparatus (Stage E0: trusted evaluator boundary only).

Isolated, research-only package. Nothing here is imported by production
Echo, RiverBrain, self-edit, council, or any live code path -- confirmed
by construction (this package imports nothing from app.core / app.* other
than stdlib, and nothing outside this package imports it).

See:
  - audits/2026-09-23_rung1_engineering_gate_specification.md (governing spec)
  - audits/2026-09-23_rung1_e0_trusted_evaluator_implementation.md (this stage's report)
"""
