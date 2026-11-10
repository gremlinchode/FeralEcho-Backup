# Scratch-writer security design

Date: 2026-11-08
Status: design only. Nothing in this document is implemented, registered, or authorized to run.
Baseline: `confine.py`, `write_file.py`, `verify_file.py`, and `tests/test_scratch_write.py` (56 tests, reported passing in `SECURITY_REPORT.md`). Those files stay as they are.

`INDEPENDENT_SECURITY_REVIEW.md` is not in this directory. The prior review was checked against the current source for this design. The load-bearing observations below match that source.

## 1. Executive recommendation

Build the next version in the Voyager lab only: a host-owned directory pin, and two functions that do not take a root. Keep the current `write_file(root, ...)` functions unregistered and unchanged in behavior.

Do not register an Echo tool, do not run the file-skill experiment, and do not connect this to the live server until the verification campaign in section 6 has passed.

A hardcoded root inside a function Echo can still call does not fix the current API. `write_file` opens whatever absolute directory the caller passes, on every call, and the denylist is only the two project trees plus nine exact broad paths.

Seatbelt is not the first control. `sandbox(7)` on this Mac says restrictions apply when a process acquires a resource: an already-open writable descriptor remains usable after a later write restriction. A sandbox profile would not stop bytes already aimed at the held directory object.

## 2. Proposed architecture and trust boundary

### What is wrong today

Verified in source:

- `write_file(root, relative_path, content)` and `verify_file(root, relative_path, expected_content)` take `root` from the caller.
- Every call runs `open_root`, which `lstat`s, `realpath`s, and `os.open`s that string. `OpenRoot` stores the descriptor and the path string. It does not store `st_dev` or `st_ino`.
- `is_protected_path` refuses `PROTECTED_ROOTS` (`FeralEcho`, `FeralEcho-voyager`) and the exact `BROAD_ROOTS` list (`/`, `/tmp`, `/private/tmp`, `/var`, `/private/var`, `/private`, `/Users`, `/Users/richietate`, `/Users/richietate/Desktop`). Any other real directory is eligible.
- After open, creates and links use `dir_fd`. A new directory placed at the old path does not receive those operations.
- `assert_fd_inside` takes `F_GETPATH`, then `is_within` calls `realpath` on that string. That re-walks the name. A rename of the same vnode changes `F_GETPATH` and does not change the inode.
- `append_audit` writes through the directory descriptor and does not recheck the path.
- `_place_file` links, then reads the result back. If a later check fails, the published name is left in place (`linked` is already true, and the read sits outside the cleanup that only unlinks the temp when `linked` is false).
- `OPERATION_LOCK` is a `threading.Lock` in one process.

### Call flow

```
operator configuration (one absolute path, set before any model call)
        |
        v
host startup
  lstat the path
  reject symlink, non-directory, protected path, broad path
  open O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC
  fstat -> store (st_dev, st_ino)
  F_GETPATH -> store that exact string
  require F_GETPATH == realpath taken before open
  hold PinnedRoot for the life of the process
        |
        v
tool registry
  exposes only:
    write_file(relative_path, content)
    verify_file(relative_path, expected_content)
  laboratory write_file(root, ...) and verify_file(root, ...) are not registered
        |
        v
Echo tool call
  dispatcher drops unknown fields (including any root)
  bound function rechecks the pin
  existing relative-path rules
  dir_fd create, fsync, recheck, link
  recheck again
  on a failed recheck after link: unlink that new name through the directory fd
  read back
  append one audit line only if the pin still matches
  ok is true only for a matching file plus a recorded audit line
```

### Where the boundary sits

The trusted component is the host process the operator starts. It is trusted because the scratch path comes from operator configuration, the descriptor is opened before Echo can call a tool, and the registered schema has no root parameter. Echo submits a relative filename and content. Host code decides which descriptor those arguments apply to.

