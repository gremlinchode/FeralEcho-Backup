# VSL Clean-Checkout Reproducibility Failure — Forensic Note

**This note exists to qualify, not retract, the prior gate's conclusion.** The previous
`MERGE` verdict (`audits/2026-09-28_vsl_final_premerge_adversarial_gate.md`) was correct
about what it actually tested. It never tested repository reproducibility from a clean
checkout, and that gap let a real regression reach `main` and `origin/main`.

## What was missing

`app/experiments/accumulation_probe/` (47 files) and `app/experiments/persistent_routing/`
(15 files) were never committed to git history by anyone, at any point
(`git log --all --oneline -- <path>` returns nothing for either). Both are real, working,
substantial packages that already existed on disk throughout the entire VSL research and
integration arc.

## Why local tests passed

Every VSL test run during acquisition, the prospective-transfer test, the accumulation
test, the integration-readiness build, and both adversarial gates ran against the local
working tree, which had these directories present as **untracked** files. `git status`
correctly showed them as `??` throughout, and I read that status repeatedly — but "review
the untracked pile" and "test whether the committed repository alone is self-sufficient"
are different checks, and only the first one was ever performed before this mission.

## Why the clean checkout fails

Reproduced directly, in a genuinely clean `git worktree` of the exact pushed commit
(`607c6d0024c7bc0810dcb0d446cd9c664551a1b2`), verified to have zero untracked files
(`git status --porcelain` empty in the worktree):

```
python3 -B -c "import app.core.echo_projects"
```

```
Traceback (most recent call last):
  File "<string>", line 4, in <module>
  File ".../app/core/echo_projects.py", line 72, in <module>
    from app.core.skill_ledger import echo_adapter as _vsl
  File ".../app/core/skill_ledger/echo_adapter.py", line 17, in <module>
    from . import runtime
  File ".../app/core/skill_ledger/runtime.py", line 24, in <module>
    from . import schemas
  File ".../app/core/skill_ledger/schemas.py", line 45, in <module>
    from .store import sha256_text, write_json_new, read_json, log_provenance_event, PRODUCTION_ROOT
  File ".../app/core/skill_ledger/store.py", line 17, in <module>
    from app.experiments.skill_ledger.common import sha256_text
  File ".../app/experiments/skill_ledger/common.py", line 15, in <module>
    from app.experiments.accumulation_probe.common import canon, sha256_obj, sha256_text
ModuleNotFoundError: No module named 'app.experiments.accumulation_probe'
```

**Root cause, precisely**: `app/experiments/skill_ledger/common.py` (committed as part of
the original VSL implementation, before the integration-readiness pass) reuses
`accumulation_probe.common`'s pure hash/canonicalization helpers rather than duplicating
them — a deliberate, documented design choice at the time ("Reuses AP-0's proven pure
helpers, never anything with production side effects"). `app/core/skill_ledger/store.py`
(written during the integration-readiness pass) then re-exported `sha256_text` from that
same module rather than duplicating it again, extending the transitive dependency from
the experimental package into the production core. Neither choice was unreasonable in
isolation; the combination created a real production dependency on a never-committed
package, and nothing in either the integration-readiness gate or the two adversarial
gates ever tested a clean checkout to catch it.

## Production dependency closure, mapped precisely (not assumed)

- `app.core.skill_ledger.store` needs exactly `app.experiments.skill_ledger.common`,
  which needs exactly `accumulation_probe.common`'s `canon`/`sha256_obj`/`sha256_text` —
  `accumulation_probe/common.py` itself is self-contained (only `hashlib`/`json`/`os`/
  `pathlib`, confirmed by direct read).
- `app/experiments/skill_ledger/harness.py` (a real, already-committed file, part of the
  "scientific reference implementation") separately needs
  `accumulation_probe.oracle_runner`/`ollama_client` and
  `persistent_routing.strategies.build_prompt`.
- `app/experiments/skill_ledger/tasks.py` separately needs
  `accumulation_probe.worlds`/`tasks`/`tasks_v2`.
- Neither `harness.py` nor `tasks.py` is imported by any file under `app/core/` — the
  **strict minimum** for the production import chain alone is just
  `accumulation_probe/common.py`. The **full** scientific reference implementation
  (re-running `harness.py`, `prospective_transfer.py`, `accumulation.py`) needs the
  complete `accumulation_probe/` and `persistent_routing/` packages.
- Both packages, checked directly, depend only on each other and stdlib — no further
  cascading dependency on any other currently-uncommitted package.
- **`accumulation_probe` is also a dependency of at least 6 other currently-uncommitted
  experiment packages** (`belief_revision_probe`, `g3_micro_probe`, `persistent_routing`,
  `strategy_characterization`, `rung1`, and transitively others) — confirming this is a
  genuinely shared, foundational research utility, not a VSL-specific accident.

## What the previous gate's conclusion must be qualified to

The prior `MERGE` verdict established, with real, adversarially-tested evidence:

- **Local implementation worked** — extensively confirmed, including under direct attack.
- **Scientific evidence survived adversarial testing** — confirmed independently, twice.

It did **not** establish, and incorrectly implied by omission:

- **Repository reproducibility from committed state alone** — this was never tested, and
  when tested just now, failed.

No part of history is being rewritten to obscure this. This note stays in the permanent
record alongside the gate reports it qualifies, and the repair that follows is recorded
as its own, separately-labeled commit.
