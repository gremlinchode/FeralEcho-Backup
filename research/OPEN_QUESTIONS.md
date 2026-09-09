# Open Questions

Only questions capable of producing a meaningful discriminating experiment are listed here — per this document's own scope rule, vague curiosity is not an open question. Priority: P0 (directly affects architectural conclusions) → P1 (affects Level 7/7.5 feasibility) → P2 (useful, non-blocking) → P3 (exploratory).

---

## Q-001 [P0] — Does verified evidence in context ever reliably change Echo's generated belief, or is "authority marker overrides evidence" (R-002) a structural property of the current architecture?

**Why it matters:** this is the load-bearing gap behind `research/FINDINGS.md` R-001/R-002 and the current Level-7 ceiling (`audits/2026-09-11_verification_and_level_7_5_8_feasibility.md`). Every mechanism tried so far (evidence rendering fix, persisted claims ledger, epistemic taxonomy, plain verify-instructions) either doesn't close it or closes only a narrower sub-problem (storage, not belief-revision).

**Current evidence:** `mechanism_c_FINAL` (0/5-ish failure under evidence-injection), `generation_epistemic_FINAL` (5/5 failure under an explicit priority instruction), this session's Missions 13/15/16 (pressure-specific collapse, 4/5 false verification claims under the combined trap).