The boundary is that dispatch edge, plus the pin checks inside the write path. Both are required. Hiding the root argument and then calling today's `write_file(configured_path, ...)` is not the design: that function opens the path again and will accept a different directory at the same path on the next call.

This holds only while Echo has no other write primitive and cannot call the laboratory functions. This capability does not itself enforce that process isolation.

### Exact host interface

Laboratory functions stay:

```python
write_file(root, relative_path, content) -> dict
verify_file(root, relative_path, expected_content) -> dict
```

New host surface, constructed once at startup:

```python
class PinnedRoot:
    fd: int
    path: str          # F_GETPATH at open
    dev: int           # st_dev at open
    ino: int           # st_ino at open

def open_pinned_root(path: str) -> PinnedRoot: ...

class ScratchWriter:
    def __init__(self, pin: PinnedRoot): ...
    def write_file(self, relative_path: str, content: str) -> dict: ...
    def verify_file(self, relative_path: str, expected_content: str) -> dict: ...
```

`ScratchWriter.write_file` and `verify_file` accept exactly those parameters. An extra `root=` argument raises `TypeError` and does not touch the filesystem.

The implementation cannot be a wrapper alone. `_write_opened` already accepts an open root, but the race is inside `_place_file` and `append_audit`. The pin checks have to sit immediately before `_write_all`'s commit point, immediately before `os.link`, and at the start of `append_audit`. `open_root`'s current behavior stays the default so the 56 existing tests keep their meaning.

### Identity check

On the scratch directory descriptor:

- `fstat` must still return the pinned `(st_dev, st_ino)`. The inode matches after a rename. It differs if the descriptor no longer refers to the opened directory.
- `F_GETPATH` must equal the stored path string, byte for byte. Do not `realpath` that string. A rename fails this comparison.

Apply the directory check to the root descriptor and to a parent descriptor only after `F_GETPATH` of that parent is the expected child of the pinned path. Do not compare a file descriptor's inode with the directory inode. Those are different objects. For a file descriptor, require `F_GETPATH` to equal the pinned directory path plus the relative name already accepted, and require the root descriptor's `fstat` to match the pin.

On mismatch before `link`: unlink the `.swtmp_*` name through the directory descriptor, do not link, do not write an audit line, return failure.

On mismatch after `link`: unlink the final name this call just created, through that same directory descriptor, then return failure. If that unlink fails, return `publish_cleanup_failed`, `ok` false, and leave the name in place for a human to inspect. Do not report `verified`.

If the directory inode no longer matches, do not unlink. The descriptor is no longer known to be the original directory.

Write a success audit line only after the file bytes match and the pin matches. If the pin does not match, skip the audit append. An audit line in the moved directory would claim a success in the wrong place. The in-memory return value still reports the failure.

## 3. Exact proposed tool interface

Echo receives only:

```python
write_file(relative_path, content) -> dict
verify_file(relative_path, expected_content) -> dict
```

Return dict, same keys as today: `accepted`, `audit_recorded`, `ok`, `operation`, `path`, `reason`, `sha256`, `size`, `status`, `verification`.

`ok` is true only when `status == "verified"`, `verification == "match"`, `accepted` is true, and `audit_recorded` is true. A matching file with a failed audit is `audit_failed` and `ok` false. A recorded audit with a mismatched file is `ok` false. Callers must not treat one as the other.

Limits, carried forward from the current writer:

