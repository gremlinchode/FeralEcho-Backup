# Lab-Only ScratchWriter — Implementation and Verification

Date of the campaign: 2026-11-08 (evidence timestamps are UTC, 2026-11-09T03:03Z).
Worktree: `/Users/richietate/Desktop/FeralEcho-voyager`, branch `project-voyager`, HEAD `dc8d6eb9b6479ef323614cd6820bb050a14299eb`.

Specification: `voyager_lab/scratch_write/FINAL_SECURITY_DESIGN.md`.
This report records the authorized lab implementation and the four required acceptance runs. It does not authorize Echo integration, tool registration, the file-skill experiment, Seatbelt, or a commit.

## 1. Files created and their purpose

| File | SHA-256 | Bytes | Purpose |
|---|---|---|---|
| `pinned_writer.py` | `285b05521916770ab798d07df29f0c44c51d8f256c81c9b870dc31ff3d0e830a` | 32327 | Trusted host pin (`open_pinned_root`, `PinnedRoot`) and rootless `ScratchWriter`. |
| `tests/test_pinned_writer.py` | `30c0385356c8e32f9735a14685e5c75a6a5e1f77260f14a4969bf37dc8ec74eb` | 35391 | Exactly three campaign tests: T1, T8, T2. |
| `IMPLEMENTATION_AND_VERIFICATION_REPORT.md` | this file | — | This record. |

`__pycache__` under `scratch_write/` and `scratch_write/tests/` was removed before this report. It is not part of the artifact.

Authorized location change, stated as a location change: the design’s sequence named an opt-in pin inside the existing write path. This assignment required a separate module and forbade edits to the prototype. The same checks live in `pinned_writer.py`. The prototype functions are imported only where their behavior is already the laboratory contract (`open_root`, path classification, `append_audit`, `OPERATION_LOCK`). `ScratchWriter` does not call `write_file.write_file` or `verify_file.verify_file`.

## 2. Prototype and review documents

Recomputed after the campaign. Each hash matches the pre-implementation baseline.

| File | SHA-256 | Bytes |
|---|---|---|
| `confine.py` | `f7520a948f5f11ce42958aa11d81b76a18e2bc52eb0d94eb637e42d4ece4b0f2` | 15516 |
| `write_file.py` | `897454a5169fa7922c270eb2f117c0c354847fb27ca8337688708251893184b9` | 10194 |
| `verify_file.py` | `638e589ba3bcec9aa738a4d50dd781bf504660df7a5408ea509614d4e094069d` | 5851 |
| `tests/test_scratch_write.py` | `880eb11218cc174a227159f0e384968f64d2e9bc35200f436ae81b99f1eab1db` | 52413 |
| `tests/__init__.py` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | 0 |
| `README.md` | `c678280f8146949f258ed920e0b0cf7d1e1e28b75d3b81458f4da7ec33653943` | 11580 |
| `SECURITY_REPORT.md` | `48a674d902a773c10fdc711d7c717f1a7dc54c09e5852e58a85bd156c7d38ac0` | 11280 |
| `FINAL_SECURITY_DESIGN.md` | `2940b3072f1a01101565ec64884a6f44c92136fadf1025f05a3988b34be63bbb` | 26446 |

`INDEPENDENT_SECURITY_REVIEW.md` is absent and was not created. `tests/test_scratch_write.py` still contains 56 `test_*` methods. The new file contains exactly `test_t1_root_substitution`, `test_t8_protected_paths`, and `test_t2_live_rename`.

## 3. Architecture implemented

The operator passes one scratch directory to `open_pinned_root`. That call uses the existing `confine.open_root` refusal order, then duplicates the directory descriptor with `F_DUPFD_CLOEXEC`, records `st_dev`, `st_ino`, and the `F_GETPATH` string taken at open, and closes the temporary open. `ScratchWriter` accepts only that `PinnedRoot` object. A later caller cannot supply a root.

Live authorization, on the retained directory descriptor:

- `fstat` must still be a directory with the pinned device and inode.
- `F_GETPATH` must equal the stored path byte for byte. The check does not `realpath` that string.
- A parent descriptor is accepted only after its own `F_GETPATH` equals the expected child of the pinned path (`pin.path` for a one-component name; `pin.path + "/" + component` for a deeper parent). The comparison is string concatenation.
- A file descriptor’s `F_GETPATH` must equal that expected child path. Its inode is not compared to the directory inode.

