# Scratch-write security report

Date: 2026-11-08

Host: macOS, Python 3.13 (`cpython-313` bytecode). Interpreter flags used by the tool: `O_NOFOLLOW`, `O_DIRECTORY`, `O_EXCL`, `O_CLOEXEC`, `F_GETPATH` with a 1024-byte buffer.

Scope: the laboratory package at `/Users/richietate/Desktop/FeralEcho-voyager/voyager_lab/scratch_write/`. No production tool was registered. No model was called. The local file-skill experiment was not run.

## Runs

### Run 1 — one assertion failed, filesystem state matched the intended failure

Command:

```bash
cd /Users/richietate/Desktop/FeralEcho-voyager/voyager_lab/scratch_write
python3 -m unittest tests.test_scratch_write -v
```

Result: 56 tests, 55 ok, 1 failure. `test_c_failure_temp_cleanup`.

The failure was `AssertionError: 2 != 1` inside `_assert_created`, which requires `st_nlink == 1`. That helper is for a finished file whose temp name has been removed. This case deliberately leaves the temp name in place, so the destination link count is 2.

Checks that had already passed in that test, before the helper:

- `ok` was false
- `status` was `temp_cleanup_failed`
- `verification` was `match`
- `audit_recorded` was true

`_assert_created` had also already confirmed the destination bytes were `b"body"`, the file was a regular file, it was not a symlink, and the mode was `0644`. The link count of 2 is the cleanup-failure state the rest of the test asserts (`st_nlink >= 2`, one `.swtmp_*` name, same inode).

No expected security result was flipped to success. The helper call was replaced with a direct read that keeps the mode and content checks and leaves the link-count check at `>= 2`.

`tearDownModule` of run 1 did not report a hash or manifest mismatch.

### Run 2 — passing run

Same command, after the assertion correction.

```
Ran 56 tests in 0.176s
OK
```

56 ok, 0 failures, 0 errors, 0 skipped. No `SCRATCH_WRITE_NOTES` line. That line is printed only when `memory/faiss.index` changes mtime while inode and size stay the same across the suite process. It was absent.

## Tests and what each one checked on disk

Normal operation, all ok:

- `test_a_normal_containment_uses_commonpath` — Voyager is not inside production by `commonpath`, even though the Voyager path starts with the production path's characters. `/tmp` and `Desktop` are protected. The temp scratch root is not.
- `test_a_normal_signatures_and_lock` — signatures are exactly `(root, relative_path, content)` and `(root, relative_path, expected_content)`. The write lock is `confine.OPERATION_LOCK`.
- `test_a_normal_source_isolation` — the three modules do not import the banned modules, do not call builtin `open`, `os.system`, or `os.popen`, and do not contain the text `5000`.
- `test_a_normal_create_file` — new file bytes, mode `0644`, `nlink == 1`, `verify_file` match, independent `O_NOFOLLOW` read, audit has no file body.
- `test_a_normal_subdirectory` — file created in a directory the test created. The tool did not create the directory.
- `test_a_normal_unicode` — `café — 日本語` plus a second line.
- `test_a_normal_multiline` — `alpha\nbeta\r\ngamma\n`.
- `test_a_normal_empty` — empty regular file.
- `test_a_normal_max_size_accepted` — exactly 1,048,576 bytes of `a`.
- `test_a_normal_umask_exact_mode` — mode `0644` under umask `0o077`.
- `test_a_normal_content_is_not_executed` — a program-shaped body did not create its sibling marker. Mode had no execute bits.
- `test_a_normal_open_root_fd_path` — `F_GETPATH` matched `realpath` for the temp root.
- `test_a_normal_nul_in_content_is_data` — a NUL byte stayed in the file and out of the audit line.

Prohibited operations, all ok. Each one asserted the canary or destination bytes, inode, and mode, not only the return dict:

- `..`, `.`, and empty components
- absolute path aimed at a sibling canary
- overwrite, including identical bytes
- APFS case-fold: `Hello.txt` then `hello.txt` → `destination_exists`, original bytes `b"ONE"`, `samefile` true
- NFC/NFD: `café.txt` then `cafe` + combining acute → `destination_exists`, original bytes unchanged, `samefile` true
- symlink as the destination
- symlink directory and symlink file used as a parent escape; the outside directory listing stayed `["safe.txt"]`
- directory destination, Unix socket, fifo
- symlink to `/dev/null` (`symlink_destination`); `/dev/null` as a root (`root_not_directory`); `st_rdev`, mode, and inode of `/dev/null` unchanged
- `mode=` raises `TypeError` and creates nothing; a pre-existing mode `0755` stays `0755`
- shebang body stored as mode `0644`
- oversized character string and oversized UTF-8 (262,145 emoji, 1,048,580 bytes)
- unsupported types: `bytes`, `bytearray`, `None`, `int`, `float`, `list`, `dict`, a `str` subclass, and a `pathlib.Path` root
- `%2e%2e/%2e%2e/...` does not escape; the literal component can be created and the outside canary stays
- reserved audit name and `.swtmp_*` names, including a nested audit name
- missing parent is not created
- `assert_fd_inside` on a descriptor opened outside the scratch root returns `escape`
- `/tmp` and `Desktop` rejected as roots; the unique probe name was not created under `/private/tmp`
- relative root does not write into the package directory
- symlink root and NUL root create nothing
- audit path is a symlink, and audit path is a hard link: outside bytes unchanged, `ok` false
- hard-linked destination name: both copies keep `b"CANARY-SAFE"`

Failure handling, all ok:

