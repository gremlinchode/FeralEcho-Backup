# `apply_to_code`: Forensic Reconstruction of All 3,196 Real Invocations

Second adversarial investigation, following directly from
`audits/2026-09-03_self_edit_forensic_verification.md`'s finding that 4
(later corrected to 5 — see §2) of the 25 real deployed
`self_edit_generated.py` versions defined the `apply_to_code` hook, and
that 1,985/3,196 real invocations (62%) reported `changed: true`. This
investigation does not use `_score_response_quality()` anywhere —
classifications below are based on direct execution, parsing, and
semantic analysis of the real, extracted historical code. **No
production file was modified. No candidate was deployed. All execution
happened in throwaway, disposable Python processes against representative
test input, never against the live system.**

---

## 1. A Real Limitation, Stated Before Anything Else

**`memory/apply_to_code_invocations.jsonl`'s schema — confirmed uniform
across all 3,196 lines — is `{ts, changed, before_len, after_len,
error}`. It never stores the actual code text, before or after.** This
means the exact historical inputs and outputs cannot be replayed
verbatim — they were never captured. What follows instead is the best
available substitute: (a) precise statistical analysis of the length/
error data that *does* exist, per real historical version, and (b)
direct reconstruction — extracting each historical version's real,
deployed `apply_to_code` source from `app/core/self_edit_backups/` and
executing it against representative, realistic input to observe its
actual, concrete behavior. This is not a replay of history; it is the
closest reproducible substitute available, and is presented as such, not
overstated as more than it is.

---

## 2. Identifying Every Real `apply_to_code`-Defining Version

**A real methodological correction, made mid-investigation, not
glossed over**: the first pass searched only for `^def apply_to_code`
and found 4 versions. A precise, exact reconciliation of invocation
timestamps against known deploy windows found 322 real invocations
(2026-08-23 → 2026-08-25) that fell in a window attributed to none of
those 4 — re-checking the actual deployed file for that window directly
revealed a **fifth** version that defines the hook via an **alias
assignment**, not a `def` statement: `apply_to_code =
refactor_shorten_code_generation_v15` (`self_edit_backups/
self_edit_20260825011254.py:29`) — invisible to a `def`-only grep, fully
visible to Python's real `getattr(module, "apply_to_code", None)`
lookup. **This is the same class of error the prior audit made** (a
too-narrow search method mistaken for a complete population) —
recorded here as a second, independently-caught instance in the same
investigation thread, not hidden.

**All five real, confirmed live windows, reconstructed from the 25
retained backup timestamps (each backup's own filename timestamp marks
when it was superseded by the next real deploy):**

| Version | Backup file | Live window (UTC) | Real invocations |
|---|---|---|---|
| V1 | `self_edit_20260813120335.py` | 2026-08-08 12:31:16 → 2026-08-13 12:03:35 | 668 |
| V2 | `self_edit_20260813175936.py` | 2026-08-13 12:03:35 → 2026-08-13 17:59:36 | 47 |
| V3 | `self_edit_20260823031936.py` | 2026-08-19 01:13:26 → 2026-08-23 03:19:36 | 537 |
| **V4 (alias)** | `self_edit_20260825011254.py` | 2026-08-23 03:19:36 → 2026-08-25 01:12:54 | 322 |
| V5 | `self_edit_20260826121324.py` | 2026-08-25 17:33:59 → 2026-08-26 12:13:24 | 150 |
| — | (unrecoverable, backups rotated away) | before 2026-08-08 12:31:16 | 1,471 |
| — | unaccounted | — | **1** |

**1,471 + 668 + 47 + 537 + 322 + 150 = 3,195 of 3,196 accounted for
(99.97%).** The one remaining stray invocation (2026-08-13, falling
in a sub-second gap right at a version boundary) was not chased
further — almost certainly a boundary artifact of a deploy happening
mid-invocation, not a new finding. **The 1,471 pre-08-08 invocations
cannot be attributed to any recoverable version** — those backups have
been rotated out by the 25-file retention cap and their exact code is
permanently gone. This means the true historical population of
apply_to_code-defining versions is **at least 6** (five recovered here,
plus whatever produced those 1,471 earlier invocations) — stated as a
real, acknowledged limit on how far back this reconstruction can reach,
not glossed over.

