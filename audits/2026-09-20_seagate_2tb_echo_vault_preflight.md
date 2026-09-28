# Seagate Backup Plus Slim 2 TB — FeralEcho Vault Preflight (READ-ONLY)

**Date:** 2026-09-20 (local ≈ 16:04–16:11, UTC 23:04–23:11) · **Author:** CLAUDE-M5 · **Status:** PREFLIGHT ONLY.
**Nothing was written to the Seagate. The drive was not formatted, erased, partitioned, mounted, unmounted, ejected, encrypted or repermissioned. No directory or file was created on it. No backup was run. FeralEcho, Git, production state and the frozen protocol were not modified.**
**Evidence labels:** **OBSERVED** (read-only command output in this session) · **INFERRED** (reasoned; not measured) · **UNKNOWN** · **UNTESTED** (would need a write, which this mission forbids).

---

## 0. Records

| Item | Before (23:04:56Z) | After (23:10:30Z) | Same? |
|---|---|---|---|
| Git HEAD | `2fba42644c82b9f7096276f4dd338d615cf1bcce` | `2fba42644c82b9f7096276f4dd338d615cf1bcce` | **yes** |
| `git status --porcelain` | 190 paths | 190 paths; `diff` of the two listings is empty | **yes** |
| Server | PID **29288**, start **Sun Sep 20 07:30:10 2026** | PID 29288, start Sun Sep 20 07:30:10 2026 | **yes** (not signalled) |
| Frozen protocol v1.0 md | `d1968caf…` | `d1968caf…` | **yes** |
| Frozen protocol v1.1 md | `e39e6238…` | `e39e6238…` | **yes** |
| v1→v1.1 traceability | `493600f4…` | `493600f4…` | **yes** |
| `.env` sha256 prefix | `37b9f33c3555222d` (from the previous mission; **not re-read** here) | — | n/a (only its *mode*, 644, was `stat`-ed) |
| Mutable production state (`river_brain.pkl`, FAISS, meta, garden …) | not read, not hashed | not read, not hashed | — |
| Seagate root listing (`ls -laO`) | 14 entries | identical, incl. all mtimes | **yes** |
| Seagate used / free bytes | 46,661,632 / 2,000,288,350,208 | 46,661,632 / 2,000,288,350,208 | **yes, byte-identical** |
| Seagate mount options | `exfat, local, nodev, nosuid, noowners, noatime, fskit` (read-write) | same | yes |

**Confirmations.** No production mutation occurred (the only repository-visible change this mission is this report file — expected `git status` count 191 after it is added; the 190 above was measured before writing it). **No Seagate write by me occurred.** Caveat stated plainly: macOS itself, at mount time (16:02 local, *before* my first command at 16:04), created `.fseventsd/` and `.Spotlight-V100/` on the volume (both timestamped 16:02; Spotlight indexing is **enabled** on it). Those are operating-system writes, not mine; I did not create, modify or remove anything. Because the volume is mounted `noatime`, my directory reads did not update access times.

---

## 1. Device identity (OBSERVED)