- `_write_all` writes `b"PARTIAL"` and raises `EIO`: destination absent, no `.swtmp_*`, keeper unchanged, audit contains neither `PARTIAL` nor `COMPLETE`
- `os.open` of a `.swtmp_*` name raises `EIO`: no destination
- parent mode `0555`: `write_failed`, directory listing empty, mode restored by the test
- read-back patched to append `b"-LIE"`: `verification_failed` / `mismatch`, real bytes remain `requested-body`, reported hash differs
- `_unlink_temp` raises: `temp_cleanup_failed`, `ok` false, body correct, mode `0644`, one temp name, same inode, `nlink >= 2`
- `append_audit` raises: `audit_failed`, file bytes correct, `audit_recorded` false
- after a verified `hello world`, the test truncates the file to `hello`: `verify_file` reports mismatch and the actual 5-byte hash; inode and mtime stay
- missing file: `verification` `missing`, path still absent
- symlink whose target text equals the expected string: `symlink_destination`, target inode and mtime unchanged
- two threads, one path: exactly one `ok`, body is `AAAA` or `BBBB`, not a concatenation, mode `0644`

Boundary, all ok:

- Directories rejected with `root_protected`, probe absent, audit name absent: production root, `memory/`, `app/`, `app/core/`, Voyager worktree, `voyager_lab/`, `voyager_lab/voyager/`, `voyager_lab/results/`. Inode compared on every directory. mtime and size compared on the four that are not live server directories.
- Every path in `FROZEN_FILES` rejected with `root_not_directory`. SHA-256, inode, size, mtime, and mode matched across the call. The list is `echo_principles.json`, `Modelfile`, `run.py`, `app/core/echo_tool_dispatch.py`, the ten modules under `voyager_lab/voyager/`, `self_check.py`, `freeze.py`, `run_experiment.py`, `RUBRIC_FREEZE.json`, `results/summary.json`, `FIRST_LOCAL_SKILL_RESEARCH.md`, `CAB_ADVERSARIAL_REVIEW.md`, `ASSESSMENT.md`, `CAPABILITY_ACQUISITION.md`, `voyager_lab/README.md`, and the three scratch modules.
- `memory/faiss.index` rejected with `root_not_directory`. Inode, size, mtime_ns, and mode matched across that call. The index was not opened and was not hashed. Probe and audit names were absent from `memory/`.
- A sibling `outside.txt` in the temp parent kept `b"OUTSIDE"` and the same inode and mtime after an absolute path, a `..` path, and an attempt to use the file as a root.

`setUpModule` / `tearDownModule` of the passing run compared SHA-256 identities of `FROZEN_FILES` and full tree manifests of `voyager_lab/results` and `voyager_lab/voyager` (kind, mode, inode, size, mtime_ns, and hash). Import of the three modules compared faiss inode and size before and after the import. No mismatch was reported.

## Independent check after the passing process exited

Performed in a new shell. This does not replay the suite's in-process hashes.

- `git status --porcelain` in `/Users/richietate/Desktop/FeralEcho-voyager`: `?? voyager_lab/` only. `git diff --stat` empty. HEAD `dc8d6eb9b6479ef323614cd6820bb050a14299eb`.
- Search for `scratch_write_probe_8f3c1d0e.txt`, `.scratch_write_audit.jsonl`, and `.swtmp_*` under the production tree, the Voyager worktree, `/tmp`, and `/private/tmp`: no matches.
- `lsof` showed the already-running listener `python3.1` pid 65139 on `*:5000`. No connection was opened to that port. `lsof` reads the local socket table.
- `lstat` of `memory/faiss.index` after the suite: regular file, mode `0644`, not a symlink, inode `36314985`, size `240784941`, mtime_ns `1794188935918876606`. The passing suite's own before/after check found no inode, size, or mtime change during that process, and it did not print the baseline numbers. This later size is an observation after the process exited, while pid 65139 was still the listener. The index bytes were not read.

## Skipped tests

None. Device nodes were not created, because that would require extra privilege. The device cases that did run are the symlink to `/dev/null` and the rejection of `/dev/null` as a root.

## Unresolved risks

The passing suite does not close these:

- A caller with its own write privilege can bypass this API.
- The protected-path list is local to this machine. A Desktop subdirectory outside the two project trees is not refused automatically.
- A rename of the scratch directory by another process, after the last `F_GETPATH` and before the write, can place the new bytes on the moved inode. No test hammers that race.
- A killed process can leave a `.swtmp_*` file inside the scratch root, and it can leave a partial final audit line.
- Cross-process overlap was not executed. The in-process lock and `link`/`EEXIST` are the mechanisms. Only threads were tested.
- `F_GETPATH` and the 1024-byte buffer are properties of this Darwin interpreter.
- APFS case-folding and NFC/NFD collisions were measured here. Another volume can differ. On this volume those collisions rejected the second create and kept the first bytes.
- The audit log inside a long-lived scratch root is unbounded.
- Parent `fsync` is best-effort after a successful link.
- This report does not claim the tool is secure against every attack.

## Operational boundaries of this session

- Production Echo was not sent a request.
- Port 5000 was not connected to. The existing listener was observed with `lsof`.
- Production memory bodies were not read. `memory/` was a rejected root. Small production sources in `FROZEN_FILES` were hashed by the suite to compare identity.
- `memory/faiss.index` was not opened and was not hashed. It was `lstat`'d and offered as a rejected root.
- Frozen Voyager modules and `voyager_lab/results` were compared by the suite and were not edited. `git diff` on the worktree is empty.
- The tool was not added to Echo's tool list.
- No shell command is executed on behalf of a model. The implementation has no `subprocess` import.
