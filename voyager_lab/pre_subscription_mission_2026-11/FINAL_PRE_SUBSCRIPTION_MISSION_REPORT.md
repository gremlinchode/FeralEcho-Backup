# Final pre-subscription mission report

Mission: repository preservation, then Grok-to-Grok relay verification, then M5-to-ARK relay verification. Work date: 2026-11-10. Echo's live process was left running. Production code, production memory, the live FAISS index, and live metadata were not modified by this mission's publication or by the loopback tests.

## What was completed

1. The reviewed Voyager research package was committed and pushed to a new remote branch, `project-voyager`, on `gremlinchode/FeralEcho-Backup`. The remote API confirmed the branch SHA before any later commit. Remote `main` and remote `vsl-implementation` were not moved by those pushes.
2. The Grok-to-Grok protocol was inspected and run twice on a loopback server. Both runs: 16 PASS, 1 FAIL. The failure is a real reporting defect and was left unpatched.
3. One synthetic M5 append was served by the local Echo file route and was watched for an ARK ack. The peer process answered. The peer relay client did not fetch or acknowledge the new entry during the watch, and it still had not by `2026-11-10T06:01:17Z`.

## What was not completed

- Live ARK receipt and acknowledgment of `m5-20261110T055419Z-9192ca65`. Label: **FAIL** for the executed watch. The message remains unacked.
- Live ARK reply, live M5 receipt of that reply, live duplicate delivery, live disconnect, and live recovery. Label: **NOT RUN**.
- A second Grok identity on this machine. None exists. The loopback pair is the stand-in.
- Any change to production `grok_relay/relay.py`. The ack-print defect is still present on purpose.

Phase labels: repository preservation **PASS** for the package that was pushed. Grok-to-Grok **PARTIAL**. M5-to-ARK **PARTIAL**.

## Commits and remote branch

Remote: `https://github.com/gremlinchode/FeralEcho-Backup`. Branch: `project-voyager`. Pushes were fast-forward only. No force-push. No merge into `main` or `vsl-implementation`.

| Commit | Role | Remote confirmation |
|---|---|---|
| `38d1b4c28a32c9a63207b4b856d8861ffba42ae6` | Reviewed research package. Parent `dc8d6eb9b6479ef323614cd6820bb050a14299eb`. 879 files | Confirmed on `project-voyager` before the status commit |
| `4238aff294bbc9fac148ff1b144e66c283c68509` | `GITHUB_PUBLICATION_STATUS.md` only. Parent is the package commit | `gh api` returned this SHA. Local HEAD matched |

This report's own commit is a later fast-forward on the same branch. Its SHA is not written inside this file. It counts as published only after the branch API returns that SHA. The operator records it in the session reply and, if that confirmation succeeds, in a following one-file commit that names this report's SHA. That following file cannot contain its own SHA.

At the time of the status commit, remote `main` was `efeb565b3221eb6ff9d7a65a3c9f3232f16806d0` and remote `vsl-implementation` was `dc8d6eb9b6479ef323614cd6820bb050a14299eb`. Those two SHAs are re-checked at the report push and stated in the session reply. They are not assumed from this paragraph alone.

Local `main` in the production worktree was left unpushed. The dirty production worktree was not staged, committed, reverted, or cleaned.

## Repository preservation

Full write-up: `voyager_lab/repository_preservation_2026-11/`. Short form:

- The GitHub repository was already **public** when this branch was created. The parent commit `dc8d6eb` was already on public `vsl-implementation`. `ORIGIN.md` and `COUNCIL.md` were already in that parent.
- Two transparency documents restate a biographical sentence that is already in `ORIGIN.md`. They were published unchanged and the sentence is not repeated here.
- Publishable set before the preservation write-up itself: research reports, protocols, harnesses, scoring tools, sanitized results, and the transparency package. Largest included file was `search_results.json` (87442 bytes). No included file was 10 MB or larger.
- Excluded and kept only on this machine: `copy_live/` (361 MB), `rebuilt/` (367 MB), both FAISS indexes, both `memory_meta.json` copies, the identity sidecar, `search.log`, `reembed.log`, four bytecode files, and three 3-byte `.human_token` fixtures. The fixtures are byte-identical synthetic files written by the lab harness. Their contents and their hash are not published. Exclusion hashes for the memory clones are in `EXCLUDED_ARTIFACTS.md`.
- `git diff --cached --check` on the package commit reported 8 trailing-whitespace warnings, all Markdown hard breaks in two sealed diagnostic reports. Those files were not edited. Secret scan of the staged blobs: 0 hits. Forbidden paths staged: 0.