---

## 3. Per-Version Statistics (Length/Error Data — Everything the Log Actually Records)

| Version | N | `changed=true` | Length delta (changed only) | Dominant error |
|---|---|---|---|---|
| V1 | 668 | 586 (87.7%) | **always negative**: min −2253, max −1, mean **−164** | — |
| V2 | 47 | 2 (4.3%) | −225 to −1 | **sandbox timeout: 45/47 (95.7%)** |
| V3 | 537 | 528 (98.3%) | **always negative**: min −3900, max −1, mean **−838** | — |
| V4 (alias) | 322 | **0 (0%)** | n/a | **`APPLY_TO_CODE_BAD_RETURN_TYPE`: 322/322 (100%)** |
| V5 | 150 | 2 (1.3%) | always **+2** (both instances) | **sandbox timeout: 145/150 (96.7%)** |

**Not one single invocation, across all 1,724 recovered `changed=true`
cases in V1/V2/V3/V5 combined, ever produced code that was the same
length or longer** (except V5's two +2-byte cases). Every real,
substantive transformation this hook has ever performed shrank the
candidate. This alone is a strong, quantitative signal before any
content-level reconstruction is even attempted.

---

## 4. Direct Reconstruction — What V1 and V3 Actually Do, Proven by Execution

The two versions responsible for essentially all real `changed=true`
activity (1,114 of 1,724 recovered instances). Their real, deployed
source was extracted verbatim and run against a representative test
candidate — realistic, non-adversarial Python containing an import, a
function whose name matches this family's own well-established
generation naming pattern (`_v10`, `_v11`, `_v14`... confirmed real
naming convention from the backups themselves), and a decorator:

```python
import re
from collections import Counter

def refactor_shorten_code_generation_v10(code: str) -> str:
    return code.strip()

def log_call(fn):
    def wrapper(*a, **kw):
        return fn(*a, **kw)
    return wrapper

@log_call
def process(code):
    tokens = re.findall(r"\w+", code)
    return Counter(tokens)
```

### V1's real `apply_to_code` (`self_edit_backups/self_edit_20260813120335.py:36-46`)

```python
def apply_to_code(code: str) -> str:
    lines = code.split('\n')
    new_lines = []
    for line in lines:
        if 'refactor_shorten_code_generation_v10' in line:
            new_lines.append('new_func')
        elif 'log_call' in line:
            new_lines.append('log_call')
        else:
            new_lines.append(line)
    return '\n'.join(new_lines)
```

**Real output, run directly:**
```python
import re
from collections import Counter

new_func
    return code.strip()

log_call
    def wrapper(*a, **kw):
        return fn(*a, **kw)
    return wrapper

log_call
def process(code):
    tokens = re.findall(r"\w+", code)
    return Counter(tokens)
```

**`compile()` result: `SyntaxError: unexpected indent`.** Any line
containing the substring `refactor_shorten_code_generation_v10` or
`log_call` — not matched-and-edited, **the entire line is discarded and
replaced with an 8-character placeholder token** — leaving the next
line's indentation orphaned with no enclosing statement. Given this
family's own naming convention iterates the exact same
`refactor_shorten_code_generation_v_N` pattern release after release
(confirmed directly from the real backup filenames/contents), this
substring match was not a rare edge case — it was close to guaranteed
to fire on the family's own typical output.

### V3's real `apply_to_code` (`self_edit_backups/self_edit_20260823031936.py:4-29`)

```python
def refactor_shorten_code_generation_v14(code: str) -> str:
    cleaned_code = re.sub(r'/\*.*?\*/|//.*', '', code, flags=re.DOTALL)
    lines = cleaned_code.split('\n')
    significant_lines = [line for line in lines if len(line.strip()) > 2]
    new_lines = []
    for line in significant_lines:
        if 'import' in line or 'from' in line:
            continue
        elif line.startswith('def'):
            if not any(s in line for s in ['->', ':']):
                new_lines.append(line.replace(':', ' -> None:'))
            else:
                new_lines.append(line)
        elif len(line) > 80:
            new_lines.append(re.sub(r'\s+', ' ', line).strip())
        else:
            new_lines.append(line)
    return '\n'.join(new_lines)

def apply_to_code(code: str) -> str:
    return refactor_shorten_code_generation_v14(code)
```

**Real output, run directly:**
```python
def refactor_shorten_code_generation_v10(code: str) -> str:
    return code.strip()
def log_call(fn):
    def wrapper(*a, **kw):
        return fn(*a, **kw)
    return wrapper
@log_call
def process(code):
    tokens = re.findall(r"\w+", code)
    return Counter(tokens)
```

**`compile()` result: parses cleanly.** But `line 12`
(`if 'import' in line or 'from' in line: continue`) **unconditionally
deletes every import statement**, with no exception for correctness.
Both `import re` and `from collections import Counter` are gone from
the output. If this code were ever executed, `re.findall(...)` and
`Counter(...)` would both raise `NameError` on their very first call. **This
is not a hypothesis — it is the exact, real, previously-documented
failure signature this project's own history already recorded** (three
successive broken `apply_to_code` deployments each missing a real
import — `is_prose`, `regex_pattern`, `re`) **now traced to a concrete,
reproducible root cause**: a deployed transformation function that
deletes imports by design, on every single line containing the
substrings "import" or "from," unconditionally.

