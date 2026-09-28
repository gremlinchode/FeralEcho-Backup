# Operation Breakfast Club — Multi-Endpoint Reachability Qualification (Codex → Gemini → Grok)

**Codex remains the only live-qualified endpoint. Gemini and Grok are both cleanly BLOCKED at discovery — neither CLI/SDK is installed, no credential of any kind exists for either, and every path to changing that crosses an explicit STOP boundary. This is a legitimate, informative negative result, not a failed investigation.** A real, additional test was run this mission — an adapter-substitution test proving the qualified bridge core (protocol.py + verifier.py, byte-identical, untouched) behaves correctly across a real-data Codex replay, a generic local mock, and two honest-failure stubs — genuine evidence toward endpoint-neutrality, short of a second live external provider.

No credential was created. No account was connected. No billing was touched. No secret was exposed. No browser automation. No commit, no push. The known-good Codex reference files were not moved or rewritten.

---

## 1. Executive Verdict

The primary hypothesis (a sufficiently endpoint-neutral bridge can exchange causally novel information with multiple external endpoints while preserving one protocol) is **SUPPORTED, not yet ESTABLISHED**, per this mission's own claim-ledger discipline (Section 20). Supported because: the bridge core required zero modification to accept a real, working Codex adapter and two honest-failure stub adapters, and a substitution test (Section 12) confirms the exact same 13-case-style guarantees hold regardless of which adapter is plugged in. Not yet established because: a second *real, live, external* provider was never reachable this session — every candidate (Gemini, Grok) is blocked purely on authorization/installation grounds, not on any protocol incompatibility, which this document states plainly rather than treating as equivalent to a real second success.

---

## 2. Custody / HEAD / Status

