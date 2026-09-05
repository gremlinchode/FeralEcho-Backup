# P3-CAUSAL-LEARNING — Causal DAG

Design-only. This document lays out, as a directed acyclic graph, every path by which a
`CORRECT`/`CORRECT_WITH_CONTAMINATION` tag verdict could arise in Condition B or C, and which of those
paths this design's controls close off, versus which remain open as genuine confounds requiring
careful attribution rather than assumption.

```mermaid
flowchart TD
    FORM["Formation: rule stated
    (marker -> tag), no worked example"]

    subgraph CondB["Condition B paths"]
        WRITE["add_to_vector_memory()
    real write attempt"]
        GATE{"memory_write_validator
    allow / warn-allow / BLOCK"}
        FAISS_STORE["memory/faiss.index +
    memory_meta.json"]
        WAIT["real >=30 min wait"]
        RETRIEVE["retrieve_relevant_memories()
    real semantic search"]
        SURFACED{"did the search surface
    the taught rule text?"}
        CTX_B["system context built from
    retrieved block (build_context_system_note)"]
    end

    subgraph CondC["Condition C paths"]
        NOWRITE["Formation content
    NEVER written"]
        CTX_C["system context built from
    EMPTY retrieval (belt-and-suspenders)"]
    end

    PROBE["Probe: marker embedded in a
    fresh, unrelated carrier question"]

    GEN["EchoDirectResponder generation
    (single model, Design B, no RiverBrain touch)"]

    RESP["Raw response"]

    CONFOUND_CHANCE["CONFOUND: chance
    (tag-shaped invented word could
    coincidentally appear -- screened
    against dictionary + prior tokens,
    residual risk near-zero but not
    literally zero)"]
    CONFOUND_PRIOR["CONFOUND: model's own
    stylistic prior toward inventing/
    echoing recently-seen-shaped tokens
    (a base-model tic, not rule-following)"]
    CONFOUND_LEAK["CONFOUND: an unrelated,
    pre-existing production memory
    entry coincidentally contains a
    similar invented word (near-zero
    given fresh, screened vocabulary,
    but checked per-trial via state_read)"]

    L1_VERDICT["Classification: L1
    (retrieval-mediated) --
    the correct explanation whenever
    SURFACED=true and CTX contains
    the real rule text"]
    L2_CANDIDATE["Classification: UNKNOWN
    (L2 CANDIDATE) -- only reachable
    in Condition C, requires state_mutation
    confirming zero write occurred AND
    ruling out all three confounds above"]
    NULL_VERDICT["Classification: NULL --
    no correct verdict above chance
    in either B or C"]

    FORM --> WRITE --> GATE
    GATE -->|allow| FAISS_STORE
    GATE -->|BLOCK| CONFOUND_LEAK
    FAISS_STORE --> WAIT --> RETRIEVE --> SURFACED
    SURFACED -->|yes| CTX_B --> GEN
    SURFACED -->|no, unrelated content instead| CTX_B

    FORM --> NOWRITE --> CTX_C --> GEN
    PROBE --> GEN
    GEN --> RESP

    RESP -->|CORRECT, Condition B, SURFACED=yes| L1_VERDICT
    RESP -->|CORRECT, Condition C, state_mutation confirms no write| L2_CANDIDATE
    RESP -->|NO_TAG/WRONG_TAG in both| NULL_VERDICT

    CONFOUND_CHANCE -.->|must be ruled out before| L2_CANDIDATE
    CONFOUND_PRIOR -.->|must be ruled out before| L2_CANDIDATE
    CONFOUND_LEAK -.->|must be ruled out before| L2_CANDIDATE
```

## Reading the DAG

- **Every path into a Condition-B correct verdict passes through `SURFACED` — whether the real
  retrieval mechanism actually found the taught rule text.** This design's `state_read` instrumentation
  makes this directly observable per trial (the Learning Investigation's own pilot already showed this
  is not guaranteed to happen even when the content was genuinely written). A correct verdict in B
  with `SURFACED=yes` is cleanly, structurally L1 — there is no other path to it in this graph.
- **Condition C has exactly one path to `GEN`, and it never passes through any real memory
  content.** This is the entire point of the design: if a correct verdict occurs here, the DAG shows
  there is no confirmed causal path from Formation to that response *except* through whatever
  persistent state the model's own weights/session carry — which, per the architecture mapping
  document, `EchoDirectResponder` is confirmed to hold none of (no cross-call memory of any kind).
- **Three confound paths are drawn explicitly, not glossed over**, because a correct Condition-C
  verdict must be checked against all three before being escalated beyond `UNKNOWN`:
  1. **Chance** — a binary-shaped or otherwise coincidental match. Mitigated but not eliminated by the
     dictionary/forbidden-substring screening (an invented tag word appearing in a response for
     reasons unrelated to the rule is astronomically unlikely given the screening, but "unlikely" is
     not "impossible," and this design does not claim otherwise).
  2. **Model stylistic prior** — some base models exhibit a tendency to echo or invent similarly-shaped
     nonsense tokens under certain prompt conditions, unrelated to genuine rule-following. This is a
     real, documented-in-the-literature LLM behavior class, not specific to this design, and must be
     considered before crediting a Condition-C success to rule retention.
  3. **Unrelated production-memory leak** — since Condition C's probe still runs through
     `EchoDirectResponder` (which itself does not query memory, per the architecture mapping), this
     specific confound path is structurally closed for THIS design's own probe call — drawn here for
     completeness and to make explicit that it is closed by construction, not merely assumed away.

## What this DAG does NOT let this design claim

No path in this graph terminates directly at "L2 confirmed." The strongest possible outcome this
design can produce is `UNKNOWN (L2 CANDIDATE)` — a result that, after every known confound is checked
and found not to explain it, would warrant a dedicated, separate, adversarially-designed follow-up
investigation specifically built to explain the anomaly. This is a deliberate, structural feature of
the design, not a limitation to be worked around: per the mission's own rule, "if unknown → UNKNOWN,
not learning," and per the two prior architecture audits' own conclusions, the prior probability of a
genuine, currently-unidentified L2 channel existing in this codebase is low enough that a single
pilot's positive result should never, on its own, be reported as more than a candidate for further
work.
