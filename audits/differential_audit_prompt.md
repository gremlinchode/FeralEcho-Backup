# FeralEcho Differential Forensic Audit — Prompt

## Why this is different from the generic version

The prompt you pasted was written for a project nobody had looked at yet.
FeralEcho isn't that project. It already has a documented forensic
history — `CLAUDE.md`'s 49 dated Findings, a separate independent audit
at `Desktop/Forensic Audit/`, and a live `PENDING_DECISIONS.md` tracker.
A full from-scratch audit would spend most of its budget re-deriving
things that are already known and verified, and — worse — could produce
answers that quietly contradict the existing record without either
version being flagged as wrong. The fix isn't less rigor. It's pointing
the rigor at the right target: **has anything changed since the last
verified claim, and what has never been looked at at all** — not
"start over as if nothing is known."

---

## Operating constraints (kept from the original, still correct)

1. **Zero hallucination.** If evidence is missing, say
   `STATUS: INSUFFICIENT EVIDENCE`. Never infer architecture from file
   names alone.
2. **Tool-first.** Every claim traces to an actual command run this
   session — `grep`, `git log`, a live `curl` against a running
   endpoint, a direct read of a pickle/JSON file — not a memory of what
   the code probably does.
3. **Evidence classification on every claim:**
   `[VERIFIED]` (directly observed this session) /
   `[HIGH CONFIDENCE]` (2+ independent observations) /
   `[HYPOTHESIS]` (plausible, needs a runtime check) /
   `[SPECULATION]` (flag, never state as fact).
4. **Preserve research intent.** River Brain, the self-edit pipeline,
   the Global Workspace, and the council mechanism are live experimental
   subsystems with real design decisions behind them, several already
   corrected once (see CLAUDE.md's own "Findings" history of catching
   its own stale claims). Don't recommend removing something without
   checking why it exists first.

---

## Phase 0 — Baseline (new; this is the actual fix)

Before investigating anything, read the current state of what's already
claimed:

- `CLAUDE.md` in full — architecture sections, the Findings history
  (especially the last ~10, which are most likely to still be fresh),
  the Liveness Ledger table, `EDIT_FORBIDDEN_TARGETS`.
- `PENDING_DECISIONS.md` — the live list of what's explicitly still
  open. Anything here is known-open; don't "discover" it as new.
- `Desktop/Forensic Audit/` — a frozen 2026-07-04 snapshot. Useful as a
  historical baseline, not current truth; CLAUDE.md's Findings history
  is the newer source when the two disagree.
- `GREMLIN_ROLE.md` and `ORIGIN.md` — the standing operating rules and
  the project's actual founding intent, so a recommendation doesn't
  accidentally propose undoing something that was a deliberate design
  choice (e.g. WOLF's retirement, the Protector Clause being
  intentionally unbuilt).

Output a short table: claim → where it's documented → last-verified
date if known. This is the differential baseline everything else checks
against.

## Phase 1 — Drift check, not re-mapping

For each subsystem CLAUDE.md already describes (River Brain / RiverBrain
class, `river_deliberation.py`'s council mechanism, the FAISS dual-index
memory system, the self-edit F1/F2/F3 pipeline, the Global Workspace bus,
the Liveness Ledger's checks, the autonomous loop registry in
`autonomy_coordinator.py`), pick 2-3 specific, checkable claims and
verify them **live** against current source or running state — not "does
this look right," but "does the exact function/threshold/file path
CLAUDE.md names still exist and do what's claimed." Report drift as a
correction, in the same voice CLAUDE.md's own Findings already use
("Correction, [date]: ...").

## Phase 2 — Real gaps, not the whole map

Only investigate structural questions CLAUDE.md doesn't already answer.
Concretely, as of this session, known-still-open items worth real
attention: `PENDING_DECISIONS.md` #9 (`reflection_shard.py` missing
self-edit protection) and #10 (scaling the RiverBrain-calibration
exercise, blocked on the MLX/Metal crash in Finding 49). If you find a
genuinely new gap CLAUDE.md never mentions, that's the highest-value
output of this whole pass — flag it clearly as new, with the same
evidence discipline as everything else.

## Phase 2.5 — Ghost code / silent failure sweep (kept, it's good)

This part of the original prompt was well-aimed and matches failure
modes this project has already been burned by for real (WOLF's hollow
auto-approval; the pre-fix `apply_to_code` hook silently failing 253/254
times while its own liveness check still reported healthy). Keep it,
scoped to files Phase 0/1 haven't already cleared:

- Swallowed exceptions (`except: pass`, catch-log-no-reraise) in
  anything not already documented as an intentional fail-open (many
  are, on purpose — check before flagging).
- Vector-store writes that never get flushed to disk.
- Functions returning fixed/mock output dressed as a live call — this
  project has found exactly this pattern twice before (WOLF, the
  hardcoded `mood` field) and both times it looked like real
  integration until checked.
- Background listeners with no live consumer.

## Phase 3 — Red team the new claims only

Phase 0/1's baseline is already trusted (it's CLAUDE.md's own
ground-truth-checked history). Spend red-team effort on whatever Phase 2
found that's genuinely new, not on re-litigating settled findings.

---

## Deliverable

Not a new 5-section report duplicating CLAUDE.md's structure. A single,
short **delta document** — what's confirmed still true, what's drifted
and needs a CLAUDE.md correction, what's genuinely new and needs its own
Finding. If nothing drifted and nothing new turned up in a given
subsystem, say so plainly — that's a real, useful result, not a null one.
