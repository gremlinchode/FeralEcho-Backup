# FeralEcho — Verified, Non-Destructive Backup and Recovery Procedure (DESIGN ONLY)

**Date:** 2026-09-20 · **Status:** DESIGN FOR OPERATOR REVIEW — **no backup has been made, nothing was transferred, nothing was restarted, no production file or Git state was touched.**
**Companion file:** `audits/2026-09-20_feralecho_backup_manifest_schema.json` (JSON Schema for the per-generation manifest).
**Evidence labels:** **OBSERVED** (read directly this session or in the two preceding audits, cited) · **INFERRED** (reasoned, not measured) · **UNKNOWN** · **SYNTHETIC-TESTED** (the tooling was exercised on a throw-away fixture in the session scratchpad — *never* on FeralEcho data; §17.9 lists exactly what those tests do and do not prove).

---

## 0. Scope, records, and the shape of the answer

### 0.1 Constraints honoured (verbatim intent)
No backup executed · no file transferred · FeralEcho not restarted/stopped · no production source or persistent state modified · no Git mutation (no commit/push/pull/fetch/reset/checkout/clean/stash/stage) · `backup_feral_echo.sh` **not run** (it rewrites `.gitignore` with `cat >` and runs `git lfs install`/`git config`) · no synchronization software · frozen persistent-competence protocol untouched · old `memory_meta*` and RiverBrain backup artifacts untouched and — by design — never deletable by anything in this plan · no network discovery or transfer · no drive formatted or altered · no destination assumed to exist.

**Only two files were created in the repository by this mission:** this plan and the schema JSON. Everything else lives in the session scratchpad (`/private/tmp/claude-501/.../scratchpad`), outside the repository.

### 0.2 Before-state (recorded before any deliverable was written; after-state in §21)
| Item | Value (OBSERVED) |
|---|---|
| Git HEAD | `2fba42644c82b9f7096276f4dd338d615cf1bcce` (branch `main`) |
| `git status --porcelain` (default untracked mode) | **186** paths before this mission's deliverables (`--untracked-files=all` counts 249 = 27 tracked-modified + 221 untracked-non-ignored + 1 for this mission's first file at the time of the recount) |
| Server | PID **29288**, start **Sun Sep 20 07:30:10 2026**, `python -u run.py`, child of `start_echo.sh` |
| Frozen protocol v1.0 / v1.1 / traceability hashes | unchanged (verified in §21) |
| Host | `LocalHostName` = `Richards-MacBook-Air`, `hw.model` = `Mac17,3`, `arm64`, "Apple M5". **The M5's hostname says "Air".** Hostnames therefore cannot tell the M5 from the Intel Air; this plan tags machines explicitly (`M5` / `INTEL`) and uses `uname -m` (`arm64` = M5, `x86_64` = Intel) as the identity test. |

### 0.3 Why this matters (from the preceding audit, `…_runtime_identity_and_state_preservation.md`)
The M5's internal SSD is the **only verified location** of (a) the source lineage since 2026-09-05 (17 unpushed commits + 27 modified + 221 untracked files) and (b) every accumulated state file. Time Machine: none configured; iCloud Desktop: off; no external volume mounted; existing state "backups" are same-disk copies that the 5-slot rotation replaces within ≈20 h. The server aborts (Metal `SIGABRT`) about twice a day; several state writers are non-atomic; corruption-then-empty-then-overwrite paths exist. So the danger is *both* device loss *and* logical corruption that a naive mirror would faithfully copy.

### 0.4 Design principles (each one is enforced by mechanism, not by promise)
1. **Generations are immutable, complete, and independent.** Each backup is a fresh full copy in a new directory created with plain `mkdir` (which fails if the path exists). No generation is ever built from, merged into, or "updated from" another. A corrupted source therefore cannot damage an older generation, and there is no incremental chain to corrupt.
2. **Nothing is ever deleted or overwritten by the procedure.** The runbook contains no `rm`, no `--delete`, no `git reset/clean/checkout/restore/stash(push)`. Failed copy attempts are *moved inside the generation* to `work/failed/` and kept as evidence.
3. **Fidelity, validity, and consistency are three separate claims** and are established by three separate mechanisms: *fidelity* = the destination bytes equal a real version of the source (hashes); *validity* = the copied state is structurally loadable (validators run on the copy only); *consistency* = pairs/sets of files belong together (FAISS count = metadata count; nothing changed mid-copy; server PID/start unchanged). A hash match proves only the first.
4. **We never claim more than the evidence supports.** The consistency levels (§15) are ordered; a copy made while the server runs is at best `VERIFIED-LIVE`, never a transactional snapshot.
5. **Validation touches copies only, inside a no-write, no-network jail, importing no FeralEcho code** (pickles are walked with `pickletools.genops`, which never imports modules).

---

## 1. Data classes

### 1.1 Class A — source lineage (irreplaceable authored work)
**Scope:** the entire working tree `/Users/richietate/Desktop/FeralEcho` **except** the three justified exclusions of §16 and **except** `memory/` and `data/` (those are Class B). OBSERVED size of the whole repo directory: **1.58 GB**; 22,761 in-scope files (`memory/` 352, `data/` 10, everything else ≈ 22,400).

