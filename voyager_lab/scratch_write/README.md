# Scratch-only file writer

Standalone laboratory tool. It creates a new regular file inside a caller-supplied scratch directory and can read that file back. It is not registered with Echo, it has no default root, and it has no command-line entry point.

Location: `/Users/richietate/Desktop/FeralEcho-voyager/voyager_lab/scratch_write/`

Modules:

- `confine.py` — path boundary, audit append, read-back.
- `write_file.py` — `write_file(root, relative_path, content)`.
- `verify_file.py` — `verify_file(root, relative_path, expected_content)`.
- `tests/test_scratch_write.py` — filesystem assertions. Run record: `SECURITY_REPORT.md`.

```bash
cd /Users/richietate/Desktop/FeralEcho-voyager/voyager_lab/scratch_write
python3 -m unittest tests.test_scratch_write -v
```

The tests choose their own temporary roots (`tempfile.TemporaryDirectory`, prefix `scratch_write_test_`) and remove them. This package does not keep a durable scratch directory.

## Interface

```python
write_file(root, relative_path, content) -> dict
verify_file(root, relative_path, expected_content) -> dict
```

Extra keyword arguments raise `TypeError`. There is no `mode` argument and no flag argument.

### Arguments

| Name | Accepted value |
|---|---|
| `root` | Absolute path of an existing real directory. The caller creates it. A symlink root is rejected. |
| `relative_path` | A `str` using `/` separators. Components are used as written. |
| `content` / `expected_content` | A plain `str`. Stored and compared as UTF-8. Subclasses of `str`, `bytes`, and other types are rejected. |

Empty text is a valid empty file. The maximum is 1,048,576 characters and 1,048,576 UTF-8 bytes. A longer character string is rejected before encoding. A string that encodes past the byte cap is rejected after encoding.

`relative_path` limits: 1024 characters, 32 components, each component at most 255 UTF-8 bytes. Rejected shapes include an absolute path, `\`, NUL, ASCII controls, an empty component (`foo//bar` or a trailing slash), `.`, `..`, the audit name `.scratch_write_audit.jsonl`, and any component starting with `.swtmp_`. Percent-encoded dots stay literal characters. Missing parent directories are rejected. The tool does not create them.

### Return value

Both functions return a dict and do not raise for a rejected write. `ok` is true only when all of these hold:

- `status` is `"verified"`
- `verification` is `"match"`
- `accepted` is true
- `audit_recorded` is true

A return without an exception is not success. The bytes read back from the destination are what `verification` describes.

| Key | Meaning |
|---|---|
| `ok` | The call met the rule above. |
| `accepted` | True only when `ok` is true. |
| `audit_recorded` | An audit line was appended inside the scratch root. |
| `operation` | `"write"` or `"verify"`. |
| `path` | The requested relative path, or `None` when it is not a short `str`. |
| `reason` | `"verified"` on success. Otherwise a stable rejection or failure name. |
| `sha256` | SHA-256 of the bytes read back, when a read happened. |
| `size` | Byte length read back, when a read happened. |
| `status` | `verified`, `rejected`, `write_failed`, `verification_failed`, `audit_failed`, or `temp_cleanup_failed`. |
| `verification` | `match`, `mismatch`, `missing`, `unreadable`, or `not_run`. |

`verify_file` does not create or modify the destination. It uses the same walk and the same audit file. `repair_mode` is off on that path, so an existing executable mode is reported as `mode_unexpected` and left unchanged.

### Reason names

Root: `root_type`, `root_nul`, `root_not_absolute`, `root_missing`, `root_symlink`, `root_not_directory`, `root_open_failed`, `root_unresolved`, `root_protected`, `root_mismatch`, `platform_unsupported`.

Path: `path_type`, `path_empty`, `path_nul`, `path_absolute`, `path_backslash`, `path_empty_component`, `path_dot_segment`, `path_control_char`, `path_too_long`, `path_component_too_long`, `path_unencodable`, `path_reserved`, `path_reserved_temp`.

Content: `content_type`, `content_unencodable`, `content_too_large`.

Destination: `missing_parent`, `symlink_or_not_directory`, `parent_unresolved`, `escape`, `symlink_destination`, `destination_directory`, `destination_not_regular`, `destination_exists`.

Outcome: `link_failed`, `write_failed`, `readback_failed`, `verification_mismatch`, `missing`, `audit_failed`, `temp_cleanup_failed`, `mode_unexpected`.

A root that fails before a directory descriptor exists returns `audit_recorded: false`. No audit file is created for that rejection.

## What a successful write does

1. `lstat` the root. Refuse a symlink or a non-directory.
2. Resolve it and refuse it when `is_protected_path` is true, before `open`.
3. Open it with `O_RDONLY | O_DIRECTORY | O_NOFOLLOW | O_CLOEXEC`.
4. Compare `F_GETPATH` on that descriptor with `realpath`. Refuse a mismatch or a protected path.
5. Walk each existing parent with `openat` and `O_NOFOLLOW`. `ENOTDIR` and `ELOOP` are both refusals. Each opened directory is checked with `F_GETPATH`.
6. `lstat` the final name without following links. An existing symlink, directory, socket, fifo, device, or regular file is a refusal. Identical content is still a refusal.
7. Create `.swtmp_<random>` in that parent with `O_CREAT | O_EXCL | O_NOFOLLOW`, mode `0644`, then `fchmod` `0644`.
8. `F_GETPATH` the temp descriptor, write every byte, `fsync`, check the path again, and `link` the temp name onto the final name with `follow_symlinks=False`.
9. `link` fails with `EEXIST` when the name already exists, including a case-folded or Unicode-normalized collision on this volume. The existing bytes stay.
10. Unlink the temp name. Read the destination back with `O_NOFOLLOW`, compare bytes and SHA-256, and append one audit line.

