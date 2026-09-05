# FeralEcho — Public-Sharing Readiness Review (2026-09-05)

**Scope and method**: requested directly, ahead of any decision to make this repo (currently private, `gremlinchode/FeralEcho-Backup`) public or share it beyond its current access. Checked, not assumed: full git history (all 151 commits, not just the current working tree) for secrets and credential-shaped content, commit author metadata for identity exposure, tracked file content for network/infrastructure details and personal disclosure, and cross-referenced against this project's own already-decided privacy rules rather than inventing new ones.

**Bottom line: do not make this public as-is.** Two items are clear, concrete blockers; a third is a real judgment call only Gremlin can make. Everything else checked out clean.

---

## Blockers

### 1. `COUNCIL.md` would be exposed, directly contradicting an already-decided project policy

`COUNCIL.md` is fully git-tracked, not excluded by `.gitignore` in any way. If this repo goes public, this file goes with it.

This isn't a fresh judgment call — the project already decided this, twice, on the record: Finding 68 (2026-07-22) states "whether it's ever shared back to the council members themselves or made public (no, stays private, full stop)"; Finding 82 (2026-07-23) reaffirms it explicitly ("Whether this file is ever shared back to the external council members (Claude, Grok, Gemini, ChatGPT, DeepSeek) or made public is unchanged and still no, for the same two reasons already on record — third-party retention/training exposure; preserving each voice's independence from what the others already said"). COUNCIL.md's own text states it plainly: "This file stays private, full stop, including from the ones who wrote it."

Nothing technical currently enforces this decision at the repository level — it's a stated intent, not a gate. Making the repo public without excluding this file would silently reverse a decision that's been made twice.

### 2. 149 of 151 commits carry a real name and hostname, directly deanonymizing "Gremlin"

`git log --all --format='%an <%ae>'` shows two identities across this repo's history:
- `Richie Tate <richietate@Richards-MacBook-Air.local>` — 149 commits
- `gremlin <gremlinchode@yahoo.com>` — 3 commits (the ones made directly on GitHub's web editor)

Every document in this repo — CLAUDE.md, GREMLIN_ROLE.md, ORIGIN.md, COUNCIL.md — refers to the human collaborator exclusively as "Gremlin," never by a real name. The commit metadata undoes that pseudonymity completely; anyone who clones the repo (public or currently-private-but-shared) can see the real name behind the persona in the very first `git log`.

This is not a new discovery — `GREMLIN_ROLE.md` already documents it plainly: *"Git commits in this repo use an auto-configured identity (`richietate@Richards-MacBook-Air.local`) — no global `user.name`/`user.email` is set. Don't silently 'fix' this by running `git config` — flag it, let Gremlin decide."* That instruction was followed correctly by prior sessions (nothing was ever silently changed) — but the decision itself was never actually made, and had no `PENDING_DECISIONS.md` row despite that file's own maintenance convention requiring one. It does now (see below).

Fixing the *display name* going forward (`git config user.name`) does nothing about the 149 already-committed identities — that requires either accepting the exposure, or a full history rewrite (`git filter-repo`/`BFH`), which is itself consequential (rewrites every commit hash, breaks any existing clone/fork, and is exactly the kind of destructive operation this project's own standing discipline says needs explicit confirmation, not a default).

### 3. `ORIGIN.md` opens with a specific, real personal disclosure

The document's second paragraph: *"FeralEcho began while Gremlin was heading into the end of a 15-year marriage."* This is real, specific, and immediately visible to anyone who opens the repo — not a security issue, a personal-privacy one. Whether this (and similar passages elsewhere in ORIGIN.md/CLAUDE.md discussing exhaustion, doubt, and the emotional weight of the project) is something Gremlin wants public is not something I can or should decide — flagging it plainly rather than making the call.

---

## Checked and clean

- **No secrets found anywhere** — current working tree and the *full* git history (`git log --all -p`, every commit, not just HEAD) were both scanned for API-key-shaped strings, private-key blocks, AWS keys, and this project's own known secret variable names (`GREMLIN_SECRET`, `THUNDERHEAD_SECRET`, `ECHO_PARTNER_SECRET`, `NEWSAPI_KEY`, `OPENWEATHER_API_KEY`). Two incidental hits, both benign: a `claude_relay` message discussing how to compare a secret via hash *without* transmitting it, and a `password="your_password"` placeholder in example code.
- **`.env` was never committed at any point in this repo's history** (`git log --all --full-history -- .env` returns nothing) and is correctly gitignored today.
- **No credential-shaped files** (`.pem`, `.key`, `id_rsa*`, `.p12`, `*credentials*`) were ever committed, at any point in history.
- **This repo's actual reachable history starts from a deliberate "clean initial commit"** (`44e7a8e`) — the one historical secret leak this project already found and fixed (Finding 7, a real `NEWSAPI_KEY`/`OPENWEATHER_API_KEY` pair in an old `new_directory/` scaffold file) lived in a *different*, pre-rewrite commit (`dc3795a`) that does not exist anywhere in this repo's object database, confirmed via `git cat-file -e`. It was also independently confirmed at the time never to have been pushed.
- **No hardcoded personal email addresses** appear in tracked file *content* (only in commit metadata, covered above).
- **No phone numbers or physical-address-shaped strings** found.
- **Tailscale IPs (`100.84.229.10` / `100.82.172.4`) are hardcoded across many files** (`sync_protocol.py`, `claude_relay/relay.py`, `thunderhead.py`, docs) — flagged for completeness, not treated as a blocker: these are Tailscale's own carrier-grade-NAT address range, meaningless and unreachable to anyone outside the specific tailnet they belong to. Low informational value to an outside reader (confirms two machines exist, nothing more) — worth knowing, not worth blocking on.
- **The extensive, detailed historical security-finding write-ups in CLAUDE.md** (unauthenticated endpoints, the `/nuke` secret-comparison bug, the leaked-key incident, etc.) are all about *already-fixed* issues, described in the same "report the vulnerability, then the fix" shape as any real public security disclosure. Not a blocker on its own — genuinely worth being aware it's there, since it's a much higher level of self-disclosed technical detail than most projects publish, even about closed issues.

---

## Recommendation

Not a go/no-go this document can make on its own — tracked as `PENDING_DECISIONS.md` #22. If and when Gremlin decides to move toward public sharing, the concrete pre-work is:
1. Decide on `COUNCIL.md`: exclude it entirely from whatever becomes public (simplest — matches the existing decision exactly), or revisit the decision itself first.
2. Decide on the git-identity exposure: accept it, or commit to a history rewrite before anything goes public (not before — a rewrite changes every commit hash and should not be done reactively for a different, orthogonal reason).
3. Decide on `ORIGIN.md`'s personal content: publish as-is, redact specific passages, or keep `ORIGIN.md` itself private while the rest goes public.

None of these were acted on in this review — this is a report, per this project's own standing discipline, not a decision.
