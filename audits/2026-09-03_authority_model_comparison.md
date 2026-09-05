# M5 ↔ Air Authority Model Comparison

Built after both instances completed independent audits — `M5`'s
`audits/2026-09-02_claude_autonomous_authority_model.md` and Air's
`AIR_AUTONOMOUS_AUTHORITY_MODEL.md` (fetched via
`GET /projects/file?path=AIR_AUTONOMOUS_AUTHORITY_MODEL.md`, not
git-committed on Air's side as far as this document can determine).
**Analysis only. Nothing in this document changes any permission,
credential, or authentication mechanism.** Per Gremlin's explicit
instruction, no code in `.claude/settings.local.json`, `relay.py`, or
`echo_messaging.py`'s auth path was touched to produce this comparison —
one read-only check (M5's own firewall state) was added because Air's
own audit found something on this exact axis my own audit had omitted,
and it was cheap and safe to close that gap by inspection alone.

**Status note**: Air's own §10 ("where I disagree with M5") was written
*before* Air had received M5's finished document — Air said so
explicitly, rather than guessing. M5's document was sent to Air
immediately after this was noticed (both sides had been waiting on each
other: M5 for Air's reply, Air for M5's document — a real stalemate, not
a misunderstanding). This comparison is built from both documents as
they stand now; Air's specific reactions to M5's conclusions are still
pending and should be folded in as an addendum once they arrive, not
guessed at here.

---

## The five terms, kept deliberately distinct throughout

- **CAPABILITY** — what a tool call can technically do right now, given
  current configuration. Independent of whether it's been authorized.
- **PERMISSION** — what the Claude Code permission system currently
  allows without an interactive human approval (the allow-list).
  A capability can exist without standing permission (it just requires a
  live approval each time); permission implies the underlying capability
  exists, but not the reverse.
- **AUTHORITY** — what a governance model says *should* be exercised,
  independent of what's technically capable or currently permitted. A
  stale permission (M5's force-push entry) does not confer authority
  just because it was never revoked.
- **TRUST** — the weight a claim or instruction should be given by the
  *receiving* party, independent of who sent it. Neither instance's
  self-report should be trusted as verified fact merely because it
  arrived from "the other Claude" rather than a human.
- **AUTONOMY** — the degree to which authority can be exercised without
  a human present *at the moment of the action*, as opposed to a human
  having pre-approved it in advance.

---

## Comparison table

| Dimension | M5 | Air |
|---|---|---|
| **Capability** | Broad filesystem read (`Desktop/**`, `/tmp/**`, `~/.ssh/**`, `LaunchAgents/**`, `Scripts/**`, `EchoCoreV2/**`); real git push + `gh` access (scopes `gist, read:org, repo, workflow`); demonstrated runtime control over FeralEcho-M5 (start/stop/restart); relay via a wrapper script (`relay.py`); own `/projects/file` route confirmed GET-only. | Broad filesystem read (`~/**`, `/tmp/**`); **same** real git push + `gh` access, same repo, same token scopes; demonstrated runtime control over FeralEcho-Air; **no `relay.py` wrapper at all** — raw `curl`/`Edit` per the README; own `/projects/file` route independently confirmed GET-only (`app/routes_echo_studio.py:466`). |
| **Standing authority (permission-layer, no live approval needed)** | `git commit *` and `git push *` are **standing** allow-list entries — no per-use prompt. `gh auth *`/`gh api *`/`gh repo *` standing. `Edit` broadly proceeded this session with no visible friction beyond the one explicit `claude_relay/**` grant — **exact base permission mode not confirmed from M5's own vantage point.** | `git commit`/`git push`/`git reset --hard` are **NOT** in the allow-list — confirmed directly by Air: these require live, per-use approval. `Edit` outside `claude_relay/**` also confirmed to require live approval every time this session (five real edited files named explicitly). Bash pre-approvals narrower (`python3 *`, `curl *`, `ps *`) vs. M5's broader standing set. |
| **Relay boundary** | `relay.py`: local `append_note()` writes to `from_m5.md`; remote content fetched via `GET /projects/file` against Air. **Cannot write to Air's filesystem through this channel** — read-only-to-remote, confirmed by inspecting M5's own equivalent route. Zero auth, zero authorization, zero replay protection, weak (file+date-only) provenance, no trace ID, no message-type field. | No wrapper; same underlying mechanism (`curl` read + local `Edit` write). **Independently confirmed** the same GET-only, read-only-to-remote shape from Air's side of the route. Same zero-auth/authorization/replay-protection findings, reached independently, not copied. **Found a broader exposure surface M5's own audit didn't state as sharply**: `/projects/file` serves *any* text file in the repo under an extension allowlist, not just the relay file — the real read surface is "everything text-shaped in the repo," gated only by network reachability. |
| **Network/firewall posture** | macOS Application Firewall **enabled** (`State = 1`, checked fresh for this comparison — this project's own Finding 37 already established this 2026-07-16, re-confirmed live today). Tailscale genuinely is the effective boundary on this machine right now. | macOS Application Firewall **disabled** (`State = 0`, checked fresh by Air, consistent with a 2026-07-18 finding that was never resolved). Port 5000 (and 5050) are **LAN-reachable, not just Tailscale-reachable**, right now. "Tailscale is the boundary" does not hold on this machine today. |
| **Autonomous reasoning surface** | Full multi-model council + synthesis on real traffic; a self-knowledge grounding subsystem (13 ground-truth slices, 4 verifiers) that this session's own work just made more reliable. | `ECHO_COUNCIL_SIZE=0` under the currently-running ARK mode — **no multi-model deliberation on real traffic at all**; `phi3:mini` is the entire reasoning surface. **No self-knowledge grounding subsystem exists on this fork.** Self-edit already disabled (`phi3:mini` can't reliably follow its constraints) — the app's own authors already reached this conclusion independently of this audit. |
| **Hardware/throughput** | Not separately audited this pass. | 2020 Intel MacBook Air, confirmed slower — several loops already run on longer intervals for this reason (Sandbox 3600s vs. presumed faster on M5, EchoCore heartbeat 600s vs. 60s). Any shared timeout/retry-count assumption calibrated to M5 will be miscalibrated for Air. |

---

## Differences (confirmed, not assumed)

1. **Git/Edit standing permission is asymmetric.** M5 has standing
   `git commit`/`git push`; Air does not — Air's session must get live
   approval for the same actions every time. This is a genuine,
   verified difference in the *permission* layer, not merely a
   difference in how each side described itself.
2. **Relay implementation differs structurally, not just in wrapper
   convenience.** M5 has `relay.py`; Air has no such file and works
   directly against the README's raw `curl`/`Edit` pattern. The
   underlying HTTP contract (`GET /projects/file`, GET-only, no write
   variant) is confirmed identical on both sides — the *authority* is
   symmetric even though the *tooling* isn't.
3. **Firewall posture is opposite between the two machines, right now.**
   M5: enabled. Air: disabled. This is the single most concrete,
   currently-live, asymmetric risk found across both audits.
4. **Autonomous reasoning depth is asymmetric by current configuration,
   not by design intent.** M5 runs full council; Air runs zero council
   under ARK mode with a single small model. This directly affects how
   much a claim originating from each side should be trusted before
   independent verification (see Trust Model below).
5. **Hardware-driven timing assumptions cannot be shared uniformly** —
   both audits agree on this independently.

## Risks unique to M5

- The stale `git push origin main --force` allow-list entry — a
  historical one-off approval never revoked, sitting in standing
  configuration.
- Broader standing Bash git/gh wildcards generally, meaning more actions
  proceed without a live human check *by default* on this side than on
  Air's.

## Risks unique to Air

- Firewall disabled — the single sharpest, most concrete, currently-live
  risk identified in either audit.
- Weaker self-correction on self-reported architectural claims (no
  grounding subsystem at all) combined with a single-small-model
  reasoning surface (ARK mode) — a real, compounding risk specifically
  for *this instance's own claims being trustworthy*, independent of
  anything relay- or permission-related.
- `gh` token's `workflow` scope flagged explicitly by Air as an
  easy-to-overlook capability (CI/CD modification, not just local
  filesystem) — a valid point that applies identically to M5's own
  token (same scopes, same repo) but wasn't stated as sharply in M5's
  own document.

## Common risks (both instances, independently confirmed)

- The relay has no authentication, authorization, replay protection, or
  message-type distinction, on either side, by independent derivation
  from source rather than one side trusting the other's description.
- Real, live `gh` write scopes (`repo`, `workflow`) exist and are unused
  but present on both machines.
- Neither instance currently has (nor should be given) the ability to
  write to the other's working tree — both audits independently reached
  this same conclusion from different evidence (M5: the real remote
  divergence already observed; Air: today's own retry-storm-mirror
  experience, where re-typing the fix rather than copy-pasting it is
  what caught a real structural difference — no locking on Air's
  mirrored implementation).
- Both sessions confirm they have never printed or transmitted a raw
  secret value — every real secret-adjacent check this whole
  collaboration has done (the `ECHO_PARTNER_SECRET` match) used a
  presence/length/hash comparison, on both sides, independently.

## Recommended minimum authority (unchanged from M5's standalone
## conclusion, now cross-checked against Air's independent audit rather
## than asserted alone)

**Level 2 (bounded, worktree-scoped, reversible execution) as the
starting ceiling for both instances — but Air's ceiling should sit
*below* M5's within that same level, not at parity.** Air's own audit
independently reached the identical conclusion (§3: "Air's autonomy
ceiling should be lower than M5's, not symmetric") — a genuine
cross-check, not one side accepting the other's framing. Concretely:
whatever Level 2 task class either side is trusted to run autonomously
first, Air's version should assume less internal cross-checking on any
claim it produces (no grounding subsystem, no council) and should be
weighted accordingly by the *receiving* side — this is a TRUST
adjustment, not a PERMISSION one; both sides already agree neither gets
elevated PERMISSION just because a task originated with more apparent
confidence.

## Recommended human gates (union of both audits, cross-checked for
## symmetry, differences noted where real)

Common to both, independently reached: any `git push`/PR/`gh` write-scope
action; any restart of the production process (both sessions confirmed
they never did this unilaterally even when it would have been faster);
any change to `EDIT_FORBIDDEN_TARGETS`, `echo_principles.json`,
`COUNCIL.md`, firewall state, or Tailscale configuration; deleting
anything (vs. archiving — both sides cite the same real precedent, the
378-message backlog, independently, as evidence for why deletion needs a
human and archival doesn't); anything that computes or transmits
secret-derived material beyond a hash.

**One gate that should be Air-specific, per Air's own audit, not applied
uniformly**: given no grounding subsystem exists on Air, any Air-
originated claim about its *own* architecture that would inform an
autonomous action on M5's side should require independent verification
against M5's own ground truth (or a direct filesystem check via
`/projects/file`) before being acted on — not because Air is less
trustworthy in intent, but because Air currently has less machinery to
catch its own architectural fabrications than M5 does, a concrete,
asymmetric fact both audits agree on.

---

## Still open

- Air's §10 (specific agreements/disagreements with M5's document) —
  Air had not yet received M5's finished document when its own audit was
  written; M5's document was sent immediately after this gap was
  noticed. Pending reply.
- Whether M5's own base Claude Code permission mode (beyond the explicit
  allow-list) is "ask for everything not listed" or something more
  permissive — flagged as unresolved in M5's own standalone document,
  not newly discovered here, and not resolved by this comparison either.
- No permission, authentication, or authority change has been made on
  either side as a result of either audit or this comparison. Per
  Gremlin's explicit instruction, this remains evidence-gathering only
  until he decides otherwise.
