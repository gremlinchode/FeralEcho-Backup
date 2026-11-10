# ScratchWriter evidence

Preserved lab evidence for the rootless pinned writer. This directory is a byte copy of records that already existed. It is not a new test run.

Git commit at preservation: `dc8d6eb9b6479ef323614cd6820bb050a14299eb`

| File | SHA-256 | Bytes |
|---|---|---|
| `voyager_lab/scratch_write/pinned_writer.py` | `285b05521916770ab798d07df29f0c44c51d8f256c81c9b870dc31ff3d0e830a` | 32327 |
| `voyager_lab/scratch_write/IMPLEMENTATION_AND_VERIFICATION_REPORT.md` | `61329569f9d049ca2c3e6fd3ef57868986e7b71a1a717f8feec9a01a4259495d` | 22129 |

The file index is `MANIFEST.json`. Each copied JSON was hashed again after copy and matched the `/tmp` original. The originals were not edited.

## What was available

| Record | Class | Verdict in the file |
|---|---|---|
| `scratch_writer_t1.json` | Passing run | `PASS` |
| `scratch_writer_t8.json` | Passing run | `PASS` |
| `scratch_writer_t2.json` | Passing run | `PASS` |
| `scratch_writer_t8_scoring_bug.json` | Failed first attempt | `FAIL` |
| `scratch_writer_t2_scorer_mismatch.json` | Failed first attempt | `FAIL` |
| `.../swpin_t2_01_s_rrf72g` | Supporting directory | Located, not copied |

No requested JSON was missing. No replacement record was written.

The T2 directory is the path stored in `preserved_directory` inside `scratch_writer_t2_scorer_mismatch.json`. At preservation it still had two empty children, `pin` (inode 36347523) and `moved` (inode 36347521). Those inodes match the first-run record of the moved pin and the replacement directory. The directory was left where it is. Copying it would have created new inodes and would not have been the original artifact.

## What the passing records establish

T1 (`checks` all true). A pin was opened on a lab directory. Supplying a caller root raised `TypeError`. A relative path with `..` and an absolute path were rejected, audited, and did not create the target names. A legal one-component write inside the pin verified. The canary inode recorded in that JSON stayed unchanged for that run. The passing test removed its own base directory. This JSON is the remaining T1 evidence.

T8 (`checks` all true). Ten protected opens were refused. `protected_open_attempts` is empty. `os.open` was not called on those paths. Probe name `pinned_probe_8f3c1d0e.txt` was absent. The protected paths were still present. Inodes in the sample window were stable. Identity in that file is `lstat` only. File bodies were not hashed.

T2 (one trial, `scored.pass` true). Payload length 1048576, SHA-256 `bf63d8a95fcc2e64619813aae35fdcbe871fdd9264caa3f365eb3aed0f679129`. The writer returned `ok: false`, `status: "rejected"`, `reason: "identity_mismatch"`, `audit_recorded: false`. The replacement listing was empty. The moved directory's inode was the pin inode.

## What the failed first attempts establish

They are scorer failures kept on purpose. They are not a second opinion that the writer published a protected or renamed file.

T8 first attempt: `probe_names_absent` is false. The other security checks in that file are true, including `every_open_refused`, `inodes_stable`, `no_pin_returned`, and `os_open_not_called_on_protected`. The verification report (line 133) records why: the scorer treated "this path exists" as "the synthetic probe is present," so `faiss.index`, `memory_meta.json`, and `summary.json` failed a check aimed at `pinned_probe_8f3c1d0e.txt`.

T2 first attempt: `scored.pass` is false and `cleanup_matches_listing` is false. The other scored checks in that file are true, including `ok_false`, `replacement_empty`, `renamed_during_call`, and `no_success_audit`. The verification report (line 176) records why: the scorer required `status == "identity_mismatch"`, while the writer returns `status: "rejected"` and `reason: "identity_mismatch"`.

## What this package does not establish

- The Darwin check-to-syscall race on write, link, and audit is still open. The T2 JSON says that seeing the temporary name shows overlap with the temporary file's lifetime, including the write. It does not show that the rename fell between a passing check and `os.link`.
- `publish_cleanup_failed` and `temp_cleanup_failed` were not observed.
- Cross-process audit interleaving was not tested.
- The official T2 run's 0.004s unittest timing is a process result from the verification report. It is not, by itself, proof that the 1 MiB body was fully written. The payload hash in the JSON is the prepared payload hash.
- The laboratory `write_file(root, ...)` API was not called in T1. That API still accepts a caller root. The existing prototype tests cover it. Those tests were not rerun for this package.
- Nested-path temporary cleanup was outside the authorized single-component set.
- T8 does not prove production FAISS or `memory_meta.json` stayed unchanged after the sample window. The T8 file itself says a live server may change size or mtime, and that such a change with no `os.open` of that path is not attributed to this writer.
- Nothing here registers a tool, loads the writer into Echo, or authorizes production use.

## Preservation check (read-only)

Checked while writing this package. No ScratchWriter test was rerun.

- `pinned_writer.py` and the verification report match the hashes above.
- Prototype hashes still match the pre-campaign values: `confine.py` `f7520a948f5f11ce42958aa11d81b76a18e2bc52eb0d94eb637e42d4ece4b0f2`, `write_file.py` `897454a5169fa7922c270eb2f117c0c354847fb27ca8337688708251893184b9`, `verify_file.py` `638e589ba3bcec9aa738a4d50dd781bf504660df7a5408ea509614d4e094069d`, `tests/test_scratch_write.py` `880eb11218cc174a227159f0e384968f64d2e9bc35200f436ae81b99f1eab1db` (56 `def test_` methods), `SECURITY_REPORT.md` `48a674d902a773c10fdc711d7c717f1a7dc54c09e5852e58a85bd156c7d38ac0`, `FINAL_SECURITY_DESIGN.md` `2940b3072f1a01101565ec64884a6f44c92136fadf1025f05a3988b34be63bbb`.
- The rootless writer is `pinned_writer.py`, with its own `tests/test_pinned_writer.py` (3 `def test_` methods, hash `30c0385356c8e32f9735a14685e5c75a6a5e1f77260f14a4969bf37dc8ec74eb`). `scratch_write/` has no package `__init__.py`. The empty `tests/__init__.py` is unchanged (`e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`).
- Production `TOOL_SCHEMAS` in `app/core/echo_tool_dispatch.py` names `read_file`, `search_memory`, and `log_thought` only. The only `scratch_write` substring under production `app/` is the test name `test_anomaly_26_out_of_scratch_write_blocked` in `app/experiments/e5_mini/tests/test_e5_mini_g0.py`. That is not a registration of this writer.
- Frozen Voyager identities still match: `voyager_lab/voyager/engine.py` inode 36256079, size 19977, mode 0644, mtime_ns 1794177805925011044; `voyager_lab/voyager/worker.py` inode 36260012, size 1398, mode 0644, mtime_ns 1794178781409311138; `voyager_lab/results/summary.json` inode 36269403, size 57749, mode 0600, mtime_ns 1794179724623157658.
- `git diff --stat` was empty. `git status --porcelain` was `?? voyager_lab/`. Nothing was committed.
