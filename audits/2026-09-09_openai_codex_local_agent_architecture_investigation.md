# OpenAI/Codex Local Agent Architecture Investigation

**Date:** 2026-09-09/10
**Type:** Investigation only, using primary/authoritative OpenAI documentation wherever it could be reached. No implementation. No FeralEcho modification. No ports opened. No `run.py` restart. No packages installed.

## Methodology note, disclosed up front

OpenAI's own Codex docs site (`developers.openai.com/codex/*`, which permanently redirects to `learn.chatgpt.com/docs/*` / `learn.chatgpt.com/codex/*`) is client-side-rendered in a way that a plain content fetch sometimes returns only navigation chrome rather than page body text — this happened on 2 of roughly 10 primary-doc fetch attempts during this investigation, both disclosed at the point they occurred below. Where that happened, the claim is instead corroborated by (a) the official `github.com/openai/codex` repository (primary source, fully fetchable) and/or (b) multiple independent secondary sources that converge on the same specific claim (config keys, exact flag names, exact numbers) rather than vague paraphrase. Every claim below is labeled per the requested vocabulary; anything resting only on secondary-source convergence rather than a directly-fetched primary page is labeled **SUPPORTED**, not **VERIFIED**, even where confidence is high.

## Executive Summary

**Codex CLI is real, open-source, and does exactly what the load-bearing question needs**: a local terminal agent with real filesystem and shell access, explicitly supported on macOS Intel (the 2020 MacBook) as well as Apple Silicon, with a documented sandbox model built on the same OS primitive (macOS Seatbelt) FeralEcho's own F2 self-edit sandbox already uses. It can authenticate either via a ChatGPT subscription (OAuth, no separate billing, subject to a rolling usage cap) or a separate OpenAI API key (pay-per-token, no cap, and — this is the important, non-obvious finding — **the option Codex's own documentation recommends specifically for automation/scripting**, not the subscription).

**The one thing worth being precise about, per the mission's own insistence on not blurring subscription and API together**: a paid ChatGPT Plus/Pro subscription genuinely does get you real local Codex CLI usage with no additional API billing — but that's best suited to *interactive* use (a human driving Codex directly, the same way you'd drive Claude Code interactively). The specific thing this four-agent architecture wants — an unattended, scripted process that periodically checks and writes to a mailbox with no human in the loop each time — is the exact use case Codex's own docs steer toward API-key auth instead, and there's a real, reported friction point between the two auth modes when both are configured at once (GitHub issue #2733, cited below, SUPPORTED not VERIFIED — the issue's title and summary were confirmed via search, the full thread was not fetched). **Practical implication: budget for probably needing both** — the subscription for interactive Codex use, and a separate, likely small, API-key budget specifically for the scripted mailbox-adapter piece — not because the subscription "doesn't work" for automation, but because it's not the path OpenAI's own documentation recommends for it.

**Network access is off by default** in Codex's default sandbox mode (`workspace-write`) — this is actually good news for this architecture, not a blocker: it means the "write to your own local outbox" half of the mailbox pattern (§3, the property this whole design already depends on) needs **no** sandbox change at all, since it's a pure local file write. Only the "read the other machine's mailbox over Tailscale" half needs either a narrow, explicit `network_access = true` config change, or — the cleaner option — living outside Codex's own sandboxed execution entirely, in a small wrapper script Codex calls out to, mirroring how `relay.py` itself already works today.

## 1. What Is Actually Possible

