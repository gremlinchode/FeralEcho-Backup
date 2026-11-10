# Project Voyager

Isolated mission-continuity prototype. Python standard library only.
It does not import FeralEcho, does not call Ollama, and does not write production memory.

The worktree is `/Users/richietate/Desktop/FeralEcho-voyager` on branch `project-voyager`.
HEAD is `dc8d6eb9b6479ef323614cd6820bb050a14299eb`. Nothing here is committed.

## Run the contract check

From `voyager_lab`:

```bash
cd /Users/richietate/Desktop/FeralEcho-voyager/voyager_lab
PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1 python3 self_check.py
```

`self_check.py` uses temporary directories. It does not write `results/` and it does not rewrite `RUBRIC_FREEZE.json`.

## Check the rubric lock

```bash
python3 freeze.py
```

A matching lock prints `FREEZE_OK` and the bundle hash
`b8b1bc1fe7056294739bd834c3e4329807b50ef6cdffab67f68f6e32e2af9b9d`.

The lock covers `voyager/atomic.py`, `suite_spec.py`, `rubric.py`, `procedures.py`,
`engine.py`, `baseline.py`, `grader.py`, `world.py`, `harness.py`, and `worker.py`.
It does not cover `self_check.py`, `freeze.py`, or `run_experiment.py`.

## Official evaluation

The one official run has already been executed. `run_experiment.py --run` refuses
when `results/summary.json` or `results/raw/` exists. Do not delete those files
to obtain a second score.

Raw rows are in `results/raw/{baseline,engine,ablation}/<mission_id>/`.
Aggregates are in `results/summary.json` and `results/RESULTS.md`.
The reading of those numbers is in `ASSESSMENT.md`.
