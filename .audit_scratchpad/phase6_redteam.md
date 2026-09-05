# Phase 6: Red Team Verification & Self-Correction (raw notes)

Actively re-checked several of this audit's own conclusions before finalizing, per protocol.
Errors CAUGHT AND CORRECTED during this pass (kept here as a methodology record, not hidden):

1. Initial custom AST import-scanner had a real bug: `from package import submodule` only
   recorded "package" as an imported name, not "package.submodule" -- this produced a batch of
   FALSE POSITIVE "zero inbound importer" results (e.g. app/core/config.py, app/core/
   conversation_service.py both initially misreported as orphaned). Fixed the scanner (added
   alias-name concatenation for ImportFrom nodes) and re-ran before drawing any conclusions from
   the dependency graph. Lesson applied: did NOT trust the first pass's raw output for the final
   report; re-verified the corrected graph's most surprising claims against direct `grep`
   cross-checks before writing them into Phase 2/4 notes.

2. `app/core/load_project_map.py` initially looked ambiguous because a plain-text grep for the
   string "load_project_map" hit `app/core/echo_core.py` too -- but that hit was `echo_core.py`'s
   own SAME-NAMED METHOD (`self.load_project_map`), an unrelated, coincidentally-named class
   method, not a real import of the module. Caught by checking for an actual `import`/`from`
   statement specifically (not a bare string match) before concluding orphan status. Confirmed:
   genuinely zero real imports of the module `app.core.load_project_map` anywhere.

3. `app/core/self_edit_generated.py` initially flagged as a "zero inbound importer" orphan by the
   static AST scanner -- this would have been a SERIOUS misclassification (this is a real,
   load-bearing, actively-hot-loaded file, arguably one of the most important files in the whole
   self-edit subsystem). Caught by cross-referencing self_edit_manager.py directly: it is loaded
   via `importlib.util.spec_from_file_location()` against a path CONSTANT, not a static `import`
   statement -- invisible to any AST-import-graph method by construction. Corrected the write-up
   to explicitly flag this as a known false-negative class for the whole methodology, not just
   this one file (any other `importlib`-loaded file elsewhere in the codebase would have the same
   blind spot -- NOT independently re-swept for other instances of this pattern, given time
   constraints; flagged as a residual methodology gap in the final report rather than silently
   left uncaveated).

4. `WhisperOfPeace.wav` -- an early, hasty single grep returned a false "referenced in
   app/autonomous_awareness.py" result; re-run with a clean, explicit, case-insensitive grep
   immediately after found ZERO matches anywhere. Did not carry the first (wrong) result forward
   into the final report -- re-verified before writing anything down, consistent with this
   audit's own stated evidence discipline. Correct conclusion: genuinely zero live code
   references, but per the project's own well-documented history with exactly this shape of
   false-positive-on-orphan-status for large autonomously-named media files, still recommended
   FLAG-not-DELETE rather than treating "zero references" as sufficient grounds for removal.

5. Checked whether a global auth middleware (`before_request`, WSGI wrapper, Flask-Talisman,
   CORS) might be compensating for the per-route `_secret_ok()` gaps found in
   routes_echo_studio.py -- confirmed absent via direct grep of run.py. This strengthens rather
   than weakens the unauthenticated-routes finding (ruled out the most likely alternative
   explanation before finalizing it as a real gap).

6. Checked whether `GREMLIN_SECRET`'s comparison could still be trivially bypassed via an unset-
   secret edge case (the classic `None == None` vulnerability class) -- re-read the actual
   `_secret_ok()` implementation directly and confirmed it fails closed (`if not GREMLIN_SECRET:
   return False`) BEFORE the `hmac.compare_digest()` call, closing that specific bypass class.
   Did not simply assume this was fixed based on any external claim -- independently traced the
   actual conditional logic.

7. Cross-checked the "9.5MB of apparently-orphaned Bible data" finding (bible_structured.json +
   books/) by specifically searching for the ONE file that IS confirmed live
   (bible_sentiment.json) to make sure I wasn't about to flag a live file as dead by mistake --
   confirmed the two are genuinely distinct root-level files with distinct content, and only one
   has a live Python consumer. Also flagged, honestly, that this check did not extend to
   non-.py consumers (e.g. any one-time shell/ingestion script under archive_optional_files/ that
   might have originally produced bible_structured.json FROM the live source, making it a
   meaningful build-provenance artifact rather than pure noise) -- left as a stated, unresolved
   caveat rather than a confident claim either way.

## Things NOT independently re-verified in this pass, stated plainly (time-boxed choices)
- Live behavior of any autonomous loop (nothing in this audit ran the actual server or made a
  live Ollama call) -- every runtime-behavior claim in this report is inferred from static source
  reading, not observed execution. Marked [HYPOTHESIS] throughout the final report where this
  matters.
- Full git history secret-scan across all 114 commits (only current working-tree content was
  regex-scanned for secret-shaped strings).
- Exhaustive read of every one of the ~600 files under app/ -- this audit sampled heavily
  (dependency graph + targeted greps + ~25 direct file reads of the most architecturally central
  or claim-relevant files) rather than reading every file end-to-end, consistent with the
  protocol's own Phase 1/2 guidance to prioritize breadth over exhaustive reading, and the
  effort-budget realities of a single audit pass.
- Whether the network boundary (firewall/Tailscale) that would determine the real severity of the
  unauthenticated-routes finding is actually enforced on any live deployment -- explicitly out of
  scope for a git-checkout-only static audit, and stated as such rather than guessed at.