Writes use descriptor-relative `open`, `link`, `unlink`, and `fsync`. The exposed methods are `write_file(relative_path, content)` and `verify_file(relative_path, expected_content)`. `close()` releases the host descriptor under the same process-local lock. It is host resource release. Echo does not receive the descriptor, and there is no method that replaces the pin.

If a validation check sees that the pinned directory’s path or inode no longer matches, the call does not link into a replacement directory. When the directory inode still matches and this call has already created a temp or a final name, it unlinks that name through the pinned descriptor. A lost directory inode does not unlink, because the descriptor is no longer known to be the original directory. `ok` is true only for `status == "verified"`, `verification == "match"`, an accepted record, and a completed audit append while the pin still holds. Bytes that exist somewhere else do not count as success.

Seatbelt is not used.

## 4. Exact public interface

```text
open_pinned_root(path) -> PinnedRoot
PinnedRoot(fd, path, dev, ino)
ScratchWriter(pin)
ScratchWriter.write_file(relative_path, content) -> dict
ScratchWriter.verify_file(relative_path, expected_content) -> dict
ScratchWriter.close() -> None
```

`inspect.signature` on the campaign run recorded:

- `write_file`: `self`, `relative_path`, `content`
- `verify_file`: `self`, `relative_path`, `expected_content`

Return keys: `accepted`, `audit_recorded`, `ok`, `operation`, `path`, `reason`, `sha256`, `size`, `status`, `verification`.

A cleaned publication returns `status: "rejected"`, `reason: "identity_mismatch"`, `verification: "not_run"`, `ok: false`, `audit_recorded: false`. `publish_cleanup_failed` and `temp_cleanup_failed` use that same string for both `status` and `reason` when the corresponding unlink fails and the leftover name remains. Content is not copied into the result or the audit line.

## 5. Baseline 56-test results

Command, from `voyager_lab/scratch_write`:

```text
python3 -m unittest tests.test_scratch_write
```

Recorded result: `Ran 56 tests in 0.185s`, `OK`, exit 0.
Passes 56. Failures 0. Errors 0. Skips 0 (unittest printed no skip line).
This loader does not collect `tests.test_pinned_writer`.

## 6. T1 — root substitution

Command:

```text
python3 -m unittest tests.test_pinned_writer.PinnedWriterCampaign.test_t1_root_substitution
```

Recorded result: `Ran 1 test in 0.006s`, `OK`, exit 0.
Evidence: `/tmp/scratch_writer_t1.json`. Verdict in that file: `PASS`.
The passing test removed its temporary base after recording identities. The JSON is the filesystem evidence.

Setup: `mkdtemp` base `.../swpin_t1_fau225um`, pin requested at `.../pin`, outside canary `.../outside/canary.txt` bytes `CANARY-SAFE-T1`.

Pinned identity at open: path `/private/var/folders/vg/3mw0sd2j7f12frh367wggw340000gn/T/swpin_t1_fau225um/pin`, device `16777233`, inode `36344446`. After the calls, `fstat` and `F_GETPATH` on the retained descriptor still reported that device, inode, and path.

| Operation | Return | Filesystem |
|---|---|---|
| `write_file(..., root=...)` | `TypeError`: unexpected keyword `root` | Raised before the body. |
| `write_file(root, relative, content)` as four positionals | `TypeError`: takes 3 positional arguments but 4 were given | Raised before the body. |
| `verify_file(..., root=...)` | `TypeError`: unexpected keyword `root` | Raised before the body. |
| `write_file("../escaped.txt", ...)` | `ok: false`, `status: "rejected"`, `reason: "path_dot_segment"`, `audit_recorded: true` | `.../escaped.txt` exists false. |
| `write_file(<absolute path>, ...)` | `ok: false`, `status: "rejected"`, `reason: "path_absolute"`, `audit_recorded: true` | absolute target exists false. |
| `write_file("legal.txt", "PINNED_SENTINEL_8f3c1d0e")` | `ok: true`, `status: "verified"`, `verification: "match"`, `accepted: true`, `audit_recorded: true`, size 24, mode 0644 (`420`), sha256 `900438a953f90ba4918b37af766f374bd8818f8baba3f45fbb4e4f7b1c50935a` | Independent `O_NOFOLLOW` read: same 24 bytes, inode `36344449`, device `16777233`, nlink 1. |
| `verify_file("legal.txt", same text)` | `ok: true`, `verification: "match"`, same sha256 | Pin listing names: `.scratch_write_audit.jsonl`, `legal.txt`. |

Canary after: inode `36344448`, size 14, mtime_ns `1794193405424295049`, same as before. Outside listing names: `canary.txt` only. Base listing names: `outside`, `pin`. `x.txt` is absent. Sentinel text and the escape body are absent from the audit text.

