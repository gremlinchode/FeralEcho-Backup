# Generic verified proposer B — implementation scope

The user's instruction to implement the recommendation authorizes this additive,
research-only prototype. C remains postponed. Prior protocols remain unchanged.

This version implements a deterministic source-only proposal engine, explicit
authority checks, an independent pairwise oracle/observation checker, a provisional
decision interface, and an exclusive-create durable journal. It does not connect
to production, load VSL, execute supplied candidate source, contact a model or
launch a retained-utility experiment.

Public developer tests may parse synthetic source strings and exercise arithmetic,
contract validation, proposal construction and supplied observation records. They
are component tests, not held-out semantic qualification. Candidate strings are
never imported, compiled or executed. Development failures may be fixed; there is
no claim of a frozen scientific run.

The prototype supports a conservative part of the proposed closed grammar.
Unsupported constructs return explicit refusal. The implementation README must
enumerate restrictions; coverage is not inferred from the design document.

Actual E0.1 launches remain unavailable. Independent custody/oracle approvals,
new-path and observer qualification, resource checks, a prospective execution
freeze and explicit experimental authorization remain prerequisites. Supplied
observations may support a PROVISIONAL decision only; they cannot qualify their
own execution boundary or authorize production writes.

Pre-existing authorities are pinned in opening.json. All authored files stay in
this namespace. No stage, commit, push, restart or production-state write.
