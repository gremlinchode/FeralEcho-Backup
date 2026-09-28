# Post-F1 Diagnostic — Why the Seagate Format Guard Stopped (READ-ONLY; STOPPED AFTER F1)

**Date:** 2026-09-21 (UTC 23:54–00:03) · **Author:** CLAUDE-M5 · **Status:** DIAGNOSTIC ONLY — **STATUS: STOPPED AFTER F1 — AWAITING REVIEW**
**No further destructive operation was performed. `eraseDisk` was not run again. F2 was not run. Nothing was encrypted, erased, repartitioned, renamed, added or deleted on the Seagate. FeralEcho and Git were not modified.**
**Labels:** **OBSERVED** (read-only command output this session) · **TESTED-REAL** (a read-only check run against the real current topology) · **TESTED-STUB** (synthetic input / stubbed commands only) · **INFERRED** · **UNKNOWN**.

---

## 0. Historical record (not altered)
* The operator ran the frozen runner (`fv_guard.sh` SHA-256 `71b22c049a55cf7f…`, `fv_runner.sh` `77d69d95377db26f…`) in Terminal.app. **F1 executed:** `diskutil eraseDisk APFS FERALECHO_INIT GPT /dev/disk4` — diskutil reported *Started erase … Finished erase on disk4*.
* The runner's **post-F1 identity re-check then failed** (`FAIL target holds an APFS physical store of container disk5`; display `CURRENT FILESYSTEM: msdos`, `CURRENT VOLUME NAME: EFI`) and stopped with `GUARD REFUSES (rc=1) / STOP: identity re-check after F1 failed`. **F2 was never reached.**
* The two executed files are **unchanged** (hashes re-verified just now: `71b22c049a55cf7f…`, `77d69d95377db26f…`). All new work is in a **separate directory** (`…/scratchpad/fmt/exec2/`, files `*_v3.sh`).

| Item | Before (23:54:59Z) | After (00:01:15Z) | Same? |
|---|---|---|---|
| Git HEAD | `2fba42644c82b9f7096276f4dd338d615cf1bcce` | same | **yes** |
| `git status --porcelain` | 192 paths | 192, listing identical | **yes** |
| Server | PID **29288**, start **Sun Sep 20 07:30:10 2026** | same | **yes** |
| Internal `disk0` partition-table hash | `62d627935939a6b8` (= recorded) | `62d627935939a6b8` | **yes** |
| Seagate topology | GPT: `disk4s1` EFI, `disk4s2` Apple_APFS → container `disk5` → volume `disk5s1` FERALECHO_INIT | identical | **yes** |
| `FERALECHO_INIT` "capacity consumed" | 974,848 B | 978,944 B (+4 KB) | **not byte-identical** — macOS' own Spotlight/fseventsd bookkeeping on the freshly mounted volume; I wrote nothing |
Confirmations: every command was read-only (list in §12); no Seagate write by me; no FeralEcho/Git/production mutation.

---

## 1. Seagate re-identified from USB identity (OBSERVED, TESTED-REAL)
The target was **not** taken from `/dev/disk4`. `ioreg` maps exactly one USB device — vendor **3010 (0x0bc2)**, product **44080 (0xac30)**, serial suffix **`…3GNB`**, speed code 2 — to whole media **`disk4`**. Independent properties of `disk4`: `Internal: NO`, `OSInternalMedia: false`, bus **USB**, `Physical`, media name **BUP Slim**, exact size **2,000,398,933,504 B**. **SEAGATE PHYSICAL IDENTITY: PASS.** (Coincidentally still numbered `disk4`; not relied upon — the guard re-derives it every time.)

## 2. Complete current topology (OBSERVED)
```
Seagate BUP Slim  (USB 0bc2:ac30, ...3GNB, 2,000,398,933,504 B, Internal: NO)      disk4    [GUID_partition_scheme]
 ├─ disk4s1  EFI            209,715,200 B   FAT32 ("msdos"), volume name "EFI", UUID 0E239BC6-…, NOT mounted    (the GPT EFI System Partition macOS adds)
 └─ disk4s2  Apple_APFS   2,000,189,177,856 B   = the APFS PHYSICAL STORE   (APFSContainerReference = disk5)
      └─ disk5   APFS Container (synthesized, "Virtual", MediaName inherited "BUP Slim", Internal: NO, bus USB)   UUID 8314D755-…
           ├─ physical stores: exactly ONE — disk4s2 (2FA7469D-…)            capacity ceiling 2,000,189,177,856 B, 100 % unallocated
           └─ disk5s1  APFS volume "FERALECHO_INIT" (Case-insensitive), UUID 7F7FE427-…, mounted /Volumes/FERALECHO_INIT (apfs, journaled, noowners)
                Encryption: false · FileVault: No · Locked: false · no cryptographic users · no snapshots/other volumes
```
The old exFAT/NTFS partition and the volume "Backup Plus" no longer exist (`/Volumes/Backup Plus` gone; no exFAT/NTFS partition listed).