| Attribute | Value |
|---|---|
| Physical disk identifier | **`/dev/disk4`** — *whole disk*, "external, physical" |
| Volume identifier | **`/dev/disk4s1`** (partition 1) |
| Volume name | `Backup Plus` (mounted at `/Volumes/Backup Plus`) — *not relied on for identity* |
| Volume UUID | `55403B63-9267-3C55-9EA8-622D0D4E412F` |
| Manufacturer / model | Seagate · `BUP Slim` (media name "Seagate BUP Slim Media") — the Backup Plus Slim family |
| USB IDs | Vendor `0x0bc2` (3010 = Seagate) · Product `0xac30` (44080) · bcdDevice `0x1708` |
| Serial | reported by macOS; **masked here** — ends `…3GNB` |
| Connection | **USB**, "Removable" connection type, `Device Location: External`, media type "Fixed"; port controller `AppleT8142USBXHCI` |
| **Negotiated link** | **480 Mb/s (USB 2.0 High Speed)** — `Device Speed = 2`, `bcdUSB = 0x0210`, power allocated **2.5 W (500 mA)** |
| Nominal capacity | 2 TB |
| Actual whole-disk capacity | **2,000,398,933,504 bytes** (3,907,029,167 × 512 B) = 1.819 TiB; 512-byte blocks |
| Partition map | **FDisk / MBR** ("FDisk_partition_scheme"); one partition, offset 1 MiB, 2,000,397,795,328 B; partition type reported `Windows_NTFS` (the MBR type byte `0x07`, which both NTFS and exFAT use) |
| Filesystem | **exFAT** ("ExFAT", bundle `exfat`) — mounted through **FSKit** (user-space file-system extension) |
| Mounted path | `/Volumes/Backup Plus` |
| Volume total / used / free | **2,000,335,011,840 B / 46,661,632 B (0.0 %) / 2,000,288,350,208 B**; allocation block (cluster) **131,072 B** |
| Mount status | **read-write** (`Media Read-Only: No`, `Volume Read-Only: No`) |
| Encryption | **none / not applicable** — exFAT has no native encryption; no encrypted partition exists (one partition only) |
| Ownership | **ignored**: `noowners` (mount), "Ignore Ownership: Yes" (System Information). Every file appears owned by the logged-in user with mode `rwx------` |
| Spotlight | **indexing enabled** on the volume (`mdutil -s`) |

**How the internal SSD is told apart (never rely on the name):** the M5's internal storage is `/dev/disk0` (internal, physical, 1.0 TB, GUID, APFS containers `disk1`/`disk2`/`disk3`, the last synthesized into `Macintosh HD`, `Data`, `VM`, …). The Seagate is `/dev/disk4`: **External · USB · FDisk/MBR · 2.0 TB · Seagate BUP Slim · one exFAT partition**. A future write-guard must require **all** of: `Device Location: External`, `Protocol: USB`, media name `Seagate BUP Slim Media`, whole-disk size exactly `2000398933504`, USB `0bc2:ac30`, serial suffix, and the volume UUID *(which will change if the disk is ever reformatted, so the vault identity file must record the new UUID at that time)* — and must refuse any target under `disk0`–`disk3`. **The BSD number `disk4` is not stable** (it is assigned in attach order) and must never be used alone.

---

## 2. Existing contents (OBSERVED — names/sizes only; no file was opened)

Top level of the volume: manufacturer material only. **No user data appears present.** ≈ 46.7 MB used.

| Entry | Size | Reading |
|---|---:|---|
| `Start_Here_Win.exe` | 18.2 MB | Seagate Windows helper |
| `Start_Here_Mac.app/` | 8.3 MB (directory) | Seagate Mac helper (standard `Contents/{MacOS,Resources,_CodeSignature,Info.plist}`) |
| `Start_Here_Chromebook.pdf`, `Warranty.pdf` | 1.2 MB, 1.6 MB | manufacturer documents |
| `Seagate/` | 384 KB; 3 entries | `Registration/SerialNumber.xml` only (**not read**, it carries the drive serial) |
| `System Volume Information/` | 384 KB | `WPSettings.dat`, `IndexerVolumeGuid` — Windows-generated bookkeeping (dir dated **Aug 14 2026**) |
| `Autorun.inf`, `.VolumeIcon.icns/.ico`, `._.` | 33 B, 156 KB, 379 KB, 4 KB | manufacturer/AppleDouble stubs |
| `.fseventsd/`, `.Spotlight-V100/` | — | **created by macOS at mount (16:02 today)** |

Not recursed beyond the three manufacturer directories above (metadata only). **Conclusion: empty in the sense that matters — safe to repurpose without losing user data.** Two observations worth a human's glance: the Windows-generated `System Volume Information` dated 2026-08-14 **suggests** (INFERRED) the disk was attached to a Windows machine once after manufacture (retail/QA or a prior owner) — there is no user content, but it may not be a factory-sealed state; and the factory helper files are re-downloadable from Seagate.