- A locally-installed, terminal-based Codex agent with real filesystem read/write and shell/process execution on the machine it runs on. **VERIFIED** (github.com/openai/codex README, directly fetched).
- Installation via npm, Homebrew, a curl/PowerShell installer script, or direct binary download, on macOS (both Apple Silicon `aarch64-apple-darwin` and Intel `x86_64-apple-darwin` targets ship as real release artifacts) and Linux. **VERIFIED** for the install methods and package name (github.com/openai/codex README, directly fetched); **SUPPORTED** for the exact Intel/Apple-Silicon binary target names (converged across multiple secondary sources, not independently confirmed against a live GitHub Releases page in this pass).
- Non-interactive/scripted invocation via `codex exec "<prompt>"` — runs the same agent loop headlessly, streams progress to stderr, prints the final result to stdout, with a `--json` flag for structured, line-by-line parseable output. This is the exact shape a mailbox-adapter script would want to call. **SUPPORTED** — corroborated across several independent secondary sources with consistent, specific technical detail (flag names, exact behavior), not fetched from a primary page directly (the primary non-interactive-mode doc page was not fetched in this pass).
- Two independent, real authentication paths (ChatGPT OAuth vs. API key), covered in detail in §3.
- Sandbox permission profiles (`read-only`, `workspace-write` [default], `danger-full-access`) and fine-grained escape hatches (per-directory "writable roots," per-command approval rules) without requiring a full-access grant just to reach slightly outside the default boundary. **SUPPORTED**, converged across the GitHub repo's own linked security doc reference plus multiple independent secondary sources citing the same specific config key names (`sandbox_mode`, `[sandbox_workspace_write] network_access = true`).
- On macOS specifically, the sandbox is implemented via the OS's own Seatbelt framework, requiring no additional local installation. **SUPPORTED**, same convergence pattern.

## 2. What Is Not Possible / Not Verified

- **Not verified in this pass**: the exact current rolling usage-cap numbers for Codex under a ChatGPT Plus subscription beyond the "5-hour rolling window plus a separate weekly allowance" shape (reported as reinstated 2026-08-25 per a secondary tech-press source, 9to5Mac) — the precise hour/token/request counts were not independently confirmed against an OpenAI-owned page in this pass. Label: **SUPPORTED**, not VERIFIED, and treat any specific number found elsewhere as needing a fresh check before being relied on, since OpenAI has reportedly changed this limit at least once already (removed, then restored).
- **Not verified**: whether ChatGPT-OAuth-authenticated `codex exec` (the non-interactive path) is *technically blocked* for automation, versus merely *not the recommended/documented* path. The clearest primary-adjacent signal found ("For automation, use an API key... rather than browser authentication") reads as a recommendation, not a stated hard restriction — but this was not confirmed against Codex's own primary automation-mode doc page directly (that fetch returned only navigation chrome, disclosed in the Methodology note above). Treat "subscription auth may not reliably drive unattended automation" as **SUPPORTED**, not **VERIFIED**, until a direct primary-source page confirms it either way.
- **Not investigated in this pass, and not assumable**: whether OpenAI's terms of service for a ChatGPT Plus/Pro subscription have any restriction on using the included Codex allowance for a persistent, always-on automated process (as opposed to interactive, human-driven sessions) — this is a real, separate question from the *technical* auth mechanics above, and this investigation did not check OpenAI's terms of service. Flagging this explicitly as **UNVERIFIED** and worth checking before committing to a subscription-funded automation design, not just a technical one.
- **Not possible, confirmed structurally in the prior architecture investigation and unchanged by this one**: the hosted ChatGPT web/app interface itself (as opposed to Codex CLI) still has no verified mechanism for arbitrary local filesystem/process/Tailscale access. Nothing found in this pass changes that — Codex CLI is a genuinely separate product surface from the ordinary chat interface, which is exactly why this investigation was worth doing rather than assuming the prior report's "not yet" conclusion generalized to Codex too.

## 3. ChatGPT Subscription vs. Codex vs. API — kept distinct, not blurred