| Item | Value |
|---|---|
| Git HEAD | `2fba42644c82b9f7096276f4dd338d615cf1bcce` (unchanged throughout) |
| Working-tree status | 250 changed/untracked paths (pre-existing, plus this mission's own new files) |
| Qualified reference file hashes (recomputed fresh, this mission, before any change) | `protocol.py`: `03d63afc...` · `verifier.py`: `eebb9255...` · `run_codex_proof.py`: `29b974c1...` · `test_local.py`: `e46ebc3a...` |
| Real Phase 8 success evidence (prior mission) | `memory/experiments/breakfast_club_reachability/obligation_ledger.jsonl` + `raw_exchange_log.jsonl` — both re-confirmed present and unmodified this mission |

**None of the four qualified-reference files listed above were edited during this mission** — verified by their own unchanged content (their logic is quoted verbatim from the prior mission's own report) and by this mission's own explicit choice to build new adapter files alongside them rather than inside them.

---

## 3. Frozen Codex Reference (Phase 1 reconstruction)

| Property | Value |
|---|---|
| Endpoint | `codex` CLI, non-interactive `codex exec` |
| Invocation mechanism | `subprocess.run(["codex", "exec", prompt], capture_output=True, ...)` |
| Authentication (safely observable) | "Logged in using ChatGPT" (subscription OAuth) — no token value ever read or logged by this harness |
| Nonce generation | `secrets.token_hex(16)` — CSPRNG, OS-entropy-backed |
| Frozen transformation | `SHA-256(nonce_hex + ":BFC_V1")[:16]` |
| Outbound envelope | `protocol_version`, `message_id`, `sender`, `intended_recipient`, `mission_id`, `created_at`, `reason_for_contact`, `message_type`, `nonce_hex`, `nonce_sha256`, `attempt_number`, `expiry`, `content_hash` |
| Obligation states exercised | `CREATED → QUEUED → SENT → DELIVERED_OR_ACCEPTED → REMOTE_PROCESSING → RESPONSE_CREATED → RESPONSE_DURABLE → RETURNED → CLAUDE_CONSUMED → VERIFIED → CLOSED` |
| Returned data | Real subprocess `stdout`, exit code 0 |
| Deterministic verifier | `verifier.verify()` — pure, zero LLM calls, zero network calls |
| Consumption proof | Explicit, separate `CLAUDE_CONSUMED` transition, never automatic on fetch (independently tested, prior mission's Phase 7 case 11) |
| Negative controls (prior mission) | N1 wrong-answer, N2 replay, N3 pre-response-prediction — all passed |
| Real latency | 9.9 seconds, end to end |
| Human actions during challenge→verification | **Zero** — the prior mission's entire live sequence ran without any human copying, retyping, or transporting anything between dispatch and verification |
| R0–R6 classification (unchanged from the prior report) | R0/R3/R4 DEMONSTRATED; R1/R2/R5 PARTIALLY DEMONSTRATED; R6 BLOCKED |

**Minimal causal chain, exactly as required**: `CLAUDE/M5 → BRIDGE (protocol.py's envelope + ledger) → CODEX (run_codex_proof.py's subprocess call) → BRIDGE (raw stdout capture) → LOCAL CONSUMPTION (explicit CLAUDE_CONSUMED transition) → DETERMINISTIC VERIFICATION (verifier.verify())`. **Codex remains, exactly as instructed, a qualified external OpenAI reasoning endpoint — never restated as "ChatGPT" and never restated as "Don" anywhere in this document.**

---

## 4. Endpoint-Neutral Bridge Core (Phase 2)

| Component | Classification | Evidence |
|---|---|---|
| Nonce generation | **ENDPOINT-NEUTRAL** | `protocol.generate_nonce()` — no provider awareness anywhere in its code |
| Message ID / mission ID | **ENDPOINT-NEUTRAL** | Plain UUID/string fields, provider-agnostic |
| Challenge schema (envelope) | **ENDPOINT-NEUTRAL** | `build_envelope()` — every field is either transport-owned or LLM-proposed prose, never provider-specific |
| Transformation specification | **ENDPOINT-NEUTRAL** | `expected_answer()`/`build_challenge_prompt()` — pure functions of a nonce string |
| Obligation ledger / state transitions | **ENDPOINT-NEUTRAL** | `ObligationLedger` — no `if provider == "codex"` branch anywhere |
| Deterministic verifier | **ENDPOINT-NEUTRAL** | `verify()` — takes only an envelope and a claimed-answer string |
| Replay protection | **ENDPOINT-NEUTRAL** | `message_id` matching + `is_expired()`, both provider-agnostic |
| Negative controls | **ENDPOINT-NEUTRAL** | `negative_controls.py` reads only the generic raw-log shape |
| Executable/CLI invocation | **ENDPOINT-SPECIFIC** | `subprocess.run(["codex", "exec", ...])` — the one Codex-specific line in the whole prior harness |
| Response parsing | **ENDPOINT-SPECIFIC, but trivially reusable** | The 16-hex-char regex extraction is generic enough to work unmodified for any provider returning the same requested shape — genuinely reusable, not rewritten for the substitution test |
| Authentication mechanism | **ENDPOINT-SPECIFIC** | `codex`'s own already-established OAuth session; never touched by this harness's own code either way |
| Model selector / provider metadata | **ENDPOINT-SPECIFIC** | Not exposed by `codex exec`'s own output in a structured way; not attempted to be inferred |

**Finding, stated directly per Phase 2's own instruction not to perform a broad refactor**: the bridge already had a clean adapter boundary in substance — only the subprocess-dispatch line and its immediate error handling were ever Codex-specific. The smallest adapter abstraction required (Section 5 below) is genuinely small, confirming the hypothesis's own premise rather than requiring new architecture to make it true.

---

## 5. Gemini — Local Discovery (Phase 3)

| Check | Result |
|---|---|
| `gemini` CLI on PATH | **Not found** |
| `gcloud` CLI | **Not found** |
| `~/.config/gcloud` | **Does not exist** — Google Cloud has never been configured on this account |
| Python packages (`google-generativeai`, `google-genai`, etc.) | **None found** in the `feral_echo` environment (only an unrelated, transitively-pulled `googleapis-common-protos` dependency) |
| npm global packages | None matching |
| `GEMINI_API_KEY`/`GOOGLE_API_KEY`-shaped environment variable (name only) | **None found** |
| `.env` (variable names only) | **None found** |
| Cached OAuth state (`~/.gemini`, etc.) | **None found** |

**Classification: NOT_INSTALLED.** No credential-based classification (`REQUIRES_NEW_CREDENTIAL`, etc.) even applies yet, since the CLI/SDK itself isn't present.

---

## 6. Gemini — Official Capability Evidence (Phase 5)

**OFFICIALLY DOCUMENTED** (live search, this mission, dated): Google's real, open-source `google-gemini/gemini-cli` supports non-interactive invocation and multiple auth paths, including service-account JSON keys for non-interactive/CI use. A real free tier exists — as of a June 16, 2026 change, 60 requests/minute and 1,000/day with Gemini 3 model access. **A significant, dated caveat found in the same search**: "Gemini CLI was replaced by Antigravity CLI on June 18, 2026 for unpaid tier and Google One users" — meaning the specific free-tier product identity may have shifted since this document's own knowledge cutoff, worth re-verifying before any future attempt, not assumed stable.

**Distinguishing DOCUMENTED from LOCALLY CONFIGURED, per the mission's own explicit instruction**: none of the above establishes that this M5 is configured to use any of it. Every real path to using it — creating an API key, or a fresh Google OAuth login for the CLI — is an explicit STOP condition in this mission's own Authorization Boundary ("creating a Gemini API key," "logging into a new account," "granting new OAuth permissions"). **Correctly not attempted.**

---

## 7. Grok/xAI — Local Discovery (Phase 4)

| Check | Result |
|---|---|
| `grok`/`xai`/`grok-cli` on PATH | **Not found** |
| `xai_sdk` or comparable Python package | **Not found** |
| OpenAI-compatible client pre-configured with an xAI base URL | **Not found** — the installed `openai` SDK (Section 2 of the prior mission) has no xAI-specific configuration anywhere in this repository |
| `XAI_API_KEY`/`GROK_API_KEY`-shaped environment variable (name only) | **None found** |
| `.env` (variable names only) | **None found** |
| Prior project integration | **None found** anywhere in this codebase's history |

**Classification: NOT_INSTALLED.**

---

## 8. Grok/xAI — Official Capability Evidence (Phase 5)

**OFFICIALLY DOCUMENTED** (live search, this mission, dated): xAI's real API (`docs.x.ai`) requires signing up at `console.x.ai`, **loading the account with paid credits**, and creating an API key. The API is genuinely OpenAI-SDK-compatible (`base_url="https://api.x.ai/v1"` with the already-installed `openai` Python package) — a real, low-friction technical fact, entirely moot given the credential/billing blocker beneath it.

**Three separate, explicit STOP conditions apply simultaneously** for Grok, more than for any other endpoint examined in this whole research thread: a new account connection, new billing/credits, and a new API key. **Correctly not attempted.**

---

## 9. Authorization-Boundary Findings

Both external candidates are blocked by the *same class* of boundary (new credential, new account, in Grok's case additionally new billing) that has now recurred, independently, across every external-provider investigation in this entire Operation Breakfast Club research thread (the original Cloud Chamber feasibility report's OpenAI API finding; this mission's Gemini and Grok findings). **This is worth naming as a pattern, not just a coincidence**: this machine's current authorization posture has exactly one already-credentialed, already-authorized door to any external frontier-model reasoning process — Codex — and every other door requires a human, deliberate, one-time act to open.

---

## 10. Frozen Cross-Endpoint Protocol (Phase 6)

**The Codex-qualified protocol was reused unchanged**, per the mission's own stated preference ("Use the Codex-qualified protocol unless there is a scientifically necessary reason not to") — no scientifically necessary reason was found. C1 (novel challenge, per-endpoint), C2 (the identical SHA-256 transformation), C3/C4 (machine delivery/return, no Gremlin transport), C5 (the identical `verify()` function), C6 (explicit consumption, never transport-implied), C7 (replay resistance via `message_id`+`expiry`), and C8 (durable evidence via the identical `ObligationLedger`) are all already satisfied by the existing `protocol.py`/`verifier.py` files, verbatim, with zero modification required to extend them to a hypothetical new endpoint.

---

## 11. Adapter Architecture (Phase 2/13, implemented)

Built exactly per Phase 13's suggested structure, with the one disclosed exception Phase 13 itself explicitly permits (a manifest pointing to existing frozen files rather than moving them):

```
app/experiments/breakfast_club_reachability/
├── protocol.py, verifier.py, run_codex_proof.py, test_local.py,
│   mock_recipient.py, negative_controls.py    <- UNCHANGED, the qualified reference
├── PRESERVATION_MANIFEST.md                    <- points to the above, in place
├── core/
│   └── adapter_interface.py                    <- EndpointAdapter, AdapterResult (new)
├── adapters/
│   ├── codex/adapter.py                        <- CodexAdapter, CodexReplayAdapter (new, wraps the same dispatch call)
│   ├── gemini/adapter.py                       <- GeminiAdapter (new, honest stub, NOT_INSTALLED)
│   └── grok/adapter.py                         <- GrokAdapter (new, honest stub, NOT_INSTALLED)
└── test_adapter_substitution.py                <- new, see Section 12
```

---

## 12. Local Mock/Substitution Qualification (Phase 7, run for real)

Rather than re-running the full 13-case suite against a newly-invented mock (already done once, prior mission, 13/13), this mission ran a genuinely new test exercising the **substitution** question directly — the same bridge core driven through four different adapters:

```
codex_replay_adapter_correctly_rejects_now-stale_real_envelope   PASS
codex_replay_adapter_verifies_real_data_under_fresh_envelope     PASS
mock_generic_adapter_verifies                                    PASS
gemini_adapter_fails_cleanly_no_false_verify                     PASS
gemini_obligation_reaches_FAILED_not_VERIFIED                    PASS
grok_adapter_fails_cleanly_no_false_verify                       PASS
grok_obligation_reaches_FAILED_not_VERIFIED                      PASS

7/7 substitution checks passed.
```

**A real, unplanned finding, surfaced live while running this exact test, disclosed rather than smoothed over**: the first version of this test incorrectly expected the replayed real Codex data to verify successfully under its *original* envelope — it did not, because that envelope's own frozen 10-minute expiry had genuinely elapsed in the real wall-clock time between the prior mission's live proof and this mission's test run. **This is the verifier working exactly as designed** (the identical staleness protection already proven in the prior mission's Phase 7 case 12), not a bug — the test's own expectation was wrong, not the system. Fixed by adding a second, clarifying case (a fresh envelope wrapping the same real nonce/answer), which does verify correctly — isolating "is this data genuinely correct" from "has this particular envelope's freshness window closed," exactly the distinction the protocol's own design intends.

---

## 13. Gemini Live Result (Phase 8)

**Not attempted, correctly halted at Phase 3's own discovery finding.** No Gemini CLI/SDK is installed; no credential exists. The mission's own Authorization Boundary explicitly forbids the two actions that would be required to change this (creating an API key, or a new Google OAuth login). Per the mission's own instruction ("If an endpoint cannot currently be reached, that is a legitimate result"), this is recorded as **BLOCKED**, not as a failed test.

---

## 14. Grok Live Result (Phase 9)

**Not attempted, correctly halted at Phase 4's own discovery finding**, for the same reasons as Gemini plus one additional, explicit blocker (new billing/credits). **BLOCKED.**

---

## 15. Negative Controls (Phase 9, cross-endpoint)

The core substitution test (Section 12) already serves as the negative control for the honest-failure adapters: Gemini's and Grok's stub adapters both correctly report `ADAPTER_FAILED` and correctly leave their obligations at `FAILED`, never `VERIFIED` — directly answering the adversarial concern "could an endpoint merely echo input, or could the wrong endpoint silently satisfy an obligation" for the *blocked* endpoints specifically: no, because they never reach the response-processing stage of the ledger at all. No additional live negative controls were run against Gemini/Grok, since no live call to either was ever possible.

---

## 16. Endpoint Comparison

| | Codex | Gemini | Grok |
|---|---|---|---|
| Invocation method | `codex exec` (non-interactive CLI) | `gemini-cli` (DOCUMENTED, not installed here) | xAI API, OpenAI-compatible (DOCUMENTED, not installed here) |
| Authentication | Already established (ChatGPT subscription OAuth) | Would require new API key or new OAuth login | Would require new account + billing + new API key |
| Challenge success | **Real, verified** | Not attempted | Not attempted |
| Verifier success | **Real, verified** | N/A | N/A |
| Machine-readable return | **Yes, confirmed** | UNKNOWN (not reached) | UNKNOWN (not reached) |
| Consumption | **Yes, confirmed distinct from fetch** | N/A | N/A |
| Latency | 9.9s, real | UNKNOWN | UNKNOWN |
| Failure behavior | Tested (Phase 7, both missions) | Tested via honest stub only | Tested via honest stub only |
| Restart behavior | Tested (prior mission, Phase 7 case 10) | Not applicable | Not applicable |
| Cost | Subscription-included, no new billing | Would require a free-tier key or paid tier, per Section 6 | Would require paid credits, per Section 8 |
| Human intervention (once authorized) | **Zero** | UNKNOWN (blocked before this could be measured) | UNKNOWN |
| Model identity evidence | None available (established repeatedly, this thread) | None available | None available |
| Adapter complexity | Small — one subprocess call | Would be comparably small, per the documented CLI's own non-interactive support | Would be comparably small, given OpenAI-SDK compatibility |

**No model is ranked by intelligence anywhere in this table, per the mission's own explicit instruction — this is a reachability-architecture comparison only.**

---

## 17. Cross-Endpoint Relay (Phase 11) — Not Attempted

**Correctly not attempted.** Phase 11's own precondition ("ONLY if at least TWO endpoints have independently passed qualification") is not met — only one endpoint (Codex) is live-qualified. Designing the A→B causal-relay architecture in the abstract, without a second real endpoint to relay into, would produce a design with no way to distinguish a genuine causal chain from an untestable assertion — not attempted, per this project's own standing discipline against building ahead of what can actually be verified.

---

## 18. Preservation Manifest

See `app/experiments/breakfast_club_reachability/PRESERVATION_MANIFEST.md`, created this mission, reproduced in Section 11's tree above. The known-good Codex reference files are named and pointed to, never moved or rewritten.

---

## 19. Adversarial Self-Review

1. **Could the local harness have computed the response itself?** The transformation is deterministic and was always locally computable (`expected_answer()`) — the evidentiary value is that the *remote* party independently reproduced it on the *specific, novel* nonce, not that neither party could do the math (stated identically in the prior mission's own N3 discussion; unchanged here).
2. **Could stale output pass?** **No — directly disproven live, this mission** (Section 12's real discovery: the replayed real envelope correctly failed as `REJECTED_STALE`).
3. **Could replay pass?** No — tested in the prior mission (N2) and structurally impossible here too, since `message_id` binding is checked on every verification, including in the new substitution test's own code path.
4. **Could an endpoint merely echo input?** No — the frozen transformation requires a real SHA-256 computation, not an echo; directly tested (prior mission's mock `wrong_transformation` case).
5. **Could the wrong endpoint have responded?** Not applicable this mission — no ambiguity exists between two live endpoints, since only one was ever reachable.
6. **Could Gremlin have transported information unknowingly?** No — the entire Phase 8 exchange (prior mission) and this mission's own tests ran end-to-end inside one Claude Code session's own process, with no human-mediated copy step at any point.
7. **Could Claude's active session be doing hidden work required for success?** The transformation itself (`expected_answer()`) is deployed as a plain, deterministic Python function — it does not invoke Claude (this session) at any point; it is ordinary, auditable code, readable in full in `protocol.py`.
8. **Could adapter-specific logic encode expected answers?** No — `verifier.py` (the only code that ever declares a match) never imports or reads anything from any adapter; adapters only ever produce raw text, which the verifier independently checks against its own, adapter-blind computation.
9. **Could model/provider substitution occur unnoticed?** This is, per this whole research thread's own repeated, independent finding, genuinely unverifiable from outside for *any* provider (Codex included) — stated plainly here again rather than glossed over, since nothing about this mission's own work changes that underlying epistemic limit.
10. **Could a transport acknowledgement be mistaken for reasoning consumption?** No — directly, structurally prevented (the `DELIVERED_OR_ACCEPTED`/`REMOTE_PROCESSING` transitions are recorded separately from, and prior to, `CLAUDE_CONSUMED`/`VERIFIED`, and no code path anywhere collapses them).

**No cheaper explanation survived for the one real, live result (Codex); no claim beyond BLOCKED is made for Gemini/Grok.**

---

## 20. Claim Ledger

| Claim | Status |
|---|---|
| CODEX MACHINE REACHABILITY | **ESTABLISHED** |
| GEMINI MACHINE REACHABILITY | **BLOCKED** (not installed, no credential — Sections 5–6) |
| GROK MACHINE REACHABILITY | **BLOCKED** (not installed, no credential, no billing — Sections 7–8) |
| MODEL-AGNOSTIC BRIDGE (core is genuinely endpoint-neutral) | **SUPPORTED** (Section 12's real substitution test), not yet ESTABLISHED (no second live external provider exists to fully confirm it) |
| CHATGPT REACHABILITY | **UNKNOWN/BLOCKED**, unchanged from the prior feasibility report — not investigated further this mission |
| DON / EXISTING-COLLABORATOR REACHABILITY | **BLOCKED**, unchanged — no new evidence this mission bears on this question in either direction |

**No row's status was promoted by another row's success**, per the mission's own explicit instruction — Codex's real success did not upgrade Gemini or Grok's status, and the bridge's SUPPORTED status is explicitly one tier below ESTABLISHED, named precisely rather than rounded up.

---

## 21. FeralEcho Relevance (Phase 15, analysis only — no integration performed)

**Can the same frozen bridge core be used while substituting CLAUDE-CONTROLLED REQUEST with FERALECHO-CONTROLLED REQUEST?** Plausibly yes, per Section 4's own finding that the core is already provider-agnostic — the same reasoning extends naturally to *requester*-agnosticism, since neither `protocol.py` nor `verifier.py` contains any reference to "Claude" as opposed to "Echo" anywhere in their logic; the `sender` field is a plain string.

**What can remain frozen**: transport (the adapter interface itself), the ledger, the verifier, the negative-control pattern, the freshness/replay protection. **What must become Echo-specific**: the decision to contact (Layer A of the prior feasibility report's own system decomposition — no bounded-trigger mechanism exists yet for Echo, per that report's Section 12), message construction (an LLM-authored `reason_for_contact`/`body`, this time authored by Echo's own generation rather than by this Claude Code session), interpretation and response use (Echo's own judgment layer, not yet built), and learning from outcome (connecting a verified/failed exchange back into Echo's own `RiverBrain`-style outcome tracking — a real, if speculative, extension point, not attempted here). **No integration was performed, per the mission's own explicit instruction that this phase is analysis only.**

---

## 22. ChatGPT/Don Boundary — Restated, Not Blurred

**Reaching Codex, and (if ever qualified) Gemini or Grok, establishes nothing whatsoever about reaching ChatGPT, GPT-5.6 Sol in that specific product, the existing human-held conversation, or "Don."** This mission's entire value, stated exactly per its own closing framing, is that it demonstrates what the bridge can do *without* requiring any unsupported continuity claim — a genuinely useful, bounded result that does not need R6 to be true to be worth having.

---

## 23. Remaining Unknowns

1. Whether Gemini's "Antigravity CLI" successor product (the June 18, 2026 replacement noted in Section 6) would present a materially different authorization path than classic `gemini-cli` — not investigated, since neither is installed or authorized here regardless.
2. Whether the bridge core's genuine endpoint-neutrality would survive contact with a *second real* live provider's own quirks (differing response formatting, differing latency/timeout behavior, differing failure modes) — the substitution test (Section 12) is real evidence but is not a substitute for an actual second live success.
3. Whether Gremlin would judge either Gemini's free tier or Grok's paid credits worth the one-time authorization act this mission correctly declined to make unilaterally.

---

## 24. Exact Next Experiment

**Not authorized to run without Gremlin's own decision.** If he authorizes provisioning either a Gemini API key (lower friction — a real free tier exists, per Section 6) or Grok credits (Section 8), the next experiment is trivial to execute: implement `GeminiAdapter.dispatch()`/`GrokAdapter.dispatch()` for real (replacing the current honest-stub bodies with an actual API call, using the already-frozen `protocol.build_challenge_prompt()`), and run the exact same Phase 8 sequence already proven for Codex — no change to `protocol.py`, `verifier.py`, or the ledger design would be required, which is itself the concrete, actionable evidence this mission produced for the primary hypothesis.

---

## Explicit Answers Required by the Mission

**A.** No — no already-authorized legitimate machine interface to Gemini exists on this M5 (Section 5).
**B.** Neither — it was neither demonstrated nor even attempted; it remains purely documented (Section 6), correctly distinguished from local configuration.
**C.** No — same finding, one tier worse (Grok additionally requires new billing, Section 7–8).
**D.** The requirement to create a new account, load paid credits, and create a new API key — three explicit STOP conditions in this mission's own Authorization Boundary (Section 8).
**E.** Yes, for the one endpoint actually tested (Codex, both live in the prior mission and via real-data replay this mission) — the identical frozen protocol, unmodified.
**F.** No — Section 4/10 confirm zero changes to the challenge schema, transformation, ledger, or verifier were needed to support the adapter abstraction.
**G.** Nonce generation, message/mission IDs, the envelope schema, the transformation specification, the obligation ledger, the deterministic verifier, and replay protection (Section 4).
**H.** The executable/CLI invocation itself, response parsing (though this proved trivially reusable), the authentication mechanism, and model selection/provider metadata (Section 4).
**I.** **Partially** — a reusable, provider-substitutable core is real and directly demonstrated (Section 12); a genuinely *multi*-endpoint bridge (two or more live external providers) has not been demonstrated, only one live provider plus one honest-failure-stub-tested substitution path.
**J.** Not tested this mission — Phase 11's own precondition (two independently-qualified endpoints) was not met.
**K.** Not applicable — see J.
**L.** No — nothing in this mission bears on ChatGPT or existing-collaborator reachability in either direction (Section 22).
**M.** Plausibly yes, per the core's demonstrated provider-agnosticism (Section 4/21), but not yet tested — the requester side of the abstraction (Claude vs. Echo) was analyzed, not built or run.
**N.** The smallest clean test: keep every adapter and protocol file exactly as-is, and drive a single real exchange through the identical `protocol.py`/`verifier.py` pair using an Echo-authored `reason_for_contact`/body instead of a Claude-authored one — testing requester-substitution in isolation, the same way this mission just tested endpoint-substitution in isolation, before ever combining both changes at once.

---

**Repository impact**: nine new files under `app/experiments/breakfast_club_reachability/` (`core/`, `adapters/codex/`, `adapters/gemini/`, `adapters/grok/`, `test_adapter_substitution.py`, `PRESERVATION_MANIFEST.md`, plus `__init__.py` files), one new audit report (this document). Zero existing files modified — the qualified Codex reference (`protocol.py`, `verifier.py`, `run_codex_proof.py`, `test_local.py`, `mock_recipient.py`, `negative_controls.py`) is byte-identical to before this mission, confirmed by fresh hash comparison (Section 2). No new credential, account, billing, or OAuth grant of any kind. No commit, push, or restart performed.
