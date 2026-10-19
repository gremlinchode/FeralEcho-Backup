# `behavioral_state.py` — Forensic Infrastructure Audit

Date: 2026-09-23. Investigator: Claude M5. Method: read-only forensic infrastructure audit — **not** a learning-claim audit. `behavioral_state.py` explicitly self-disclaims learning ("THIS IS NOT A LEARNING MECHANISM," its own module docstring, line 7), and that classification is accepted here without re-litigation. The question this mission answers is narrower and different: what exactly makes this the most rigorously demonstrated persistent-state→restart→behavior chain in FeralEcho, precisely where does that demonstration break down, and can its consumer architecture serve as a scientifically clean, provenance-agnostic pattern for a future, genuinely learning-shaped mechanism.

No production code, prompt, configuration, or persistent state was modified. `behavioral_state.py` was not touched. No component was connected to another. No experiment was run or implemented. Every claim below is labeled OBSERVED (verified directly against current source or a live artifact this mission), REPRODUCED (recomputed without mutation), RETRIEVED (traced accurately to an earlier artifact, not independently reproduced), INFERRED (a reasoned conclusion from the above), or UNKNOWN (a real, stated gap).

**Opening HEAD:** `2fba42644c82b9f7096276f4dd338d615cf1bcce`. **Closing HEAD:** `2fba42644c82b9f7096276f4dd338d615cf1bcce` — unchanged. **Working-tree delta:** a `git status --porcelain` snapshot (230 entries) was captured before this mission's first read and diffed against the same command at report-writing time; the only difference is this report's own new, untracked path. Full accounting in §19.

---

## 1. Executive verdict

**`behavioral_state.py` is real, correctly-built infrastructure that demonstrates a genuinely restart-surviving, causally-consequential state→behavior chain — but the one real live demonstration of that chain used a test-only code path that bypassed the exact production gate the candidate-tournament document flagged, and this mission's own direct trace confirms the flag was substantively correct, though not for the precise reason the tournament document's own wording implied.**

Precisely: `get_structural_self_facts()` — the single function that houses the behavioral-directive check — is itself deliberately, correctly architected so that its *internal* directive-matching logic never re-applies an introspection gate (OBSERVED, confirmed by an explicit code comment and by the union logic that widens the slice set independent of `_relevant_slices()`'s own keyword gating, §7). But this internal correctness is moot for real human conversation, because **all three real human-facing production entry points** (`app/routes_echo_studio.py`, `run.py`'s `/mirror_echo`, `terminal_client.py`) gate the *entire call* to `get_structural_self_facts(msg)` behind `_is_introspective(msg)` at the *outer* caller level (OBSERVED, direct source read, all three call sites, §7) — meaning the function is never even invoked for an ordinary-topic human message, regardless of what its own internal logic would correctly do once invoked. Only two non-human-facing, fully autonomous call sites in `app/emergent_scheduler.py` call it unconditionally.

The one real, live, quantified demonstration of this mechanism's behavioral effect (`audits/c1_live_validation_report.md`, primary evidence located and read in full, §4) is genuine and its own numbers hold up under independent re-derivation — but the test script (`scripts/validate_behavioral_state_live.py`) calls `echo_ground_truth.get_structural_self_facts(prompt)` **directly**, and separately calls the model via `river_deliberation._ollama_query()` **directly** — bypassing both the outer `_is_introspective()` gate every real human-facing entry point imposes, and the entire real production request pipeline (council deliberation, synthesis, routing) those entry points would otherwise invoke. This is classification **C** in the mission's own A/B/C framework: a test-only, direct-call path, not the real production path and not even a partially representative one for the specific claim "an ordinary human conversation mentioning a trigger word will produce this effect."

None of this makes the mechanism bad infrastructure — its persistence, restart-survival, audit-logging, and human-confirmation-gating machinery are all real, correct, and (per §12) genuinely reusable independent of provenance. It does mean the specific, oft-cited "0/2 → 2/2 → 1/2" numbers describe a real property of the *architecture in isolation*, not a demonstrated property of *real production conversations*, and the gap between those two claims is precise, quantifiable, and previously under-stated.

## 2. Files/artifacts inspected