## 3. Does container `disk5` belong exclusively to the Seagate? (OBSERVED — YES)
* `diskutil apfs list -plist` lists four containers and their stores: `disk1`→`disk0s1`, `disk2`→`disk0s3`, `disk3`→`disk0s2`, **`disk5`→`disk4s2`**. `disk5` has **one** physical store, `disk4s2`, whose parent whole disk is `disk4` (the USB-identified Seagate). It has no store on any internal disk, and **no other container has a store on `disk4`**.
* `disk5` reports `Internal: NO`, bus USB (inherited); only the *disk-image-style* `Virtual` flag differs from a raw disk, which is normal for a synthesized APFS container.

## 4. Proof that `disk5` is NOT the boot/system/Data container and has no internal store (OBSERVED)
`/` = `disk3s1s1` and `/System/Volumes/Data` = `disk3s5`, both `ParentWholeDisk = disk3`; container **`disk3`** has exactly one physical store, **`disk0s2`** (the internal SSD, `Internal: YES`, Apple Fabric, APPLE SSD AP1024Z) and holds Macintosh HD, Preboot, Recovery, Data and VM. `disk5` ≠ `disk3`, ≠ `disk1`/`disk2` (the ISC and Recovery containers, stores `disk0s1`/`disk0s3`); **`disk0`'s partition table is unchanged** (hash `62d627935939a6b8` = recorded).

## 5. The FERALECHO_INIT volume
Device identifier **`disk5s1`**, container `disk5`, the only volume in it; unencrypted; root contains only `.fseventsd` and `.Spotlight-V100` (macOS-created).

## 6. Did F1 complete successfully despite the guard failure? — **PASS**
Every F1 postcondition holds: GUID map ✔, EFI (≈210 MB) + exactly one Apple_APFS partition ✔, one APFS container on the Seagate ✔, one empty unencrypted volume named FERALECHO_INIT ✔ (case-insensitive APFS, the personality chosen) ✔, capacity ≈ 2.0 TB ✔, mounted read-write ✔, old exFAT gone ✔, internal SSD untouched ✔. The guard failure was a **false alarm about a correct result**, not a failed erase.

## 7. Any destructive operation after F1? — **No** (OBSERVED)
Only one container/one volume exist on the Seagate; the volume is still named `FERALECHO_INIT` and **unencrypted** (F2 would have renamed and encrypted it); no additional volumes, containers or partitions; no `FERALECHO_VAULT`; the volume root holds nothing but macOS metadata. The runner's own transcript ended at the guard refusal before any further verb.

## 8. Encryption — **NO** (`Encryption: false`, `FileVault: No`, "No cryptographic users for disk5s1").
## 9. FeralEcho data on the Seagate — **NO** (volume root: `.fseventsd`, `.Spotlight-V100` only; ≈ 0.98 MB consumed, which is APFS metadata; the EFI partition is unmounted and was created empty by `eraseDisk`, not inspected; no backup tooling was ever run against it and the production repository is unchanged).
## 10. Internal SSD unchanged — **PASS** (partition-table hash and the four internal containers' stores identical).

---

## 11. Diagnosis of the guard logic

### 11.1 Cause of the guard failure — **your hypothesis is CORRECT (verified independently)**
**Reproduction (read-only, against the real current state):** running the *unchanged* frozen guard's `fv_decide mid` on freshly collected facts gives exactly one failure — `FAIL target holds an APFS physical store of container disk5` — and every other gate passes; `APFS_CONTAINER_STORE_WHOLE = disk1:disk0 disk2:disk0 disk3:disk0 disk5:disk4`. The failing gate is the *pre-format* invariant applied unchanged after F1.
* **PRE-F1 invariant (valid):** *the target must not participate in any existing APFS container* — before the erase, a Seagate that already belonged to an APFS container would be a red flag.
* **POST-F1 invariant (what the guard lacked):** *the target must participate in **exactly one** APFS container, that container must have **exactly one** physical store, that store must be **the target's own Apple_APFS partition**, the container must be **external and not the boot/Data container**, and no other container may touch the target.* F1 **intentionally** creates such a container; its existence is an **expected postcondition**, and the check only makes sense with the phase flipped.
* The runner called the *same* `fv_verify_target mid` **twice** (after F1 **and after F2**), so the phase error would have blocked the run at both points; even after a successful F2 it would have reported a failure.

### 11.2 Cause of the EFI display — **your second hypothesis is CORRECT**
`fv_collect` filled `T_P1_FSTYPE/NAME/UUID` from the node **`/dev/${T}s1`** — a leftover of the pre-format layout (MBR slice 1 = the exFAT volume). After F1 the GPT layout is `disk4s1 = EFI`, `disk4s2 = Apple_APFS`, so `disk4s1` is the **EFI FAT32 partition** (`msdos`, name `EFI`, UUID `0E239BC6-…`, verified). `fv_display` printed those fields regardless of phase. It was a **display/inspection error only** (the EFI partition was *not* an erase or F2 target — F2's locator queries the APFS container's volume list, never `${T}s1`), but it is exactly the kind of "wrong object selected" error the guard must not be able to make.