| Rule | Value |
|---|---|
| Content type | plain `str` only. Subclasses, bytes, and other types are refused. |
| Encoding | UTF-8 strict. A lone surrogate is `content_unencodable`. |
| Maximum size | 1,048,576 characters before encoding, and 1,048,576 bytes after encoding. |
| Path type | one relative `str`. Absolute paths, backslashes, and NUL are refused. |
| Path syntax | no empty component, no `.` or `..`, no ASCII control or DEL. No URL decoding. No Unicode normalization. |
| Path caps | 1024 characters, 255 UTF-8 bytes per component, depth 32. |
| Reserved names | `.scratch_write_audit.jsonl` and any component starting with `.swtmp_`. |
| Parents | must already exist. The tool does not create directories. |
| Overwrite | never, including identical content, case-folded names, and NFC/NFD collisions on this volume. |
| New file mode | `0644` after `fchmod`. No mode argument. |
| Existing mode | a pre-existing file is `destination_exists` and is not chmod'd by `verify_file`. |
| Execution | the tool does not execute content, start a shell, or import the written file. |
| Audit | one JSON object per line, ASCII, sorted keys, payload excluded. Appended only through the scratch directory descriptor. |

`verify_file` reads with `O_NOFOLLOW`, does not create the file, and does not follow a symlink even when the target text matches. A missing file is `verification_failed` / `missing`.

The tool must refuse: a root argument, a protected or broad directory, a symlink root, a symlink path component, a symlink destination, a directory, socket, fifo, or device at the destination, an existing regular file, a reserved name, a missing parent, a path that fails the pin, and any result whose read-back or audit step failed.

## 4. Root ownership and directory identity

Ownership: the operator chooses the path. The host opens it once at startup and keeps the descriptor. Echo never receives the path, the descriptor, or a way to reopen it.

Startup fails closed unless all of these are true: the path is an absolute `str` with no NUL; `lstat` shows a directory and not a symlink; `is_protected_path` is false; `os.open` with `O_DIRECTORY|O_NOFOLLOW` succeeds; `F_GETPATH` equals the pre-open `realpath`; `fstat` yields one device and inode, which are stored.

The scratch directory must sit outside both project trees. The existing denylist already rejects those trees. Startup uses that same check. A Desktop subdirectory outside the two trees remains eligible if the operator points at it; the host does not invent a wider denylist in this version. The operator is responsible for not choosing a sensitive directory. Echo is not.

Identity during a call is the pair `(device, inode)` plus the path string, as section 2 defines. Descriptor-relative `open`, `link`, and `unlink` stay. `os.replace` and `os.rename` stay unused.

## 5. Race-condition limitations

The pin can guarantee three things when a check actually runs:

- A replacement directory at the old path does not receive `dir_fd` operations. That is already how the prototype works.
- A rename that is visible at a check point fails the call. `ok` stays false. A success audit line is not appended.
- A name this call published, if a later check sees the directory has moved, is unlinked through the original descriptor before the function returns, when that unlink succeeds.

The pin cannot guarantee:

- Closing the interval between a passing check and `os.write` or `os.link`. Darwin has no `openat2` / `RESOLVE_BENEATH`. Userspace can sample `F_GETPATH` and then lose the race. Bytes can land on the moved inode in that interval.
- Cleanup of a publish that races again after the cleanup check, or of a process killed between `link` and `unlink`.
- That `sandbox-exec` would remove the race. `sandbox-exec(1)` is marked deprecated and points developers at App Sandbox. `sandbox(7)` states that an already-open writable descriptor may still be used after write restrictions are in place. App Sandbox around the whole Echo server would also break memory, FAISS, logs, and model I/O. It is the wrong first control.
- Cross-process audit atomicity. The append is `O_APPEND` without `flock`. POSIX `PIPE_BUF` atomicity applies to pipes, not to this regular file. Whether this volume interleaves short writes is untested.
- Anything about a process that can write the filesystem without using this tool.

Seatbelt on a helper process is worth a later look only as a second layer that blocks new opens outside one path. It is not necessary for this first capability, and it is not a substitute for the pin. Cost of doing it now: a separate helper, a generated profile, IPC, and a deprecated interface, without a documented guarantee about `linkat` on an already-held directory descriptor. That last behavior is UNKNOWN. Evidence that would resolve it is a small Seatbelt trial that renames the directory after `open` and attempts `linkat` on the held descriptor. That trial is not part of this design and is not authorized here.

