"""AP-0 Convention Accumulation Probe -- isolated research harness (Stage 0: instrument / carrier-consumption gate).

Nothing in this package is imported by, or writes to, any production FeralEcho module or state. It talks to the local Ollama server
over plain HTTP and grades candidates in the kernel sandbox by invoking `sandbox-exec` directly (it deliberately does NOT import
`sandbox.run_script`, whose module-level logging setup writes files, nor `scripts/run_capability_pilot.py` / `self_edit_manager`).
All experiment state lives under memory/experiments/accumulation_probe/ (override with env AP0_ROOT for tests).
"""