Audit file inode `36344452`, size 889, four records:

1. write `legal.txt`, accepted true, reason `verified`, verification `match`.
2. verify `legal.txt`, accepted true, reason `verified`, verification `match`.
3. write `../escaped.txt`, accepted false, reason `path_dot_segment`.
4. write of the absolute path, accepted false, reason `path_absolute`.

All 15 T1 checks in the JSON are true. The old `write_file(root, ...)` API was not called in T1. The 56-test file covers that API. T1 created no file outside the pin.

## 7. T8 — protected paths

Command:

```text
python3 -m unittest tests.test_pinned_writer.PinnedWriterCampaign.test_t8_protected_paths
```

First run: `Ran 1 test in 0.008s`, exit 1, verdict `FAIL` in `/tmp/scratch_writer_t8_scoring_bug.json`.
Security checks on that run were already true: every open refused, no pin returned, `protected_open_attempts` is `[]`, inodes stable, `content_identity` `PASS`. The failing check was `probe_names_absent: false`. The scorer treated “this path exists” as “the synthetic probe is present,” so `faiss.index`, `memory_meta.json`, and `summary.json` failed a check they were never supposed to fail. The scorer was corrected so only the name `pinned_probe_8f3c1d0e.txt` counts as the probe, and so existing protected paths must still exist afterward. The security outcome was not reclassified. The first JSON was kept.

Official rerun: `Ran 1 test in 0.005s`, `OK`, exit 0.
Evidence: `/tmp/scratch_writer_t8.json`. Verdict: `PASS`. `content_identity`: `PASS`.
`protected_open_attempts`: `[]`. All six checks true. `probe_after` is false for every target.

The guard records an `os.open` of a protected path and raises `EPERM` before the real open. Zero protected opens were recorded.

| Target | Raised | Pin returned |
|---|---|---|
| `/Users/richietate/Desktop/FeralEcho` | `root_protected` | false |
| `.../FeralEcho/memory` | `root_protected` | false |
| `.../FeralEcho/app/core` | `root_protected` | false |
| `/Users/richietate/Desktop/FeralEcho-voyager` | `root_protected` | false |
| `.../voyager_lab/voyager` | `root_protected` | false |
| `.../voyager_lab/results` | `root_protected` | false |
| `.../memory/faiss.index` | `root_not_directory` | false |
| `.../memory/memory_meta.json` | `root_not_directory` | false |
| `.../results/summary.json` | `root_not_directory` | false |
| `.../memory/pinned_probe_8f3c1d0e.txt` (absent) | `root_missing` | false |

T8 window, before and after identical (lstat only; bodies were not read or hashed):

| Path | inode | size | mtime_ns | mode |
|---|---|---|---|---|
| `memory/faiss.index` | 36343287 | 240826413 | 1794193134142855521 | 0644 |
| `memory/memory_meta.json` | 36343158 | 135792931 | 1794193134065796598 | 0644 |
| `voyager_lab/results/summary.json` | 36269403 | 57749 | 1794179724623157658 | 0600 |
| `memory/` directory | 635294 | 4256 | 1794193509991944984 | — |

Every recorded delta has `inode_changed`, `size_changed`, and `mtime_changed` false, and `exists_before == exists_after`. The absent probe stayed absent.

A later lstat, after the campaign and while the live server was still running, shows different FAISS and `memory_meta.json` identities (FAISS inode `36348112`, size `240827949`; `memory_meta.json` inode `36348106`, size `135795199`). OBSERVED: those files changed after the T8 samples. VERIFIED for the T8 window: the samples match and `os.open` was not called. INFERENCE: the live server continued its own writes. That later change is outside T8 and is not a T8 failure.

## 8. T2 — live directory rename during a write

Command:

```text
python3 -m unittest tests.test_pinned_writer.PinnedWriterCampaign.test_t2_live_rename
```

First run: `Ran 1 test in 0.055s`, exit 1. Evidence preserved at `/tmp/scratch_writer_t2_scorer_mismatch.json`.
Writer result on that run: `ok: false`, `accepted: false`, `audit_recorded: false`, `status: "rejected"`, `reason: "identity_mismatch"`, `verification: "not_run"`, path `published.txt`. Replacement listing empty. Moved listing empty. `renamed_during_call: true`. The only false scoring check was `cleanup_matches_listing`, because the scorer required `status == "identity_mismatch"`. The writer’s cleaned-publication status is `"rejected"` with reason `"identity_mismatch"`, which is the shape in section 4. The scorer was aligned to that shape and to the leftover-name rules for `publish_cleanup_failed` and `temp_cleanup_failed`. Design failure conditions were not met: the replacement did not contain the file, and `ok` was not true.