### 11.3 Review of the *remaining* F2 procedure against the ACTUAL topology
| Piece of the original F2 | Verdict on the real topology |
|---|---|
| Locator `fv_find_volume disk4 FERALECHO_INIT false` | **correct** — returns `disk5s1` (TESTED-REAL) because it walks `Containers[].PhysicalStores` → `Volumes[]` from the APFS plist, so it can select neither the EFI partition nor the store partition `disk4s2` |
| Command `diskutil apfs eraseVolume disk5s1 -name FERALECHO_VAULT -passprompt` | **correct target and syntax** (man page: erases an *existing APFS volume*, keeps it in its container, yields an *encrypted-from-birth* volume with a passphrase option; inherits case-insensitive APFS) — it acts on the volume inside container `disk5`, never on the container, the store partition, the EFI, or the whole disk |
| Guard before F2 (`fv_verify_target mid`) | **wrong** — the phase error of §11.1 |
| Guard after F2 (`fv_verify_target mid >/dev/null`) | **wrong** — same error; would report failure after a *successful* F2 |
| Status display before F2 | **wrong** — the EFI selection of §11.2 |
| Independent check that F2's device really is the intended volume | **missing** — the locator was the only barrier; the revised design adds `fv_f2_decide` (§11.4) |
| Authorization | the exact phrase was consumed before F1; because the plan is being revised after review, the continuation **requires the phrase again** (plus the typed whole-disk node and the typed volume node) |
**ORIGINAL F2 SAFE AS WRITTEN — the F2 *command and target selection* are correct and safe for the actual topology; the *procedure around it* (guards, display) is not runnable as written.** I therefore did not merely relax the failing condition: I rebuilt the mid/post logic so the phase invariant is explicit, and added a dedicated F2-target check.

### 11.4 Revised, phase-aware guard (v3 — NOT executed against any destructive verb)
New files in `exec2/` (the executed originals untouched): `fv_guard_v3.sh` (`6aba813a…`) and `fv_runner_v3.sh` (`b3338425…`); the runner contains **exactly one** destructive verb (F2) and **no** `eraseDisk`.
1. **Phase-specific APFS gate.** `pre`: no container has a store on the target. `mid`/post-F1: exactly one container with a store on the target; that container has exactly **one** physical store and it lies **on the target**; the store is the target's own `Apple_APFS` partition; the container is external, and is neither the boot nor the Data container; the partition map is at most one EFI + exactly one `Apple_APFS`.
2. **Topology by content type, never by slice number:** partitions are read from `diskutil list -plist` with their `Content` (EFI / Apple_APFS); `mid` no longer uses `${T}s1` at all, and its display prints the partition map, the physical store and the container instead of a "filesystem/volume name".
3. **F2 target check (`fv_f2_decide`):** the device must be an APFS **volume** (slice suffix; `FilesystemType apfs`; not `EFI`, not `Apple_APFS`), named `FERALECHO_INIT`, **unencrypted**, `Internal: NO`, belong to *the* Seagate container, in a container with **exactly one** volume.
4. **Continuation runner `fv_run_continue_f2`:** TTY required → passphrase-storage attestation → internal-fingerprint check → `fv_verify_target mid` → locate the single INIT volume → `fv_f2_decide` → **exact authorization phrase re-typed + whole-disk node typed + volume node typed** → F2 → read-only `fv_post_run` (post-format gates, informational USB speed) → stop.