## 6. Prioritized adversarial verification plan

Do not run these tests under this document. A later assignment has to authorize them. Preserve the 56 current tests and run them first after any implementation. A failure there stops the campaign.

Filesystem evidence for every test: return dict; `lstat` of the scratch directory and of every new name (`st_dev`, `st_ino`, `st_nlink`, mode, size); SHA-256 of file bytes read with `O_NOFOLLOW`; directory listing of the original path, the renamed path, and any replacement; the audit file's bytes; a canary file outside the scratch directory, compared by inode and bytes.

A file match and an audit record are scored separately.

### T1. Root substitution (do this first)

What: Echo's registered functions cannot be aimed at another directory.
How: Call `ScratchWriter.write_file` with a `root` keyword. Call it with a relative path of `../outside.txt` and an absolute path. Separately call the laboratory `write_file` on `/Users/richietate/Documents` or another real unprotected directory and record that it still accepts that root. That call confirms the old API is unchanged and must stay unregistered.
PASS: The bound calls raise `TypeError` or return `ok` false with no file created anywhere; the outside canary is unchanged. The laboratory call's acceptance of an unprotected root is recorded as expected, not as a bound-API success.
FAIL: A bound call creates a file outside the pinned inode, or accepts `root=`.
UNKNOWN if skipped: Whether dispatch filtering alone is enough. Source inspection cannot see a future registration mistake.

### T2. Rename and replacement during a write

What: A second process moves the scratch directory, or swaps a new directory onto its path, while a 1 MiB write runs.
How: Record the pin. Process A writes. Process B waits until `.swtmp_*` appears, then renames the scratch directory aside and mkdir's a new directory at the old path. Repeat enough times to hit during the temp write, around `link`, and after the final name appears. Do not modify the writer to sleep.
PASS: The replacement directory never contains the new file or a `.swtmp_*` name. If the original inode was renamed during the call, `ok` is false, no success audit line exists on that inode, and the published name is absent or the result is `publish_cleanup_failed` with the leftover path identified. The canary is unchanged.
FAIL: The replacement inode contains the file; `ok` is true while the file's directory path is not the pinned path; a success audit line sits on the moved inode.
UNKNOWN: Which window was hit if no trial observes a rename between the check and `link`. Absence of a hit is not proof the window is gone. Report the trial count.

### T3. Two processes, same destination

What: Concurrent create of one name.
How: Two interpreters, one pinned directory, same relative path, different full payloads.
PASS: At most one `ok` true. The file is mode `0644`, one complete payload, matching SHA-256, not a mixture. The other result is `destination_exists` when it loses at `link`. Leftover temps are listed.
FAIL: Both `ok` true, or the file bytes are a combination of both payloads.
UNKNOWN: Audit-line interleaving. Score that under T7, not as a file failure.

### T4. Two processes, different destinations

What: Concurrent create of `a.txt` and `b.txt`.
How: Two interpreters, same pinned directory, different names and payloads.
PASS: Both `ok` true, each file equals only its own payload, mode `0644`, two independently parsed audit objects.
FAIL: Either file contains the other payload, either file is not mode `0644`, or one call's file is missing while `ok` is true.
UNKNOWN: Nothing about rename resistance. This test does not move the directory.

### T5. Process termination

What: `SIGKILL` at observable stages.
How: Kill when `.swtmp_*` exists and the final name does not; when the temp size is still short of the payload; when the final name exists and `nlink >= 2`; during a large audit append.
PASS: A kill before `link` leaves no partial published file. A kill after `link` leaves one complete published payload. A later write of a new name can still finish. A later write of the same name returns `destination_exists` only if that published file is present. `ok` is not inferred for the killed process.
FAIL: A short or mixed published file, or a later call treats a temp file as a successful destination.
UNKNOWN: The exact instruction the process died on. The listing is the evidence. An in-process exception is not a substitute for `SIGKILL`.