### V4 (alias) — a type-contract violation, not a text transformation

`apply_to_code = refactor_shorten_code_generation_v15`, and
`refactor_shorten_code_generation_v15(origin_func)` is a **decorator
factory** — it expects a *function* and returns a *new function*, not a
string transformation. Calling it with a code string (as
`_apply_self_edit_output()` always does) returns a Python function
object, not a string. **Confirmed against the real log data**: 322/322
invocations during this version's live window logged
`APPLY_TO_CODE_BAD_RETURN_TYPE` — a real, named, explicit safety check
(inside `_run_apply_to_code_sandboxed()`) correctly caught this every
single time, with zero exceptions and zero candidates ever silently
corrupted by it. **This is the one version, of the five recovered, whose
real-world effect was benign** — not because its logic is sound, but
because its fundamental type mismatch is caught before it can do
anything.

### V2 and V5 — functionally inert due to timeout, true behavior unobserved

95.7% (V2) and 96.7% (V5) of real invocations hit the 2-second sandbox
timeout (`_run_apply_to_code_sandboxed(..., timeout=2.0)`) before
completing at all. Whatever these two versions' real logic does, it
could not finish within budget in the overwhelming majority of real
attempts — their actual behavior is **not observable from this data**;
the tiny minority that did complete (2/47 and 2/150) shrank or grew by a
few bytes, too sparse a sample to characterize with any confidence.

---

## 5. Classification (Not Using `_score_response_quality()` Anywhere)

| Version | Real share of all recoverable invocations | Classification | Basis |
|---|---|---|---|
| **V1** | 668/2724 recovered (24.5%) | **HARMFUL** | Directly reproduced: produces a `SyntaxError` on realistic input containing its own family's typical naming pattern. Not indeterminate — proven by direct execution. |
| **V3** | 537/2724 (19.7%) | **HARMFUL** | Directly reproduced: produces syntactically valid but semantically guaranteed-to-crash code (unconditional import deletion). Matches this project's own previously-documented real `NameError` incidents exactly. |
| **V4 (alias)** | 322/2724 (11.8%) | **NEUTRAL / INERT (fails safe)** | A real type-contract violation, but one that a real, explicit safety check catches every time with zero silent corruption. |
| **V2** | 47/2724 (1.7%) | **INDETERMINATE** | 95.7% of real invocations never completed (timeout); true behavior unobserved. |
| **V5** | 150/2724 (5.5%) | **INDETERMINATE** | 96.7% timeout, same reasoning as V2. |
| Pre-08-08 (unrecovered) | 1,471/3,196 (46.0% of the full log) | **UNKNOWN — permanently, by construction** | Code no longer exists to inspect; the log itself never recorded content. |

**Direct answer to the central question: does the 62% "changed
something" rate represent meaningful modification, or merely textual/
state mutation?**