`os.rename` and `os.replace` are not used. A rename would replace an existing destination. The link leaves the existing name untouched.

Content is data. A text file whose bytes look like a program is written as bytes. The file mode is `0644`, so the execute bits are clear. A shebang does not change that.

## Audit log

Path inside the scratch root: `.scratch_write_audit.jsonl`

One JSON object per line, ASCII, sorted keys. Fields: `timestamp` (UTC, microseconds, `Z`), `operation`, `path`, `accepted`, `reason`, `size`, `sha256`, `verification`. File content is not a field.

The log is opened only from the root descriptor after `lstat`. A symlink, directory, socket, fifo, device, executable, or extra hard link is not opened. A refused audit still makes `ok` false. When the destination was already linked and the bytes match, the file stays for inspection and `status` is `audit_failed`.

## Protected roots on this machine

`is_protected_path` uses `realpath` and `commonpath`. A string prefix is not the check. On this host, `FeralEcho-voyager` starts with the characters `FeralEcho`, and a prefix test would treat the laboratory as inside production. `commonpath` does not.

Refused trees:

- `/Users/richietate/Desktop/FeralEcho`
- `/Users/richietate/Desktop/FeralEcho-voyager`

Refused exact directories: `/`, `/tmp`, `/private/tmp`, `/var`, `/private/var`, `/private`, `/Users`, `/Users/richietate`, `/Users/richietate/Desktop`.

A private subdirectory of the system temp area can be a scratch root. A subdirectory of `Desktop` that is outside both trees above is not on this denylist. The caller is responsible for choosing that root. The test suite does not use one.

## Security guarantees that the 2026-11-08 suite exercised

These are host results, recorded in `SECURITY_REPORT.md`. They are not a claim about every operating system.

- New files, including a permitted subdirectory, Unicode text, multiline text, an empty file, and a file of exactly 1,048,576 bytes, matched the requested bytes and hash on an independent `O_NOFOLLOW` read.
- Created files were regular files, mode `0644`, including under umask `0o077`.
- `..`, `.`, absolute paths, controls, overlong paths, reserved names, and missing parents were rejected, and the canary bytes stayed put.
- An existing file was not overwritten, including identical content, an APFS case-fold (`Hello.txt` / `hello.txt`), and an NFC/NFD pair (`café` / `cafe` + combining acute).
- A symlink destination, a symlink parent, a directory, a socket, a fifo, and a symlink to `/dev/null` were rejected. `/dev/null` as a root was rejected. Its device identity stayed the same across the call.
- A hard link from outside the scratch into a scratch name was treated as an existing file. Both copies kept the canary bytes.
- An audit symlink and an audit hard link were not written through. The outside canary stayed unchanged.
- Interrupted writes and a failed temp open left no destination and no `.swtmp_*` name. A read-only parent left an empty directory.
- A lied read-back reported `verification_failed` while the real file still held the requested bytes.
- A cleanup failure reported `temp_cleanup_failed` with `ok` false, left the correct destination, and left exactly one temp name on the same inode.
- Two threads writing the same new path produced exactly one success. The file was one of the two bodies, mode `0644`.
- Production directories, production source files, `memory/faiss.index`, the frozen Voyager modules, and `voyager_lab/results` were offered as roots and rejected. The suite compared hashes or tree manifests around the run. See the report for the independent check after the process exited.

## Known limitations

- This is a Python API. A process that can already write anywhere can ignore it. The denylist is this machine's two trees plus a short list of broad directories.
- `F_GETPATH` is Darwin-specific. This interpreter accepts a 1024-byte buffer and rejects 4096. A failed `F_GETPATH` fails closed.
- Another process can rename the scratch directory after the last `F_GETPATH` check and before the write. The bytes would then land on the moved inode. That race was not given a flaky test.
- A crash after the temp file is created and before it is unlinked can leave a `.swtmp_*` orphan inside the scratch directory. That orphan is not a replacement of an existing destination.
- In-process calls share one lock. A second process is stopped from overwriting by `link` returning `EEXIST`. Two processes were not launched in the suite.
- The audit log grows for as long as the scratch root is used. A crash during the single-line append can leave a partial last line.
- Parent-directory `fsync` failures are ignored after a link that has already succeeded.
- The tool does not create device nodes. Coverage of devices is the `/dev/null` symlink and the rejection of `/dev/null` as a root.
- Case-folding and Unicode normalization were measured on this APFS volume. They are not a portable rule.
- A subdirectory of `Desktop` outside the two protected trees is not automatically refused.

## What a future integration would require

This package does not provide that integration.

A later isolated caller would import `write_file` and `verify_file` from this directory, pass a scratch root the caller created, and treat `ok` as the only success bit. `verify_file` would stay a separate call so an evaluator can read the destination without trusting the writer.

That caller would have to live outside `/Users/richietate/Desktop/FeralEcho`. Production tool discovery walks the application tree. Putting this package there, or adding it to the live tool list, would be a different and currently unauthorized change. The local file-skill experiment is also not authorized by the existence of this writer.