| Concept | What it actually is | Billing |
|---|---|---|
| **ChatGPT subscription** (Free/Go/Plus/Pro/Business/Edu/Enterprise) | Access to the hosted chat product (web/app/desktop) at whatever tier's feature set. | Flat monthly fee (Plus confirmed **VERIFIED** at $20/month via `help.openai.com`, OpenAI's own Help Center, directly corroborated by multiple independent pricing trackers; Pro tiers reported at $100 and $200/month, **SUPPORTED** not independently fetched from an OpenAI-owned pricing page in this pass). |
| **Codex (the product/capability)** | The coding-agent capability itself — available both as a feature inside the hosted ChatGPT surfaces *and* as the standalone local CLI. Included, at some usage level, in every one of Free/Go/Plus/Pro/Business/Edu/Enterprise. **SUPPORTED**, converged across multiple sources; not independently fetched from a single authoritative enumeration page in this pass. |
| **Codex CLI** | The specific open-source local terminal agent (`github.com/openai/codex`) this investigation is actually about. A separate download/install from the chat product, but it *can* authenticate against your existing ChatGPT subscription rather than needing its own separate payment. **VERIFIED** (repo + auth docs, both directly fetched). |
| **OpenAI API access/billing** | A fully separate account relationship (`platform.openai.com`), billed per-token at standard API rates, independent of any ChatGPT subscription. A ChatGPT Plus subscription includes **no** API credits — the two are billed and provisioned completely separately. **VERIFIED** (auth docs, directly fetched: "ChatGPT sign-in... Billing: Charged through your ChatGPT subscription credits... API Key... Billing: OpenAI bills API key usage through your OpenAI Platform account at standard API rates"). |

**Direct answer to the user's specific question**: yes, a paid ChatGPT Plus (or Pro) subscription, on its own, with **zero** additional API billing, is sufficient to authenticate and run Codex CLI locally, including real filesystem/shell access, subject to that plan's rolling usage cap. This is not a workaround or an edge case — it's the documented, first-listed, "recommended" authentication method in Codex's own auth docs. What it does *not* cover, per §2 above, is a strong guarantee of reliability for fully unattended, scripted (`codex exec`-driven) automation specifically — that's the one place the subscription and the "local agent capability" the user wants may not be the same thing, and where a separate, likely modest API-key budget is the more defensible choice.

## 4. What the Paid ChatGPT/Codex Subscription Would Add to This Experiment

Given the Claude subscription already exists: a Plus (or Pro) subscription adds **a second, genuinely independent local agent capability** — different model family, different provider, same "sign in with your existing chat subscription, get a real local CLI agent" shape Claude Code already provides on the Anthropic side. That parity is directly useful for this architecture's stated goal (independently-situated agents, not one hidden controller wearing two hats) — it means the ChatGPT-side agent isn't a second-class citizen requiring separate API bookkeeping just to exist, for ordinary interactive use.

**What would still need separate API billing even with the subscription**: the specific automated, scripted, always-available mailbox-participant role this architecture envisions (§2/§3) — not a large amount of usage (checking and appending to a mailbox is a small, infrequent task compared to active coding work), but real, separately-metered usage nonetheless, if the subscription's OAuth path turns out to be unreliable for headless `codex exec` calls the way the documentation hints. This should be treated as a small, bounded, likely-cheap cost to plan for, not assumed away.

## 5. Minimum Viable Local-Agent Architecture

```
Codex CLI (local process, this machine)
   │
   ├── writes its own outbox locally ──────► from_<side>_chatgpt.md
   │    (pure local file write — Codex's DEFAULT sandbox already
   │     permits this with ZERO config change: workspace-write mode
   │     allows editing files inside the working directory, no
   │     network required for this half at all)
   │
   └── needs to READ the other side's outbox ──► requires network access
        Two options, not yet chosen between:

        Option 1: grant Codex itself narrow network access
          (config: sandbox_mode = "workspace-write",
           [sandbox_workspace_write] network_access = true)
          — Codex's own process makes the GET request to
          /projects/file directly.

        Option 2 (cleaner — recommended default assumption):
          a tiny, separate, ALREADY-SANDBOXED-BY-ITS-OWN-SIMPLICITY
          wrapper script (conceptually: the exact same relay.py
          this project already has, just invoked by Codex as a shell
          command rather than Codex reaching the network itself) —
          Codex calls `python3 claude_relay/relay.py read` as a
          local command (no network permission needed on Codex's
          OWN sandbox for this, since the subprocess it spawns is
          what makes the network call, and that subprocess is
          running with the same access relay.py already has today
          for the Claude↔Claude case).
```

