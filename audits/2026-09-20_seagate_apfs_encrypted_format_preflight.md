# Seagate → GPT + APFS (Encrypted) Format Preflight — FeralEcho Vault (READ-ONLY; NOTHING FORMATTED)

**Date:** 2026-09-20 (UTC 23:19–23:35) · **Author:** CLAUDE-M5 · **Status:** PREFLIGHT ONLY — **STATUS: AWAITING FORMAT AUTHORIZATION**
**The Seagate was not formatted, erased, partitioned, encrypted, mounted, unmounted, ejected or written by me. No vault or directory was created. No FeralEcho file, Git state, production state or the frozen protocol was modified. The authorization phrase has NOT been consumed.**
**Evidence labels:** **OBSERVED** (read-only command output this session) · **INFERRED** · **UNKNOWN** · **TESTED-STUB** (tooling exercised only against synthetic input or stubbed commands — never against a real destructive verb).

---

## 0. Records

| Item | Before (23:19:45Z) | After (23:32:39Z) | Same? |
|---|---|---|---|
| Git HEAD | `2fba42644c82b9f7096276f4dd338d615cf1bcce` | `2fba42644c82b9f7096276f4dd338d615cf1bcce` | **yes** |
| `git status --porcelain` | 191 paths | 191 paths (`diff` of the listings is empty; this report file will make it 192) | **yes** |
| Server | PID **29288**, start **Sun Sep 20 07:30:10 2026** | PID 29288, start Sun Sep 20 07:30:10 2026 | **yes** |
| Frozen protocol v1.0 / v1.1 / traceability | `d1968caf…` / `e39e6238…` / `493600f4…` | identical | **yes** |
| Mutable production state | not read, not hashed (only file *mtimes* were sampled, §14) | — | — |
| Seagate whole disk | `/dev/disk4`, 2,000,398,933,504 B, MBR | same | **yes** |
| Seagate volume | `disk4s1`, exFAT, UUID `55403B63-9267-3C55-9EA8-622D0D4E412F`, used 46,661,632 B / free 2,000,288,350,208 B | same (`df` used 45,568 KiB, identical) | **yes** |
| Seagate root | 12 manufacturer/macOS-metadata names (§4) | same names; full `ls -laO` (incl. mtimes) identical to the previous preflight | **yes** |
| USB link | **480 Mb/s**, 500 mA, `bcdUSB 0x0210` | **480 Mb/s**, 500 mA | **yes (still USB 2)** |
| Internal `disk0` partition-table hash (for the future post-format "internal untouched" check) | `62d627935939a6b8` | `62d627935939a6b8` | yes |

