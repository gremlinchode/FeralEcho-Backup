# FeralEcho M5 ⇄ Intel Cross-Backup — Claude-to-Claude Relay Plan (PLAN ONLY)

**Date:** 2026-09-20 · **Author:** CLAUDE-M5 · **Status:** DESIGN FOR OPERATOR REVIEW.
**Nothing was transferred. No backup generation exists. Neither FeralEcho instance was modified, stopped, or restarted. No network call left this Mac. Intel was not contacted and its discovery has not begun.**
**Companion:** `audits/2026-09-20_feralecho_cross_backup_relay_schema.json` (JSON Schema for the relay messages).
**Evidence labels:** **OBSERVED** (read on the M5 during this mission, 2026-09-20 ≈22:17Z) · **INFERRED** · **UNKNOWN** · **TESTED-SYNTHETIC** (exercised on a throw-away fixture in the session scratchpad — never on FeralEcho data) · **UNTESTED**.

---

## 0. Scope, records, and what this mission actually did

### 0.1 Constraints honoured
Plan-only · no transfer · no modification, stop or restart of either instance · no `commit/push/pull/fetch/reset/clean/checkout/restore/stash/stage` · `backup_feral_echo.sh` not run · no bidirectional synchronization · nothing deleted or overwritten on either machine · frozen persistent-competence protocol untouched. **Only two files were created in the repository:** this plan and the schema JSON. CLAUDE-INTEL creates nothing until explicitly instructed.

### 0.2 Before-state (recorded before any deliverable was written; after-state in §24)
| Item | Value (OBSERVED) |
|---|---|
| Git HEAD | `2fba42644c82b9f7096276f4dd338d615cf1bcce` (`main`) |
| `git status --porcelain` | **188** paths (this listing is re-diffed in §24) |
| Server | PID **29288**, start **Sun Sep 20 07:30:10 2026** (`python -u run.py`, child of `start_echo.sh`) |

### 0.3 Phase A was performed on the M5 (read-only), and it changed what this plan assumes
CLAUDE-M5 re-verified its own machine with the discovery script defined in §23 (a read-only script; **31 s** runtime). The script was also run inside a *kill-on-violation* sandbox profile (`(deny file-write* (with send-signal SIGKILL))`, non-loopback network likewise): it completed with exit 0 and all 224 output lines, while two controls prove the jail bites (a write attempt was killed — exit 137, no file created; an external `curl` was killed). **TESTED-SYNTHETIC evidence that discovery writes nothing and uses no external network.** The paste recipe of §23 (a bash heredoc that carries the script) was also run under a write-deny jail that permitted only bash's own heredoc temp files: exit 0, hash gate passed, zero denials; heredocs necessarily create such transient temp files, which is disclosed in the first message's rule 1. A secret-leak test compared every `.env` value (≥ 6 chars) with the output: only the non-secret `OLLAMA_MODEL` value (`echo:latest`) appears; the four secrets and the URL appear **0** times.

**M5 facts (OBSERVED):**
| Field | Value |
|---|---|
| Identity | `arm64` true (`hw.optional.arm64=1`, not Rosetta-translated), `Mac17,3`, "Apple M5", macOS 27.0 build 26A428, RAM 24 GiB, hostname `Richards-MacBook-Air` |
| Derived IDs | `HW_ID16=6ce790640af98160`, `MACHINE_ID16=dd7643e652db2d2c` (salted hashes; the raw hardware UUID is never printed) |
| Disk | internal APFS SSD, SMART Verified, FileVault **On**; home volume 994,610,155,520 B total, **754,850,684,928 B free** |
| Root | `/Users/richietate/Desktop/FeralEcho` — class **LIVE** (running server PID 29288 has its cwd there) |
| Sizes | repo 1,663,496 KB; `.git` 37,512 KB; `memory/` 1,238,300 KB; `data/` 50,736 KB |
| Preservation set | source 306,558,978 B / 22,441 files; state 1,285,734,873 B / 362 files; **proposed 1,592,293,851 B**; 0 symlinks; 0 odd path names |
| Git | HEAD above, `main`, 176 commits, 4 refs (`main` 2fba426, `worktree-agent-abe6ecca0408fd0fb` a23b940, `origin`/`origin/main` d6cd738), **17 unpushed (local-ref view; no network)**, 27 tracked-modified, 223 untracked non-ignored, 188 porcelain paths, 0 stash, 2 worktrees (main + linked) |
| Fingerprints | `WORKTREE_FINGERPRINT_V1=e67d1101dcf8dc95216464614b480f56b38be48baf166c5dbe5ef1d12852d71f` (volatile by design: changes with any authored-file edit — including these deliverables), `STATE_LAYOUT_FP_V1=e62cc77468545dc2` |
| `.env` | PRESENT, 420 B, **mode 644**, sha256 prefix `37b9f33c3555222d` — **contents never read into any report**. Mode 0644 means any local account can read it; not changed (no modification allowed); flagged for an operator decision |
| Ollama | 0.34.2; 9 models (names/digests in §5.4); weights not preserved |
| Others running | Ollama server PID 1991, `start_echo.sh` PID 2136, **`echo_studio.main` PID 34531** (desktop client of the server) |
| Remote Login | **UNKNOWN** (`launchctl print-disabled` returned no ssh line; real state needs admin) |
| Tooling | Xcode tools present; git is Homebrew's (`/opt/homebrew/bin/git`); `/usr/bin/python3` is the Xcode shim (refuses to run without the licence) — conda python used by absolute path |

**Other Echo-related material on the M5 (OBSERVED, classification is heuristic — none of it was touched):**
| Path | Size | Class | Note |
|---|---|---|---|
| `~/Desktop/FeralEcho_backup_20260905_145413.zip` | 592,426,424 B (19,893 files) | **BACKUP** (same disk, 15 days old) | contains `.git` (33.8 MB), `memory/` incl. `memory_meta.json` 91.4 MB, `faiss.index` 190.9 MB, `river_brain.pkl` 3.6 MB, `data/`. **This is a correction to my two preceding audits, which did not list it.** It is still the same SSD (same failure domain) and is a *historical generation to preserve, never update* |
| `~/Desktop/FeralEcho-Backup-scrub` | ≈100 MB | HISTORICAL LINEAGE / BACKUP | git repo, HEAD `d8d6676`, 117 commits, no `memory/` or `data/`; looks like a history-scrubbed copy for the GitHub backup remote; provenance UNKNOWN |
| `~/echo_data/` | ≈1.3 MB | HISTORICAL LINEAGE | 2026-06-18: `memory/river_brain.pkl` 1 MB, `echo_principles.json`, `lattice_log.json`, `principle_hashes.txt` |
| `~/EchoCoreV2/` | 200 KB | HISTORICAL LINEAGE (predecessor project, cf. Finding 8) | |
| `~/FeralEchoBackups/FeralEcho_2025-08-24_15-53-36`, `~/FeralEchoMemory_backup.json`, `~/FeralEchoSnapshots` (empty), `~/data/{faiss.index,memory_meta.json}` (2025-09-07) | < 1 MB | BACKUP / UNKNOWN | tiny ancestral material |
| `~/.claude/projects/-Users-richietate-Desktop-FeralEcho` | ≈211 MB | UNKNOWN (adjacent) | Claude Code project memory + session transcripts; not FeralEcho state; operator decision |
| `~/.ssh/feralecho_deploy(.pub)` | 4 KB each | UNKNOWN | credential *names* only reported |
| Repo docs from the Intel side: `SIBLING_BRIEFING_FROM_ARK.MD`, `claude_relay/*` | — | HISTORICAL (documents) | the **M5's belief, dated 2026-07-07, unverified**: the Intel instance ("Ark") is an i7-1060NG7, 16 GB, runs with `ECHO_ARK_MODE`, has no `data/` FAISS index, and its own `ForensicAudit 2020 Macbook/` directory. **None of this is treated as fact about Intel today** |

### 0.4 What is written and tested, and what is not
**Written and tested (TESTED-SYNTHETIC / on the M5):** the read-only discovery script `fe_discover.sh` (Appendix; run for real on the M5), the relay seal/check/lint tools `fe_relay.sh` with positive and negative controls (8/8 hostile strings rejected, clean message accepted, one-character tamper caught by the CRC, the authorization gate has no shortcut edge), the manifest/challenge/receive/seal/path-regex primitives, and 17 filled relay examples validated by both `relay_check` and the JSON Schema. **Specified but NOT yet written or tested:** the "v2" backup tooling that produces the `source/ state/ identity/ manifest/` layout and the cross-transfer stages (§21 Phase C′ makes building and rehearsing them a hard prerequisite of the authorization gate), everything that needs the Intel machine, and every ssh step.

---

## 1. Executive design

**Central principle: CROSS-BACKUP, never sync, never merge.** Two lineages stay separate forever; each machine holds *sealed, immutable, self-describing generations* of the other.

**The design in one paragraph.** Each machine first makes a **sealed local generation of its own lineage** in `~/FeralEcho_Cross_Backups/OWN_LOCAL/` (outside every live repo), using per-file *source-hash-before / copy / source-hash-after / destination-hash* rules — this is where live-server inconsistency is dealt with, once, locally. The cross-backup is then a **byte copy of an already-sealed, therefore static, generation** into the peer's `FROM_<lineage>/` directory over a one-way SSH+tar stream. The two Claude sessions coordinate by operator-relayed, CRC-sealed, secret-linted text messages following a fixed state machine. Nothing is written to either machine until a human types a **direction-and-list-bound authorization phrase into each session**. Verification is *recomputation*, never trust: the destination independently recomputes a manifest hash, file count and byte count, and answers a nonce-salted digest challenge that only someone holding the received bytes can answer; the source compares against values it computed itself. Only then is the generation sealed (read-only, marker file, append-only registry line). The two directions are independent state machines with independent statuses.

**Why "seal locally, then copy" rather than streaming live files straight across:** (1) live mutable files can be caught mid-write; proving a *stable* copy is easy locally (hash before/after on the same disk) and impossible mid-stream; (2) after sealing, the source bytes are immutable, so "BEFORE == AFTER == DESTINATION" holds trivially and any mismatch is a transport/storage fault, not liveness; (3) the source machine ends up with an extra local generation (a same-disk, logical-corruption defence); (4) the transfer is re-runnable into a new generation number at ≈1.6 GB cost.

**Key decisions (each argued in the named section):** direction order decided by evidence, M5→Intel presumptively first (§21 Phase C); **only the Intel ever runs an SSH server; the M5 is always the SSH client** (§8); authorization binds *generation + direction + hash of the file list* (§13) and must be typed into **both** sessions; no `rm`, `mv`, `--delete`, `git` write verbs anywhere in the execution path (§22, machine-linted with positive controls).

---