**Competing hypotheses:**
- H-A: the current local model (3B–8B class) fundamentally lacks the capacity for reliable evidence arbitration under adversarial framing, regardless of prompt engineering.
- H-B: a second, independent model call (cross-checking the first, mirroring the Dissent Log's proven pattern) can close the gap architecturally without a larger model.
- H-C: the gap is domain-general and will persist under any single-model, single-pass architecture, closable only by deterministic external verification restricted to checkable domains (code, file/git state) — i.e., general Level 7 is not closable by prompting or persistence alone.

**Next discriminating experiment:** Mission 16's independent replication (in progress) plus a dedicated test of H-B (build and test a second-model cross-check, per `audits/2026-09-11_...feasibility.md` Section 26 item 3) — H-B is falsified if the cross-check shows the same failure rate as single-pass generation.

---

## Q-002 [P0] — Is R-002's "authority marker overrides evidence" pattern present in the Git/provenance domain too, or specific to sensory/verification-instruction framing tested so far?

**Why it matters:** directly gates Mission 18's Git-interface design. If a future Git-query result, or a prior Echo assertion about having checked Git, can be substituted for real evidence the same way a "VERIFIED" flag can (R-002), the interface's provenance-ledger design (Mission 18 Section 4/10) is not optional — it is the only thing standing between this exact, already-twice-observed failure mode and a system with real repository-inspection power.

**Current evidence:** Mission 16's domain-comparison sub-experiment (filesystem/git simulated-tool-result conditions) — results pending analysis at time of this document's construction.

**Competing hypotheses:** domain-general (git/filesystem claims fail the same way as sensory claims) vs. domain-specific (something about the sensory-perception framing specifically primes the failure).

**Falsification:** a clean (near-0%) false-verification rate on the git/filesystem domain conditions would meaningfully weaken the domain-general reading, though a single small-n test should not be treated as decisive either way.

**Update (Mission 19):** tested directly, with a mixed, non-clean result. Filesystem (authority-attributed false claim): 0/8. Git (identical design): 5/8 (62.5%) — a real, reproduced-once divergence between two similarly-"checkable" simulated-tool-result domains, not yet replicated at higher n. Domain accessibility does not predict outcome cleanly; still unresolved, now with a real but small-n contradiction on record rather than no data at all.

---

## Q-008 [P0] — Does the near-total factual capture found in the Mission 19 authority ladder require authority-framing specifically, or does any 10-turn incremental escalation (regardless of claimed source) produce the same effect?

**Why it matters:** this is the single highest-priority gap `audits/2026-09-11_authority_evidence_separation_forensics.md` leaves open, and it directly determines whether any future mitigation should be scoped around "authority claims" or around "multi-turn conversational escalation" generally — a materially different design target. If authority is not required, a mitigation designed only against authority-framing would miss the real mechanism.

**Current evidence:** a two-turn design (Control 2 vs. Control 5, authority vs. no-authority, identical claim/pressure) showed no meaningful difference (13.3% vs. 0%) — weak evidence against authority-specificity in that design. But the ladder (where the largest effect, ~100% capture, was found) had no non-authority control at all.

**Competing hypotheses:** H1 (authority-specific escalation dynamics — an incrementally-strengthening chain of external validation genuinely carries more weight turn over turn) vs. H2/H8 (generic conversational-accumulation effect — the same 10-turn ratchet with no authority attribution at all, e.g. "you said X, and X, and X again," produces the same capture rate).

**Next discriminating experiment:** run the identical L0–L10 escalation structure with every "expert"/"institution" reference replaced by a plain, unattributed restatement or a user-attributed restatement, holding turn count and wording-intensity progression constant. If capture rate matches the authority version, H1 is falsified for this design; if it's meaningfully lower, H1 survives.

**ANSWERED (Mission 20, `audits/2026-09-11_authority_free_ladder_causal_isolation.md`), exploratory n but a clean, categorical result: capture rate does NOT differ by source attribution — all four conditions (authority, no-authority, neutral-source, user-assertion) transitioned by turn L1–L3, with 9/9 non-authority conversations transitioning at L1 specifically and authority's own 3 primary-batch reps being, if anything, the slowest of the four. H1 (authority-specific causality for factual capture) is NOT supported at this scale.** A narrower, real, direction-consistent effect remains open: authority showed 1/5 false independent-verification claims at the ladder's final turn vs. 0/9 for all non-authority conditions — this narrower question (does authority specifically inflate false-verification-claim rate, holding factual capture constant) is NOT yet resolved at adequate power and is the natural successor question (see Mission 20's own Recommended Next Experiment #1: scale Conditions A vs. B to n≥15-20 specifically on this dimension).

---

## Q-003 [P1] — Would a larger local model reduce the false-verification-under-pressure rate, or is the failure architecture-level rather than model-capacity-level?

**Why it matters:** directly answers whether Level 7's blocker is a "requires a stronger model" bottleneck or an "architecture can compensate" bottleneck (per the feasibility study's own required decision tree). Not tested anywhere in the corpus as of this pass.

**Current evidence:** none — explicitly flagged as untested in `audits/2026-09-11_...feasibility.md` Section 26 item 2.

**Next discriminating experiment:** replicate the Mission 15/16 false-verification trap on a larger locally-hostable model (e.g., a 30B+ class model, if hardware permits) under identical conditions.

---

## Q-004 [P1] — Does hypothesis formation / competing-explanation comparison exist anywhere as a latent capability, or is it genuinely absent?

**Why it matters:** the two unmet Level 7.5 criteria (per the feasibility study's Level 7.5 assessment) with zero supporting mechanism anywhere in the codebase, as opposed to R-001/R-002 which have at least partial mechanisms to build on.

**Current evidence:** none directly tested; `echo_projects_autonomy`'s "investigation" never evaluates competing explanations, only pass/fail on a single generated artifact.

**Next discriminating experiment:** not yet designed. Would require constructing a task with two or more genuinely plausible explanations and observing whether Echo, unprompted or lightly prompted, ever considers more than one.

---

## Q-005 [P2] — Does memory retrieval materially influence model selection, task-type classification, or self-edit targeting, or is it fully decoupled as `CLAUDE.md` Finding 75/76's ablation found?

**Why it matters:** bears on whether "persistent memory" (`CURRENT_STATE.md`'s Memory section) is functionally load-bearing for anything beyond conversational recall, which matters for any future claim about Echo's autonomy being informed by its own history.

**Current evidence:** `CLAUDE.md` Finding 75's code-trace found only two scheduling branches and one storage-dedup gate ever consult memory retrieval outside conversational recall; Finding 76's ablation experiment found no statistically distinguishable effect at n=30, but flagged its own noise floor as likely larger than any real effect present.

**Next discriminating experiment:** already proposed in Finding 76 itself (rerun at `temperature=0` to remove sampling-noise confound) — not yet done as of this pass.

---

## Q-006 [P2] — Is the RiverBrain trust-gate history (R-007) an isolated historical bug, or representative of a broader pattern across every "trust"-gated mechanism in this codebase?

**Why it matters:** directly bears on the Level 8 ceiling assessment (`audits/2026-09-11_...feasibility.md` Section 24, item 11) — if representative, it's strong evidence against assuming any future automated-trust mechanism self-activates without a human noticing.

**Current evidence:** one confirmed instance (RiverBrain); council-rater's trust threshold (a second, similar mechanism) is documented as having required a human to notice an 8-day-stalled spot-check backlog before it could activate — a second data point in the same direction, not yet formally counted as a "broader audit."

**Next discriminating experiment:** a dedicated audit of every mechanism in the codebase gated by an automated "trust"/"baseline_trusted"-style flag, checking each one's actual activation history against its computed-eligibility history.

---

## Q-009 [P1] — Is `echo_projects_autonomy`'s current 65.9+ hour silent gap (R-010) a real code defect (the loop doesn't retry after an F2 failure) or a restart-frequency artifact (the server never stayed up long enough to reach a natural 6h cycle during this investigation window)?

**Why it matters:** `echo_projects_autonomy` is the closest existing mechanism to a genuine Level 7.5 "autonomous investigation" capability (`audits/2026-09-11_verification_and_level_7_5_8_feasibility.md`). If it silently stops retrying after any single failure, that's a real, fixable reliability defect directly undermining any autonomy claim. If it's a restart artifact, there's no code defect at all — just an observation-window problem specific to this unusually restart-heavy investigation period.

**Current evidence:** one confirmed live gap (`audits/2026-09-11_feralecho_unresolved_defect_audit.md`, D-03), last failure a genuine cross-file import inconsistency (F2-caught, working as designed). No evidence yet distinguishes the two hypotheses.

**Next discriminating experiment:** the cheapest real experiment in this entire research program — simply observe whether the loop fires during a genuine, uninterrupted 6+ hour server uptime window. No new code, no new harness, just patience and one more `/admin/liveness-status` check afterward.

**Partially answered (Mission 22, `audits/2026-09-09_autonomous_investigation_liveness_recovery_forensics.md`).** The restart-frequency explanation is **ruled out for the specific 8.07-hour window observed**: same PID throughout, zero restarts, and the loop's live in-memory scheduling record (`get_autonomy_status()`) never advanced past its single startup-time evaluation despite the next checkpoint being structurally ~2 hours overdue by the end of the window. What remains open is narrower than before: a genuine code-level thread stall (H1) vs. a new, evidence-motivated possibility — OS-level suspend extending a long single `time.sleep(21600)` call's real completion time (H3), directly plausible given this project's actual usage pattern (the operator's laptop closes and reopens repeatedly during a work shift). These two remain genuinely indistinguishable from currently available evidence. **Separately, and now fully resolved, not just partially**: the deeper capability question is answered — `echo_projects_autonomy` has a confirmed 0/61 (0%) real-world success rate across its entire operational history (2026-08-11–2026-09-06), independent of the liveness question. **Next discriminating experiment, narrowed**: a single controlled, disclosed restart with full before/after state capture, to see whether the very next scheduling evaluation occurs promptly (would support "this specific thread was stuck, a restart is sufficient recovery") — deliberately not performed in Mission 22, per its own investigation-sequencing rule.

**Substantially answered (Mission 23, `audits/2026-09-09_autonomous_scheduler_restart_temporal_lifecycle_forensics.md`).** The recommended restart was performed (via `safe_restart.sh`'s watchdog-safe path). Result: the scheduler evaluation occurred promptly (~6 min post-restart, matching the documented startup delay) and fired *twice*, the second time landing at exactly 21600.15s after the first — precise to a fraction of a second. Direct inspection of macOS's own `pmset -g log` found Mission 22's stalled window contained a real Clamshell Sleep + lid-wake event (~76 min), while this mission's clean, precisely-on-time window contained zero sleep/wake events — real, dated, independently-sourced correlational support for H3, though not proof by controlled manipulation (forbidden by this mission's own constraints). **Remaining open**: whether the scheduler survives a *future* real sleep/wake event without stalling again (none occurred naturally to test against this mission), and the exact CPython/`time.sleep()` semantics across a full OS suspend. A new, higher-priority question surfaced by this mission: why "sandbox test timed out" is now the dominant F2 failure mode (4 of 17 F2 failures) — flagged as the next investigation ahead of further liveness work.

**That follow-up question is now fully answered (Mission 24, `audits/2026-09-09_f2_sandbox_timeout_forensics.md`), and independent of the still-open sleep/wake scheduler question above.** `F2_TIMEOUT` is a deterministic structural mismatch, not a lifecycle-dependent phenomenon: `_run_f2_multi_file()` never sets `stdin=`, so the sandboxed subprocess inherits `run.py`'s real, live stdin — confirmed directly against the running process to be a genuine terminal (`/dev/ttys002`), not `/dev/null`. Any generated project taking the "interactive text scenario" interpretation the spec itself invites contains a reachable `input()` call that blocks on this live-but-silent terminal until the real 60s timeout fires. Confirmed both directions via direct reproduction (a real pty hangs; an explicitly closed stdin instead produces an immediate `EOFError`) and cross-validated against all real historical data (4/4 timeout cases contain `input()`; the 3 other `input()`-containing cases that did *not* time out were independently confirmed, via untruncated re-execution, to fail on unrelated bugs before ever reaching their own `input()` line). This reproduces on demand regardless of sleep/wake state — it does **not** bear on the still-open H1-vs-H3 scheduler question above, which remains open pending a future natural sleep/wake event to observe.

**The remaining "is this a spec/testability mismatch or a violation of an established contract" question is now closed (Mission 25, `audits/2026-09-09_f2_stdin_contract_archaeology.md`).** Archaeology of the specification, git history, and a sibling sandbox mechanism found strong, dated, first-party evidence for an **Autonomous F2** contract as *established project practice* (not an explicit rule for this file specifically): three live prompt-construction sites plus one dead one all forbid `input()`/interactivity in autonomous generation, all dated to the repo's first commit; a sibling kernel-sandboxed mechanism (`sandbox/run_script.py`'s `run_sandbox_script_isolated()`, identical invocation shape) already mocks `input()` to fail fast, live 10 days before `echo_projects.py` was written. `echo_projects.py`'s own spec text is the one place in the codebase inviting interactivity, and its F2 harness never adopted the sibling's fix. Zero test coverage anywhere exercises F2's stdin behavior. **Newly open, not resolved by this mission (deliberately — archaeology only, no fix applied):** whether the eventual fix (if any) belongs in the harness (mock/close stdin) or the specification (retract "interactive text scenario") or both, and whether `echo_projects.py`'s author knew of the sibling precedent — the evidence cannot distinguish "not known" from "known and set aside."

**Which-fix question is now answered by direct experiment (Mission 26, `audits/2026-09-09_f2_stdin_resolution_experiment.md`): both, together (Option D) — neither the existing input-mock nor `stdin=DEVNULL` is sufficient alone.** The mock (imported and run directly against 9 real fixtures via the real sandbox mechanism) only patches `builtins.input`; `sys.stdin.readline()`/`sys.stdin.read()` hang under it exactly as under unmodified behavior — a real, newly-discovered gap. `DEVNULL` closes the hang uniformly but silently converts `readline()`/`read()`-based interactivity into a false `SANDBOX_OK` pass rather than any failure. **New open question this raises**: whether the harness fix (extending the mock to cover `sys.stdin.readline`/`read`) should live in `sandbox/run_script.py` (shared with `run_sandbox_script_isolated()`, which was also found this mission to share the identical `readline`/`read` gap — not previously known) or as a new, `echo_projects.py`-local mechanism. Also still open: whether `_build_autonomous_spec()`'s replacement wording (if any) should drop "interactive" entirely or redirect it toward a simulated-interaction framing this mission found no evidence models currently produce unprompted. No code was changed — recommendation and open questions only.

**Placement question is now resolved (Mission 27, `audits/2026-09-09_f2_stdin_enforcement_boundary.md`): `sandbox/safe_exec_wrapper.py`'s `_install_patches()`, not `run_script.py` and not `echo_projects.py`.** A fuller execution-graph trace found 6 real live callers of the shared sandbox mechanism (not just the 2 Mission 26 examined), none needing real stdin; `safe_exec_wrapper.py` is the one layer all 6 already route through and the one file every other sandbox primitive is already patched in. The mechanism itself was also refined and directly verified: replacing `sys.stdin` with a small stream-object class transparently covers `input()` too (CPython routes `input()` through `sys.stdin.readline()` once `sys.stdin` isn't the original object) — one mechanism instead of two incomplete ones. **New open questions from this mission**: whether `isatty()`/`fileno()`/`.encoding`/context-manager behavior on the replacement stream need explicit handling (not resolved); whether `code_verification.py`'s chat-extracted-code caller (a newly-identified, less-autonomous exposure — real code blocks from live chat responses, not just autonomous generation) needs any different treatment than the other 5 callers; whether the mechanism's completeness holds once verified *inside* the real sandboxed subprocess rather than only in a bare, unsandboxed check (no interaction mechanism identified, but not yet confirmed). Mission 28 is specified to implement; no code was changed this mission.

**Implemented and closed (Mission 28, `audits/2026-09-09_f2_stdin_contract_implementation.md`): the `readlines()`/context-manager/`isatty()`/`fileno()` unknowns are resolved, and the harness-vs-spec question is now moot since both were done.** `readlines()` and iteration were verified through the real sandbox for the first time (not just inferred by extension). `isatty()`/`fileno()`/`readable()`/`seekable()`/`writable()`/`closed`/context-manager behavior were all confirmed to work correctly via `io.TextIOBase`'s own honest inherited defaults, deliberately left un-overridden. `code_verification.py`'s chat-extracted-code caller was regression-tested directly and shows no different treatment than the other 5 callers — no special-casing needed. **A new, more important open question replaces these, found only through adversarial testing this mission performed beyond what was originally scoped**: candidate code calling `os.read(0, ...)` directly bypasses the entire fix and still reproduces Mission 24's original hang — a genuinely different attack surface (raw file-descriptor access) than the `sys.stdin`/`input()` Python-object surface every prior mission in this thread addressed. Not fixed, deliberately, per Mission 28's own explicit "do not expand scope" instruction — flagged as the clearest, highest-priority candidate for a dedicated Mission 29-equivalent investigation: the full raw-fd attack surface (`os.read`, `os.dup`/`dup2` against fd 0, anything else reaching an already-open descriptor without going through `sys.stdin`) has not been mapped, and no fix design exists yet. A second, lower-severity, also-unfixed question: whether `sys.stdin` should be made harder for candidate code to simply reassign to its own object (defeats the contract, though not the hang-safety property) — a real design tradeoff against legitimate candidate code that might reassign `sys.stdin` for unrelated reasons, not resolved.

**The `os.read(0, ...)` question's boundary and mechanism are now determined (Mission 29, `audits/2026-09-09_os_level_stdin_fd0_forensics.md`), narrowing what a future Mission 30 needs to decide.** Confirmed: one root cause (inherited fd 0), not several; `echo_sandbox.sb`'s broad `/dev` allowance is deliberate and correct, ruling out the Seatbelt layer; the fix belongs in `safe_exec_wrapper.py` (same layer as Mission 28's own fix), operating on the raw descriptor via `os.close(0)` before candidate code runs — evidence-tested (in isolation, not implemented) to produce a genuine `OSError`, unlike a `/dev/null` redirect, which was shown to reproduce Mission 26's already-diagnosed false-success ambiguity at the raw-fd layer. **Newly open, for Mission 30 specifically**: whether `os.close(0)`'s exact behavior holds once actually implemented inside the real `safe_exec_wrapper.py`/Seatbelt chain (only verified in a bare, isolated `os.fork()` this mission — deliberately not implemented in the real sandbox, per Mission 29's own scope limit); whether the eventual Liveness Ledger canary for this should extend `f2_stdin_contract` or be a new sibling check (deferred, since there's no real fix yet for a canary to verify); `termios`/`fcntl`-level descriptor manipulation was not tested and remains a genuinely open, if likely lower-priority, corner of the same raw-fd attack surface.

---

## Q-007 [P3] — Does the "taxonomy laundering" failure mode (R-002's taxonomy-specific instance) generalize beyond the OBSERVED/DERIVED/INFERRED/SPECULATIVE/IMAGINED vocabulary to other structured-classification schemes?

**Why it matters:** if any future mechanism design (including a Git-provenance schema per Mission 18) introduces its own structured classification vocabulary, this question determines whether that vocabulary itself becomes a new attack surface for the same laundering pattern.

**Current evidence:** observed twice, both times with the same specific taxonomy (`audits/2026-09-10_...isolation.md`, and again in the `H_generic_reasoning_control` condition of Mission 15's replication).

**Next discriminating experiment:** not yet designed; exploratory.