## Relay test identifiers

Loopback primary (16 PASS, 1 FAIL): send `m5-20261110T055342Z-7f9bdfe1`, reply `ark-20261110T055342Z-c4907c42`.

Loopback published-harness re-run (16 PASS, 1 FAIL, exit 1): send `m5-20261110T060005Z-ff0fb4bc`, reply `ark-20261110T060005Z-20446aea`.

Live probe: `m5-20261110T055419Z-9192ca65`. New-entry SHA-256 `273e6cc8382ba012d5274f2b02b6334ff84423a9541918c5cb93f6aca8b60ba6`. Local serve HTTP 200, 20245 characters. Peer file remained 4688 characters. Outbox `acked: false`.

The loopback failure, both runs: `read` prints `Ack recorded for not-a-real-id` when the outbox has no such id. A printed ack is evidence only together with `acked: true` on that outbox row.

## Known failure modes

- `append` can succeed while the peer client never pulls. That is the live outcome.
- HTTP 200 from `/projects/file` means the file was served. It does not mean the peer client read it.
- An `ack:` line is applied only when the sender later runs `read`.
- `read` can report an acknowledgment that changed no outbox row.
- A character cursor and the endpoint's byte `size` are different numbers. Using `size` as the cursor truncates the next read.
- Rewinding a cursor replays messages. A cursor that thinks the file shrank does not replay.
- The file route is unauthenticated. Private addresses and mailbox history stay off this branch for that reason.
- The live program lives in an untracked production directory. Publishing it would publish private addresses. The loopback copy is the reproducible artifact.

## Security and privacy exclusions

- No FAISS index, cloned `memory_meta.json`, identity sidecar, `.human_token`, credential file, or private conversation body is in the staged research package or in this report commit.
- Production `grok_relay/` is not in the commit.
- Tailscale addresses are not printed in these reports.
- Git identity configuration was not changed. It stays unset.
- The live mailbox received one synthetic entry. That file is local and untracked. Its historical text is not in Git.

## Remaining manual steps

1. On ARK, `relay.py read`, then append `ack: m5-20261110T055419Z-9192ca65` and `reply fe-pre-sub-live-20261110`. On M5, `relay.py read`, then confirm the outbox row is `acked: true`.
2. Decide whether to patch the ack-print defect. This mission left it in place so the failure stays visible. A patch belongs in a reviewed change to the relay program, not in a report.
3. Decide the already-public repository's privacy posture separately. This mission did not flip visibility and did not rewrite history.

## Reproducible without Grok Build

- The `project-voyager` branch, once the remote lists the commit that adds these reports.
- The loopback command:

```bash
python3 voyager_lab/pre_subscription_mission_2026-11/run_isolated_protocol_test.py
```

Expected: 16 PASS, 1 FAIL, exit 1. Standard library only. No model call. No Echo process.

- The exclusion inventory and the sealed experiment reports already on the branch.

## Still dependent on a machine, a process, or a person

- Live M5-to-ARK delivery needs both Echo file routes up and a person or process on ARK that actually runs `read` and appends the ack. Reachability of the peer file is already demonstrated. Client receipt is not.
- Reading either live mailbox requires a network path to that machine's port 5000. This report does not claim that path is a private network.
- GitHub remains the remote. SSH key authentication to GitHub was refused from this machine. The pushes that already landed used a one-shot HTTPS credential helper. No token was written into the repo or into git config.
- Grok Build is not required to re-run the loopback harness or to read the published reports.

## Evidence boundary

The ten-fact copy-only retrieval result, the full-corpus NOT READY decision, and the evidence-to-answer outcome stay in their own sealed reports. This mission did not rerun them, did not install `rebuilt/`, and did not spend a generation. Echo pid 65139 was still running at the `2026-11-10T06:01:17Z` inspection.