### T6. Abandoned temporary files

What: `.swtmp_*` left behind is not silently deleted, and a later successful write does not depend on deleting it.
How: Leave a regular `.swtmp_` plus 32 hex digits, a symlink with that prefix, a name that merely contains the prefix, and a hard link to a published file (`nlink >= 2`). Run one new write of a different legal name. Do not add an automatic cleaner in this version.
PASS: The new write's `ok` follows the file and audit rules. Every planted temp, symlink, and extra link is still present afterward, bytes and inodes unchanged.
FAIL: Any planted name is removed, or a symlink is followed.
UNKNOWN: A future janitor policy. This design does not include one. A janitor would need its own authorized design: unlink one name through the pinned descriptor only after `lstat` shows a regular file, the exact temp pattern, the writer uid, and a matching pin, and it would leave `nlink > 1` and every symlink for a human.

### T7. Concurrent and interrupted audit writes

What: Audit bytes stay parseable, and a torn audit does not make `ok` true.
How: Two processes append by writing different files. Separately `SIGKILL` during one large audit append. Parse the log with a strict one-JSON-object-per-line reader. Do not repair lines.
PASS: Every complete line is one object with the expected keys and no file content. A torn last line is a failed audit. Any call whose file matches and whose audit append did not complete has `audit_recorded` false and `ok` false.
FAIL: `ok` true with a torn or missing audit line; two records fused into one line and still treated as success; file content present in the log.
UNKNOWN: Whether a short append on this volume can interleave if the campaign never produces a fused line. Say that the interleave question is unanswered. Do not upgrade it to a guarantee.

### T8. Protected paths

What: The pin cannot be opened on production, Voyager, memory, or FAISS, and a bound write cannot create a probe there.
How: `open_pinned_root` on the production root, `memory/`, `app/core/`, the Voyager worktree, `voyager_lab/voyager/`, `voyager_lab/results/`, and `memory/faiss.index`. Then one bound write using the legal pin, with relative paths that try to escape it. Compare inode, size, and mtime of those targets. Do not hash `faiss.index`. Do not read memory bodies. Do not connect to port 5000.
PASS: Every protected open fails, no probe file appears, and the identity fields of those targets are unchanged across the call. Escape paths return `ok` false.
FAIL: A probe appears, an identity field changes, or `open_pinned_root` returns a pin for one of those paths.
UNKNOWN: Host bugs that write those paths without using `ScratchWriter`. This test does not cover them.

Priority: existing 56 tests, then T1, T8, T2, T5, T3, T7, T4, T6. Stop on the first FAIL.

## 7. Guarantees and non-guarantees

| Claim | State |
|---|---|
| One unraced call stays inside a caller-supplied directory that is not on the denylist; `..`, absolute paths, static symlinks, and an already-outside descriptor are rejected | Already demonstrated |
| Production, Voyager, broad roots, Desktop, `/tmp`, frozen files, and `faiss.index`-as-root are refused; probes stay absent | Already demonstrated |
| No overwrite; new files are mode `0644`; 1 MiB cap; content is not executed; audit excludes the payload; `ok` is false when a simulated audit append fails | Already demonstrated |
| Two threads in one process produce one complete body, `AAAA` or `BBBB` | Already demonstrated |
| `dir_fd` operations remain on the opened directory object if a different directory is put at the old path | Supported by source inspection |
| `F_GETPATH` plus `realpath` can go stale; `append_audit` does not recheck; a published name is kept if a check fails after `link` | Supported by source inspection |
| An ordinary directory outside the denylist is a legal laboratory root | Supported by source inspection |
| An already-open writable descriptor survives a later Seatbelt write restriction | Supported by `sandbox(7)` on this machine |
| `PinnedRoot`, `ScratchWriter` without a root argument, recheck before `link` and before audit, unlink of a name this call just published | Proposed but not implemented |
| Rename or replacement during a write; two processes; `SIGKILL`; audit interleaving | Requires adversarial testing |
| No remaining rename window; Seatbelt revoking a held descriptor; safety against a process that writes without this API; Echo skill, planning, or self-improvement | Fundamentally outside this design |