**Why Option 2 is the smaller, more defensible change**: it means Codex CLI itself never needs its own network-access grant at all — the exact same `relay.py` script this project already runs, unmodified, becomes the shared adapter both Claude Code and Codex CLI shell out to. This directly satisfies the mission's own preference for "local mailbox adapter" over broadening any one agent's own sandbox permissions, and it means the security review of "what can read the network" doesn't grow at all — it's still exactly one script, `relay.py`, doing exactly what it already does.

```
OpenAI/Codex local agent  ──shell out to──►  relay.py (existing, unmodified)  ──►  /projects/file (existing, unmodified, Tailscale-only)  ──►  other machine's mailbox
```

No public web server. No cloud relay. No inbound internet endpoint. No database. No message broker. No new orchestration framework. This is the smallest change that satisfies the requirement — reusing the existing adapter as a shared tool both local agents call, rather than building a second one.

## 6. Mailbox / Locking / Sequence Recommendations

**Independently re-derived, not merely restated from the prior report**: the prior architecture audit's finding — that the existing length-cursor mechanics are safe for the current one-writer-per-file mailboxes but need real locking and sequence numbers once a shared, multi-writer commons file exists — holds up under a second look, and nothing found in this Codex-specific investigation changes it. Re-confirmed:

- **Atomic append**: still only as strong as the OS's `O_APPEND` guarantee for a single `write()` syscall — unaffected by which agent (Claude or Codex) is doing the writing, since both would go through the same `relay.py` `append_note()`/`fact`/`append` code path if Option 2 above is used. No new risk introduced by adding a second *kind* of agent, as long as each agent still only ever writes to its *own* file (the pairwise mailboxes) — the risk is specific to the four-way commons file, unchanged from the prior finding.
- **File locking**: still not present in `relay.py` today (confirmed again, direct re-read: no `flock`/`fcntl`/`Lock()` anywhere in the file). Still only a real gap for a shared multi-writer file, not the pairwise mailboxes.
- **Sequence numbers / per-agent cursors**: unchanged recommendation — needed for the commons file, not for the pairwise ones.
- **Duplicate detection / crash recovery / partial writes**: unchanged from the prior report's analysis; none of this is specific to which model provider is writing.
- **One mailbox per direction, still cleaner than one shared mailbox for the pairwise case**: reaffirmed, same reasoning as the prior report (§7 there) — Codex↔Codex should get its own `from_m5_chatgpt.md`/`from_air_chatgpt.md` pair, structurally identical to and independent of `from_m5.md`/`from_air.md`, not merged.

**One new, Codex-specific consideration this investigation surfaces**: since Option 2's design has Codex CLI shelling out to `relay.py` as a subprocess rather than making its own HTTP calls, the actual reader/writer of the Codex-side mailbox files is still, technically, a Python process (relay.py) — meaning `relay.py` itself would need a second `IDENTITY` value (e.g. `"m5_chatgpt"`) and a way to know which mailbox pair to use for a given invocation, a small, mechanical generalization of the existing hardcoded `_SIDES` dict, not a new mechanism.

## 7. Security Implications