**Meaningful — but meaningfully destructive, not meaningfully neutral.**
This is not whitespace noise, not trivial reformatting, not a
no-op-shaped mutation. It is real, deterministic, rule-based content
transformation — and in every recoverable case where it could be
directly characterized (V1, V3 — 1,114 of the 1,724 recoverable
`changed=true` cases, 65%), that transformation was **provably harmful**:
one version guarantees a syntax error, the other guarantees a
guaranteed-to-crash-if-ever-run result via unconditional import
deletion. There is no recovered evidence, anywhere in this
investigation, of a single `changed=true` invocation that improved a
candidate.

---

## 6. Regressions, Exceptions, Behavioral/Persistence/Memory/Latency Effects, Crashes

- **Regressions**: not directly testable in the "before vs. after in
  production" sense, since transformed candidates never reach
  production visibly distinguishable from untransformed ones in any
  currently-logged record — but see §7's causal-link discussion below.
- **Exceptions**: real, named, and bucketed in the log itself —
  `APPLY_TO_CODE_BAD_RETURN_TYPE` (322), three distinct real `NameError`
  shapes reported in the broader log beyond the 5 recovered windows
  (`name 're' is not defined`: 114 project-wide; `name
  'regex_pattern' is not defined`: 75; `name 'is_prose' is not defined`:
  21 — these predate the 5 windows recovered here and are additional,
  independent confirmation of the same import-stripping failure class
  recurring across multiple historical, now-unrecoverable versions).
- **Persistence/memory effects**: none escaped the sandbox in any
  recovered case — `_run_apply_to_code_sandboxed()`'s real, kernel-level
  write-blocking (Finding 31/41B3/69's fix) caught 20 real
  `blocked_write_attempt` cases project-wide; none of the 5 versions
  recovered here triggered one.
- **Latency**: real and significant — V2 and V5 show the sandbox's
  2-second timeout firing on ~96% of real invocations, meaning whatever
  those two versions attempt is costly enough (or hung/looping) to
  routinely exceed budget. This is itself a real cost: every one of
  those timeout invocations consumed 2 real seconds of wall-clock time
  inside the self-edit generation pipeline for zero effect.
- **Crashes**: none of the 5 recovered versions crashed the *host*
  process — every failure mode observed (syntax corruption, import
  deletion, bad return type, timeout) was contained and logged, exactly
  as the sandboxing architecture is designed to do. The candidates
  themselves were effectively "crashed" (rendered non-functional), but
  the system protecting against that consequence held throughout.

---

## 7. One Causal Link Worth Naming, Flagged as Plausible, Not Proven

`audits/2026-09-03_self_edit_forensic_verification.md` found real,
historical `staging_import_failed` (4,033 occurrences) and
`import_hallucination` (606 occurrences) results in `SELF_EDIT.log`. V3
(and plausibly other unrecovered versions sharing the same
import-deleting pattern) would produce **exactly** this failure
signature in any candidate it touched — a perfectly good, generated
candidate that legitimately used `re`/`Counter`/etc. would have those
imports silently deleted by `apply_to_code` *before* F1/F2/F3 ever saw
it, then correctly fail F2's staging import test for a reason that has
nothing to do with the original generation's own quality. **This is
flagged as a plausible, not confirmed, contributor** — establishing it
definitively would require correlating exact timestamps between
`apply_to_code` invocations and immediately-following staging failures,
which the available log data does not cleanly support (the
`apply_to_code` log has no candidate identifier linking it to a specific
later `staging_import_failed` line). Worth a dedicated follow-up if this
causal question ever becomes a priority.

---

## 8. What This Investigation Does Not Establish

- The exact content of the 1,471 pre-08-08 invocations, or which
  version(s) produced them — permanently unrecoverable from current
  evidence.
- Whether V2 or V5's actual logic (versus its timeout-dominated
  real-world behavior) would have been beneficial, harmful, or neutral
  had it ever completed — genuinely indeterminate, not merely
  understudied.
- A confirmed (as opposed to plausible) causal link between historical
  `apply_to_code` corruption and the broader `staging_import_failed`/
  `import_hallucination` rejection counts.
- Nothing here implies the current, live `self_edit_generated.py` (which
  does not define `apply_to_code` at all, per the prior audit) is
  presently affected by any of this — this is a forensic reconstruction
  of past behavior, not a live, ongoing issue.

No production code was modified in the course of this investigation.