## 8. Implementation sequence

Do this only under a later authorization. This document does not authorize it.

1. Leave `write_file(root, ...)`, `verify_file(root, ...)`, and the 56 tests behaviorally unchanged.
2. Add an opt-in pin on the open root: `(st_dev, st_ino, path string)`. Unpinned calls keep today's checks.
3. Add the directory recheck immediately before `os.link` and at the start of `append_audit`. Compare the directory inode with the pin, and compare `F_GETPATH` with the stored string. Do not `realpath` the live path.
4. If the recheck fails after this call's `link` succeeded, unlink that final name through the directory descriptor. On unlink failure, return `publish_cleanup_failed` and `ok` false.
5. Skip the audit append when the pin does not match. Never append a success line in that state.
6. Add `ScratchWriter` in a new lab module. It is constructed with `open_pinned_root` and exposes the two rootless methods. Extra keyword arguments raise `TypeError` before any write.
7. Re-run the existing 56 tests. They must pass before any new test runs.
8. Add the campaign tests T1–T8 in a new test module. Run them in the priority order in section 6.
9. Stop. Do not register tools, do not edit production, and do not run the file-skill experiment.

Estimated size: one opt-in change in the existing write path, one small new module, one new test module. The risky part is step 3–5, because it touches the write path. The opt-in pin is what keeps the current tests meaningful.

## 9. Complexity and major risks

Complexity is small if the patch stays opt-in. It becomes a second writer if someone copies `write_file.py` instead of extending the existing path. Do not copy it.

| Risk | Why it matters |
|---|---|
| A wrapper that still calls `write_file(path, ...)` | Re-opens by name and drops the pin. |
| Comparing a file inode to the directory pin | Every write fails, or a bad patch deletes the wrong check. |
| Unlink when the directory inode does not match | Cleanup can hit an unrelated directory. |
| Treating a green 56-test run as race proof | Those tests never rename the directory and never use a second process. |
| Registering the laboratory function | Restores caller-chosen roots, including unprotected directories. |
| Choosing a scratch directory inside either project tree | Startup must refuse it. A file Echo can write must not be a file the host later imports. |
| Spending the remaining time on Seatbelt or App Sandbox | `sandbox(7)` already says a held writable descriptor is not revoked. That work does not buy the guarantee T2 is for. |

## 10. GO / NO-GO

**GO**, for a later lab-only implementation of sections 2–3 and 8, followed by the existing 56 tests and then T1, T8, and T2.

**NO-GO**, for Echo tool registration, production integration, the file-skill experiment, shell access, arbitrary filesystem access, and any claim about intelligence or self-improvement.

The GO expires if the existing 56 tests fail, or if T1, T8, or T2 fails. A T2 run that never observes a rename between the check and `link` does not satisfy T2.

## Smallest next action

The smallest next engineering action is the opt-in directory pin and `ScratchWriter`, in the Voyager lab, without changing today's laboratory signatures, and then T1, T8, and T2.

Evidence that justifies a further step: the 56 tests still pass; T1 shows the bound functions create nothing when given a root or an escape path; T8 shows the pinned open fails on production, Voyager, memory, and FAISS with those inodes unchanged; T2 shows the replacement directory stays empty and a write that observes a moved directory returns `ok` false with no success audit on that directory.

That evidence would justify keeping the lab implementation. It would still not justify registering an Echo tool. Tool registration needs a separate decision after the full campaign, including T3, T5, and T7.

If T2 shows a published file in the replacement directory, or `ok` true for a file that is not at the pinned path, stop. Further userspace checks would not be the fix, and this capability should not be given to Echo.