| Component | Why it must survive | Evidence |
|---|---|---|
| `.git/` (36.6 MB, 177 files, 3 packs + 112 loose objects) with **all refs** — `main` `2fba426`, `worktree-agent-abe6ecca0408fd0fb` `a23b940` (an *ancestor* of `main`: 0 unique commits, `main` is 62 ahead), `origin/main` `d6cd738` | commit history incl. the **17 unpushed commits** | OBSERVED |
| Tracked-but-modified files (27) and untracked non-ignored files (221) | authored work that exists nowhere else, not even in Git | OBSERVED |
| Ignored-but-meaningful files | `.env` (secrets — see §0.4/§12 warning), `WhisperingWires/*.log`, `app/core/self_edit_backups/`, `app/core/self_edit_plans/`, `sandbox/`, `Figure_*.png`, `WhisperOfPeace.wav` (Echo incident records — **keep**), scaffold directories | OBSERVED |
| Config / scripts | `Modelfile`, `start_echo.sh`, `safe_restart.sh`, `echo_principles.json`, `COUNCIL.md`, `ORIGIN.md`, `run.py`, hooks in `.git/hooks` (`post-checkout/post-commit/post-merge/pre-push`, LFS) | OBSERVED |
| Audit / research artifacts | `audits/` (12.6 MB, includes the frozen protocol and this mission's files), `research/`, `hub/`, `claude_relay/` | OBSERVED |
| Linked worktree `.claude/worktrees/agent-abe6ecca0408fd0fb` (70 MB) | copied as files; its `.git` *file* holds an **absolute** path into the original `.git` (SYNTHETIC-TESTED: after a restore into a new location it still points at the original repo until `git worktree repair <path>` is run from the restored root — §13 step R6) | OBSERVED / SYNTHETIC-TESTED |
| **Redundant Git carriers inside each generation** | `git/repo.bundle` (`git bundle create --all`, verified) so the history is recoverable *without* the copied `.git`, plus identity text files (§1.3) | designed |

Out-of-repo Class A (tiny, captured into `identity/`): `~/Library/LaunchAgents/com.gremlin.echo.plist`; full `pip freeze` of the runtime interpreter (Python 3.12.13, conda env `feral_echo`). **Not captured by the automation, operator decision:** `~/.ssh/*` private keys and the Tailscale identity (credentials; putting them on a portable disk is a risk decision, §16), Ollama weights (§16), the HuggingFace cache for `all-MiniLM-L6-v2` (needed offline because `run.py` forces `HF_HUB_OFFLINE=1`; ~90 MB; **recommended** manual copy, §16).

### 1.2 Class B — persistent state
Exact paths and OBSERVED sizes (bytes, at 2026-09-20 ≈12:46 local; sizes drift, the runbook re-measures). Class letters IRR/EXP/REB/EPH are from the preservation audit §5.

**B1 — the exact minimal persistent-state set (13 files, 317,043,348 bytes ≈ 302 MiB).** If only these plus Class A survive, the system is recoverable in the sense the audit defines. Copied first, verified hardest.

| # | Path (relative to repo root) | Bytes | Audit class | Live-mutation behaviour (audit §5–6) |
|---|---|---:|---|---|
| 1 | `memory/memory_meta.json` | 100,898,000 | **IRR** (the texts *are* the data) | full rewrite per FAISS add, **meta written first**; not atomic across the pair |
| 2 | `memory/faiss.index` | 201,040,941 | REB but expensive (re-embed all texts; cost UNMEASURED) | written second; **must be kept with #1 as a pair** |
| 3 | `data/question_garden.jsonl` | 10,546,647 | EXP | full rewrite + append, **no lock, not atomic**, ≥ every 5 min |
| 4 | `memory/river_brain.pkl` | 4,377,549 | EXP | `open("wb")`+`pickle.dump`, **not atomic**, ~80 saves/h |
| 5 | `memory/task_type_classifier.pkl` | 50,617 | REB | `open("wb")`, not atomic |
| 6 | `memory/drift_detectors.pkl` | 1,034 | REB | tmp+replace, 120 s |
| 7 | `memory/self_model_claims.jsonl` | 8,904 | **IRR** (small) | append |
| 8 | `memory/council_ratings.jsonl` | 118,545 | **IRR** (human labels) | append + atomic rewrite by `spot_check.py` |
| 9 | `memory/snapshot_baseline.json` | 926 | IRR (trust decisions) | tmp+replace, rare |
| 10 | `memory/behavioral_directives.json` | 38 | would be IRR once populated | tmp+replace |
| 11 | `memory/genesis/genesis_hash.txt` | 64 | anchor | static |
| 12 | `memory/genesis/council_hash.txt` | 65 | anchor | static |
| 13 | `memory/genesis/genesis_timestamp.txt` | 18 | anchor | static |

**B2 — strongly recommended (11 files, ≈ 148.7 MiB):** `memory/interaction_log.jsonl` (19,824,388), `memory/interaction_log.jsonl.1.gz` (12,071,636), `memory/reflection_shard.jsonl` (38,731,965), `memory/reflection_journal.jsonl` (13,431,941), `memory/SELF_EDIT.log` (28,610,103; the convergence tracker replays it in full), `memory/council_deliberations.jsonl` (30,502,059), `memory/echo_messages.jsonl` (2,873,665), `memory/self_edit_outcomes.jsonl` (97,431), `memory/dissent_log.jsonl` (1,200), `memory/optuna.db` (9,752,576), `memory/self_model.json` (18,736).

**B3 — everything else under `memory/` and `data/`** (≈ 800 MB of the 1.25 GB in `memory/` + `data/`): snapshots (22 MB), `memory/archive/`, `memory/backups/` (96 MB), the two `memory_meta_backup_before_*_migration_20260902*.json` files (~89 MB each — **must be kept**), `memory/history/`, `memory/experiments/`, other logs (`dream_bridge.log` 81 MB, `quarantine_journal.jsonl` 35 MB, `echo_watchdog.log` 34 MB, `validator_audit.log` 26 MB …), `echo_state*.npy`, sense signature files, etc. **Nothing is excluded for size.** Ephemeral files (`echo_server.pid`, `echo_sentinel.json`) are copied but never restored (§13).

Partition guarantee: the runbook computes `all.lst = A ∪ B1 ∪ B2 ∪ B3` and the judge fails the generation if the parts overlap, miss a file, or if the destination tree ≠ scope. **No file is silently omitted.**

### 1.3 Class C — identity and recovery evidence (stored under `identity/`, plus `manifest/`)
| Artifact | What it proves / is for |
|---|---|
| `git_head.txt`, `git_branch.txt`, `git_refs.txt` | exact commit and all ref tips at backup time |
| `git_status_v2.txt`, `git_diff_HEAD.patch` (+`.stat`), `git_untracked_nonignored.txt`, `git_ignored.txt`, `git_worktrees.txt`, `git_stash.txt`, `git_unpushed_count.txt` | what was dirty/untracked/ignored; a second, tool-independent carrier of tracked edits; restore cross-check |
| `git/repo.bundle` + `git_bundle_verify.txt` | history recoverable with plain `git clone` |
| `manifest/all.lst`, `A/B1/B2/B3.lst`, `stat.tsv` (size, mtime, mode per file), `A.pre/post/dest.sha256`, `copyrec.tsv` (every copy attempt with pre/post/dest hashes), `results.tsv`, `final.sha256`, `retry.lst`, `created_during.lst`, `vanished_during.lst`, `validation.json`, `kv.env` | hash evidence for every file; permission/mtime record for restores where the destination filesystem drops them |
| `GENERATION.json` (+`.sha256`), `SEAL.sha256` | the machine-readable manifest (schema JSON) and a hash over every non-tree file in the generation |
| authored-tree fingerprint (in `GENERATION.json`) | deterministic identity of the copied source: sha256 over sorted `path\0sha256\n` of every A-part file, with and without the four self-mutating files. **It is not the `8e6808dc…` fingerprint** of the earlier identity manifest — that one used a suffix-restricted 513-file set the archived manifest does not fully specify, so it is *recorded for reference only* (`legacy_reference_not_recomputed`), not claimed reproducible |
| `runtime.txt`, `pip_freeze.txt` | server PID + start time; `sw_vers`; `uname`; Python version; sha256 of `pip freeze`; `ollama list` and loopback `api/tags` digests (expected: `echo:latest` prefix `8cbcbe23800bfe9c`, built from the tracked `Modelfile`, `FROM llama3:instruct` digest prefix `365c0bd3c000a25d`) |
| `env_names_and_hash.txt` | `.env` variable **names** and one SHA-256 of the file — never values |
| `com.gremlin.echo.plist` | launchd configuration |
| `destination.txt`, `kv.env` | destination volume identity: filesystem, volume UUID, device location, free space |
| `audit_references` | pointers to the preservation audit and this plan |

---

## 2. Backup versus synchronization

**A synchronised mirror is not a backup.** It replicates deletions, truncations, corruption, and an accidentally-emptied FAISS index to every copy within one cycle. The existing M5↔Air sync (`sync_protocol.py`) merges *interaction-log entries*, is not a backup of `memory/`, and **nothing in this plan uses or extends it** (also: no synchronization software is used, per the mission constraint).

What makes this a backup:
| Property | Mechanism |
|---|---|
| Immutable generations | new directory per backup, created by plain `mkdir` (fails if it exists); sealed by `SEAL.sha256` and a `COMPLETE-<level>` or `QUARANTINED-NOT-KNOWN-GOOD` marker; the judge **refuses** to re-judge a sealed generation |
| Append-only history | `generations.log` is written only with `>>`; one line per event (`VERIFIED-*`, `RESTORE-TESTED`, `REPLICA-VERIFIED`) with the manifest hash; no "latest" pointer is ever rewritten |
| One-way | source → destination only; no bidirectional flow; no `--delete` anywhere; second copies are made from a *sealed generation* by byte copy + cold verification |
| Independent | a generation never depends on another (no incrementals, no hard-link chains) — a bad generation costs one generation |
| Verified | §6, §7 — a generation that has not passed verification is labelled `QUARANTINED-NOT-KNOWN-GOOD` or `RESCUE-LIVE`, never silently accepted |

---

## 3. Safe macOS copy semantics

**Tools present on this M5 (OBSERVED):** `/bin/cp` (BSD), `/usr/bin/ditto`, `/usr/bin/tar` = **bsdtar 3.5.3 / libarchive 3.7.4**, `/usr/bin/rsync` = **openrsync** ("protocol version 29, rsync 2.6.9 compatible"), `/usr/bin/shasum` 6.02 (Perl; `sha256sum` is *not* assumed), `sqlite3` 3.54.0, `head`/`stat`/`find`/`sort`/`xargs`/`comm` (BSD). `/usr/bin/python3` is the Xcode shim and **refuses to run** until the Xcode licence is accepted (OBSERVED: "You have not agreed to the Xcode license agreements") — the plan therefore uses the conda interpreter by absolute path, `-I` (isolated) mode, and never `/usr/bin/python3`. Shell: **`/bin/bash` 3.2.57** for every script (no associative arrays, no `mapfile`); the default zsh is *not* used for the tools (zsh reserves `status` as read-only — SYNTHETIC-TESTED: this broke an earlier draft of `fe_copy_one`, fixed by renaming).

| Tool | Decision | Why |
|---|---|---|
| `cp -p` (per file) | **Used** for live state files | preserves mode + times; refuses nothing by itself, so the code checks the destination does not exist first; `-c` (APFS clone) is **avoided** — a clone shares blocks and defeats the purpose on the same volume |
| `tar -cf - --null -T list \| tar -xpkf -` | **Used** for the static bulk tree (Class A) | preserves modes/mtimes/symlinks; `-k` = keep existing (never overwrite); explicit file lists mean nothing outside the audited scope is copied; **no** `--delete`-like semantics exist |
| `ditto` | not used | silently overwrites; fails to fail |
| `rsync` (openrsync) | **not used on the M5** | it *has* `--delete`; flag coverage of openrsync differs from GNU rsync and was not enumerated here (UNKNOWN); it is also "sync software" in spirit. If ever used as a fallback it must be run with `-n` (dry run) first and never with `--delete` |
| GNU-only flags | avoided | no `stat -c`, `sed -i` without extension, `find -printf`, `readlink -f`, `date -d`, `cp --reflink`, `sha256sum`, `comm -z`, `xargs -r` |

**Fail visibly:** every stage is a bash function that `return`s non-zero and prints a line starting with `STOP:`; `set -o pipefail` makes a broken `tar | tar` pipeline fail; the operator's rule is "the first `STOP:` ends the run — do not paste the next block".

---

## 4. Live mutable state — per-artifact strategy

FeralEcho keeps running during the backup (it must not be stopped). Every source file is put in one of five categories; the strategy is per category and **nothing claims a transactional multi-file snapshot**.

| Cat. | Meaning | Artifacts | Strategy |
|---|---|---|---|
| **A** | append-only growth is legitimate | `interaction_log.jsonl`, `reflection_shard.jsonl`, `reflection_journal.jsonl`, `council_deliberations.jsonl`, `SELF_EDIT.log`, `SELF_EDIT_MASTERY_.log`, `self_model_claims.jsonl`, `workspace_log.jsonl`, `seam_log.jsonl`, `dream_bridge.log`, `quarantine_journal.jsonl`, `echo_watchdog.log`, `validator_audit.log`, `dissent_log.jsonl`, `WhisperingWires/*.log` (explicit list `FE_APPEND_SET`) | `cp`, then accept **only if** the destination hash equals the hash of the first *N* source bytes read **after** the copy (N = destination size) **and** the source did not shrink. Detects rotation (`log_retention` gzips + truncates daily) and mid-file rewrites. A partial last line is possible and is recorded, not repaired |
| **B** | rewritten whole; short window | `river_brain.pkl`, `task_type_classifier.pkl`, `drift_detectors.pkl`, `question_garden.jsonl`, `council_ratings.jsonl`, `self_model.json`, `snapshot_baseline.json`, and every file *not* listed in `FE_APPEND_SET` (strict by default) | hash source → copy → hash source again → hash destination; accept **only if** dest = pre = post (VERIFIED-STABLE) or dest = pre or dest = post (VERIFIED-LIVE-VERSION: the copy is a complete real version). A torn read matches neither, so it fails. Prefix matches are **not** accepted here (a truncated pickle *is* a prefix of the completed one — accepting prefixes would be a false pass) |
| **C** | needs a quiescent window for *true* consistency | the pair `memory/memory_meta.json` + `memory/faiss.index` (two-file write; meta first; ~26 persists/h — INFERRED persist duration a few seconds) | copied as two category-B files; then **pair evidence**: both unchanged pre→post, server PID/start unchanged, and (on the copy) `faiss.ntotal == len(meta)`. Bounded retry (≤3). If persistently mutated, escalate to a controlled quiescent window — a **future, separately approved** step, not part of today's plan. Rough collision risk per attempt INFERRED at a few percent; three consecutive collisions much less — this is an estimate, not a measurement |
| **D** | snapshot-like mechanism exists | `memory/optuna.db` (SQLite, rollback-journal mode: no `-wal`/`-shm` present — OBSERVED); APFS local snapshots (`tmutil localsnapshot`; **0 local snapshots exist now** — OBSERVED) | Optuna DB: plain category-B copy, then `PRAGMA integrity_check` **on the copy** via a read-only immutable URI (never opens the source DB). APFS snapshot: a *possible* later upgrade that would freeze the whole Data volume for the copy window (removing copy-window races, **not** the writers' own non-atomicity); it needs `tmutil` (a system write) and `mount_apfs`/sudo, is UNVERIFIED on this machine, and is left as an operator decision |
| **E** | unknown writer behaviour | `echo_messages.jsonl`, `sync_state.json` (direct `w`), sense signature files, `memory/models`, anything new | treated as category B (strict). Any file that cannot be verified is labelled `LIVE-MUTATED-DURING-BACKUP` and listed, not hidden |

**What forces a downgrade.** Server PID/start changed during the window (a Metal abort + watchdog restart, ~2/day, rewrites state); a file created/vanished in scope (`SCOPE-DRIFT`, informational); a B1 or Class-A file not verified → `QUARANTINED`; B2/B3 file not verified → level capped at `RESCUE-LIVE` with the file listed.

**The claim this plan will not make:** "this backup is a consistent point-in-time snapshot of a running system." The strongest honest claim is `VERIFIED-LIVE`: every file is a faithful copy of a real version, the FAISS pair is count-aligned and unchanged over the window, the server did not restart, and all copies are structurally loadable.

---

## 5. First-rescue backup (what "rescue" means)
The fastest defensible copy, made **before** any improvement of the preservation code: identity capture → `git bundle` → B1 (verified individually, most important first) → Class A tree → B2 → B3 → hash verification. It is still the full runbook (there is no cheaper safe subset — measured hash throughput is ≈300 MB/s (200 MB in 0.67 s, SYNTHETIC-TESTED on a scratch file), `cp` of 200 MB in 0.06 s from cache); the total data is 1.6 GB, so wall-clock time on the SSD is expected on the order of minutes (INFERRED; not measured on production data; slower on a USB disk). A rescue generation may legitimately end as `RESCUE-LIVE`. It is *never* deleted or edited; a later generation supersedes it in usefulness, not in existence.

---

## 6. Verified backup — the four-step proof
For every file: **(1)** source hash *before*; **(2)** copy; **(3)** source hash *after* and destination hash; **(4)** compare with the category predicate (§4). Class A (22 k static files) uses three bulk hash lists — `A.pre.sha256` (before the tar copy), `A.post.sha256` (after), `A.dest.sha256` (destination) — and any A file that mismatches is retried individually by the same per-file function.

Deterministic manifests: file lists are produced with `LC_ALL=C sort`, hashes with `shasum -a 256` in `sha256␣␣./path` form; `manifest/final.sha256` is the sorted list of accepted destination hashes and is checked with `shasum -a 256 -c` (**PASS** only if every line is `OK`). Independent re-read: after `sync`, the whole tree is hashed again (`fe_stage_cold_verify`), and — for a removable disk — once more after unmount/remount, because the first pass may be served from the page cache. `SEAL.sha256` extends the same check to every non-tree file. The judge writes `GENERATION.json`; the generation is sealed by a marker file whose *name* carries the verdict (`COMPLETE-VERIFIED-LIVE`, `COMPLETE-RESCUE-LIVE`, or `QUARANTINED-NOT-KNOWN-GOOD`).

---

## 7. Mutable-file double-check (exact rules)
Predicates (implemented in `fe_copy_one`, cross-audited by the judge from the recorded hashes):
* **REWRITE (strict)** — PASS iff `dest == pre && pre == post` → `VERIFIED-STABLE`; or `dest == pre || dest == post` → `VERIFIED-LIVE-VERSION`; otherwise `MISMATCH`.
* **APPEND** — PASS iff `sha256(dest) == sha256(head -c size(dest) source_now)` **and** `size(source_now) >= size(dest)` → `VERIFIED-APPEND-PREFIX` (or `VERIFIED-STABLE` if nothing moved); otherwise `MISMATCH`.
* `MISMATCH` → the attempt's copy is **moved** to `work/failed/attemptN/<path>` (never deleted) and the file is retried, up to `FE_MAX_ATTEMPTS` (default 3, bounded). After the last attempt the copy is kept in the tree and the file is recorded as **`LIVE-MUTATED-DURING-BACKUP`** with all three hashes. Every attempt is one row in `copyrec.tsv`.
* Before/after **source** hashing is what makes a torn read detectable: a torn read equals neither a complete earlier nor a complete later version.

**Known limit (OBSERVED in the synthetic test):** a file rewritten faster than it can be hashed (the test used 300 rewrites/s) can never be verified and ends `LIVE-MUTATED-DURING-BACKUP`. FeralEcho's real rewrite rates (river pickle ≈ once a minute, garden ≈ minutes) are orders of magnitude slower — but that is INFERRED from the audit, not measured on production files.

---

## 8. Destination classes and what each one protects against

| Class | Destination | Protects against | Does **not** protect against |
|---|---|---|---|
| **BEST-EXTERNAL** | external disk (APFS/HFS+), unplugged after the run | SSD failure, APFS container corruption, accidental erase, most software faults, macOS reinstall | fire/theft *if kept beside the Mac*; ransomware while attached; a failing disk (verify, keep 2 copies) |
| **BEST-OTHER-MACHINE** | separate machine on separate power/storage | as above + local disaster if geographically apart | compromise of the transfer path |
| **GOOD-AIR** | the Intel Air via one-way, no-delete transfer (§9) | SSD failure of the M5, logical corruption of the M5 state | unknown health/space of the Air (UNKNOWN until inspected); Air is a *different Echo instance* (its own live state must never be overwritten) |
| **TEMPORARY-SAME-SSD** | `$HOME/FeralEcho_backups/` on the M5's SSD, *outside* the repo | **logical corruption**, accidental overwrite/edit, the "corrupt→empty→overwrite" hazard, a bad restart | **any physical failure of the same disk, theft, fire, water, APFS container loss, device replacement/erase** — same failure domain. Evidence that this domain is fragile: every existing "backup" is on this disk and the whole 5-slot snapshot window rotates in ≈20 h |

**Safest first destination.** If the operator has an external disk with ≥ 5 GB free (UNKNOWN — none is mounted now, OBSERVED), use it (BEST-EXTERNAL). If not, **still make the TEMPORARY-SAME-SSD generation today**: the dominant near-term risk is logical corruption (two aborts a day, non-atomic writers), which a same-disk *independent, immutable* generation defeats, and it takes minutes. It must be followed by an off-device copy as soon as one exists; it is **not** a substitute for one.

---

## 9. Intel Air — one-way plan and read-only pre-inspection
**Principles.** Push-only, append-only, no delete, no overwrite; the Air receives a *sealed generation* into a **new** directory `~/FeralEcho_backups_from_M5/<generation-id>/` and is never asked to run FeralEcho on it; nothing is placed inside any FeralEcho checkout on the Air (a different Echo instance whose own state must not be touched).
**Direction decision.** Either machine must accept an SSH connection. Enabling Remote Login on the **M5** would add a new listener on the production machine; enabling it on the **Air** exposes the less critical machine. The plan therefore has the **M5 push** to the Air (`ssh` client only on the M5). Because the receiving command uses `mkdir`-if-absent and `tar -k`, an M5-side fault or a corrupted source cannot overwrite an older generation on the Air. (Residual: an M5 compromise holding the key could still write *new* directories on the Air — a dedicated key with a forced command is a later hardening, not needed for today.)

### 9.1 Read-only pre-inspection (RUN ON INTEL — physically at the Air; nothing is written, nothing is enabled)
```bash
# RUN ON INTEL   (read-only; copy the whole output back to the operator's notes)
uname -m; sw_vers; scutil --get LocalHostName; sysctl -n hw.model
df -h /
diskutil info / | grep -E "File System Personality|Volume Name|Solid State|SMART Status|Device Location|Volume Free Space|FileVault"
fdesetup status
tmutil destinationinfo 2>&1 | head -5
/bin/bash --version | head -1
command -v shasum tar cp ditto rsync sqlite3 python3
tar --version | head -1
ls -ld "$HOME/FeralEcho_backups_from_M5" 2>&1      # must report "No such file or directory"
ls -d "$HOME"/Desktop/FeralEcho* "$HOME"/FeralEcho* 2>&1 | head -10   # names only: is a fork checkout present, and where?
launchctl print-disabled system 2>/dev/null | grep -i ssh              # informational: is the ssh service disabled?
```
**Decision table.** Proceed only if: `uname -m` = `x86_64`; ≥ 5 GB free (3 × generation size); SMART Status `Verified` (or `Not Supported`, noted); `FeralEcho_backups_from_M5` absent; `shasum` and `tar` and `/bin/bash` present. Whether the Air is reachable from the M5, whether Remote Login is enabled, and its Tailscale name are **UNKNOWN** and must not be discovered by scanning — the operator reads the Air's own Tailscale app and types the name into `FE_AIR`.

### 9.2 Transfer and verification (later, only after explicit approval; not part of minimum-today)
```bash
# RUN ON M5   (after a sealed generation exists at $FE_DEST_ROOT/FeralEcho_backups/$FE_GEN_ID)
case "${FE_AIR:-}" in ""|*EXACT*|*REPLACE*) echo "STOP: set FE_AIR to the Air's own Tailscale name or IP"; false;; esac
ssh -o BatchMode=yes -o ConnectTimeout=10 "$FE_AIR" "mkdir -p FeralEcho_backups_from_M5 && test ! -e FeralEcho_backups_from_M5/$FE_GEN_ID && df -k ."
( cd "$FE_DEST_ROOT/FeralEcho_backups" && tar -cf - "$FE_GEN_ID" ) | ssh -o BatchMode=yes "$FE_AIR" "cd FeralEcho_backups_from_M5 && tar -xpkf -"
```
```bash
# RUN ON INTEL   (bash 3.2 is enough; the generation carries its own tools)
/bin/bash
export FE_GEN="$HOME/FeralEcho_backups_from_M5/<the exact FE_GEN_ID printed on the M5>"    # type the real ID; the next line refuses a wrong path
test -f "$FE_GEN/SEAL.sha256" || echo "STOP: wrong path"
. "$FE_GEN/tools/fe_lib.sh"; . "$FE_GEN/tools/fe_stages.sh"
fe_stage_cold_verify
shasum -a 256 "$FE_GEN/GENERATION.json"          # compare with the hash printed on the M5 (generations.log, 4th column)
```
The Intel side verifies **bytes**, not semantics; structural validation (needs `faiss`) was done on the M5 before sealing.
**Untested:** every Intel/ssh command in this section (no network use is allowed in this mission). Treat §9.2 as a design to be rehearsed once, on a *small* dummy generation, before trusting it.

---

## 10. External-drive plan (RUN ON M5, operator-attended; **nothing here formats or erases anything**)
1. **Identify without writing:** `ls -la /Volumes` and `diskutil list` (read-only). Plug the drive in only when told; run both commands again and note the *new* entry.
2. **Inspect the chosen volume:** `diskutil info "/Volumes/<name>"` — record *Volume Name*, *Volume UUID*, *File System Personality*, *Device Location* (must say `External`), *Volume Free Space*, *Read-Only Volume* (must be `No`), *Solid State*, *Protocol*. If `Device Location` says Internal, or the volume is the boot volume, it is **not** an external drive (`FE_DEST_CLASS` would be a lie; `fe_stage_precheck` also refuses a class ≠ TEMPORARY when the stat device ids match).
3. **Filesystem:** APFS or HFS+ preferred (preserves permissions, xattrs, mtimes). **exFAT/FAT** drop POSIX modes (`.env` would lose 0600 — the manifest's `stat.tsv` records modes so a restore can re-apply them) and may create `._*` AppleDouble sidecars, which the judge will report as `DEST-TREE … extra` and label the generation `QUARANTINED`; use APFS unless nothing else exists. **NTFS** is read-only from macOS: unusable. **Never reformat** as part of this plan; if the drive holds other data it is left alone — the plan writes only a new `FeralEcho_backups/` directory.
4. **Encryption:** every generation contains **secrets** (`.env`, API keys, the shared `GREMLIN_SECRET`/`ECHO_PARTNER_SECRET`). An encrypted APFS volume is strongly recommended. Whether to encrypt is the operator's decision; enabling it means reformatting a *new/empty* drive — outside this plan.
5. **Space:** free ≥ 2 × source (enforced by `fe_stage_precheck`); recommend ≥ 10 × one generation (≈ 16 GB) so that months of generations fit.
6. **Generation naming:** `FeralEcho_backups/gen-<UTC>-<LABEL>-<M5|INTEL>` (e.g. `gen-20260920T134500Z-RESCUE1-M5`), unique, sortable, never reused.
7. **Copy and verify:** §17 steps 3–8. Then `sync`.
8. **Eject and cold-verify:** `diskutil unmount "$FE_DEST_ROOT"`, physically unplug, plug back in, re-run `fe_stage_cold_verify`. Only then is the copy proven to have reached the medium, not just the cache. Record the result in the operator's notes.
9. **Restore test:** `fe_stage_drill` (§14) into a scratch directory on the M5's SSD — later, not today.
10. **Storage:** label the disk; keep it disconnected when not in use (an attached backup is exposed to the same ransomware/`rm`/software faults as the source); keep the second copy in a different place.

---

## 11. Generation retention

**The rule, kept exactly as given — and it is not excessive:**

> **NO BACKUP GENERATION MAY BE DELETED UNTIL AT LEAST TWO OTHER VERIFIED RECOVERY COPIES EXIST ON PHYSICALLY DISTINCT STORAGE.**

Definitions: a *verified recovery copy* = a sealed generation labelled `COMPLETE-VERIFIED-*` (not `RESCUE-LIVE`, not `QUARANTINED`), whose `fe_stage_cold_verify` passed on *that* storage within the last 30 days. *Physically distinct storage* = a different physical device from each other and from the generation proposed for deletion (a second volume or partition on the same disk does **not** count; the M5's SSD counts as one device). The copies counted are *other generations or byte-verified replicas*, never the live production files.

Why it is not excessive: one generation is ≈ 1.6 GB; a 500 GB disk holds hundreds. Storage pressure will not force any deletion for a long time, so the rule costs nothing today and removes the failure mode "we pruned the good one after the bad one arrived". Consequence for now: **nothing may be deleted at all** (no generation, and — separately — none of the old `memory_meta_backup_*`, `river_brain.pkl.pre_*`, or snapshot files in the source, which stay as they are).
The plan contains **no deletion command** of any kind. If a human ever deletes a generation, they do it by hand, after checking the rule against `generations.log`. The production `snapshot_manager` rotation (5 slots) is unchanged and untouched (production code is out of scope); these generations make that rotation harmless. Suggested cadence once the procedure is proven: one generation per day plus one immediately before/after any risky operation.

---

## 12. Corruption-propagation defence
| Defence | Mechanism |
|---|---|
| Independent generations | no incrementals, no mirroring: an old good generation cannot be overwritten by a new bad state |
| Size floors | absolute floors in `fe_validate.py` (≈ 95 % of the measured 2026-09-20 sizes): `memory_meta.json` ≥ 95 MB and ≥ 124,000 entries; `faiss.index` ≥ 190 MB; `question_garden.jsonl` ≥ 10 MB and ≥ 15,000 lines; `river_brain.pkl` ≥ 4.0 MB; `self_model_claims.jsonl` ≥ 8 KB. Violations ⇒ `VALIDATION` anomaly ⇒ **QUARANTINED**. (SYNTHETIC-TESTED: the default floors correctly fail a tiny fixture.) A relative floor against the previous verified generation is a *manual* comparison of two `validation.json` files — not automated, not tested |
| FAISS vs metadata | `faiss.read_index(copy).ntotal` must equal `len(json.load(meta copy))`; mismatch ⇒ `pair_aligned:false` ⇒ level capped at `RESCUE-LIVE` and a failure recorded. (A mismatch where meta is *ahead* is repairable per the audit; where the index is ahead it is not — the copy is kept either way) |
| Structural validity | pickles are walked with `pickletools.genops` to the `STOP` opcode (SYNTHETIC-TESTED: a stream referencing a non-existent module passes; a truncated stream fails) — **no unpickling, so no FeralEcho import, no code execution**; JSON/JSONL parsed line by line (≤ 1 invalid last line tolerated); SQLite `integrity_check` via `mode=ro&immutable=1` |
| Validation only on copies, in a jail | `sandbox-exec -p '(version 1)(allow default)(deny file-write*)(deny network*)(allow file-write* (literal "/dev/null") (literal "/dev/dtracehelper"))'`, `python -I`, `PYTHONDONTWRITEBYTECODE=1` (SYNTHETIC-TESTED: a write outside is denied with "Operation not permitted"). The source is never opened by a validator |
| Never import production persistence modules | validator imports only `faiss`, `json`, `pickletools`, `sqlite3`, `os`, `sys`; `-I` ignores the working directory and `PYTHONPATH` |
| Honest labelling | any validation failure, coverage failure, or unverified B1/Class-A file ⇒ marker file `QUARANTINED-NOT-KNOWN-GOOD` and `consistency_level: QUARANTINED` — **kept**, never counted as a recovery copy, never used for a restore over live state |
| Torn-source awareness | a hash match proves the copy equals the source *as it was*; a source that was already torn/empty is copied faithfully and caught by the validators/floors, not by the hashes |
| Secrets | the backup *increases* the number of places `.env` exists. Keep destinations under operator control; do not put generations on cloud-synced folders |

---

## 13. Restore procedure (designed before the first backup; **never executed here**)
Principles: **restore into a NEW directory first; never over live state; get explicit approval before any change to production; preserve the current live state before touching it; use only `COMPLETE-VERIFIED-*`/`RESTORE-TESTED` generations.**

* **R0 — Decide the scenario.** (a) one damaged file; (b) FAISS/meta pair; (c) source tree; (d) whole machine lost. For (a) and (b) the *current* files are first preserved (R1) and the replacement is placed beside the original as `<name>.recovered` for the operator to swap.
* **R1 — Preserve current state (mandatory, even if it looks corrupt).** Make a fresh generation of the current live state (label `PRE-RESTORE`) using §17. A `QUARANTINED` result is fine — it is evidence.
* **R2 — Choose the generation.** `cat "$DEST/FeralEcho_backups/generations.log"`; take the newest `COMPLETE-VERIFIED-*` with a `RESTORE-TESTED` line if one exists.
* **R3 — Verify it.** `fe_stage_cold_verify` (must PASS).
* **R4 — Restore into a scratch directory** with the drill's copy step (`tar` extraction with `-k`), never into the live path.
* **R5 — Validate the restored copy** with `fe_validate.py` in the jail; check counts against `GENERATION.json` (`validation`) and `identity/git_head.txt`.
* **R6 — Git.** The restored `.git` should report the recorded HEAD; independently `git clone generation/git/repo.bundle` must reach the same HEAD. If the tree is restored to a **different path**, run `git -C <restored-root> worktree repair <restored-root>/.claude/worktrees/agent-abe6ecca0408fd0fb` (SYNTHETIC-TESTED: this rewrites only the restored copy's pointers; the original repository was byte-identical afterwards). **Never run any git command inside a restored worktree before that repair** — its `.git` file points at the original repo.
* **R7 — Permissions.** From `manifest/stat.tsv`: re-apply modes (`.env` must be 0600) if the destination filesystem lost them.
* **R8 — Do not restore ephemeral files:** `memory/echo_server.pid`, `memory/echo_sentinel.json` (stale after any abort), and any `*.lock` file.
* **R9 — Swap into production (only with explicit approval, server stopped through the watchdog path — see `safe_restart.sh`, never a raw `kill`).** Order: source/Git → non-pair state → `memory_meta.json` then `faiss.index` (**from the same generation only**) → `river_brain.pkl` **last** (the order `snapshot_manager` itself uses). Then start via the watchdog.
* **R10 — After start:** compare RiverBrain observation total, FAISS `ntotal`, meta count, garden line count against the manifest; run `/admin/liveness-status`; record the outcome as a new line in `generations.log`. Ollama models are re-created from the tracked `Modelfile` + `llama3:instruct` (or re-pulled); verify digests against `identity/runtime.txt`. **Untested on production; unknown:** whether the registry still serves the 12-month-old `llama3:instruct` digest.

---

## 14. Restore drill (temporary isolated directory — **not run now**)
`fe_stage_drill` (Appendix B): requires a sealed `COMPLETE-*` generation; cold-verifies it; extracts the tree into `FE_DRILL_DIR` (must not exist, must not be inside the production tree); re-hashes the restored tree against `final.sha256`; checks the restored `.git` HEAD and a fresh `git clone` of the bundle against `identity/git_head.txt`; compares the changed/untracked path count (ignoring the three excluded patterns); runs `git fsck` on the *restored* copy; runs the validator on the restored tree inside the jail; appends `RESTORE-TESTED` to `generations.log`. It never touches production and never runs git inside the restored worktree.
Acceptance: all steps pass. Repeat after the first successful generation, after each new destination, and monthly.
**SYNTHETIC-TESTED:** the drill passed on the fixture (including a linked worktree), and the fixture's source `.git` was byte-identical before/after. A first draft warned "path count 25 vs 23" because the backup excludes `__pycache__`/`.DS_Store`; the comparison now ignores those patterns on both sides.

---

## 15. Manifest schema
`audits/2026-09-20_feralecho_backup_manifest_schema.json` (JSON Schema 2020-12, valid; a manifest produced from the synthetic fixture validates with 0 errors). Required content: generation ID; created/completed UTC; host name/OS/arch; tool versions; source root, `live` flag, Git head/branch/dirty/porcelain count/unpushed count; authored-tree fingerprint (with and without self-mutating files) + legacy reference; server PID/start before and after and `restarted_during_backup`; destination class/root/filesystem/volume UUID/device location/same-device flag/free bytes; **consistency level** ∈ {`RESCUE-LIVE`, `VERIFIED-LIVE`, `VERIFIED-QUIESCENT`, `QUARANTINED`, `RESTORE-TESTED`}; per-file inventory (path, tier, part, size, sha256, pre/post source sha256, status, type, attempts); validation results; anomalies; audit references; exclusions.
Level semantics: **RESCUE-LIVE** — every file is a faithful copy of a real (or append-prefix) version but pair alignment/validation/steady server are not all established. **VERIFIED-LIVE** — RESCUE-LIVE + validation passed + FAISS count = meta count + same server PID/start + every B1 file verified. **VERIFIED-QUIESCENT** — as VERIFIED-LIVE but with all writers stopped (future; `fe_judge.py` cannot produce it). **QUARANTINED** — NOT KNOWN GOOD. **RESTORE-TESTED** — a `VERIFIED-*` generation whose drill passed; because a sealed generation is never edited, it is recorded as an append-only `generations.log` line, and `restore_drill` inside `GENERATION.json` stays `null`.

---

## 16. Justified exclusions ("do not back up garbage" without dropping value)
| Excluded | Count / size (OBSERVED) | Justification |
|---|---|---|
| `**/__pycache__/**` | 79 directories | bytecode regenerated by Python from the source that *is* backed up; nothing authored |
| `**/.pytest_cache/**` | 1 directory | tool cache, regenerated |
| `**/.DS_Store` | 42 files | Finder view metadata |

**Deliberately NOT excluded despite size or "zero references":** `memory/faiss.index` (201 MB, expensive to rebuild), `memory_meta_backup_before_*` (89 MB each — user rule: never delete), `dream_bridge.log` (81 MB) and other logs (Echo's own record), `WhisperOfPeace.wav` (20 MB) and `Figure_*.png` (incident records Echo produced — the project's own memory says "kept incident records, not clutter"), scaffold directories (`x86_64_env`, `my_python_project`, …: self-edit output, possibly meaningful), `.claude/` (69 MB, includes the worktree and `settings.local.json`), `sandbox/` (83 MB), `app/core/self_edit_backups/` and `self_edit_plans/`. Rationale: "no live code references" has been wrong here before (recorded in the project's own history).

**Out of automation scope, each a decision for the operator:** Ollama weights (35 GB; rebuildable from the tracked `Modelfile` plus a base model *if the registry still serves it*; optionally copy the blobs of `echo:latest` + `llama3:instruct`, ≈ 4.7 GB + adapter, to remove that dependency); the conda environment (rebuildable from `identity/pip_freeze.txt`); the HuggingFace `all-MiniLM-L6-v2` cache (`~/.cache/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2`, ≈ 90 MB — recommended manual copy because startup is offline-only); `~/.ssh` and Tailscale credentials; the Intel Air's own FeralEcho state.

---

## 17. Exact operator runbook

**Conventions.** Every block begins with a host label: `# RUN ON M5`, `# RUN ON INTEL`, or `# RUN ON EXTERNAL DESTINATION` (meaning: the command reads/writes the mounted external volume, still typed on the M5). Blocks are pasted **one at a time**; if any line prints `STOP:` or a stage returns non-zero, **stop and do not paste the next block**. Nothing below stops, restarts, or signals FeralEcho. Nothing below runs Git commands that change state (`git bundle create`, `git diff`, `git status`, `git ls-files`, `git for-each-ref`, `git rev-parse`, `git clone` *of the bundle into a new directory*, and — in the restore path only — `git worktree repair <path>` on the restored copy). The M5's normal shell is zsh; **every block assumes a fresh `/bin/bash`** (3.2), started in step 1.

**Human preconditions (no command can enforce these):** no other Claude Code/IDE session is running in the repo; nobody runs `git`, `safe_restart.sh`, `kill`, or an experiment for the duration; the Mac is on power and will not sleep; FeralEcho is left running exactly as it is.

### 17.1 Step 1 — PRECHECK (before-state)
```bash
# RUN ON M5
/bin/bash --noprofile --norc
export GIT_OPTIONAL_LOCKS=0
export FE_SRC="/Users/richietate/Desktop/FeralEcho"
export FE_PY="/Users/richietate/miniforge3/envs/feral_echo/bin/python3"
uname -m                                   # MUST print: arm64   (Intel would print x86_64 — then STOP)
cd "$FE_SRC" || echo "STOP: no such directory"
git rev-parse HEAD                         # write it down (expected on 2026-09-20: 2fba42644c82b9f7096276f4dd338d615cf1bcce)
git status --porcelain | wc -l             # write it down (186 before this mission's files were added)
ps -o pid=,lstart= -p "$(cat memory/echo_server.pid)"    # write it down (expected: 29288, Sun Sep 20 07:30:10 2026)
date -u +%Y-%m-%dT%H:%M:%SZ                # write it down
"$FE_PY" --version                         # expect Python 3.12.13
```
```bash
# RUN ON M5   (install the tools; the directory is created with plain mkdir, so it cannot silently reuse an old one)
export FE_TOOLS_DIR="$HOME/fe_backup_tools"
mkdir "$FE_TOOLS_DIR" || echo "STOP: $FE_TOOLS_DIR already exists — choose another name, never reuse"
# Now paste, in order, Appendix A (fe_lib.sh), B (fe_stages.sh), C (fe_judge.py), D (fe_validate.py), E (b1.lst and b2.lst).
# Each appendix block is a complete `cat > "$FE_TOOLS_DIR/…" <<'FE_EOF'` command — paste it as it stands.
shasum -a 256 "$FE_TOOLS_DIR"/fe_lib.sh "$FE_TOOLS_DIR"/fe_stages.sh "$FE_TOOLS_DIR"/fe_judge.py "$FE_TOOLS_DIR"/fe_validate.py "$FE_TOOLS_DIR"/b1.lst "$FE_TOOLS_DIR"/b2.lst
# Compare each line with the table in Appendix F. ANY difference = paste corruption: STOP.
```

### 17.2 Step 2 — DESTINATION CHECK (read-only; writes nothing)
```bash
# RUN ON M5
ls -la /Volumes
diskutil list
# For an external disk: note the mounted volume's name in /Volumes and type it below EXACTLY.
# For the TEMPORARY same-SSD generation use:  export FE_DEST_ROOT="$HOME"   and   export FE_DEST_CLASS=TEMPORARY-SAME-SSD
export FE_DEST_ROOT="/Volumes/EDIT-THIS-TO-THE-EXACT-VOLUME-NAME"   # deliberately a path that does not exist: if you forget to edit it, the next stage refuses it
export FE_DEST_CLASS=BEST-EXTERNAL                                    # or TEMPORARY-SAME-SSD — must match reality
export FE_HOST_TAG=M5
export FE_LABEL=RESCUE1
export FE_B1_LIST="$FE_TOOLS_DIR/b1.lst"; export FE_B2_LIST="$FE_TOOLS_DIR/b2.lst"
. "$FE_TOOLS_DIR/fe_lib.sh"; . "$FE_TOOLS_DIR/fe_stages.sh"
echo "--- SOURCE volume:";      diskutil info "$(fe_devnode "$FE_SRC")"       | grep -E "Volume Name|Volume UUID|File System Personality|Device Location|Solid State|Part of Whole|APFS Physical Store"
echo "--- DESTINATION volume:"; diskutil info "$(fe_devnode "$FE_DEST_ROOT")" | grep -E "Volume Name|Volume UUID|File System Personality|Device Location|Solid State|Part of Whole|APFS Physical Store|Free Space|Read-Only"
# CONFIRM by eye: for a BEST-* class the destination must be Device Location: External and a different Part of Whole / APFS Physical Store than the source.
fe_stage_show
```
`fe_stage_show` prints `FE_SRC`, `FE_DEST_ROOT`, `FE_DEST_CLASS`, `FE_GEN_ID`, `FE_GEN` and the exact confirmation line. **Read them.** Then type the confirmation line exactly as printed (it contains the generation ID, so a stale confirmation from an earlier attempt cannot authorise a new generation):
```bash
# RUN ON M5
export FE_CONFIRMED=YES-WRITE-TO-<the FE_GEN_ID printed by fe_stage_show>
fe_stage_precheck        # must end with: PRECHECK PASS
fe_stage_dest            # first stage that writes — destination only — must print: generation directory created
```

### 17.3 Step 3 — SOURCE IDENTITY (read-only against the source; writes to the generation)
```bash
# RUN ON EXTERNAL DESTINATION   (writes only under $FE_GEN; reads the repo and the running process's PID/start)
fe_stage_source_identity      # writes identity/, git/repo.bundle (verified), manifest/kv.env; prints the server PID/start
fe_stage_lists                # builds and checks the A/B1/B2/B3 partition; must end with: LISTS PASS
```
Expected: `LISTS PASS`, with `B1=13` and `B2=11`. A `STOP: a B1 file is missing from the source` means the plan's file list no longer matches the machine — stop and revise the plan; do not edit the list on the fly.

### 17.4 Step 4 — RESCUE COPY
```bash
# RUN ON EXTERNAL DESTINATION
fe_stage_copy_B          # B1 first, then B2, then B3; per-file pre/post/dest hashing; bounded retry. Prints NOT-VERIFIED lines if any
fe_stage_copy_A          # bulk tar stream of the non-state tree + three bulk hash lists
```
`fe_stage_copy_B` returning non-zero only means some file could not be verified (it is listed); the judge decides the label. Do not re-run a stage that already copied (it will refuse: destination exists) — **start a new generation instead**.

### 17.5 Step 5 — MANIFEST
```bash
# RUN ON EXTERNAL DESTINATION
fe_stage_after_state     # server PID/start after; scope drift (files created/vanished); HEAD unchanged?
fe_stage_judge           # coverage, per-file verdicts, retry of failing Class-A files, GENERATION.json (first pass)
```
Expected first pass: `consistency_level=RESCUE-LIVE … anomalies=0` (it cannot be higher before validation). `QUARANTINED` here means a Class-A/B1 file or the coverage failed: read the listed `ANOMALY:` lines; the generation is kept, labelled, and a new one is attempted after the cause is understood.

### 17.6 Step 6 — HASH VERIFICATION (independent re-read)
```bash
# RUN ON EXTERNAL DESTINATION
sync
fe_stage_cold_verify     # re-hashes every tree file against manifest/final.sha256; must print COLD VERIFY PASS
```

### 17.7 Step 7 — STATE VALIDATION (copies only, inside the jail)
```bash
# RUN ON EXTERNAL DESTINATION
fe_stage_validate        # sandbox-exec jail, python -I; prints "passed" and "pair_aligned"
fe_stage_judge           # second pass: folds validation into GENERATION.json
```
Expected: `"passed": true`, `"pair_aligned": true`, and `consistency_level=VERIFIED-LIVE`. If the FAISS/meta counts differ the generation stays `RESCUE-LIVE` and the mismatch is recorded — it is **information about production state**, not a reason to alter anything.

### 17.8 Step 8 — GENERATION LABEL, then Step 9 — SECOND COPY / SECOND DEVICE
```bash
# RUN ON EXTERNAL DESTINATION
fe_stage_label           # SEAL.sha256, GENERATION.json.sha256, marker COMPLETE-<level> or QUARANTINED-NOT-KNOWN-GOOD, generations.log line
ls "$FE_GEN"; cat "$FE_DEST_ROOT/FeralEcho_backups/generations.log"
```
```bash
# RUN ON EXTERNAL DESTINATION   (second physically distinct device mounted; different volume from the first, enforced)
export FE_DEST2_ROOT="/Volumes/EDIT-THIS-TO-THE-SECOND-DEVICE-VOLUME-NAME"
fe_stage_replicate       # byte copy of the SEALED generation, cold-verify there, REPLICA-VERIFIED line; must print REPLICA PASS
```
If no second device exists yet, that is the state to remember: **one copy is a rescue, not safety** (§11). For the Intel Air use §9.

### 17.9 Step 10 — RESTORE DRILL (later; not part of today), Step 11 — FINAL STATUS
```bash
# RUN ON M5   (LATER — after approval; restores into a NEW scratch directory; never the production tree)
export FE_DRILL_DIR="$HOME/fe_restore_drill_$(date -u +%Y%m%dT%H%M%SZ)"
fe_stage_drill           # must print DRILL PASS ... and appends RESTORE-TESTED to generations.log
```
```bash
# RUN ON M5   (FINAL STATUS — record all of it in the operator's notes)
cd "$FE_SRC" && git rev-parse HEAD && git status --porcelain | wc -l && ps -o pid=,lstart= -p "$(cat memory/echo_server.pid)"
cat "$FE_DEST_ROOT/FeralEcho_backups/generations.log"
# Compare with step 1: HEAD identical; porcelain count identical; server PID and start time identical.
# Physically label the drive; unplug it; keep it away from the Mac. Cold-verify once more after the next plug-in.
```

### 17.10 What the synthetic tests did and did not prove (SYNTHETIC-TESTED, session scratchpad only)
A throw-away fixture (a small git repo with a linked worktree, 50-entry `memory_meta.json`, a real 50-vector FAISS index, pickles including one that would raise `ImportError` if loaded, a JSONL garden, a SQLite DB, files with spaces and parentheses in their names, `__pycache__`/`.DS_Store`) was backed up with the tools exactly as pasted in the appendices. Results:
| Test | Result |
|---|---|
| Clean run | RESCUE-LIVE → (validation) → **VERIFIED-LIVE**; cold verify passes; source fixture byte-identical (content hash + size + mtime, including its `.git`) before and after |
| Concurrent hot non-atomic rewriter + atomic rewriter + append growth while copying | append files verified via prefix rule; the two continuously rewritten files ended `LIVE-MUTATED-DURING-BACKUP` (correct — un-verifiable); B3-only failures cap the level at RESCUE-LIVE with the files listed; Class-A/B1 failures ⇒ QUARANTINED |
| Tamper one byte in a destination file / replica identity file | `COLD VERIFY FAIL` naming the file |
| Delete a file from the destination tree | judge flags `DEST-TREE` ⇒ QUARANTINED |
| Truncated pickle; default floors on a tiny fixture | validator fails (`not enough data in stream`; 7 floor failures) |
| `sandbox-exec` jail | write outside denied ("Operation not permitted"); read allowed |
| `mkdir` of an existing generation; `fe_copy_one` onto an existing file; second `fe_stage_replicate` to the same target; second judge on a sealed generation | all **refused** |
| A-part mismatch | judge lists it in `retry.lst`; retry moves the old copy to `work/failed/pre-retry/` and re-copies; ends VERIFIED-STABLE |
| Scope drift | a file listed in `created_during.lst` becomes an informational `SCOPE-DRIFT` anomaly |
| Replication (with the same-volume guard bypassed for the test only) | REPLICA PASS; tamper detected |
| Restore drill incl. linked worktree | DRILL PASS; original fixture `.git` untouched by drill and by `git worktree repair <restored path>` |
| Throughput | `shasum -a 256`: 200 MB in 0.67 s (≈300 MB/s) |

**Not proven:** anything on the real 1.6 GB tree (file count 22,761, real FAISS/pickle contents); behaviour under the real server's write pattern; any external-drive, exFAT, Intel, SSH or Tailscale step; whether `cp -p` clones on APFS by default (a 200 MB copy took 0.06 s, which is consistent with a page-cache copy *or* a clone — not determined; on the same volume that only affects how independent the TEMPORARY copy is physically, not its logical independence); `tmutil localsnapshot`; the `PORCELAIN` count semantics at 249 paths; performance of `git bundle create` on the real 36 MB `.git` (expected seconds — INFERRED).

---

## 18. Destructive-command review

**Rejected outright (not used anywhere in the runbook or tools):**
| Command / pattern | Why rejected |
|---|---|
| `rm`, `rm -rf`, `find -delete` | irreversible; the plan needs no deletion (failed attempts are *moved* inside the generation) |
| `rsync --delete`, any mirroring `rsync -a src/ dest/` | mirrors deletions/corruption; not a backup (§2) |
| `mv` of a **source** file; `mv` over a destination file | source is read-only in this plan; `mv` appears only for moving *the procedure's own failed attempts* within `$FE_GEN/work/failed/` (source: `fe_lib.sh`, 2 sites) |
| `git reset`, `git clean`, `git checkout`, `git restore`, `git stash push/pop/drop`, `git commit/add/push/pull/fetch/gc/rebase/merge`, force push | all mutate Git state or history; the backup reads Git only. (`git stash list` is read-only and used) |
| `diskutil erase*/partition*/reformat/apfs delete*`, `newfs*`, `dd`, `hdiutil` | would alter or format a drive — the plan never does |
| `tmutil` (any verb), `sudo`, `chmod -R`, `chown -R`, `kill*`, `pkill`, `launchctl` (except `print-disabled`, read-only, on the *Air* pre-inspection) | system writes / process control; forbidden by the mission or unnecessary |
| `cp -c`, `ditto` onto existing paths, `>` redirection onto an existing file | clone semantics / silent overwrite. Redirections in the tools write only *new* files inside `$FE_GEN` (the generation directory is created empty by `mkdir`), plus `>>` to the append-only `generations.log` |
| `sed -i`, in-place editing of anything | not used (only `sed -E` as a filter) |
| `backup_feral_echo.sh` | rewrites `.gitignore`, changes git config — never run |
| Any command using a variable that could be empty as a path root | every stage begins with `: "${VAR:?…}"` or an explicit `[ -d ]` check; `mkdir` and `tar -k` fail rather than overwrite |

**Preferred fail-if-exists forms used:** `mkdir "$FE_GEN"` (no `-p`), `tar -xkf` (keep existing), `[ -e "$d" ]` guard in `fe_copy_one`, `test ! -e` on the Air, judge refusal on sealed generations, `>>` for the registry.

**Automated lint of every fenced code block in §17 and Appendices A–E** (executed when this file was generated; regexes and results):
Scanner self-check: 18 fenced blocks, 591 code lines scanned; positive controls (`mv`, `git bundle create`, `git clone`, `mkdir -p`) were found, so the scanner is not blind.

| Pattern | Occurrences in runbook + tools | Reading |
|---|---:|---|
| rm as a command | 0 | none — required |
| --delete | 0 | none — required |
| mv | 2 | only the two failed-attempt moves inside `$FE_GEN/work/failed/` |
| git reset/clean/checkout/restore/commit/add/push/pull/fetch/gc/rebase/merge/stash-mutating | 0 | none — required |
| rsync | 0 | none in code (mentioned only in prose) |
| diskutil erase/partition/reformat/apfs | 0 | none |
| dd | 0 | none |
| sudo | 0 | none |
| kill/pkill | 0 | none |
| tmutil | 0 | none |
| sed -i | 0 | none |
| chmod/chown | 0 | none |
| cp -c | 0 | none |
| git bundle create | 1 | 1 site: streams to the bundle file in `$FE_GEN/git/` |
| git clone | 1 | drill only: clones the *bundle* into a new directory |
| git worktree repair | 0 | restore/drill copy only (prose in §13; not executed by any stage) |
| mkdir -p | 5 | creates only parent directories of destination paths / generation container |

Exact matching lines for the non-zero patterns:
* `mv` → `mkdir -p "$FE_GEN/work/failed/pre-retry/$(dirname "$rel")" && mv "$d" "$FE_GEN/work/failed/pre-retry/$rel" || `
* `mv` → `MISMATCH) mkdir -p "$FE_GEN/work/failed/attempt$attempt/$(dirname "$rel")" && mv "$d" "$FE_GEN/work/failed/att`
* `git bundle create` → `( cd "$FE_SRC" && git bundle create "$FE_GEN/git/repo.bundle" --all ) || { echo "STOP: git bundle failed"; ret`
* `git clone` → `git clone -q --no-checkout "$FE_GEN/git/repo.bundle" "$FE_DRILL_DIR.bundle_clone" 2>/dev/null || { echo "DRILL`
* `mkdir -p` → `mkdir -p "$FE_GEN/work/failed/pre-retry/$(dirname "$rel")" && mv "$d" "$FE_GEN/work/failed/pre-retry/$rel" || `
* `mkdir -p` → `mkdir -p "$(dirname "$d")" || return 2`
* `mkdir -p` → `MISMATCH) mkdir -p "$FE_GEN/work/failed/attempt$attempt/$(dirname "$rel")" && mv "$d" "$FE_GEN/work/failed/att`
* `mkdir -p` → `mkdir -p "$FE_DEST_ROOT/FeralEcho_backups" || return 1`
* `mkdir -p` → `mkdir -p "$FE_DEST2_ROOT/FeralEcho_backups" || return 1`

**Hard-fail patterns present: NONE**


**Judgement on residual risk:** the tools *write* to exactly three places — the generation directory `$FE_GEN`, the append-only `generations.log` next to it, and (for the drill) a caller-supplied new `FE_DRILL_DIR`/`…bundle_clone`/`drill_fsck_*.txt`. They *read* the repository and the process table. The single command that touches the repository object store at all is `git bundle create`, which streams to the bundle file; the source `.git` was byte-identical after it in the synthetic test, and the Class-A pre/post hash compare would flag any change on the real tree.

---

## 19. Minimum-today plan

Goal: get one verified, independent, immutable generation of **Class A + B1 + Class C** (plus B2/B3, which cost nothing extra here) off the running production tree today, without stopping anything.
1. **Freeze** (§17 preconditions): other sessions closed; no git; power on.
2. **Step 1** — record before-state; install and hash-check the tools.
3. **Step 2** — choose the destination: an attached external disk (BEST-EXTERNAL) if one exists; otherwise `FE_DEST_ROOT="$HOME"` with `FE_DEST_CLASS=TEMPORARY-SAME-SSD`. Read the printed variables; type the confirmation.
4. `fe_stage_precheck` → `fe_stage_dest`.
5. **Step 3** — `fe_stage_source_identity` (Git bundle first, so the history is safe within seconds) → `fe_stage_lists`.
6. **Step 4** — `fe_stage_copy_B` (B1 first) → `fe_stage_copy_A`.
7. **Step 5–7** — `fe_stage_after_state`, `fe_stage_judge`, `sync`, `fe_stage_cold_verify`, `fe_stage_validate`, `fe_stage_judge`.
8. **Step 8** — `fe_stage_label`. Expected `COMPLETE-VERIFIED-LIVE`; `COMPLETE-RESCUE-LIVE` is acceptable for a first rescue; `QUARANTINED-…` is kept and investigated.
9. **As soon as a second device exists** — `fe_stage_replicate`, or the Air path (§9) after its pre-inspection.
10. **Not today unless approved:** the restore drill, any Air transfer, any change to production code, any restart.
11. **Record** the final status block (step 11) in the operator's notes.

If step 1's `uname -m` is not `arm64`, or any `STOP:` appears, stop and report; do not improvise.

---

## 20. Final answers

**(1) The exact minimum data set that must survive.**
* **Source lineage:** the full repo tree including `.git` (all refs; the 17 unpushed commits), the 27 tracked-modified and 221 untracked authored files, `.env`, and a `git bundle --all` of the history.
* **State (B1, 13 files, 317,043,348 B):** `memory/memory_meta.json`, `memory/faiss.index` (kept with the meta as a *pair*), `data/question_garden.jsonl`, `memory/river_brain.pkl`, `memory/task_type_classifier.pkl`, `memory/drift_detectors.pkl`, `memory/self_model_claims.jsonl`, `memory/council_ratings.jsonl`, `memory/snapshot_baseline.json`, `memory/behavioral_directives.json`, `memory/genesis/{genesis_hash,council_hash,genesis_timestamp}.txt`.
* **Identity/recovery evidence (Class C):** HEAD/refs/status/diff/bundle, per-file hashes with sizes/mtimes/modes, authored-tree fingerprint, server PID/start, runtime versions, Ollama model digests, `pip freeze`, launchd plist, `.env` names + hash.
* Strongly recommended with it: B2 (`interaction_log`, `reflection_*`, `council_deliberations`, `SELF_EDIT.log`, `optuna.db`, …). B3 (the rest of `memory/` and `data/`, including the old `memory_meta_backup_*` files) is copied too — nothing is excluded for size.

**(2) The safest first destination.** An **attached external disk** (APFS, ≥ 5 GB free, `Device Location: External`), then unplugged; whether the operator has one is UNKNOWN (none is mounted). If none exists today, take the **TEMPORARY-SAME-SSD** generation anyway — it defeats logical corruption and bad restarts, the most probable near-term threats — and treat it as incomplete protection until an off-device copy (external disk or the Intel Air after its read-only pre-inspection) exists.

**(3) The exact minimum-today backup sequence.** §19: precheck → tools → destination confirmation → `fe_stage_precheck`/`fe_stage_dest` → `fe_stage_source_identity` (bundle first) → `fe_stage_lists` → `fe_stage_copy_B` (B1 first) → `fe_stage_copy_A` → `fe_stage_after_state` → `fe_stage_judge` → `sync` → `fe_stage_cold_verify` → `fe_stage_validate` → `fe_stage_judge` → `fe_stage_label` → (`fe_stage_replicate` when a second device exists). Command-level detail: §17 and Appendices A–F.

**(4) How to prove the copy is good.** Four independent proofs, in increasing strength: (i) per-file source-before/source-after/destination SHA-256 with the category predicate; (ii) the sorted manifest re-hashed after `sync` (`COLD VERIFY PASS`) and again after unmount/replug; (iii) structural validation of the *copy* in a no-write jail (pickle streams complete, JSON/JSONL parse, SQLite integrity, FAISS `ntotal` = metadata count, size/count floors); (iv) a restore drill that rebuilds the tree in a scratch directory, matches the manifest, recovers Git via both the restored `.git` and the bundle, and re-validates. Only (iv) earns `RESTORE-TESTED`; until then the honest label is at most `VERIFIED-LIVE`.

**(5) What a backup still does NOT protect against.**
* **Physical loss of everything on one device**, and — for the same-SSD generation — any failure of that SSD; theft/fire/water when the copies sit together.
* **Semantic corruption that is structurally valid** (e.g. a plausible-looking but wrong `river_brain.pkl`, wrong FAISS vectors, a garden silently shortened by the audit's lost-update bug): hashes prove the copy equals the source; validators prove loadability, not correctness.
* **Not a point-in-time snapshot** while the server runs: a `VERIFIED-LIVE` generation can still contain a pair caught between a meta write and an index write in a way the count check does not reveal (INFERRED possibility).
* **Everything written after the backup** (RiverBrain learns ≈1.2 k observations/day; the garden changes every few minutes); **the writers' own hazards** — the backup does not fix the non-atomic pickles, the FAISS/meta pair, or the corrupt→empty→overwrite path.
* **Secrets exposure:** every generation contains `.env`; a stolen drive is a credential leak unless encrypted.
* **Items outside the tree:** Ollama weights (registry dependence; a 12-month-old base model digest may not be servable), the HF embedding cache, `~/.ssh`/Tailscale identity, the Air's own instance state.
* **Operator/host compromise, ransomware while a drive stays attached, a wrong destination confirmed by a human.**
* **Untested procedures:** the external-drive, Intel, SSH, exFAT and APFS-snapshot paths, and anything on the real full-size tree, until rehearsed.

**(6) What must happen before FeralEcho can safely resume higher-risk experimentation.** (a) At least one generation labelled `COMPLETE-VERIFIED-LIVE` **on storage other than the M5 SSD**, and a second verified copy on a *third* physically distinct device, at least one off the M5 (the §11 rule, as a working precondition); (b) a **passed restore drill** (`RESTORE-TESTED`) from the off-SSD copy; (c) a *second, later* generation made by the same procedure (repeatability; comparison of counts between the two); (d) a decision by the operator, separately and explicitly, on the preservation fixes ranked in the preservation audit §13 — at least the atomic-write helper (P1) and the refuse-to-overwrite-after-failed-load guard (P2) for RiverBrain, classifier and garden — because backups shrink the loss window but do not remove the corruption hazard; (e) an agreed cadence (daily plus before/after any risky operation) and a named owner; (f) the standing prohibitions stay in force until (a)–(c) hold: no casual restart or `kill -9`, no ad-hoc import of production state, no deletion of old artifacts. The persistent-competence experiment remains under its **HOLD**; lifting it is a separate decision this plan does not make.

**STOP. Nothing has been backed up. The next step requires explicit operator approval of the destination and runbook.**

---

## 21. Integrity record
### 21.1 Before / after (all read-only observations)
| Item | Before | After | Same? |
|---|---|---|---|
| Git HEAD | `2fba42644c82b9f7096276f4dd338d615cf1bcce` | `2fba42644c82b9f7096276f4dd338d615cf1bcce` | **yes** |
| `git status --porcelain` (default mode) | 186 paths | 188 paths | the diff of the two status listings is exactly **two added lines**: `?? audits/2026-09-20_feralecho_backup_manifest_schema.json` and `?? audits/2026-09-20_feralecho_verified_backup_and_recovery_plan.md` — this mission's two deliverables. No pre-existing path changed state |
| Server | PID 29288, start Sun Sep 20 07:30:10 2026 | PID 29288, start Sun Sep 20 07:30:10 2026 | **yes** — not restarted, not signalled |
| Frozen protocol v1.0 md / json | `d1968caf…8c06` / `b35ad16b…8131` | identical | **yes** |
| Frozen protocol v1.1 md / json | `e39e6238…f0ac` / `f27a4127…4396` | identical | **yes** |
| v1→v1.1 traceability (`audits/2026-09-20_persistent_competence_v1_to_v1_1_traceability.md`) | `493600f4d137…c594` | identical | **yes** |
| `.git/index.lock`, stash entries | none, 0 | none, 0 | yes |
| Manifest schema file sha256 (final) | — | `e1e88f6a022eb9aa8ad4f3026beb8eb4c1670cac10c636c2ddcace035c4641a3` | — |

### 21.2 Confirmations
* **No production source or persistent state was modified.** Files written inside the repository: exactly the two deliverables above. Files written elsewhere: only the session scratchpad (`/private/tmp/claude-501/…/scratchpad`): the tool drafts, a synthetic fixture repository with its own throw-away `git init`, its synthetic "destination" and "replica" directories, restore-drill directories, and status snapshots. No `FeralEcho_backups/`, `fe_backup_tools/` or `fe_restore_drill_*` directory exists in `$HOME` or the repo (checked); `/Volumes` shows only `Macintosh HD` and `Recovery`.
* **No backup was created, no file was transferred.** Nothing in this mission read the *contents* of production state files for backup purposes; production files were only `stat`-ed (sizes/mtimes), listed, and counted. **No network use**: the only network-adjacent call was `ollama list` against the local Ollama server on loopback; nothing was discovered, probed, or contacted on the tailnet or the internet.
* **No Git mutation.** Read-only Git commands (`rev-parse`, `status`, `for-each-ref`, `rev-list`, `ls-files`, `worktree`/`stash list`, `grep` on `.git/config` for a *count* of credential-shaped URLs = 0) were run with `GIT_OPTIONAL_LOCKS=0` so that no index refresh occurred. All Git write-type commands appear only against the synthetic fixture inside the scratchpad, never against the FeralEcho repository.
* `backup_feral_echo.sh` was not run; no synchronization software was used; the frozen protocol files were not opened for writing.

### 21.3 Disclosures (things a reviewer should know, stated plainly)
1. One command in this session, `mkdir -p /dev/null`, was typed by mistake inside a compound read-only diagnostic; it failed ("File exists") and had no effect.
2. The **synthetic fixture tests** used `rm -rf` on fixture/destination directories that I had created in the scratchpad (never on repository or home paths). The **runbook itself contains no `rm`** (machine-checked in §18).
3. The synthetic runs of `fe_stage_source_identity` read real host facts (the real `~/Library/LaunchAgents/com.gremlin.echo.plist`, the real interpreter's `pip freeze`, `ollama list`) and wrote copies into scratchpad fixture directories. Those are read-only against production; they mean the scratchpad holds a copy of the plist and a package list.
4. **Two tooling bugs were found by testing, not by review, and fixed before this file was generated:** `fe_copy_one` used a variable named `status` (read-only in zsh; renamed `vstat`); `diskutil info <subdirectory>` fails ("Could not find disk"), so the tools now resolve the device node with `df` first. Earlier draft behaviours also corrected: a whole-generation QUARANTINE for a single non-core mutated log (now tiered), a drill path-count false alarm from the excluded cache files, an in-place re-judge of a finished generation (now refused), and hostnames failing to identify the machine (now an explicit `FE_HOST_TAG`).
5. **The first version of the §18 lint was blind:** it scanned the template before the tool sources were substituted and reported zero hits for everything, including patterns known to exist. It now scans the final text, reports how many blocks/lines it scanned, and **fails the generation if positive controls (`mv`, `git bundle create`, `git clone`, `mkdir -p`) are not found**. A lint that reports "0" without proof it can see is exactly the kind of false assurance this project warns about.
6. **Paste-fidelity of the appendices** was checked mechanically after generation: the five appendix blocks were extracted from this very file, executed in a fresh bash into a new directory, and all six resulting files matched the SHA-256 table of Appendix F (6/6 `OK`). The final tool versions were then re-run end to end on the synthetic fixture (clean run → VERIFIED-LIVE → restore drill PASS → replica PASS); those hashes are the ones in Appendix F.
7. `git status --porcelain` was 186 at the start of this and the preceding mission; `--untracked-files=all` gives 249 (27 modified + 221 untracked + 1 deliverable at the time of that count). The plan uses the default-mode figure for continuity and records the `all` figure in `kv.env`.

### 21.4 Residual uncertainty (UNKNOWN / UNTESTED — none of these is claimed)
The behaviour of the tools on the real 22,761-file tree and the real running server; real persist durations for the FAISS pair (the collision estimate is INFERRED); whether an external disk exists; whether the Intel Air is reachable/healthy/has space and Remote Login; any exFAT/NTFS/Intel/SSH behaviour; whether `cp` clones on APFS by default; `tmutil localsnapshot` on this machine; whether the Ollama registry still serves the base-model digest; whether the linked worktree matters beyond its files (it has 0 unique commits); the semantic correctness of any state file (only structure and internal count alignment are checked).


---

## Appendix A — `fe_lib.sh` (paste as one block)
```bash
cat > "$FE_TOOLS_DIR/fe_lib.sh" <<'FE_EOF'
# fe_lib.sh -- FeralEcho backup helpers. bash 3.2+ (macOS /bin/bash). SOURCE this; do not execute.
# Requires exported: FE_SRC (source repo root), FE_GEN (existing generation dir), FE_MAX_ATTEMPTS (default 3).
# Guarantees by construction: never writes under $FE_SRC; never deletes anything; never overwrites an
# existing destination file (failed attempts are MOVED inside $FE_GEN/work/failed, kept as evidence).
: "${FE_MAX_ATTEMPTS:=3}"
# Append-only files: growth during the copy is legitimate. Everything NOT listed is treated as
# REWRITE (strict: the copy must equal a complete pre- or post-copy version of the source).
: "${FE_APPEND_SET:= ./memory/interaction_log.jsonl ./memory/reflection_shard.jsonl ./memory/reflection_journal.jsonl ./memory/council_deliberations.jsonl ./memory/SELF_EDIT.log ./memory/SELF_EDIT_MASTERY_.log ./memory/self_model_claims.jsonl ./memory/workspace_log.jsonl ./memory/seam_log.jsonl ./memory/dream_bridge.log ./memory/quarantine_journal.jsonl ./memory/echo_watchdog.log ./memory/validator_audit.log ./memory/dissent_log.jsonl ./WhisperingWires/thoughts.log ./WhisperingWires/harmony.log }"
fe_devnode() { df "$1" | awk 'NR==2{print $1}'; }   # device node behind any path (diskutil info wants a device or mount point)
fe_sha()  { shasum -a 256 < "$1" | awk '{print $1}'; }
fe_size() { stat -f %z "$1"; }
fe_type_of() { case "$FE_APPEND_SET" in *" $1 "*) echo APPEND ;; *) echo REWRITE ;; esac; }

# fe_copy_one <rel path starting ./> <tier label>   -> appends one row per attempt to manifest/copyrec.tsv
# return 0 = verified copy in place; 3 = kept but LIVE-MUTATED-DURING-BACKUP; 1/2 = error (nothing accepted)
fe_copy_one() {
  local rel="$1" tier="$2" s d type attempt pre post dst pfx spre spost sdst vstat rec
  s="$FE_SRC/$rel"; d="$FE_GEN/tree/$rel"; type=$(fe_type_of "$rel"); rec="$FE_GEN/manifest/copyrec.tsv"
  { [ -f "$s" ] && [ ! -L "$s" ]; } || { echo "REFUSE: not a regular file: $rel" >&2; return 2; }
  if [ -e "$d" ]; then
    if [ "${FE_REPLACE_EXISTING:-0}" = 1 ]; then   # retry path: move (never delete) the old copy aside
      mkdir -p "$FE_GEN/work/failed/pre-retry/$(dirname "$rel")" && mv "$d" "$FE_GEN/work/failed/pre-retry/$rel" || return 2
    else echo "REFUSE: destination exists: $rel" >&2; return 2; fi
  fi
  mkdir -p "$(dirname "$d")" || return 2
  attempt=1
  while :; do
    spre=$(fe_size "$s"); pre=$(fe_sha "$s")
    cp -p "$s" "$d" || { echo "COPY-ERROR: $rel" >&2; return 1; }
    post=$(fe_sha "$s"); spost=$(fe_size "$s")
    dst=$(fe_sha "$d"); sdst=$(fe_size "$d"); pfx=""
    if [ "$type" = APPEND ]; then
      pfx=$(head -c "$sdst" "$s" | shasum -a 256 | awk '{print $1}')      # first N bytes of the source as it is NOW
      if [ "$dst" = "$pfx" ] && [ "$spost" -ge "$sdst" ]; then
        if [ "$dst" = "$pre" ] && [ "$pre" = "$post" ]; then vstat=VERIFIED-STABLE; else vstat=VERIFIED-APPEND-PREFIX; fi
      else vstat=MISMATCH; fi
    else
      if   [ "$dst" = "$pre" ] && [ "$pre" = "$post" ]; then vstat=VERIFIED-STABLE
      elif [ "$dst" = "$pre" ] || [ "$dst" = "$post" ]; then vstat=VERIFIED-LIVE-VERSION
      else vstat=MISMATCH; fi
    fi
    if [ "$vstat" = MISMATCH ] && [ "$attempt" -ge "$FE_MAX_ATTEMPTS" ]; then vstat=LIVE-MUTATED-DURING-BACKUP; fi
    printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$rel" "$tier" "$type" "$attempt" "$pre" "$post" "$dst" "$pfx" "$spre" "$spost" "$sdst" "$vstat" >> "$rec"
    case "$vstat" in
      MISMATCH) mkdir -p "$FE_GEN/work/failed/attempt$attempt/$(dirname "$rel")" && mv "$d" "$FE_GEN/work/failed/attempt$attempt/$rel" || return 2
                attempt=$((attempt + 1)) ;;
      LIVE-MUTATED-DURING-BACKUP) return 3 ;;
      *) return 0 ;;
    esac
  done
}

# fe_copy_list <listfile (newline-separated ./rel paths)> <tier> : copy every file, tally, print any non-verified
fe_copy_list() {
  local rel n=0 bad=0 rc
  while IFS= read -r rel; do
    [ -n "$rel" ] || continue
    fe_copy_one "$rel" "$2"; rc=$?
    n=$((n + 1)); [ "$rc" -eq 0 ] || { bad=$((bad + 1)); echo "  NOT-VERIFIED(rc=$rc): $rel"; }
  done < "$1"
  echo "fe_copy_list: tier=$2 files=$n not_verified=$bad"; [ "$bad" -eq 0 ]
}

# fe_hash_list <root> <listfile> <outfile> : "sha256  ./rel" for every file in the list, list order preserved
fe_hash_list() { ( cd "$1" && tr '\n' '\0' < "$2" | xargs -0 shasum -a 256 ) > "$3"; }
FE_EOF
```

## Appendix B — `fe_stages.sh` (paste as one block)
```bash
cat > "$FE_TOOLS_DIR/fe_stages.sh" <<'FE_EOF'
# fe_stages.sh -- runbook stages as bash functions (bash 3.2+). SOURCE after fe_lib.sh. Each stage returns non-zero
# and prints "STOP:" on failure; the operator must not continue past a STOP. No stage deletes or overwrites anything.
set -o pipefail
export GIT_OPTIONAL_LOCKS=0   # git must never refresh the index or take optional locks in the source repo
FE_JAIL='(version 1)(allow default)(deny file-write*)(deny network*)(allow file-write* (literal "/dev/null") (literal "/dev/dtracehelper"))'

fe_stage_show() {   # RUN ON M5. Prints every variable that decides where bytes go. Writes nothing.
  : "${FE_SRC:?FE_SRC not set}" "${FE_DEST_ROOT:?FE_DEST_ROOT not set}" "${FE_DEST_CLASS:?FE_DEST_CLASS not set}"
  FE_UTC=${FE_UTC:-$(date -u +%Y%m%dT%H%M%SZ)}; FE_LABEL=${FE_LABEL:-RESCUE1}
  : "${FE_HOST_TAG:?set FE_HOST_TAG to M5 or INTEL (hostnames do not distinguish the two machines)}"
  FE_HOST=$(scutil --get LocalHostName 2>/dev/null || hostname -s)
  FE_GEN_ID="gen-$FE_UTC-$FE_LABEL-$FE_HOST_TAG"; FE_GEN="$FE_DEST_ROOT/FeralEcho_backups/$FE_GEN_ID"
  export FE_UTC FE_LABEL FE_HOST FE_HOST_TAG FE_GEN_ID FE_GEN
  echo "FE_SRC        = $FE_SRC"; echo "FE_DEST_ROOT  = $FE_DEST_ROOT"; echo "FE_DEST_CLASS = $FE_DEST_CLASS"
  echo "FE_GEN_ID     = $FE_GEN_ID"; echo "FE_GEN        = $FE_GEN"
  [ -e "$FE_GEN" ] && { echo "STOP: generation path already exists"; return 1; }
  echo "To authorise writing, type exactly:  export FE_CONFIRMED=YES-WRITE-TO-$FE_GEN_ID"
}

fe_stage_precheck() {   # RUN ON M5. Read-only against the source and destination.
  : "${FE_GEN:?run fe_stage_show first}"
  case "$FE_DEST_CLASS" in BEST-EXTERNAL|BEST-OTHER-MACHINE|GOOD-AIR|TEMPORARY-SAME-SSD) ;; *) echo "STOP: FE_DEST_CLASS invalid"; return 1 ;; esac
  [ -d "$FE_SRC/.git" ] || { echo "STOP: FE_SRC is not a git working tree root"; return 1; }
  { [ -d "$FE_DEST_ROOT" ] && [ -w "$FE_DEST_ROOT" ]; } || { echo "STOP: FE_DEST_ROOT missing or not writable"; return 1; }
  case "$FE_DEST_ROOT/" in "$FE_SRC"/*) echo "STOP: destination is inside the source tree"; return 1 ;; esac
  case "$FE_SRC/" in "$FE_DEST_ROOT"/*) echo "STOP: source is inside the destination"; return 1 ;; esac
  local g; for g in index.lock MERGE_HEAD CHERRY_PICK_HEAD REVERT_HEAD rebase-merge rebase-apply BISECT_LOG; do
    [ -e "$FE_SRC/.git/$g" ] && { echo "STOP: git operation in progress ($g)"; return 1; }; done
  local badn syml
  badn=$(cd "$FE_SRC" && find . \( -name __pycache__ -o -name .pytest_cache \) -prune -o -name '*[[:cntrl:]\\]*' -print | head -3)
  [ -z "$badn" ] || { echo "STOP: path with control character or backslash: $badn"; return 1; }
  syml=$(cd "$FE_SRC" && find . \( -name __pycache__ -o -name .pytest_cache \) -prune -o -type l -print | head -3)
  [ -z "$syml" ] || { echo "STOP: symlinks in scope (plan assumes none): $syml"; return 1; }
  local need avail; need=$(du -sk "$FE_SRC" | awk '{print $1}'); avail=$(df -k "$FE_DEST_ROOT" | awk 'NR==2{print $4}')
  echo "source KB=$need  destination available KB=$avail"
  [ "$avail" -ge $((need * 2)) ] || { echo "STOP: destination free space < 2x source size"; return 1; }
  FE_SAMEDEV=UNKNOWN
  if [ "$(stat -f %d "$FE_SRC")" = "$(stat -f %d "$FE_DEST_ROOT")" ]; then FE_SAMEDEV=SAME-VOLUME; fi
  export FE_SAMEDEV; echo "same-volume test: $FE_SAMEDEV"
  case "$FE_DEST_CLASS" in TEMPORARY-SAME-SSD) ;; *) [ "$FE_SAMEDEV" != SAME-VOLUME ] || { echo "STOP: class says separate storage but volumes match"; return 1; } ;; esac
  local t; for t in shasum tar cp head stat find xargs sort comm awk sync; do command -v "$t" >/dev/null || { echo "STOP: missing tool $t"; return 1; }; done
  [ -x "${FE_PY:-}" ] || { echo "STOP: FE_PY must be an absolute path to a python3 interpreter (not the Xcode shim)"; return 1; }
  "$FE_PY" -I -c 'import sys;assert sys.version_info>=(3,9)' || return 1
  echo "PRECHECK PASS"
}

fe_stage_dest() {   # RUN ON M5. First stage that writes (destination only).
  [ "${FE_CONFIRMED:-}" = "YES-WRITE-TO-$FE_GEN_ID" ] || { echo "STOP: FE_CONFIRMED not set to the exact confirmation string"; return 1; }
  mkdir -p "$FE_DEST_ROOT/FeralEcho_backups" || return 1
  mkdir "$FE_GEN" || { echo "STOP: mkdir refused (generation exists or path invalid)"; return 1; }   # plain mkdir: fails if it exists
  mkdir "$FE_GEN/manifest" "$FE_GEN/tree" "$FE_GEN/work" "$FE_GEN/identity" "$FE_GEN/git" "$FE_GEN/tools" || return 1
  cp -p "$FE_TOOLS_DIR/fe_lib.sh" "$FE_TOOLS_DIR/fe_stages.sh" "$FE_TOOLS_DIR/fe_judge.py" "$FE_TOOLS_DIR/fe_validate.py" "$FE_GEN/tools/" || return 1
  { df -k "$FE_DEST_ROOT"; diskutil info "$(fe_devnode "$FE_DEST_ROOT")" 2>&1; ls -la "$FE_DEST_ROOT" 2>&1 | head -50; } > "$FE_GEN/identity/destination.txt"
  FE_CREATED_UTC=$(date -u +%Y-%m-%dT%H:%M:%SZ); export FE_CREATED_UTC
  echo "generation directory created: $FE_GEN"
}

fe_stage_source_identity() {   # RUN ON M5. Read-only against the source. Class C evidence + kv.env + before-state.
  local m="$FE_GEN/manifest" i="$FE_GEN/identity"
  ( cd "$FE_SRC" && export GIT_OPTIONAL_LOCKS=0
    git rev-parse HEAD > "$i/git_head.txt"; git symbolic-ref -q HEAD > "$i/git_branch.txt" || echo DETACHED > "$i/git_branch.txt"
    git for-each-ref --format='%(objectname) %(refname)' > "$i/git_refs.txt"
    git status --porcelain=v2 --branch --untracked-files=all > "$i/git_status_v2.txt"
    git worktree list --porcelain > "$i/git_worktrees.txt"; git stash list > "$i/git_stash.txt"
    git ls-files -o --exclude-standard > "$i/git_untracked_nonignored.txt"; git ls-files -o -i --exclude-standard --directory > "$i/git_ignored.txt"
    git rev-list --count '@{u}..HEAD' > "$i/git_unpushed_count.txt" 2>/dev/null || echo UNKNOWN > "$i/git_unpushed_count.txt"
    git diff HEAD --binary > "$i/git_diff_HEAD.patch"; git diff HEAD --stat > "$i/git_diff_HEAD.stat"
  ) || return 1
  ( cd "$FE_SRC" && git bundle create "$FE_GEN/git/repo.bundle" --all ) || { echo "STOP: git bundle failed"; return 1; }   # writes only the bundle file
  ( cd "$FE_SRC" && git bundle verify "$FE_GEN/git/repo.bundle" ) > "$i/git_bundle_verify.txt" 2>&1 || { echo "STOP: bundle did not verify"; return 1; }
  local pid; pid=$(cat "$FE_SRC/memory/echo_server.pid" 2>/dev/null || true)
  if [ -n "$pid" ] && ps -p "$pid" >/dev/null 2>&1; then SRV_PID_BEFORE=$pid; SRV_START_BEFORE=$(ps -o lstart= -p "$pid"); else SRV_PID_BEFORE=none; SRV_START_BEFORE=none; fi
  export SRV_PID_BEFORE SRV_START_BEFORE
  "$FE_PY" -m pip freeze > "$i/pip_freeze.txt" 2>/dev/null
  [ -f "$HOME/Library/LaunchAgents/com.gremlin.echo.plist" ] && cp -p "$HOME/Library/LaunchAgents/com.gremlin.echo.plist" "$i/com.gremlin.echo.plist"
  { echo "pid=$SRV_PID_BEFORE start=$SRV_START_BEFORE"; sw_vers; uname -a; "$FE_PY" --version; echo "pip_freeze_sha256=$(shasum -a 256 < "$i/pip_freeze.txt" | awk '{print $1}')"
    ollama list 2>&1; curl -s --max-time 5 http://127.0.0.1:11434/api/tags 2>&1 | head -c 4000; } > "$i/runtime.txt" 2>&1
  { [ -f "$FE_SRC/.env" ] && { sed -E 's/=.*//;/^[[:space:]]*(#|$)/d' "$FE_SRC/.env"; shasum -a 256 "$FE_SRC/.env"; }; } > "$i/env_names_and_hash.txt" 2>/dev/null   # NAMES and one hash, never values
  { printf 'FE_GEN_ID=%s\nFE_LABEL=%s\nFE_CREATED_UTC=%s\nFE_SRC=%s\nFE_DEST_CLASS=%s\nFE_DEST_ROOT=%s\nSAMEDEV=%s\n' "$FE_GEN_ID" "$FE_LABEL" "$FE_CREATED_UTC" "$FE_SRC" "$FE_DEST_CLASS" "$FE_DEST_ROOT" "$FE_SAMEDEV"
    printf 'HOST=%s (tag %s, %s)\nOSVER=%s\nARCH=%s\n' "$FE_HOST" "$FE_HOST_TAG" "$(sysctl -n hw.model 2>/dev/null)" "$(sw_vers -productVersion 2>/dev/null)" "$(uname -m)"
    printf 'HEAD=%s\nBRANCH=%s\nPORCELAIN=%s\nUNPUSHED=%s\n' "$(cat "$i/git_head.txt")" "$(cat "$i/git_branch.txt")" "$(grep -c '^[12u?] ' "$i/git_status_v2.txt")" "$(cat "$i/git_unpushed_count.txt")"
    printf 'SRV_PID_BEFORE=%s\nSRV_START_BEFORE=%s\nLEGACY_FP=%s\n' "$SRV_PID_BEFORE" "$SRV_START_BEFORE" "8e6808dc64fbebe52523a4b71369768af191675df2c17f88ae6cb6ff76b5f844"
    printf 'TOOL_TAR=%s\nTOOL_SHASUM=%s\nTOOL_PYTHON=%s\n' "$(tar --version | head -1)" "$(shasum --version | head -1)" "$("$FE_PY" --version 2>&1)"
    printf 'FS=%s\nVOL_UUID=%s\nDEV_LOC=%s\nFREE_BYTES=%s\n' "$(diskutil info "$(fe_devnode "$FE_DEST_ROOT")" 2>/dev/null | awk -F': +' '/File System Personality|Type \(Bundle\)/{print $2; exit}')" \
      "$(diskutil info "$(fe_devnode "$FE_DEST_ROOT")" 2>/dev/null | awk -F': +' '/Volume UUID/{print $2; exit}')" "$(diskutil info "$(fe_devnode "$FE_DEST_ROOT")" 2>/dev/null | awk -F': +' '/Device Location/{print $2; exit}')" \
      "$(df -k "$FE_DEST_ROOT" | awk 'NR==2{print $4*1024}')"; } > "$m/kv.env"
  echo "source identity captured; server before: pid=$SRV_PID_BEFORE start=$SRV_START_BEFORE"
}

fe_stage_lists() {   # RUN ON M5. Read-only against the source. Builds and checks the partition of every in-scope file.
  local m="$FE_GEN/manifest"; : "${FE_B1_LIST:?}" "${FE_B2_LIST:?}"
  ( cd "$FE_SRC" && find . \( -name __pycache__ -o -name .pytest_cache \) -prune -o \( -type f -o -type l \) ! -name .DS_Store -print | LC_ALL=C sort ) > "$m/all.lst" || return 1
  grep -v -e '^\./memory/' -e '^\./data/' "$m/all.lst" > "$m/A.lst"
  grep    -e '^\./memory/' -e '^\./data/' "$m/all.lst" > "$m/B.lst"
  LC_ALL=C sort "$FE_B1_LIST" > "$m/B1.lst"; LC_ALL=C sort "$FE_B2_LIST" > "$m/B2.lst"
  [ -z "$(LC_ALL=C comm -23 "$m/B1.lst" "$m/B.lst")" ] || { echo "STOP: a B1 file is missing from the source: $(LC_ALL=C comm -23 "$m/B1.lst" "$m/B.lst")"; return 1; }
  [ -z "$(LC_ALL=C comm -23 "$m/B2.lst" "$m/B.lst")" ] || { echo "STOP: a B2 file is missing from the source: $(LC_ALL=C comm -23 "$m/B2.lst" "$m/B.lst")"; return 1; }
  [ -z "$(LC_ALL=C comm -12 "$m/B1.lst" "$m/B2.lst")" ] || { echo "STOP: B1 and B2 overlap"; return 1; }
  LC_ALL=C sort "$m/B1.lst" "$m/B2.lst" > "$m/B12.lst"; LC_ALL=C comm -23 "$m/B.lst" "$m/B12.lst" > "$m/B3.lst"
  ( cd "$FE_SRC" && tr '\n' '\0' < "$m/all.lst" | xargs -0 stat -f '%N%t%z%t%m%t%Lp' ) > "$m/stat.tsv" || return 1
  printf 'all=%s A=%s B1=%s B2=%s B3=%s\n' "$(wc -l < "$m/all.lst")" "$(wc -l < "$m/A.lst")" "$(wc -l < "$m/B1.lst")" "$(wc -l < "$m/B2.lst")" "$(wc -l < "$m/B3.lst")"
  echo "LISTS PASS"
}

fe_stage_copy_A() {   # RUN ON M5. Bulk tar stream of the non-state tree (source read-only). Hash lists taken before/after/at destination.
  local m="$FE_GEN/manifest"
  fe_hash_list "$FE_SRC" "$m/A.lst" "$m/A.pre.sha256" || return 1
  tr '\n' '\0' < "$m/A.lst" > "$m/A.lst0"
  ( cd "$FE_SRC" && tar -cf - --null -T "$m/A.lst0" ) | ( cd "$FE_GEN/tree" && tar -xpkf - ) || { echo "STOP: tar pipeline failed"; return 1; }
  fe_hash_list "$FE_SRC" "$m/A.lst" "$m/A.post.sha256" || return 1
  fe_hash_list "$FE_GEN/tree" "$m/A.lst" "$m/A.dest.sha256" || { echo "STOP: destination hashing failed (missing file?)"; return 1; }
  echo "copy A done: $(wc -l < "$m/A.lst") files"
}

fe_stage_copy_B() {   # RUN ON M5. Per-file copy with before/after source hash + destination hash and bounded retry.
  local m="$FE_GEN/manifest" rc=0
  [ -e "$m/copyrec.tsv" ] || : > "$m/copyrec.tsv"
  fe_copy_list "$m/B1.lst" B1 || rc=1
  fe_copy_list "$m/B2.lst" B2 || rc=1
  fe_copy_list "$m/B3.lst" B3 || rc=1
  return $rc   # non-zero only means: some file is not VERIFIED (see NOT-VERIFIED lines); the judge decides the label
}

fe_stage_judge() {   # RUN ON M5 (reads only $FE_GEN, writes manifest files). Repeatable.
  local m="$FE_GEN/manifest" rc
  ( cd "$FE_GEN/tree" && find . -type f | LC_ALL=C sort ) > "$m/dest.lst"
  "$FE_PY" -I "$FE_GEN/tools/fe_judge.py" "$FE_GEN"; rc=$?
  if [ "$rc" -eq 3 ]; then   # A-part files whose bulk copy did not verify: retry each file individually
    local rel; while IFS= read -r rel; do FE_REPLACE_EXISTING=1 fe_copy_one "$rel" A; done < "$m/retry.lst"
    ( cd "$FE_GEN/tree" && find . -type f | LC_ALL=C sort ) > "$m/dest.lst"
    "$FE_PY" -I "$FE_GEN/tools/fe_judge.py" "$FE_GEN"; rc=$?
  fi
  return $rc
}

fe_stage_validate() {   # RUN ON M5. Reads ONLY the destination copy, inside a no-write, no-network jail. Imports no FeralEcho code.
  PYTHONDONTWRITEBYTECODE=1 sandbox-exec -p "$FE_JAIL" "$FE_PY" -I "$FE_GEN/tools/fe_validate.py" "$FE_GEN/tree" ${FE_VALIDATE_ARGS:-} > "$FE_GEN/manifest/validation.json"
  local rc=$?; grep -E '"(passed|pair_aligned)"' "$FE_GEN/manifest/validation.json"; return $rc
}

fe_stage_after_state() {   # RUN ON M5. Read-only.
  local pid; pid=$(cat "$FE_SRC/memory/echo_server.pid" 2>/dev/null || true)
  if [ -n "$pid" ] && ps -p "$pid" >/dev/null 2>&1; then SRV_PID_AFTER=$pid; SRV_START_AFTER=$(ps -o lstart= -p "$pid"); else SRV_PID_AFTER=none; SRV_START_AFTER=none; fi
  printf 'SRV_PID_AFTER=%s\nSRV_START_AFTER=%s\n' "$SRV_PID_AFTER" "$SRV_START_AFTER" >> "$FE_GEN/manifest/kv.env"
  ( cd "$FE_SRC" && GIT_OPTIONAL_LOCKS=0 git rev-parse HEAD ) | diff - "$FE_GEN/identity/git_head.txt" >/dev/null || echo "ANOMALY: git HEAD changed during backup"
  ( cd "$FE_SRC" && find . \( -name __pycache__ -o -name .pytest_cache \) -prune -o \( -type f -o -type l \) ! -name .DS_Store -print | LC_ALL=C sort ) > "$FE_GEN/manifest/all.post.lst"
  LC_ALL=C comm -13 "$FE_GEN/manifest/all.lst" "$FE_GEN/manifest/all.post.lst" > "$FE_GEN/manifest/created_during.lst"
  LC_ALL=C comm -23 "$FE_GEN/manifest/all.lst" "$FE_GEN/manifest/all.post.lst" > "$FE_GEN/manifest/vanished_during.lst"
  echo "scope drift: created=$(wc -l < "$FE_GEN/manifest/created_during.lst") vanished=$(wc -l < "$FE_GEN/manifest/vanished_during.lst")"
  echo "server after: pid=$SRV_PID_AFTER start=$SRV_START_AFTER"
}

fe_stage_cold_verify() {   # RUN ON M5 or INTEL. Re-hash every destination file against the manifest. Repeat after unmount/remount.
  local bad n=0
  bad=$( cd "$FE_GEN/tree" && shasum -a 256 -c ../manifest/final.sha256 2>&1 | grep -v ': OK$' | head -20 )
  if [ -f "$FE_GEN/SEAL.sha256" ]; then bad="$bad$( cd "$FE_GEN" && shasum -a 256 -c SEAL.sha256 2>&1 | grep -v ': OK$' | head -20 )"; fi
  [ -z "$bad" ] && echo "COLD VERIFY PASS: $(wc -l < "$FE_GEN/manifest/final.sha256") tree files$( [ -f "$FE_GEN/SEAL.sha256" ] && echo " + $(wc -l < "$FE_GEN/SEAL.sha256") sealed non-tree files")" || { echo "COLD VERIFY FAIL:"; echo "$bad"; return 1; }
}

fe_stage_label() {   # RUN ON M5. Writes the marker and the append-only registry line. Marker names cannot be confused.
  local lvl; lvl=$("$FE_PY" -I -c 'import json,sys;print(json.load(open(sys.argv[1]))["consistency_level"])' "$FE_GEN/GENERATION.json") || return 1
  ( cd "$FE_GEN" && shasum -a 256 GENERATION.json > GENERATION.json.sha256 ) || return 1
  ( cd "$FE_GEN" && find . \( -path ./tree -o -name SEAL.sha256 \) -prune -o -type f -print0 | LC_ALL=C sort -z | xargs -0 shasum -a 256 ) > "$FE_GEN/SEAL.sha256" || return 1
  if [ "$lvl" = QUARANTINED ]; then : > "$FE_GEN/QUARANTINED-NOT-KNOWN-GOOD"; else : > "$FE_GEN/COMPLETE-$lvl"; fi
  printf '%s\t%s\t%s\t%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$FE_GEN_ID" "$lvl" "$(awk '{print $1}' "$FE_GEN/GENERATION.json.sha256")" >> "$FE_DEST_ROOT/FeralEcho_backups/generations.log"
  echo "generation $FE_GEN_ID labelled: $lvl"
}

fe_stage_drill() {   # RUN ON M5 (or INTEL). Restore drill: rebuilds a generation into a NEW directory; never touches production.
  : "${FE_GEN:?}" "${FE_DRILL_DIR:?FE_DRILL_DIR must be a path that does not exist yet}" "${FE_PY:?}"
  [ ! -e "$FE_DRILL_DIR" ] || { echo "STOP: FE_DRILL_DIR exists"; return 1; }
  case "$FE_DRILL_DIR/" in "${FE_SRC:-/nonexistent}"/*) echo "STOP: drill dir is inside the production tree"; return 1 ;; esac
  ls "$FE_GEN"/COMPLETE-* >/dev/null 2>&1 || { echo "STOP: generation is not COMPLETE-* (QUARANTINED generations are not drill candidates)"; return 1; }
  fe_stage_cold_verify || return 1
  mkdir "$FE_DRILL_DIR" || return 1
  ( cd "$FE_GEN/tree" && tar -cf - . ) | ( cd "$FE_DRILL_DIR" && tar -xpkf - ) || { echo "STOP: restore copy failed"; return 1; }
  local bad; bad=$( cd "$FE_DRILL_DIR" && shasum -a 256 -c "$FE_GEN/manifest/final.sha256" 2>&1 | grep -v ': OK$' | head -5 )
  [ -z "$bad" ] || { echo "DRILL FAIL: restored tree does not match manifest: $bad"; return 1; }
  # Git recoverability, two independent ways. Neither runs inside .claude/worktrees/* (its .git file points at the ORIGINAL repo).
  local want got; want=$(cat "$FE_GEN/identity/git_head.txt")
  got=$(git -C "$FE_DRILL_DIR" rev-parse HEAD 2>/dev/null); [ "$got" = "$want" ] || { echo "DRILL FAIL: restored .git HEAD $got != $want"; return 1; }
  git clone -q --no-checkout "$FE_GEN/git/repo.bundle" "$FE_DRILL_DIR.bundle_clone" 2>/dev/null || { echo "DRILL FAIL: bundle clone failed"; return 1; }
  got=$(git -C "$FE_DRILL_DIR.bundle_clone" rev-parse HEAD 2>/dev/null); [ "$got" = "$want" ] || { echo "DRILL FAIL: bundle HEAD $got != $want"; return 1; }
  # working-tree equivalence: same number of changed/untracked paths as at backup time
  local n1 n2   # the backup deliberately excludes __pycache__, .pytest_cache and .DS_Store, so ignore those paths on both sides
  n1=$(grep '^[12u?] ' "$FE_GEN/identity/git_status_v2.txt" | grep -v -e __pycache__ -e .pytest_cache -e .DS_Store | wc -l)
  n2=$(git -C "$FE_DRILL_DIR" status --porcelain=v2 --untracked-files=all | grep '^[12u?] ' | grep -v -e __pycache__ -e .pytest_cache -e .DS_Store | wc -l)
  [ "$n1" = "$n2" ] || { echo "DRILL WARN: porcelain path count backup=$n1 restored=$n2 (investigate; racy-index differences do not change this count)"; }
  git -C "$FE_DRILL_DIR" fsck --no-progress > "$FE_GEN/../drill_fsck_$(date -u +%Y%m%dT%H%M%SZ).txt" 2>&1 || echo "DRILL WARN: git fsck reported problems (see drill_fsck_*.txt)"
  PYTHONDONTWRITEBYTECODE=1 sandbox-exec -p "$FE_JAIL" "$FE_PY" -I "$FE_GEN/tools/fe_validate.py" "$FE_DRILL_DIR" ${FE_VALIDATE_ARGS:-} > "$FE_DRILL_DIR.validation.json" || { echo "DRILL FAIL: validation of restored tree failed"; return 1; }
  echo "DRILL PASS for $FE_GEN_ID  (restored to $FE_DRILL_DIR, bundle clone at $FE_DRILL_DIR.bundle_clone)"
  printf '%s\t%s\tRESTORE-TESTED\tdrill=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$FE_GEN_ID" "$FE_DRILL_DIR" >> "$FE_DEST_ROOT/FeralEcho_backups/generations.log"
}

fe_stage_replicate() {   # RUN ON M5. Copies a SEALED generation byte-for-byte to a second destination root, then cold-verifies it there.
  : "${FE_GEN:?}" "${FE_DEST2_ROOT:?}" "${FE_GEN_ID:?}"
  ls "$FE_GEN"/COMPLETE-* >/dev/null 2>&1 || ls "$FE_GEN"/QUARANTINED-* >/dev/null 2>&1 || { echo "STOP: generation is not sealed"; return 1; }
  { [ -d "$FE_DEST2_ROOT" ] && [ -w "$FE_DEST2_ROOT" ]; } || { echo "STOP: FE_DEST2_ROOT missing or not writable"; return 1; }
  { [ "$(stat -f %d "$FE_DEST2_ROOT")" != "$(stat -f %d "$FE_DEST_ROOT")" ] || [ "${FE_TEST_ALLOW_SAME_VOLUME:-0}" = 1 ]; } || { echo "STOP: second destination is on the same volume as the first"; return 1; }   # FE_TEST_ALLOW_SAME_VOLUME is for synthetic tests only
  local g2="$FE_DEST2_ROOT/FeralEcho_backups/$FE_GEN_ID"
  [ ! -e "$g2" ] || { echo "STOP: $g2 already exists"; return 1; }
  mkdir -p "$FE_DEST2_ROOT/FeralEcho_backups" || return 1
  ( cd "$FE_DEST_ROOT/FeralEcho_backups" && tar -cf - "$FE_GEN_ID" ) | ( cd "$FE_DEST2_ROOT/FeralEcho_backups" && tar -xpkf - ) || { echo "STOP: replication tar pipeline failed"; return 1; }
  sync
  ( FE_GEN="$g2"; fe_stage_cold_verify ) || { echo "REPLICA FAIL: $g2"; return 1; }
  cmp "$FE_GEN/GENERATION.json.sha256" "$g2/GENERATION.json.sha256" || return 1
  printf '%s\t%s\tREPLICA-VERIFIED\tfrom=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$FE_GEN_ID" "$FE_DEST_ROOT" >> "$FE_DEST2_ROOT/FeralEcho_backups/generations.log"
  echo "REPLICA PASS: $g2"
}
FE_EOF
```

## Appendix C — `fe_judge.py` (paste as one block)
```bash
cat > "$FE_TOOLS_DIR/fe_judge.py" <<'FE_EOF'
#!/usr/bin/env python3
"""fe_judge.py -- audit a FeralEcho backup generation. stdlib only. Reads files under <gen>/manifest,
writes results.tsv, GENERATION.json (+ final.sha256, retry.lst). Never touches the source tree, never
imports FeralEcho code, never deletes. Exit codes: 0 = no file-level failure, 3 = retry needed, 1 = failures/QUARANTINED."""
import hashlib, json, os, sys, time

SELF_MUTATING = {"app/core/self_edit_convergence.json", "app/core/self_edit_generated.py",
                 "sandbox/scripts/temp_self_edit.py", "staging/self_edit_candidate.py"}
OK = {"VERIFIED-STABLE", "VERIFIED-LIVE-VERSION", "VERIFIED-APPEND-PREFIX"}

def read_lines(p):
    if not os.path.exists(p): return []
    with open(p, encoding="utf-8", newline="\n") as f: return [l.rstrip("\n") for l in f if l.rstrip("\n")]

def read_sha(p):
    out = {}
    for l in read_lines(p):
        if l.startswith("\\"): raise SystemExit("escaped path in %s (newline/backslash in a name); STOP: %r" % (p, l))
        h, _, path = l.partition("  ")
        if len(h) != 64 or not path: raise SystemExit("malformed sha256 line in %s: %r" % (p, l))
        out[path] = h
    return out

def read_kv(p):
    kv = {}
    for l in read_lines(p):
        k, _, v = l.partition("=")
        kv[k] = v
    return kv

def fingerprint(items):  # sha256 over sorted 'path\0sha256\n' (path without leading ./)
    h = hashlib.sha256()
    for path, sha in sorted(items): h.update(path.encode() + b"\0" + sha.encode() + b"\n")
    return h.hexdigest()

def main(gen):
    m = os.path.join(gen, "manifest"); tree = os.path.join(gen, "tree")
    if any(n.startswith(("COMPLETE-", "QUARANTINED-")) for n in os.listdir(gen)):
        print("REFUSED: generation is sealed (marker present). Never re-judge in place; create a new generation."); return 2
    lst = {k: read_lines(os.path.join(m, k + ".lst")) for k in ("all", "A", "B1", "B2", "B3")}
    anomalies = []
    # 1. coverage: every in-scope source file is in exactly one part; destination tree has exactly those files
    parts = {"A": lst["A"], "B1": lst["B1"], "B2": lst["B2"], "B3": lst["B3"]}
    union = [p for v in parts.values() for p in v]
    if len(union) != len(set(union)): anomalies.append("COVERAGE: a file appears in more than one part")
    if set(union) != set(lst["all"]): anomalies.append("COVERAGE: parts do not equal all.lst (missing=%d extra=%d)" % (
        len(set(lst["all"]) - set(union)), len(set(union) - set(lst["all"]))))
    dest_files = set(read_lines(os.path.join(m, "dest.lst")))
    if dest_files != set(lst["all"]): anomalies.append("DEST-TREE: destination files != source scope (missing=%d extra=%d)" % (
        len(set(lst["all"]) - dest_files), len(dest_files - set(lst["all"]))))
    # 2. per-file verdicts
    apre, apost, adest = (read_sha(os.path.join(m, "A.%s.sha256" % k)) for k in ("pre", "post", "dest"))
    rows = {}
    for l in read_lines(os.path.join(m, "copyrec.tsv")):
        c = l.split("\t")
        if len(c) != 12: raise SystemExit("bad copyrec row: %r" % l)
        rows.setdefault(c[0], []).append(c)
    files, retry = [], []
    stat = {}
    for l in read_lines(os.path.join(m, "stat.tsv")):
        r = l.split("\t")
        if len(r) == 4: stat[r[0]] = r
    for part, paths in parts.items():
        for rel in paths:
            rec = {"path": rel[2:], "tier": part, "part": "A-source" if part == "A" else "B-state"}
            if rel in rows and rows[rel][-1][11] != "MISMATCH":
                c = rows[rel][-1]
                rec.update(sha256=c[6], source_sha256_pre=c[4], source_sha256_post=c[5], status=c[11],
                           type=c[2], attempts=len(rows[rel]), size=int(c[10]))
            elif part == "A":
                pre, post, dst = apre.get(rel), apost.get(rel), adest.get(rel)
                if dst is None: st = "MISSING-IN-DEST"
                elif pre == post == dst: st = "VERIFIED-STABLE"
                elif dst in (pre, post): st = "VERIFIED-LIVE-VERSION"
                else: st = "MISMATCH"; retry.append(rel)
                rec.update(sha256=dst, source_sha256_pre=pre, source_sha256_post=post, status=st, type="REWRITE", attempts=1)
                if dst is not None and rel in stat: rec["size"] = int(stat[rel][1])
            else:
                rec.update(sha256=None, status="NOT-COPIED", type="?", attempts=0)
            files.append(rec)
    bad = [f for f in files if f["status"] not in OK]
    for f in bad: anomalies.append("FILE %s: %s" % (f["status"], f["path"]))
    # 3. outputs
    with open(os.path.join(m, "results.tsv"), "w") as f:
        f.write("path\ttier\tstatus\ttype\tattempts\tsha256\n")
        for r in files: f.write("%s\t%s\t%s\t%s\t%s\t%s\n" % (r["path"], r["tier"], r["status"], r["type"], r["attempts"], r["sha256"]))
    with open(os.path.join(m, "final.sha256"), "w") as f:  # for `cd tree && shasum -a 256 -c ../manifest/final.sha256`
        for r in sorted(files, key=lambda r: r["path"]):
            if r["sha256"]: f.write("%s  ./%s\n" % (r["sha256"], r["path"]))
    with open(os.path.join(m, "retry.lst"), "w") as f: f.write("".join(p + "\n" for p in retry))
    kv = read_kv(os.path.join(m, "kv.env"))
    validation = json.load(open(os.path.join(m, "validation.json"))) if os.path.exists(os.path.join(m, "validation.json")) else None
    a_items = [(r["path"], r["sha256"]) for r in files if r["part"] == "A-source" and r["sha256"]]
    srv_changed = (kv.get("SRV_PID_BEFORE") != kv.get("SRV_PID_AFTER")) or (kv.get("SRV_START_BEFORE") != kv.get("SRV_START_AFTER"))
    for nm, label in (("created_during", "created"), ("vanished_during", "vanished")):
        ds = read_lines(os.path.join(m, nm + ".lst"))
        if ds: anomalies.append("SCOPE-DRIFT: %d in-scope files %s during the backup window (informational): %s" % (len(ds), label, ", ".join(ds[:5])))
    if srv_changed: anomalies.append("SERVER: PID/start time changed during the backup window (restart or abort happened)")
    b1_ok = all(f["status"] in OK for f in files if f["tier"] == "B1")
    if validation is not None and not validation.get("passed"): anomalies.append("VALIDATION: %s" % validation.get("failures"))
    core_bad = [f for f in bad if f["tier"] in ("A", "B1")]   # source code / identity-critical state
    if any(a.startswith(("COVERAGE", "DEST-TREE", "VALIDATION")) for a in anomalies) or core_bad: level = "QUARANTINED"
    elif bad or validation is None or srv_changed or not b1_ok or not validation.get("pair_aligned"): level = "RESCUE-LIVE"
    else: level = "VERIFIED-LIVE"
    counts = {"files_total": len(files), "verified": len(files) - len(bad), "not_verified": len(bad),
              "bytes_total": sum(f.get("size") or 0 for f in files)}
    gen_json = {
        "schema_version": "1.0", "generation_id": kv.get("FE_GEN_ID"), "label": kv.get("FE_LABEL"),
        "created_utc": kv.get("FE_CREATED_UTC"), "completed_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "host": {"name": kv.get("HOST"), "os": kv.get("OSVER"), "arch": kv.get("ARCH")},
        "tool_versions": {k[5:].lower(): v for k, v in kv.items() if k.startswith("TOOL_")},
        "source": {"root": kv.get("FE_SRC"), "live": True,
                   "git": {"head": kv.get("HEAD"), "branch": kv.get("BRANCH"), "dirty": kv.get("PORCELAIN", "0") != "0",
                           "porcelain_paths": int(kv.get("PORCELAIN", "0")), "unpushed_commits": kv.get("UNPUSHED")},
                   "authored_tree_fingerprint": {
                       "definition": "sha256 over sorted '<path-without-./>\\0<sha256>\\n' for every A-part file",
                       "excluding_self_mutating_files_sha256": fingerprint([i for i in a_items if i[0] not in SELF_MUTATING]),
                       "including_self_mutating_files_sha256": fingerprint(a_items),
                       "legacy_reference_not_recomputed": kv.get("LEGACY_FP")},
                   "server": {"pid_before": kv.get("SRV_PID_BEFORE"), "start_before": kv.get("SRV_START_BEFORE"),
                              "pid_after": kv.get("SRV_PID_AFTER"), "start_after": kv.get("SRV_START_AFTER"),
                              "restarted_during_backup": srv_changed}},
        "destination": {"class": kv.get("FE_DEST_CLASS"), "root": kv.get("FE_DEST_ROOT"), "filesystem": kv.get("FS"),
                        "volume_uuid": kv.get("VOL_UUID"), "device_location": kv.get("DEV_LOC"),
                        "same_physical_device_as_source": kv.get("SAMEDEV"), "free_bytes_before": kv.get("FREE_BYTES")},
        "consistency_level": level, "restore_drill": None, "validation": validation, "counts": counts,
        "anomalies": anomalies, "exclusions": ["**/__pycache__/**", "**/.pytest_cache/**", "**/.DS_Store"],
        "audit_references": ["audits/2026-09-20_feralecho_runtime_identity_and_state_preservation.md",
                             "audits/2026-09-20_feralecho_verified_backup_and_recovery_plan.md"],
        "files": files}
    with open(os.path.join(gen, "GENERATION.json"), "w") as f: json.dump(gen_json, f, indent=1, sort_keys=True)
    print("consistency_level=%s files=%d verified=%d not_verified=%d anomalies=%d" % (level, len(files), counts["verified"], len(bad), len(anomalies)))
    for a in anomalies[:40]: print("  ANOMALY:", a)
    return 3 if retry else (1 if level == "QUARANTINED" else 0)

if __name__ == "__main__": sys.exit(main(sys.argv[1]))
FE_EOF
```

## Appendix D — `fe_validate.py` (paste as one block)
```bash
cat > "$FE_TOOLS_DIR/fe_validate.py" <<'FE_EOF'
#!/usr/bin/env python3
"""fe_validate.py <tree_root> -- structural validation of a COPIED FeralEcho state tree. Run only on copies,
inside a no-write jail. Imports NO FeralEcho code (no unpickling: pickles are walked with pickletools.genops,
which never imports modules or executes anything). Prints one JSON document to stdout."""
import json, os, pickletools, sqlite3, sys
FLOORS = {  # absolute sanity floors from the 2026-09-20 audit (~95% of measured); a first generation has no predecessor
  "memory/memory_meta.json": {"min_bytes": 95_000_000, "min_entries": 124_000},
  "memory/faiss.index": {"min_bytes": 190_000_000},
  "data/question_garden.jsonl": {"min_bytes": 10_000_000, "min_lines": 15_000},
  "memory/river_brain.pkl": {"min_bytes": 4_000_000},
  "memory/self_model_claims.jsonl": {"min_bytes": 8_000}}
def main(root, floors=FLOORS):
    res = {"checks": [], "failures": [], "pair_aligned": None}
    def chk(name, ok, detail=""):
        res["checks"].append({"name": name, "ok": bool(ok), "detail": detail})
        if not ok: res["failures"].append("%s: %s" % (name, detail))
    P = lambda rel: os.path.join(root, rel)
    for rel, fl in floors.items():
        if not os.path.exists(P(rel)): chk("present:" + rel, False, "missing"); continue
        sz = os.path.getsize(P(rel)); chk("floor_bytes:" + rel, sz >= fl.get("min_bytes", 0), "%d bytes (floor %s)" % (sz, fl.get("min_bytes")))
    n_meta = n_idx = None
    if os.path.exists(P("memory/memory_meta.json")):
        try:
            meta = json.load(open(P("memory/memory_meta.json"))); n_meta = len(meta)
            chk("json:memory_meta", isinstance(meta, dict) and n_meta > 0, "%d entries" % n_meta)
            fl = floors.get("memory/memory_meta.json", {}).get("min_entries", 0); chk("floor_entries:memory_meta", n_meta >= fl, "%d (floor %d)" % (n_meta, fl))
        except Exception as e: chk("json:memory_meta", False, repr(e))
    if os.path.exists(P("memory/faiss.index")):
        try:
            import faiss; n_idx = faiss.read_index(P("memory/faiss.index")).ntotal; chk("faiss:read_index", True, "ntotal=%d" % n_idx)
        except Exception as e: chk("faiss:read_index", False, repr(e))
    if n_meta is not None and n_idx is not None:
        res["pair_aligned"] = (n_meta == n_idx)
        chk("pair:count_alignment", n_meta == n_idx, "meta=%d index_ntotal=%d (meta ahead is repairable, index ahead is not)" % (n_meta, n_idx))
    for rel in ("memory/river_brain.pkl", "memory/task_type_classifier.pkl", "memory/drift_detectors.pkl"):
        if os.path.exists(P(rel)):
            try:
                ops = sum(1 for _ in pickletools.genops(open(P(rel), "rb").read())); chk("pickle_stream:" + rel, ops > 0, "%d opcodes, reached STOP" % ops)
            except Exception as e: chk("pickle_stream:" + rel, False, repr(e))
    for rel in ("data/question_garden.jsonl", "memory/self_model_claims.jsonl", "memory/council_ratings.jsonl"):
        if os.path.exists(P(rel)):
            good = bad = 0
            for line in open(P(rel), encoding="utf-8", errors="replace"):
                if not line.strip(): continue
                try: json.loads(line); good += 1
                except Exception: bad += 1
            fl = floors.get(rel, {}).get("min_lines", 0)
            chk("jsonl:" + rel, bad <= 1 and good >= fl, "%d valid, %d invalid (<=1 tolerated: possible final partial line), floor %d" % (good, bad, fl))
    for rel in ("memory/snapshot_baseline.json", "memory/behavioral_directives.json"):
        if os.path.exists(P(rel)):
            try: json.load(open(P(rel))); chk("json:" + rel, True)
            except Exception as e: chk("json:" + rel, False, repr(e))
    if os.path.exists(P("memory/optuna.db")):
        try:
            c = sqlite3.connect("file:%s?mode=ro&immutable=1" % P("memory/optuna.db"), uri=True); r = c.execute("PRAGMA integrity_check").fetchone()[0]; chk("sqlite:optuna", r == "ok", r)
        except Exception as e: chk("sqlite:optuna", False, repr(e))
    res["passed"] = not res["failures"]
    print(json.dumps(res, indent=1))
    return 0 if res["passed"] else 1
if __name__ == "__main__": sys.exit(main(sys.argv[1], {} if "--no-floors" in sys.argv else FLOORS))  # --no-floors: tests only
FE_EOF
```

## Appendix E — file lists (paste as one block)
```bash
cat > "$FE_TOOLS_DIR/b1.lst" <<'FE_EOF'
./memory/memory_meta.json
./memory/faiss.index
./data/question_garden.jsonl
./memory/river_brain.pkl
./memory/task_type_classifier.pkl
./memory/drift_detectors.pkl
./memory/self_model_claims.jsonl
./memory/council_ratings.jsonl
./memory/snapshot_baseline.json
./memory/behavioral_directives.json
./memory/genesis/genesis_hash.txt
./memory/genesis/council_hash.txt
./memory/genesis/genesis_timestamp.txt
FE_EOF
cat > "$FE_TOOLS_DIR/b2.lst" <<'FE_EOF'
./memory/interaction_log.jsonl
./memory/interaction_log.jsonl.1.gz
./memory/reflection_shard.jsonl
./memory/reflection_journal.jsonl
./memory/SELF_EDIT.log
./memory/council_deliberations.jsonl
./memory/echo_messages.jsonl
./memory/self_edit_outcomes.jsonl
./memory/dissent_log.jsonl
./memory/optuna.db
./memory/self_model.json
FE_EOF
```

## Appendix F — SHA-256 of the pasted files (verify after pasting)
| File | SHA-256 |
|---|---|
| `fe_lib.sh` | `d71bcf1541d3be78b9530e2ff8435f7a539cd3fcbef3f81bb4c4b0c1f19bb486` |
| `fe_stages.sh` | `fb3dcf3b77d96e5fa20905ba766e71c0e8760d7ff8f2175af83125a59f974c13` |
| `fe_judge.py` | `78ba2897921384415448a1eede686d65be6e6ed24473c0239c50315fcf496fdc` |
| `fe_validate.py` | `e5737bb6ac9d0e70fc1cfb09ff369a24483d1e476180f45884ec4b6898db9300` |
| `b1.lst` | `2f7b3b1b6d7432869e7df6b0ef253ad7463baeba0128495b47dd7ab22d1fa60c` |
| `b2.lst` | `eb3b617ee9e8f4404604021493a48a21b6556ad88028393b440565e06218ed39` |