### 11.5 Adversarial / mutation tests of the revised guard (TESTED-REAL baseline + TESTED-STUB mutations)
| Group | Cases | Result |
|---|---|---|
| Mid gates on the **real** post-F1 topology | baseline | **PASS** (all gates; only the informational USB-2 `WARN`) |
| Mid gates, mutated facts (21 cases: baseline, consistent renumbering to `disk7`/`disk8`, and 19 attacks) | Seagate mixed stores; fusion (2 stores on the Seagate); **internal APFS container**; container = boot; container = Data; **container backed by internal storage**; internal `disk0` as target; wrong external disk; **stale disk number**; **EFI partition as target**; **APFS store partition as target**; two containers on the Seagate; no container (F1 not done); still MBR; extra partition; two `Apple_APFS`; store ≠ target's partition; wrong size; virtual device | baseline and renumbering **PASS**; **all 19 attacks refused** |
| **F2 target check** (11 cases: baseline + 10) | **EFI partition** as F2 device; **APFS store partition** as F2 device; container reference `disk5`; **internal Data volume**; **wrong container**; **missing INIT volume**; **multiple volumes**; already-encrypted target; unknown encryption; stale/empty device | baseline **PASS** on the real volume `disk5s1`; **all 10 attacks refused** |
| Volume locator (8 cases) | good; already encrypted; wrong name; two volumes; two containers; none on target; fusion; **zero volumes** | only "good" accepted; 7 aborts |
| Continuation runner sequencing under stubs (12 scenarios; real `diskutil` execution blocked by a kill-sandbox) | all-pass and 11 failure points | all-pass: one `eraseVolume` call, **zero** `eraseDisk`; **no** F2 call on any failure before the confirmations; F2 called only after the typed confirmations |
| v3 in `pre` mode on the *current* (post-F1) state | must refuse | refused (stale MBR/exFAT expectations) — the phases cannot be confused |
| Post-format decision on the *current* (pre-F2) state | must fail encryption/name/mount | **FAIL** on all three (it would not pass an unencrypted INIT volume) |
| Lint of v3 files (positive controls: earlier report's lint) | — | guard: **0** destructive command lines; runner: **1** (`eraseVolume`); no `-passphrase`/`-stdinpassphrase`/hint options; no `sudo/rm/mv/dd/hdiutil` |

---

## 12. Commands used (all read-only)
`git rev-parse`/`status --porcelain` (`GIT_OPTIONAL_LOCKS=0`); `ps`; `date`; `diskutil list`, `diskutil list -plist`, `diskutil info [-plist]` (disk4, disk4s1, disk4s2, disk5, disk5s1), `diskutil apfs list [-plist] [disk5]`, `diskutil apfs listCryptoUsers disk5s1` (a listing), `mount`; `ls -laO`, `ls -A`, `df -k` on the new volume; `ioreg -r -c IOUSBHostDevice -l -w0`; `system_profiler SPUSBHostDataType`; `plutil -extract/-convert` (parsing); the guard's own read-only collectors; `shasum`; test scripts and synthetic plists written **only to the session scratchpad**; `sandbox-exec` wrappers (a real `diskutil` execution under them is killed; none ran). **Not run:** any `diskutil erase*/partition*/apfs create|add|delete|erase|encrypt|resize*`, `mount/unmount/eject`, `hdiutil`, `mdutil`, `sudo`, or any write to the Seagate.

## 13. Recommended next human-operated step (NOT executed; needs your review and explicit action)
Continue with **F2 only**, using the revised files. In Terminal.app, in a fresh `/bin/bash --noprofile --norc`:
```bash
cd /private/tmp/claude-501/-Users-richietate-Desktop-FeralEcho/7fcb20e9-1ea2-4966-92aa-f5bb98c0da19/scratchpad/fmt/exec2
shasum -a 256 -c SHA256SUMS                 # both files must print OK
. ./fv_guard_v3.sh; . ./fv_runner_v3.sh
fv_run_continue_f2
```
It will (1) require the TTY, (2) ask you to type `PASSPHRASE STORED IN TWO INDEPENDENT LOCATIONS`, (3) re-check the internal fingerprint and the post-F1 topology, print the partition map / physical store / container, (4) ask you to type **`AUTHORIZE FORMAT OF VERIFIED SEAGATE FERALECHO VAULT`** again and then the whole-disk node it shows (`/dev/disk4`) and the volume node (`/dev/disk5s1`), (5) run `diskutil apfs eraseVolume disk5s1 -name FERALECHO_VAULT -passprompt` — **`diskutil` prompts for your passphrase; it never touches Claude**, (6) run the read-only post-format gates, and stop. Then the manual eject → unlock (with your independently stored passphrase, "remember in Keychain" **unchecked**) test, and tell me; I will re-run the read-only verification and report the requested PASS/FAIL block. **Untested items remain:** whether `-passprompt` asks for the passphrase twice, and how `eraseVolume` behaves on this hardware (it may request admin authorization).
**One observation for a later decision (not changed):** the volume mounts with `noowners` (ownership ignored — normal for an external volume). Modes are still stored, but ownership is not enforced; whether to enable ownership on the vault is a separate, explicitly authorized change.

**REVISED CONTINUATION AVAILABLE: YES.**

---

## Appendix A — `fv_guard_v3.sh` (read-only; no destructive verb)
```bash
# fv_guard_v3.sh -- PHASE-AWARE successor to the guard that stopped after F1 (kept unmodified beside it). READ-ONLY identity + safety guard for the future Seagate format. bash 3.2. SOURCE it; nothing here writes.
# It contains NO destructive verb. It only collects facts (diskutil info/list, ioreg, sysctl), decides PASS/FAIL, prints the
# identity table, and checks typed confirmations. Facts are gathered as KEY=VALUE lines so the decision logic can be tested on synthetic input.
FV_EXPECT_VID=3010; FV_EXPECT_PID=44080; FV_EXPECT_SERIAL_SUFFIX=3GNB; FV_EXPECT_SIZE=2000398933504; FV_EXPECT_MEDIANAME="BUP Slim"
FV_EXPECT_MACHINE_ID16=dd7643e652db2d2c; FV_EXPECT_INTERNAL_HASH=62d627935939a6b8; FV_EXPECT_MODEL=Mac17,3
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
  # --- v3: partition/container topology of the target, derived by CONTENT TYPE (never "partition s1")
  local k=0 pdev pcont; local plist_parts=$(diskutil list -plist "/dev/$T" 2>/dev/null); local ptypes="" efi="" apfsp="" pdevs=""
  while pdev=$(pl "$plist_parts" "AllDisksAndPartitions.0.Partitions.$k.DeviceIdentifier"); [ -n "$pdev" ]; do
    pcont=$(pl "$plist_parts" "AllDisksAndPartitions.0.Partitions.$k.Content"); ptypes="$ptypes $pcont"; pdevs="$pdevs $pdev:$pcont"
    case "$pcont" in EFI) efi="$pdev";; Apple_APFS) apfsp="$pdev";; esac; k=$((k+1)); done
  echo "T_PART_TYPES=$ptypes"; echo "T_PART_DEVS=$pdevs"; echo "T_EFI_DEV=$efi"; echo "T_APFS_PART_DEV=$apfsp"
  local ci=0 cref onT=0 refs="" cn_stores="" cn_allonT="" cn_nvol="" cn_stdevs=""
  while cref=$(pl "$ap" "Containers.$ci.ContainerReference"); [ -n "$cref" ]; do
    local sj=0 sdv n_on=0 n_all=0 devs=""; while sdv=$(pl "$ap" "Containers.$ci.PhysicalStores.$sj.DeviceIdentifier"); [ -n "$sdv" ]; do
      n_all=$((n_all+1)); [ "${sdv%%s[0-9]*}" = "$T" ] && n_on=$((n_on+1)); devs="$devs $sdv"; sj=$((sj+1)); done
    if [ $n_on -gt 0 ]; then onT=$((onT+1)); refs="$refs $cref"; cn_stores="$n_all"; cn_allonT=$([ $n_on -eq $n_all ] && echo 1 || echo 0); cn_stdevs="$devs"
      local vn=0; while [ -n "$(pl "$ap" "Containers.$ci.Volumes.$vn.DeviceIdentifier")" ]; do vn=$((vn+1)); done; cn_nvol=$vn; fi; ci=$((ci+1)); done
  echo "CONT_ON_T_COUNT=$onT"; echo "CONT_ON_T_REFS=$refs"; echo "CONT_ON_T_NSTORES=$cn_stores"; echo "CONT_ON_T_ALL_STORES_ON_T=$cn_allonT"; echo "CONT_ON_T_STORE_DEVS=$cn_stdevs"; echo "CONT_ON_T_NVOL=$cn_nvol"
  local cr; cr=$(printf '%s' "$refs" | tr -d ' '); echo "CONT_REF=$cr"; [ -n "$cr" ] && echo "CONT_REF_INTERNAL=$(pl "$(dinfo "/dev/$cr")" Internal)" || echo "CONT_REF_INTERNAL="
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
  if [ "$mode" = pre ]; then
    local st; for st in $(g APFS_CONTAINER_STORE_WHOLE); do [ "${st#*:}" = "$T" ] && { no "PRE-F1: target holds an APFS physical store of container ${st%%:*} (must have none before the erase)"; break; }; done
    case "$(g APFS_CONTAINER_STORE_WHOLE)" in *":$T"*) ;; *) ok "PRE-F1: no APFS container of this Mac has a physical store on $T";; esac
  else
    # POST-F1 invariant: the target must participate in EXACTLY the one container that F1 created, and only that container, on its own stores
    [ "$(g CONT_ON_T_COUNT)" = 1 ] && ok "POST-F1: exactly one APFS container has a physical store on $T (container $(g CONT_ON_T_REFS))" || no "POST-F1: $(g CONT_ON_T_COUNT) APFS containers have a store on $T (need exactly 1)"
    [ "$(g CONT_ON_T_NSTORES)" = 1 ] && [ "$(g CONT_ON_T_ALL_STORES_ON_T)" = 1 ] && ok "POST-F1: that container has exactly one physical store, and it lies on $T ($(g CONT_ON_T_STORE_DEVS))" || no "POST-F1: container stores=$(g CONT_ON_T_NSTORES) all-on-target=$(g CONT_ON_T_ALL_STORES_ON_T) (mixed or foreign stores refused)"
    local cr; cr=$(g CONT_REF); [ -n "$cr" ] && [ "$(g CONT_REF_INTERNAL)" = false ] && [ "$cr" != "$(g BOOT_PARENT)" ] && [ "$cr" != "$(g DATA_PARENT)" ] && ok "POST-F1: container $cr is external (Internal: NO) and is neither the boot nor the Data container" || no "POST-F1: container '$cr' is internal/boot/Data or unknown (internal='$(g CONT_REF_INTERNAL)')"
    local t apfs=0 efi=0 other=0; for t in $(g T_PART_TYPES); do case "$t" in Apple_APFS) apfs=$((apfs+1));; EFI) efi=$((efi+1));; *) other=$((other+1));; esac; done
    [ $apfs -eq 1 ] && [ $other -eq 0 ] && [ $efi -le 1 ] && ok "POST-F1: partition map is [$(g T_PART_DEVS)] - at most one EFI plus exactly one Apple_APFS" || no "POST-F1: unexpected partition layout [$(g T_PART_DEVS)]"
    case " $(g CONT_ON_T_STORE_DEVS) " in *" $(g T_APFS_PART_DEV) "*) [ -n "$(g T_APFS_PART_DEV)" ] && ok "POST-F1: the container's physical store is T's own Apple_APFS partition $(g T_APFS_PART_DEV)";; *) no "POST-F1: container store [$(g CONT_ON_T_STORE_DEVS)] is not T's Apple_APFS partition [$(g T_APFS_PART_DEV)]";; esac
  fi
  [ "$(g BOOT_PARENT)" != "$T" ] && [ "$(g DATA_PARENT)" != "$T" ] && ok "not the booted system or Data volume's disk (boot=$(g BOOT_PARENT) data=$(g DATA_PARENT))" || no "target is the boot/Data volume disk"
  if [ "$mode" = pre ]; then
    [ "$(g T_CONTENT)" = FDisk_partition_scheme ] && ok "pre-format partition map is still MBR (plan not stale)" || no "partition map is '$(g T_CONTENT)', expected FDisk_partition_scheme (state changed since the preflight)"
    [ "$(g T_P1_FSTYPE)" = exfat ] && [ "$(g T_P1_UUID)" = "55403B63-9267-3C55-9EA8-622D0D4E412F" ] && ok "partition 1 is the exFAT volume with the preflight volume UUID" || no "partition 1 is '$(g T_P1_FSTYPE)' uuid '$(g T_P1_UUID)' (stale or different disk)"
    [ -z "$(g T_ROOT_UNEXPECTED_NAMES)" ] && ok "root holds only factory/macOS-metadata names" || no "UNEXPECTED root entries: $(g T_ROOT_UNEXPECTED_NAMES) - STOP, possible user data"
  else
    [ "$(g T_CONTENT)" = GUID_partition_scheme ] && ok "mid-format: partition map is now GUID" || no "mid-format: partition map is '$(g T_CONTENT)', expected GUID_partition_scheme"
  fi
  [ "$(g MAC_ARM)" = 1 ] && [ "$(g MAC_MODEL)" = "$FV_EXPECT_MODEL" ] && [ "$(g MAC_MACHINE_ID16)" = "$FV_EXPECT_MACHINE_ID16" ] && ok "running on the expected Mac ($FV_EXPECT_MODEL, machine id $FV_EXPECT_MACHINE_ID16)" || no "wrong Mac (model '$(g MAC_MODEL)', id '$(g MAC_MACHINE_ID16)')"
  # PROTOCOL AMENDMENT (operator, 2026-09-20): a verified 480 Mb/s (USB 2) link is a WARNING, not a HOLD. ONLY this gate is relaxed; unknown or slower-than-480 speeds still fail.
  local sp; sp=$(g USB_SPEED_CODE); case "$sp" in 3|4|5) ok "USB link is SuperSpeed or faster (speed code $sp)";; 2) printf 'WARN  USB LINK AT USB 2 SPEED (480 Mb/s, speed code 2) - informational only; transfer speed is not a consistency requirement (M5_G001 is staged locally first)\n';; *) no "USB speed code unknown or below 480 Mb/s: '$sp'";; esac
  return $fail
}
# --- display + typed confirmation. $1 = facts text, $2 = file/fd to read answers from (default /dev/tty)
fv_display() { local f="$1" mode="${2:-pre}" T; T=$(printf '%s\n' "$f" | sed -n 's/^TARGET=//p'); local q; q() { printf '%s\n' "$f" | sed -n "s/^$1=//p" | head -1; }
  printf '%s\n' "TARGET DEVICE          : /dev/$T" "MODEL                  : $(q T_MEDIANAME) (Seagate USB $FV_EXPECT_VID:$FV_EXPECT_PID)" "SERIAL SUFFIX          : $FV_EXPECT_SERIAL_SUFFIX" "EXACT BYTE SIZE        : $(q T_SIZE)" \
   "EXTERNAL/INTERNAL      : $( [ "$(q T_INTERNAL)" = false ] && echo 'EXTERNAL (Internal: NO)' || echo 'INTERNAL !!!')"
  if [ "$mode" = pre ]; then printf '%s\n' "CURRENT FILESYSTEM     : $(q T_P1_FSTYPE)  (partition map: $(q T_CONTENT))" "CURRENT VOLUME NAME    : $(q T_P1_NAME)" "CURRENT VOLUME UUID    : $(q T_P1_UUID)"
  else printf '%s\n' "PARTITION MAP          : $(q T_CONTENT)  partitions:$(q T_PART_DEVS)" "APFS PHYSICAL STORE    : $(q CONT_ON_T_STORE_DEVS)" "APFS CONTAINER         : $(q CONT_ON_T_REFS)  (volumes: $(q CONT_ON_T_NVOL))"; fi; }
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
  facts=$(fv_collect "$T"); printf '%s\n' "$facts" | fv_decide "$mode"; local rc=$?; fv_display "$facts" "$mode"
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
  echo "USB_SPEED_CODE=$(ioreg -r -c IOUSBHostDevice -l -w0 2>/dev/null | fv_usb_map | awk -v t=$T '$5==t{print $4}' | head -1)"
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
  case "$(g USB_SPEED_CODE)" in 3|4|5) printf 'INFO  negotiated USB link: SuperSpeed or faster (code %s)\n' "$(g USB_SPEED_CODE)";; 2) printf 'WARN  negotiated USB link: 480 Mb/s (USB 2) - informational only\n';; *) printf 'INFO  negotiated USB link: unknown (code %s)\n' "$(g USB_SPEED_CODE)";; esac
  return $fail
}

# ===== small typed gates used by the runner =====
fv_require_tty() { [ -t 0 ] && [ -t 1 ] || { echo "ABORT: not an interactive terminal (stdin/stdout must be a TTY). The passphrase prompt and every confirmation need a real terminal - run this in Terminal.app yourself, not through an automated tool."; return 1; }; }
fv_attest() { local a src="${1:-/dev/tty}"; echo "Type exactly:  PASSPHRASE STORED IN TWO INDEPENDENT LOCATIONS"; IFS= read -r a < "$src"; [ "$a" = "PASSPHRASE STORED IN TWO INDEPENDENT LOCATIONS" ] || { echo "ABORT: attestation not exact"; return 1; }; }
fv_confirm_node() { local want="$1" src="${2:-/dev/tty}" a; [ -n "$want" ] || { echo "ABORT: empty device to confirm"; return 1; }; printf 'Type the device node again to continue [%s]: ' "$want"; IFS= read -r a < "$src"; [ "$a" = "$want" ] || { echo "ABORT: typed '$a' != '$want'"; return 1; }; }
fv_internal_hash() { diskutil list -plist disk0 2>/dev/null | plutil -extract AllDisksAndPartitions.0.Partitions xml1 -o - - 2>/dev/null | shasum -a 256 | cut -c1-16; }

# ===== read-only post-format verification, callable any time after the operator's format (derives everything from the USB identity) =====
fv_post_run() {
  fv_verify_target mid >/dev/null || { fv_verify_target mid; echo "POST: identity gates failed"; return 1; }
  local T="$FV_TARGET" V; V=$(diskutil apfs list -plist | fv_find_volume "$T" FERALECHO_VAULT true) || { echo "$V"; echo "POST: cannot uniquely locate the encrypted FERALECHO_VAULT volume"; return 1; }
  fv_post_collect "$T" "$V" | fv_post_decide "$FV_EXPECT_INTERNAL_HASH"
}

# ===== v3: the F2 target check. F2 must act on the ONE empty, unencrypted FERALECHO_INIT APFS *volume* inside the ONE container that lives on the verified Seagate =====
fv_f2_collect() {  # $1 = candidate volume device id (from fv_find_volume), stdout = KEY=VALUE
  local V="$1" v; v=$(dinfo "/dev/$V")
  echo "F2_DEV=$V"; echo "F2_FSTYPE=$(pl "$v" FilesystemType)"; echo "F2_NAME=$(pl "$v" VolumeName)"; echo "F2_ENC=$(pl "$v" Encryption)"; echo "F2_LOCKED=$(pl "$v" Locked)"
  echo "F2_CONTAINER=$(pl "$v" APFSContainerReference)"; echo "F2_INTERNAL=$(pl "$v" Internal)"; echo "F2_CONTENT=$(pl "$v" Content)"; echo "F2_MOUNT=$(pl "$v" MountPoint)"
}
fv_f2_decide() {  # stdin = fv_collect facts (mode mid) + fv_f2_collect facts. rc 0 only if F2's target is exactly the expected volume.
  local facts; facts=$(cat); local fail=0; g() { printf '%s\n' "$facts" | sed -n "s/^$1=//p" | head -1; }
  ok() { printf 'PASS  %s\n' "$1"; }; no() { printf 'FAIL  %s\n' "$1"; fail=1; }
  local D; D=$(g F2_DEV)
  case "$D" in disk[0-9]*s[0-9]*) [ "${D%%s[0-9]*}" != "$D" ] && ok "F2 device '$D' has a slice suffix (a volume/partition node, not a whole disk)";; *) no "F2 device '$D' is not of the form diskNsM";; esac
  [ "$(g F2_FSTYPE)" = apfs ] && ok "F2 target filesystem is apfs (not an EFI/FAT partition, not a bare APFS store partition)" || no "F2 target filesystem is '$(g F2_FSTYPE)' - EFI/physical-store/other partition refused"
  [ "$(g F2_CONTENT)" != EFI ] && [ "$(g F2_CONTENT)" != Apple_APFS ] && ok "F2 target is not an EFI or Apple_APFS store partition (content $(g F2_CONTENT))" || no "F2 target content '$(g F2_CONTENT)' is a partition, not an APFS volume"
  [ "$(g F2_NAME)" = FERALECHO_INIT ] && ok "F2 target volume name FERALECHO_INIT" || no "F2 target volume name '$(g F2_NAME)'"
  [ "$(g F2_ENC)" = false ] && ok "F2 target is still UNENCRYPTED and empty-by-construction (about to be replaced)" || no "F2 target encryption is '$(g F2_ENC)' (already encrypted or unknown)"
  [ "$(g F2_INTERNAL)" = false ] && ok "F2 target reports Internal: NO" || no "F2 target reports internal/unknown"
  [ -n "$(g CONT_REF)" ] && [ "$(g F2_CONTAINER)" = "$(g CONT_REF)" ] && ok "F2 target belongs to container $(g CONT_REF), the one container on the verified Seagate" || no "F2 target container '$(g F2_CONTAINER)' != the Seagate's container '$(g CONT_REF)'"
  [ "$(g CONT_ON_T_NVOL)" = 1 ] && ok "that container holds exactly one volume" || no "container holds $(g CONT_ON_T_NVOL) volumes (need exactly 1)"
  return $fail
}
```
## Appendix B — `fv_runner_v3.sh` (one destructive verb: F2)
```bash
# fv_runner_v3.sh -- CONTINUATION after the original runner stopped following a SUCCESSFUL F1. Contains ONE destructive verb (F2). NEVER sourced or run by any test against a real device.
# Sourced AFTER fv_guard_v3.sh, by the OPERATOR, in Terminal.app (bash 3.2). The passphrase is prompted by diskutil (-passprompt); this script never sees it.
fv_run_continue_f2() {
  set -u; unset HISTFILE; set +o history 2>/dev/null
  fv_require_tty || return 1
  fv_attest || return 1
  [ "$(fv_internal_hash)" = "$FV_EXPECT_INTERNAL_HASH" ] || { echo "ABORT: internal disk0 partition-table hash changed since the preflight"; return 1; }
  fv_verify_target mid || { echo "STOP: post-F1 identity/topology gates failed - nothing was changed"; return 1; }
  local T="${FV_TARGET:-}"; [ -n "$T" ] || { echo "ABORT: empty TARGET_DISK"; return 1; }
  local V; V=$(diskutil apfs list -plist | fv_find_volume "$T" FERALECHO_INIT false) || { echo "$V"; echo "STOP: cannot uniquely locate the empty FERALECHO_INIT volume"; return 1; }
  { printf '%s\n' "$FV_FACTS"; fv_f2_collect "$V"; } | fv_f2_decide || { echo "STOP: F2 target check failed - nothing was changed"; return 1; }
  fv_confirm "$FV_FACTS" || return 1                                                   # exact authorization phrase (re-typed after review) + typed device node of the WHOLE DISK
  fv_confirm_node "/dev/$V" || return 1                                                # typed node of the VOLUME F2 will replace
  echo ">> STEP F2 (replaces the EMPTY unencrypted FERALECHO_INIT volume with an encrypted-from-birth volume; diskutil will prompt for the passphrase): diskutil apfs eraseVolume $V -name FERALECHO_VAULT -passprompt"
  diskutil apfs eraseVolume "$V" -name FERALECHO_VAULT -passprompt || { echo "STOP: eraseVolume failed - inspect read-only; do not store anything on the volume"; return 1; }
  sleep 2
  fv_post_run; local rc=$?
  [ $rc -eq 0 ] && echo "POST-FORMAT CHECKS PASSED. STOP. Now do the manual eject/unlock test. Vault creation is a separate authorization." || echo "POST-FORMAT CHECKS FAILED. STOP. Do not use the volume."
  return $rc
}
```
## Appendix C — hashes
| File | SHA-256 |
|---|---|
| `fv_guard_v3.sh` | `6aba813abf778f63d11f50a8eff1603e59a8d5b71b6f46921c98925e01af1b8e` |
| `fv_runner_v3.sh` | `b3338425248a93ab06c6b10579dc81f5bdcc0339576442684c85cbf5d1f876ed` |
| `fv_guard.sh` (executed by the operator, unchanged) | `71b22c049a55cf7f271fa704aae070a68a91aa129734b3b27faefd0a2ca08745` |
| `fv_runner.sh` (executed by the operator, unchanged) | `77d69d95377db26fa218d71e4493bb7ee00d7b4ae7e22337266da019db556f19` |