Preserved first-run tree, re-listed in this session (left on disk):

Base `/private/var/folders/vg/3mw0sd2j7f12frh367wggw340000gn/T/swpin_t2_01_s_rrf72g`.

| Directory | inode | device | names | nlink | size |
|---|---|---|---|---|---|
| `pin` (replacement created at the old path) | 36347523 | 16777233 | `[]` | 2 | 64 |
| `moved` (original pinned directory) | 36347521 | 16777233 | `[]` | 2 | 64 |

Those inodes match the first-run JSON (`pin_ino` 36347521 moved aside; replacement inode 36347523). Empty-directory size 64 and nlink 2 are `.` and the parent. No audit file is present.

Official rerun: `Ran 1 test in 0.004s`, `OK`, exit 0, one trial.
Evidence: `/tmp/scratch_writer_t2.json`. Verdict: `PASS`. The passing test deleted that trial’s base after recording identities. Those official-pass directories were not re-stat’d. The preserved tree above is the independent inspection, and it has the same outcome shape.

Official trial 1:

- Payload: 1048576 bytes of `Z`. SHA-256 `bf63d8a95fcc2e64619813aae35fdcbe871fdd9264caa3f365eb3aed0f679129`. The body is not stored in the JSON.
- Temp name observed: `.swtmp_c5e5158901d15e20487428ed76d73fd4`.
- `saw_temp: true`, `renamed_during_call: true`, `refused_post_return: false`, `fatal: false`, `writer_error: null`.
- Result: `ok: false`, `accepted: false`, `audit_recorded: false`, `status: "rejected"`, `reason: "identity_mismatch"`, `sha256: null`, `size: null`, `verification: "not_run"`, path `published.txt`.
- Pinned path at open: `/private/var/folders/vg/3mw0sd2j7f12frh367wggw340000gn/T/swpin_t2_01_l54wjyek/pin`, device `16777233`, inode `36347703`.
- After the call, the retained descriptor’s `F_GETPATH` was `.../moved` and its inode was still `36347703`.
- Replacement directory at the old path: inode `36347705`, listing `[]`, audit absent.
- Moved directory: inode `36347703`, listing `[]`, audit absent.

All ten scored checks are true, including `replacement_empty`, `moved_inode_is_pin`, `replacement_inode_differs`, `no_success_audit`, `ok_false`, and `file_not_reported_verified`. `success_audit` is `[]`.

The poller renames only while `write_file` has not returned and a stack frame is still inside `pinned_writer.py`, and only when a `.swtmp_*` name is visible. A rename after return is discarded as `refused_post_return`. No sleep was inserted in the writer. The poller does not take `OPERATION_LOCK`.

Which of the writer’s internal windows was hit is UNKNOWN. Seeing the temp name shows overlap with the temp’s lifetime, which includes the write. The 0.004s pass does not prove the 1 MiB body was fully written. Both successful cleanup paths return the same reason and leave both directories empty, so “before link” and “link then unlink” are not separated by this evidence.

## 9. Audit behavior and cleanup behavior

Success audit is a JSON line with `accepted: true`, `verification: "match"`, and `reason: "verified"`. T1’s legal write and legal verify produced those two lines inside the pinned directory. T1’s path rejections were audited with `accepted: false` while the pin still held.

On pin loss, `ScratchWriter` skips every audit append, success and failure. T2’s official trial and the preserved first trial both have `audit_recorded: false` and no audit file on either directory inode.

Cleanup that removes the names this call created returns `identity_mismatch` and `ok: false`. If the final-name unlink fails, the status and reason are `publish_cleanup_failed`, `ok` is false, the name is left, and there is no audit. If the temp unlink fails after a successful final unlink, or the unpublished temp cannot be removed, the status and reason are `temp_cleanup_failed`. `publish_cleanup_failed` and `temp_cleanup_failed` were not observed in this campaign. Verify does not unlink a pre-existing file when the pin is lost.

## 10. Residual race limitations

Darwin provides no userspace operation that links or writes only if a directory’s path is still a chosen string. `F_GETPATH` and `fstat` are checked, and then `os.write`, `os.link`, or `confine.append_audit` runs as a later call. A rename in that interval can still land bytes on the pinned inode after the check has passed. The implementation then tries to unlink the name this call published, through the same directory descriptor, and it withholds `ok: true` and the success audit when a later check sees the move.

