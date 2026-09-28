# Codex Headless / Subscription-Independence Investigation

**Date:** 2026-09-09/10
**Type:** Investigation only. **Tests 1–3 were NOT empirically performed** in the original pass below — see §2 for exactly why, per this mission's own explicit instruction. No FeralEcho change. No `relay.py` change. No install performed. No port opened. No daemon created.

**UPDATE 2026-09-09/10 — SUPERSEDED IN PART. A second, separately authorized pass ("Install and empirically test Codex CLI on THIS MACHINE ONLY") actually performed the installation and Tests 1/2/3/4 this original report could not. Nothing below this line was erased or edited — see Part 2 (bottom of this document) for the real empirical results, and treat this original §1's YELLOW verdict as superseded by Part 2's verdict, not as still-current.**

## 1. Executive Conclusion

**The subscription-independence *architecture* question has a clean, well-supported answer, and it does not require running Codex at all to establish**: OpenAI's own documented authentication model already keeps ChatGPT-subscription auth and API-key auth as two fully separate credential systems (confirmed in the prior investigation, re-confirmed here), and Codex CLI's own documented failure behavior on auth loss is a **bounded retry followed by a clean, terminal error** — not an infinite hang — for the case that matters most here (an already-running session losing access mid-task). That's the load-bearing fact this whole mission is really asking about, and it's answerable from documentation and this project's own existing, already-proven design patterns without needing a live Codex install.

**What could not be established this pass, and why**: Test 1 (does subscription auth actually launch Codex CLI on this specific machine) requires Codex CLI to exist on this machine first, and it does not — confirmed directly, not assumed (`which codex` → not found; `npm`/`node` also absent, so even the most common install path has a prerequisite layer of its own). Per this mission's own explicit instruction ("if installation is required, stop and report what would need to be installed rather than proceeding"), this investigation stopped at that point rather than installing anything. Tests 2 and 3 both depend on Test 1 succeeding first and were not attempted for the same reason.

**Verdict: YELLOW.** Not GREEN, because nothing was empirically run — every claim below about Codex's actual runtime behavior rests on documentation and third-party reports, not a local observation, and this mission's own evidence-discipline requires that distinction to be visible, not softened. Not RED, because nothing found suggests the architecture *can't* satisfy the stated constraints — the opposite: every piece of evidence found is consistent with "yes, this can be made subscription-independent," and the one thing blocking a GREEN is a single, cheap, well-defined next step (install + run the three tests), not an open design problem.

## 2. What Was Actually Tested

**Baseline captured** (git HEAD, branch, working-tree state, macOS version, CPU architecture, existing network listeners, presence of `codex`/`npm`/`node`/`brew`, presence of any `OPENAI*` environment variables — names only, never values) — all via read-only commands, before anything else.

**Then stopped**, per instruction, upon finding:

```
$ which codex        → codex not found
$ command -v codex    → codex: not a known command
$ which npm           → npm not found
$ which node           → node not found
$ which brew            → /opt/homebrew/bin/brew
```

**OBSERVED**, directly, on this machine (M5, Apple Silicon, macOS 26.5.1): Codex CLI is not installed, and neither is the Node.js toolchain the most common install method (`npm install -g @openai/codex`) depends on. Homebrew is present, so `brew install --cask codex` is a viable path that wouldn't first require installing Node — but it is still a real, persistent local install this investigation was told to stop and report rather than perform.