**Confirmations.** Every command executed was read-only (list in §16). **No Seagate formatting occurred. No Seagate file was intentionally created** (macOS' own `.fseventsd/`/`.Spotlight-V100/`, timestamped 16:02 at mount, pre-date this mission). **No FeralEcho production state changed. Git was not mutated** (read-only commands with `GIT_OPTIONAL_LOCKS=0`). `PASSPHRASE PROVIDED INTERACTIVELY: NO` — no passphrase has been provided, requested, seen or recorded in this mission.

---

## 1. The Seagate, re-identified from scratch (OBSERVED)
Discovery started from `diskutil list` of **all** disks and from the USB registry, not from the old `/dev/disk4`. Result: **the same physical drive is again enumerated as `disk4`. That is attach-order coincidence, not identity** — the guard below derives the target from the USB identity every time and never accepts a typed disk number.

| Property | Value | Agrees with previous preflight? |
|---|---|---|
| Current device identifier | **`/dev/disk4`** (whole), **`/dev/disk4s1`** (partition 1) | same number (not relied on) |
| External / internal | `Internal: NO` · `Device Location: External` · `OSInternalMedia: false` | yes |
| Removable | `RemovableMedia: No` (media "Fixed") · `Ejectable: Yes` · `RemovableMediaOrExternalDevice: Yes` | yes |
| Physical | `VirtualOrPhysical: Physical` (not a disk image) | — |
| Bus | `BusProtocol: USB` | yes |
| Manufacturer / model | Seagate · `BUP Slim` (diskutil media name; System Information: "Seagate BUP Slim Media") | yes |
| USB vendor / product | `0x0bc2` (3010) / `0xac30` (44080) · bcdDevice `0x1708` | yes |
| Serial suffix | **`…3GNB`** (full serial deliberately not recorded here) | yes |
| Exact whole-disk size | **2,000,398,933,504 bytes** (512-byte blocks) | yes |
| Partition map | `FDisk_partition_scheme` (**MBR**), one partition at offset 1 MiB | yes |
| Filesystem | **exFAT** (FSKit), volume name `Backup Plus`, **volume UUID `55403B63-9267-3C55-9EA8-622D0D4E412F`** | yes |
| Mounted path | `/Volumes/Backup Plus`, read-write, `noowners`, `noatime` | yes |
| **Negotiated USB speed** | **480 Mb/s** (`Device Speed = 2`) · `bcdUSB = 0x0210` · power allocated **2.5 W (500 mA)** · port controller `AppleT8142USBXHCI` · Location ID `0x00100000` | **unchanged** |
| SMART | `Not Supported` (over this USB bridge) | yes |
| USB ↔ disk linkage | exactly **one** USB device node named "BUP Slim" (`ioreg -p IOUSB`); its subtree contains whole media **`disk4`** (`Size = 2000398933504`, `Whole = Yes`) and **`disk4s1`** — i.e. the block device is tied to the USB vendor/product/serial by the registry tree, independent of the disk number | — |

**Result: identity is unambiguous** (one match on VID:PID + serial suffix + exact size + media name + volume UUID + USB-tree ownership).

---

## 2. Internal-disk exclusion gate (evidence, OBSERVED)
| Object | Evidence that it is *not* the Seagate |
|---|---|
| Internal physical disk | `/dev/disk0` — `Internal: YES`, bus **Apple Fabric**, "APPLE SSD AP1024Z", 1,000,555,581,440 B, GUID map; contents: `disk0s1` Apple_APFS_ISC (container `disk1`), `disk0s2` Apple_APFS (container **`disk3`**), `disk0s3` Apple_APFS_Recovery (container `disk2`) |
| APFS container of the internal disk | container `disk3` has **exactly one physical store, `disk0s2`** (`diskutil apfs list`); **no APFS container of this Mac has a physical store on `disk4`** |
| Booted system volume | `/` = `disk3s1s1` (Macintosh HD, Internal); `ParentWholeDisk = disk3` |
| Data volume | `/System/Volumes/Data` = `disk3s5`; `ParentWholeDisk = disk3` |
| Recovery / Preboot / VM | `disk3s3` / `disk3s2` / `disk3s6` — all inside container `disk3` |
| The Seagate | whole disk `disk4`: `Internal: NO`, bus **USB**, MBR, exFAT, 2.0 TB — none of the above properties |
The destructive procedure carries these as **hard, independently re-derived gates** (§9): `Internal` must be false, `OSInternalMedia` false, bus USB, physical, USB-tree ownership, not in the internal whole-disk set, no APFS physical store on the target, not the parent of `/` or Data, plus exact size/media/UUID. The disk number is never trusted.

---

## 3. USB link recheck
Current negotiated link: **480 Mb/s (USB 2.0 High Speed), 500 mA — unchanged.**
> **USB LINK STILL AT USB 2 SPEED.** Recommendation to the operator: physically reseat the drive, connect it directly, and/or change the appropriate cable or adapter, then re-check that macOS reports **5 Gb/s or better** before continuing. Do not format merely because the link is slow, and do not treat the slow link as a reason to format now.

What the evidence supports, and nothing more: on this port the drive enumerated as a **High-Speed device** (`Device Speed 2`, `bcdUSB 0x0210`, 500 mA allowance). The evidence **does not** distinguish between the cable, an adapter, a hub, the port, the enclosure bridge or the drive; **I do not know which is responsible.** (The Location ID `0x00100000` has one populated tier, which is *consistent with* no intermediate hub — INFERRED, not established. Several child nodes in the registry carry an unexplained `USBSpeed = 3` property; it was not interpreted.) The guard treats this as **`HOLD`**: it refuses to proceed while the link is below SuperSpeed.

---

## 4. Existing contents — one final check (OBSERVED)
Top level of `/Volumes/Backup Plus`: `._.`, `.fseventsd/`, `.Spotlight-V100/`, `.VolumeIcon.icns`, `.VolumeIcon.ico`, `Autorun.inf`, `Seagate/`, `Start_Here_Chromebook.pdf`, `Start_Here_Mac.app/`, `Start_Here_Win.exe`, `System Volume Information/`, `Warranty.pdf` — **exactly the previously observed manufacturer/helper material plus the macOS-created metadata** (`.fseventsd`, `.Spotlight-V100`). Nothing new appeared (a `comm` against the previous 12 names is empty). Used space unchanged: 46,661,632 B. **No user data. Safe to destroy.** (`.Spotlight-V100` returned "Operation not permitted" to a listing — a protected OS metadata directory, not user data.) The guard re-checks this immediately before formatting and refuses if any name outside the allow-list appears.

---

## 5. Target format design
| | |
|---|---|
| Partition scheme | **GUID Partition Map** |
| Filesystem | **APFS (Encrypted)** — the plain `APFS` personality = *case-insensitive*, the same as the M5's internal volumes; (`diskutil listFilesystems` confirms `APFS` and `Case-sensitive APFS` as valid personalities). Case is a **permanent** property; the source tree has 0 case collisions, so either would work — plain APFS avoids tool surprises |
| Vault volume name | **`FERALECHO_VAULT`** (filesystem-safe; the temporary empty volume made by the first step is `FERALECHO_INIT`) |
| Encryption | volume-level, **encrypted from birth** (see §6/§8) |

**Exactly what the format operation will destroy:**
* the existing **exFAT filesystem** — destroyed;
* **all existing Seagate helper files** (`Start_Here_*`, `Seagate/`, PDFs, `Autorun.inf`, icons, `System Volume Information`, Spotlight/fseventsd metadata) — destroyed;
* the existing **volume UUID `55403B63-…` will cease to identify the reformatted filesystem** (the new APFS volume gets a new UUID; the vault identity file must record it);
* the **partition structure changes** (MBR → GUID; one exFAT partition → an APFS container, plus whatever EFI partition macOS adds);
* **recovery of the old contents should not be assumed afterwards.**
The old contents are disposable (§4), so nothing of value is lost.

---

## 6. Passphrase handling — mechanism
* **Rejected:** `-passphrase <text>` (the secret appears in the process argument list and possibly shell history); `-stdinpassphrase` (avoids argv but requires piping the secret from a variable/file/pipe into the shell — it would pass through something scripted); `-passphraseHint` (a hint is displayed while the volume is locked — never use one); typing the passphrase in Claude Code chat or any file/script/env/manifest/relay.
* **Chosen:** **`-passprompt`** — `diskutil` itself prompts on the terminal; the secret never enters an argument, variable, file or history. The man page defines it as the interactive option and states that a volume created with any passphrase option is *"encrypted from the beginning of its existence (as opposed to having encryption applied later)"* and that `eraseVolume` with a passphrase option yields an encrypted volume "initially accessible by the Disk User". (Whether the prompt asks for the passphrase twice is **UNKNOWN/UNTESTED** — hence the mandatory post-format lock/unlock test in §12.)
* **Where it runs:** in **Terminal.app by the operator**, in a fresh `/bin/bash --noprofile --norc`, with `HISTFILE` unset and history off. **The runner refuses to start without a TTY** (TESTED: run from this non-interactive tool it prints "ABORT: not an interactive terminal" and returns 1) — so no automated tool, including Claude Code's shell, can execute it or intercept the prompt.
* **What the audit records:** `PASSPHRASE PROVIDED INTERACTIVELY: NO` (no passphrase has been entered yet). After the future run it may record `YES` — never the value.
* Fallback (weaker on identity, best on secret UI): Disk Utility's native "Erase → APFS (Encrypted), Scheme: GUID Partition Map" with *View → Show All Devices* and the whole external disk selected — provided the read-only guard is run before and the post-format checks after; the passphrase is typed into macOS' secure dialog.

---

## 7. Passphrase recovery warning — required attestation
Before any destructive step the runner requires the operator to type, exactly, **`PASSPHRASE STORED IN TWO INDEPENDENT LOCATIONS`**, meaning: the passphrase is stored in **at least two independent secure locations**; **neither is solely on the M5**; **neither is solely on the Seagate**; and **it is not stored inside FeralEcho**. (Claude does not ask where, and records nothing.) Documentation for the `diskutil apfs` verbs shows only passphrase users and an *institutional* recovery key — **no personal recovery key is created for an external APFS volume by this method (INFERRED)**: a lost passphrase means the vault is unrecoverable. When macOS later offers to *remember* the password in the Keychain, leave that unchecked during the verification test in §12, otherwise a Keychain-cached copy can mask a mistyped or mis-stored passphrase.

---

## 8. The format procedure (DESIGN — nothing executed)
`MBR + exFAT` → `GPT + APFS Encrypted` in **two destructive verbs**, each preceded by the guard, with the passphrase prompted interactively. Syntax checked against the local `diskutil` man page: `eraseDisk [-noEFI] format name [scheme] device` and `apfs eraseVolume volumeDevice -name newName [-passprompt]`.

| Step | Command (exactly as printed by the runner) | Effect |
|---|---|---|
| F0 | operator preconditions: link reseated to ≥ 5 Gb/s; FeralEcho untouched; Terminal.app; attestation typed | — |
| G1 | `fv_verify_target pre` (18 identity + pre-format-state gates, USB link gate) then `fv_confirm`: exact phrase + typed device node | read-only |
| **F1** | `diskutil eraseDisk APFS FERALECHO_INIT GPT /dev/<TARGET_DISK>` | destroys the MBR/exFAT; writes GPT; creates one APFS container with one **empty, unencrypted** volume `FERALECHO_INIT` |
| G2 | `fv_verify_target mid` — the target is **re-derived from the USB identity** (not from the old number), gates re-run with "GPT" expected; then `fv_find_volume <disk> FERALECHO_INIT false` must find exactly one container / one store / one volume; then typed re-confirmation of `/dev/<volume>` | read-only |
| **F2** | `diskutil apfs eraseVolume <volume> -name FERALECHO_VAULT -passprompt` | replaces the **empty** init volume with an **encrypted-from-birth** volume; `diskutil` prompts for the passphrase on the terminal |
| P | `fv_post_collect` + `fv_post_decide` (§12) | read-only |
Why not `addVolume … -passprompt` + `deleteVolume`? It would create a second volume and then require a delete — one more destructive verb on the same disk for no benefit. Why not `eraseDisk` alone? It cannot set a passphrase. Why not encrypt afterwards (`encryptVolume`)? Encryption "applied later" is inferior to encrypted-from-birth (the man page's own wording) and gives the empty volume a window unencrypted — harmless here (no secrets yet) but unnecessary.
Notes: `eraseDisk` may create a small EFI partition on an external GUID disk (accepted by the post-check: at most one); it may prompt for macOS admin authorization; **UNTESTED on this hardware** — no destructive verb was ever run against any real device in this mission. A **rehearsal on a throw-away disk image** (`hdiutil`) would exercise the exact verbs safely, but creating and erasing a virtual disk is itself an erase/format action, so it was **not done** and needs its own authorization.

The two files that implement this are in Appendices A and B (SHA-256 in Appendix C). **`fv_guard.sh` contains no destructive verb; `fv_runner.sh` is the only file that does (exactly two).**

---

## 9. Destructive-command adversarial review
Every attack below was tried against the guard/runner with synthetic or stubbed input (**TESTED-STUB**); the runner tests ran inside a sandbox that kills any real `diskutil` execution (and a control proved the sandbox kills a real `diskutil list`).

| Attack | Guard | Result |
|---|---|---|
| Wrong disk number / disk **renumbering after reconnect** | target derived from USB VID:PID + serial suffix via the ioreg tree; a consistent `disk7` scenario **passes**, a USB device owning a *different* disk **fails** | ✔ 2/2 |
| **Partial identity match** (size off by one byte; wrong serial; wrong UUID; wrong media name; second identical drive) | every property is a separate gate; **exactly one** USB match required | ✔ refused (5/5) |
| Accidentally **targeting the internal APFS container / internal disk** | `Internal` false, `OSInternalMedia` false, bus USB, physical, not in the internal whole-disk set, no APFS physical store on target, not parent of `/` or Data, `fv_find_volume` refuses `disk0`'s container | ✔ refused (disk0, internal flag, bus, internal set, APFS store, boot parent, Data parent) |
| Targeting a **partition** instead of the whole disk | whole-disk name regex `^disk[0-9]+$` (no `s` suffix), `WholeDisk true` | ✔ `disk4s1` refused |
| **Quoting errors / wildcard expansion / empty or stale variable** | target must be a non-empty single token; `disk*`, `disk4 disk0`, empty all refused; the runner aborts on empty `TARGET_DISK` at both steps; all expansions are quoted; the target is **recomputed before each verb** (stale value impossible) | ✔ refused (empty, wildcard, two-word; empty mid-run) |
| **Copy/paste truncation** | files are SHA-256-pinned (Appendix C); the paste is verified before use; the exact phrase and the typed node must match exactly (a trailing space, lowercase, "yes", "continue", node without `/dev/` all refused) | ✔ 8/8 refused |
| **Shell-history / process-list secret leakage** | passphrase only via `-passprompt`; no secret variable exists; history off; fresh shell | by construction |
| **Unexpected mounted volume / user data appears** | pre-format gates: partition 1 must be exFAT **with the preflight UUID**; root names must be within the factory/macOS allow-list | ✔ refused |
| **Stale plan** (disk already reformatted) | pre-format gate expects MBR + that UUID; the mid-run gate expects GPT | ✔ refused |
| Operator runs it on the **wrong Mac** | gate on `hw.optional.arm64`, `hw.model = Mac17,3`, machine id `dd7643e652db2d2c` | ✔ refused |
| Running it through an automated tool / non-terminal | `fv_require_tty` | ✔ refused |
| A failure part-way | F2 is unreachable unless F1 succeeded **and** the re-derived identity and the init-volume locator pass; post-check failure ends with "Do not use the volume" | ✔ 13/13 failure scenarios call no verb they should not (F1: 0 verbs on any pre-F1 failure; F2 never after an F1-stage failure) |
Test totals: **20** guard attacks refused + baseline (link corrected) passes + renumbering passes; **9** typed-confirmation cases (1 accept, 8 refuse); **8** volume-locator cases (1 accept, 7 abort, incl. the internal container); **14** post-format decision cases (1 accept, 13 refuse); **14** runner sequencing scenarios.

---

## 10. No blind variable execution
Immediately before **each** destructive verb the runner prints, and requires the operator to confirm by typing:
```
TARGET DEVICE          : /dev/diskN
MODEL                  : BUP Slim (Seagate USB 3010:44080)
SERIAL SUFFIX          : 3GNB
EXACT BYTE SIZE        : 2000398933504
EXTERNAL/INTERNAL      : EXTERNAL (Internal: NO)
CURRENT FILESYSTEM     : exfat  (partition map: FDisk_partition_scheme)
CURRENT VOLUME NAME    : Backup Plus
CURRENT VOLUME UUID    : 55403B63-9267-3C55-9EA8-622D0D4E412F
```
An empty or unexpected `TARGET_DISK` aborts (TESTED-STUB). This display was produced against the real system in this mission and is byte-for-byte what the operator would see (the guard then refused only because of the USB-2 `HOLD`).

---

## 11. Human authorization phrase
Exactly, and only:

**`AUTHORIZE FORMAT OF VERIFIED SEAGATE FERALECHO VAULT`**

No equivalent wording; not "yes", not "continue", not any prior authorization. The runner compares the typed line **byte-for-byte**, then requires the device node to be typed back. **This mission did not consume it.** Vault creation, backup tooling, M5_G001, the source/state copy, the Git bundle and the Intel backup are **not** authorized by it.

---

## 12. Post-format verification (DESIGN; `fv_post_collect` / `fv_post_decide` — TESTED-STUB)
Mandatory immediately after F2, all read-only; **any FAIL ⇒ "POST-FORMAT CHECKS FAILED. Do not use the volume."**
1. **Same physical device:** external, USB, exact size 2,000,398,933,504, media name `BUP Slim`, USB VID:PID + serial suffix (re-derived, not the old number).
2. **GUID partition map** (`GUID_partition_scheme`).
3. **Partitions:** exactly one `Apple_APFS` plus **at most one** EFI; **no** leftover exFAT/NTFS or any other partition.
4. **One APFS container** on the target with **one volume**.
5. **Filesystem `apfs`, plain (case-insensitive) APFS.**
6. **`Encryption: true`** (the volume is encrypted).
7. **Volume name `FERALECHO_VAULT`.**
8. **Capacity** ≥ 1.99 TB and ≤ the whole disk.
9. **Mount path `/Volumes/FERALECHO_VAULT`**, **read-write**, volume reports `Internal: NO`.
10. **Internal SSD untouched:** `disk0` partition-table hash equals the value recorded before F1 (currently `62d627935939a6b8`); the root mount device is unchanged.
11. **Negotiated USB link** reported (must be ≥ 5 Gb/s if the link was corrected; otherwise the earlier HOLD stands).
12. **Manual (operator) passphrase proof:** eject, reconnect, and unlock with the passphrase **retrieved from a stored copy** (not from memory or a Keychain); leave "remember in Keychain" unchecked; repeat with the second stored copy if possible. Dismiss any Time Machine "use as backup disk" prompt. **Do not** create `FERALECHO_VAULT/` or any directory. Decide Spotlight indexing for the vault as a separate, authorized change.
**Then STOP again** (§13).

---

## 13. Vault creation is a separate gate
A successful format authorizes **nothing else**: not the `FERALECHO_VAULT/` directory tree, not installing backup tooling, not `M5_G001`, not copying source/state, not the Git bundle, not the Intel backup. After post-format verification the procedure **stops**; the next mission creates the vault layout (from the earlier preflight, §6 there) and runs Generation 001 under the previously designed verification protocol.

---

## 14. Local staging (A) versus direct-to-vault (B) for `M5_G001` — reassessed
Evidence gathered (all read-only): hash throughput 300 MB/s and local `cp` of 200 MB in 0.06 s (measured earlier this session); the mutable pair (`memory_meta.json` + `faiss.index`) is ≈ 302 MiB; observed write cadence by **mtime sampling only** (4 samples over 60 s): `river_brain.pkl` changed **once per ≈ 60 s**, the pair/garden had last been written ≈ 5 minutes earlier (all at the same second — written together); the M5 has **754 GB free**; the USB link is currently 480 Mb/s but **may be correctable**, so the link **does not decide** the architecture.

| Criterion | **A. Stage sealed generation on the M5 SSD, then copy the static generation** | **B. Copy/hash production directly into a new Seagate generation** |
|---|---|---|
| Consistency | the per-file *hash-before / copy / hash-after / hash-dest* proof runs at SSD speed; the source-mutation window per attempt ≈ 2 s (pre-hash 1 s + copy ≈ 0.1 s + post-hash 1 s for the pair) | the window includes the slow copy: ≈ 5 s at ~100 MB/s (USB 3, INFERRED) to ≈ 11 s at ~35 MB/s (USB 2, INFERRED) — **2.5×–5× wider at the same persist rate** |
| Production-state mutation risk | reads production once; never writes | reads production once **per attempt**, longer; never writes — **neither mutates production** |
| Internal-SSD dependency | uses ≈ 1.7 GB of the 754 GB free, outside the repo (`OWN_LOCAL`) | none |
| Free space | trivial | none on the SSD; failed attempts accumulate on the vault (`work/failed/` ≈ 0.3 GB per failed pair) |
| Live-file mutation handling | retries are cheap and local | every retry rewrites and re-reads the vault |
| Copy duration | +≈ 1 min local stage; the vault copy is a single sequential-friendly pass | one pass but with slow retries |
| Verification complexity | two byte-equality checks (stage→vault static; sealed manifest), *live* consistency isolated in the local layer | one combined proof; live and transport faults are entangled |
| Ability to retry safely | **the exact sealed bytes survive locally**: a failed/marginal vault write is retried by re-sending *identical* bytes | a failed vault write **cannot** be reproduced identically — the live state moved on |
| Crash behaviour | M5 crash/unplug mid-copy leaves the sealed local generation intact and a marked-abandoned partial on the vault | mid-copy failure leaves neither a complete local nor a complete vault generation; must re-read live state |
| Bonus | an extra sealed same-disk copy; a restore drill can run without the vault attached | none |
**Recommendation: A** for `M5_G001` — and it holds at USB 3 speed too (window 2× narrower; identical-bytes retry; sealed local copy). The cost is small and bounded (≈ 1.7 GB, ≈ 1 minute). **Not implemented.**

---

## 15. Drive-media claim discipline
**Media type: UNKNOWN.** macOS reports `Solid State: Info not available`, `Media Type: Generic`, SMART "Not Supported" over the bridge, and a generic USB-drive icon resource; none of that establishes HDD, SSD, SMR or CMR, and SMART being unavailable is **not** evidence of drive type. **Erratum (not an edit of the earlier file):** the previous preflight described this drive as "a 2.5-inch spinning drive … commonly shingled (SMR)" and drew reserve/speed rationale from that. Those statements were **inferences from the product name, not evidence**, and are **withdrawn**; the 25 % reserve recommendation stands on growth/fragmentation/safety grounds alone, and all throughput figures are just estimates for an unknown medium. Nothing in this report assumes a physical media type.

---

## 16. Commands used (every one read-only)
| # | Command | Writes? |
|---|---|---|
| 1 | `git rev-parse HEAD`, `git status --porcelain` (`GIT_OPTIONAL_LOCKS=0`); `ps -o pid=,lstart= -p 29288`; `date -u`; `shasum -a 256` of three frozen files | no |
| 2 | `man diskutil` (documentation), `diskutil listFilesystems` | no |
| 3 | `diskutil list`, `diskutil list -plist [diskN]`, `diskutil info [-plist] disk4 / disk4s1 / disk0 / /System/Volumes/Data / /`, `diskutil apfs list [-plist]` | no (list/info only) |
| 4 | `mount`, `df -k/-h`, `ls -laO`, `ls -A`, `stat -f %m`, `comm` on the Seagate root (names/sizes only; no file opened) | no |
| 5 | `system_profiler SPUSBHostDataType` (serial masked), `ioreg -p IOUSB`, `ioreg -r -c IOUSBHostDevice [-n "BUP Slim"] -l -w0`, `ioreg -r -c IOMedia`, `ioreg -rd1 -c IOPlatformExpertDevice`, `sysctl` | no |
| 6 | `plutil -extract/-convert … -o -` (parsing to stdout), `sed`, `awk`, `grep`, `sort`, `tr`, `cut`, `paste`, `cat` | no |
| 7 | test harnesses in the session scratchpad (`sandbox-exec` wrappers; bash test scripts; synthetic plist files written **only to the scratchpad**) | scratchpad only; **`/usr/sbin/diskutil list` was executed once under the sandbox and killed by it; no destructive verb ran anywhere** |
**Not run:** any `diskutil erase*`, `partitionDisk`, `apfs create*/add*/delete*/encrypt*/erase*`, `mount`/`unmount`/`eject`, `zeroDisk`/`secureErase`, `hdiutil`, `mdutil`, `touch/mkdir/cp/mv/rm/chmod/chflags`, `sudo`, `fsck*`, `diskutil verify*`.
**Explicit check that no command targeted internal storage for modification:** the only commands naming internal objects (`disk0`, `disk3*`, `/`, `/System/Volumes/Data`) were `diskutil info`, `diskutil list`, `diskutil apfs list`, `mount`, and `df`. Disclosure: `ioreg` printed the drive's full serial once in my working output (it is not written to this report or any file); only the suffix `…3GNB` is recorded.

---

## 17. Final answers (mirrored in the chat reply)
1. **Verified device:** Seagate "BUP Slim", USB `0bc2:ac30`, serial suffix `…3GNB`, 2,000,398,933,504 B, MBR, one exFAT volume `Backup Plus` (UUID `55403B63-9267-3C55-9EA8-622D0D4E412F`).
2. **Current identifier:** `/dev/disk4` (volume `disk4s1`) — *not identity*.
3. **Not the internal SSD:** `Internal: NO`, bus USB (internal is Apple Fabric), physical, owned by the USB device node in the registry tree; the internal disk is `disk0` with its APFS container `disk3` having one physical store `disk0s2` and **no** container store on `disk4`; `/`, Data, Recovery, Preboot, VM all live in `disk3`.
4. **USB speed:** **480 Mb/s — USB LINK STILL AT USB 2 SPEED** (500 mA); reseat/direct-connect/change the appropriate cable or adapter; cause undetermined.
5. **Root:** still only disposable factory helper files plus macOS metadata.
6. **Target format:** GUID Partition Map + APFS (Encrypted), case-insensitive, volume `FERALECHO_VAULT`.
7. **Secrets:** `diskutil … -passprompt` in Terminal.app by the operator; TTY-only; never argv, stdin pipe, file, env, history, chat or relay; `PASSPHRASE PROVIDED INTERACTIVELY: NO`.
8. **Procedure:** guard → `diskutil eraseDisk APFS FERALECHO_INIT GPT /dev/<TARGET_DISK>` → re-derive identity + locate the single empty init volume → `diskutil apfs eraseVolume <volume> -name FERALECHO_VAULT -passprompt` → post-format checks.
9. **Guards:** USB-identity-derived target (never a typed number), 18 identity/state gates + link gate, internal-disk exclusion, whole-disk regex, exact-size/UUID/factory-root checks, wrong-Mac check, TTY requirement, re-derivation before each verb, typed exact phrase + typed device node, typed passphrase-storage attestation, stubbed failure tests.
10. **A (stage locally) for `M5_G001`.**
11. **Post-format checks:** identity, GUID, one APFS partition (+≤1 EFI), one container/one volume, APFS, encryption, name, capacity, mount/rw, internal untouched, link speed, manual lock/unlock with the stored passphrase.
12. **Authorization phrase:** `AUTHORIZE FORMAT OF VERIFIED SEAGATE FERALECHO VAULT`

**STATUS: AWAITING FORMAT AUTHORIZATION**

---

## Appendix A — `fv_guard.sh` (read-only; contains no destructive verb)
```bash
# fv_guard.sh v1 -- READ-ONLY identity + safety guard for the future Seagate format. bash 3.2. SOURCE it; nothing here writes.
# It contains NO destructive verb. It only collects facts (diskutil info/list, ioreg, sysctl), decides PASS/FAIL, prints the
# identity table, and checks typed confirmations. Facts are gathered as KEY=VALUE lines so the decision logic can be tested on synthetic input.
FV_EXPECT_VID=3010; FV_EXPECT_PID=44080; FV_EXPECT_SERIAL_SUFFIX=3GNB; FV_EXPECT_SIZE=2000398933504; FV_EXPECT_MEDIANAME="BUP Slim"
FV_EXPECT_MACHINE_ID16=dd7643e652db2d2c; FV_EXPECT_MODEL=Mac17,3
FV_PHRASE="AUTHORIZE FORMAT OF VERIFIED SEAGATE FERALECHO VAULT"
FV_FACTORY_NAMES=" ._. .fseventsd .Spotlight-V100 .VolumeIcon.icns .VolumeIcon.ico Autorun.inf Seagate Start_Here_Chromebook.pdf Start_Here_Mac.app Start_Here_Win.exe System Volume Information Warranty.pdf .Trashes .DS_Store "
pl() { printf '%s' "$1" | plutil -extract "$2" raw -o - - 2>/dev/null; }                      # pl "<plist text>" keypath
dinfo() { diskutil info -plist "$1" 2>/dev/null; }
h16() { shasum -a 256 | cut -c1-16; }
# --- USB identity -> whole BSD disk (independent of disk numbering). Prints: VID PID SERIAL SPEED WHOLE  (one line per USB device that owns a whole disk)
fv_usb_map() { awk '
  function flush() { if (name != "" && whole != "") printf "%s %s %s %s %s\n", vid, pid, ser, spd, whole; }
  /^\+-o / { flush(); name=$0; vid=""; pid=""; ser=""; spd=""; whole=""; lastwhole=""; next }
  /"idVendor" = / && vid=="" { vid=$NF }
  /"idProduct" = / && pid=="" { pid=$NF }
  /"USB Serial Number" = / && ser=="" { s=$0; sub(/.*= "/,"",s); sub(/"$/,"",s); ser=s }
  /"Device Speed" = / && spd=="" { spd=$NF }
  /"Whole" = / { lastwhole=$NF }
  /"BSD Name" = "disk[0-9]+"$/ { if (lastwhole=="Yes" && whole=="") { s=$0; sub(/.*= "/,"",s); sub(/"$/,"",s); whole=s } }
  END { flush() }'; }
# --- collect facts for candidate whole disk $1 (the candidate itself comes from fv_usb_map, never from a typed number)
fv_collect() {
  local T="$1" p ph pv mach usbline
  p=$(dinfo "/dev/$T"); ph=$(diskutil list -plist 2>/dev/null)
  echo "TARGET=$T"
  echo "T_INTERNAL=$(pl "$p" Internal)"; echo "T_BUS=$(pl "$p" BusProtocol)"; echo "T_VIRT=$(pl "$p" VirtualOrPhysical)"; echo "T_WHOLE=$(pl "$p" WholeDisk)"
  echo "T_SIZE=$(pl "$p" Size)"; echo "T_MEDIANAME=$(pl "$p" MediaName)"; echo "T_NODE=$(pl "$p" DeviceNode)"; echo "T_CONTENT=$(pl "$p" Content)"; echo "T_OSINTERNAL=$(pl "$p" OSInternalMedia)"
  local usb; usb=$(ioreg -r -c IOUSBHostDevice -l -w0 2>/dev/null | fv_usb_map)
  echo "USB_MATCH_COUNT=$(printf '%s\n' "$usb" | awk -v v=$FV_EXPECT_VID -v pr=$FV_EXPECT_PID -v s=$FV_EXPECT_SERIAL_SUFFIX '$1==v && $2==pr && substr($3,length($3)-length(s)+1)==s' | wc -l | tr -d ' ')"
  echo "USB_WHOLE_FOR_TARGET=$(printf '%s\n' "$usb" | awk -v v=$FV_EXPECT_VID -v pr=$FV_EXPECT_PID -v s=$FV_EXPECT_SERIAL_SUFFIX -v t=$T '$1==v && $2==pr && substr($3,length($3)-length(s)+1)==s && $5==t{print $5}' | head -1)"
  echo "USB_SPEED_CODE=$(printf '%s\n' "$usb" | awk -v t=$T '$5==t{print $4}' | head -1)"
  # internal / boot exclusion sets
  local w i internal_set="" ap; for w in $(printf '%s' "$ph" | plutil -extract WholeDisks json -o - - 2>/dev/null | tr -d '[]"' | tr ',' ' '); do
    [ "$(pl "$(dinfo "/dev/$w")" Internal)" = true ] && internal_set="$internal_set $w"; done
  echo "INTERNAL_WHOLE_DISKS=$internal_set"
  ap=$(diskutil apfs list -plist 2>/dev/null); i=0; local stores=""
  while pv=$(pl "$ap" "Containers.$i.ContainerReference"); [ -n "$pv" ]; do
    local j=0 sd; while sd=$(pl "$ap" "Containers.$i.PhysicalStores.$j.DeviceIdentifier"); [ -n "$sd" ]; do stores="$stores $pv:${sd%%s[0-9]*}"; j=$((j+1)); done; i=$((i+1)); done
  echo "APFS_CONTAINER_STORE_WHOLE=$stores"
  echo "BOOT_PARENT=$(pl "$(dinfo /)" ParentWholeDisk)"; echo "DATA_PARENT=$(pl "$(dinfo /System/Volumes/Data)" ParentWholeDisk)"
  # pre-format state expected by the plan
  local parts; parts=$(diskutil list -plist "/dev/$T" 2>/dev/null)
  echo "T_PART_COUNT=$(printf '%s' "$parts" | plutil -extract AllDisksAndPartitions.0.Partitions raw -o - - 2>/dev/null)"
  local pd; pd=$(dinfo "/dev/${T}s1"); echo "T_P1_FSTYPE=$(pl "$pd" FilesystemType)"; echo "T_P1_UUID=$(pl "$pd" VolumeUUID)"; echo "T_P1_NAME=$(pl "$pd" VolumeName)"; echo "T_P1_MOUNT=$(pl "$pd" MountPoint)"
  local mp; mp=$(pl "$pd" MountPoint); local extra=""; if [ -n "$mp" ] && [ -d "$mp" ]; then local n; while IFS= read -r n; do case "$FV_FACTORY_NAMES" in *" $n "*) ;; *) extra="$extra[$n]" ;; esac; done < <(ls -A "$mp" 2>/dev/null); fi
  echo "T_ROOT_UNEXPECTED_NAMES=$extra"
  echo "MAC_ARM=$(sysctl -in hw.optional.arm64)"; echo "MAC_MODEL=$(sysctl -n hw.model)"
  mach=$(printf 'feralecho-machine-v1|%s|%s|%s' "$( [ "$(sysctl -in hw.optional.arm64)" = 1 ] && echo arm64 || echo x86_64)" "$(sysctl -n hw.model)" "$(ioreg -rd1 -c IOPlatformExpertDevice 2>/dev/null | awk -F'"' '/IOPlatformUUID/{print $4}')" | h16)
  echo "MAC_MACHINE_ID16=$mach"
}
# --- decide: reads KEY=VALUE facts on stdin; prints one line per gate; exit 0 only if EVERY gate passes
fv_decide() {   # $1 = pre (default) | mid (after the erase step: expects GPT instead of the old MBR/exFAT state)
  local mode="${1:-pre}" facts; facts=$(cat); local fail=0
  g() { local k; k=$(printf '%s\n' "$facts" | sed -n "s/^$1=//p" | head -1); printf '%s' "$k"; }
  ok() { printf 'PASS  %s\n' "$1"; }; no() { printf 'FAIL  %s\n' "$1"; fail=1; }
  local T; T=$(g TARGET)
  case "$T" in disk[0-9]|disk[0-9][0-9]) ok "target '$T' is a WHOLE-disk name (no slice suffix, no wildcard, non-empty)";; *) no "target '$T' is not a whole-disk name like disk4 (empty/partition/wildcard refused)";; esac
  [ "$(g T_NODE)" = "/dev/$T" ] && ok "device node /dev/$T matches" || no "device node mismatch ($(g T_NODE))"
  [ "$(g T_INTERNAL)" = false ] && ok "Internal: NO" || no "Internal is '$(g T_INTERNAL)' - refuses internal storage"
  [ "$(g T_OSINTERNAL)" = false ] && ok "OSInternalMedia: false" || no "OSInternalMedia is '$(g T_OSINTERNAL)'"
  [ "$(g T_BUS)" = USB ] && ok "bus protocol USB" || no "bus is '$(g T_BUS)', not USB"
  [ "$(g T_VIRT)" = Physical ] && ok "physical (not a disk image / virtual)" || no "VirtualOrPhysical is '$(g T_VIRT)'"
  [ "$(g T_WHOLE)" = true ] && ok "whole disk" || no "not a whole disk"
  [ "$(g T_SIZE)" = "$FV_EXPECT_SIZE" ] && ok "exact size $FV_EXPECT_SIZE bytes" || no "size '$(g T_SIZE)' != $FV_EXPECT_SIZE"
  [ "$(g T_MEDIANAME)" = "$FV_EXPECT_MEDIANAME" ] && ok "media name '$FV_EXPECT_MEDIANAME'" || no "media name '$(g T_MEDIANAME)'"
  [ "$(g USB_MATCH_COUNT)" = 1 ] && ok "exactly one USB device with $FV_EXPECT_VID:$FV_EXPECT_PID and serial suffix $FV_EXPECT_SERIAL_SUFFIX" || no "USB match count '$(g USB_MATCH_COUNT)' (need exactly 1)"
  [ "$(g USB_WHOLE_FOR_TARGET)" = "$T" ] && [ -n "$T" ] && ok "that USB device owns whole disk $T (ioreg tree, not the disk number)" || no "USB device does not own $T"
  case " $(g INTERNAL_WHOLE_DISKS) " in *" $T "*) no "target is in the internal whole-disk set [$(g INTERNAL_WHOLE_DISKS)]";; *) ok "not in internal whole-disk set [$(g INTERNAL_WHOLE_DISKS)]";; esac
  local st; for st in $(g APFS_CONTAINER_STORE_WHOLE); do [ "${st#*:}" = "$T" ] && { no "target holds an APFS physical store of container ${st%%:*}"; break; }; done; case "$(g APFS_CONTAINER_STORE_WHOLE)" in *":$T"*) ;; *) ok "no APFS container of this Mac has a physical store on $T";; esac
  [ "$(g BOOT_PARENT)" != "$T" ] && [ "$(g DATA_PARENT)" != "$T" ] && ok "not the booted system or Data volume's disk (boot=$(g BOOT_PARENT) data=$(g DATA_PARENT))" || no "target is the boot/Data volume disk"
  if [ "$mode" = pre ]; then
    [ "$(g T_CONTENT)" = FDisk_partition_scheme ] && ok "pre-format partition map is still MBR (plan not stale)" || no "partition map is '$(g T_CONTENT)', expected FDisk_partition_scheme (state changed since the preflight)"
    [ "$(g T_P1_FSTYPE)" = exfat ] && [ "$(g T_P1_UUID)" = "55403B63-9267-3C55-9EA8-622D0D4E412F" ] && ok "partition 1 is the exFAT volume with the preflight volume UUID" || no "partition 1 is '$(g T_P1_FSTYPE)' uuid '$(g T_P1_UUID)' (stale or different disk)"
    [ -z "$(g T_ROOT_UNEXPECTED_NAMES)" ] && ok "root holds only factory/macOS-metadata names" || no "UNEXPECTED root entries: $(g T_ROOT_UNEXPECTED_NAMES) - STOP, possible user data"
  else
    [ "$(g T_CONTENT)" = GUID_partition_scheme ] && ok "mid-format: partition map is now GUID" || no "mid-format: partition map is '$(g T_CONTENT)', expected GUID_partition_scheme"
  fi
  [ "$(g MAC_ARM)" = 1 ] && [ "$(g MAC_MODEL)" = "$FV_EXPECT_MODEL" ] && [ "$(g MAC_MACHINE_ID16)" = "$FV_EXPECT_MACHINE_ID16" ] && ok "running on the expected Mac ($FV_EXPECT_MODEL, machine id $FV_EXPECT_MACHINE_ID16)" || no "wrong Mac (model '$(g MAC_MODEL)', id '$(g MAC_MACHINE_ID16)')"
  local sp; sp=$(g USB_SPEED_CODE); case "$sp" in 3|4|5) ok "USB link is SuperSpeed or faster (speed code $sp)";; 2) printf 'HOLD  USB LINK STILL AT USB 2 SPEED (speed code 2) - reseat/direct-connect/change the appropriate cable or adapter before continuing\n'; fail=1;; *) no "USB speed code unknown '$sp'";; esac
  return $fail
}
# --- display + typed confirmation. $1 = facts text, $2 = file/fd to read answers from (default /dev/tty)
fv_display() { local f="$1" T; T=$(printf '%s\n' "$f" | sed -n 's/^TARGET=//p'); printf '%s\n' \
  "TARGET DEVICE          : /dev/$T" "MODEL                  : $(printf '%s\n' "$f" | sed -n 's/^T_MEDIANAME=//p') (Seagate USB $FV_EXPECT_VID:$FV_EXPECT_PID)" "SERIAL SUFFIX          : $FV_EXPECT_SERIAL_SUFFIX" \
  "EXACT BYTE SIZE        : $(printf '%s\n' "$f" | sed -n 's/^T_SIZE=//p')" "EXTERNAL/INTERNAL      : $( [ "$(printf '%s\n' "$f" | sed -n 's/^T_INTERNAL=//p')" = false ] && echo 'EXTERNAL (Internal: NO)' || echo 'INTERNAL !!!')" \
  "CURRENT FILESYSTEM     : $(printf '%s\n' "$f" | sed -n 's/^T_P1_FSTYPE=//p')  (partition map: $(printf '%s\n' "$f" | sed -n 's/^T_CONTENT=//p'))" "CURRENT VOLUME NAME    : $(printf '%s\n' "$f" | sed -n 's/^T_P1_NAME=//p')" "CURRENT VOLUME UUID    : $(printf '%s\n' "$f" | sed -n 's/^T_P1_UUID=//p')"; }
fv_confirm() {  # $1 = facts, $2 = answers source. Returns 0 only for the EXACT phrase AND the exact device node typed back.
  local facts="$1" src="${2:-/dev/tty}" a b T; T=$(printf '%s\n' "$facts" | sed -n 's/^TARGET=//p'); [ -n "$T" ] || { echo "ABORT: empty target"; return 1; }
  { IFS= read -r a; IFS= read -r b; } < "$src"
  [ "$a" = "$FV_PHRASE" ] || { echo "ABORT: authorization phrase not exact"; return 1; }
  [ "$b" = "/dev/$T" ] || { echo "ABORT: typed device node '$b' != /dev/$T"; return 1; }
  return 0
}
# --- the one entry point: derive the target from the USB identity, gate it, display it. Prints TARGET_DISK=<name> on success only.
fv_verify_target() {   # $1 = pre (default) | mid
  local mode="${1:-pre}" T facts; T=$(ioreg -r -c IOUSBHostDevice -l -w0 2>/dev/null | fv_usb_map | awk -v v=$FV_EXPECT_VID -v pr=$FV_EXPECT_PID -v s=$FV_EXPECT_SERIAL_SUFFIX '$1==v && $2==pr && substr($3,length($3)-length(s)+1)==s{print $5}' | head -2 | tr '\n' ' ' | sed 's/ $//')
  case "$T" in "") echo "ABORT: no Seagate matching the expected USB identity"; return 1;; *" "*) echo "ABORT: more than one match ($T)"; return 1;; esac
  facts=$(fv_collect "$T"); printf '%s\n' "$facts" | fv_decide "$mode"; local rc=$?; fv_display "$facts"
  [ $rc -eq 0 ] && { echo "TARGET_DISK=$T"; FV_FACTS="$facts"; FV_TARGET="$T"; return 0; } || { echo "GUARD REFUSES (rc=$rc)"; return 1; }
}

# ===== step-2 locator: after eraseDisk, find the ONE empty unencrypted init volume on the target's own APFS container (read-only) =====
# stdin = `diskutil apfs list -plist` XML. Prints the volume DeviceIdentifier, or an ABORT line and rc=1.
fv_find_volume() {   # $1 = whole disk, $2 = expected volume name, $3 = expected Encryption (true|false)
  local T="$1" WANT="$2" WENC="$3" ap i=0 found="" nfound=0 pv; ap=$(cat)
  while pv=$(pl "$ap" "Containers.$i.ContainerReference"); [ -n "$pv" ]; do
    local j=0 sd on=0; while sd=$(pl "$ap" "Containers.$i.PhysicalStores.$j.DeviceIdentifier"); [ -n "$sd" ]; do
      case "$sd" in "$T"s[0-9]*) on=1 ;; esac; j=$((j+1)); done
    if [ $on -eq 1 ]; then
      nfound=$((nfound+1)); local nv=0 vd vn ve; while vd=$(pl "$ap" "Containers.$i.Volumes.$nv.DeviceIdentifier"); [ -n "$vd" ]; do nv=$((nv+1)); done
      vd=$(pl "$ap" "Containers.$i.Volumes.0.DeviceIdentifier"); vn=$(pl "$ap" "Containers.$i.Volumes.0.Name"); ve=$(pl "$ap" "Containers.$i.Volumes.0.Encryption")
      [ "$j" = 1 ] && [ "$nv" = 1 ] && [ "$vn" = "$WANT" ] && [ "$ve" = "$WENC" ] && found="$vd" || { echo "ABORT: container $pv on $T has stores=$j volumes=$nv name='$vn' encrypted='$ve' (expected 1 store, 1 volume $WANT, encrypted=$WENC)"; return 1; }
    fi; i=$((i+1)); done
  [ "$nfound" = 1 ] && [ -n "$found" ] && { echo "$found"; return 0; }
  echo "ABORT: found $nfound APFS containers on $T (need exactly 1)"; return 1
}
# ===== post-format facts and decision (read-only). Pure decision reads KEY=VALUE facts on stdin so it can be tested on synthetic input =====
fv_post_collect() {  # $1 = whole disk (derived again from the USB identity by the caller), $2 = volume device id (from fv_init_volume, or re-derived)
  local T="$1" V="$2" p parts ap; p=$(dinfo "/dev/$T"); parts=$(diskutil list -plist "/dev/$T" 2>/dev/null); ap=$(diskutil apfs list -plist 2>/dev/null)
  echo "TARGET=$T"; echo "T_INTERNAL=$(pl "$p" Internal)"; echo "T_BUS=$(pl "$p" BusProtocol)"; echo "T_SIZE=$(pl "$p" Size)"; echo "T_CONTENT=$(pl "$p" Content)"; echo "T_MEDIANAME=$(pl "$p" MediaName)"
  local k=0 types="" sizes="" c; while c=$(pl "$parts" "AllDisksAndPartitions.0.Partitions.$k.Content"); [ -n "$c" ]; do types="$types $c"; sizes="$sizes $(pl "$parts" "AllDisksAndPartitions.0.Partitions.$k.Size")"; k=$((k+1)); done
  echo "T_PART_TYPES=$types"; echo "T_PART_SIZES=$sizes"
  local v; v=$(dinfo "/dev/$V"); echo "V_ID=$V"; echo "V_NAME=$(pl "$v" VolumeName)"; echo "V_FS=$(pl "$v" FilesystemType)"; echo "V_ENCRYPTION=$(pl "$v" Encryption)"; echo "V_LOCKED=$(pl "$v" Locked)"
  echo "V_WRITABLE=$(pl "$v" WritableVolume)"; echo "V_INTERNAL=$(pl "$v" Internal)"; echo "V_MOUNT=$(pl "$v" MountPoint)"; echo "V_PARENT=$(pl "$v" ParentWholeDisk)"; echo "V_CASE=$(diskutil info "/dev/$V" 2>/dev/null | sed -n 's/^ *File System Personality: *//p')"
  local i=0 pv nvol=0 cap="" ncont=0; while pv=$(pl "$ap" "Containers.$i.ContainerReference"); [ -n "$pv" ]; do
    local sd=$(pl "$ap" "Containers.$i.PhysicalStores.0.DeviceIdentifier"); case "$sd" in "$T"s[0-9]*) ncont=$((ncont+1)); cap=$(pl "$ap" "Containers.$i.CapacityCeiling"); local n=0; while [ -n "$(pl "$ap" "Containers.$i.Volumes.$n.DeviceIdentifier")" ]; do n=$((n+1)); done; nvol=$n;; esac; i=$((i+1)); done
  echo "C_COUNT_ON_TARGET=$ncont"; echo "C_VOLUME_COUNT=$nvol"; echo "C_CAPACITY=$cap"
  echo "INTERNAL_LAYOUT_HASH=$(diskutil list -plist disk0 2>/dev/null | plutil -extract AllDisksAndPartitions.0.Partitions xml1 -o - - 2>/dev/null | shasum -a 256 | cut -c1-16)"
  echo "ROOT_MOUNT_DEV=$(mount | awk '$3=="/"{print $1}')"
}
fv_post_decide() {  # stdin facts; args: $1 = expected INTERNAL_LAYOUT_HASH recorded before formatting
  local facts; facts=$(cat); local fail=0; g() { printf '%s\n' "$facts" | sed -n "s/^$1=//p" | head -1; }
  ok() { printf 'PASS  %s\n' "$1"; }; no() { printf 'FAIL  %s\n' "$1"; fail=1; }
  [ "$(g T_INTERNAL)" = false ] && [ "$(g T_BUS)" = USB ] && [ "$(g T_SIZE)" = "$FV_EXPECT_SIZE" ] && [ "$(g T_MEDIANAME)" = "$FV_EXPECT_MEDIANAME" ] && ok "still the same physical Seagate (external, USB, exact size, media name)" || no "device identity changed"
  [ "$(g T_CONTENT)" = GUID_partition_scheme ] && ok "GUID partition map" || no "partition map is '$(g T_CONTENT)'"
  local t apfs=0 efi=0 other=0; for t in $(g T_PART_TYPES); do case "$t" in Apple_APFS) apfs=$((apfs+1));; EFI) efi=$((efi+1));; *) other=$((other+1));; esac; done
  [ $apfs -eq 1 ] && [ $other -eq 0 ] && [ $efi -le 1 ] && ok "partitions: exactly one Apple_APFS (+ at most one EFI); nothing else [$(g T_PART_TYPES)]" || no "unexpected partition layout [$(g T_PART_TYPES)]"
  [ "$(g C_COUNT_ON_TARGET)" = 1 ] && [ "$(g C_VOLUME_COUNT)" = 1 ] && ok "one APFS container with one volume on the target" || no "containers=$(g C_COUNT_ON_TARGET) volumes=$(g C_VOLUME_COUNT)"
  [ "$(g V_FS)" = apfs ] && ok "filesystem APFS" || no "filesystem '$(g V_FS)'"
  case "$(g V_CASE)" in APFS) ok "case-insensitive APFS (matches the M5 internal volume)";; *) no "personality '$(g V_CASE)' (expected plain APFS)";; esac
  [ "$(g V_ENCRYPTION)" = true ] && ok "ENCRYPTION ENABLED" || no "encryption is '$(g V_ENCRYPTION)' - volume is NOT encrypted"
  [ "$(g V_NAME)" = FERALECHO_VAULT ] && ok "volume name FERALECHO_VAULT" || no "volume name '$(g V_NAME)'"
  [ "$(g V_INTERNAL)" = false ] && [ "$(g V_PARENT)" != "" ] && ok "volume reports Internal: NO" || no "volume Internal/parent problem"
  local cap; cap=$(g C_CAPACITY); [ -n "$cap" ] && [ "$cap" -ge 1990000000000 ] && [ "$cap" -le "$FV_EXPECT_SIZE" ] && ok "capacity $cap bytes (>= 1.99 TB, <= whole disk)" || no "capacity '$cap' out of range"
  [ "$(g V_MOUNT)" = "/Volumes/FERALECHO_VAULT" ] && ok "mounted at /Volumes/FERALECHO_VAULT" || no "mount point '$(g V_MOUNT)'"
  [ "$(g V_WRITABLE)" = true ] && ok "read-write" || no "not writable"
  [ "$(g INTERNAL_LAYOUT_HASH)" = "$1" ] && [ -n "$1" ] && ok "internal disk0 partition table unchanged" || no "internal layout hash '$(g INTERNAL_LAYOUT_HASH)' != recorded '$1'"
  return $fail
}

# ===== small typed gates used by the runner =====
fv_require_tty() { [ -t 0 ] && [ -t 1 ] || { echo "ABORT: not an interactive terminal (stdin/stdout must be a TTY). The passphrase prompt and every confirmation need a real terminal - run this in Terminal.app yourself, not through an automated tool."; return 1; }; }
fv_attest() { local a src="${1:-/dev/tty}"; echo "Type exactly:  PASSPHRASE STORED IN TWO INDEPENDENT LOCATIONS"; IFS= read -r a < "$src"; [ "$a" = "PASSPHRASE STORED IN TWO INDEPENDENT LOCATIONS" ] || { echo "ABORT: attestation not exact"; return 1; }; }
fv_confirm_node() { local want="$1" src="${2:-/dev/tty}" a; [ -n "$want" ] || { echo "ABORT: empty device to confirm"; return 1; }; printf 'Type the device node again to continue [%s]: ' "$want"; IFS= read -r a < "$src"; [ "$a" = "$want" ] || { echo "ABORT: typed '$a' != '$want'"; return 1; }; }
fv_internal_hash() { diskutil list -plist disk0 2>/dev/null | plutil -extract AllDisksAndPartitions.0.Partitions xml1 -o - - 2>/dev/null | shasum -a 256 | cut -c1-16; }
```

## Appendix B — `fv_runner.sh` (the only file with destructive verbs: exactly two)
```bash
# fv_runner.sh v1 -- the ONLY file containing destructive diskutil verbs. NEVER sourced or run by any test against real devices.
# To be run by the OPERATOR in Terminal.app (bash 3.2) AFTER the authorization phrase, from the verified guard file. Sourced AFTER fv_guard.sh.
# The passphrase is never seen by this script: diskutil prompts for it on the terminal (-passprompt). No secret is in any argument, variable or file.
fv_run_format() {
  set -u; unset HISTFILE; set +o history 2>/dev/null
  fv_require_tty || return 1
  fv_attest || return 1
  fv_verify_target pre || return 1
  local T="${FV_TARGET:-}"; [ -n "$T" ] || { echo "ABORT: empty TARGET_DISK"; return 1; }
  local IH; IH=$(fv_internal_hash); [ -n "$IH" ] || { echo "ABORT: cannot record internal partition-table hash"; return 1; }
  echo "Recorded internal disk0 partition-table hash: $IH"
  fv_confirm "$FV_FACTS" || return 1                                                 # exact authorization phrase + typed device node
  echo ">> STEP F1 (destroys the exFAT volume, its factory files and the MBR): diskutil eraseDisk APFS FERALECHO_INIT GPT /dev/$T"
  diskutil eraseDisk APFS FERALECHO_INIT GPT "/dev/$T" || { echo "STOP: eraseDisk failed - the disk may be partially changed; do NOT retry blindly"; return 1; }
  sleep 3
  fv_verify_target mid || { echo "STOP: identity re-check after F1 failed"; return 1; }   # re-derived from USB identity, NOT from the old number
  T="${FV_TARGET:-}"; [ -n "$T" ] || { echo "ABORT: empty TARGET_DISK after F1"; return 1; }
  local V; V=$(diskutil apfs list -plist | fv_find_volume "$T" FERALECHO_INIT false) || { echo "$V"; echo "STOP: cannot uniquely locate the empty init volume"; return 1; }
  fv_confirm_node "/dev/$V" || return 1
  echo ">> STEP F2 (replaces the EMPTY init volume with an encrypted one; diskutil will prompt for the passphrase): diskutil apfs eraseVolume $V -name FERALECHO_VAULT -passprompt"
  diskutil apfs eraseVolume "$V" -name FERALECHO_VAULT -passprompt || { echo "STOP: eraseVolume failed - the volume may exist unencrypted; do not store anything on it"; return 1; }
  sleep 2
  fv_verify_target mid >/dev/null || { echo "STOP: identity re-check after F2 failed"; return 1; }; T="${FV_TARGET:-}"
  V=$(diskutil apfs list -plist | fv_find_volume "$T" FERALECHO_VAULT true) || { echo "$V"; echo "STOP: the encrypted vault volume cannot be uniquely located"; return 1; }
  [ -n "$V" ] || { echo "STOP: cannot find the new volume"; return 1; }
  fv_post_collect "$T" "$V" | fv_post_decide "$IH"; local rc=$?
  [ $rc -eq 0 ] && echo "POST-FORMAT CHECKS PASSED. STOP. Vault creation is a separate authorization." || echo "POST-FORMAT CHECKS FAILED. STOP. Do not use the volume."
  return $rc
}
```

## Appendix C — hashes and lint
| File | SHA-256 |
|---|---|
| `fv_guard.sh` | `9b36cd220f2994135ca65f5d14714f967030c665cfdfdb0a2c926fdb27cedfa6` |
| `fv_runner.sh` | `edee2d3503f534e19ebb1732f6336b795c928381f8f3de50b0f10d520d2c51b7` |

**Machine lint of the two files** (executed when this report was generated; positive controls: a synthetic destructive command line and a synthetic `-passphrase` line are detected, and an `echo`ed mention is correctly *not* counted as a command):

| Check | Result |
|---|---|
| destructive `diskutil` command lines in `fv_guard.sh` | **0** (verb names appearing anywhere in its code, comments excluded: 0) |
| destructive `diskutil` command lines in `fv_runner.sh` | **2** — eraseDisk, eraseVolume |
| passphrase-carrying options (`-passphrase`, `-stdinpassphrase`, `-passphraseHint`, `-newPassphrase`, `-oldPassphrase`) in either file | **0** |
| `-passprompt` in the runner's code (1 executed command + 1 echoed description) | 2 |
| `sudo` / `rm` / `mv` / `dd` / `hdiutil` in either file's code | 0 |
| destructive command lines containing a wildcard, `$(...)`, or an unquoted device expansion | 0 |

