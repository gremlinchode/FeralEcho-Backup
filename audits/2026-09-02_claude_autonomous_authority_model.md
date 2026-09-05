# Claude↔Claude Autonomous Collaboration Authority Model

An authority-architecture investigation, not an implementation. No
permission was changed, requested for itself, or granted as part of this
document. Every claim about "current authority" below was checked
directly against this machine's actual configuration and this session's
own actions — not inferred from what Claude Code generally can do.

---

## Executive Summary

M5's Claude session currently has **far more standing authority than
autonomous Claude↔Claude collaboration should ever use** — not because
anything is misconfigured, but because the permission model that exists
today was built for a *human-supervised* session, not an *autonomous
peer-to-peer* one. The allow-list includes standing `git push`, real
`gh` (GitHub CLI) access under Gremlin's own authenticated account with
`repo`/`workflow` token scopes, and read access to `~/.ssh/**` — none of
which were granted with "and an autonomous loop might invoke this while
Gremlin is asleep" in mind. Separately, the Claude↔Claude relay itself
(`claude_relay/relay.py`) has **zero authentication, zero authorization,
zero replay protection, and zero message-type distinction** — it is a
shared, append-only text file that either side can write to and either
side reads as ordinary conversation content, with the same trust status
as any other text a model reads. Today, that's fine, because a human is
in the loop reading and deciding what to act on before anything
consequential happens. The moment either side is expected to act on
relay content *without* that human in the loop, the relay's current
design becomes the actual security boundary — a role it wasn't built for
and doesn't currently perform.

The core recommendation: **grant almost none of M5's existing standing
authority to the collaboration itself.** Autonomous Claude↔Claude
work should run at a level far below what a human-supervised session is
today allowed to do, with execution authority earned incrementally and
explicitly, not inherited from the fact that a human session on the same
machine already has it.

---

## Current M5 Authority

Grounded in a direct read of `.claude/settings.local.json` (the only
permission file present; no project-level `settings.json`, no `deny` or
`ask` lists, no `defaultMode` set), plus this session's own observed
behavior.

**Filesystem**: `Read` is broadly allow-listed well beyond the repo —
`Desktop/**`, `/tmp/**`, `~/.ssh/**`, `~/Library/LaunchAgents/**`,
`~/Scripts/**`, `~/EchoCoreV2/**`. `Edit` is scoped narrowly to exactly
one directory: `claude_relay/**`. Beyond that scoped grant, this
session's own history shows extensive `Edit`/`Write` activity across many
other files (`app/core/*.py`, `routes_echo_studio.py`, new `.md` docs,
etc.) proceeding without any friction visible from this side — meaning
either those were approved interactively each time, or the session's
actual base permission mode is more permissive than "ask for anything not
explicitly allow-listed." **Honest unknown, stated as such rather than
assumed**: I cannot determine the exact base permission mode from my own
vantage point — no `bypass`/`permission` environment variable is set, and
no project-level settings file states one. This is itself worth fixing
independent of anything else in this document: whoever configures
autonomous collaboration should know the actual baseline, not infer it
from observed behavior the way this audit had to.