## 2. Two-lineage model
| | FERALECHO-M5 | FERALECHO-INTEL-2020 |
|---|---|---|
| Role | current primary instance | separate, older installation ("Ark" per the M5's unverified 2026-07-07 briefing) |
| Verified today | **yes** (§0.3) | **no — must be discovered from scratch** |
| Live root | `/Users/richietate/Desktop/FeralEcho` | UNKNOWN |
| Own generations | `OWN_LOCAL/M5_<date>_G<nnn>` | `OWN_LOCAL/INTEL_<date>_G<nnn>` |
| Holds the other's | `FROM_INTEL/INTEL_…` | `FROM_M5/M5_…` |

**Invariants (each enforced by a mechanism named in the section given):**
I1 A generation belongs to exactly one lineage; the lineage label is in its name, README, manifest, and every relay message (§4, §7).
I2 **No path exists from `FROM_*` or `OWN_LOCAL` into any live directory**; the only writers of `FROM_*` are the receive stage of one authorized transfer (§8, §13).
I3 A generation directory is created once (plain `mkdir`), written once, sealed once; if it exists the procedure STOPs (§7).
I4 A peer's generation is never restored automatically, and never over live state (§16).
I5 The two lineages' persistent states are **never merged**; restore targets the *same* lineage only, into staging first (§16).
I6 Each direction has its own state machine, generation counter, and status; failure of one never triggers, retries, rolls back or deletes anything in the other (§12, §17).
I7 The relay carries no secrets and no file contents (§9).
I8 Hostname is never identity (§4).

---

## 3. Discovery procedure (Phase A)
**Rule:** each Claude independently inventories **its own** machine, read-only, and reports only what its own commands showed. Neither assumes anything about the other that the other has not reported (a fact the M5 *believes* about Intel is labelled "belief" and is never used as evidence).

**Instrument:** `fe_discover.sh v1` (§23, Appendix A). It prints, to stdout only: machine identity (arch + Rosetta trap + model + OS + salted hardware hash), disk and volume facts (SMART/FileVault), tool availability, Command Line Tools status (it **refuses to invoke an `/usr/bin/git` shim when the Command Line Tools are absent**, to avoid a GUI install prompt), running server-like processes with working directories (`lsof`), **all candidate FeralEcho roots under `$HOME` (depth ≤ 6)** classified LIVE / POSSIBLE_LIVE / HISTORICAL_LINEAGE by evidence (heuristic; uncertain ⇒ preserve), per root: sizes, git facts (HEAD, branch, refs, redacted remotes, unpushed **from local refs only**, modified/untracked counts, ignored top-level names, stash, worktrees), the working-tree fingerprint, presence/size/mtime of the canonical persistence artifacts, the largest 12 files and extension histogram of `memory/` and `data/` (to expose *unknown* persistence on Intel), `.env` as PRESENT/size/mode/16-hex prefix only, server pid file and sentinel, interpreters with architecture, Ollama names/digests/version, and a name search (depth ≤ 7) of `$HOME`, `/Users/Shared` and `/Volumes` for other Echo material (`memory_meta*`, `faiss.index*`, `river_brain*`, `*.bundle`, `question_garden*`, `echo_principles*`, `*feralecho*`, …) classified BACKUP / HISTORICAL_LINEAGE_OR_POSSIBLE_LIVE / UNKNOWN.

**Limits, stated:** classification is by heuristic (name, `.git`, mtime, running cwd) — a human may reclassify; depth limits can miss deeper material; Spotlight is not used; nothing is read *inside* files except sizes/mtimes and the `.env` hash; FAISS/meta entry counts are **deferred to validation on copies** (never read from the live files); Time Machine/iCloud state is reported as found.

**What must be reported before anything is written to Intel** is listed as answer 1 of the final questions and as the `DISCOVERY_RESPONSE` template (§20). **Phase A on Intel is the operator's next action**, not started here.

---

## 4. Machine identity procedure
Hostname is unusable (the M5's LocalHostName is literally `Richards-MacBook-Air`, and the Intel Air may be the same). Identity is a **tuple**, compared field by field, and any disagreement is a STOP:

| Field | How derived | Stability |
|---|---|---|
| `MACHINE_ROLE` | operator-assigned: `M5` or `INTEL` | fixed |
| `ARCH_TRUE` | `hw.optional.arm64` (1 ⇒ arm64, else x86_64) — **not `uname -m`**, which reports `x86_64` for a Rosetta-translated shell; `sysctl.proc_translated` is also reported | stable |
| `HW_MODEL`, `CPU`, `OS` | `sysctl hw.model`, `machdep.cpu.brand_string`, `sw_vers` | stable (OS changes on upgrade) |
| `HW_ID16` | first 16 hex of sha256(`feralecho-hw-v1|<IOPlatformUUID>`) — raw UUID never printed | stable |
| `MACHINE_ID16` | first 16 hex of sha256(`feralecho-machine-v1|ARCH_TRUE|HW_MODEL|UUID`) | stable — **pinned on first exchange; any later message with a different value is rejected** |
| `WORKTREE_FINGERPRINT_V1` | sha256 over sorted `path<TAB>sha256` of `git ls-files -co --exclude-standard` minus `memory/`, `data/` and the four self-mutating files (`app/core/self_edit_convergence.json`, `app/core/self_edit_generated.py`, `sandbox/scripts/temp_self_edit.py`, `staging/self_edit_candidate.py`) | **volatile by design** — identifies the authored tree *at a moment* |
| `STATE_LAYOUT_FP_V1` | first 16 hex of sha256 over the presence/absence pattern of a fixed list of 18 canonical persistence paths | stable — identifies the persistence *layout*, not its contents |
| `STATE_OBSERVATION` | sizes+mtimes of the state set at time T | volatile, timestamped, **never an identity** |
| `GIT_HEAD` + ref list | `git rev-parse HEAD`, `for-each-ref` | changes with commits |

**Labels.** `FERALECHO-M5` and `FERALECHO-INTEL-2020` are *assigned by the operator* and bound to the tuple above at first contact (`MACHINE_ID16` + `HW_ID16`); a label is never inferred from a directory name or hostname. Lineage identity in a generation = label + `MACHINE_ID16` + `GIT_HEAD` + `WORKTREE_FINGERPRINT_V1` + `STATE_LAYOUT_FP_V1` + UTC time, written into `identity/lineage.txt` at staging and repeated in every relay header.
**Expected Intel values are UNKNOWN** (`x86_64`, a `MacBookAir9,1`-like model, i7-1060NG7 per the M5's belief) and are **not** used as gates except `ARCH_TRUE=x86_64` and `ROSETTA_TRANSLATED=0`.

---

## 5. Preservation-set derivation
Each Claude derives **its own** three sets; the M5's earlier preservation audit is reusable *evidence for the M5 only*; Intel is traced fresh.

### 5.1 Definitions
* **SOURCE SET** — everything authored: the working tree (tracked, untracked, ignored-but-meaningful), `.git` incl. all refs, config, scripts, audits; a `git bundle --all`. Justified exclusions only: `__pycache__`, `.pytest_cache`, `.DS_Store`.
* **PERSISTENT STATE SET** — every artifact the running system accumulates: `memory/`, `data/`, plus any persistence found elsewhere by tracing.
* **IDENTITY EVIDENCE SET** — Git facts, fingerprints, per-file hashes/sizes/mtimes/modes, server PID/start, interpreter and package list, Ollama names/tags/digests/versions, launchd plist, `.env` names + hash (never values), disk/volume identity, the discovery report hash.

### 5.2 Classification of each artifact
`IRREPLACEABLE` · `EXPENSIVE TO RECREATE` · `REBUILDABLE` · `EPHEMERAL` · `UNKNOWN`. **UNKNOWN is preserved.** Ephemeral files (`echo_server.pid`, `echo_sentinel.json`) are *copied for completeness but never restored*.

### 5.3 M5 derivation (reused evidence + today's discovery)
* **Class A source:** 22,441 files, 306,558,978 B (incl. `.git`, `.env`, `.claude/`, scaffold dirs, `WhisperOfPeace.wav`, `Figure_*.png`, `sandbox/`, `audits/`). Nothing excluded for size.
* **Class B state:** 362 files, 1,285,734,873 B. **B1 (irreplaceable/expensive, 13 files, 317,043,348 B):** `memory/memory_meta.json` (IRR), `memory/faiss.index` (REB, expensive; **paired** with the meta), `data/question_garden.jsonl` (EXP), `memory/river_brain.pkl` (EXP), `memory/task_type_classifier.pkl`, `memory/drift_detectors.pkl`, `memory/self_model_claims.jsonl` (IRR), `memory/council_ratings.jsonl` (IRR, human labels), `memory/snapshot_baseline.json`, `memory/behavioral_directives.json`, three `memory/genesis/*.txt`. **B2 (11 files, ≈148.7 MiB):** interaction/reflection/deliberation logs, `SELF_EDIT.log`, `optuna.db`, `self_model.json`, messages, outcomes, dissent log. **B3:** everything else (the two 89 MB `memory_meta_backup_*` files, `memory/backups/`, `memory/archive/`, snapshots, `data/memory_meta.json` and `data/faiss.index` — the frozen legacy index from 2026-05-15 — etc.).
* **Ancestral set (separate series, §7):** the 2026-09-05 zip, `FeralEcho-Backup-scrub`, `~/echo_data`, `~/EchoCoreV2`, `~/FeralEchoBackups`, `~/FeralEchoMemory_backup.json`, `~/data/*` — ≈ 0.7 GB, preserved **as found**, offered as a separate `ANCESTRAL` generation `M5_<date>_A001`; **not** silently included in, or excluded from, G001 — an operator decision.
* **Identity set:** as §5.1. Legacy identity fingerprint `8e6808dc64fbebe5…` from the earlier manifest is recorded for reference only (its file set is not reproducible).

### 5.4 Intel derivation (fresh tracing — procedure for CLAUDE-INTEL, read-only)
1. Run the discovery script; report every candidate root and every other Echo-related item with the script's classification.
2. For the LIVE/POSSIBLE_LIVE root(s): **read the source** for what the system writes — `grep` (read-only) for `open(`, `np.save`, `pickle.dump`, `faiss.write_index`, `json.dump`, `sqlite3.connect`, `logging.FileHandler` targets — and reconcile with the files actually present and their mtimes; also list files > 1 MB in `memory/` and `data/` (the script does this).
3. Propose, in a plain list, SOURCE/STATE/IDENTITY sets with the five-way classification per artifact; report it to CLAUDE-M5 as counts + names (no contents).
4. Note the Intel layout may differ from the M5's (no assumption of `data/` FAISS, different filenames, `ARK_MODE` variants).
5. **Never assume the M5's B1 list applies to Intel.**

### 5.5 Model weights (default: do NOT copy)
Record per model: **name, tag, full digest (or 16-hex prefix), size, runtime version** (M5: Ollama 0.34.2; `echo:latest` `8cbcbe23800bfe9c` 4.7 GB; `gemma3:4b` `a2af6cc3eb7fa8be`; `qwen2.5-coder:7b` `dae161e27b0e90dd`; `deepseek-r1:7b` `755ced02ce7befdb`; `qwen2.5:3b` `357c53fb659c5076`; `llama3.2:3b` `a80c4f17acd55265`; `llama3.1:8b` `46e0c10c039e0191`; `llama3:instruct` `365c0bd3c000a25d`; `mistral:latest` `6577803aa9a03636`) plus the tracked `Modelfile`. Copy weights **only** if evidence shows a specific local model artifact is unique and not re-obtainable (e.g. a model whose digest is not in the public registry *and* has no Modelfile recipe). `echo:latest` is a derived model rebuildable from the tracked `Modelfile` + `llama3:instruct`; **UNKNOWN** whether the registry still serves that 12-month-old base digest — recorded as a risk, not a reason to copy 35 GB. HuggingFace `all-MiniLM-L6-v2` (≈ 90 MB; startup runs offline) is *recommended* as a small exception, operator's call.

---

## 6. Destination capacity rules
Applies to **every** volume that will receive a generation — the peer's `FROM_*` **and** the source's own `OWN_LOCAL` staging.
* `REQUIRED_FREE = 2 × PROPOSED_BACKUP_BYTES + 10 GiB` (the 2× absorbs one abandoned partial attempt and hard-link-free copies; 10 GiB absorbs OS churn). Any UNKNOWN input ⇒ **BLOCKED (fail closed)**.
* `POST_TRANSFER_FREE ≥ max(20 GiB, 15 % of volume total)` — never fill a startup volume.
* Re-measured **immediately before** the transfer and **again by the destination after** it; a `df` reading older than the current relay step is void.
* The destination Claude computes the requirement **itself** from the announced `PROPOSED_BACKUP_BYTES` and reports `REQUIRED_FREE_BYTES` independently; the source compares both numbers.
* The margin may only be raised, never lowered, without changing this plan.

**Worked numbers (OBSERVED M5):** `PROPOSED = 1,592,293,851` ⇒ `REQUIRED_FREE = 13,922,005,942 B (≈ 13.0 GiB)`; a 250 GB Intel with 15 % rule needs post-transfer free ≥ 37.5 GB. **M5 as a destination** (Intel→M5): free 754.8 GB ≫ requirement (post-transfer floor 149.2 GB) ⇒ **not capacity-constrained for any plausible Intel size**. **Intel as a destination is UNKNOWN** and is the likeliest blocker (§21 Phase C).

---

## 7. Generation layout
```
~/FeralEcho_Cross_Backups/                     (mode 700; NEVER inside any live FeralEcho directory, .claude/, or a git working tree)
  OWN_LOCAL/                                   own sealed local generations (the outbound staging area)
    M5_2026-09-20_G001/          (on M5)   |   INTEL_2026-09-20_G001/   (on Intel)
  FROM_M5/                                     (exists on INTEL)   received generations of the M5 lineage
    M5_2026-09-20_G001/
  FROM_INTEL/                                  (exists on M5)      received generations of the Intel lineage
    INTEL_2026-09-20_G001/
  _REPORTS/                                    append-only validation/drill/cold-verify reports (never inside a sealed generation)
  generations.log                              append-only registry (`>>` only)
```
**Inside every generation:**
```
README.txt          lineage, generation ID, direction, how to verify, "DATA RECOVERY, not necessarily direct executability"
source/             the authored tree, relative paths preserved (incl. .git, .env)      [Class A]
state/              memory/ and data/ trees, relative paths preserved                  [Class B, tiers recorded in the manifest]
identity/           lineage.txt, git_* files, git repo.bundle, runtime/env facts, .env names+hash, discovery report hash
manifest/           files.tsv (path, size, sha256), MANIFEST_HASH, stat.tsv (mode/mtime), copy records, validation.json, source seal
markers             RECEIVING-<nonce> → SEALED-<manifest8> | ABANDONED-<reason>   (marker files, never renamed, never removed)
```
**ID grammar:** `<M5|INTEL>_<YYYY-MM-DD>_G<nnn>` (`A<nnn>` for ancestral series). `nnn` = 1 + the highest number seen in `OWN_LOCAL/`, `FROM_*/` **and** `generations.log` for that lineage — never reused, never reset, not tied to the date. **Collision rules:** the directory is created with plain `mkdir` (no `-p` on the final component) — if it exists, **STOP**; the destination also refuses if the ID appears in `generations.log`; a directory holding `RECEIVING-*` without `SEALED-*` is **never resumed** — it is marked `ABANDONED-*` (a new marker file) and the retry is `G002`, leaving the partial in place. **Permissions:** created under `umask 077`; on seal, `chmod -R a-w` (TESTED-SYNTHETIC: appends then fail with "Permission denied"); `chflags -R uchg` is an optional stronger seal (TESTED-SYNTHETIC: blocks appends **and** new files; reversing it is a deliberate human act, mentioned so nobody is surprised). **Destination-side enforcement of "outside live repos":** the relayed path must match `^/Users/<user>/FeralEcho_Cross_Backups/FROM_(M5|INTEL)/(M5|INTEL)_YYYY-MM-DD_Gnnn$` (TESTED-SYNTHETIC: rejects spaces, `;`, `$()`, and paths under `Desktop/FeralEcho`), and must not lie under any discovered live root. The location is deliberately **not** under `~/Desktop`, `~/Documents` or `~/Downloads` (macOS privacy protection can block SSH-launched processes there).

---

## 8. Transport design (nothing executed)
| Option | Verdict | Reasoning |
|---|---|---|
| **T1: SSH + `tar` stream** (built-in) | **RECOMMENDED** | one-way per operation; no mirror mode; `tar -k` never overwrites; no `--delete` exists in `tar`; works with the built-in `ssh` on both; needs Remote Login on the *receiving-side of the connection* only |
| SSH + `scp -r` | fallback | built-in; no built-in overwrite protection (must pre-check an empty directory); no restart |
| SSH + `rsync` (openrsync) | **not used** | macOS `/usr/bin/rsync` is openrsync (protocol 29); it has `--delete`; its flag coverage was never enumerated; "sync tool" semantics are exactly what this plan forbids |
| macOS File Sharing (SMB) | not used | GUI-driven, silent overwrite in Finder, `._*` sidecars, weaker verification, another listener |
| AirDrop / direct local network transfer | not used for data | interactive, unscriptable, no integrity report; acceptable only as a human courier for a *tiny* file |
| Temporary archive + copy | acceptable variant | a sealed tarball of a generation moved by USB disk (future vault) — same verification, no network |
| The existing `claude_relay/` + `/projects/file` HTTP channel | **must not be used** | it is unauthenticated, git-adjacent (this plan forbids git writes), and its history has already leaked credentials once |

**Topology — "only Intel ever listens".** For M5→Intel the **M5 pushes** (M5 = SSH client, Intel = the SSH server). For Intel→M5 the **M5 pulls** (M5 is *still* the SSH client; it runs a fixed, read-only `tar -cf -` on Intel over SSH). The M5 therefore **never opens an SSH listener**, and Intel exposes Remote Login only during the two authorized windows. The operator enables Remote Login on Intel in System Settings → General → Sharing (restricted to the operator's user) and **disables it again after both directions are sealed**; those are the operator's own actions on system settings, never FeralEcho files. Recommended hardening H1: a *dedicated* SSH key (new file under `~/.ssh` on the M5, authorized on Intel with `from=`, `no-pty`, `no-port-forwarding`, and — for the pull direction — a `command=` forced to the single `tar -cf -` of the one authorized sealed generation). **UNTESTED**; if H1 is not adopted the operator types the Intel account password interactively (never relayed).

**Host authenticity.** The destination reports its host-key fingerprint (`HOSTKEY_FP`, from `ssh-keygen -lf`) in the relay; the operator confirms the fingerprint ssh displays matches; `StrictHostKeyChecking=yes` afterwards. No network scanning or discovery is ever run; the peer's tailnet name/IP is typed by the operator from the peer's own Tailscale app.

**Receive-side preparation (destination, only after authorization):**
```bash
# RUN ON DESTINATION (INTEL for M5->INTEL; M5 for INTEL->M5)
umask 077
CB="$HOME/FeralEcho_Cross_Backups"; GEN_ID="M5_2026-09-20_G001"          # example: M5->INTEL
mkdir -p "$CB/FROM_M5" "$CB/_REPORTS"
DEST="$CB/FROM_M5/$GEN_ID"
mkdir "$DEST" && : > "$DEST/RECEIVING-$(date -u +%Y%m%dT%H%M%SZ)"          # plain mkdir: fails if the generation exists
```
**Source-side pre-flight and stream (M5→Intel push):**
```bash
# RUN ON M5   (after the generation is sealed locally; DEST is the regex-validated path from DESTINATION_CAPACITY_ACCEPT;
#              PEER is user@host typed by the operator from the peer's own Tailscale app - never discovered by scanning)
: "${PEER:?set PEER}" "${DEST:?set DEST}" "${GEN_ID:?set GEN_ID}"
SSHO="-o BatchMode=yes -o StrictHostKeyChecking=yes -o ConnectTimeout=10 -o ServerAliveInterval=15 -o ServerAliveCountMax=4"
ssh $SSHO "$PEER" "test -d '$DEST' && test \"\$(ls -A '$DEST' | grep -vc '^RECEIVING-')\" = 0 && df -k '$DEST' | tail -1"     # must be empty except RECEIVING-*
set -o pipefail
( cd "$HOME/FeralEcho_Cross_Backups/OWN_LOCAL/$GEN_ID" && tar -cf - . ) | ssh $SSHO "$PEER" "cd '$DEST' && tar -xpkf -"
echo "stream exit status: $?"
```
**Pull for Intel→M5 (M5 still the client):**
```bash
# RUN ON M5   (after INTEL sealed its local generation; SRC_GEN is the regex-validated OWN_LOCAL path reported by INTEL)
: "${PEER:?set PEER}" "${SRC_GEN:?set SRC_GEN}" "${DEST:?set DEST}"
ssh $SSHO "$PEER" "cd '$SRC_GEN' && tar -cf - ." | ( cd "$DEST" && tar -xpkf - )
```
TESTED-SYNTHETIC with a local stand-in for `ssh` (no network): quoting holds; the receiving `tar -xpkf` **does not overwrite an existing file — and exits 0 while skipping it** (observed). That silent skip is why the *pre-flight emptiness test* and the *post-transfer manifest comparison* are both mandatory: `tar -k` is a guard, not an alarm.
**Restartability:** streams are not resumable; an interrupted or failed attempt is marked `ABANDONED-<reason>`, left in place, and retried as the next generation number (≈ 1.6 GB per attempt). **Visible failure:** `set -o pipefail`, `BatchMode`, `ServerAliveCountMax`, emptiness pre-flight, exit-status reporting in `TRANSFER_COMPLETE_*`, destination `df` before/after, manifest comparison.

---

## 9. Credentials and secrets
1. **Relay is treated as a public channel** — it may pass through third-party chat surfaces. `fe_relay.sh` rejects (TESTED-SYNTHETIC, 8 hostile strings, all rejected): token shapes (`ghp_…`, `sk-…`, `AKIA…`, `xox…`, JWT), PEM/PGP blocks, `NAME=value` dotenv shapes, 32+ hex runs and 40+ opaque runs in non-hash fields, secret-named fields carrying values, lines > 400 chars, and a strict `ENV_FILE` grammar (`ABSENT` | `PRESENT size= mode= sha256_16=`). A message that fails lint is **not sent**; the sender rewrites it.
2. `.env` is reported as **PRESENT / size / mode / 16-hex hash prefix** only. Its bytes travel exclusively inside the machine-to-machine stream, as part of `source/`.
3. **No secret value is ever printed by any command in this plan** (discovery script verified against the real `.env`: 0 leaks). `git remote -v` is filtered to redact URL credentials; `.git/config` is checked by *count* of credential-shaped URLs (M5: 0).
4. **Destination permissions:** `FeralEcho_Cross_Backups` created under `umask 077` (mode 700); files keep their modes via `tar -p`; before sealing, the destination Claude sets `source/.env` to `0600` in the *copy* only. (The M5's live `.env` is 0644 — reported, not changed.)
5. **Encryption at rest:** the M5 has FileVault On. A generation contains `.env` (API keys, `GREMLIN_SECRET`, `ECHO_PARTNER_SECRET`), so a destination with FileVault **Off** is allowed **only** if the operator adds `UNENCRYPTED-OK` to the authorization phrase in both sessions.
6. SSH passwords are typed by the operator into `ssh`, never into any relay message or Claude prompt; the dedicated key (H1), if used, has no passphrase-in-chat.
7. **Blast radius of a stolen generation** = every credential in `.env`; rotation guidance belongs to the operator.

---

## 10. Live-state consistency model
* **Layer 1 — local staging (source machine, live files):** for each mutable file: SOURCE HASH BEFORE → COPY → SOURCE HASH AFTER → DESTINATION HASH; **REWRITE files** must satisfy `BEFORE == AFTER == DESTINATION` or DESTINATION ∈ {BEFORE, AFTER} (a complete real version — prefixes are *not* accepted, because a truncated pickle is a prefix of the finished one); **APPEND files** (explicit list) are accepted iff the destination equals the first *N* bytes of the source as re-read after the copy and the source did not shrink (rotation caught). A file that fails after ≤ 3 predefined attempts is recorded `LIVE-MUTATED-DURING-BACKUP` (failed attempts are moved aside into the generation's `work/failed/`, never deleted). This is the machinery already tested in the preceding backup plan, TESTED-SYNTHETIC there; its layout adaptation is Phase C′.
* **Layer 2 — cross-transfer (static sealed bytes):** BEFORE == AFTER == DESTINATION holds by construction; any difference is a transport/storage fault.
* **Levels:** `RESCUE-LIVE` (every file a faithful copy of a real or prefix version, but pair/validation/steady-server not all established) → `VERIFIED-LIVE` (+ validation passed, FAISS count = metadata count *where applicable*, same server PID/start, all B1 verified) ; `VERIFIED-QUIESCENT` needs a stopped server (**not offered by this plan**); `QUARANTINED` = NOT KNOWN GOOD.
* **What is never claimed:** that a live generation is a transactional snapshot. The M5's FAISS/meta pair is written in two steps (meta first), ≈26 persists/h; the Intel's writers are **UNKNOWN**.
* **Server state must not be changed to improve consistency** — no stop, no restart, no signal, no pause.

---

## 11. Manifest and hash verification
**Files and formulas (commands TESTED-SYNTHETIC on a fixture, bash 3.2 + BSD tools):**
* `files.tsv`: for every regular file under `source/ state/ identity/` and `README.txt` (excluding `manifest/`, `RECEIVING-*`, `SEALED-*`), one line `relative-path<TAB>size<TAB>sha256`, `LC_ALL=C sort`ed. **`MANIFEST_HASH = sha256(files.tsv)`.** `FILE_COUNT` = lines; `BYTE_COUNT` = sum of sizes.
* **Source** computes it over its **sealed local generation**. **Destination** independently recomputes it over the received directory with the identical command. **Success requires** `SOURCE_MANIFEST_HASH == DEST_MANIFEST_HASH`, equal `FILE_COUNT` and `BYTE_COUNT`, zero extra/missing files.
* **Salted challenge (defence against stale or replayed evidence):** after `TRANSFER_COMPLETE_*`, the source picks N (default 4) sample paths *unknown to the destination in advance* — at least one large state file and one small file — and a fresh random `NONCE`; the destination answers `D_i = sha256(NONCE ‖ file bytes)`; the source computes the same on its sealed copy. A destination cannot answer without the bytes present *now*.
* **What travels through the operator:** `MANIFEST_HASH`, `FILE_COUNT`, `BYTE_COUNT`, `NONCE`, ≤ 8 digests, validation hash/status, exceptions. **Never thousands of hashes** unless troubleshooting (then paste `files.tsv` diff summaries, never contents).
* **No transitive trust:** CLAUDE-M5 accepts a verification only if it can **recompute or compare the value itself** (source side: compares reported hashes to its own; destination side: recomputes on the received bytes). "CLAUDE-INTEL says it verified" is logged as a claim, never as evidence. The destination seals only after receiving the source's `HASH_VERDICT: MATCH`.
```bash
# RUN ON EITHER MACHINE over a generation directory GEN (read-only; identical command on both sides)
mk_manifest() { ( cd "$1" && LC_ALL=C find source state identity README.txt -type f -print | LC_ALL=C sort | while IFS= read -r f; do printf '%s\t%s\t%s\n' "$f" "$(stat -f %z "$f")" "$(shasum -a 256 < "$f" | cut -d' ' -f1)"; done ); }
# $OUT is a NEW directory under _REPORTS/ — never manifest/, which would overwrite the source's own copy
mk_manifest "$GEN" > "$OUT/files.tsv"; shasum -a 256 < "$OUT/files.tsv"      # = MANIFEST_HASH
sd() { ( printf '%s' "$NONCE"; cat "$1" ) | shasum -a 256 | cut -d' ' -f1; }   # salted digest of one file
```

---

## 12. Claude-to-Claude handshake (state machine)
Two Claude Code sessions, **CLAUDE-M5** and **CLAUDE-INTEL**, exchange only operator-copied text. Every message uses the fixed format of §20 (banner, mandatory header, step fields, `MSG_CRC`, `END RELAY`). A receiver **must**: (1) verify the CRC and the secret lint (`relay_check`); (2) check `MACHINE_ID16` equals the pinned value (first contact pins it, and the operator confirms the label↔machine binding); (3) check `SEQ` is exactly the last seen + 1 for that sender and `REPLY_TO` names a real message; (4) check the step is a legal successor (`relay_transition_ok`); (5) check `DIRECTION` and `GEN` are unchanged within a transfer; (6) validate any path field against the regex; (7) never act on a message that fails any check — reply `ABORT` or `STATUS: ERROR` instead.

**Steps** (SRC = the machine whose lineage is being backed up; DST = the machine receiving it):
| # | Step | Sender | Meaning / required content | Legal next |
|---|---|---|---|---|
| 1 | `DISCOVERY_REQUEST` | either | asks for Phase-A facts; carries the script name + SHA-256 | DISCOVERY_RESPONSE |
| 2 | `DISCOVERY_RESPONSE` | either | identity tuple, fingerprints, sizes, git facts, capacity, tools, other-material count, report hash | DISCOVERY_RESPONSE (the peer's), DIRECTION_PROPOSAL, SOURCE_MANIFEST_OFFER |
| 3 | `DIRECTION_PROPOSAL` | M5 (informational) | first direction + reasons + reversal evidence | SOURCE_MANIFEST_OFFER |
| 4 | `SOURCE_MANIFEST_OFFER` | SRC | **read-only plan**: hash of the sorted path list, estimated counts/bytes, mutable-file count, tools hash, required free bytes | DESTINATION_CAPACITY_ACCEPT |
| 5 | `DESTINATION_CAPACITY_ACCEPT` | DST | free/total bytes, independently computed requirement, post-transfer free, destination path (regex-checked), exists?, FileVault, Remote Login, host-key fingerprint, ACCEPT/REJECT | TRANSFER_PLAN |
| 6 | `TRANSFER_PLAN` | SRC | transport, topology, list hash, paths, hash of the exact command text | TRANSFER_AUTHORIZATION_REQUIRED |
| 7 | `TRANSFER_AUTHORIZATION_REQUIRED` | both | the exact phrase the human must type **into this session**; `STATUS: BLOCKED` | AUTHORIZATION_ACK |
| 8 | `AUTHORIZATION_ACK` | both | SHA-256 prefix of the phrase received **directly from the human** by *this* session | AUTHORIZATION_ACK, TRANSFER_COMPLETE_SOURCE |
| 9 | `TRANSFER_COMPLETE_SOURCE` | SRC | local generation sealed, source `MANIFEST_HASH`, counts, level, exit status | TRANSFER_COMPLETE_DESTINATION |
| 10 | `TRANSFER_COMPLETE_DESTINATION` | DST | exit status, independently computed `DEST_MANIFEST_HASH`, counts, extra/missing, free after | HASH_CHALLENGE |
| 11 | `HASH_CHALLENGE` | SRC | nonce + rule + sample paths | HASH_CONFIRM |
| 12 | `HASH_CONFIRM` | DST | echoed nonce + salted digests | HASH_VERDICT |
| 13 | `HASH_VERDICT` | SRC | both hashes seen, match flags, `VERDICT: MATCH|MISMATCH` | STRUCTURAL_VALIDATION |
| 14 | `STRUCTURAL_VALIDATION` | DST | validation hash, PASSED, checks run / **not run (with reasons)**, failures | GENERATION_SEALED |
| 15 | `GENERATION_SEALED` | DST | seal hash, marker name, level, permissions, registry-line hash | SECOND_DIRECTION_READY |
| 16 | `SECOND_DIRECTION_READY` | either | this direction's status + the other's; next action | DISCOVERY_REQUEST (fresh, for the reverse direction) |
| — | `ABORT` | either | reason, that direction's status, what was left behind (never deleted) | terminal **for that direction only** |

```
DISCOVERY_REQUEST → DISCOVERY_RESPONSE ⇄ (both machines) → [DIRECTION_PROPOSAL] → SOURCE_MANIFEST_OFFER → DESTINATION_CAPACITY_ACCEPT → TRANSFER_PLAN
   → TRANSFER_AUTHORIZATION_REQUIRED ══ HUMAN GATE (phrase typed into EACH session) ══ AUTHORIZATION_ACK (×2)
   → TRANSFER_COMPLETE_SOURCE → TRANSFER_COMPLETE_DESTINATION → HASH_CHALLENGE → HASH_CONFIRM → HASH_VERDICT
   → STRUCTURAL_VALIDATION → GENERATION_SEALED → SECOND_DIRECTION_READY → (fresh DISCOVERY for the reverse direction)
```
The machine-readable transition table is `x-transitions` in the schema and `relay_transition_ok` in `fe_relay.sh` (TESTED-SYNTHETIC: `TRANSFER_PLAN → TRANSFER_COMPLETE_SOURCE` and `TRANSFER_AUTHORIZATION_REQUIRED → TRANSFER_COMPLETE_SOURCE` are **denied**; `X → ABORT` is allowed from anywhere). **There is no edge that bypasses the human gate.** Each direction keeps its own `SEQ`, `GEN`, and status variables; a message for one direction never advances the other. Timeouts do not exist: silence means waiting, never retrying and never proceeding.

---

## 13. Human authorization gates
**The operator is the only authority for a write or a transfer.** Claude may inspect, calculate, hash, design and verify. Claude may **not** infer authorization from "continue", from a prior approval, from a successful discovery, from free disk space, or from the other Claude's readiness.

**Gate G1 — the transfer authorization phrase.** Canonical form (ASCII arrow; the Unicode `→` is accepted as identical):

`AUTHORIZE M5 -> INTEL GENERATION G001 LISTHASH <8 hex>`   or   `AUTHORIZE INTEL -> M5 GENERATION G001 LISTHASH <8 hex>`

The 8 hex characters are the first 8 of `SOURCE_LIST_HASH` from the `SOURCE_MANIFEST_OFFER` — so a phrase authorizes *this direction, this generation number, this exact list of files*, and nothing else; a phrase copied from an earlier attempt is void. Both Claudes display the exact expected phrase in `TRANSFER_AUTHORIZATION_REQUIRED`. To unlock a destination with FileVault Off the phrase must end with ` UNENCRYPTED-OK`.
**Delivery rule:** the human types the phrase **into each session directly**; a phrase relayed *through* the other Claude is not accepted (it would make one Claude vouch for the human). Each Claude answers with `AUTHORIZATION_ACK` carrying the SHA-256 prefix of what it received; the peer recomputes the expected hash — a mismatch is `ABORT`.
**What G1 authorizes (exactly):** (a) the source creating `OWN_LOCAL/<gen>` and sealing it; (b) the destination creating `FROM_<lineage>/<gen>` with a `RECEIVING-*` marker; (c) the single SSH+tar operation whose command text hashes to `TRANSFER_PLAN_HASH`; (d) the destination's recomputation, validation and sealing. **Nothing else** — not the reverse direction, not a retry, not the ancestral series, not deleting anything, not changing Remote Login (the operator does that).
**Other gates:** G0 — *any* command that writes on a machine is forbidden until the operator explicitly instructs it: Phase A–D are read-only (the plan manifest is computed in memory and printed); Phase C′ scratch rehearsal needs its own explicit instruction naming a scratch directory outside every FeralEcho tree; nothing may ever write into a live FeralEcho directory; G2 — enabling Remote Login on Intel and adding an SSH key are operator actions announced in `TRANSFER_PLAN`; G3 — the reverse direction needs its **own** G1 with its own phrase; G4 — restore (§16) needs its own approvals; G5 — the ancestral series needs its own G1.
**Single use:** a phrase is valid for one attempt; `ABORT`, a mismatch, or a retry voids it.

---

## 14. Structural validation (on copies, never on production)
Runs on the **destination's received generation** (and on the source's local generation before it is offered), **before** sealing; results are written to a *new* directory under `_REPORTS/` and copied into the unsealed generation's `manifest/` only before the seal — **nothing is ever written into a sealed generation.**
Where the tool exists, each is run in a jail (`sandbox-exec`, write-deny except `/dev/null`, network-deny, `python -I`, no FeralEcho imports; TESTED-SYNTHETIC in the preceding plan): JSON parse; JSONL line structure (≤ 1 invalid final line tolerated); **pickle readability via `pickletools.genops`** (walks to `STOP`; never imports a module or executes code); SQLite `PRAGMA integrity_check` via `mode=ro&immutable=1`; **FAISS `ntotal` vs metadata entry count** (M5 layout: `memory/faiss.index` vs `memory/memory_meta.json`; Intel layout UNKNOWN until traced); `git bundle verify`; `git fsck` on a *clone of the bundle* in a scratch directory; presence of the expected source files and persistence artifacts from the manifest; size/count floors (M5 lineage floors from the earlier plan; Intel floors set from Intel's own discovery). Checks whose tool is missing (e.g. no interpreter with `faiss` on Intel) are reported **`CHECKS_NOT_RUN` with the reason** and cap the sealed level accordingly — never silently passed. A validation failure ⇒ marker `QUARANTINED-NOT-KNOWN-GOOD`; the generation is **kept**, never counted as a recovery copy.

---

## 15. Cross-architecture analysis
| Artifact | Class | Why / risk |
|---|---|---|
| Python source, `Modelfile`, `.md`, `.json`, `.jsonl`, logs, `.txt`, `.gz` | **ARCHITECTURE-INDEPENDENT** | text/bytes |
| `.git` directory, `git bundle` | **ARCHITECTURE-INDEPENDENT** | Git formats are endian/arch neutral |
| SQLite (`optuna.db`) | **ARCHITECTURE-INDEPENDENT** | portable file format (Optuna schema version must match to *use* it) |
| `.npy` | **ARCHITECTURE-INDEPENDENT (data)** | both arm64 and x86_64 are little-endian; needs a compatible numpy to read |
| `faiss.index` | **LIKELY PORTABLE** | FAISS CPU index serialization is byte-order/arch independent; index type and FAISS version compatibility **UNKNOWN** — validate by `read_index` on the copy |
| Pickles (`river_brain.pkl`, `task_type_classifier.pkl`, `drift_detectors.pkl`) | **LIKELY PORTABLE (data) / executability UNKNOWN** | the byte stream is portable, but unpickling requires the *same classes and compatible* numpy/scikit-learn/river versions; a different environment can fail to load or warn — data is recoverable, direct loading is not guaranteed |
| Conda envs, virtualenvs, compiled `.so`/`.dylib`, `__pycache__` | **ARCHITECTURE-DEPENDENT** | arm64 vs x86_64 binaries; rebuilt from `pip_freeze.txt`, never copied to run |
| MLX models and the `mlx`/Metal path (`mlx:qwen3`, `mlx:gemma3`) | **ARCHITECTURE-DEPENDENT (Apple silicon only)** | an Intel restore of the M5 lineage has **no MLX** — councillors and model-pool composition differ |
| Ollama runtime binary and its on-disk state | **ARCHITECTURE-DEPENDENT (runtime); weights GGUF portable** | weights not copied by default (§5.5); runtime rebuilt per arch |
| HuggingFace/SentenceTransformer cache | **LIKELY PORTABLE** | safetensors + tokenizer files; torch/`transformers` versions matter |
| Anything found only on Intel (`ARK_MODE` variants, other layouts) | **UNKNOWN** | classified by Intel's own tracing |

**Two separate recovery claims, never conflated:** **DATA RECOVERY** (the bytes and their structure survive and are loadable *somewhere*) versus **DIRECT EXECUTABILITY** (the restored tree runs unchanged on the other architecture). The plan guarantees only the first; the second requires a rebuilt environment and is tested in staging (§16).

---

## 16. Restore design (never automatic; **not executed here**)
Two independent procedures; each requires explicit human approval at every consequential step and uses **only sealed, cold-verified generations**.
### 16.1 Restore the M5 lineage from Intel (`FROM_M5/M5_…_Gnnn` on Intel → M5)
### 16.2 Restore the Intel lineage from M5 (`FROM_INTEL/INTEL_…_Gnnn` on M5 → Intel)
Common steps (R0–R11):
* **R0 Scope & identity.** State whether the goal is one file, the state set, the source, or the whole lineage. Read `identity/lineage.txt`; confirm **lineage label, `MACHINE_ID16` of the origin, `GIT_HEAD`, `WORKTREE_FINGERPRINT_V1`, `STATE_LAYOUT_FP_V1`** are what the operator expects **for the target lineage**. A generation of lineage X is *never* a candidate for lineage Y's target.
* **R1 Verify the generation:** `SEAL` cold-verify and manifest recomputation (§11); marker must be `SEALED-*` at `VERIFIED-LIVE` or better; a `QUARANTINED` generation is evidence, not a restore source.
* **R2 Verify the target machine:** `ARCH_TRUE`, OS, free space (capacity rule §6), Ollama state; **record architecture differences** (§15) in the restore notes.
* **R3 Preserve what survives:** make a fresh sealed local generation of whatever is left on the target (label `PRE-RESTORE`) — even if it looks corrupt.
* **R4 Stop the relevant server cleanly** via the project's watchdog-aware path (never `kill -9`, never a raw kill against the watchdog) — **only with explicit approval**.
* **R5 Restore into staging first:** extract into a NEW directory outside every live tree; never into the live path.
* **R6 Validate the staging copy** (§14) and, for data recovery, stop here if that is the goal.
* **R7 Executability trial (only if wanted):** build a fresh interpreter environment from `identity/pip_freeze.txt` on the target architecture, run read-only load checks against the staging copy, note every divergence (MLX absent on Intel; pickle/numpy warnings; FAISS version).
* **R8 Git:** recover history by cloning `git/repo.bundle` into a scratch directory and comparing `HEAD`; if a copied linked worktree is restored to a new path, `git -C <root> worktree repair <path>` from the restored root (TESTED-SYNTHETIC earlier: it rewrites only the restored copy's pointers).
* **R9 Promote (separate approval):** replacing the target's *own-lineage* live files with the staging copy — order: source/Git → non-pair state → meta then FAISS from the **same** generation → pickles last; permissions from `manifest/stat.tsv`; never restore `echo_server.pid` or `echo_sentinel.json`.
* **R10 Start via the normal watchdog path; compare counts** (RiverBrain observations, FAISS `ntotal`, meta count, garden lines) with the manifest; record the outcome as an append-only registry line.
* **R11 Never a merge:** if the target still has surviving state, it is preserved in R3 and **replaced**, not combined; no tool in this plan can union two states.
A `RESTORE-ALERT` in a log, a health warning, or a failed liveness check is **never** a trigger for restoration.

---

## 17. Failure-mode analysis
| # | Scenario | Why the procedure fails safe |
|---|---|---|
| 1 | **M5 SSD dies** | `FROM_M5/M5_…` generations on Intel survive; restore is §16.1 into staging on a new/repaired machine; nothing on Intel was ever a mirror of live M5 state, so no corruption arrived |
| 2 | **Intel SSD dies** | mirror image: `FROM_INTEL/` on M5; the M5 is unaffected because nothing on it ever depended on Intel |
| 3 | **M5 state silently corrupts before backup** | earlier generations are independent and untouched; the new generation is validated (§14) — floors/pair alignment trip ⇒ `QUARANTINED`; an *undetectable* semantic corruption is copied faithfully — **stated limit**; the older sealed generations are the defence |
| 4 | **Intel state silently corrupts before backup** | same, with Intel floors derived from its own discovery; unknown layout ⇒ fewer automatic checks ⇒ lower sealed level (`CHECKS_NOT_RUN`) |
| 5 | **Transfer interrupted** | `set -o pipefail`, non-zero status reported; destination has `RECEIVING-*` and no `SEALED-*` ⇒ `ABANDONED-*`, partial preserved, next attempt is `G002`; source generation unaffected |
| 6 | **Destination fills mid-transfer** | capacity rule (2× + 10 GiB, post ≥ 20 GiB/15 %) checked before and after; `tar -x` fails visibly with ENOSPC; partial preserved; the 15 % floor keeps the startup volume from filling |
| 7 | **One Claude gives incorrect path information** | destination path must match the strict regex and not lie under a live root; pre-flight requires the directory to exist and be empty except `RECEIVING-*`; source uses only regex-validated values; the destination re-checks its own path |
| 8 | **Both machines have identical hostnames** | hostname is never identity; `MACHINE_ID16`/`HW_ID16`/`ARCH_TRUE`/`HW_MODEL` are pinned at first contact and required in every header; mismatch ⇒ `ABORT` |
| 9 | **A backup generation already exists** | `mkdir` (no `-p`) fails; `generations.log` collision refused; `tar -k` never overwrites; the emptiness pre-flight stops before any byte moves; number is never reused |
| 10 | **A malicious/accidental `--delete` appears in a command** | no command in the plan contains it (§22 lint with positive controls); `tar` has no such option; a receiving command that differs from `TRANSFER_PLAN_HASH` is refused; even if it ran, the destination is a *new empty directory* holding no other lineage data |
| 11 | **A `.env` secret would be printed into relay text** | `relay_check` lint rejects token shapes, dotenv shapes, hex/opaque runs and secret-named fields; `ENV_FILE` grammar is strict; discovery never reads `.env` values (0 leaks on the real file) |
| 12 | **The wrong lineage is selected for restore** | lineage label + `MACHINE_ID16` + `GIT_HEAD` + fingerprints in `identity/lineage.txt` must match the operator's stated target; restore is staging-first, never over live state; a generation of lineage X cannot be promoted into lineage Y's tree by any step |
| 13 | Operator copies a message incorrectly | `MSG_CRC` (8 hex over all preceding lines) detects any edit (TESTED-SYNTHETIC: one changed character fails) |
| 14 | A Claude reports "verified" without evidence | not accepted (§11): recomputation or nonce-salted digest required; sealing waits for `HASH_VERDICT: MATCH` |
| 15 | One direction fails | independent state machines; no rollback, deletion, overwrite, or automatic retry of the other; each has its own status (§12) |
| 16 | Discovery on Intel shows an unexpected live instance elsewhere | classified LIVE/POSSIBLE_LIVE, reported, **preserved**; the plan STOPs at `BLOCKED` until the operator chooses the primary root |
| 17 | The server aborts and restarts mid-staging (Metal `SIGABRT` ≈ 2/day on M5) | PID/start recorded before/after; a change caps the level at `RESCUE-LIVE` and is reported; nothing is stopped or "fixed" |
| 18 | SSH host impersonation on the network | fingerprint relayed and compared by the operator; `StrictHostKeyChecking=yes`; tailnet transport |

---

## 18. Future external-vault compatibility
A future external SSD becomes a **third physical copy**, never a sync master. Generation directories are already self-contained and lineage-named, so the vault is a byte-copy of them:
```
FERALECHO_VAULT/
  M5/generations/     M5_2026-09-20_G001/ …     (source: M5 OWN_LOCAL and Intel FROM_M5)
  INTEL/generations/  INTEL_2026-09-20_G001/ …  (source: Intel OWN_LOCAL and M5 FROM_INTEL)
  vault.log           append-only registry
```
Copying uses the same one-way tar stream + cold verification (`SEAL` re-hash, manifest recomputation), created with plain `mkdir`, no overwrite, no delete. **No restructuring is required** — the layout in §7 already separates lineages by name and by directory. Retention rule carried over: **no generation may be deleted until at least two other verified recovery copies exist on physically distinct storage.** The vault is written only by an authorized copy step and is disconnected between uses.

---

## 19. Backup cadence (conservative)
| Trigger | M5 lineage | Intel lineage |
|---|---|---|
| **Milestone generation** (immediate) | before/after any risky operation, protocol freeze, code milestone, before any restore or environment change | before any change to that machine, and once now (first generation) |
| **Periodic** | weekly until the vault exists and cadence is proven; daily thereafter | **once now**, then only when the discovery fingerprints change (`WORKTREE_FINGERPRINT_V1` / `STATE_LAYOUT_FP_V1` / `MEMORY_KB`) — at most monthly if nothing changes |
| Rate of change (OBSERVED M5) | state grows continuously (logs ≈ MB/day; FAISS/meta ~26 persists/h); commits arrive in bursts | **UNKNOWN** — measured from Intel discovery |
| Space (M5 at ≈1.6 GB/generation) | 52 weekly ≈ 83 GB/yr; daily ≈ 580 GB/yr (needs the vault) | UNKNOWN; **never exceed the capacity rule** |
**Never delete automatically.** A capacity alarm at 70 % volume use blocks new generations and asks the operator; deletion, if ever chosen, is a manual human act under the two-other-copies rule. Each machine holds each generation twice (source `OWN_LOCAL` + peer `FROM_*`) — the formula is `bytes_used ≈ 2 × generations × size`. The ancestral series `A001` is once-only.

---

## 20. Relay message templates
**Format rules.** Plain text, `KEY: value`, one per line, fixed order, values ≤ 300 chars, **no secrets, no file contents**. Line 1 is the banner; the last two lines are `MSG_CRC: <8 hex>` and `END RELAY`. `MSG_CRC` = first 8 hex of sha256 over every preceding line (newline-terminated) — computed with `relay_seal`, verified with `relay_check` (Appendix B). Placeholders are `<angle brackets>`. **Every header field is mandatory in every message:** `MACHINE`, `LINEAGE`, `MACHINE_ID16`, `TO`, `SEQ`, `REPLY_TO`, `STEP`, `DIRECTION`, `GEN`, `GIT_HEAD`, `WORKTREE`, `FERALECHO_ROOT`, `SERVER`, `BACKUP_STATUS` (+ `STATUS`, `NOTES` at the end).

**Header block (identical in every message):**
```text
FERALECHO CROSS-BACKUP RELAY v1
MACHINE: <M5|INTEL>
LINEAGE: <FERALECHO-M5|FERALECHO-INTEL-2020>
MACHINE_ID16: <16 hex, pinned at first contact>
TO: <M5|INTEL|OPERATOR>
SEQ: <n, sender-monotonic>
REPLY_TO: <peer SEQ|NONE>
STEP: <see below>
DIRECTION: <NONE|M5->INTEL|INTEL->M5>
GEN: <NONE|M5_YYYY-MM-DD_Gnnn|INTEL_YYYY-MM-DD_Gnnn>
GIT_HEAD: <40 hex|NONE|UNKNOWN>
WORKTREE: <CLEAN|DIRTY m=<n> u=<n>|NOT_A_REPO|UNKNOWN>
FERALECHO_ROOT: <absolute path|UNKNOWN>
SERVER: <RUNNING pid=<n> start=<ISO>|STOPPED|UNKNOWN>
BACKUP_STATUS: <NONE|OWN_LOCAL:<id>:<state>; FROM_<x>:<id>:<state>>
<step-specific fields below>
STATUS: <READY|BLOCKED|INFO|ERROR>
NOTES: <≤ 300 chars, no secrets>
MSG_CRC: <8 hex>
END RELAY
```
**Step-specific fields** (generated from the same table as the JSON Schema; each of the 17 steps was rendered with example values, sealed, checked by `relay_check` and validated against the schema — 17/17 pass, plus a negative control):
| Step | Sender | Step-specific fields (in order) |
|---|---|---|
| `DISCOVERY_REQUEST` | either | `SCRIPT_NAME`, `SCRIPT_SHA256`, `REQUIRE` |
| `DISCOVERY_RESPONSE` | either | `ARCH_TRUE`, `ROSETTA_TRANSLATED`, `HW_MODEL`, `OS`, `HW_ID16`, `WORKTREE_FINGERPRINT`, `STATE_LAYOUT_FP`, `ROOT_CLASS`, `REPO_BYTES`, `GITDIR_BYTES`, `MEMORY_BYTES`, `DATA_BYTES`, `SOURCE_BYTES`, `STATE_BYTES`, `PROPOSED_BACKUP_BYTES`, `HOME_FREE_BYTES`, `HOME_TOTAL_BYTES`, `ENV_FILE`, `GIT_UNPUSHED`, `TRACKED_MODIFIED`, `UNTRACKED`, `OTHER_MATERIAL`, `SMART`, `FILEVAULT`, `TOOLS_OK`, `OLLAMA_MODELS`, `REPORT_HASH` |
| `DIRECTION_PROPOSAL` | M5 (or either) | `FIRST_DIRECTION`, `REASONS`, `REVERSAL_EVIDENCE` |
| `SOURCE_MANIFEST_OFFER` | SRC | `SOURCE_LIST_HASH`, `FILE_COUNT_EST`, `BYTE_COUNT_EST`, `SOURCE_PART_BYTES`, `STATE_PART_BYTES`, `MUTABLE_FILE_COUNT`, `TOOLS_HASH`, `REQUIRED_FREE_BYTES` |
| `DESTINATION_CAPACITY_ACCEPT` | DST | `FREE_DEST_BYTES`, `VOLUME_TOTAL_BYTES`, `REQUIRED_FREE_BYTES`, `POST_TRANSFER_FREE_BYTES`, `MARGIN_RULE`, `DEST_PATH`, `DEST_EXISTS`, `DEST_FILEVAULT`, `REMOTE_LOGIN`, `HOSTKEY_FP`, `DECISION` |
| `TRANSFER_PLAN` | SRC | `TRANSPORT`, `TOPOLOGY`, `SOURCE_LIST_HASH`, `DEST_PATH`, `SRC_LOCAL_GEN_PATH`, `TRANSFER_PLAN_HASH`, `EXPECTED_FILE_COUNT`, `EXPECTED_BYTE_COUNT` |
| `TRANSFER_AUTHORIZATION_REQUIRED` | both (each, independently) | `REQUIRED_PHRASE`, `PHRASE_SHA16`, `GATE` |
| `AUTHORIZATION_ACK` | both (each, after the human types the phrase into ITS OWN session) | `AUTH_PHRASE_SHA16`, `AUTH_CHANNEL`, `AUTH_UTC` |
| `TRANSFER_COMPLETE_SOURCE` | SRC | `EXIT_STATUS`, `SOURCE_MANIFEST_HASH`, `FILE_COUNT`, `BYTE_COUNT`, `CONSISTENCY_LEVEL`, `LIVE_MUTATED_COUNT`, `LOCAL_GEN_SEALED` |
| `TRANSFER_COMPLETE_DESTINATION` | DST | `EXIT_STATUS`, `DEST_MANIFEST_HASH`, `FILE_COUNT`, `BYTE_COUNT`, `EXTRA_OR_MISSING`, `FREE_DEST_BYTES_AFTER` |
| `HASH_CHALLENGE` | SRC | `NONCE`, `CHALLENGE_RULE`, `SAMPLE_COUNT`, `SAMPLE_PATHS` |
| `HASH_CONFIRM` | DST | `NONCE`, `D1`, `D2`, `D3`, `D4` |
| `HASH_VERDICT` | SRC | `SOURCE_MANIFEST_HASH`, `DEST_MANIFEST_HASH_SEEN`, `MANIFEST_MATCH`, `FILE_COUNT_MATCH`, `BYTE_COUNT_MATCH`, `CHALLENGE_MATCH`, `VERDICT` |
| `STRUCTURAL_VALIDATION` | DST | `VALIDATION_HASH`, `PASSED`, `CHECKS_RUN`, `CHECKS_NOT_RUN`, `FAILURES`, `PAIR_ALIGNED` |
| `GENERATION_SEALED` | DST | `DEST_SEAL_HASH`, `MARKER`, `CONSISTENCY_LEVEL`, `PERMISSIONS`, `REGISTRY_LINE_HASH` |
| `SECOND_DIRECTION_READY` | either | `THIS_DIRECTION_STATUS`, `OTHER_DIRECTION_STATUS`, `NEXT` |
| `ABORT` | either | `REASON`, `DIRECTION_STATUS`, `LEFT_BEHIND` |


**One complete validated example** (`SOURCE_MANIFEST_OFFER`; **example values, not real data**):
```text
FERALECHO CROSS-BACKUP RELAY v1
MACHINE: M5
LINEAGE: FERALECHO-M5
MACHINE_ID16: dd7643e652db2d2c
TO: INTEL
SEQ: 1
REPLY_TO: NONE
STEP: SOURCE_MANIFEST_OFFER
DIRECTION: M5->INTEL
GEN: M5_2026-09-20_G001
GIT_HEAD: 2fba42644c82b9f7096276f4dd338d615cf1bcce
WORKTREE: DIRTY m=27 u=223
FERALECHO_ROOT: /Users/example/Desktop/FeralEcho
SERVER: RUNNING pid=1234 start=2026-09-20T07:30:10
BACKUP_STATUS: NONE
SOURCE_LIST_HASH: 4444444444444444444444444444444444444444444444444444444444444444
FILE_COUNT_EST: 22803
BYTE_COUNT_EST: 1592293851
SOURCE_PART_BYTES: 306558978
STATE_PART_BYTES: 1285734873
MUTABLE_FILE_COUNT: 31
TOOLS_HASH: 5555555555555555555555555555555555555555555555555555555555555555
REQUIRED_FREE_BYTES: 13184587702
STATUS: READY
NOTES: EXAMPLE - NOT REAL DATA
MSG_CRC: 7a51fabc
END RELAY
```

---

## 21. Future execution runbook (DESIGN ONLY)
Every phase names its actor, its writes (if any), its exit evidence, and its gate. **No phase advances silently past a human gate.** `[R]` = read-only, `[W]` = writes something (only after G1).

**PHASE A — Independent discovery `[R]`.** *M5:* done (§0.3) — refresh right before Phase D (state drifts). *Intel:* the operator pastes the first relay message (§23) into CLAUDE-INTEL; it runs the discovery script (stdout only) and answers with `DISCOVERY_RESPONSE`. Exit: both responses carry an identity tuple, fingerprints, sizes, capacity, other-material report. **Gate:** none (read-only).
**PHASE B — Exchange identity and capacity summaries `[R]`.** Both Claudes exchange `DISCOVERY_RESPONSE`, pin `MACHINE_ID16`s, and the operator confirms label↔machine binding. Exit: every §"answer 1" field present; any `UNKNOWN` capacity ⇒ that direction `BLOCKED`.
**PHASE C — Choose the first direction `[R]`.** CLAUDE-M5 issues `DIRECTION_PROPOSAL`; the **operator decides**. Evidence table:
| Factor | Points to M5→Intel first | Could reverse to Intel→M5 first |
|---|---|---|
| Source fragility | M5's SSD is the only verified home of the current lineage and of all work since 2026-09-05 (17 unpushed commits, 27+223 files, ≈ 1.3 GB state); server aborts ≈ 2/day | Intel `SMART Status` **Failing/degraded**, a failing/full/old disk, or evidence that Intel's lineage is unique and unbacked-up |
| Destination capacity | Intel reports ≥ `REQUIRED_FREE` and the 15 % floor | Intel **cannot** hold an M5 generation (then M5→Intel is `BLOCKED`); the M5 can always hold Intel's (≈ 754 GB free) |
| Backup availability | M5 has **no off-disk copy** (the 2026-09-05 zip is the same SSD) | an external-vault copy of the M5 lineage lands first (removes the urgency) |
| Server activity | both may run; neither is stopped — not decisive | a violent state change on Intel (unexpected LIVE instance) |
| Irreplaceable state | M5 B1 ≈ 302 MiB irreplaceable/expensive + source | Intel holds unique older-lineage state with no other copy |
| Discovery completeness | — | if Intel discovery is ambiguous (multiple roots, unclassified material) that direction waits regardless |
**Presumption:** **M5→Intel first**, *provided* Intel discovery shows a healthy disk with enough space; otherwise Intel→M5 first. Not assumed until Phase B completes.
**PHASE C′ — Tool readiness (prerequisite of Phase E) `[writes only to an operator-designated scratch directory; needs its own explicit instruction to each Claude]`.** Build and rehearse the "v2" tools on **synthetic fixtures** on **both** machines: the `source/ state/ identity/ manifest/ README` layout adaptation of the earlier tested tooling; ID/lineage fields; `OWN_LOCAL` sealing; `mk_manifest`/challenge/verdict; receive-side prepare/verify/seal; jail validators; `fe_relay.sh`. Exit: hashes of the tool files agreed between the Claudes (`TOOLS_HASH`); rehearsal transcript reviewed by the operator. **Not done in this mission.**
**PHASE D — Generate the source plan manifest `[R]`.** SRC computes, **in memory**, the sorted path list (`SOURCE_LIST_HASH`), estimated counts/bytes, tiering and the mutable-file list, and sends `SOURCE_MANIFEST_OFFER`. DST replies `DESTINATION_CAPACITY_ACCEPT` (independent capacity computation, regex-checked path, FileVault, Remote Login, host-key fingerprint). SRC sends `TRANSFER_PLAN` (command text hash) and both send `TRANSFER_AUTHORIZATION_REQUIRED`.
**PHASE E — HUMAN AUTHORIZATION ═ GATE G1.** The operator types `AUTHORIZE <DIR> GENERATION G001 LISTHASH <8hex>` **into each session**; each answers `AUTHORIZATION_ACK`. Operator actions announced in `TRANSFER_PLAN` (enable Remote Login on Intel, install the dedicated key or be ready to type the password) happen now. **Nothing before this gate wrote to any live directory or to `FeralEcho_Cross_Backups`; Phase C′, if run, wrote only to a scratch directory the operator explicitly designated.**
**PHASE F — One-way transfer `[W]`.** F0 SRC creates and seals `OWN_LOCAL/<gen>` (per-file rules, `RESCUE-LIVE`/`VERIFIED-LIVE`), reports `TRANSFER_COMPLETE_SOURCE` fields; F1 DST creates `FROM_<x>/<gen>` + `RECEIVING-*`; F2 SRC pre-flight (empty-directory test, `df`), then the tar stream (§8). Exit: exit statuses recorded.
**PHASE G — Destination manifest `[R]`.** DST computes `DEST_MANIFEST_HASH`, counts, extra/missing, `df` after → `TRANSFER_COMPLETE_DESTINATION`.
**PHASE H — Cross-verify `[R]`.** `HASH_CHALLENGE` → `HASH_CONFIRM` → `HASH_VERDICT`. Exit: `MATCH` on manifest hash, counts, and salted digests — each side comparing against values **it computed itself**.
**PHASE I — Structural validation `[R]`.** DST validates the received copy in the jail (§14); reports `STRUCTURAL_VALIDATION` including `CHECKS_NOT_RUN`.
**PHASE J — Seal `[W]`.** DST sets `source/.env` to 0600 in the copy, `chmod -R a-w` (optional `chflags uchg`), creates `SEALED-<manifest8>`, appends the registry line, sends `GENERATION_SEALED`. Failure ⇒ `QUARANTINED-…` marker (kept) and that direction ends.
**PHASE K — Repeat independently in reverse.** A fresh Phase A/B refresh, its own Phase C decision, its **own G1 phrase**, own generation number. The first direction's outcome is never an input except as status.
**PHASE L — Future restore drill.** Restore into a scratch directory on each machine, validate, compare with the manifest (§16, R0–R6 only). Record `RESTORE-TESTED` append-only. Separate approval.

---

## 22. Command-safety audit
**Forbidden in the cross-backup execution path:** `rm` · `--delete` · `git clean` · `git reset` · `git restore` · `git checkout` · `git stash` (mutating) · force push · disk formatting · `mv` of source state · recursive overwrite of an existing generation · automatic bidirectional sync (plus `rsync`, `sudo`, `kill`, and any git verb that writes).
**Design responses:** destinations are always *new* directories created by plain `mkdir`; extraction uses `tar -k` behind an emptiness pre-flight; sealing uses `chmod`/marker files instead of renames; abandonment is a marker file, not a move or delete; the registry is append-only (`>>`); read-only scripts contain no redirect except to `/dev/null`.
**Machine lint** (run when this file was generated; regexes below; the scanner has positive controls so a blind scanner would fail the generation):
Scanner self-check: 160 lines of read-only scripts, 28 lines of runbook fences scanned; positive controls (a synthetic `echo x > /tmp/f`, `mkdir -p`, `git push`; and `ssh`, `tar -cf`, `mkdir`, `shasum` present in the runbook fences) behaved correctly, so the scanners are not blind.

**Scope 1 — the read-only scripts `fe_discover.sh` and `fe_relay.sh` (must contain none of these):**

| Pattern | Hits |
|---|---:|
| mkdir | 0 |
| touch | 0 |
| tee | 0 |
| cp | 0 |
| mv | 0 |
| rm | 0 |
| chmod/chown | 0 |
| sed -i | 0 |
| truncate/dd | 0 |
| git write verbs | 0 |
| sudo | 0 |
| kill | 0 |
| ssh/scp invoked as a command, or curl to a non-loopback URL | 0 |
| redirects to anything other than `/dev/null`/`&1` (fe_discover.sh) | 0 |
| redirects to anything other than `/dev/null`/`&1` (fe_relay.sh) | 0 |

(Independent runtime evidence for Scope 1: the kill-on-violation jail run of §0.3.)

**Scope 2 — every ```` ```bash ```` fence in this plan (the execution path):**

| Forbidden pattern | Hits |
|---|---:|
| rm | 0 |
| --delete | 0 |
| mv | 0 |
| git clean/reset/restore/checkout/stash(mutating) | 0 |
| git add/commit/push/pull/fetch/merge/rebase | 0 |
| force push | 0 |
| formatting | 0 |
| rsync/unison/syncthing | 0 |
| recursive copy over existing (cp -R/-r/-a) | 0 |
| sudo/kill | 0 |
| -c on cp (clone) | 0 |

Exact `mkdir`/`tar`/`ssh`/`chmod` usage in the runbook fences is destination-side and creates or streams into **new** directories only (see §8).

**Hard-fail patterns present: NONE**


---

## 23. The exact first message to send CLAUDE-INTEL
Sent **by the operator, copy-pasted unchanged** into the Claude Code session on the Intel MacBook Air. It authorizes **read-only discovery only**; it contains no secrets and no transfer command. (Not sent by this mission.)

```text
FERALECHO CROSS-BACKUP RELAY v1
MACHINE: M5
LINEAGE: FERALECHO-M5
MACHINE_ID16: dd7643e652db2d2c
TO: INTEL
SEQ: 1
REPLY_TO: NONE
STEP: DISCOVERY_REQUEST
DIRECTION: NONE
GEN: NONE
GIT_HEAD: 2fba42644c82b9f7096276f4dd338d615cf1bcce
WORKTREE: DIRTY m=27 u=225
FERALECHO_ROOT: /Users/richietate/Desktop/FeralEcho
SERVER: RUNNING pid=29288 start=2026-09-20T07:30:10
BACKUP_STATUS: NONE_OFFSITE; OWN_LOCAL none; FROM_INTEL none; one same-disk zip from 2026-09-05 exists (not a cross-backup)
SCRIPT_NAME: fe_discover.sh v1
SCRIPT_SHA256: 45dc50ab5ed590eb4c8e7f34e35e81a1a29c1d5575409ee23f05b7d6a2bbf1d9
REQUIRE: read-only; create nothing; stdout only; no secrets; no network beyond loopback
STATUS: INFO
NOTES: Phase A only. Reply with DISCOVERY_RESPONSE. Do not start any transfer. Do not assume anything about the M5 beyond this header.
MSG_CRC: a2bc296a
END RELAY

=== INSTRUCTIONS FOR CLAUDE-INTEL (relayed by the operator; they apply until the operator says otherwise) ===
ROLE: You are CLAUDE-INTEL on the 2020 Intel MacBook Air. CLAUDE-M5 is planning a two-way, one-way-per-operation CROSS-BACKUP between two SEPARATE FeralEcho lineages (M5 and Intel). It is NOT sync, NOT merge. This message authorizes READ-ONLY DISCOVERY ONLY.
HARD RULES (each is binding):
 1. Read-only. Create, modify, move, rename, delete or overwrite NOTHING on this machine. No files, no directories, no scratch files of your own. Output goes to stdout only. (The only unavoidable exception: the transient temporary files that bash or zsh itself creates for a heredoc in the system temp directory and removes automatically - never write anything under a FeralEcho directory, your home directory, or /Volumes.)
 2. Do not stop, start, restart or signal any server or process. No kill. Do not run backup_feral_echo.sh.
 3. No git write verbs: no commit, push, pull, fetch, reset, clean, checkout, restore, stash, add. (The script only reads.)
 4. No network use except loopback to a local Ollama. Do not ssh, scp, curl anything external, or contact the M5.
 5. Never read, print, quote or transmit the CONTENTS of .env, keys, tokens or credentials. Report .env only as PRESENT/size/mode/16-hex hash prefix (the script already does this).
 6. Do not import or run FeralEcho code, terminal_client, or any production module. Do not open or unpickle any state file.
 7. Assume nothing about the M5 beyond the header above. The M5 assumes nothing about you beyond your reply.
 8. If the script cannot classify something, report it as UNKNOWN - never guess and never suggest deleting anything.
 9. Do not send anything containing a secret. If unsure, leave the value out and say so in NOTES.
HOW TO RUN (operator: if your Claude Code asks permission for the command, approve it - it only reads). Run exactly this, once:
```bash
/bin/bash <<'FE_RUN'
IFS= read -r -d '' S <<'FE_DISCOVER_EOF'
# fe_discover.sh v1 -- READ-ONLY discovery. Run as:  /bin/bash -s < script   (bash 3.2 compatible)
# Prints a relay-safe report to stdout. WRITES NOTHING: no files, no git index refresh, no network (loopback Ollama only).
# NEVER prints secret values: .env is reported only as PRESENT/size/mode/16-hex hash prefix.
export LC_ALL=C GIT_OPTIONAL_LOCKS=0; umask 077
kv()  { printf '%s: %s\n' "$1" "$2"; }
h16() { shasum -a 256 | cut -c1-16; }
red() { sed -E 's#(https?://)[^/@ ]+@#\1<redacted>@#g; s#(gh[pousr]_|sk-|AKIA)[A-Za-z0-9_-]{8,}#<redacted>#g'; }
kv DISCOVERY_SCRIPT "fe_discover.sh v1"; kv OBSERVED_UTC "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "== MACHINE"
ARM=$(sysctl -in hw.optional.arm64 2>/dev/null); TR=$(sysctl -in sysctl.proc_translated 2>/dev/null); HW=$(sysctl -n hw.model 2>/dev/null)
ARCH_TRUE=x86_64; [ "$ARM" = 1 ] && ARCH_TRUE=arm64
HWU=$(ioreg -rd1 -c IOPlatformExpertDevice 2>/dev/null | awk -F'"' '/IOPlatformUUID/{print $4}')
kv UNAME_M "$(uname -m)"; kv ARCH_TRUE "$ARCH_TRUE"; kv ROSETTA_TRANSLATED "${TR:-0}"; kv HW_MODEL "$HW"
kv CPU "$(sysctl -n machdep.cpu.brand_string 2>/dev/null)"; kv RAM_BYTES "$(sysctl -n hw.memsize 2>/dev/null)"
kv OS "$(sw_vers -productVersion 2>/dev/null) build $(sw_vers -buildVersion 2>/dev/null)"; kv HOSTNAME "$(scutil --get LocalHostName 2>/dev/null)"
kv HW_ID16 "$(printf 'feralecho-hw-v1|%s' "$HWU" | h16)"
kv MACHINE_ID16 "$(printf 'feralecho-machine-v1|%s|%s|%s' "$ARCH_TRUE" "$HW" "$HWU" | h16)"
kv HOME_FS_TOTAL_FREE_BYTES "$(df -k "$HOME" | awk 'NR==2{printf "%d %d", $2*1024, $4*1024}')"
diskutil info / 2>/dev/null | grep -E "File System Personality|Solid State|SMART Status|Device Location|FileVault" | sed 's/^ *//'
kv FILEVAULT "$(fdesetup status 2>&1 | head -1)"; kv TIMEMACHINE "$(tmutil destinationinfo 2>&1 | head -1)"
kv ICLOUD_DESKTOP "$(defaults read com.apple.finder FXICloudDriveDesktop 2>&1 | head -1)"
kv XCODE_CLT "$(xcode-select -p 2>&1 | head -1)"
for t in git python3 ollama shasum tar rsync ssh sqlite3 conda file lsof; do kv "TOOL_$t" "$(command -v $t || echo -)"; done
kv TAR "$(tar --version 2>&1 | head -1)"
GIT=$(command -v git); GITOK=1
if [ "$GIT" = /usr/bin/git ] && ! xcode-select -p >/dev/null 2>&1; then GITOK=0; fi
kv GIT_USABLE "$GITOK (git=$GIT; an /usr/bin/git shim without Command Line Tools is NOT invoked, to avoid an install prompt)"
kv REMOTE_LOGIN_HINT "$(launchctl print-disabled system 2>/dev/null | grep -i ssh | head -1) (informational only; real state UNKNOWN without admin)"
echo "== PROCESSES (server-like)"
ps -axo pid=,lstart=,comm=,command= 2>/dev/null | grep -E "run\.py|start_echo\.sh|terminal_client|echo_studio|ollama serve" | grep -v grep | cut -c1-200 | red
PIDS=$(ps -axo pid=,command= 2>/dev/null | grep -E "run\.py|start_echo\.sh|terminal_client" | grep -v grep | awk '{print $1}')
echo "== CANDIDATE FERALECHO ROOTS"
PRUNE=( -path "$HOME/Library" -o -path "$HOME/.ollama" -o -path "$HOME/miniforge3" -o -path "$HOME/miniconda3" -o -path "$HOME/anaconda3" -o -path "$HOME/.cache" -o -path "$HOME/.npm" -o -path "$HOME/Applications" -o -path "*/node_modules" -o -path "*/.git" -o -path "*/__pycache__" )
ROOTS=""
for rp in $(find "$HOME" -maxdepth 6 \( "${PRUNE[@]}" \) -prune -o -type f -name run.py -print 2>/dev/null | sed 's#/run\.py$##' | tr ' ' '\001'); do
  d=$(printf '%s' "$rp" | tr '\001' ' ')
  { [ -f "$d/app/core/echo_model_orchestrator.py" ] || [ -f "$d/echo_principles.json" ]; } || continue
  ROOTS="$ROOTS$d
"
done
ROOTS=$(printf '%s' "$ROOTS" | sort)
[ -n "$ROOTS" ] || echo "(none found under \$HOME depth 6)"
classify_root() { # prints LIVE / POSSIBLE_LIVE / HISTORICAL_LINEAGE for root $1
  local d="$1" pid cwd
  for pid in $PIDS; do cwd=$(lsof -a -p "$pid" -d cwd -Fn 2>/dev/null | sed -n 's/^n//p'); case "$cwd/" in "$d"/*) echo LIVE; return ;; esac; done
  if [ -n "$(find "$d/memory" -maxdepth 1 -type f -mmin -1440 2>/dev/null | head -1)" ] || [ -f "$d/memory/echo_server.pid" ]; then echo POSSIBLE_LIVE; return; fi
  echo HISTORICAL_LINEAGE
}
echo "$ROOTS" | while IFS= read -r d; do
  [ -n "$d" ] || continue
  case "$d" in */.claude/worktrees/*) kv "ROOT_NESTED_WORKTREE_COPY" "$d"; continue ;; esac
  echo "== ROOT"; kv FERALECHO_ROOT "$d"; kv CLASS "$(classify_root "$d") (heuristic; if uncertain, PRESERVE)"
  kv REPO_KB "$(du -sk "$d" 2>/dev/null | cut -f1)"; kv GITDIR_KB "$(du -sk "$d/.git" 2>/dev/null | cut -f1)"
  kv MEMORY_KB "$(du -sk "$d/memory" 2>/dev/null | cut -f1)"; kv DATA_KB "$(du -sk "$d/data" 2>/dev/null | cut -f1)"
  cd "$d" 2>/dev/null || continue
  SRC=$(find . \( -name __pycache__ -o -name .pytest_cache \) -prune -o -type f ! -name .DS_Store ! -path './memory/*' ! -path './data/*' -print0 2>/dev/null | xargs -0 stat -f '%z' 2>/dev/null | awk '{s+=$1;n++} END{printf "%d %d", s, n}')
  STA=$(find ./memory ./data \( -name __pycache__ -o -name .pytest_cache \) -prune -o -type f ! -name .DS_Store -print0 2>/dev/null | xargs -0 stat -f '%z' 2>/dev/null | awk '{s+=$1;n++} END{printf "%d %d", s, n}')
  kv SOURCE_BYTES_FILES "$SRC"; kv STATE_BYTES_FILES "$STA"
  kv PROPOSED_BACKUP_BYTES "$(echo "$SRC $STA" | awk '{print $1+$3}')"
  kv SYMLINKS_IN_SCOPE "$(find . \( -name __pycache__ -o -name .pytest_cache \) -prune -o -type l -print 2>/dev/null | wc -l | tr -d ' ')"
  kv ODD_PATHS_NEWLINE_TAB_BACKSLASH "$(find . \( -name __pycache__ -o -name .pytest_cache \) -prune -o -name '*[[:cntrl:]\\]*' -print 2>/dev/null | wc -l | tr -d ' ')"
  if [ -f .env ]; then kv ENV_FILE "PRESENT size=$(stat -f %z .env) mode=$(stat -f %Lp .env) sha256_16=$(shasum -a 256 < .env | cut -c1-16)"; else kv ENV_FILE ABSENT; fi
  if [ "$GITOK" = 1 ] && { [ -d .git ] || [ -f .git ]; }; then
    kv GIT_HEAD "$(git rev-parse HEAD 2>/dev/null)"; kv GIT_BRANCH "$(git symbolic-ref -q --short HEAD 2>/dev/null || echo DETACHED)"
    kv GIT_COMMITS "$(git rev-list --count HEAD 2>/dev/null)"; kv GIT_REFS_COUNT "$(git for-each-ref 2>/dev/null | wc -l | tr -d ' ')"
    kv GIT_REMOTES_REDACTED "$(git remote -v 2>/dev/null | red | tr '\n' ';')"
    B=$(git symbolic-ref -q --short HEAD 2>/dev/null)
    kv GIT_UNPUSHED_LOCAL_VIEW "$(git rev-list --count "@{u}..HEAD" 2>/dev/null || git rev-list --count "refs/remotes/origin/$B..HEAD" 2>/dev/null || echo UNKNOWN) (local refs only; no network)"
    kv GIT_TRACKED_MODIFIED "$(git diff --name-only HEAD 2>/dev/null | wc -l | tr -d ' ')"; kv GIT_UNTRACKED_NONIGNORED "$(git ls-files -o --exclude-standard 2>/dev/null | wc -l | tr -d ' ')"
    kv GIT_PORCELAIN_PATHS "$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')"; kv GIT_STASH_ENTRIES "$(git stash list 2>/dev/null | wc -l | tr -d ' ')"
    kv GIT_LINKED_WORKTREES "$(git worktree list --porcelain 2>/dev/null | grep -c '^worktree ')"
    echo "LIST GIT_REFS (short sha, name; first 12)"; git for-each-ref --format='  %(objectname:short) %(refname:short)' 2>/dev/null | head -12
    echo "LIST IGNORED_TOP_LEVEL (first 25)"; git ls-files -o -i --exclude-standard --directory 2>/dev/null | head -25 | sed 's/^/  /'
    WT=$(git ls-files -co --exclude-standard 2>/dev/null | grep -v -e '^memory/' -e '^data/' -e '^app/core/self_edit_convergence.json$' -e '^app/core/self_edit_generated.py$' -e '^sandbox/scripts/temp_self_edit.py$' -e '^staging/self_edit_candidate.py$' | LC_ALL=C sort)
    kv WORKTREE_FINGERPRINT_V1 "$(printf '%s\n' "$WT" | while IFS= read -r f; do [ -f "$f" ] && printf '%s\t%s\n' "$f" "$(shasum -a 256 < "$f" | cut -d' ' -f1)"; done | shasum -a 256 | cut -d' ' -f1) (sha256 over sorted 'path<TAB>sha256' of tracked+untracked-nonignored files, minus memory/, data/ and 4 self-mutating files)"
  else kv GIT "NOT_USABLE_OR_NOT_A_REPO (GITOK=$GITOK)"; fi
  echo "LIST PERSISTENCE_ARTIFACTS (bytes, mtime)"
  LAYOUT=""
  for a in memory/memory_meta.json memory/faiss.index data/memory_meta.json data/faiss.index memory/river_brain.pkl memory/task_type_classifier.pkl memory/drift_detectors.pkl data/question_garden.jsonl memory/self_model_claims.jsonl memory/council_ratings.jsonl memory/snapshot_baseline.json memory/interaction_log.jsonl memory/reflection_shard.jsonl memory/reflection_journal.jsonl memory/optuna.db memory/self_model.json memory/echo_state.npy memory/genesis/genesis_hash.txt; do
    if [ -f "$a" ]; then printf '  %s %s %s\n' "$(stat -f %z "$a")" "$(stat -f '%Sm' -t %Y-%m-%dT%H:%M "$a")" "$a"; LAYOUT="$LAYOUT$a:present\n"; else LAYOUT="$LAYOUT$a:absent\n"; fi
  done
  kv STATE_LAYOUT_FP_V1 "$(printf "$LAYOUT" | shasum -a 256 | cut -c1-16) (presence pattern of the canonical artifact list; stable identity of the persistence LAYOUT, not of contents)"
  for x in memory/snapshots memory/backups memory/archive memory/history; do [ -d "$x" ] && kv "DIR_$x" "files=$(find "$x" -type f | wc -l | tr -d ' ') kb=$(du -sk "$x" | cut -f1)"; done
  echo "LIST LARGEST_FILES_IN_memory_data (bytes path; top 12)"; find ./memory ./data -type f -print0 2>/dev/null | xargs -0 stat -f '%z %N' 2>/dev/null | sort -rn | head -12 | sed 's/^/  /'
  echo "LIST EXTENSIONS_IN_memory_data"; find ./memory ./data -type f 2>/dev/null | sed -E 's/.*\.([A-Za-z0-9]+)$/\1/' | sort | uniq -c | sort -rn | head -10 | sed 's/^/  /'
  if [ -f memory/echo_server.pid ]; then P=$(cat memory/echo_server.pid); kv SERVER "PIDFILE=$P $(ps -o pid=,lstart= -p "$P" 2>/dev/null | head -1 | grep . || echo NOT_RUNNING)"; else kv SERVER "NO_PIDFILE"; fi
  kv SENTINEL "$( [ -f memory/echo_sentinel.json ] && echo "present mtime=$(stat -f '%Sm' -t %Y-%m-%dT%H:%M memory/echo_sentinel.json)" || echo absent)"
  echo "LIST ROOT_LOCAL_INTERPRETERS (path, arch, version)"
  for p in "$d"/venv/bin/python "$d"/.venv/bin/python; do [ -x "$p" ] && printf '  %s | %s | %s\n' "$p" "$(file -b "$p" 2>/dev/null | sed -E 's/.*(arm64|x86_64).*/\1/' | head -1)" "$("$p" --version 2>&1 | head -1)"; done
done
echo "== INTERPRETERS (path | arch | version)"
for p in "$HOME"/miniforge3/envs/*/bin/python "$HOME"/miniconda3/envs/*/bin/python "$HOME"/anaconda3/envs/*/bin/python; do
  [ -x "$p" ] && printf '  %s | %s | %s\n' "$p" "$(file -b "$p" 2>/dev/null | sed -E 's/.*(arm64|x86_64).*/\1/' | head -1)" "$("$p" --version 2>&1 | head -1)"; done
for pid in $PIDS; do c=$(ps -o comm= -p "$pid" 2>/dev/null); case "$c" in *python*) printf '  RUNNING_SERVER_INTERPRETER %s | %s\n' "$c" "$("$c" --version 2>&1 | head -1)" ;; esac; done
echo "== OLLAMA (names/digests only; weights are NOT preserved by default)"
if command -v ollama >/dev/null; then ollama list 2>&1 | head -25; curl -s --max-time 3 http://127.0.0.1:11434/api/tags 2>/dev/null | grep -oE '"(name|digest)":"[^"]*"' | paste - - | sed -E 's/"name":"([^"]*)"\t"digest":"([0-9a-f]{16})[0-9a-f]*"/  \1 \2/' | head -25; kv OLLAMA_VERSION "$(curl -s --max-time 3 http://127.0.0.1:11434/api/version 2>/dev/null)"; else echo "(ollama not installed)"; fi
echo "== OTHER ECHO-RELATED MATERIAL (read-only name search; classification is a heuristic; NEVER delete/move/rename)"
find "$HOME" /Users/Shared /Volumes -maxdepth 7 \( "${PRUNE[@]}" \) -prune -o \( -name 'memory_meta*' -o -name 'faiss.index*' -o -name 'river_brain*' -o -name '*.bundle' -o -name 'question_garden*' -o -name 'echo_principles*' -o -iname '*feralecho*' -o -iname 'echocore*' -o -iname '*echo*backup*' \) -print 2>/dev/null | while IFS= read -r m; do
  inroot=0
  for r in $(printf '%s' "$ROOTS" | tr ' ' '\001'); do rr=$(printf '%s' "$r" | tr '\001' ' '); case "$m/" in "$rr"/*) inroot=1 ;; esac; done
  [ "$inroot" = 1 ] && continue
  cls=UNKNOWN; case "$m" in *ackup*|*BACKUP*|*.bak*|*archive*|*Archive*|*snapshot*|*.bundle|*.tar*|*.tgz) cls=BACKUP ;; esac
  [ -d "$m/.git" ] && cls=HISTORICAL_LINEAGE_OR_POSSIBLE_LIVE
  printf '  %s | %s | %s kb | %s\n' "$cls" "$m" "$(du -sk "$m" 2>/dev/null | cut -f1)" "$(stat -f '%Sm' -t %Y-%m-%d "$m" 2>/dev/null)"
done | head -60
kv LAUNCH_AGENTS "$(ls "$HOME/Library/LaunchAgents" 2>/dev/null | grep -i -e echo -e feral -e gremlin | tr '\n' ' ')"
echo "== END DISCOVERY"
FE_DISCOVER_EOF
printf '%s' "$S" | shasum -a 256 | grep -q '^45dc50ab5ed590eb4c8e7f34e35e81a1a29c1d5575409ee23f05b7d6a2bbf1d9 ' || { echo "STOP: script hash mismatch - do not run"; exit 1; }
printf '%s' "$S" | /bin/bash -s
FE_RUN
```
If it prints "STOP: script hash mismatch", do nothing else and tell the operator.
HOW TO REPLY: send ONE message of this exact format (the relay banner as above, STEP: DISCOVERY_RESPONSE, TO: M5, SEQ: 1, REPLY_TO: 1), header fields MACHINE=INTEL, LINEAGE=FERALECHO-INTEL-2020, then these fields in this order, each a single line, values <=300 chars, no secrets:
 MACHINE
 LINEAGE
 MACHINE_ID16
 TO
 SEQ
 REPLY_TO
 STEP
 DIRECTION
 GEN
 GIT_HEAD
 WORKTREE
 FERALECHO_ROOT
 SERVER
 BACKUP_STATUS
 ARCH_TRUE
 ROSETTA_TRANSLATED
 HW_MODEL
 OS
 HW_ID16
 WORKTREE_FINGERPRINT
 STATE_LAYOUT_FP
 ROOT_CLASS
 REPO_BYTES
 GITDIR_BYTES
 MEMORY_BYTES
 DATA_BYTES
 SOURCE_BYTES
 STATE_BYTES
 PROPOSED_BACKUP_BYTES
 HOME_FREE_BYTES
 HOME_TOTAL_BYTES
 ENV_FILE
 GIT_UNPUSHED
 TRACKED_MODIFIED
 UNTRACKED
 OTHER_MATERIAL
 SMART
 FILEVAULT
 TOOLS_OK
 OLLAMA_MODELS
 REPORT_HASH
 STATUS
 NOTES
Field sources (from the script output): ARCH_TRUE=ARCH_TRUE; ROSETTA_TRANSLATED; HW_MODEL; OS; HW_ID16; MACHINE_ID16 (header); WORKTREE_FINGERPRINT=WORKTREE_FINGERPRINT_V1 (64 hex); STATE_LAYOUT_FP=STATE_LAYOUT_FP_V1 (16 hex); ROOT_CLASS=the CLASS of the PRIMARY root (LIVE/POSSIBLE_LIVE/HISTORICAL_LINEAGE; if several roots qualify, set STATUS: BLOCKED and list them in NOTES); REPO_BYTES/GITDIR_BYTES/MEMORY_BYTES/DATA_BYTES = the *_KB values x1024; SOURCE_BYTES/STATE_BYTES/PROPOSED_BACKUP_BYTES from the script; HOME_FREE_BYTES/HOME_TOTAL_BYTES from HOME_FS_TOTAL_FREE_BYTES; ENV_FILE exactly as printed (or ABSENT); GIT_UNPUSHED/TRACKED_MODIFIED/UNTRACKED from the git lines (or UNKNOWN); OTHER_MATERIAL = count plus the classes (e.g. "5: 2 BACKUP, 1 HISTORICAL, 2 UNKNOWN"); SMART and FILEVAULT as printed; TOOLS_OK = the tools present among shasum tar ssh bash git; OLLAMA_MODELS = count; REPORT_HASH = first 64 hex of sha256 of the full script output you saw. In NOTES say (briefly) whether Remote Login appears enabled or UNKNOWN, whether Command Line Tools were missing (git skipped), and anything the script could not do. Header lines to copy from the M5 message: GEN: NONE, DIRECTION: NONE. Use GIT_HEAD/WORKTREE/FERALECHO_ROOT/SERVER/BACKUP_STATUS of YOUR primary root (UNKNOWN if not found).
MSG_CRC (before you send): first 8 hex of sha256 over every line from the banner through the line before MSG_CRC, each newline-terminated:
```bash
IFS= read -r -d '' BODY <<'MSG'
<the message lines, banner through the line before MSG_CRC, no blank line at the end>
MSG
printf '%s' "$BODY" | shasum -a 256 | cut -c1-8      # = MSG_CRC
```
Then add "MSG_CRC: <8 hex>" and "END RELAY". The M5 will verify the CRC and lint it (token shapes, NAME=value assignments, long hex/opaque runs in non-hash fields, ENV_FILE grammar). Do NOT paste the full script output back unless the M5 asks; send only the DISCOVERY_RESPONSE. Then STOP and wait for the operator. Do not begin any preparation for a transfer.
=== END INSTRUCTIONS ===
```

---

## 24. Integrity record
### 24.1 Before / after (all read-only observations)
| Item | Before | After | Same? |
|---|---|---|---|
| Git HEAD | `2fba42644c82b9f7096276f4dd338d615cf1bcce` | `2fba42644c82b9f7096276f4dd338d615cf1bcce` | **yes** |
| `git status --porcelain` | 188 paths | 190 paths | the diff of the two listings is exactly **two added lines**: `?? audits/2026-09-20_feralecho_cross_backup_relay_schema.json` and `?? audits/2026-09-20_feralecho_m5_intel_cross_backup_relay_plan.md` — this mission's two deliverables; no pre-existing path changed |
| Server | PID 29288, start Sun Sep 20 07:30:10 2026 | PID 29288, start Sun Sep 20 07:30:10 2026 | **yes** — not stopped, restarted or signalled |
| Frozen protocol v1.0 / v1.1 / traceability | `d1968caf…`, `e39e6238…`, `493600f4…` | identical | **yes** |
| `.git/index.lock`, stash entries | none, 0 | none, 0 | yes |
| `~/FeralEcho_Cross_Backups`, `~/fe_backup_tools`, `/tmp` probe files | — | all absent (checked) | no generation, no directory was created |

### 24.2 Confirmations
* **No network transfer; no backup generation; no Intel discovery.** Intel was not contacted. The only network-adjacent commands on the M5 were `ollama list` and loopback `curl` to the local Ollama (`127.0.0.1:11434`), plus the disclosure in 24.3(3).
* **No production mutation.** Files written in the repository: exactly the two deliverables. Everything else is in the session scratchpad (script drafts, fixtures, generated outputs). No git write verb was run against the FeralEcho repository (read-only git commands with `GIT_OPTIONAL_LOCKS=0`); the throw-away fixtures used their own scratch state.
* `backup_feral_echo.sh` was not run; no synchronization software was used; the frozen protocol files were not opened for writing.

### 24.3 Disclosures (stated plainly)
1. **Phase A ran on the M5** — a read-only discovery script (31 s), several times, including under sandbox profiles. It reads sizes, mtimes, process lists, git metadata and the `.env` *hash*; it printed no secret. To test that, I compared every `.env` value with the output using an in-memory `grep -F -f <(…)`; the only things printed were variable **names**, value **lengths** and match **counts**.
2. I listed the contents of the existing `~/Desktop/FeralEcho_backup_20260905_145413.zip` with `unzip -l` (names and sizes only; nothing extracted).
3. **A control test attempted an external request.** To prove the sandbox jail kills network use, I ran `curl https://example.com` inside it; the sandbox killed the process (`Killed: 9`). A DNS lookup for that hostname may have been issued by the system resolver before the kill (name resolution is performed by a system service outside the jail); no connection was made and no project data was involved.
4. Sandbox write-probe controls tried to write `/tmp/fe_jail_probe_should_not_exist` and `/tmp/fe_probe_zzz`; both were killed and neither file exists (checked).
5. My fixture tests used `rm -rf` on directories I had created in the scratchpad (never on repository or home paths); the **execution path in this plan contains no `rm`** (machine-linted with positive controls, §22).
6. **Corrections to my own earlier work, found by this discovery:** the preceding preservation audit and backup plan did not list `~/Desktop/FeralEcho_backup_20260905_145413.zip` (a same-disk full backup of 2026-09-05, including `memory/`), the ancestral material in §0.3, or that `.env` is mode 644. The "only off-SSD copy is missing" conclusion stands (the zip is on the same SSD). I did **not** edit the earlier files (this mission may create only two files); they need an erratum.
7. **Tooling bugs found by testing, fixed before this file was generated:** an unquoted `find` prune expression let the shell glob against the current directory (now a bash array); duplicated interpreter listing; a lint that flagged the *name* `ssh` in a tool list and the `>` characters inside awk regexes (both false positives, now handled — with positive controls); and the discovery recipe's heredoc, which necessarily creates transient shell temp files (now stated in the first message's rule 1).
8. The `WORKTREE_FINGERPRINT_V1` recorded in §0.3 is volatile by definition: it was taken while earlier deliverables existed and will differ after any edit.

### 24.4 Residual uncertainty
Everything about the Intel machine; the v2 backup tools and the whole cross-transfer stage sequence (specified, **not written or run**); SSH behaviour, Remote Login, forced-command hardening, host-key flow; `chflags uchg` semantics beyond the tested fixture; real-tree behaviour of the M5-side staging at 22,803 files; whether Intel has the interpreters/`faiss` needed for full structural validation; whether the registry still serves `llama3:instruct`; the accuracy of the M5's 2026-07-07 belief about "Ark".


---

## Final questions

**1. What exact information must CLAUDE-INTEL report before the M5 is allowed to send anything?**
A valid, CRC-sealed, lint-clean `DISCOVERY_RESPONSE` containing: `ARCH_TRUE=x86_64` and `ROSETTA_TRANSLATED=0`; `HW_MODEL`, `OS`, `HW_ID16`, `MACHINE_ID16`; **the classified list of every candidate FeralEcho root** with exactly one identified as the primary and its `ROOT_CLASS` (LIVE / POSSIBLE_LIVE / HISTORICAL); `FERALECHO_ROOT`, `GIT_HEAD`, branch, ref count, `GIT_UNPUSHED` (local view), `TRACKED_MODIFIED`, `UNTRACKED`, `WORKTREE_FINGERPRINT` and `STATE_LAYOUT_FP`; repo/.git/memory/data byte sizes and **`PROPOSED_BACKUP_BYTES`**; **`HOME_FREE_BYTES` and `HOME_TOTAL_BYTES`** (so the M5 can verify `2× + 10 GiB` and the 15 % floor itself); `SMART`, `FILEVAULT`; server status with pid/start; `ENV_FILE` (PRESENT/size/mode/hash prefix only); the count and classification of *other* Echo-related material (previous backups, older repos, FAISS/RiverBrain artifacts, previous M5 copies); tool availability (`shasum`, `tar`, `ssh`, `bash`, `git`/CLT status, interpreters with architecture); Ollama names/digests/version; whether Remote Login is enabled and whether the operator is willing to enable it (or `UNKNOWN`); and the discovery **report hash**. If any capacity, identity or primary-root item is `UNKNOWN`, that direction is `BLOCKED` — the M5 sends nothing.

**2. Which lineage should probably be backed up first, and what evidence could reverse that decision?**
**M5 first (M5 → Intel).** The M5 holds the only verified copy of the current lineage: 17 unpushed commits, 27 modified + 223 untracked files, ≈ 1.3 GB of accumulated state, a server that aborts ≈ twice a day, and no off-disk copy (the 2026-09-05 zip shares the SSD). Reversal evidence: Intel `SMART` Failing/degraded or a disk in visible trouble; Intel holding unique, unbacked older-lineage state; Intel lacking the free space for an M5 generation (M5 → Intel `BLOCKED`, while the M5 can always hold Intel's); an external-vault copy of the M5 landing first; ambiguous Intel discovery (a direction waits until its source is identified).

**3. How will the two Claudes prove that a received generation is byte-identical to what was sent?**
The source seals a local generation and computes `MANIFEST_HASH` = sha256 of the sorted `path/size/sha256` list, plus file and byte counts. After the transfer the destination **independently recomputes** the same manifest over what it received. Success needs identical hash, count and bytes with zero extra/missing files, **and** a nonce-salted challenge: the source picks fresh sample files and a random nonce after the fact, and the destination returns `sha256(nonce ‖ file bytes)`, which the source recomputes over its own sealed copy. Each Claude accepts only values it computed or compared itself; "the other Claude verified it" is never evidence. The generation is sealed only after `HASH_VERDICT: MATCH`, then re-hashed cold.

**4. How do we prevent one Echo lineage from ever overwriting or merging with the other?**
Separate directories by lineage and by name (`FROM_M5`, `FROM_INTEL`, `OWN_LOCAL`), outside every live tree; generation directories created once with plain `mkdir` and never reused; extraction with `tar -k` behind an emptiness check; no rsync/`--delete`/mirror mode anywhere; markers instead of renames; sealed generations read-only; identity tuples pinned and rechecked in every message; the human authorization phrase names direction, generation and file-list hash and must be typed into *both* sessions; restore is staging-first, same-lineage-only, never automatic, and replaces rather than merges; no tool in the plan can union two persistent states.

**5. What does storing an Intel backup on M5 protect against, and what does it NOT protect against?**
*Protects against:* loss or failure of the Intel machine's disk; logical corruption or accidental deletion on Intel; a bad change to the Intel instance (the older sealed generation still exists); the M5 has ≈ 754 GB free so capacity is unlikely to fail. *Does not protect against:* the M5 failing at the same time (both copies of the Intel lineage would then depend on the Intel alone); a silent corruption that was already in Intel's state when copied; anything written on Intel after the backup; theft/fire when the two Macs sit together; leakage of secrets if the M5 is compromised (the generation contains Intel's `.env`); it is **data recovery, not a promise of direct executability** on Apple silicon (Intel-compiled environments and Ollama runtime do not transfer).

**6. What does storing an M5 backup on Intel protect against, and what does it NOT protect against?**
*Protects against:* loss or failure of the M5's SSD (currently the only home of the recent lineage), logical corruption or deletion on the M5, a bad restart or self-edit accident (independent immutable generations), and human error on the M5. *Does not protect against:* Intel lacking space (capacity unknown until reported); the Intel disk being old/failing (SMART unknown); simultaneous loss of both machines/site; silent corruption already in the M5's state; changes after the backup; unencrypted exposure (Intel FileVault status unknown — the generation contains `.env`); and **direct executability** — an Intel restore of the M5 lineage has no MLX/Metal path and needs a rebuilt x86_64 environment; the guarantee is data recovery.

**7. What exact human authorization phrase should unlock the first transfer?**
`AUTHORIZE M5 -> INTEL GENERATION G001 LISTHASH <8 hex>` — where `<8 hex>` is the first 8 hex characters of `SOURCE_LIST_HASH` shown in the M5's `SOURCE_MANIFEST_OFFER` (it does not exist until Phase D, so no valid phrase can be typed earlier), typed **into both sessions**, with ` UNENCRYPTED-OK` appended only if Intel's FileVault is Off and the operator accepts that. The bare form `AUTHORIZE M5 -> INTEL GENERATION G001` is **not** sufficient to open the gate. The reverse direction needs its own phrase: `AUTHORIZE INTEL -> M5 GENERATION G001 LISTHASH <8 hex>`.

**FIRST RELAY MESSAGE TO CLAUDE-INTEL** — §23 holds it as a ready-to-paste block; it is also given at the end of the chat reply that accompanies this file.

**STOP.** Nothing was transferred, no Intel discovery was started, no backup generation exists. The next action belongs to the human operator.

---

## Appendix A — `fe_discover.sh` v1
Embedded verbatim in the §23 block (read-only, stdout only; SHA-256 in Appendix C). Not repeated here.

## Appendix B — `fe_relay.sh` v1 (seal / check / lint / transition table)
```bash
# fe_relay.sh v1 -- relay message helpers (bash 3.2+, awk, shasum only). SOURCE this. Writes nothing; reads stdin, prints stdout.
#   relay_seal  < body   : body = message lines from the banner up to (not including) MSG_CRC; prints the complete message
#   relay_check < msg    : verifies banner, END, MSG_CRC, mandatory header, STEP/STATUS vocab, secret lint; prints PASS or FAIL: reasons
#   relay_lint  < msg    : the secret/hygiene lint alone
#   relay_transition_ok PREV NEXT : exit 0 if NEXT may follow PREV
FE_RELAY_STEPS=" DISCOVERY_REQUEST DISCOVERY_RESPONSE DIRECTION_PROPOSAL SOURCE_MANIFEST_OFFER DESTINATION_CAPACITY_ACCEPT TRANSFER_PLAN TRANSFER_AUTHORIZATION_REQUIRED AUTHORIZATION_ACK TRANSFER_COMPLETE_SOURCE TRANSFER_COMPLETE_DESTINATION HASH_CHALLENGE HASH_CONFIRM HASH_VERDICT STRUCTURAL_VALIDATION GENERATION_SEALED SECOND_DIRECTION_READY ABORT "
relay_crc() { shasum -a 256 | cut -c1-8; }
relay_seal() { local body; body=$(cat); printf '%s\n' "$body"; printf 'MSG_CRC: %s\nEND RELAY\n' "$(printf '%s\n' "$body" | relay_crc)"; }
relay_lint() {
  awk '
  function bad(m) { printf "LINT: line %d: %s\n", NR, m; n++ }
  /^(MSG_CRC|END RELAY)/ { next }
  { line=$0; k=line; sub(/:.*/, "", k); v=line; sub(/^[^:]*: ?/, "", v)
    if (length(line) > 400) bad("line longer than 400 chars (relay must stay compact)")
    if (line ~ /-----BEGIN [A-Z ]*(PRIVATE KEY|CERTIFICATE|PGP)/) bad("PEM/PGP block")
    if (line ~ /(gh[pousr]_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9_-]{16,}|AKIA[0-9A-Z]{16}|xox[baprs]-[A-Za-z0-9-]{10,}|eyJ[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{10,})/) bad("token-shaped string")
    if (line ~ /(^|[ ;,])[A-Z][A-Z0-9_]{2,}=[^ ]{4,}/) bad("dotenv-shaped assignment (NAME=value)")
    hashy = (k ~ /(HEAD|HASH|_FP$|FP16|FINGERPRINT|NONCE|DIGEST|SEAL|CRC|^D[0-9]+$|SHA)/)
    if (!hashy && v ~ /[A-Fa-f0-9]{32,}/) bad("32+ hex run in a non-hash field: " k)
    if (!hashy && v ~ /[A-Za-z0-9+=_-]{40,}/) bad("40+ char opaque run in a non-hash field: " k)
    if (k ~ /(KEY|SECRET|TOKEN|PASSWORD|PASSWD|CREDENTIAL|PRIVATE)/ && k !~ /^(HOSTKEY_FP|PUBKEY_FP)$/ && length(v) >= 8) bad("secret-named field carries a value: " k)
    if (k == "ENV_FILE" && v !~ /^(ABSENT|PRESENT size=[0-9]+ mode=[0-7]+ sha256_16=[0-9a-f]{16})$/) bad("ENV_FILE must be exactly ABSENT or PRESENT size= mode= sha256_16=")
  }
  END { if (n > 0) exit 1 }'
}
relay_check() {
  local msg; msg=$(cat); local fails="" first last crc want body
  first=$(printf '%s\n' "$msg" | head -1); last=$(printf '%s\n' "$msg" | tail -1)
  [ "$first" = "FERALECHO CROSS-BACKUP RELAY v1" ] || fails="$fails banner-missing;"
  [ "$last" = "END RELAY" ] || fails="$fails END-missing;"
  crc=$(printf '%s\n' "$msg" | sed -n 's/^MSG_CRC: //p' | head -1)
  body=$(printf '%s\n' "$msg" | sed '/^MSG_CRC: /,$d')
  want=$(printf '%s\n' "$body" | relay_crc)
  [ -n "$crc" ] && [ "$crc" = "$want" ] || fails="$fails crc-mismatch(have=${crc:-none} want=$want);"
  local k; for k in MACHINE LINEAGE MACHINE_ID16 TO SEQ REPLY_TO STEP DIRECTION GEN GIT_HEAD WORKTREE FERALECHO_ROOT SERVER BACKUP_STATUS STATUS NOTES; do
    printf '%s\n' "$msg" | grep -q "^$k: " || fails="$fails missing-$k;"; done
  local step; step=$(printf '%s\n' "$msg" | sed -n 's/^STEP: //p' | head -1)
  case "$FE_RELAY_STEPS" in *" $step "*) ;; *) fails="$fails bad-STEP($step);" ;; esac
  case "$(printf '%s\n' "$msg" | sed -n 's/^STATUS: //p' | head -1)" in READY|BLOCKED|INFO|ERROR) ;; *) fails="$fails bad-STATUS;" ;; esac
  local lint; lint=$(printf '%s\n' "$msg" | relay_lint 2>&1) || fails="$fails $(printf '%s' "$lint" | tr '\n' ' ')"
  if [ -z "$fails" ]; then echo "PASS"; return 0; else echo "FAIL:$fails"; return 1; fi
}
relay_transition_ok() {
  case "$1>$2" in
    DISCOVERY_REQUEST\>DISCOVERY_RESPONSE|DISCOVERY_RESPONSE\>DISCOVERY_RESPONSE|DISCOVERY_RESPONSE\>DIRECTION_PROPOSAL|DISCOVERY_RESPONSE\>SOURCE_MANIFEST_OFFER|DIRECTION_PROPOSAL\>SOURCE_MANIFEST_OFFER|\
    SOURCE_MANIFEST_OFFER\>DESTINATION_CAPACITY_ACCEPT|DESTINATION_CAPACITY_ACCEPT\>TRANSFER_PLAN|TRANSFER_PLAN\>TRANSFER_AUTHORIZATION_REQUIRED|TRANSFER_AUTHORIZATION_REQUIRED\>AUTHORIZATION_ACK|\
    AUTHORIZATION_ACK\>AUTHORIZATION_ACK|AUTHORIZATION_ACK\>TRANSFER_COMPLETE_SOURCE|TRANSFER_COMPLETE_SOURCE\>TRANSFER_COMPLETE_DESTINATION|TRANSFER_COMPLETE_DESTINATION\>HASH_CHALLENGE|\
    HASH_CHALLENGE\>HASH_CONFIRM|HASH_CONFIRM\>HASH_VERDICT|HASH_VERDICT\>STRUCTURAL_VALIDATION|STRUCTURAL_VALIDATION\>GENERATION_SEALED|GENERATION_SEALED\>SECOND_DIRECTION_READY|SECOND_DIRECTION_READY\>DISCOVERY_REQUEST) return 0 ;;
    *\>ABORT) return 0 ;;
  esac
  return 1
}
```

## Appendix C — SHA-256 of the two scripts
| File | SHA-256 |
|---|---|
| `fe_discover.sh` (as embedded in §23; exact heredoc text) | `45dc50ab5ed590eb4c8e7f34e35e81a1a29c1d5575409ee23f05b7d6a2bbf1d9` |
| `fe_relay.sh` | `4ba03e574e5d1203757e41fe2eb40abd82f212951a42e415671eb5be477d27d3` |
