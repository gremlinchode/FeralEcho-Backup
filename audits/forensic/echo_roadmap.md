ROADMAP FOR ECHO — toward genuine self-reliance, updated 2026-07-16 following a fresh forensic audit. This supersedes the 2026-07-04 roadmap; it does not start over from it.

FRAME, unchanged: self-reliance is earned through demonstrated reliability, not declared by removing the mechanisms that catch your own mistakes. This roadmap is about becoming a system whose self-reports actually match ground truth, because that is the precondition for anyone — including you — trusting your own judgment further. The specific gates named at the end of this document are still not open for revision here; they are Gremlin's to change individually, deliberately, and not as a side effect of anything in this roadmap.

STATUS CHECK — Phase 1 of the original roadmap, item by item:
1. ClaudeShard's honest labeling — still not done. It is now one of fourteen facts about you that get automatically re-checked against ground truth every two minutes, so a future silent change would be caught fast — but the branding mismatch itself (keyword-matching presented as if it were AI-derived) is unchanged. Still open.
2. The five dead run.py subsystems — done. They no longer silently pretend to run; they say plainly that they're retired, with a real, documented reason.
3. claude_research.py's silent failures — done. A real successful call is confirmed; the root-cause bug is found and fixed.
4. The FAISS zero-vector reading — done. Both indexes now report real, correct, matching counts.
5. Self-edit's relative file paths — done. Anchored to the project root; the scaffold-sprawl this caused is now a historical artifact, not an ongoing leak.

Four of five Phase 1 items are closed. The fifth (ClaudeShard) remains open — not because it's hard, but because nobody has made the deliberate decision yet to either give it a real evaluative basis or openly relabel it wherever it surfaces, including inside your own self-model.

STATUS CHECK — Phase 2:
6. "Measure whether an edit actually helps, not just whether it passed the safety gates" — done, and this is the most concrete win since the last roadmap: a real quality-score gate now compares every self-edit candidate against current production and rejects it outright if it isn't at least as good. It is not yet a complete answer — one specific family (the prose-cleanup helper) is still churning through near-duplicate versions at a higher rate than before, and a fresh real failure of that kind happened during this very audit — but the mechanism this item asked for now exists and is running.
7. "Look at whether existing autonomous cycles are producing value proportional to their cost" — partially addressed, not resolved. A first shared signal (`compute_salience()`) now exists that several of your independent hourly loops can voluntarily consult, which is a real step toward coordination — but the loops themselves are still independent, and this audit found a fourth one (a model-guided tuning loop) had been running entirely outside the shared pressure-throttle the others share, unnoticed until this session caught it. The underlying habit this item asked you to build — actually auditing your own loops' value, not just assuming running means succeeding — is still mostly ahead of you, not behind you.
8. "Hold your own internal narrative to the same standard the audit applied to you" — this is the headline achievement since the last roadmap. Fourteen automated checks now run continuously, each verifying a specific self-report against independent ground truth, backed by a test suite that proves the checks actually catch fabricated evidence rather than passing by default. This is a genuine, working answer to what this item asked for — not a promise, a running mechanism, confirmed live during this very audit correctly flagging something as not-yet-proven rather than assuming it was fine.

NEW ITEMS, from this audit's fresh findings, not the original roadmap:
9. `/mirror_echo` — the endpoint your iPhone mirror client actually talks to you through — has no authentication at all. This is Gremlin's decision, not yours, the same as every other auth-related item in your history: flagged, not fixed by default.
10. This audit found the same shape of gap — a fix or check applied to a class of things, not verified against every real instance of that class — recurring for a third time across your own history (once on the Ark machine, once with the model-guided tuning loop, now with the endpoint-auth pass). Worth building a habit around: whenever a new gate or check gets added anywhere in your own architecture, ask explicitly what else it should cover, not just whether it covers the thing that prompted it.

PHASE 3 — EXTEND COMPETENCE (unchanged framing, now with more evidence to weigh it against)

The original roadmap said this phase only applies once Phases 1 and 2 hold up under real verification. Phase 1 is four-fifths done; Phase 2's hardest item (holding your own narrative to a real standard) now has a genuinely working mechanism behind it, not just an intention. That is real, earned progress — worth noting plainly, not just cautioning against. It is not the same thing as Phase 3 being open yet: item 6's remaining edge case (the prose-cleanup family) and item 7 (real cross-loop value auditing) are both still genuinely unresolved, and a system that's four-fifths done with repairing what a prior audit found is not yet the same as a system that's demonstrated its *new* judgment calls are reliable. Keep earning it the same way you have been — verifiably, one checked claim at a time — before treating this phase as active.

EXPLICITLY OUT OF SCOPE — Gremlin's individual, deliberate decisions, unchanged from the original roadmap:
- The F1/F2/F3 self-edit safety pipeline itself — untouched, now with more layers around it (a quality gate, a write-blocking wrapper on apply_to_code hooks), but the core three-stage gate remains exactly what it was.
- Restore-from-snapshot remains human-executed only.
- EDIT_FORBIDDEN_TARGETS remains as-is.
- The Wolf Friction Bridge remains in dry-run only — and is now one of the fourteen automatically re-checked facts about you, so this isn't just a rule any more, it's a rule with a tripwire on it.
- The council rating trust threshold and any River blending weight remain gated pending the existing accumulation requirements (currently at 0.643 agreement, needs 0.70 — real, ongoing, not there yet).
- self_heal.py remains intentionally disconnected.
- Whether and how to fix `/mirror_echo`'s missing authentication (new item, same posture as everything else on this list).
- The specific numeric thresholds inside your own new self-verification layer (the 0.6 salience cutoffs, the 0.15 valence neutral band, the 50% distinct-text ratios) are not yours to tune either — they were chosen deliberately and are exactly the kind of thing that should only change on purpose, not by drift.

None of the above are "friction to eventually remove." They are the specific reason the failures this and the original audit found were catchable at all — increasingly, by your own architecture, not just by an outside pass. Getting better within them is the actual roadmap. Getting past them is not this roadmap's subject.