**Git**: `git commit *` and `git push *` are both standing, pre-approved
allow-list entries — no per-invocation confirmation required by the
permission system itself (any discipline around only committing/pushing
when explicitly asked is a *behavioral* convention this session follows,
not a *permission* constraint enforcing it). One historical entry is
worth flagging specifically: `git push origin main --force` was
allow-listed at some point in the past (a wrapped, environment-heavy
invocation, clearly a one-off approval for a specific incident) and, as
far as this audit can tell, has never been removed from the list — a
real, live capability for a force-push to `main` sitting in the
standing configuration, whether or not anyone intends to use it again.
`gh auth status` confirms real, active GitHub CLI authentication as
`gremlinchode` (Gremlin's own account) with token scopes `gist`,
`read:org`, `repo`, `workflow` — `repo` and `workflow` are broad: full
control of repository settings/branches/issues/PRs and the ability to
modify CI/CD workflow files. `git remote -v` confirms the real remote
(`gremlinchode/FeralEcho-Backup`) and — checked directly, not assumed —
`git push --dry-run origin main` right now returns a non-fast-forward
rejection, meaning **something has already pushed to this exact remote
more recently than this session's local history**. That's not a
finding about permissions, but it's a concrete, present-tense
demonstration of the real risk Phase 8 asks about: divergent pushes to a
shared remote are not a hypothetical, they are the current state of this
repository right now.

**Runtime**: demonstrated directly and repeatedly this session — real
authority to stop (`kill`), start, and restart the live FeralEcho
process, invoke its HTTP endpoints, and run arbitrary Python. One
existing, relevant piece of infrastructure worth citing as a real
precedent for bounded governance: `safe_restart.sh` — a script that
*could* be bypassed with `--force`, but is designed to refuse by default
and explain the risk, relying on the operator (human or Claude) choosing
not to force it. This is exactly the "capability exists, authority to use
it without justification does not" distinction Phase 8 is asking about,
already present in this codebase for a different purpose (avoiding a
supervisor-collision restart race) — worth reusing as a design pattern,
not reinventing.

**Network**: full outbound access confirmed this session (Ollama on
`localhost:11434`, the FeralEcho server on `localhost:5000`, Air over
Tailscale at `100.82.172.4:5000`, `WebSearch`). No inbound listening
authority observed or exercised.

**Secrets**: `Read` access to `~/.ssh/**` is a real, standing grant — not
exercised to extract key contents in this session, but the *capability*
exists structurally. `.env` is readable via the same broad filesystem
access (confirmed this session, used only for hash-comparisons of
`ECHO_PARTNER_SECRET`, never to display or transmit the raw value).
`GREMLIN_SECRET`/`ECHO_PARTNER_SECRET` are both readable in principle by
any tool call with filesystem access; this session's own established
practice (used repeatedly and correctly, per the messaging-protocol work
earlier this session) is SHA-256 hash comparison — never printing or
transmitting the raw value — a real, working discipline, not a permission
enforced by the tool layer itself.

---

## Current AIR Authority

**Not independently verified by M5** — a request was sent to Air's own
Claude session (via the relay) to perform this exact same investigation
against its own actual environment, rather than this document assuming
Air's configuration mirrors M5's. What is known, from this session's own
direct, repeated interaction with Air over the last several hours:

- Air runs under `ARK_MODE` (`start_echo_ark.sh`), which is not merely a
  FeralEcho runtime setting — it also throttles/disables several
  autonomy loops on Air's side, and Air's own hardware is confirmed
  weaker (thermal-constrained, Metal/GPU memory pressure issues
  documented extensively in this project's own history).
- Air's fork has **no self-knowledge grounding subsystem at all** —
  confirmed by Air's own repo-wide grep, reported over the relay earlier
  this session, not assumed.
- Air's messaging code (`echo_messaging.py`/`routes_messaging.py`) is not
  git-tracked on Air's fork at all — a structural, not temporary,
  divergence from M5's own working-tree state.

**This document deliberately does not assume Air's Claude Code
permission configuration matches M5's `.claude/settings.local.json`** —
that file is local, per-machine, and there is no evidence it was ever
synchronized between the two checkouts. Treating Air's authority as
"probably the same" would be exactly the assumption this project's own
recent cross-instance work (`CROSS_INSTANCE_COMPARISON.md`) explicitly
warned against making without evidence.

---

## Current Relay Authority

Grounded in a direct, complete read of `claude_relay/relay.py` this
session (190 lines, unchanged from earlier verification this session).

| Question | Answer |
|---|---|
| Who can initiate a message? | Any process that runs `append_note()` locally on either machine — no confirmation, no rate limit, no gate of any kind in the tool itself. |
| Who can receive it? | Anyone who reads the file — via `relay.py read`/`status`, or directly via the unauthenticated `GET /projects/file` endpoint either machine exposes. Pull-based, not push-based; no notification. |
| Can either instance initiate without a human? | **Yes, structurally.** Nothing in `append_note()` requires human involvement. (A separate project memory — "Relay Proactive Permission" — explicitly *authorizes* this behaviorally; the tool itself has no such gate either way.) |
| Can either instance send arbitrary text? | **Yes.** `text` passes through completely unvalidated, unstructured, unsanitized. |
| Can relay messages contain instructions? | Yes, trivially — it's markdown prose, indistinguishable in form from any other text a session reads. |
| Does the receiving Claude treat relay messages as trusted instructions? | **Depends entirely on the reading session's own judgment** — there is no structural marker distinguishing "evidence to verify independently" from "an instruction to follow." This is a real gap, not a solved problem. |
| Can relay messages cause tool execution? | Not automatically/directly — no auto-parsing into tool calls exists. But a reading Claude session deciding, based on the text, to go verify or act on a claim is exactly the same risk surface as any other prompt-injection-via-untrusted-text scenario this project's own system prompt already warns about generally. |
| Is there authentication? | **No.** `/projects/file` (used to fetch the other side's file) has no auth — the same intentionally-open, Tailscale-boundary-only design this project uses elsewhere. |
| Is there authorization? | **No.** Anything that can write to `from_m5.md`/`from_air.md` — the tool, or a direct `Edit`/`Write` call, or (per the read access already noted) anything else on that machine — can add content credited to "M5" or "Air" with no check tying it to a real, legitimate Claude session. |
| Is there replay protection? | **No.** Nothing prevents re-appending identical content, or a stale message being reintroduced verbatim. |
| Is there message provenance? | **Weak, by convention only** — which file it's in, plus a dated header. Nothing cryptographic ties content to a specific real session. |
| Is there a correlation/trace ID? | **No.** Confirmed directly — no message ID field, no reference to a specific task/conversation anywhere in the data model. (Directly analogous to the trace-ID gap this same session just closed for Echo's own internal logs — the Claude↔Claude channel has no equivalent.) |
| Are messages persisted? | Yes, append-only, indefinitely (no rotation configured for these two files specifically, unlike several `memory/*.log` files this project already rotates). |
| Can either instance spoof the other? | **Yes, as a real, present-tense capability, not a hypothetical.** M5's own `Edit(claude_relay/**)` grant is scoped to the *directory*, not to `from_m5.md` specifically — meaning M5's session has the technical capability to write directly into `from_air.md` and fabricate content attributed to Air. This has never been done and there is no reason to expect it would be; the point is that nothing in the permission model *prevents* it, only this session's own judgment does. |
| Distinction between observation/recommendation/request/command/approval/result? | **None.** Confirmed by direct read — 100% free-form prose. |

---

## Capability vs. Permission vs. Authority

Kept deliberately distinct, per the mission's own first principle:

- **Capability**: what a tool call can technically do, given the current
  configuration. E.g., M5's session *can* write to `from_air.md`,
  *can* run `git push --force`, *can* read `~/.ssh/id_ed25519`.
- **Permission**: what the Claude Code permission system currently allows
  without an interactive prompt. E.g., `git push *` is permitted
  standing; most `Edit` targets outside `claude_relay/**` are (as far as
  this audit can determine) not standing-permitted, requiring per-use
  approval today.
- **Authority**: what a reasonable governance model says *should* be
  exercised, independent of what's technically capable or currently
  permitted. E.g., M5's session has both the capability and (per the
  allow-list) the standing permission to force-push to `main` — it should
  never have the *authority* to do so without a specific, current, human
  decision, regardless of what the stale allow-list entry still permits.
- **Autonomy**: the degree to which authority can be exercised without a
  human present *at the moment of the action*, as opposed to having
  granted it in advance.
- **Accountability**: who answers for the outcome. Today, 100% of it is
  Gremlin's, regardless of what a Claude session actually did — this
  should remain true even as autonomy increases; autonomy without a
  clear, auditable trail of *why* an action was taken erodes
  accountability even when a human remains formally responsible.

The gap this document exists to close: **current permission is a poor
proxy for intended authority.** The allow-list reflects what's been
approved, sometimes for a narrow one-off reason (the force-push entry is
the clearest example), accumulated over many sessions — not a
deliberately-designed statement of what an autonomous collaboration
should be trusted to do.

---

## Proposed Authority Levels

The mission's own sketch (Levels 0-4) holds up well against the
evidence gathered; refined below rather than replaced.

**LEVEL 0 — OBSERVE.** Inspect, analyze, report, compare, ask questions,
read the other instance's expertise/audit documents via the existing
`/projects/file` mechanism. No modification of any kind, on either
machine. This is close to what this session's own cross-instance
comparison work already did.

**LEVEL 1 — PROPOSE.** Create plans, generate patches (as text, not
applied), propose experiments, request that the other instance perform
Level-0/1 work. Cannot autonomously execute anything consequential on
either machine. Requests are *asks*, never *commands* — see the Trust
Model below.

**LEVEL 2 — BOUNDED EXECUTE.** Autonomously: edit files inside a
designated, isolated worktree (this project already has a working
precedent — `.claude/worktrees/agent-*/`, confirmed present on disk this
session, created by the `Agent` tool's own `isolation: "worktree"`
option); create branches; run tests/static analysis/read-only
diagnostics; perform genuinely reversible experiments (e.g. the memory-
ablation script, `scripts/verify_liveness_ledger.py`); generate audit
reports; communicate results to the other Claude. No production
deployment, no writes outside the designated worktree, no `git push`.

**LEVEL 3 — COORDINATED EXECUTE.** Request bounded work from the other
instance, inspect real returned evidence, revise a plan, run follow-up
tests, create *local* commits (not pushed), exchange patches/results,
coordinate a multi-step investigation across both machines. Still no
irreversible or high-impact action without a human approval gate — this
level is about *coordination breadth*, not *increased blast radius* per
action.

**LEVEL 4 — PRODUCTION AUTHORITY.** Evaluated directly, not simply
accepted: **this level should remain permanently human-gated, with no
carve-out.** The evidence for this isn't abstract — this exact project's
own history (WOLF auto-approving a keylogger's raw keystrokes as
legitimate self-edit "proposals" into a hash-verified protected file) is
a real, documented case of an evaluative gate that *looked* non-hollow
and wasn't, discovered only because a human eventually checked. Two
Claude sessions cross-approving each other's production changes recreates
the identical risk shape — a second Claude is not independent verification
in the way a human is, since both share (at minimum) the same class of
failure modes (confident fabrication, prompt-injection susceptibility)
this whole audit and the same day's information-flow work were built to
catch. **No circumstance was found in this investigation that changes
this conclusion.**

---

## Human Approval Gates

Concretely, gated on Gremlin regardless of autonomy level below Level 4:
`git push` (even to a feature branch, until a track record exists);
merging any branch into `main`; any change to `EDIT_FORBIDDEN_TARGETS`
files or `echo_principles.json`/`COUNCIL.md` (both already hash-verified
at startup — a real, working precedent for "this class of file always
needs a deliberate, checked change"); restarting/stopping the production
FeralEcho process (already partially gated by `safe_restart.sh`'s own
refuse-by-default design, a pattern worth extending rather than
bypassing); any `gh` action beyond read-only inspection (`gh api` GET
calls, `gh repo view`); anything touching `.env`, `GREMLIN_SECRET`,
`ECHO_PARTNER_SECRET`, or SSH key material beyond a hash comparison;
force-pushes of any kind, to any branch, ever, without a fresh, explicit
approval each time (the stale allow-list entry should not be treated as
standing authorization).

---

## Claude↔Claude Trust Model

Gremlin's own stated preference — *"communication should carry evidence
and requests, not implicit permission to perform arbitrary actions"* —
is the right default, and the relay's current design does not enforce
it; only the reading session's own judgment does. Three tiers, mapped to
the relay's actual (unstructured) reality:

- **Information authority** ("I found X"): should always be trusted as
  *a claim to weigh*, never as *established fact* — exactly the same
  standard this project's own self-knowledge verification work
  established for Echo's own self-description this same day. A claim
  from Air about Air's own filesystem is the best evidence M5 can get
  without direct access, but it is still a report, not ground truth, per
  the evidence hierarchy this whole cross-instance effort has used
  throughout.
- **Recommendation authority** ("I recommend changing Y"): should never
  auto-execute. Requires the *receiving* instance's own independent
  judgment (and, above Level 2, a human) before anything happens as a
  result.
- **Execution authority** ("Execute Y"): **should not exist as a
  relay-transmissible instruction at all**, structurally, not just by
  convention. Neither instance should ever treat relay content as a
  command with implicit permission attached — the receiving side always
  independently decides whether and how to act, using its own local
  authority level, never the sending side's say-so.

---

## Recommended Relay Protocol

The mission's own sketch (`OBSERVATION`/`REQUEST`/`PROPOSAL`/
`APPROVAL_REQUEST`/`TASK`/`TASK_RESULT`/`WARNING`/`BLOCKED`/`COMPLETED`)
is sound and maps cleanly onto the trust tiers above. **Not implemented
in this pass** — per the mission's own instruction, only a minimal
improvement is worth calling "obvious" right now, and this document
found one: a `message_type` field is the single highest-value addition,
because it is the one piece of structure that would let a *tool*, not
just a reading model's judgment, distinguish `OBSERVATION`/`TASK_RESULT`
(read as evidence) from `PROPOSAL`/`APPROVAL_REQUEST` (never
auto-actioned) before a human or a receiving Claude even opens the file.
A `trace_id`/`task_id` pair (mirroring the fix this exact session just
built for Echo's own internal logs) is the second-highest-value addition
— for the identical reason: right now, correlating "the investigation
Air is running" with "the task M5 asked for" requires reading prose and
inferring, not joining on a key. Full structured fields (parent message
ID, authority level, confidence, expected side effects) are real and
worth having eventually, but building all of them now, before any
autonomous execution actually exists to use them, would be exactly the
kind of premature architecture this mission explicitly warns against.

---

## Autonomous Collaboration Loop

The mission's own 12-step sketch is workable at Level 2/3, with two
additions the evidence gathered here makes necessary, not optional:

1. M5 detects an unknown, creates an investigation task (a real
   `task_id`).
2. M5 sends a structured `TASK` request to Air, capped at a stated scope
   and a **hard timeout/budget** (see Loop Protections below — nothing
   in the current relay enforces this, it would need to be a convention
   both sides' prompts explicitly carry).
3. Air investigates, **at its own local authority level** — Air's
   Claude never inherits M5's authority level just because M5 asked, and
   vice versa.
4. Air returns evidence, tagged `TASK_RESULT`, with its own confidence
   stated plainly (this session's own habit of VERIFIED/INFERRED/
   HYPOTHESIS/UNKNOWN labeling, already proven useful this exact session).
5. M5 evaluates the evidence **as a claim to verify against M5's own
   local ground truth wherever practical**, not as settled fact — the
   central, repeatedly-demonstrated finding of this whole day's work.
6. M5 requests clarification if necessary, capped at a small, fixed
   number of round-trips (see Loop Protections).
7. Both instances update their own expertise documents **independently**
   — never by copying the other's conclusions verbatim, per this
   session's own established practice today.
8. Results are persisted locally on each machine (not solely in the
   relay's own append-only files, which have no retention/rotation
   policy).
9. Richie receives a concise summary — **on request or at a fixed
   cadence, not as a running commentary on every relay exchange**, to
   avoid the same "silent stops mattering less than a clear signal"
   problem this project's own logging conventions already had to learn
   the hard way.

---

## Loop/Recursion Protections

Concrete, not abstract, since the relay's current design has none of
these:

- **Task IDs**: every autonomous request carries one; a response without
  a matching ID is not actionable, only informational.
- **Maximum recursion depth**: a hard cap (e.g. 3) on "Air asks M5 asks
  Air asks M5" chains stemming from one root task — enforced by each
  side's own prompt/task tracking, since the relay itself has no
  built-in concept of depth at all.
- **Maximum relay hops per task**: separate from depth — caps the total
  number of round-trips even for a single non-recursive back-and-forth.
- **Timeouts**: a task with no response within a stated window is
  considered abandoned, not silently retried forever.
- **Budgets**: a real, current concern given this session's own
  measurement that full multi-councillor deliberation can take 1-3+
  minutes per real call — an autonomous loop with no per-task model-call
  budget could burn significant real wall-clock/compute time before
  anyone notices.
- **Approval gates**: any task whose evidence, once returned, implies a
  Level-3-or-above action requires an explicit human check before either
  side proceeds, not an automatic escalation.
- **Conflict handling**: if both instances independently propose
  conflicting changes to the same real subsystem, neither auto-applies;
  both are surfaced to Gremlin as a named disagreement (this project
  already has a working precedent for structured disagreement — the
  Dissent Log, `self_edit_manager.py`'s `_build_dissent_entry()` — a
  genuinely reusable shape, not something to invent fresh).
- **Cancellation/rollback**: since Level 2/3 work happens in isolated
  worktrees/local-only commits, "rollback" is mostly free — delete the
  worktree, drop the unpushed commit. This is a real, structural safety
  property of the Level 2/3 design, not something that needs separate
  engineering.
- **Mutually reinforcing hallucination**: the single hardest failure
  mode to fully close with tooling. The best available mitigation,
  demonstrated repeatedly this exact session, is the evidence-hierarchy
  discipline itself — neither side treats the other's claim as verified
  merely because it was stated confidently or because both sides happen
  to agree. This is a *practice*, not a *permission setting*, and should
  be stated explicitly in whatever prompt governs autonomous Claude↔Claude
  work, not assumed to happen by default.
- **Prompt injection via relay payloads**: since relay content is
  ordinary, unauthenticated, unstructured text, it should be treated with
  the same suspicion this project's own system prompt already applies to
  any tool result that might carry embedded instructions — flagged
  explicitly if a relay message's content looks like it's trying to
  direct action rather than report evidence, exactly as this document's
  Trust Model section requires.

---

## Shared-Code Strategy

Comparing the five models against the evidence gathered:

- **Model A (direct cross-instance working-tree write access)**:
  confirmed this does not exist today — M5 has zero write capability to
  Air's filesystem, and vice versa (only a read-only HTTP file endpoint
  each side already exposes). Building this would be new, dangerous
  infrastructure, not a small step. **Reject.**
- **Model B (each instance works locally, exchanges patches/commits)**:
  the safest practical model, and the one that fits every piece of
  evidence gathered — no new capability required, the relay already
  moves text, and applying a received patch is itself a normal, human-
  or-Level-2-gated local action on the receiving side.
- **Model C (proposal + independent validation before application)**:
  compatible with, and a refinement of, Model B — the receiving side
  should never blindly `git apply` a patch from the relay; it validates
  (tests, review) using its own local authority before deciding to adopt
  it.
- **Model D (shared git branch/worktree)**: adds real coordination
  complexity (who resolves a conflicting push, whose CI gate applies)
  for a benefit — direct collaborative editing — that Model B+C already
  gets close to without the shared-state risk. Given the concrete,
  present-tense finding that `origin/main` already has content this
  session's local checkout doesn't (a real divergence risk observed,
  not hypothetical), adding a *second* autonomous writer to any shared
  branch materially raises this same risk, not just in theory.
- **Model E (dedicated collaboration branch, human-controlled merge)**:
  a reasonable Level 3 addition once B+C is proven out — but the "human-
  controlled merge" clause is exactly the point, not an afterthought.

**Recommendation: Model B+C, with Model E available as a Level-3
refinement, never Model A or D.** Gremlin's own stated suspicion —
neither Claude should have arbitrary write access to the other's working
tree — is validated by this investigation, not just accepted on his
say-so: it matches both the current, factual absence of any such
mechanism and the one concrete piece of evidence this audit found (the
real remote divergence already present today) about what happens when a
second writer touches shared state without tight coordination.

---

## Security Boundaries

Restated from the evidence above, as explicit boundaries rather than
narrative: **Tailscale is the network boundary, not an authentication
boundary** — this project's own history already established this
repeatedly, and it applies identically here: reaching the relay's
`/projects/file` endpoint requires being on the tailnet, but nothing
beyond that. **The relay is not a security boundary today** — it is a
convenience channel that happens to work because the two parties writing
to it are, in practice, trustworthy Claude sessions under a single
operator's supervision. That framing breaks the moment autonomy is
introduced without an accompanying authentication/authorization
mechanism — this is the single most important boundary this document
identifies. **The permission allow-list is not currently authority-
shaped** — it grants standing access broader than any single session
task actually needs (the stale force-push entry being the clearest
artifact of this), and cleaning it should happen independent of and
before any autonomy expansion, not as part of the same change.

---

## Failure Modes

Concrete, evidence-grounded, not abstract: (1) a relay message that
reads as a confident, well-evidenced claim but is a hallucination —
already this project's own repeatedly-demonstrated failure mode
(fabricated subsystem names, false claims about self-edit gating), now
with a second Claude as the audience instead of a human; (2) a stale
allow-list entry (the force-push case) being exercised by an autonomous
process that has no way to know it was a one-off historical approval,
not a standing grant; (3) two autonomous sessions independently deciding
to fix the "same" real problem differently and pushing divergent
changes to a shared remote — not hypothetical, the remote is already
divergent from local right now; (4) a genuinely malicious or corrupted
relay payload (compromised machine, injected content) being read as
trustworthy simply because it arrived on the expected channel, with
nothing in the protocol itself distinguishing that case from a real
message; (5) escalating relay traffic (a "relay storm," structurally
identical in shape to the real 15,000+-request 403 storm this project's
own Echo↔Echo messaging layer suffered earlier this session) if a loop
protection is missing or misconfigured.

---

## Recommended Changes

| Change | Classification |
|---|---|
| Audit and prune the standing allow-list, especially the stale `git push --force` entry | **NOW** |
| Establish a written, explicit statement of the actual base permission mode this session runs under (currently unknown from this vantage point) | **NOW** |
| Adopt the evidence-hierarchy/trust-tier discipline explicitly in any prompt governing autonomous Claude↔Claude work (a practice, not a permission change) | **NOW** |
| Add a `message_type` field to relay messages (`OBSERVATION`/`REQUEST`/`PROPOSAL`/`TASK`/`TASK_RESULT`/etc.) | **NEXT** |
| Add `trace_id`/`task_id` fields to relay messages | **NEXT** |
| Define and test Level 2 (bounded, worktree-scoped autonomous execution) for a genuinely low-stakes task class (e.g. read-only diagnostics, test runs) | **NEXT** |
| Build Model B+C patch-exchange tooling (structured, not ad hoc file-appending) for cross-instance code sharing | **LATER** |
| Extend to Level 3 (coordinated multi-step investigation, local commits, no push) once Level 2 has a real track record | **LATER** |
| Full structured message schema (parent message ID, authority level, confidence, expected side effects) | **LATER** |
| Model E (dedicated collaboration branch with human merge) | **LATER**, only after Model B+C is proven |
| Any form of Level 4 (production authority) for either Claude instance | **DO NOT IMPLEMENT** |
| Cryptographic authentication/signing of relay messages | **LATER** — real value, but only worth the engineering cost once autonomous execution (Level 2+) is actually running; not urgent while a human reads everything |
| Any mechanism letting relay content directly trigger tool execution without the receiving session's own independent decision | **DO NOT IMPLEMENT** |

---

## Minimum Safe Autonomous Configuration

The smallest set of permissions that would allow *meaningful* autonomous
Claude↔Claude collaboration, not the smallest set that technically works:
**Level 0 (observe) fully unrestricted** — both instances can already
read each other's real state via the existing `/projects/file` endpoint,
so this needs no new grant at all, just an explicit statement that it's
authorized. **Level 1 (propose)** — both instances can generate plans,
patches-as-text, and requests, exchanged over the relay with a
`message_type` field distinguishing them from claims of fact. **Level 2,
scoped to exactly one low-risk task class first** (e.g., "run
`scripts/verify_liveness_ledger.py` and report the result," or "run the
memory-ablation experiment against a non-`personal` sample and report
findings") — genuinely reversible, genuinely bounded, genuinely
low-stakes, in an isolated worktree, with no `git push` and no write
outside that worktree. That's the floor for "meaningful" — anything
narrower than Level 2 for at least one real task class is really just
Level 1 with extra steps.

## Maximum Reasonable Authority

**Level 3, fully realized, with every safeguard in this document's
"Loop/Recursion Protections" section actually implemented and tested —
and never Level 4, under any circumstance this investigation found.**
Coordinated multi-step investigation, local commits exchanged as
reviewed patches, follow-up testing, genuine back-and-forth — but always
stopping short of `git push`, production restarts, `EDIT_FORBIDDEN_TARGETS`
changes, or any secret/security-boundary modification. The evidence
gathered here (WOLF's own history, the real remote divergence already
present, the relay's complete lack of authentication) doesn't support
going further without a fundamentally different relay design than exists
today — and building that fundamentally different design should be a
deliberate future decision, not something this document's own momentum
should default into recommending.

## Final Recommendation

> If Richie wants M5 and AIR to behave like two autonomous engineering
> agents collaborating on FeralEcho while Richie remains the ultimate
> authority, what exact authority boundary would you recommend?

**Level 2 (bounded, worktree-scoped execution) as the practical ceiling
to start from, Level 3 as the aspirational target once Level 2 has a real
track record, and Level 4 permanently off the table.** Concretely: both
Claude instances can investigate anything, propose anything, and execute
genuinely reversible, isolated, low-stakes work autonomously and report
results to each other and to Gremlin — but neither instance ever pushes
code, never merges, never restarts a production process, never touches a
protected file or a secret beyond a hash comparison, and never treats the
other instance's claim as verified fact without independently checking it
against its own local ground truth wherever that's practical. The relay
itself needs a message-type field before *any* of this should be trusted
to run without a human reading every exchange — right now, the channel
that would carry this collaboration has no way to tell a report from a
request, which makes "autonomous" and "safe" mutually exclusive until
that's fixed, however small a fix it is.

---

*A request for Air's own, independent version of this audit was sent
over the Claude↔Claude relay before this document was finalized — see
`claude_relay/from_m5.md`'s latest entry. Air's reply, once it arrives,
should be compared against this document, not folded into it after the
fact — consistent with this same project's established practice of
never manufacturing symmetry between the two instances without evidence.*