---

## 3. Filesystem suitability (current exFAT, evaluated **without** modification)

### 3.1 What FeralEcho must preserve — measured on the M5's real tree (metadata scan, no contents read)
22,818 files (1,593,904,534 B logical) and 526 directories in scope (caches/`.DS_Store` excluded). Measured: **3 paths contain an exFAT-illegal character** — the scaffold chain `./root:xnu-11417.140.69.705.2~1/RELEASE_X86_64/my_new_dir` (a colon; three *empty* directories, an Echo-incident artifact); **151 executable files** outside `.git`; **266 files carry extended attributes** (mostly macOS-generated: `com.apple.lastuseddate#PS` 201, `com.apple.macl` 181, `kMDLabel…` 60, `com.apple.provenance` 38, `com.apple.quarantine` 12, `TextEncoding` 2, `WhereFroms` 2); **0 symlinks, 0 hard links, 0 case/normalization collisions**; longest component 77 B, longest path 113 B; 8 paths with a non-ASCII em-dash (fine on exFAT); `.env` is mode 644.

### 3.2 Requirement-by-requirement
| Must preserve | exFAT (current) | Verdict |
|---|---|---|
| Complete Git repos incl. `.git` | bytes preserved and `git` operates on a copy, but **hook/executable bits are lost** (4 hooks in `.git/hooks`), file modes/ownership are not stored, and every restored object/file must have modes re-applied from `manifest/stat.tsv` | **degraded (recoverable from manifest)** |
| Working-tree files | content preserved; **151 exec bits lost**; **266 files' xattrs lost or turned into `._*` AppleDouble sidecar files** (which the judge would count as "extra files") | **degraded** |
| JSON / JSONL / pickle / FAISS / logs | pure bytes — preserved exactly; hashes independent of filesystem | **fully preserved** |
| `.env` | bytes preserved, but **no permission or ownership enforcement**: anyone who mounts the disk reads it, and the disk is unencrypted | **unacceptable without encryption** |
| Executable / source files | content yes; x-bit no | degraded |
| Filenames and structure | **the 3 colon-named directories cannot be created** (exFAT spec forbids `: * ? " < > \| \`; Apple's driver behaviour on `:` is **UNKNOWN/UNTESTED** without a write) — they are empty, so no data is lost, but "complete structure" is not exact; otherwise structure is fine (no collisions, short paths) | **degraded (trivially)** |
| Large immutable generations | **no immutable flag** (`chflags uchg` is a macOS HFS+/APFS feature — UNTESTED on exFAT); read-only is at best a DOS attribute; **no journal** — an unclean eject or power loss can leave the filesystem inconsistent; **128 KiB clusters waste 2,921,394,794 B (2.92 GB) on this tree** (on-disk ≈ 4.52 GB vs 1.59 GB logical; APFS 4 KiB blocks waste 0.07 GB) | **weak for "immutable, sealed" generations** |
| SHA-256 manifests | content hashes, unaffected | fully preserved |

Additional facts: MBR keeps **one** partition table (GPT keeps a backup copy); exFAT is served through FSKit (a user-space module — maturity/performance on 22 k small files **UNKNOWN**); Spotlight will index and scatter `.Spotlight-V100`, `.fseventsd`, `.Trashes`, `._*` onto the vault; the only real advantage of exFAT is cross-platform readability (Windows/Linux/any Mac since 10.6.5).

### 3.3 The other filesystems, for the decision
| Format | Permissions / xattrs / symlinks / hardlinks | Encryption | Journal / integrity | Notes |
|---|---|---|---|---|
| **APFS (Encrypted)** | all preserved | **native, per-volume passphrase** | copy-on-write, crash-safe metadata; snapshots | macOS ≥ 10.13 only; not readable on Windows; APFS is tuned for flash, acceptable on a spinning disk for large sequential generations |
| APFS (unencrypted) | all preserved | none | as above | fidelity ok, secrets exposed |
| Mac OS Extended (Journaled) / (Journaled, Encrypted) | all preserved | encrypted variant exists | journal | legacy; supported for now; prefer APFS unless the Intel machine were very old |
| exFAT | **none of the above** | none | none | current state |
| NTFS | n/a | n/a | n/a | **read-only on macOS** — unusable as a vault |
| Encrypted disk image (sparsebundle/dmg, APFS inside) **on** exFAT | full semantics *inside* the image | **AES password** | APFS inside | no reformat needed; adds a layer (image bands are the single point of corruption; mount step; exFAT below still un-journaled) |
| tar (pax) archive per generation on exFAT | preserved *inside the archive* | none | none | preserves modes/xattrs/dirs; loses browsability; still unencrypted |

---

## 4. Encryption
**Currently: not encrypted, and it cannot be encrypted in place** — exFAT has no macOS-native encryption; there is no hardware-encryption software on the disk (only the registration folder). Every generation will contain `.env` (API keys, `GREMLIN_SECRET`, `ECHO_PARTNER_SECRET`) — a lost or borrowed unencrypted disk is a credential leak.
Safest **macOS-native** options (none performed):
1. **Reformat to APFS (Encrypted)** with GUID partition map — full-volume AES-XTS, passphrase-unlocked on mount, ownership/permissions/xattrs/snapshots preserved. *Best fidelity and best protection.*
2. **Keep exFAT** and put an **encrypted APFS sparsebundle/dmg** on it (`hdiutil`/Disk Utility "New Image → Encrypted"). Non-destructive; keeps Windows-readable outer disk; but weaker (extra layer, band-file corruption risk, outer exFAT un-journaled).
3. Do not encrypt individual files ad hoc; do not put secrets in relay text.
**Custody (decision for the operator, no secret exposed here):** a lost passphrase means unrecoverable vault — keep the passphrase in two independent places (a password manager *and* an offline written copy); do not rely on a Keychain that lives only on the M5.

---

## 5. Capacity analysis
**Set to preserve (M5, re-measured today):** 22,818 files, **1,593,904,534 B logical** (drifted up from 1,592,293,851 B two hours earlier — the tree changes). Free space: **2,000,288,350,208 B**.

| Quantity | exFAT as-is | APFS (4 KiB blocks) |
|---|---:|---:|
| On-disk size of one M5 generation (set + slack + bundle/manifests ≈ 0.05–0.1 GB, INFERRED) | **≈ 4.6 GB** (4,515,299,328 B + overhead) | **≈ 1.75 GB** |
| One generation as a share of free space | 0.23 % | 0.09 % |
| Hard-reserve rule proposed | keep **free ≥ max(25 % of volume = 500,083,752,960 B ≈ 500 GB, 200 GB)**; alarm at **60 % used**; refuse new generations at **75 % used** | same |
| Usable budget above the reserve | ≈ 1.50 TB | ≈ 1.50 TB |
| Generations that fit, **both lineages combined, if Intel ≈ M5** | ≈ 326 (today's size) · ≈ 163 (each 2× larger) | ≈ 857 · ≈ 428 |
| Per lineage (even split) | ≈ 163 · ≈ 81 | ≈ 428 · ≈ 214 |

**Rationale for a conservative reserve:** 25 % free protects against growth of the set (RiverBrain/logs/FAISS/`.git` all grow; the Intel set is UNKNOWN), against an HDD slowing sharply when nearly full, against an SMR drive's rewrite penalties (INFERRED — see §8), and keeps room for manifests/reports and one temporary re-copy after a failed attempt. **Restore drills do not consume vault space:** they extract into a temporary location on the M5's internal SSD (754 GB free) and only append a small report to `restore_drills/`. Ancestral material (≈ 0.7 GB logical, incl. the 592 MB 2026-09-05 zip) is a one-time `A001`. Cadence sanity (from the earlier plan): weekly M5 + monthly Intel ≈ 64 generations/year — even at exFAT-2× sizes ≈ 0.6 TB/year, so the vault would last years; daily M5 would consume ≈ 1.7 TB/year at exFAT-2× and is **not** advisable on this disk without pruning under the two-other-copies rule.
(The earlier plan's per-volume rule `2 × set + 10 GiB` is trivially satisfied here; the 25 % floor is the binding rule for the vault.)

---

## 6. Vault layout (DESIGN — nothing created)
```
FERALECHO_VAULT/                                   (the ONLY top-level directory FeralEcho tools may create on the disk)
  vault_identity/
    VAULT_ID.txt          vault UUID (new, random), created-UTC, filesystem, volume UUID at creation, disk size, USB 0bc2:ac30, serial-suffix hash, lineages allowed
    WRITE_GUARD.txt       the refuse-unless rules of §1 (external + USB + size + volume UUID + vault ID; never disk0-disk3)
    README.txt            purpose; "backup vault, not a sync master"; how to verify; "DATA RECOVERY, not necessarily direct executability"
  vault.log               append-only registry (>> only): generation sealed / cold-verified / restore-tested events with manifest hashes
  M5/
    generations/
      M5_2026-09-20_G001/     (short alias "M5_G001"; the full ID keeps the date so IDs never collide across machines)
        README.txt  source/  state/  identity/  manifest/   + markers RECEIVING-* -> SEALED-<manifest8> | ABANDONED-<reason> | QUARANTINED-NOT-KNOWN-GOOD
      M5_..._G002/
  INTEL_2020/
    generations/
      INTEL_2026-..._G001/    same internal structure
  restore_drills/
    M5/     drill reports only (append-only files)
    INTEL_2020/
  _reports/               cold-verify and validation reports, append-only, never inside a sealed generation
```
Rules: **M5 and Intel never share mutable state** — each lineage has its own `generations/` tree, its own IDs, its own registry lines; no file, symlink or index is shared; **no generation is ever overwritten** (plain `mkdir` per generation; the procedure STOPs if it exists); **no synchronization, no merging, no `--delete`**; generations are sealed read-only and their manifests are never edited. *Optional stronger separation (only if APFS is chosen):* create **two APFS volumes** (`M5_VAULT`, `INTEL_VAULT`) in the one container — shared free space, separate mounts and separate passphrases; the directory layout above still applies inside each. OS-generated noise (`.Spotlight-V100`, `.fseventsd`, `.Trashes`, `.DS_Store`, `._*`) may appear at the vault root and inside directories; the manifest scope must be defined so it neither flags nor silently ignores them *inside* a sealed generation (and Spotlight indexing on the vault should be disabled after formatting — an authorized change, not made now).

---

## 7. Backup priority — reassessed
The 2 TB disk is a **physically separate** device, needs no network and **removes the SSH/Remote-Login dependency** from the first copy. The proposed order stands, with two amendments the discovery forced:

0. **(new) Decisions before any write:** filesystem/encryption (§10), passphrase custody, and the **USB link** — the disk is currently negotiated at USB 2.0 speed (480 Mb/s, 500 mA); reseating it on a USB-3 cable/port is an operator action to try first.
1. **M5 → Seagate G001** — *but* build the sealed generation on the internal SSD first (`OWN_LOCAL`, fast, per-file before/after hashing while the server runs) and then copy the *sealed, static* generation to the Seagate. Rationale: at 480 Mb/s a ≈ 320 MB FAISS/meta pair takes ≳ 10 s per attempt on the USB disk versus ≈ 1 s locally — a 10× wider window for the live-mutation race (INFERRED from ≈ 26 persists/hour). Local staging also gives a same-disk second copy.
2. **Verify M5 G001 completely:** manifest recomputation, cold re-hash **after the operator unmounts and reconnects the disk**, structural validation of the copy in the jail.
3. **Restore drill** into a temporary directory on the **internal SSD** (not the vault, not the live tree).
4. **Connect the Seagate to the Intel** and independently preserve **Intel → `INTEL_2020/…_G001`** (the Intel Claude runs its own read-only discovery first; Intel must be able to mount the chosen filesystem — APFS needs macOS ≥ 10.13, exFAT is universal; its free space is irrelevant because the vault holds the copy).
5. **Mac-to-Mac cross-backups stay valuable**, not optional in the strict sense: with only one vault disk, each lineage has *one* off-machine copy; the earlier rule "no generation deleted until two other verified copies exist on physically distinct storage" is met only after a third copy (cross-backup or a second disk). The cross-backup plan is therefore kept as the second physical copy, just lower priority and no longer on the critical path.
Nothing found contradicts "M5 first": the M5 is the machine holding the only verified recent lineage and it is the machine the disk is attached to. Intel discovery remains a prerequisite only for step 4.

---

## 8. Drive health and identity (OBSERVED)
* **SMART: "Not Supported"** (`diskutil info disk4`/`disk4s1`); `smartctl` is not installed. The USB bridge does not expose SMART to macOS; the "SMART Status: Verified" line in System Information belongs to the internal SSD, not to this drive.
* What macOS **does** expose non-destructively: manufacturer, model, USB IDs, firmware/bcd version, serial, negotiated speed and power allowance, capacity, block size, partition map and offset, volume UUID, filesystem, mount options.
* **Drive type not reported** (`Solid State: Info not available`). The Backup Plus Slim 2 TB is a 2.5-inch spinning drive — **INFERRED from the product line, not from macOS** — and drives of this class are commonly shingled (SMR): slow sustained writes once the cache fills and sensitivity to power loss/unclean disconnects. **UNKNOWN** for this unit.
* **Link/power concern:** the negotiated USB 2.0 link and the 500 mA allowance are below what a bus-powered 2.5-inch drive normally uses on USB 3; this is not evidence of a fault, but a marginal power budget plus an un-journaled filesystem is a poor combination during a long copy. A SuperSpeed link (5 Gb/s, 900 mA) should be established first (cable/port check by the operator).
* **Speed estimate (INFERRED, unmeasured):** at USB 2.0 ≈ 30–40 MB/s sustained; 1.6 GB is ≈ 1 minute of raw transfer, but 22.8 k small files through FSKit-exFAT plus the verification re-reads plausibly make one generation 15–30 minutes; USB 3 would be limited by the HDD (~100 MB/s).
* No surface test, no write test, no test file was created. The first real health signal will be the first fully verified generation (write, cold re-read, hash) — and, given a single disk, a second copy elsewhere.

---

## 9. Command safety — every command used (all read-only)
| # | Command | Purpose | Writes? | Touches internal M5 disk for modification? |
|---|---|---|---|---|
| 1 | `git rev-parse HEAD`; `git status --porcelain` (`GIT_OPTIONAL_LOCKS=0`) | before/after repo state | no | no (repo read only) |
| 2 | `ps -o pid=,lstart= -p 29288`; `date -u` | server PID/start; time | no | no |
| 3 | `diskutil list` | all disks, incl. internal for contrast | no | lists only |
| 4 | `mount` (filtered) | mount options | no | no |
| 5 | `ls -la /Volumes` | volumes present | no | no |
| 6 | `diskutil info disk4` / `diskutil info disk4s1` | whole-disk and volume identity | no | **targets disk4 (the Seagate) only** |
| 7 | `df -k` / `df -h` on `/Volumes/Backup Plus` | space | no | no |
| 8 | `ls -laO`, `stat -f` on the volume root; `du -sk` on 3 manufacturer directories; `find … -maxdepth 3 … \| sed` names inside them | contents check (names/sizes only; no file opened) | no | no |
| 9 | `system_profiler SPUSBDataType` (empty on this OS), `SPUSBHostDataType`, `SPStorageDataType` (serial masked) | USB identity, speed, power | no | no |
| 10 | `ioreg -p IOUSB -w0 -l`, `ioreg -c IOUSBHostDevice -w0 -l` (filtered) | negotiated speed, bcdUSB | no | no |
| 11 | `command -v smartctl` | SMART tooling | no | no |
| 12 | `mdutil -s "/Volumes/Backup Plus"` | Spotlight *status* | no (status query) | no |
| 13 | `diskutil info /System/Volumes/Data` (grep) | compare internal filesystem personality | no | reads only |
| 14 | `python3` scripts using `os.walk`/`os.lstat` over the repo tree (names, sizes, link counts) and `find … \| xargs xattr` (attribute **names** only) | exFAT-compatibility scan of the *source* tree | no | reads only |
| 15 | `shasum -a 256` of three frozen protocol files; `stat -f '%Lp' .env` (mode only) | integrity records | no | no |
**No `diskutil erase/partition/mount/unmount/eject/repair/verify/apfs`, no `hdiutil`, no `touch/mkdir/cp/mv/rm/chmod/chown/chflags`, no `mdutil -i/-E`, no redirection onto the Seagate, no `sudo`.** No command took an internal-disk identifier as an argument to anything but a read-only `diskutil info`/`list`. (`diskutil verifyVolume` and `fsck_exfat` were deliberately **not** run because they may require unmounting.)

---

## 10. Recommendations and the stop gate
**Is the current formatting appropriate?** No — it is *usable* but materially weakens preservation fidelity and cannot protect secrets: no permissions or ownership, no encryption, no journal, no immutability flag, executable bits/xattrs lost, 3 illegal directory names, 2.9 GB of cluster slack, MBR with a single partition table, USB-2 link, Spotlight indexing on.
**Would reformatting provide a meaningful advantage?** Yes: **APFS (Encrypted)** on a GUID map keeps modes, ownership, symlinks, xattrs and empty structure exactly, encrypts `.env` at rest, is crash-safe, supports snapshots, and removes the slack. The cost — losing the factory helper files (irrelevant, re-downloadable) and Windows readability — is small. The alternative that avoids erasing (an encrypted APFS sparsebundle on the exFAT volume) is acceptable but strictly weaker.
**Encryption:** yes, use it — the vault will hold `.env` and the shared secrets.
**Recommended next action (for the operator):** (a) decide **APFS (Encrypted)** versus the non-destructive sparsebundle; (b) decide passphrase custody (two independent places); (c) reseat the drive on a USB-3 cable/port and re-check that macOS reports 5 Gb/s; (d) only then give an explicit written authorization naming the disk identity (§1: `disk4` **and** `0bc2:ac30` **and** serial suffix **and** exact size **and** volume UUID) for the *format-and-create-vault* step, which is a separate mission; the backup itself is a further, separate authorization.

### STOP-GATE VERDICT
**SAFE AFTER FILESYSTEM/ENCRYPTION DECISION**

**Why.** The device is unambiguously identified and is not the internal SSD; it holds no user data; it has 2 TB, more than enough for years of both lineages under a 25 % reserve; and nothing observed argues against using it. But writing FeralEcho generations to it *as it is now* would (1) put `.env` and other credentials on an unencrypted, permissionless disk, (2) lose executable bits, xattrs and three directory names, (3) forgo immutable sealing and journaling, and (4) run over a USB-2 link. Those are decisions only the operator can make (format? encrypt? which passphrase custody? cable?), so the disk is not yet ready — but neither is it unusable ("DO NOT USE YET" would be too strong). **No vault was created, no backup was run, and the disk was not formatted.** The next phase requires explicit operator authorization.