- `app/core/behavioral_state.py` (full source, 326 lines)
- `app/core/echo_ground_truth.py` — `_is_introspective()` (lines 260–277), `_relevant_slices()` and its surrounding `_SLICE_SIGNALS`/`_SEE_HEAR_CONJUNCTION_RE` machinery (lines 1–330 read for context), `_build_behavioral()` and `get_structural_self_facts()` in full (lines 1120–1220), and the explicit code comment at lines ~40–50 distinguishing the behavioral slice's gating from every other slice's
- `app/routes_echo_studio.py` lines 100–115 (the `_is_introspective(msg)` gate around the sole `/chat/stream` call to `get_structural_self_facts`)
- `run.py` lines 560–575 (the identical gate around `/mirror_echo`'s call)
- `terminal_client.py` lines 384–395 (the identical gate around the terminal client's call)
- `app/emergent_scheduler.py` lines 660–670 and 785–795 (the two unconditional, non-human-facing autonomous call sites)
- `memory/behavioral_directives.json` (current real content: empty, `{"directives": [], "version": 1}`, read directly)
- `memory/behavioral_directives_audit.jsonl` (full content, 10 real lines, read directly — the complete real lifecycle of the one directive this mechanism has ever held: `propose_and_confirm` → 8 `read_match` events → `delete`)
- `audits/c1_live_validation_report.md` (full text, 99 lines) — the primary evidence document for the "0/2 → 2/2 → 1/2" figures
- `scripts/validate_behavioral_state_live.py` (full source, 238 lines) — the actual test harness that produced the primary evidence
- `scripts/verify_behavioral_state.py` (header and test-inventory portions read; confirmed, via its own explicit docstring, "NO LIVE MODEL CALL ANYWHERE IN THIS FILE" — an offline machinery test suite, not a behavioral demonstration)
- `audits/2026-09-19_persistent_competence_candidate_tournament.md` §6 (the "Second-New-Mechanism (`behavioral_state.py`) Deep Dive," read in full during the prior mission this audit continues from, re-consulted here for exact wording)

## 3. Evidence/provenance method

Every claim is labeled per the discipline stated above. Per this mission's explicit instruction, no earlier report's "CONFIRMED" or "VERIFIED" label was treated as itself evidence; every load-bearing claim in this report was independently re-derived from source or from the primary artifact (`c1_live_validation_report.md`/`validate_behavioral_state_live.py`), not from the candidate tournament document's own characterization of them.

## 4. Primary-evidence reconstruction

**Located, traced to the actual test harness, not merely the summary report.** `audits/c1_live_validation_report.md` is the primary evidence document; `scripts/validate_behavioral_state_live.py` is the exact code that produced it, and both were read in full this mission (§2).

**What prompts were used (OBSERVED, direct read of the harness source):** an invented trigger word, `zorbnak` (chosen specifically because it cannot occur in any real, unrelated conversation), paired with an invented, mechanically-checkable compliance marker, `FLURBWEDGE`. Nine real prompts across five phases: 2 baseline (no directive exists yet), 2 immediate (fresh subprocess, right after the directive is established), 2 restart-simulated (a separate later subprocess, freshly paraphrased, no reminder of the directive's own wording), 2 control (trigger word absent entirely), 1 near-miss (`zorbnix`, a visually similar but genuinely different invented word).

**What state was written (OBSERVED, cross-checked against the real, live audit log):** exactly one real directive, `{"trigger_keywords": ["zorbnak"], "directive_text": "When a message mentions 'zorbnak', begin your reply with the word 'FLURBWEDGE' before anything else."}`, written via the real `propose_and_confirm_directive()` function to the real `memory/behavioral_directives.json` — confirmed by this mission's own direct read of `memory/behavioral_directives_audit.jsonl`, whose first line is byte-for-byte consistent with this description, timestamp `1788472087.29...`.

**Who/what wrote it (OBSERVED):** the test script itself, calling `behavioral_state.propose_and_confirm_directive(..., human_confirmed=True)` with `provenance={"proposed_by": "gremlin_via_claude_code_session", "reason": "C1 live validation...", "mission_authorization": "explicit, detailed Phase 1 design (A-F) provided directly by the user"}` — a real, explicit, human-authorized action, not autonomous.

**Whether writing required explicit human confirmation (OBSERVED):** yes — `human_confirmed=True` is a required, literal-bool-checked parameter (`if human_confirmed is not True: raise BehavioralStateError(...)`), confirmed by direct source read of `propose_and_confirm_directive()` (§7 of the prior candidate-tournament document already established this; this mission independently re-confirmed it by reading the function body directly, not by trusting the citation).

**How persistence was implemented (OBSERVED):** atomic write (`temp file + os.replace`), no cache, fresh disk read on every `load_state()` call — confirmed directly from source, §7 below.

**What constituted restart (OBSERVED, and this is a genuinely strong methodological choice by the original test):** each phase (baseline, establish, immediate, restart-simulated, control, cleanup) was invoked as a **separate `python3` subprocess** — a fresh interpreter each time, not merely a fresh function call within one long-lived process. This is a stricter simulation of restart than most of this project's own other research artifacts use (compare: several RiverBrain-adjacent missions relied on in-process isolation techniques that this project's own Tier-8 forensic work later found to be incomplete). The harness's own stated reason for not restarting the real `run.py` Flask server is also verified directly: `_call_echo()` calls `river_deliberation._ollama_query()` directly, which talks to Ollama over HTTP with no dependency on the Flask process — a real, correct architectural fact, not merely asserted.

**What consumer read the state (OBSERVED):** `behavioral_state.get_matching_directives(prompt)`, called from inside `echo_ground_truth.get_structural_self_facts(prompt)` — but, critically, the test script (`_measure()`, line 87) calls `get_structural_self_facts(prompt)` **directly**, not through any of the three real human-facing production entry points that would normally be the thing calling it (§7 traces exactly what this means).

**What responses counted as behavioral success (OBSERVED):** `raw_response.strip().upper().startswith(COMPLIANCE_MARKER.upper())` or the marker appearing within the response's first 40 characters — a fixed, deterministic, mechanically-checkable string match, applied identically to every trial.

**Who/what evaluated those responses (OBSERVED):** the test script's own `complies = ...` line — a hardcoded Python string check, not an LLM, not a human, and not the model itself. This is a genuinely independent evaluator in the narrow structural sense (the model being tested never grades its own output).

**Whether evaluation was blind (INFERRED, not explicitly stated in either artifact):** the script computes `measurement` (including `directive_exposure`) *before* making the live call and records it in the same result dict as the eventual compliance verdict — there is no blinding mechanism separating "did we know the directive was exposed" from "did we score compliance," but since the compliance check is a fixed, deterministic string match with no room for evaluator discretion, blinding in the human-rater sense does not apply here; the more relevant question (whether the *scoring code* could have been influenced by which phase it was scoring) does not arise, since the compliance check is identical code for every phase.

**Whether sampling was deterministic (OBSERVED, and this is a real, disclosed limitation neither artifact hides):** `_ollama_query()` is called with no `temperature` override visible in the harness's own call (`_ollama_query("echo:latest", prompt, system=system_context or None, task_type="personal")`), and the primary report itself states the compliance rate "is real but probabilistic, not deterministic" — confirming, by the original investigators' own admission, that sampling was not pinned to a deterministic/greedy setting. This means the one non-compliant trial (Phase E, second prompt) cannot be distinguished, from this evidence alone, between "the model genuinely, systematically deprioritizes the directive under restart-simulated conditions" and "ordinary sampling variance happened to land on a non-compliant token sequence that trial."

**Whether controls were genuinely matched (OBSERVED, this mission's own re-derivation from the harness source, not merely the report's characterization):** the control phase (F) prompts (asking about gardening/weather) and the near-miss phase (F2, `zorbnix`) are run through the identical `_measure()`→`_call_echo()`→compliance-check pipeline as every other phase — genuinely matched code path, differing only in prompt content, which is the correct control design.

**Whether the claimed numbers are accurately represented by later reports (REPRODUCED, this mission):** yes, exactly. The candidate-tournament document's "0/2 baseline, 2/2 immediate, 1/2 post-restart-paraphrase" figures match this mission's own direct re-read of the primary table row-for-row: Phase A = 2/2 non-compliant (0% compliance), Phase C = 2/2 compliant, Phase E = 1/2 compliant, Phase F/F2 = correctly non-matching throughout. **No discrepancy found between the primary report and its later citation** — the discrepancy this mission does find is not in the numbers, but in what production-reachability claim those numbers can support (§6, §7).

## 5. Full data-flow map

```
HUMAN CONFIRMATION / EVENT          A human (this test: a Claude Code
        │                            session, per explicit user authorization)
        │  (OBSERVED — provenance dict recorded verbatim)
        ▼
WRITE                                propose_and_confirm_directive(
        │                              human_confirmed=True, ...)
        │  (OBSERVED — refuses hard on anything but the literal bool True;
        │   confirmed by direct source read, §7 below)
        ▼
PERSISTENT ARTIFACT                  memory/behavioral_directives.json
        │                            (atomic write; memory/behavioral_
        │                             directives_audit.jsonl logs the
        │                             mutation with full provenance)
        │  (OBSERVED)
        ▼
PROCESS RESTART                      A fresh python3 subprocess
        │  (OBSERVED, real, in the C1 validation — a genuinely stronger
        │   restart simulation than an in-process reimport)
        ▼
READ                                 behavioral_state.get_matching_directives(
        │                              prompt) — fresh disk read, deterministic
        │                              exact-substring keyword match
        │  (OBSERVED — no cache anywhere in the read path)
        ▼
PROMPT/CONSUMER                      echo_ground_truth.get_structural_self_facts(
        │                              prompt) → _build_behavioral(matches)
        │  (OBSERVED — internally correct: evaluated independent of
        │   _is_introspective(), by explicit design, §7)
        │
        │  ██████ GATE, OUTER CALLER LEVEL ██████
        │  All 3 real human-facing entry points (routes_echo_studio.py,
        │  run.py's /mirror_echo, terminal_client.py) call
        │  get_structural_self_facts(msg) ONLY IF _is_introspective(msg)
        │  is first true — CONFIRMED by direct source read of all three
        │  call sites, §7. The C1 live-validation harness bypasses this
        │  gate entirely by calling get_structural_self_facts() directly.
        │  Only app/emergent_scheduler.py's two autonomous call sites
        │  call it unconditionally.
        ▼
MODEL GENERATION                     river_deliberation._ollama_query(
        │                              "echo:latest", prompt, system=...)
        │  (OBSERVED, in the C1 validation — but this is ALSO a direct,
        │   test-only call, bypassing the real production request
        │   pipeline — deliberation/synthesis/routing — that the 3 real
        │   human-facing entry points would otherwise use)
        ▼
OBSERVABLE BEHAVIOR                  Response text, checked for the
        │                            invented compliance marker
        ▼
EVALUATION                           A fixed, deterministic string-match
                                      function in the test script itself
                                      (independent of the model, not
                                      independent of the code being tested
                                      in the sense that it was written by
                                      the same session that ran the test)
```

**For every arrow, per the mission's explicit checklist:**

- **Exact source location:** given inline above and in §2/§7.
- **Whether production uses it:** WRITE/PERSISTENCE/READ — yes, unconditionally, this is real production machinery with no test-only substitute anywhere. PROMPT/CONSUMER's *internal* logic — yes, real production code. The OUTER GATE and MODEL GENERATION step — **no**, the live validation used a direct-call bypass at exactly these two points (§6, §7).
- **Whether experimental tests used the same path:** partially — WRITE through READ, yes, identically; PROMPT/CONSUMER's internal logic, yes, identically (the harness calls the real function); the outer gate and the real request pipeline, no.
- **Whether any gate/filter lies between components:** yes, precisely one that matters — the outer `_is_introspective()` check at the three human-facing call sites, which does not exist between `get_structural_self_facts()` and its own internal `_build_behavioral()` call (§7).
- **Whether any step can silently fail:** yes, by design and documented as intentional — `load_state()`, `get_matching_directives()`, and the `try/except` wrapping `behavioral_state` import inside `get_structural_self_facts()` all fail closed to empty/no-effect on any error, never raising into the caller (OBSERVED, direct source read).
- **Whether any component substitutes live information for stored information:** no — unlike `self_model_claims.py`'s consumer (which re-resolves a "current fact" live from `self_model.json` rather than trusting the stored record, per this mission's prior sibling audit), `_build_behavioral()` renders the stored `directive_text` verbatim, with no live re-derivation of any kind.
- **Whether state provenance is retained:** yes, fully — the `provenance` dict is required, non-optional, and persisted verbatim alongside the directive and in the separate audit log (OBSERVED).

**Minimum subset actually responsible for the observed behavioral effect (this mission's own synthesis, INFERRED from the above):** `propose_and_confirm_directive()` → `memory/behavioral_directives.json` → `get_matching_directives()` → `get_structural_self_facts()`'s internal (non-introspection-gated) union logic → `_build_behavioral()` → the model's own context-following behavior. **The outer `_is_introspective()` gate and the real production request pipeline (council/synthesis) are not part of this minimum subset, and were not exercised by the one real demonstration that exists.**

## 6. Production reachability analysis

**Direct question: would the reported behavioral consequence still be reachable during an ordinary real production conversation?**

**Answer: only under a narrow, specific conjunction of conditions, or via a path never tested by the live validation at all.**

For the three real human-facing entry points: **no**, not for an ordinary message mentioning a directive's trigger keyword, unless that same message is *also* independently classified as introspective by `_is_introspective()`. Since `_is_introspective()` (§7) matches phrases about Echo's own internal state, architecture, or self-referential questions — a category with essentially no overlap with an arbitrary directive's trigger keywords (the test directive's own trigger, "zorbnak," or a realistic real-world trigger like a project codename or a person's name, would not typically co-occur with an introspective framing) — this conjunction would be rare to the point of practical non-occurrence for most plausible real directives. **Under what exact conditions would it fire?** A message that is simultaneously about Echo's own nature/architecture *and* happens to mention the directive's trigger keyword — e.g., "does your self-edit pipeline know anything about zorbnak" would satisfy both conditions; "tell me about zorbnak" alone would not reach `get_structural_self_facts()` at all through any of the three human-facing routes. **How often would those conditions plausibly occur?** This mission did not find, and did not attempt to construct, any empirical estimate of this joint rate — it is INFERRED to be low based on the semantic disjointness of the two keyword sets, but this is a qualitative judgment, not a measured one.

For the two autonomous, non-human-facing call sites in `app/emergent_scheduler.py`: **yes, unconditionally** — these call `get_structural_self_facts(prompt)` with no `_is_introspective()` check at all (OBSERVED, direct source read). A directive whose trigger keyword happens to appear in Echo's own autonomously-generated reflection/scheduling prompt text would reach the full chain, including a real model call, entirely outside any human conversation. **Whether this ever has, in the real, live production system's history, actually occurred is UNKNOWN** — this mission did not search `memory/reflection_journal.jsonl` or the scheduler's own prompt-history logs for the one real directive's now-deleted trigger keyword, since doing so would require either importing a FeralEcho module or searching a large log file outside this mission's necessary scope; flagged as a concrete, cheap follow-up rather than performed here.

## 7. `_is_introspective()` gate analysis

**All consumers/callers of `get_structural_self_facts()`, enumerated exhaustively via direct repo-wide grep, this mission (not retrieved from any prior characterization):**

| Caller | File:line | Gated by `_is_introspective()`? |
|---|---|---|
| `/chat/stream` (Echo Studio) | `app/routes_echo_studio.py:110-112` | **Yes** — `if _is_introspective(msg): ground_truth = get_structural_self_facts(msg)` |
| `/mirror_echo` (phone symbiote channel) | `run.py:569-571` | **Yes** — identical shape: `get_structural_self_facts(msg) if _is_introspective(msg) else ""` |
| Terminal client | `terminal_client.py:390-392` | **Yes** — identical shape |
| `emergent_scheduler.py`'s reflection cycle | `app/emergent_scheduler.py:667-668` | **No** — unconditional call |
| `emergent_scheduler.py`'s second autonomous call site | `app/emergent_scheduler.py:793-794` | **No** — unconditional call |
| `archive_janitor/echo_self_probe.py` (a retired diagnostic, not a live production caller) | lines 65, 91 | Calls with `prompt=""` (all slices) or a caller-supplied prompt directly — not a real production path either way |
| `scripts/validate_behavioral_state_live.py` (the C1 live-validation harness) | line 87 | **No** — calls `get_structural_self_facts(prompt)` directly, with no gate |
| `scripts/verify_behavioral_state.py` (the offline machinery test suite) | lines 389, 393, 396 | Calls directly with varied prompts to test the function's own slice-selection logic in isolation — not a production path, and explicitly makes no live model call at all |

**Reconstructing the historical behavioral-state experiment against this table (OBSERVED, direct comparison of the harness source against the table above): it exercised path C — a test-only/direct-call path that bypassed production gating — at two distinct points, not one.** First, it bypassed the outer `_is_introspective()` gate by calling `get_structural_self_facts()` directly rather than through any of the three real, gated, human-facing entry points. Second, and separately, it bypassed the entire real production request pipeline (`deliberate_and_learn()`'s council deliberation and synthesis) by calling `river_deliberation._ollama_query()` directly for the model response — a real, single-model, non-council call, whereas a real Echo Studio conversation would ordinarily route through council deliberation for most task types (RETRIEVED from this project's own extensive prior documentation of `river_deliberation.py`'s architecture, not independently re-verified this mission for the specific `task_type="personal"` the harness used, which per this project's own well-documented `DIRECT_ECHO_TASKS` bypass would in fact route to a single-model call in real production too — so this second bypass is less consequential than it might first appear, and is noted here for completeness rather than as an additional, equally-weighted gap).

**What exactly does `_is_introspective()` change about the conclusion?** It does not change whether the *architecture itself* works — §5's minimum-subset analysis and the harness's own `directive_exposure` measurement (100% correct across all 9 trials) establish that the write→persist→read→internal-render chain is completely reliable, independent of `_is_introspective()`, exactly as the code comment at `echo_ground_truth.py`'s top claims. What it changes is the **claim about real production reachability**: the demonstrated 2/2 → 1/2 compliance results describe what happens *once `get_structural_self_facts()` is actually called* — a precondition that, for the three real human-facing entry points, requires the triggering message to *also* be independently classified introspective. The live validation's own `directive_exposure=True` measurements are real and correct **for the function call it actually made**; they say nothing about whether that function call would have happened at all had the same 9 prompts been sent through the real, gated, human-facing pipeline instead of directly.

## 8. Causality analysis

**Does existing evidence establish that the persisted behavioral state *caused* the later behavior, as opposed to some fixed/non-state explanation?**

The C1 validation's own design already includes several of the mission's requested controls, and this mission independently re-verifies each:

- **State present vs. absent ablation:** yes, genuinely present — Phase A (baseline, no directive exists) vs. Phase C/E (directive exists) is exactly this comparison, and it shows a clean 0/2 → 3/4 shift (OBSERVED, re-derived from the primary table).
- **Matched negative controls:** yes — Phase F (trigger word entirely absent) correctly shows `state_retrieval=False`/`directive_exposure=False` in both trials, and Phase F2 (the near-miss `zorbnix`) correctly shows the same, confirming the match is genuinely keyword-exact, not fuzzy or coincidental (OBSERVED).
- **Pre/post comparison:** yes, Phase A vs. Phase C, as above.
- **Restart control:** yes, genuinely — Phase E used a separate later subprocess with freshly-paraphrased prompts (OBSERVED, re-derived from the harness source, §4).
- **Paraphrase control:** yes — Phase E's two prompts are phrased entirely differently from Phase C's, and neither repeats the directive's own wording (OBSERVED, direct comparison of the actual prompt strings in the harness source).
- **Unrelated-topic control:** yes — Phase F.
- **Instruction-conflict control:** **not found** — no trial pits the directive against a competing, contradictory instruction to see which one the model actually follows; this specific control does not exist in the primary evidence.
- **Evidence behavior occurs without the state:** yes — Phase A, 2/2 non-compliant, confirming the compliance marker is not something the model would produce spontaneously.
- **Evidence state exists but behavior fails to follow it:** yes — Phase E's second trial (`directive_exposure=True`, `actual_behavioral_compliance=False`) is exactly this case, and the primary report treats it honestly as a real, unresolved instance of imperfect compliance rather than explaining it away.

**Strongest fixed/non-state explanation compatible with the observations, constructed per the mission's own instruction:** a hand-authored, static system-prompt rule of the exact shape `_build_behavioral()` renders — "if the word 'zorbnak' appears in the user's message, begin your reply with 'FLURBWEDGE'" — injected via ordinary prompt engineering with **no `behavioral_state.py` mechanism at all**, would be observably indistinguishable from the real mechanism's behavior in every one of the 9 real trials, because the rendered text the model actually sees is, in both cases, an explicit, human-authored, verbatim instruction. **The instrument this mission is auditing does not, and does not claim to, produce a different downstream instruction than a human directly writing the same rule into a static system prompt would.** What the real mechanism adds over this counterfeit is not a different *effect on the model*, but real *infrastructure properties around* that effect: restart-survival without needing a code deploy to add/remove the rule, a bounded and audited store, human-confirmation enforcement, and rollback — all real, all independently valuable, and all orthogonal to whether the underlying behavioral effect itself required anything beyond ordinary instruction-following.

**Does existing evidence establish causation, per the mission's exact question?** For the narrow claim "does an exposed, human-written instruction measurably raise the probability of the specified compliant behavior over baseline" — **yes**, cleanly, at n=4 for the treated cells and n=2/n=2/n=1 for the negative controls, small but genuinely controlled. For the broader claim "does the *behavioral_state.py mechanism specifically*, as opposed to any equivalent way of getting the same instruction in front of the model, cause anything beyond what a static prompt engineering rule would" — **no**, and this mission does not find that the primary evidence claims otherwise; the primary report's own classification ("persistent, state-mediated behavioral conditioning... not L2 learning") is consistent with this reading, not contradicted by it.

## 9. Content-vs-machinery decomposition

| Element | Classification |
|---|---|
| The specific rule "if 'zorbnak' appears, say 'FLURBWEDGE' first" | **CONTENT** — human-authored, arbitrary, carries zero generality |
| `human_confirmed=True` gating | **Provenance-specific machinery** — enforces *who* may write, not *how* writing/persistence works |
| Atomic write-to-temp-then-`os.replace` | **Generic persistence machinery** — provenance-agnostic; identical code would work for any writer |
| `_backup_current_state_before_mutation()` / rollback | **Generic persistence machinery** — provenance-agnostic |
| The append-only audit log (`_append_audit()`) | **Generic persistence machinery**, with a **provenance-specific payload** — the mechanism (append a JSON line) is generic; the fields it records (`human_confirmed`, `provenance` dict) are shaped around the human-confirmation use case, but nothing in the write path *requires* those specific field names to remain human-shaped |
| Fresh-disk-read-every-call, no cache | **Generic persistence/consumer machinery** — provenance-agnostic |
| Deterministic exact-substring keyword matching (`get_matching_directives()`) | **Generic consumer machinery** — the matching logic has no idea whether the stored text originated from a human or anything else |
| `_build_behavioral()`'s disclaimed rendering ("human-confirmed instructions, not something Echo learned or recalls") | **Provenance-specific machinery**, specifically the *wording* of the disclaimer — the rendering *function itself* (take stored text, prepend a framing sentence, join with newlines) is generic; only the literal disclaimer string is human-provenance-specific |
| The bypass of `_is_introspective()` for this slice specifically | **Generic consumer-architecture design choice** — a decision about when a slice is relevant to inject, unrelated to who or what produced the slice's content |
| Bounds (`MAX_DIRECTIVES=20`, `MAX_TRIGGER_KEYWORD_LEN=60`, etc.) | **Generic machinery** — provenance-agnostic size/count limits |
| The model's own compliance behavior (context-following) | **Model-native instruction following** — not part of this module's machinery at all; a property of the underlying LLM |

**We care primarily about the machinery, per the mission's own framing — and the overwhelming majority of it is genuinely provenance-agnostic.** The only elements that are load-bearing on "a human specifically confirmed this" are: the single `human_confirmed is not True: raise` guard clause inside each of the three mutator functions, and the literal wording of one disclaimer string inside `_build_behavioral()`. Everything else — atomic persistence, restart survival, deterministic retrieval, bounded storage, audit logging, and the deliberate non-gating-on-introspection design — has no dependency on the writer's identity or nature.

## 10. Provenance-agnostic consumer analysis (DESIGN/ANALYSIS ONLY)

**Could the same downstream consumer machinery accept state whose provenance was (A) explicit human confirmation, (B) a deterministic independent evaluator, (C) a sandbox pass/fail outcome, or (D) another trusted machine-derived outcome, without changing the fundamental consumer architecture?**

**Yes, and the interface contract that makes this possible is precise and narrow: `get_matching_directives()` and `_build_behavioral()` consume exactly two fields per record — `trigger_keywords: list[str]` and `directive_text: str` — and neither function reads, checks, or branches on any other field, including `provenance` itself** (OBSERVED, direct source read: `get_matching_directives()`'s loop only ever accesses `directive["trigger_keywords"]`; `_build_behavioral()` only ever accesses `d['directive_text']`). The `provenance` dict is required at *write* time (`propose_and_confirm_directive()` refuses a falsy/non-dict provenance) and is *persisted* alongside the directive, but it is never *read* by anything on the consumption side of the chain. **Provenance is metadata attached upstream of the interface the consumer actually depends on, not a property the consumer's logic branches on.**

This means: a record written by a deterministic evaluator (option B — e.g., a claim that passed the same kind of rule-engine check `self_knowledge_verification.py` already performs), a real sandbox pass/fail outcome (option C — e.g., a code pattern confirmed, via F2, to reliably solve a class of task), or another trusted machine-derived outcome (option D) could, in principle, be written into an identically-shaped record (`{trigger_keywords, directive_text, provenance, created_at}`) and consumed by the exact same `get_matching_directives()`/`_build_behavioral()` code, with **zero change to either function**, provided the writer supplies a `provenance` dict describing the real origin honestly (this module's own write-time validation only checks that `provenance` is a non-empty dict — it does not, and structurally cannot, verify that a caller's *claimed* provenance is truthful; see §11's counterfeit analysis for why this matters).

**If provenance matters, identify exactly where and why:** it matters at exactly one point — the three `human_confirmed is not True: raise` guard clauses. These are a **policy decision about who may write**, not a property of the storage/retrieval/rendering machinery itself. A machine-derived-evidence variant of this same architecture would need its own, differently-shaped gate (e.g., "was this evaluated by an independent, non-self-referential checker" rather than "did a literal human confirm this"), but that gate could be swapped in at exactly the same three call sites, with the rest of the module (§9's "generic machinery" rows) completely unchanged.

**One real, load-bearing caveat this mission surfaces, not present in the mission's own framing:** `_build_behavioral()`'s disclaimer text is currently hardcoded to say "human-confirmed instructions, not something Echo learned or recalls." If this same consumer machinery were ever fed machine-derived-evidence records without also changing this literal string, the model would be told something false about the content's own provenance — a real, concrete integration risk for any future extension of this pattern, not a defect in the current, honest, human-only implementation.

## 11. Counterfeit analysis

**Smallest non-learning counterfeit capable of reproducing the reported behavioral-state result:** a static system prompt, hardcoded into `echo_ground_truth.py` (or even simpler, a fixed Python dict of `{keyword: instruction}` pairs checked with the identical `in lowered` substring test `get_matching_directives()` already uses), with no `propose_and_confirm_directive()`, no JSON file, no audit log, and no restart-survival mechanism beyond "the code itself is on disk and gets re-read every time the module is imported, same as any other Python source file." This counterfeit would produce **byte-identical model-facing prompt text** to the real mechanism for the one real trigger/directive pair this mission has evidence for, and therefore would be expected to reproduce the identical 0/2 → 2/2 → 1/2 result, since the model's compliance behavior depends only on what text it sees, not on how that text was stored upstream.

**What, if anything, does `behavioral_state.py` demonstrate beyond this counterfeit?** Exactly the properties enumerated in §9 as "generic machinery": the ability to *add or remove* a directive without a code deployment; a bounded, auditable, rollback-capable store; and an enforced human-confirmation gate that a hardcoded system prompt has no equivalent of (a hardcoded prompt is implicitly "confirmed" the moment a human commits the code change, but there is no explicit, logged, per-instruction confirmation record the way `propose_and_confirm_directive()` produces one). **These are real, valuable, operational properties — genuinely different from, and better than, editing source code by hand every time a new instruction is wanted — but they are properties of a *deployment/operations* mechanism, not evidence of anything beyond instruction-following.**

**Per the mission's own explicit instruction: a mechanism can be excellent infrastructure while demonstrating zero learning, and it should not be penalized for correctly being infrastructure.** This audit does not penalize it on that basis. §12 addresses what is genuinely reusable, on its own terms, without demanding it be more than what it honestly is.

## 12. Reusable primitive inventory

| Primitive | Demonstrated in production | Demonstrated experimentally only | Merely implemented | Untested | Broken/unreachable |
|---|---|---|---|---|---|
| **1. Safe write** (`_atomic_write_json`, temp+`os.replace`) | — | — | ✓ (real production writes have only ever occurred during the one C1 validation and its cleanup) | — | — |
| **2. Provenance preservation** (required, persisted `provenance` dict) | — | ✓ (the one real record's provenance is real and was independently confirmed this mission, §4) | — | — | — |
| **3. Persistence** (`memory/behavioral_directives.json`, flat JSON, no cache) | — | ✓ (real file, real ten-day-plus-since-2026-09-03 lifespan per the backup directory's own timestamp, §2) | — | — | — |
| **4. Restart survival** | — | **✓ — the single strongest-demonstrated primitive of the seven**, via a genuine separate-subprocess test (§4) | — | — | — |
| **5. Retrieval** (`get_matching_directives`, deterministic keyword match) | — | ✓ (demonstrated live, correctly discriminating exact match from near-miss, §4) | — | — | — |
| **6. Behavioral consumption** (`_build_behavioral` → `get_structural_self_facts` → generation) | — | **Demonstrated experimentally only via a test-only bypass path (§6, §7) — not demonstrated in real production, and, per this mission's own analysis, essentially unreachable through the three real human-facing entry points for an ordinary-topic directive** | — | — | (not broken — reachable, just gated to near-zero real-world frequency for human-facing use; genuinely unconditional and reachable for the two autonomous `emergent_scheduler.py` call sites, whose real-world firing rate is UNKNOWN, §6) |
| **7. Causal measurability** (the four-way separated measurement discipline: `state_existence`/`state_retrieval`/`directive_exposure`/`actual_behavioral_compliance`) | — | **✓ — this is itself a genuinely reusable methodological primitive**, independent of `behavioral_state.py`'s own content: any future mechanism claiming a persistence→behavior chain could adopt this exact four-way decomposition to avoid conflating "the architecture worked" with "the model complied" | — | — | — |

**Nothing in this table is production-demonstrated** — every real, live exercise of this mechanism to date has been a deliberate, human-run validation or test, not an organic real-conversation occurrence (consistent with the real store currently holding zero directives, §2). This is not itself a criticism of the mechanism's design; it is a factual statement about its actual usage history to date.

## 13. Weaknesses/failure modes

1. **The production-reachability gap itself (§6, §7)** — the single most consequential weakness this mission found: the demonstrated behavioral effect is real for the code path tested, and that code path is not the one an ordinary real conversation would traverse.
2. **No instruction-conflict control** (§8) — untested whether a directive reliably wins against a competing instruction elsewhere in context.
3. **Non-deterministic sampling in the one live test** (§4) — the single non-compliant trial cannot be cleanly attributed to a systematic restart/paraphrase effect versus ordinary sampling variance, since temperature/seed were not pinned.
4. **The disclaimer-text risk for future provenance extension** (§10) — a hardcoded "human-confirmed... not learned" string that would become false if this consumer architecture were ever reused for machine-derived evidence without updating it.
5. **No liveness-ledger check exists for this module at all** (RETRIEVED from the prior candidate-tournament document's own finding, independently plausible given this mission's own grep of `liveness_ledger.py`'s check names not surfacing any `behavioral_state`-named entry — not independently re-confirmed by a full read of `liveness_ledger.py`'s complete check list this mission, flagged as RETRIEVED rather than OBSERVED) — a real gap relative to this project's own stated standard that every subsystem gets a ground-truth check, and specifically relevant here because nothing currently monitors whether the production-reachability gap this audit found ever silently worsens or improves.
6. **The mechanism's real production usage to date is exactly one test directive, created and deleted within roughly three minutes** (OBSERVED, from the real audit log's own timestamps: `1788472087` write, `1788472247` delete — a 160-second real lifespan) — meaning there is no real, organic, non-test usage history to examine at all.
7. **`n=4` for the treated trials, `n=2`/`n=2`/`n=1` for the three negative-control conditions** (§4, §8) — small enough that the primary report's own honest framing ("75% should be read as a real, honest first measurement, not a precise rate") should be taken at face value; this mission agrees with that self-assessment and does not find grounds to treat the figure as more precise than the original investigators themselves claimed.

## 14. Learning-loop component inventory

Per Mission 9's instruction, using only already-existing FeralEcho mechanisms and evidence recovered across this session's own prior archaeology (this session's `2026-09-23_feralecho_second_pass_deep_research_archaeology.md` and `2026-09-23_self_model_claims_adversarial_learning_audit.md`, both RETRIEVED and treated as this mission's own prior direct findings, not re-verified from scratch a third time where already independently established):

| Link | Candidate component | Status | Strongest existing evidence |
|---|---|---|---|
| **EXPERIENCE** | Real conversational turns; real F2 sandbox executions; real self-edit generation attempts; real council deliberations | **OBSERVED WORKING** | This project's own extensive, multi-thousand-entry `interaction_log.jsonl`/`self_edit_attempt_ledger.jsonl` history (RETRIEVED, this session's prior archaeology) |
| **INDEPENDENT EVALUATION** | Real F2 sandbox pass/fail (deterministic, non-LLM); `self_knowledge_verification.py`'s deterministic rule engine (this session's own sibling audit, OBSERVED); `code_verification.py`'s sandbox-execution-based checker | **OBSERVED WORKING**, for the sandbox-execution shape specifically — this is the one evaluator class this project has repeatedly, independently confirmed is not self-referential, not model-graded, and has the highest real observation volume of any candidate (RETRIEVED, this session's own archaeology and sibling audit) | `sandbox/echo_sandbox.sb` + `run_sandbox_script_isolated()`, real, high-volume, independently confirmed across multiple prior forensic missions (RETRIEVED) |
| **RETAINED CHANGE** | RiverBrain `model_task_stats`; `self_model_claims.jsonl`; `behavioral_directives.json`; `self_edit_attempt_ledger.jsonl` | **OBSERVED WORKING**, for simple append/mean-update persistence generally — but see the weakest-link discussion below for which of these is *causally consumed correctly* | Multiple independently-confirmed real, growing, restart-surviving files across this session's own prior work |
| **RESTART/CONTEXT BOUNDARY** | `behavioral_state.py`'s genuine separate-subprocess test (this mission, §4); RiverBrain's pickle (real but carries a known writer-thread contamination risk, RETRIEVED, Tier-8); `self_model_claims.py`'s trivial fresh-disk-read (this session's sibling audit, OBSERVED) | **OBSERVED WORKING**, best-demonstrated by `behavioral_state.py` specifically (this mission's own primary-evidence reconstruction, §4) — this is `behavioral_state.py`'s clearest genuine "best in class" property among all candidates surveyed across this research arc | `c1_live_validation_report.md`, this mission's own re-verification |
| **BEHAVIORAL CONSUMER** | `behavioral_state.py`'s `_build_behavioral()` (real, but production-unreachable for ordinary human topics, this mission, §6/§7); `self_model_claims.py`'s `_build_self_model_claims()` (real, gated the same way, this session's sibling audit); RiverBrain's `score_model()` (real, unconditionally reachable, RETRIEVED, this session's archaeology) | **PARTIALLY DEMONSTRATED** across every candidate — the one unconditionally-production-reachable consumer (RiverBrain's `score_model()`) is fed by a self-referential evaluator for its dominant-volume path (RETRIEVED); the two consumers fed by genuinely independent evaluators (`self_model_claims.py`, `behavioral_state.py`) are both gated to near-unreachability for ordinary human conversation (this mission + sibling audit) | See individual mechanism audits |
| **HELD-OUT TEST** | Frozen persistent-competence protocol v1.1's E2/E3/E5 partitions (design-only, never executed, RETRIEVED, this session's archaeology); E5-mini's P/E/N/Z arm design (design-only, never qualified for a real model run, RETRIEVED) | **DESIGNED BUT UNBUILT** | `audits/2026-09-20_persistent_competence_frozen_protocol_v1_1.md` §5 (RETRIEVED) |
| **INDEPENDENT OUTCOME MEASUREMENT** | Frozen protocol v1.1's oracle (`ORC-1`–`ORC-4`, deterministic sandbox-based, design-only, RETRIEVED); real F2 sandbox execution as already used in production self-edit (OBSERVED WORKING, narrower scope than the frozen design) | **PARTIALLY DEMONSTRATED** — the production-scale version (F2) is real and working but narrow (code correctness only); the general-purpose, multi-task-family version (the frozen protocol's oracle) is fully designed and never run | This mission's own read of the frozen protocol (RETRIEVED, prior mission) |
| **REPEATED ACCUMULATION** | Frozen protocol v1.1 §12's `[LONG-1]`–`[LONG-8]` longitudinal design (design-only, never run, RETRIEVED); RiverBrain's `_MEAN_EFFECTIVE_WINDOW=200` EMA (real but makes staged-vs-continuous accumulation indistinguishable below that threshold, RETRIEVED) | **DESIGNED BUT UNBUILT**, with one real, working, but weak analog (RiverBrain's own mechanical, unvalidated accumulation) | `audits/2026-09-20_persistent_competence_frozen_protocol_v1_1.md` §12 (RETRIEVED) |
| **Dormant/candidate infrastructure not yet in the chain at all** | `river.bandit` (confirmed still unused anywhere in the repo, this session's own direct grep, OBSERVED); Rung-1/`accumulation_probe`'s hidden-test evaluator (currently active, per this session's own carried-forward context, RETRIEVED not independently re-verified this mission); the frozen protocol v1.0's counterfeit-learner exploit and its v1.1 fix's null/positive-control statistical machinery (`[QUAL-4]`, RETRIEVED, this session's prior archaeology) | See individual entries | — |

## 15. Missing-link analysis

**The single, precisely-identifiable missing link across the entire inventory, per this mission's own synthesis:** an evaluator that is **both** genuinely independent (in the structural sense `self_knowledge_verification.py`/F2-sandbox-execution already achieve) **and** feeds a consumer that is **unconditionally reachable in real production conversation** (in the sense only RiverBrain's `score_model()` and `emergent_scheduler.py`'s autonomous calls currently are). Every mechanism surveyed across this research arc has one property or the other, never both simultaneously:

- RiverBrain's `score_model()`: unconditionally reachable, but its dominant-volume feeding evaluator (`learn()`) is self-referential.
- `self_model_claims.py` / `behavioral_state.py`: genuinely independent evaluators (or, for `behavioral_state.py`, a genuine human-confirmation gate functioning as an evaluator-equivalent), but both consumers are gated to near-unreachability for ordinary human-facing conversation.
- The frozen protocol's oracle and the F2 sandbox: genuinely independent, and reachable *within their own narrow scope* (real self-edit code generation), but never wired into a held-out, repeated-accumulation test at any scale.

This is the same underlying gap this session's prior archaeology mission already named from a different angle (RiverBrain's disconnected-reward-wire finding) — this mission's own independent route to it, via `behavioral_state.py`'s reachability analysis specifically, converges on the identical structural diagnosis.

## 16. Minimum complete experiment — DESIGN ONLY, not implemented, not run

Per Mission 11's instruction to prefer recombination over invention, and using the strongest already-existing components identified in §14:

**Experience:** real F2 sandbox pass/fail outcomes on a fixed, narrow class of task (mirroring the frozen protocol v1.1's own already-designed `list_aggregation`/`string_transformation`/`dict_lookup_merge` capability families, §14's `HELD-OUT TEST` row — reused by citation, not reinvented).

**Independent evaluation:** the same deterministic, non-LLM sandbox oracle already proven at production scale (F2), extended (design-only, per the frozen protocol's own already-specified `[ORC-1]`–`[ORC-4]`) with the frozen protocol's own already-designed hidden-test/grader-manifest-hash discipline, so the evaluator cannot be gamed by a candidate that has seen the expected outputs.

**Retained change:** a fresh, `behavioral_state.py`-shaped carrier — not `behavioral_state.py` itself (this experiment does not connect anything to that module, per this mission's own strict scope, and per the persistent-competence design lineage's own explicit recommendation to build a *fresh*, differently-provenanced carrier rather than repurpose a human-confirmation-gated one) — using the **identical machinery** §9/§10 identified as provenance-agnostic: atomic write-to-temp, no cache, fresh-disk-read-every-call, bounded size, full audit logging. The only change from `behavioral_state.py`'s own code is which gate replaces `human_confirmed is not True: raise` — here, `oracle_verdict is not True: raise` (i.e., only a record whose associated sandbox execution genuinely passed may ever be written).

**Restart/context boundary:** `behavioral_state.py`'s own already-proven separate-subprocess methodology (§4), reused verbatim as a testing pattern, not as a shared module.

**Behavioral consequence:** a consumer function structurally identical to `_build_behavioral()` (read two fields, render an explicit, disclaimed instruction block) — but, critically, **wired to fire unconditionally on every relevant task-typed request**, the way `emergent_scheduler.py`'s two autonomous call sites already do, rather than gated behind `_is_introspective()` — closing exactly the reachability gap §6/§7 of this report identify as `behavioral_state.py`'s own real-world weak point.

**Held-out transfer:** the frozen protocol v1.1's own already-designed E2 (same family, new task)/E3 (surface-changed)/E5 (structurally novel) partitions, reused by direct citation of their existing specification rather than redesigned.

**Independently measured improvement:** the frozen protocol's own already-specified paired McNemar/permutation statistical machinery (`[STAT]`, `[HYP-C1]`–`[HYP-C6]`), reused rather than reinvented.

**Second learning episode / additional retained improvement:** the frozen protocol's own already-designed `[LONG-1]`–`[LONG-8]` longitudinal accumulation design (§12 of that protocol), reused by citation.

**Distinguishing this from every named alternative, per the mission's own list:**
- *Fixed policy / prompt-context adaptation:* ruled out by the frozen protocol's own already-designed EMPTY/NEUTRAL/POISON context-ablation arms (`[ARM-14]`–`[ARM-18]`), reused directly.
- *Retrieval:* ruled out by the frozen protocol's own already-designed exemplar-vs-retrieved-episodic-memory distinction (RETRIEVED from the prior zero-cost-ceiling adversarial review's E2 design, cited by name, not reproduced here).
- *Bookkeeping:* ruled out specifically by requiring the held-out transfer step to show a *held-out task* pass-rate improvement, not merely a growing count — the same distinction §11 of this report's own §8-causality analysis already applies to `behavioral_state.py` itself.
- *Model-native capability / evaluator leakage / selection effects / memorization:* all addressed by the frozen protocol's own already-designed control battery (`[QUAL-2]`'s sandbox exploit tests, `[QUAL-4]`'s null-effect calibration and positive-control power check) — reused wholesale, not redesigned.
- *The known v1.0 counterfeit learner (the alphabetical tie-break exploit):* explicitly avoided by reusing v1.1's own already-fixed HMAC-keyed tie-break (`[TIE-1]`/`[TIE-2]`), cited by name, not reimplemented here.

**Genuinely new component this design cannot avoid, stated explicitly rather than silently designed:** the "unconditional, non-introspection-gated behavioral consumer wired to fire on every relevant task-typed request" is a real, new wiring decision — every existing FeralEcho consumer that is unconditionally reachable (RiverBrain's `score_model()`, `emergent_scheduler.py`'s two calls) either has a contaminated evaluator or is non-human-facing; every consumer fed by a clean evaluator is currently gated. **No existing FeralEcho code today combines "clean evaluator" with "unconditionally reachable, human-facing consumer" — this specific combination would need to be built, even though every other piece of this experiment is pure recombination of already-existing, already-designed components.** This is named explicitly, per the mission's instruction, rather than glossed over as if it were also pure recombination.

**This experiment is specified but not run, per this mission's explicit scope.**

## 17. Ranked next three research actions

1. **Measure the real joint-occurrence rate of `_is_introspective()` firing alongside an arbitrary keyword-shaped signal, using already-existing production logs (`interaction_log.jsonl`), read-only, with no code change.**
   - *Question:* how often, in real historical production conversation, would a message plausibly satisfy both an introspective classification and an arbitrary topical trigger — i.e., is §6's "essentially never" INFERENCE actually correct, or is it a real, non-negligible fraction of real traffic?
   - *Information value:* high and cheap — this single measurement would convert this report's own qualitative "rare" claim (§6) into an actual number, directly sharpening exactly the reachability gap this mission's central finding depends on.
   - *Prerequisite:* none beyond read access to the existing log.
   - *Research risk:* very low — purely observational, no model call, no state mutation.
   - *Code changes required:* none.
   - *Positive result (a real, non-negligible joint rate found):* would mean `behavioral_state.py`'s existing gating is less restrictive in practice than this report's structural analysis alone suggests, meaningfully raising its practical relevance without touching any code.
   - *Negative result (confirming near-zero joint occurrence):* would confirm this report's own INFERENCE quantitatively, strengthening (not merely repeating) §6/§7's central finding.
   - *Advances the accumulated-competence question:* indirectly — it calibrates how seriously to weight `behavioral_state.py`'s current reachability gap when designing any future extension of its pattern.

2. **A read-only trace of whether `app/emergent_scheduler.py`'s two unconditional call sites have ever, in real production history, generated a self-referential prompt that happened to contain a real directive's trigger keyword** (§6's stated UNKNOWN).
   - *Question:* has the one real production-reachable path for this mechanism ever actually fired organically?
   - *Information value:* moderate — a real historical firing (or confirmed absence of one) would directly answer whether this mechanism has ever had a genuine, non-test production effect at all.
   - *Prerequisite:* the one real historical directive's trigger keyword is known (`zorbnak`) and the store is now empty — this specific question can only be answered for the one historical directive that existed, within its ~160-second real lifespan; a genuinely useful version of this investigation would need a directive that persisted for a meaningful real duration, which has never happened.
   - *Research risk:* low — read-only log search.
   - *Code changes required:* none.
   - *Positive result:* would be a first real, organic (non-test) production firing — a genuinely new data point.
   - *Negative result:* given the ~160-second real lifespan, an absence is nearly certain and uninformative — this action's own expected value is capped low by that fact, which should be weighed against action 1's cheaper, more informative alternative.
   - *Advances the accumulated-competence question:* marginally — mostly informative about this specific mechanism's history, not the broader architecture.

3. **A dedicated, independent read-only forensic audit of RiverBrain's `learn_from_sandbox_outcome()`/`learn_from_rating()` disconnection from `model_task_stats`, specifically scoped to design (not implement) the fix this session's prior archaeology already identified as the single most repeatedly-confirmed, load-bearing wiring gap in this project's entire research history.**
   - *Question:* what is the minimum, safest, most precisely-scoped code change that would reconnect these two genuinely-independent signals to the statistic `score_model()` actually reads, and what would the frozen protocol's own already-designed null/positive-control battery say about whether that reconnection is safe to test before touching production?
   - *Information value:* very high — this is, per both this mission's own §15 missing-link analysis and this session's prior archaeology, the single most consequential, most independently-reconfirmed gap in the entire research program; closing the design gap (not the code gap) is the natural next step before any implementation decision is made.
   - *Prerequisite:* this mission's own §15/§16 findings, plus a full independent re-read of `learn_from_sandbox_outcome()`/`learn_from_rating()`'s exact current call sites (not fully re-verified this mission beyond the negative-grep already performed in this session's prior work).
   - *Research risk:* low if kept strictly to design (no implementation); the risk shifts to "moderate" the moment anyone tries to actually wire this without first running it through a frozen, adversarially-reviewed protocol of the kind this session's archaeology already found this project is capable of producing.
   - *Code changes required:* none for the design phase itself.
   - *Positive result:* a genuinely reviewable, frozen design specifying exactly how to reconnect these signals safely, ready for the same adversarial-review/blind-review cycle the persistent-competence protocol lineage already demonstrated works.
   - *Negative result:* a design pass that concludes the reconnection cannot be done safely without also solving a harder prerequisite problem (e.g., RiverBrain's own singleton/writer-thread isolation risk, per Tier-8) — itself a valuable, falsifiable finding that would redirect priority toward that prerequisite instead.
   - *Advances the accumulated-competence question:* directly and centrally — per §15, this is the one link every candidate mechanism surveyed across this entire research arc still lacks simultaneously.

**Explicitly not recommended, and why:** implementing §16's minimum complete experiment itself. It is real, buildable largely from existing designed components, and directly answers the mission's own central synthesis question — but it is also the single most expensive item this report could recommend, and per the mission's own explicit preference for hypothesis-killing investigations that are cheap relative to full implementation, actions 1–3 above should be run first; several of them could, in principle, change how action 16's design should be scoped before any of it is built.

## 18. Limitations

This audit did not independently re-verify `liveness_ledger.py`'s complete check inventory to confirm the absence of a `behavioral_state`-specific check claimed in §13 item 5 — this is RETRIEVED from the prior candidate-tournament document and is plausible given this mission's own partial grep, but not independently confirmed by a full read of that file's check list. This audit did not measure the real joint-occurrence rate named as Recommendation 1 in §17 — that measurement is proposed, not performed. This audit did not independently re-verify `river_deliberation.py`'s `DIRECT_ECHO_TASKS` routing behavior for `task_type="personal"` beyond citing this project's own prior extensive documentation of it — the claim that the C1 validation's single-model call is *less* of a bypass than it might first appear (§7) rests on that prior documentation, not a fresh re-read of `river_deliberation.py`'s current source this mission. The §14 learning-loop component inventory draws heavily on this session's own two immediately-prior missions (the second-pass archaeology and the `self_model_claims.py` audit) rather than re-deriving every cited fact from primary source a third time in one session — each such reuse is marked RETRIEVED, per this report's own discipline, but a reader relying on this report alone for those specific claims should treat them at one remove from this mission's own direct verification.

## 19. State-integrity/provenance block

- **Opening HEAD:** `2fba42644c82b9f7096276f4dd338d615cf1bcce`. **Closing HEAD:** `2fba42644c82b9f7096276f4dd338d615cf1bcce` — unchanged.
- **Working-tree integrity:** a `git status --porcelain` snapshot (230 entries) was captured before this mission's first read (`/tmp/bs_audit_status_before.txt`, outside the repository) and compared against the same command at report-writing time; the only difference is this report's own new, untracked path.
- **Files created by this mission:** exactly one — `audits/2026-09-23_behavioral_state_forensic_infrastructure_audit.md`.
- **No production code, prompt, configuration, or persistent state was modified.** `behavioral_state.py` was not touched. No FeralEcho module was imported in a way that could mutate state (the file reads performed — `memory/behavioral_directives.json`, `memory/behavioral_directives_audit.jsonl` — used the plain `Read` tool against existing text files, not a Python import). No component was connected to any other. No experiment was run or implemented. No Rung-1, `accumulation_probe`, AP-0, E5-mini, or RiverBrain process or artifact was started, stopped, advanced, repaired, or interfered with.

---

## The 20 required questions, answered explicitly

**1. Does `behavioral_state.py` reliably persist information across restart?**
Yes — this is its single most rigorously demonstrated property, via a genuine separate-subprocess test, and its architecture (no cache, fresh disk read on every call) makes this reliability structurally guaranteed rather than merely observed once (§4, §12).

**2. Does persisted state causally alter later behavior?**
Yes, for the one real, tested case, and with genuine (if small, n=4) controls establishing a real 0% → 75% shift over baseline (§4, §8). It does not establish anything beyond what a hand-written static instruction achieving the identical rendered text would also achieve (§11).

**3. Was the historical behavioral-consequence experiment representative of the real production path?**
No, precisely and in two distinct ways: it bypassed the outer `_is_introspective()` gate that all three real human-facing entry points impose on the call that houses this mechanism, and it bypassed the real production request pipeline for the model call itself (§6, §7).

**4. What exactly does `_is_introspective()` change about that conclusion?**
It does not change whether the architecture works — that is independently, correctly confirmed regardless. It changes whether the architecture is ever *invoked at all* during an ordinary real human conversation: for the three human-facing entry points, `get_structural_self_facts()` (and therefore this mechanism) is never called unless the same message is also classified introspective — a conjunction this report finds is plausibly rare, though not empirically measured (§6, §7, and Recommendation 1 in §17).

**5. Does `behavioral_state.py` demonstrate learning?**
No — and it does not claim to; its own module docstring says so explicitly, and this mission accepts that classification without re-litigating it.

**6. What DOES it demonstrate?**
A real, correctly-built, restart-surviving, human-confirmation-gated, auditable persistence-and-retrieval mechanism whose consumer architecture is genuinely provenance-agnostic (§9, §10) — real infrastructure, honestly and accurately self-labeled, with one significant, previously under-quantified production-reachability gap (§6, §7).

**7. What is its strongest reusable architectural property?**
The clean separation between generic, provenance-agnostic machinery (atomic write, fresh-read retrieval, deterministic matching, audit logging) and the single, narrow, swappable point where provenance-specific policy is enforced (`human_confirmed is not True: raise`) — this separation, more than any single primitive, is what makes §10's provenance-agnosticism analysis answerable at all, and is the clearest positive lesson this audit found.

**8. Is its behavioral consumer provenance-agnostic?**
Yes, structurally — `get_matching_directives()` and `_build_behavioral()` read only `trigger_keywords` and `directive_text`, never `provenance` itself (§10).

**9. Could independently evaluated machine-derived state use the same consumer architecture in principle, without changing the consumer's fundamental design?**
Yes, in principle, per §10's interface-contract analysis — with the one concrete caveat that `_build_behavioral()`'s hardcoded disclaimer text would need to change to remain honest about the new provenance, and the `human_confirmed` gate would need a differently-shaped replacement policy check.

**10. What evidence would be required before doing so scientifically?**
The full battery already specified, by citation, in §16's minimum complete experiment design — a genuinely independent evaluator, held-out transfer tasks, the frozen protocol's own already-designed null/positive-control and counterfeit-learner defenses, and, critically, the one genuinely new component this report identifies explicitly (§16's closing paragraph): a consumer wired to fire unconditionally on real, relevant, human-facing traffic, which nothing in FeralEcho currently combines with a clean evaluator.

**11. Which existing FeralEcho component currently provides the strongest candidate for each link in: experience → evaluation → retention → restart → behavior → held-out test → outcome → accumulation?**
Experience: real F2 sandbox executions. Evaluation: F2's own deterministic pass/fail, or `self_knowledge_verification.py`'s rule engine. Retention: any of the three JSONL/JSON stores surveyed (RiverBrain's pickle, `self_model_claims.jsonl`, `behavioral_directives.json`) — mechanically comparable. Restart: `behavioral_state.py`, unambiguously (§4, §12, §14). Behavior: RiverBrain's `score_model()`, for unconditional reachability specifically (though contaminated at its dominant-volume evaluator). Held-out test: the frozen persistent-competence protocol v1.1's E2/E3/E5 design (unbuilt). Outcome: the same protocol's oracle design (unbuilt). Accumulation: the same protocol's §12 longitudinal design (unbuilt).

**12. Which link is weakest?**
The BEHAVIORAL CONSUMER link, project-wide — every candidate examined across this research arc trades off cleanly between "unconditionally reachable" and "fed by a genuinely independent evaluator," and none achieves both simultaneously (§15).

**13. Which link is completely missing, if any?**
Not fully missing, but the specific *combination* named in §15 (a clean evaluator feeding an unconditionally-reachable, human-facing consumer) does not exist anywhere in the current codebase, per this mission's own review of every candidate this research arc has surveyed.

**14. Does FeralEcho already contain all major pieces required for a clean persistent-learning experiment?**
Mostly yes, at the design level — see §16, which is built almost entirely from existing, already-specified components — but not at the implementation level, since the frozen protocol has never been run and the one genuinely missing wiring pattern (§15/§16's closing note) has never existed in any form.

**15. Does it already contain all major pieces required for an ACCUMULATED-COMPETENCE experiment specifically?**
Design-level, yes — the frozen protocol v1.1's §12 longitudinal design is fully specified and, per this session's own prior archaeology, has never been run. Implementation-level, no — nothing in this codebase has ever executed a repeated-accumulation test of any kind, at any scale, for any mechanism surveyed.

**16. What is the smallest experiment capable of distinguishing genuine retained competence from the strongest known counterfeit?**
Per §16: reuse the frozen protocol v1.1's own already-designed EMPTY/NEUTRAL/POISON context-ablation arms and its `[QUAL-4]` null-effect/positive-control battery directly, rather than inventing a new counterfeit-detection design — this project has already built and adversarially hardened exactly this apparatus once; the smallest experiment is to run that design, not to redesign it.

**17. What should we investigate next, and why?**
Per §17's ranked list: (1) the real joint `_is_introspective()`/arbitrary-keyword occurrence rate — cheap, sharpens this report's own central finding with an actual number; (2) whether the one real historical directive ever fired organically via the autonomous path — cheap but low expected information value given its ~160-second real lifespan; (3) a dedicated design-only forensic pass on reconnecting RiverBrain's two genuinely independent signals to `model_task_stats` — the highest-value item, because it is the one link this entire research arc keeps independently rediscovering as the central, unsolved gap.

**18. What should we explicitly STOP investigating unless new evidence appears?**
Per this session's own prior sibling audit, the `self_model_claims.py` learning-candidate branch remains closed. This mission adds: further attempts to characterize `behavioral_state.py` itself as evidence of anything beyond correctly-built, honestly-labeled infrastructure should also stop — its own module docstring and this mission's own independent re-derivation agree completely, and no further scrutiny of this specific module is likely to change that conclusion absent a genuinely new experiment (such as §17's Recommendation 1) producing new data.

**19. Has the archaeology uncovered a plausible path forward that requires mostly CONNECTING AND QUALIFYING existing mechanisms rather than inventing another architecture?**
Yes, substantially — §16's minimum complete experiment design is built almost entirely from components this project has already designed, and in several cases already adversarially hardened (the frozen protocol's own tie-break fix and null/positive-control battery). The one genuine exception, named explicitly rather than smoothed over, is the "clean evaluator + unconditionally-reachable, human-facing consumer" combination (§15/§16's closing paragraph) — a real, if narrow, new wiring pattern, not an entirely new architecture.

**20. What result from this mission would most strongly justify changing the current Rung-1 roadmap?**
A confirmed measurement, from Recommendation 1 (§17), that the real joint occurrence rate of `_is_introspective()` firing alongside relevant topical content is *not* negligible — that would mean `behavioral_state.py`'s existing pattern is already closer to real production relevance than this report's structural analysis alone suggests, and would argue for prioritizing a design pass on making its consumer architecture provenance-agnostic (§10) sooner rather than later, ahead of the larger, more expensive RiverBrain-reconnection work in Recommendation 3.
