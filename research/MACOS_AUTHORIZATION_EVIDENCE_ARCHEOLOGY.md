# macOS Authentication & Authorization Evidence Archaeology

> **READ-ONLY ARCHAEOLOGY — NOT IMPLEMENTED — NOT AN ARCHITECTURAL REQUIREMENT**

---

## 1. Executive Summary

macOS provides real, inspectable evidence about **account identity** and **process identity** (OBSERVED, directly on this machine) and real, documented guarantees about **local biometric authentication** (DOCUMENTED, via Apple's own API reference). None of this evidence, individually or combined, establishes **authorization for a specific operation by a specific human** — the gap `research/OPOSSUM_MODE_BRAINSTORM.md` Section 6 already named as unsolved remains unsolved after this archaeology, for a precise, now-evidenced reason: every mechanism macOS exposes answers "is the device owner present" or "is this process running as this account," never "did this particular human, right now, authorize this particular FeralEcho action." Authorization, if it is ever built, would still be **application-defined policy layered on top of** OS-provided authentication/identity facts — macOS does not solve it for FeralEcho, it only supplies raw material.

A directly relevant, previously-unknown finding surfaced during local probing: the conda `python3.12` interpreter FeralEcho actually runs under is **ad-hoc code-signed** (no Apple Developer Team ID) — meaning code-signing cannot serve as an identity anchor for FeralEcho's own runtime, only for signed system/vendor binaries like Ollama's.

## 2. Research Question

What authentication, identity, privilege, session, and authorization evidence can an ordinary local FeralEcho process obtain from macOS, and which claims can it legitimately make from that evidence? See Section 12/13 for the direct answer.

## 3. Environment Examined

- Machine: Apple M5 MacBook (Model Identifier `Mac17,3`), macOS 26.5.1 (Build 25F80) — OBSERVED (`sw_vers`, `system_profiler SPiBridgeDataType`).
- Active local user: `richietate`, UID 501, console session open since Jun 23 2026 (82 days uptime at time of probing) — OBSERVED (`id`, `who`, `w`).
- FeralEcho's actual runtime interpreter: `~/miniforge3/envs/feral_echo/bin/python3.12` — OBSERVED (`codesign -dv`).
- No Touch ID authentication event was triggered at any point. No macOS setting, account, permission, Keychain entry, or security configuration was changed. All commands run were read/query-only.

## 4. macOS Authentication Evidence

- `id` / `whoami` / `python3 -c "os.getuid()"` all agree: current process context is UID 501, `richietate` — OBSERVED, self-consistent across three independent tools.
- `w` shows 6 distinct active sessions (one `console`, five `ttys`), all under the same user, some running real long-lived FeralEcho-adjacent processes (`python -m echo_studio.main`, two `caffeinate` invocations) — OBSERVED. This directly establishes that **multiple concurrent local sessions under one account is the real, current, everyday condition on this machine**, not a hypothetical — any authorization design must handle "which of six sessions counted as the authorizing one" as a real case, not an edge case.
- `launchctl print gui/501` — OBSERVED — confirms a real, OS-managed per-user GUI session (`type = login`, `security context: { uid = 501, asid = 100026 }`), created by `loginwindow` running as `creator euid = 0` (root). This is a real, OS-internal trust boundary: the login session's own creation is root-mediated, not something any ordinary user-level process (including FeralEcho) could forge from inside a normal session.

## 5. Touch ID Evidence Boundary

- `bioutil -r -s` — OBSERVED, read-only, does not trigger authentication — reports real configuration: Touch ID enabled for unlock, biometric timeout 172800s (48h), match timeout 14400s (4h). This establishes **configuration state**, not an authentication **event**.
- `LocalAuthentication.framework` and `Security.framework` are present on disk, and Python (via PyObjC) can successfully `import LocalAuthentication` — OBSERVED, import-only, no policy evaluation call made. This establishes that **the API is reachable from a Python process** — not that FeralEcho currently uses it, and not what happens if it did.
- **DOCUMENTED** (Apple Developer Documentation, `developer.apple.com/documentation/localauthentication/lacontext` and related `LAPolicy` pages, consulted via WebSearch): `LAContext.evaluatePolicy(_:localizedReason:reply:)` returns an asynchronous boolean success/failure plus an error object. The relevant policies are named `deviceOwnerAuthentication` / `deviceOwnerAuthenticationWithBiometrics` — Apple's own naming and documentation describe this as verifying **the device owner**, not a specific named individual selected from among possibly multiple enrolled fingerprints. The API's return value is a pass/fail signal plus (optionally) an opaque `evaluatedPolicyDomainState` token for detecting *changes* to enrolled biometrics between calls — it does not return "which enrolled print matched" or any identity claim beyond "some enrolled credential succeeded."
- **INFERRED from the above**: successful Touch ID establishes "a credential enrolled on this device, recognized by the Secure Enclave, was presented and matched" — it does **not** establish which of potentially several enrolled fingerprints matched, does not establish that the presenter is the account's usual human operator specifically (as opposed to any other person whose print happens to be enrolled), and does not establish anything about which *operation* the presenter intends to authorize, since Touch ID success is not operation-scoped by the OS — that scoping, if any, is entirely up to whatever application requested the check.
- **NOT TESTABLE SAFELY**: whether a successful Touch ID event is independently timestamped/logged anywhere a separate process (not the requesting app) could read — this would require either triggering a real authentication event or reading system audit/log subsystems in a way not clearly distinguishable from probing security-log internals; deliberately not attempted, left UNKNOWN rather than guessed.
- **Distinguishing the two framings the mission requires**: "macOS can perform this authentication" is OBSERVED true (the framework is present and callable). "FeralEcho can independently verify that this authentication occurred" is **UNKNOWN** — no safe local probe in this pass established a way for a *second*, independent process to corroborate a *first* process's LAContext success without itself either being the one performing the check (collapsing back to self-report) or reading system-level logs whose accessibility/safety was not established here.

## 6. Session/User Identity

Evidence source → observation → interpretation → limitation, per the mission's required style:

- OS reports UID 501, username `richietate`, real console session open 82 days
  → the current process (and, by the same mechanism, FeralEcho's own process) executes under this account
  → this establishes **account context**
  → does NOT establish that a specific human is physically present or currently attentive; a session left open for 82 days is exactly the case where "account is active" and "a human is at the keyboard right now" have long since diverged.
- `launchctl print gui/501` reports a real, root-created login session
  → the session's *creation* is OS/root-mediated, not user-process-forgeable
  → this establishes the session object itself has a trustworthy origin
  → does NOT establish that everything happening inside that session, hours or days later, is still attributable to the original login event.
- `w` shows six concurrent sessions under one account
  → multiple terminals/processes share one account context simultaneously
  → establishes that "the account is active" is compatible with many different concurrent activities, not one
  → does NOT let FeralEcho, from inside any one session, determine what is happening in the others without separately inspecting them.

Username == human identity is explicitly not assumed anywhere above, per the mission's own instruction — every claim above is scoped to *account* and *session*, never to a specific person.

## 7. Process/Privilege Identity

- Real, OBSERVED: `python3.12`'s own UID/EUID (501/501, matching the login account) via direct `os.getuid()`/`os.geteuid()` call.
- Real, OBSERVED, and the most consequential finding of this section: `codesign -dv` on the actual conda interpreter FeralEcho runs under shows `Signature=adhoc`, `TeamIdentifier=not set` — **this binary has no cryptographic identity chain back to any developer or vendor.** An adhoc signature only certifies "this exact binary's contents match the hash computed when it was adhoc-signed on this machine" — it provides zero information about *who* built or shipped it.
- By contrast, `codesign -dv` on the installed Ollama binary shows a real Developer Team ID (`3MU9H2V9Y9`), a real signing timestamp, and the hardened-runtime flag — OBSERVED, a genuine, meaningful contrast: **some of FeralEcho's dependencies have verifiable publisher identity; FeralEcho's own interpreter does not.**
- **INFERRED**: this means code-signing cannot serve as an identity/integrity anchor for *FeralEcho's own process* in any future design — only for specific, separately-vetted signed dependencies it calls out to. Any claim like "this process is verifiably the real FeralEcho" would need to rest on something else (e.g., this session's own `working_tree_file_identity()`/`runtime_process_identity_and_self_report()` file-hash and PID-based evidence, Section 15) rather than code-signing.
- `/var/db/auth.db` (the real, on-disk Authorization Services policy database) exists — OBSERVED via `ls -la` — but is owned `root:wheel`, mode `600` (owner-read/write only). **A FeralEcho process running as UID 501 cannot read this file at all.** This is a real, concrete, previously-unstated limitation: whatever authorization-policy evaluation the OS itself might do via Authorization Services happens in a privilege tier FeralEcho's own process cannot inspect directly — it could, at most, ask the OS to evaluate a right and receive a pass/fail answer, never audit the policy database itself.
- **"I am running as user X" vs. "user X authorized this particular action"**: no local evidence source found in this pass bridges this gap. UID/session facts establish the former unconditionally; nothing examined establishes the latter for any *specific* action without either (a) the app itself defining and enforcing that scoping (Section 8's finding, restated), or (b) a real-time, operation-scoped confirmation mechanism (e.g., a fresh LocalAuthentication prompt worded for the specific action) that this project has never built and this mission did not test.

## 8. Authorization Mechanisms

- **DOCUMENTED**: Apple's Authorization Services framework (`AuthorizationServices.framework`, part of `Security.framework`) provides `AuthorizationRef`/rights-based evaluation for privileged operations (the mechanism behind macOS's "Click the lock to make changes" system-preference prompts) — this is a real, distinct API from LocalAuthentication, oriented around *rights* (named strings an app defines, like `com.example.myapp.right`) evaluated against policy in `/var/db/auth.db`, which can require password, biometrics, or admin-group membership depending on how the right is configured.
- **INFERRED, not independently confirmed by invocation** (invoking it was out of scope/unsafe for this pass): the policy behind any given right is still something the *calling application* defines when it registers the right — the OS provides the *evaluation mechanism and secure prompt UI*, not the *policy content*. This directly answers Section 5 of the mission ("do not assume macOS solves application-level authorization automatically") — it does not; it provides infrastructure an application could build authorization on top of, at real integration cost (a right must be registered, typically via a signed helper tool or `EvaluateAndUpdateRights`-style call this project has never used), not a ready-made "is this person allowed to do Y" answer.
- Available to ordinary/unprivileged/command-line/Python/Flask-server processes in principle (Authorization Services is a standard framework, not gated to app-store or entitled apps) — **DOCUMENTED** existence, **NOT TESTABLE SAFELY / UNKNOWN** in this pass whether it behaves identically for a bare Python/Flask process versus a properly bundled, signed macOS `.app` — Apple's own documentation and developer-forum discussion (not independently re-verified here beyond the search summary) suggests some Authorization Services flows assume an app bundle/helper-tool structure this project does not currently have.

## 9. Independent Verification Levels

Every evidence source discussed above, classified per the mission's L0-L3 scale:

| Evidence | Level | Why |
|---|---|---|
| `os.getuid()`/`os.geteuid()` read by FeralEcho itself | **L1** | Local OS observation, but only as good as trusting the OS call itself hasn't been intercepted inside a compromised process (Section 11, Case H) |
| `who`/`w`/`launchctl print gui/<uid>` | **L1-L2** | Reports OS-maintained session state; genuinely independent of FeralEcho's own process state (a compromised Echo process can't rewrite `launchd`'s session table), but still trusts the OS layer generally |
| `codesign -dv` on a *third-party* signed binary (e.g. Ollama) | **L2, bounded** | Independently checkable against Apple's own trust chain — but only tells you about *that binary*, not about FeralEcho or about who is currently operating it |
| `codesign -dv` on FeralEcho's own interpreter | **N/A** | Adhoc-signed — provides no identity chain to verify against at all; not usable as evidence of anything beyond "unchanged since last adhoc-sign" |
| LocalAuthentication (`LAContext`) success/failure | **L1** | A local OS observation reported back to the *same requesting process* — nothing found in this pass promotes this to L2 (independently corroborated by a second process) or L3 (externally/cryptographically anchored beyond the device's own Secure Enclave) |
| Authorization Services rights evaluation | **L1-L2, theoretical** | Would be OS-mediated (like LocalAuthentication) but policy-checkable via `/var/db/auth.db` in principle — except that file is unreadable to FeralEcho's own UID (Section 7), so even the "L2, a second mechanism could check the same policy" possibility is closed off in practice for an ordinary unprivileged process |
| `/var/db/auth.db` contents | **Unreachable** | Exists, confirmed by `ls`, but permission-denied to FeralEcho's real UID — cannot be used as evidence by FeralEcho at all, only described as existing |
| Echo's own claim "I verified the operator" | **L0** | By definition, unless built explicitly on one of the above and disclosed as such |

**No L3 evidence source (cryptographically or externally anchored beyond this single machine's own Secure Enclave/OS) was found anywhere in this pass.** Everything traces back, at best, to trusting this one Mac's own OS and Secure Enclave — consistent with `OPOSSUM_MODE_BRAINSTORM.md`'s own finding that this project has no existing trust anchor external to the local machine.

## 10. Threat Model

- **A — legitimate authenticated operator**: real evidence available (Sections 4/6) — account/session/UID all consistent. Strongest case, and still only establishes account context, not moment-to-moment intent.
- **B — someone else has physical access to an already-unlocked machine**: **no evidence source found in this entire pass distinguishes this from Case A.** UID, session, and console-user facts are all identical whether the account's usual owner or a different person with physical access is the one actually typing. This is a real, structural gap, not a minor caveat.
- **C — Touch ID succeeds**: establishes "the device owner's enrolled biometric matched" (Section 5) — not which enrolled print, not that this specific action was the one intended, not anything beyond that single pass/fail moment.
- **D — password succeeds**: comparable evidentiary strength to C at the "device owner authenticated" level (`deviceOwnerAuthentication` covers both paths per Apple's own documented policy naming) — a password additionally proves knowledge of a secret rather than possession of a biometric trait, a different but not obviously stronger guarantee for FeralEcho's purposes, since both ultimately reduce to the same OS-level pass/fail signal to the requesting app.
- **E — remote/local automation**: this project's own real, existing pattern (`GREMLIN_SECRET`-gated endpoints, per `CLAUDE.md`'s documented history) is a real answer here, but it is an **application-level shared secret**, not anything macOS itself provides — nothing in this archaeology found an OS-level mechanism that would improve on "the caller presented the configured secret."
- **F — privilege boundary, a differently-privileged process interacts with Echo**: OBSERVED that UID/GID differences are directly, cheaply checkable (`id`, `ps -o uid,user`) — this is real, usable L1 evidence, unlike most of the authorization questions above.
- **G — compromised user session**: every piece of L1 evidence in Section 9 degrades together under this threat model, since all of it ultimately trusts "the OS layer is honest," which a compromised session (not necessarily a compromised OS kernel) doesn't automatically invalidate — but a compromised session *could* include a keylogger or automation tool presenting real, valid Touch ID/password prompts on the real user's behalf without the real user's actual intent, which no evidence source examined here would distinguish from a genuine action.
- **H — compromised FeralEcho process itself**: the single most important case per the mission's own framing. **Nothing examined in this pass would remain trustworthy if Echo's own process is the thing that's compromised**, because every evidence source Echo itself would read (`os.getuid()`, an `LAContext` call, a file read) is read *by that same process* — a compromised process can simply lie about what it read, or patch the functions that would do the reading (directly analogous to this session's own real, already-documented finding that a compromised/malicious in-process actor can monkeypatch Python-level checks). The only evidence in this whole document that does **not** depend on trusting the Echo process itself is OS-session-table state read by a genuinely separate process/tool (`who`, `launchctl`) — and even that requires trusting whatever separate tool does the reading wasn't also compromised.

## 11. Adversarial Findings

Working through the mission's own attack list plainly:

- **Could Echo accidentally treat "the Mac is unlocked" as "the operator is authorized"?** Yes, easily, and this is the single most likely real design mistake — "unlocked" and "the legitimate operator is present and intends this action" are shown above (Case B, Section 10) to be genuinely indistinguishable from any evidence this pass found.
- **Could Echo treat "Touch ID succeeded" as "this specific human authorized this specific operation"?** Yes, and Section 5's documentation review shows this is *not* what the API establishes — it establishes device-owner-credential match, not operation-specific intent, unless the calling application itself constructs and enforces that binding (which macOS does not do automatically).
- **Could malware inside the user's session create a false authorization signal?** Yes — anything running with the user's own privileges can present real, valid OS-level facts (real UID, even a real successful LocalAuthentication call if it can get the real user to physically touch the sensor, e.g. via a disguised prompt) without the user's genuine intent for the specific downstream action.
- **Could a compromised Echo process forge its own authorization evidence?** Yes, directly — see Case H, Section 10. This is not a remote risk; it's the default state of any self-reported check.
- **Could stale authentication evidence survive longer than it should?** Yes, and this is *documented*, not speculative: `bioutil -r -s` reported a real 48-hour biometric timeout and a real 4-hour match timeout on this machine — any design caching "Touch ID succeeded at time T" for use later needs to reason explicitly about these real, configured windows, not assume authentication is instantaneous-only.
- **Could authorization become invalid while Echo still believes it is valid?** Yes — e.g., the account could be logged out, the session ended, or the physical operator could change, all without any push notification to a process that cached an earlier "authorized" belief and never re-checked.
- **Could an attacker manipulate the interface between macOS and Echo?** Yes, in principle, at multiple layers this pass did not attempt to test (process injection, `LD_PRELOAD`-style interception is less applicable on macOS but analogous techniques exist, XPC message spoofing) — flagged as UNKNOWN/NOT TESTABLE SAFELY rather than dismissed.
- **Could a legitimate authentication event be replayed conceptually as authorization for a different operation?** Yes — since the OS-level signal is a bare pass/fail with no operation-scoping baked in by macOS itself (Section 5), any binding between "this Touch ID success" and "this specific action" is entirely the application's own responsibility to construct, and a naive design (check-once, trust-forever within some window) would be exactly this replay risk.
- **What claims remain impossible for Echo to establish, full stop, with anything found in this pass?** Two, stated precisely: (1) **that a specific named human, rather than any person with physical/session access, is the one currently acting** — every mechanism examined authenticates *the device/account*, never *the individual* beyond "an enrolled credential for this account matched"; (2) **that Echo's own process has not itself been compromised while performing any of these checks** — every L1 evidence source in Section 9 is read by the very process whose trustworthiness would be in question during Case H.

## 12. What Echo Could Legitimately Claim

Grounded strictly in what was OBSERVED or DOCUMENTED above, never INFERRED beyond what the evidence supports:

- "I am currently running as account `richietate` (UID 501)" — OBSERVED, directly, cheaply, repeatedly checkable.
- "A login session for this account exists and was created by the OS login mechanism, not by an ordinary user process" — OBSERVED via `launchctl print`.
- "A third-party dependency's binary (e.g. Ollama) carries a verifiable publisher signature; my own interpreter does not" — OBSERVED via `codesign`, a genuinely useful negative-and-positive finding pair.
- "A local biometric or passcode check, if I request one, will report pass/fail for *some* enrolled device-owner credential" — DOCUMENTED (Apple's own API reference).
- "I cannot read the system Authorization Services policy database directly" — OBSERVED (permission denied by file mode).

## 13. What Echo Could NOT Legitimately Claim

- "The current physical operator is definitely [specific named person]" — no mechanism examined establishes this; only account/credential-match facts are available.
- "A Touch ID/password success means this specific operator authorized this specific FeralEcho action" — not what the OS-level signal means (Section 5); would require the application to construct and enforce that binding itself, and this project has no such mechanism today.
- "I have verified my own process has not been compromised" — structurally impossible for a process to establish about itself using only evidence that process itself reads (Case H, Section 10) — this would require an external, independent observer, which is exactly this session's own already-established `provenance_check.py` design principle (a reconciliation of two *independent* observations, never a single process's self-report).
- "Successful authorization now guarantees continued authorization later" — real, documented timeout windows exist (Section 11) but nothing examined enforces per-operation freshness automatically; that would again be an application-level responsibility, unbuilt today.

## 14. Relationship to Opossum Mode

Answering the narrow question the mission poses directly: **the evidence boundary remains too weak to make a full authorization-aware Opossum Mode technically defensible today**, for a precise reason grounded in this archaeology rather than in the prior brainstorm's more general concern: every macOS-provided signal examined answers a *device/account/credential-match* question, and Opossum Mode's actual open problem (Section 6 of the brainstorm) is an *operator-intent-for-this-specific-action* question. macOS narrows the search space usefully (it rules out "no one authenticated at all" and "wrong account entirely") but does not close the gap the brainstorm identified as the hard one.

Distinguishing the concepts the mission asks not to merge: **authentication** (device-owner credential match — real, available) is not **identity** (which specific human — not available beyond account-level), is not **authorization** (permission for a specific action — not provided by macOS automatically, would be application policy), is not **trust** (a broader, ongoing judgment — no mechanism here provides this at all), is not **operator legitimacy** (whether this account *should* be doing this — purely application-defined), is not **action-specific permission** (scoped consent for one particular operation — the piece most conspicuously absent from every mechanism examined).

This does not strengthen the case for building any part of Opossum Mode now. If anything, it sharpens *why* the brainstorm's Section 18 Open Question #1 (can an authorization mechanism be built that is independently, adversarially testable) remains unanswered: macOS supplies real L1 evidence, but nothing that reaches L2/L3 independence for the one claim (operator-intent-for-this-action) that would actually matter.

## 15. Relationship to Existing FeralEcho Provenance Architecture

The `evidence → provenance → reconciliation → interpretation` pattern (`app/core/provenance_check.py`, built this session) is directly, structurally compatible with the evidence categories found here — but the fit is partial, not complete, and forcing it further than the evidence supports would repeat exactly the mistake that architecture was built to prevent:

- macOS account/session facts (Section 6) are exactly evidence-shaped — a `working_tree_file_identity()`-style primitive could, in principle, wrap `os.getuid()`/`launchctl`-class reads the same disciplined way (return facts, never a verdict).
- A hypothetical "was Touch ID recently satisfied" check would fit the same pattern *as one input* — but Section 9's finding that it stays L1 (self-reported by the requesting process, never independently corroborated) means a reconciliation step built on it would have only one witness, not two — and this project's own reconciliation primitive (`reconcile_process_and_selfreport()`) was specifically designed around comparing *independent* observations. A single-witness "reconciliation" would be reconciliation in name only.
- The Liveness Ledger's discipline (ground-truth, adversarially tested) is the right template for *building* any future authorization-adjacent check — but Section 9's L0-L3 findings show there is currently no L2+ macOS-provided fact to build such a check *on top of* for the operator-intent question specifically. The ledger pattern is ready; the raw material it would need is not.
- No fit is forced where none exists: Authorization Services' rights/policy database (Section 8) is real but currently unreachable to FeralEcho's own process (Section 7) — this is flagged as a genuine architectural gap, not glossed over as "solved in principle."

## 16. Open Questions

1. Could a second, genuinely separate local process (not FeralEcho itself) be built to independently observe and log LocalAuthentication events, providing the L2 corroboration Section 9 found missing — and would that require privileges/entitlements this project does not currently have? UNKNOWN, not tested.
2. What, exactly, would it take for an ordinary Python/Flask process (not a signed, bundled `.app`) to register and evaluate an Authorization Services right — is this genuinely reachable, or does it require an app-bundle/helper-tool structure this project would need to build first? UNKNOWN, DOCUMENTED-level research only in this pass.
3. Is there any macOS-native mechanism (beyond what was found here) that binds a single authentication event to a single, specific, application-defined action rather than a bare pass/fail — e.g., anything in newer Authorization Services APIs (the WWDC22 "Streamline local authorization flows" session was surfaced by search but not reviewed in depth here)? Worth a dedicated follow-up.
4. Would giving FeralEcho's own interpreter a real, non-adhoc code signature change anything material for identity-anchoring purposes, or is this a dead end given FeralEcho is not distributed/notarized software? Worth a cheap, separate cost/benefit look.
5. Does this project's own existing `GREMLIN_SECRET` shared-secret pattern already represent the practically-achievable ceiling for this problem on a single-user home-lab machine, making further macOS-API investment a poor use of effort relative to its real payoff?

## 17. Recommendation

Do not pursue building any authorization-aware Opossum Mode component on the strength of this archaeology. The evidence found here narrows the problem (rules out "no OS-level signal exists at all") without solving it (the operator-intent-for-this-action gap remains open, and the one system-level mechanism that might address it — Authorization Services — is unreachable to FeralEcho's own process as currently structured). This is a genuine, if partial, negative result, and per this project's own standing research discipline, that is a legitimate and useful outcome, not a failed mission.

## 18. Exact commands/tools/API documentation inspected

Local (all read-only, none modified system/account/security state): `sw_vers`; `id`; `whoami`; `who`; `w`; `stat -f "%Su" /dev/console`; `python3 -c "os.getuid()/os.geteuid()/getpass.getuser()"`; `launchctl print gui/$(id -u)`; `bioutil -r -s`; `ls -d` on `LocalAuthentication.framework`/`Security.framework`; `python3 -c "import LocalAuthentication"` (import only, no policy evaluation call); `security list-keychains` (path listing only, no secret read); `system_profiler SPiBridgeDataType`; `codesign -dv` on the live conda `python3.12` and on `/Applications/Ollama.app`'s binary; `ls -la /var/db/auth.db`; `ioreg -n IOHIDSystem` (idle-time field only); `csrutil status`.

External (via WebSearch, restricted to `developer.apple.com`): Apple Developer Documentation for `LAContext`, `evaluatePolicy(_:localizedReason:reply:)`, `evaluatedPolicyDomainState`, `canEvaluatePolicy:error:`, `LAPolicy.deviceOwnerAuthentication`, `LAPolicy.deviceOwnerAuthenticationWithBiometrics`, and the WWDC22 "Streamline local authorization flows" session listing (title/existence surfaced, not deep-reviewed). Authorization Services framework facts in Section 8 beyond framework existence are DOCUMENTED-via-search-summary and INFERRED, not independently re-verified against primary API reference pages in this pass — flagged accordingly rather than overstated.

## 19. Repository Impact

- Path count before: 133 (`git status --short`). Path count after: 134 — exactly one new untracked file.
- HEAD before: `2fba42644c82b9f7096276f4dd338d615cf1bcce`. HEAD after: unchanged (no commit made).
- Modified files: none. Staged files: none. Commits created: none. Pushes performed: none.
- The live FeralEcho server process was not inspected, signaled, restarted, or otherwise touched at any point in this mission.
- Touch ID was never triggered. No macOS account, permission, Keychain entry, security setting, launch agent/daemon, or configuration was changed at any point — every command run was a read/query form only.

---

### AUTHORIZATION EVIDENCE VERDICT

**B — Partial.** macOS provides real, independently-inspectable authentication and account/session identity evidence (Sections 4, 6, 9) — genuinely useful, genuinely L1-and-occasionally-L2. But the specific claim any future authorization-aware Opossum behavior would actually need — that a particular human authorized a particular action, corroborated independently of FeralEcho's own process — remains application-level, largely L0/L1-only, and in the one case where the OS provides a real policy-evaluation mechanism for exactly this (Authorization Services), that mechanism's own policy database is currently unreachable to FeralEcho's process (Section 7). Not C (Insufficient) because real, usable L1/L2 evidence genuinely exists and narrows the problem meaningfully. Not A (Promising) because the specific hard question from the Opossum brainstorm is not shown to be tractable by anything found here.

**The single most important research question that would have to succeed before FeralEcho should ever implement authorization-aware Opossum behavior:** *Can a second, genuinely independent local mechanism (not FeralEcho's own process) corroborate an authentication/authorization event — closing the L1→L2 gap found throughout Section 9 — without requiring privileges or an application structure (signed bundle, helper tool) this project does not have and would need to newly build?* Everything else in this document is narrowing and framing; this is the one open question whose answer would actually change whether the broader concept is worth designing at all.
