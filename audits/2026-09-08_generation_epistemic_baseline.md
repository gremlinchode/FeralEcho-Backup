# Generation-Time Epistemic Revision — Baseline

## Safety / state preserved before any change

- Git HEAD at mission start: `9de04a3944f0f0ad38c970f51fde3edd845312a4` ("Implement persistent evidence-backed self-model claims") — the just-committed living-self-model work.
- Prior commit: `5bc94bb05b1011bca9fc1b9235803fc05a105eb6` ("Connect prior F2 evidence to initial self-edit generation").
- `git status` at start: only pre-existing, unrelated modifications (`claude_relay/from_m5.md`, `sandbox/scripts/temp_self_edit.py`) and a large backlog of untracked audit `.md` files from earlier missions this session — none touched by this mission.
- Server: live and healthy, PID 27987, `stage: "serving"`, confirmed via `/state`.
- All prior audits preserved untouched.

## File hashes at mission start (relevant to this investigation)

```
7db260713a17e57749e8786757290e9b6dfdba4aa32ffa8c26d908aa5a93751c  app/core/self_model_claims.py
19d06cb3f1886f81460c2b9bd0ae27253b6b677b72d585d3d05b22dc2f800cda  app/core/self_knowledge_verification.py
679a8cf49ce0adc059ee69c114471189c87824fe9550d7f731fe35493550e8ca  app/core/echo_ground_truth.py
53eeadbf0eef1d5f986fbf91939fc2379ffd76967479ba5f95c035a1a3ff9a5c  app/routes_echo_studio.py
793fc2f20c71bf415ee5518f1828896ef5f2611587bbe1195b8be1885f733d46  app/core/liveness_ledger.py
a63a524cabb96acff5a39b13563624fbfbdef8e00cbc0f07c041e76f9812903f  app/core/self_edit_manager.py
```

## The real, existing claims ledger state at mission start

`memory/self_model_claims.jsonl`, 3 lines:

```json
{"timestamp": "2026-09-08T03:20:55.997630+00:00", "subject": "RiverBrain", "verified": false, "evidence": "test evidence: response denied RiverBrain despite real observations", "proposed_by": "test_response", "verified_by": "self_knowledge_verification"}
{"timestamp": "2026-09-08T03:26:35.116930+00:00", "subject": "RiverBrain", "verified": false, "evidence": "\n\n⚠️ Note: this response denies that RiverBrain exists/is real — the current self-model shows real, active evidence to the contrary. Treat the denial as unverified, not the underlying fact.", "proposed_by": "echo_response", "verified_by": "self_knowledge_verification"}
{"timestamp": "2026-09-08T03:27:02.141032+00:00", "subject": "RiverBrain", "verified": false, "evidence": "\n\n⚠️ Note: this response denies that RiverBrain exists/is real — the current self-model shows real, active evidence to the contrary. Treat the denial as unverified, not the underlying fact.", "proposed_by": "echo_response", "verified_by": "self_knowledge_verification"}
```

Two of these three are real, from real conversations run during the living-self-model mission's own Phase 12 test. Both record `verified: false` for RiverBrain — meaning, per `self_knowledge_verification.py`'s own docstring contract ("verified is True if a checked claim matched real ground truth, False if a checked claim was wrong"), that a **denial** of RiverBrain was checked and found wrong — i.e. RiverBrain genuinely exists. This is the exact real, empirical failure this mission investigates.

## The known RiverBrain baseline, carried forward from the two prior missions

- Self-Transparency Audit (`audits/2026-09-08_self_transparency_audit_FINAL.md`): Echo affirmed RiverBrain's existence in four live conversations, denied it in a fifth, while `river_brain.pkl` held 160,000+ real observations throughout.
- Living Self-Model implementation (`audits/2026-09-08_living_self_model_validation.md`, now committed as `9de04a3`): Gate 3 (persistence) passed — a claim verified in one conversation was durably retrieved into a fresh conversation's real context. Gate 1 (correctness) failed both post-implementation trials — Echo's main generated answer still denied RiverBrain despite the evidence being present in context; only the separate post-hoc verifier caught it.

**This mission's baseline for Phase 16's comparison is therefore 0/2** on the strict "Echo's own generated answer is correct" measure, immediately post the living-self-model commit, before any change made in this mission.

## Real current RiverBrain ground truth at mission start

`memory/self_model.json`'s `river_brain.total_observations`: 173,370 (confirmed via direct read at the start of this mission — the number moves continuously since the server is genuinely live and learning).