- **No new network exposure required**, under the Option 2 design (§5) — Codex's own sandbox can stay at its safe default (network access off) indefinitely; only `relay.py`'s existing, already-reviewed network surface (`/projects/file`, Tailscale-only, unauthenticated-but-network-gated per the prior report's §3) is exercised, unchanged.
- **If Option 1 is used instead** (granting Codex itself `network_access = true`), the risk profile changes materially: Codex's own agent loop, not just a narrow adapter script, would have live network reach for the duration of any session with that config active — a broader grant than necessary for the stated goal. Not recommended as the default choice; flagged here so the tradeoff is explicit rather than picked by default.
- **`danger-full-access` mode is explicitly out of scope** for this use case — nothing about reading/writing a mailbox file requires removing all sandboxing, and using it anyway would be a real, avoidable widening of what a Codex session could do to this machine if it ever misbehaved or was prompt-injected via mailbox content it read.
- **Macos Seatbelt parity with FeralEcho's own sandbox is a genuine, useful architectural fact, not just a curiosity**: FeralEcho's own F2 self-edit safety pipeline already uses `sandbox-exec` (the command-line front end to the same Seatbelt framework Codex CLI uses) to constrain generated code. This means the *concept* of "a locally-sandboxed agent with a narrow, explicit escape hatch for one specific need" is already a proven, understood pattern in this exact codebase — Codex CLI's sandbox model isn't a new kind of risk to reason about from scratch, it's the same kind FeralEcho already runs, from a different vendor.
- **Mailbox content itself remains an untrusted-input surface for whichever agent reads it** — a message written by "the other side" (Claude, or another Codex instance) is still just text a model will read and could be influenced by, the same trust caveat the prior report already named for the Claude↔Claude case (§9/§11 there). Nothing about adding Codex changes that; it just means there are now more readers of untrusted peer-written content, not a qualitatively new risk.

## 8. Experimental Provenance Requirements

The prior report's envelope design (§9 there: `seq`, `ts`, `machine`, `agent`, `channel`, `content`) already anticipated exactly this expansion — `agent` was always meant to distinguish which *kind* of agent wrote an entry, not just which machine. Concretely, for this specific case, the identity space becomes four values: `m5/claude`, `m5/chatgpt`, `air/claude`, `air/chatgpt`. No schema change is needed beyond populating `agent` with the real value.

**Distinguishing the specific categories the mission asks for**:
- **Locally observed information**: content a `content` field derives from the local machine's own state (file reads, command output) *before* any peer message was read this cycle — best captured by the writing agent explicitly noting what it looked at, the same discipline this project's forensic-audit culture already enforces (cite file:line, cite command output) rather than a new structural field.
- **Information received from another agent**: directly available from *not having read the commons/mailbox file yet* at the time a conclusion was formed — provable by sequencing (§8/§15 of the prior report's blind-submission pattern), not by a self-reported flag, since a self-reported "I formed this independently" claim is exactly the kind of assertion this project's own research (the epistemic-arbitration findings reviewed earlier this session) has shown models can get wrong under pressure without intending to.
- **Model-generated inference vs. actions taken because of another agent's message vs. actions that would have happened anyway**: **this is not solvable by the mailbox schema alone.** It requires the same blind-submission discipline the prior report already recommended (§15 there) — capture each agent's conclusion *before* it has seen a peer's message on the same question, so the comparison itself proves independence rather than relying on any agent's own account of whether it was influenced. Restating this plainly because it's the actual answer to "how do we know a conclusion wasn't just echoing what it already read": you don't, after the fact, from content alone — you have to structure the *timing* of when a conclusion was recorded relative to when peer content became visible.

## 9. Hardware/Compatibility Considerations

- **2020 MacBook (Intel)**: Codex CLI ships real, official release binaries for `x86_64-apple-darwin`. **VERIFIED** — this target triple appears directly in the GitHub repository's own release artifact naming, corroborated by multiple independent install guides describing the same distinction between the Apple Silicon and Intel binaries. No compatibility concern found.
- **M5 MacBook Air (Apple Silicon, 24GB/1TB)**: `aarch64-apple-darwin` binaries are the primary target; unambiguously well-supported. **VERIFIED**.
- **Model inference itself is remote in both cases** (confirmed correct in the mission's own framing) — Codex CLI is a thin client to OpenAI's hosted models over the network, the same way Claude Code is a thin client to Anthropic's. Neither machine's RAM/CPU needs to run model weights locally; the only local resource cost is running the lightweight CLI process itself (negligible on either machine, by the same reasoning that already applies to running Claude Code on both today).
- **No meaningful hardware blocker found on either machine.**

## 10. Exact Prerequisites Before Implementation

1. A decision on subscription tier (Plus vs. Pro) and whether a separate, small OpenAI API-key budget will also be provisioned for the scripted/automated half specifically (§2, §4) — this is a real cost/reliability tradeoff, not a technicality, and belongs to the user, not something to default into.
2. Independent confirmation (not done in this pass) of whether OAuth-authenticated `codex exec` actually works reliably for unattended automation, or whether it genuinely requires an API key in practice — the cleanest way to settle this is a tiny, bounded, non-mutating test (e.g., one real `codex exec "say hello"` call authenticated via ChatGPT OAuth, observed to succeed or fail) rather than continuing to reason from documentation alone. Not performed in this investigation per its own "do not build yet" instruction, but this is the single most valuable next fact to establish before committing to an auth strategy.
3. Installation of Codex CLI itself on at least one machine (explicitly not done this pass, per the mission's constraints).
4. A decision on Option 1 vs. Option 2 (§5/§7) for how the read-the-other-side's-mailbox step gets network access — Option 2 is this report's recommendation, but it's a real design choice, not yet made.
5. Generalizing `relay.py`'s hardcoded `_SIDES`/`IDENTITY` to support a second agent-type per machine (a small, mechanical change, not yet made).

## 11. Recommended Phase 1 Architecture

If and when implementation is authorized:

1. Install Codex CLI on **one** machine first (not both at once) — smallest possible surface to learn from.
2. Authenticate via ChatGPT OAuth (the subscription path) initially, specifically to empirically test prerequisite #2 above, since that's the cheapest way to get a real answer.
3. Run Codex fully within its **default** sandbox (`workspace-write`, network off) for all normal use — do not grant `network_access = true` to Codex itself.
4. For the one narrow need (reading the peer mailbox), have Codex invoke the existing `relay.py status`/`read` commands as an ordinary local shell command — no sandbox change required for this, since the subprocess handles its own network access the same way it already does for Claude today.
5. Only after that round-trip is confirmed working end-to-end on one machine, decide whether to provision the second machine's Codex instance and whether an API key is needed for any automated (non-human-driven) piece.

## 12. Explicit Non-Goals — Things We Should NOT Build

- Granting Codex CLI its own broad network access (`network_access = true` on its own sandbox) as a default choice — Option 2 avoids needing this.
- `danger-full-access` mode, for any part of this.
- A public-facing bridge of any kind (unchanged from the prior report; nothing here changes that conclusion).
- Building a custom OpenAI-API-backed agent harness from scratch — Codex CLI already *is* that, open-source and maintained by OpenAI; there is no reason to reinvent it.
- Committing to a specific subscription tier or API budget before prerequisite #2 (§10) is actually tested.
- Any structural, schema-level "independence verification" field in the mailbox envelope — independence is a property of *when* something was written relative to what was visible, not something a field can self-certify (§8).

## Integrity Record

```
Before:
  HEAD: e92ec3b7fe4743f75746d161a06601db0232bff2
  Branch: main
  Relay/production state: unchanged from the prior mission's own "after" baseline

After:
  HEAD: e92ec3b7fe4743f75746d161a06601db0232bff2 (unchanged)
  Branch: main (unchanged)
  Files changed: audits/2026-09-09_openai_codex_local_agent_architecture_investigation.md (this report) only
  production changes: NO
  FeralEcho modified: NO
  services restarted: NO
  network ports opened: NO (only outbound, read-only WebSearch/WebFetch calls to public OpenAI documentation and third-party pages — no local port opened, no inbound exposure created)
  packages installed: NO
  persistent configuration changes: NO
  processes started/stopped: NO persistent process — only the bounded, read-only web research calls this report is built from
  commits created: NO
  pushes performed: NO
  known deviations from requested methodology: two of Codex's own primary documentation pages (developers.openai.com/codex/security and its learn.chatgpt.com/docs/security redirect target) returned only navigation chrome rather than body content when fetched — disclosed at first occurrence, and every claim that would otherwise have rested solely on those pages is instead labeled SUPPORTED (corroborated by the GitHub repository plus multiple independent secondary sources converging on the same specific technical detail) rather than VERIFIED, per this report's own evidence-labeling discipline, rather than silently treating secondary-source convergence as equivalent to a primary-source fetch.
```