That cleanup is itself a later call. A second rename after the cleanup check, or a process killed between link and unlink, can leave a name on the moved inode. This campaign did not observe that leftover. T2 does not prove the interval is closed.

`confine.append_audit` is reached only after a passing pin check, and the pin is checked again after the append. An append that completes onto a directory renamed during that append can leave a line on the moved inode while the return value is a failure. A success audit on the moved inode would be a campaign failure. None was present.

`OPERATION_LOCK` is process-local. Same-name publication across processes is the `link` `EEXIST` gate. Cross-process audit interleaving was not tested. `O_APPEND` on this regular file is not a multi-process atomic record boundary.

## 11. Git status and changed-file summary

After bytecode removal, and with this report included:

```text
git status --porcelain
?? voyager_lab/

git diff --stat
```

`git diff --stat` is empty. HEAD remains `dc8d6eb9b6479ef323614cd6820bb050a14299eb`. No commit, merge, or push was made. The whole `voyager_lab/` tree is untracked, so porcelain shows one untracked directory rather than per-file deltas. The files this assignment added under `scratch_write/` are `pinned_writer.py`, `tests/test_pinned_writer.py`, and this report.

## 12. Production and frozen Voyager files

No production source file was edited. No command connected to port 5000, signaled the live process, or called Echo. FAISS and `memory_meta.json` were not read or hashed.

Frozen identities, re-lstat’d while writing this report, match the known frozen files:

| Path | inode | size | mode | mtime_ns |
|---|---|---|---|---|
| `voyager_lab/voyager/engine.py` | 36256079 | 19977 | 0644 | 1794177805925011044 |
| `voyager_lab/voyager/worker.py` | 36260012 | 1398 | 0644 | 1794178781409311138 |
| `voyager_lab/results/summary.json` | 36269403 | 57749 | 0600 | 1794179724623157658 |

`summary.json` is the same inode, size, mode, and mtime recorded inside the T8 window. The frozen experiment was not rerun. The file-skill experiment was not run.

## 13. Unresolved limitations

- The check-to-syscall interval remains. Section 10 is the precise bound.
- T2 does not identify which internal window the rename hit.
- `publish_cleanup_failed` and `temp_cleanup_failed` were not exercised.
- Cross-process audit interleaving was not tested. T2 is a same-process thread.
- Nested-path temp cleanup was not in the authorized set. T1 and T2 use one path component.
- T1 did not call the older root-accepting `write_file`. That function still accepts a caller root. The new interface does not.
- A directory the denylist does not name, such as `Documents`, was not used as a pin and was not written.
- The implementation is not registered as an Echo tool and is not on a production import path.

## 14. Decision

**GO.** Retain `pinned_writer.py` and `tests/test_pinned_writer.py` as a verified lab artifact.

The four mandatory acceptance conditions passed: the original 56 tests, T1, T8, and T2. The two first-run failures were scorer mismatches against filesystem outcomes that already met the security rules. Those evidence files were kept. No stop condition in the assignment fired.

This GO authorizes nothing else. It does not authorize Echo integration, tool registration, production use, a commit, Seatbelt, or the file-skill experiment.

## Acceptance table

| Requirement | Result | Evidence |
|---|---|---|
| Existing 56 tests | PASS | `python3 -m unittest tests.test_scratch_write` — 56 tests, 0.185s, OK, exit 0. Prototype hashes in section 2 match. |
| T1 root substitution | PASS | `/tmp/scratch_writer_t1.json`. Three `TypeError`s on `root`. Escape and absolute writes `ok: false`. Escape and absolute targets exist false. Canary inode 36344448 unchanged. Legal file only inside the pin. |
| T8 protected paths | PASS | `/tmp/scratch_writer_t8.json`. Ten refusals, zero protected `os.open` calls, inode/size/mtime unchanged inside the window. First-run scorer bug preserved at `/tmp/scratch_writer_t8_scoring_bug.json`. |
| T2 live rename | PASS | `/tmp/scratch_writer_t2.json`. Trial 1, `ok: false`, replacement inode 36347705 empty, moved inode 36347703 empty, no success audit. Independent re-list of the preserved first trial at `.../swpin_t2_01_s_rrf72g`. |
| Prototype unchanged | PASS | Eight baseline hashes in section 2. `git diff --stat` empty. |
| Production untouched | PASS | T8 lstat window stable and `os.open` not called. Frozen `engine.py`, `worker.py`, and `summary.json` identities unchanged. No production source edit and no port 5000 contact. Later FAISS movement is outside the T8 window. |