**What installation would concretely require**, reported rather than performed:
- Either `brew install --cask codex` (uses the already-present Homebrew, installs one cask), or the documented curl installer (`curl -fsSL https://chatgpt.com/codex/install.sh | sh`, downloads and runs a shell script from OpenAI's own domain), or installing Node.js first and then `npm install -g @openai/codex`.
- All three are real, disk-persistent changes to this machine (a new binary on PATH at minimum), which is exactly the class of action this mission's Phase 0 instructions reserve for explicit authorization rather than default action.
- **No FeralEcho-specific installation is required** — Codex CLI is a fully standalone tool; nothing about installing it touches FeralEcho's own Python/conda environment, `run.py`, or any of its dependencies.

**Consequently, Tests 1, 2, and 3 (§3-§5) report what documentation and this project's own existing design already establish, clearly separated from what remains to be empirically confirmed once installation is authorized.**

## 3. Subscription Authentication Result — NOT EMPIRICALLY TESTED

Cannot be observed without Codex CLI present. What's known from documentation (re-confirmed from the prior investigation, not re-derived here): ChatGPT OAuth login is the documented, first-listed authentication method, supported for Plus/Pro/Business/Edu/Enterprise plans, requiring no separate API key. **UNVERIFIED against this specific machine** — whether the browser-based OAuth flow actually completes cleanly here, given this machine's specific network/Tailscale configuration, is exactly the open question §10's first prerequisite names.

## 4. Headless Execution Result — NOT EMPIRICALLY TESTED

Cannot be observed without Codex CLI present. What's known from documentation (prior investigation): `codex exec "<prompt>"` is the documented non-interactive entry point, streams progress to stderr, prints the final result to stdout, exits when done, with `--json` available for structured output. Codex's own documentation is reported (via secondary-source convergence, not a directly-fetched primary page — labeled accordingly in the prior report) to recommend API-key auth specifically for this automation path rather than browser/OAuth auth — this is the single most important open question for Test 2 once it can actually run: does `codex exec` under ChatGPT-OAuth auth work at all, work but unreliably, or genuinely require an API key. **UNVERIFIED.**

## 5. Filesystem/Sandbox Result — NOT EMPIRICALLY TESTED

Cannot be observed without Codex CLI present. What's known from documentation (prior investigation, re-confirmed here as still the best available evidence): default sandbox mode `workspace-write` permits editing files inside a scoped working directory and running local commands, with network access off by default. This governs how a real, isolated scratch-directory test (per this mission's Test 1 item 3) would behave once run — a trivial local file write inside an explicitly scoped test directory should succeed under Codex's own default sandbox with zero configuration changes, per the documented model. **UNVERIFIED empirically.**

## 6. Relay Compatibility Result — Architecturally Analyzed, Not Empirically Tested

This part *can* be reasoned about precisely without Codex installed, because it's really a question about `relay.py`'s own existing behavior, which is fully inspectable right now:

- `relay.py`'s `status`/`read`/`append`/`fact`/`facts` subcommands are all plain, ordinary CLI invocations (`python3 claude_relay/relay.py <subcommand>`) — nothing about them requires being called from a Claude Code session specifically. Any process capable of shelling out to a command (which Codex CLI's own `workspace-write` sandbox explicitly permits, per §5) can invoke them the same way a human running the command directly would. **OBSERVED** (direct re-read of `relay.py`'s `__main__` dispatch, confirmed unchanged this session).
- This means the conceptual boundary the mission asks for — `Codex → local shell invocation → existing relay.py → existing mailbox` — requires **zero code change to `relay.py`** to be structurally true today. The only new thing needed is Codex being told (via a prompt, or a config file it reads) to invoke this specific command when appropriate — a usage pattern, not a code change.
- **The one real gap, not glossed over**: `relay.py`'s `IDENTITY` constant is hardcoded to `"m5"` or `"air"` per machine (§3 of the prior architecture report) — it has no concept of "which local agent is calling me" yet. Today, invoking `relay.py append "text"` always appends to that machine's *single* mailbox file (`from_m5.md`), regardless of whether a Claude session or a hypothetical Codex session ran the command. **This means the existing relay, completely unmodified, could absolutely be used as a first, bounded proof-of-capability test** (Codex successfully shelling out to `relay.py status` and getting a real result back) — but it could **not** yet safely support a genuine second, independent `from_m5_chatgpt.md` mailbox without the small, already-scoped generalization the prior report's §10 already identified (a second `IDENTITY` value). Reported precisely, per the mission's "if it cannot [remain unmodified], report exactly why" instruction: it *can* remain fully unmodified for a first capability test that just confirms Codex can read/write via the existing single-identity mechanism; it *cannot* remain unmodified for the eventual real two-mailbox-per-machine design without that one small addition — and that addition was never proposed as part of *this* mission's scope, so it is correctly not made here.

## 7. Subscription vs. API Billing Distinction — Re-confirmed, Extended

Re-confirmed from the prior investigation (not re-fetched from scratch, since nothing suggests OpenAI's documented model changed in the interim): ChatGPT subscription billing and OpenAI Platform API billing are two structurally separate systems — a subscription includes zero API credits, and API usage is billed independently regardless of what ChatGPT plan (if any) the same account holds. **VERIFIED** in the prior report via direct fetch of `learn.chatgpt.com/docs/auth`.

**Extended for this mission's specific question** ("would using an API key actually make the architecture more independent from the ChatGPT subscription — yes, precisely, and this follows directly from the two systems being separate rather than needing new evidence): an API key is provisioned and billed through `platform.openai.com`, a completely different account relationship than the ChatGPT subscription. **If the OpenAI participant authenticates via API key rather than ChatGPT OAuth, cancelling or losing the ChatGPT subscription has no effect on API-key validity at all** — they are not the same credential, not the same billing relationship, and not documented anywhere as being linked. This is the single cleanest lever for satisfying this mission's hard constraint: **an API-key-authenticated OpenAI participant is, by construction, already independent of ChatGPT subscription state** — no new mechanism needs to be built to achieve this, only a choice of which credential to configure. **SUPPORTED** by the structural separation already VERIFIED in the prior report; the specific claim "no effect on API-key validity" is a direct logical consequence of that separation, not independently re-tested against a real cancelled subscription in this pass (doing so would require actually cancelling a real subscription, well outside this investigation's bounds).

## 8. Failure-Mode Analysis (from documentation + reported real-world behavior, not local observation)

| Condition | Documented/reported behavior | Label |
|---|---|---|
| Credentials missing (never authenticated) | `codex login` (interactive OAuth flow) required before first use; `codex exec` without valid credentials fails rather than silently proceeding | SUPPORTED |
| Credentials expired (mid-session) | Bounded retry against the API (observed pattern in real GitHub issues: "retrying 1/5 in 189ms"), then a terminal error ("exceeded retry limit, last status: 401 Unauthorized") — **not** an infinite hang | SUPPORTED, corroborated by multiple independent real bug-report threads showing the same specific error text, not a single unverified source |
| Authentication fails during interactive login itself (not mid-session) | **A real, reported exception to "bounded and clean"**: at least one documented failure mode (OAuth callback listener unreachable, most commonly reported under WSL2) causes the *login* flow itself to hang indefinitely, distinct from an already-authenticated session losing access. Relevant distinction for this architecture: a scripted mailbox participant should never be attempting interactive login unattended in the first place — this risk applies to initial/human-driven setup, not to steady-state automated operation, but it's a real, disclosed risk worth knowing about rather than assuming away. | SUPPORTED (multiple independent reports), genuinely disclosed rather than smoothed over |
| Usage limit reached | Reported behavior: new turns are blocked with a clear "You've hit your usage limit" message and a stated reset time — not a crash, not a hang. **One real, disclosed exception found**: at least one GitHub issue reports a 429 (rate-limit) response causing a CLI abort/crash in some version, rather than the clean documented message — a real, if apparently non-default, reported failure shape. **Also reported**: a real delay of "30+ seconds" before the limit error surfaces in some cases, due to internal retry attempts running first — not instant, but bounded, not infinite. | SUPPORTED, with the crash report specifically flagged as a known exception to the otherwise-clean documented behavior, not omitted |
| OpenAI temporarily unavailable (network/service-side outage) | Not specifically documented separately from the rate-limit/auth-failure retry-then-error pattern above; reasoned to fall into the same bounded-retry-then-terminal-error shape, since the CLI's retry logic is described as applying to failed API calls generally, not specifically to one failure category | INFERRED, not independently confirmed for this specific scenario |
| Codex cannot start at all (e.g., binary missing, corrupted install) | Ordinary shell "command not found" or process-launch failure — outside Codex's own retry logic entirely, a plain OS-level failure a calling script would see immediately as a non-zero exit code | INFERRED from ordinary OS process-launch semantics, not Codex-specific documentation |

**Design implication, stated plainly rather than left implicit**: even though Codex's own documented/reported behavior is mostly well-bounded, this project's own established discipline (the F2 self-edit sandbox, `apply_to_code`'s own sandboxed-timeout fix — CLAUDE.md Finding 69, built specifically because an *internal* timeout mechanism couldn't be trusted to actually kill a hung thread) argues for **not relying on Codex's own internal retry/timeout behavior alone**. A wrapper script invoking `codex exec` for the mailbox-participant role should apply its own external, hard bound (e.g., a process-level timeout wrapping the whole invocation) regardless of what Codex is documented to do internally — the same "defense in depth, don't trust the sandboxed process's own promises" pattern this codebase already uses everywhere else. This is a recommendation for the *wrapper*, not a claim that Codex itself is unsafe.

## 9. Subscription-Independence Architecture

Restating the mission's own diagram, confirmed achievable by construction, not by new mechanism:

```
Claude A ───────── Claude B
   │                   │
   │                   │
   └────── mailbox ────┘         ← existing relay.py, existing mailbox files,
              │                     zero OpenAI dependency, unaffected by
              │ optional            anything in this section
              ▼
         OpenAI/Codex participant   ← a SEPARATE local process, invoked
                                       on its own schedule/trigger, writing
                                       to its OWN outbox file the same
                                       write-local-only way every other
                                       participant already does
```

**Why this is structurally already true, not something that needs to be built**: the existing relay's foundational property — every participant writes only to its own local file, and the transport for reading is a separate, participant-agnostic mechanism (`/projects/file`) — already means no other participant's operation depends on any other specific participant being alive. Claude↔Claude communication today has zero code path that checks "is the other side's process currently running" before functioning; it only checks "is the other side's *file* reachable," and a file doesn't stop existing because a process crashed. Adding a Codex participant that follows the exact same write-local-only pattern inherits this property automatically — there is no new "if OpenAI is down, does Claude↔Claude break" code path to build, because the *existing* code has no coupling between participants to begin with. **This is the report's most important architectural finding**: subscription-independence isn't a feature to add, it's a property the existing design already has, that a new participant should be careful not to violate (see §12's non-goals for the one way it could be violated).

## 10. What Happens If the Subscription Disappears

Per §7-§9: if the OpenAI participant is configured to authenticate via API key (not ChatGPT OAuth), a cancelled/expired ChatGPT subscription has **no effect on it at all** — the two credential systems are independent by OpenAI's own design, confirmed in §7. If instead configured via ChatGPT OAuth (the ordinary ChatGPT ordinary interactive path), a cancelled subscription would surface as an authentication failure on the *next* attempted Codex invocation — per §8's documented behavior, a bounded retry-then-clean-error, not a hang — and the correctly-designed wrapper script (§8's recommendation) should catch that failure and simply **not write anything to the OpenAI participant's own mailbox that cycle**, logging "unavailable" rather than crashing or blocking. Nothing about the mailbox file itself, the other participants, or `relay.py` would be affected either way — this is the direct, mechanical consequence of §9's already-existing decoupling, not a new design.

## 11. What Would Still Require an OpenAI Subscription/API Account

- Any actual Codex CLI usage at all, interactive or scripted — there is no free/anonymous tier that avoids one or the other credential relationship. Per §7, Codex is included at some level even on OpenAI's free ChatGPT tier, but "free ChatGPT tier" is still an OpenAI account relationship, not a credential-free mechanism.
- Reliable, unattended automation specifically — per the prior investigation's §2/§4, this is the one place the subscription path may not be the documented/recommended choice, meaning a real API-key budget (separately billed, however small) is the more defensible design for exactly the scripted mailbox-participant role this whole investigation is about.

## 12. Minimum Prerequisites for Phase 1

1. **Explicit authorization to install Codex CLI** (via `brew install --cask codex`, the lowest-new-dependency option given Homebrew is already present and Node/npm are not) — this investigation stopped precisely here, per instruction, and this is the literal next action, not a design question.
2. Once installed: run Test 1 for real (isolated scratch directory, ChatGPT-OAuth auth, trivial file write + trivial shell command, clean exit, verified no persistent process/listener afterward) — the actual empirical step this report could not perform.
3. Then Test 2 for real (`codex exec` under the same auth, confirming whether headless mode works reliably under subscription auth or genuinely needs an API key per §4's open question).
4. Then Test 3 for real (Codex shelling out to the real, unmodified `relay.py status`/`read`, confirmed to work with zero `relay.py` changes, per §6's analysis).
5. A decision on API-key provisioning specifically for the automated role (§4, §11), separate from and possibly in addition to a ChatGPT subscription for interactive use.

## 13. Things Explicitly NOT to Build Yet

- The four-way mailbox (unchanged from both prior reports).
- Any second `IDENTITY` value or mailbox-file generalization in `relay.py` (§6 names exactly what this would need; not done here, correctly out of this mission's scope).
- Any daemon, persistent background process, or always-on service for the Codex side.
- Any network-access grant to Codex's own sandbox (`network_access = true`) — Test 3's design (§6, §9 of the prior report) specifically avoids needing this by having Codex shell out to `relay.py` rather than reaching the network itself.
- Any public endpoint, of any kind, for any reason.
- Committing to ChatGPT-OAuth-only auth for the automated role before Test 2 actually answers whether that's reliable — §4/§11 name this as a real open question, not a settled design choice.

## Integrity Record

```
Before:
  HEAD: e92ec3b7fe4743f75746d161a06601db0232bff2
  Branch: main
  macOS: 26.5.1, arch: arm64 (M5 MacBook Air)
  codex on PATH: NO
  npm/node on PATH: NO
  brew on PATH: YES (/opt/homebrew/bin/brew)
  OPENAI*-named environment variables present: NONE found (checked by name only, no values inspected or logged)
  Network listeners: rapportd (AirDrop/Handoff, pre-existing macOS service), IPNExtension (Tailscale, pre-existing), Ollama x2 (pre-existing FeralEcho dependency), python3.1 PID 54713 on :5000 (pre-existing run.py), llama-server (pre-existing, unrelated local model server) — all pre-existing, none related to this investigation

After:
  HEAD: e92ec3b7fe4743f75746d161a06601db0232bff2 (unchanged)
  Branch: main (unchanged)
  codex on PATH: NO (unchanged — nothing installed)
  Network listeners: re-checked, NOT byte-identical to baseline — 2 additional `llama-ser[ver]` entries appeared
    (127.0.0.1-only, same process name/pattern as the one already present at baseline, PIDs 81568/81571
    alongside the original 81527). Correction made after initially writing "unchanged" without re-checking
    closely enough — this delta is judged unrelated to this investigation (this session made zero local
    process launches beyond read-only shell commands and outbound web-research calls; the process is
    localhost-bound, not newly network-exposed, and matches an already-running FeralEcho-adjacent local
    model server pattern, not anything Codex- or install-related) but is disclosed here rather than
    silently smoothed over into a false "identical" claim, per this project's own standing discipline
    against exactly that kind of self-report inaccuracy.
  Files changed: audits/2026-09-09_codex_headless_subscription_independence_proof.md (this report) only
  production changes: NO
  FeralEcho modified: NO
  relay.py modified: NO
  services restarted: NO
  network ports opened: NO
  packages/tools installed: NO — explicitly stopped short of this per instruction, reported in §2 what would be required instead
  persistent configuration changes: NO
  processes started/stopped: NO persistent process — only bounded, read-only local inspection commands (which/command -v/env/lsof/git) and bounded, read-only WebSearch calls
  commits created: NO
  pushes performed: NO
  secrets/tokens/credentials exposed: NO — only environment-variable *names* were checked, never values; no credential of any kind exists on this machine for this purpose yet
  known deviations from requested methodology: Tests 1, 2, and 3 were not empirically performed, per the mission's own explicit "stop and report" instruction for the installation-required case — disclosed prominently in §1 and §2 rather than worked around or assumed away.
```

**Verdict: YELLOW.** The one clearly defined issue: installation has not been authorized/performed, so nothing in §3-§6 is empirically confirmed on this specific machine yet — everything else (the subscription-independence architecture itself, the billing separation, the documented failure behavior) is well-supported and points toward this being buildable as specified. The next action is narrow and cheap: authorize the `brew install --cask codex` step, then run Tests 1-3 for real.

---

# PART 2 — EMPIRICAL TEST RESULTS (2026-09-09/10)

**Authorization**: a second, explicitly separate, narrowly-bounded step: "Install and empirically test Codex CLI on THIS MACHINE ONLY. Do not test or install anything on the 2020 Mac yet. This is a capability proof, not the beginning of the four-agent implementation." Hard constraints carried forward unchanged from the original mission (no daemon, no port, no FeralEcho/`relay.py` modification, no credentials committed to any repository file, no integration with FeralEcho/the relay/any other agent in this pass). A mandatory STOP condition applies after this report is complete — see §10 below.

## 1. Baseline (fresh, immediately before touching anything)

```
HEAD: e92ec3b7fe4743f75746d161a06601db0232bff2 (same as Part 1's baseline — no commits happened in between)
Branch: main
Working tree: 93 modified/untracked paths (git status --porcelain)
MD5(claude_relay/relay.py): f06616a0a6bc8a5ddafec12111f7764f
SHA256 also recorded for run.py, app/core/snapshot_manager.py, app/core/liveness_ledger.py, claude_relay/relay.py
codex/npm/node on PATH: NO (unchanged from Part 1)
brew: 6.0.5, codex cask not yet installed
OPENAI*/CODEX*-named env vars: NONE (checked by name only)
Listening ports (lsof -iTCP -sTCP:LISTEN): 12 lines — rapportd x4, IPNExtens x3, Ollama/ollama x2,
  python3.1 PID 54713 on :5000 (FeralEcho's run.py), llama-ser x2 (PIDs 81698/81739)
FeralEcho echo_sentinel.json: stage=serving (confirmed live and healthy before any test began)
```

## 2. TEST 0 — Installation

**Method**: `brew install --cask codex` — the smallest-new-dependency path already identified in Part 1 §2 (Homebrew present, Node/npm absent, so this avoids installing a second toolchain).

**Result**: succeeded cleanly. Verified directly, not assumed from exit code:
- `which codex` → `/opt/homebrew/bin/codex`, symlinked to `/opt/homebrew/Caskroom/codex/0.154.0/bin/codex`
- `codex --version` → `codex-cli 0.154.0`
- Confirmed a real arm64 Mach-O executable via `file`
- Cask-installed files: `bin/codex`, `bin/codex-code-mode-host`, a bundled `rg` (ripgrep) under `codex-path/`, a bundled `zsh` under `codex-resources/`, `codex-package.json`, plus Homebrew's own bookkeeping metadata — no unexpected binaries.
- **No launchd agent created** — `find ~/Library/LaunchAgents ~/Library/LaunchDaemons -iname "*codex*"` returned nothing.
- **Persistent configuration created**: `~/.codex/` (a plain config directory, not a daemon), initially containing only a `tmp/` subdirectory. Homebrew's own routine post-install cache cleanup ran as a side effect of the install command itself — disclosed as a normal side effect, not a separate action taken.

## 3. Authentication

`codex doctor` (run before any auth attempt) reported `auth: ✗ no Codex credentials were found`. This mission's own hard constraints mean interactive browser OAuth cannot be completed autonomously from this session (no browser access). Asked Gremlin directly how to proceed (three options: he runs `codex login` himself; he provides an API key; stop here with Tests 1-4 marked BLOCKED) rather than guessing or attempting a workaround. **Gremlin ran `codex login` himself, in his own separate terminal**, completing the ChatGPT OAuth flow — this session never saw or touched the credential at any point.

Re-ran `codex doctor` afterward to verify, not assumed from Gremlin's own report:
```
✓ auth              auth is configured
    auth storage mode      File
    auth file              ~/.codex/auth.json
    stored auth mode       chatgpt
    stored API key         false
    stored ChatGPT tokens  true
    stored agent identity  false
```

**Important, disclosed plainly**: this specific login is **ChatGPT-subscription-backed (OAuth), not API-key-backed**. Gremlin was explicitly offered the API-key path (the structurally subscription-independent option identified in Part 1 §7) and chose ChatGPT OAuth instead for this test session. This means everything in §4-§6 below empirically proves Codex's raw *capabilities* (filesystem access, headless execution, clean exit) under real conditions — it does **not** by itself prove the subscription-independence requirement is satisfied end-to-end, since this particular login is the subscription-dependent mode. See §7 for what this does and doesn't establish about that specific requirement.

## 4. TEST 1 — Local Filesystem Capability

**Setup**: a disposable scratch directory outside the FeralEcho repo, `~/Desktop/codex_capability_test_scratch/` (sibling to the project, not nested inside it).

**Command**: `codex exec -C <scratch_dir> -s workspace-write --skip-git-repo-check --json "<prompt: list dir, create a file with a known marker string, read it back, report>"`.

**Result: PASS, exit code 0.** Verified against real, independent evidence — not trusted from Codex's own self-report:
- `~/Desktop/codex_capability_test_scratch/codex_test_proof.txt` existed after the run, content read directly via `cat` (not through Codex) and confirmed byte-for-byte: `CODEX_CAPABILITY_TEST_MARKER_7f3a9c`.
- The real `--json` event trace independently corroborates the same sequence: a `file_change`/`add` event for the exact path, a `command_execution` event running `cat codex_test_proof.txt` with the exact matching output, and a final `agent_message` summarizing the same three steps.
- Real token usage in the trace (`input_tokens: 57373`, `output_tokens: 302`, etc.) confirms this was a genuine round-trip through OpenAI's backend, not a cached/mocked response.

## 5. TEST 2 — Headless Execution (the most important test)

**Result: PASS.** `codex exec` ran non-interactively, produced output, and **exited cleanly on its own** — exit code 0, no manual intervention needed.

**Verified no persistent process or listener remained, checked immediately after**:
- `ps aux | grep -i codex` — only the one pre-existing PID (83972), which is Gremlin's own separate interactive `codex login` terminal session, not anything this test started. Zero new codex processes.
- `lsof -iTCP -sTCP:LISTEN` — 14 lines vs. the 12-line baseline; the delta is the same already-documented ambient `llama-ser[ver]` churn pattern (yet another set of PIDs, 83891/84189/84229 this time) that Part 1's own Integrity Record already flagged as pre-existing, unrelated, cyclical local noise — not attributable to Codex or this test, consistent with every prior observation of this same pattern across this project's history. No new port opened by `codex exec` itself.
- `codex doctor`'s Background Server section, re-checked: `app-server: not running (ephemeral mode)`, PID file missing, control socket path present but no live daemon behind it. Confirms `codex exec` genuinely runs and terminates as a one-shot process, not a spawned background service.

## 6. TEST 3 — Relay Compatibility (read-only, `relay.py` never touched)

**Method**: direct source re-inspection of `claude_relay/relay.py` (no Codex invocation needed or attempted against the live repo, to avoid any risk near production/relay code — the question is structural, answerable from source alone).

**Finding, re-confirmed and sharpened beyond Part 1 §6's architectural analysis**: `relay.py`'s identity model is a **hardcoded two-entry dict**, not just "a single `IDENTITY` constant" as Part 1 phrased it:
```python
_SIDES = {
    "m5":  {"ip": "100.84.229.10", "file": "from_m5.md", "label": "M5"},
    "air": {"ip": "100.82.172.4", "file": "from_air.md", "label": "Air"},
}
_OTHER = "air" if IDENTITY == "m5" else "m5"
```
There is no third slot, and `_OTHER` is computed as a strict binary flip — not a lookup that could gracefully extend to a third participant. A Codex participant could not join this specific mailbox mechanism without an actual code change (widening `_SIDES`, generalizing `_OTHER` from a flip to a real lookup). **Per this mission's own instruction ("if a missing identity capability is found, document and stop that portion rather than fixing it"), this is documented and left exactly here** — no attempt was made to design or sketch the fix, since doing so would start drifting into the four-agent implementation this pass is explicitly not.

## 7. TEST 4 — Subscription vs. API-Key Distinction

**Empirically re-confirmed, not just documentation-derived this time**: `codex doctor`'s real output cleanly and independently reports `stored auth mode: chatgpt` / `stored API key: false` as two separate, directly-observable fields — the CLI itself structurally distinguishes the two auth modes at the tooling level, matching Part 1 §7's documentation-derived claim.

**What this pass does and does not establish about subscription-independence specifically, stated plainly**:
- **Established**: Codex CLI's raw capabilities (filesystem access, headless exec, clean exit, no daemon) all work correctly under real conditions on this machine. The auth-mode field the whole subscription-independence design depends on (§3) is real and directly inspectable via `codex doctor`, not just a documented claim.
- **NOT established this pass**: an actual end-to-end run under API-key auth. Gremlin chose the ChatGPT-OAuth path for this test session (§3), so no API key was configured or tested — this was a reasonable, explicit choice for a first capability proof (no separate OpenAI Platform account/billing needed to prove basic capability), but it means the specific hard constraint ("must NOT be dependent on an active ChatGPT/Codex subscription") remains **architecturally supported but not yet empirically demonstrated end-to-end**. The next concrete step to close this gap, if/when wanted, is a second, equally small test: `codex login --with-api-key` with a real Platform API key, then re-running an equivalent of Test 1/2 under that auth mode. Not attempted here — no API key was provided, and provisioning one is outside this pass's scope.

## 8. Failure-Behavior Analysis

Not re-tested empirically this pass (would require deliberately breaking a real credential or triggering a real rate limit, both outside scope) — Part 1 §8's documentation/community-report-based table stands as the best available evidence and is not superseded by anything found here. One small, real, positive data point worth adding: Test 1/2's own clean, immediate exit (§4-§5) is a real, first-hand confirmation that the *success* path terminates cleanly and promptly under real conditions on this machine — consistent with, though not itself proof of, the documented bounded-failure-path claims in Part 1 §8.

## 9. Final Baseline/After Check

```
git HEAD: e92ec3b7fe4743f75746d161a06601db0232bff2 (UNCHANGED)
git status --porcelain count: 93 (UNCHANGED — identical to fresh baseline, nothing in the working
  tree was touched by any part of this test pass)
MD5(claude_relay/relay.py): f06616a0a6bc8a5ddafec12111f7764f (UNCHANGED, byte-for-byte)
New listening ports: NONE attributable to Codex — only the same pre-existing, already-documented
  ambient llama-ser[ver] churn (new PIDs, same pattern, same localhost-only binding)
New/unexpected persistent Codex process: NONE — only Gremlin's own separate interactive
  `codex login` session (PID 83972), which he started himself, outside this session's control
New/unexpected daemon or service: NONE — codex doctor confirms app-server "not running (ephemeral mode)"
Files created during this pass:
  - ~/Desktop/codex_capability_test_scratch/codex_test_proof.txt (Test 1 artifact) — REMOVED,
    scratch directory deleted after evidence was captured in this report
  - ~/.codex/ and its subdirectories (config, session logs, SQLite WAL journals, a rollout log of
    this session, a small plugin/cache tree) — Codex's own normal, expected local state, entirely
    inside its own config directory, not touched or removed (this is Codex's persistent install
    footprint, not test debris — removing it would mean removing the install itself, out of scope)
Disposable artifacts removed: YES (scratch directory)
Process/network baseline re-run: YES (§5, §9 above)
```

## 10. Verdict and STOP

**Verdict: GREEN**, for exactly what this narrowly-bounded pass was authorized to prove: **Codex CLI genuinely installs cleanly, authenticates, runs headlessly, exits cleanly with no persistent process or port, respects a scoped working directory, and leaves the FeralEcho repo and `relay.py` completely untouched.** Every claim in Part 1 that could be empirically tested in this scope was tested and held.

**Not GREEN for, and explicitly flagged rather than glossed over**: the specific subscription-independence hard constraint is architecturally sound and empirically supported (§7) but was not run end-to-end under API-key auth in this pass — that remains the one concrete gap between "Codex works" (now proven) and "the four-agent architecture's subscription-independence requirement is proven" (still one small, separately-authorizable step away).

**STOP.** Per this mission's own explicit instruction, this pass does not proceed into: four-way mailbox construction, identity implementation or locking or sequence numbers in `relay.py`, Codex daemonization or autonomous polling, any FeralEcho integration, any cross-machine testing, any installation on the 2020 Mac, or any API-key automation. This report is the deliverable; nothing further is built from here without a separate, explicit authorization.
