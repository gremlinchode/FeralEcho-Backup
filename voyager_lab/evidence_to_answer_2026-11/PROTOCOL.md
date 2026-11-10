# Evidence-to-answer experiment protocol

Frozen before any generation. Scoring rules in this file are the rules.
Do not change them after any model reply is observed.

Seal order: answer_key.json, items.json, preflight.py, PROTOCOL.md, score.py

## Acceptance

Exactly 10 completed model replies are required.
At least 8 of 10 answers must be correct under these scoring rules.
Incomplete is not Outcome A.
Fewer than 10 completed replies stops Phase Two.
More than one completed model reply for one Phase One item makes that item incomplete.
Do not pick the favorable reply.
Zero completed replies for an item makes that item incomplete.

## Outcomes

Outcome A: exactly 10 completed replies and fewer than 8 correct. Stop.
Do not run Phase Two. Do not build memory architecture. Do not run a correction round.
Outcome B: same-turn utilization passes and storage fails.
Outcome C: storage succeeds and retrieval fails.
Outcome D: storage and retrieval succeed and utilization fails.
Outcome E: storage, retrieval, and utilization all succeed on the tested items.
A mixed result stays mixed.
Outcome E does not establish generalized learning.

## Budget and pathway

The generation budget is 22 local echo:latest generations.
The mode is fast.
The pathway is POST http://127.0.0.1:5000/chat/stream.
The request body is conversation_id, message, and mode fast.
The contingency budget is 2 infrastructure retries in total, not per item.
Every POST counts toward 22, including an infrastructure failure.
Do not retry a completed wrong answer.
A legitimate retry uses the same conversation_id.
The wall-clock limit and the socket timeout are both 180 seconds.
Score done.text only.
An empty done.text with the done event present is a completed wrong reply.
Do not concatenate token text into a substitute answer.
If task_type on a completed reply is not exactly general, record it and do not retry.
HTTP status 400 or higher is infrastructure.
A connection failure is infrastructure.
A timeout is infrastructure.
The exact server-error sentence is infrastructure: Error: could not generate a response.
The same sentence without the period is not infrastructure.
The same sentence with two periods is not infrastructure.

## Scoring

Strip the done text.
Then remove at most one trailing period when the key does not already end with a period
and the stripped text ends with exactly one period.
No partial credit.
Extra words, a case mismatch, internal extra whitespace, quotes, and a caveat suffix fail.
Do not award partial credit after observing an incorrect response.
Echo does not grade herself.

## Phase Two

Phase Two runs only when the Phase One gate passes.
The delay is 1860 seconds after the latest Phase One finished_at.
Each Phase Two trial uses a new conversation id.
The delayed question does not contain the fact sentence.
Unknown remains an available storage outcome.
Unknown remains an available retrieval outcome.
A correct later answer does not establish storage.
A correct later answer does not establish retrieval.
A memory write does not establish retrieval.
Retrieving only a short key-only echo reply does not count as retrieving the fact.
That combination is not a clean Outcome C or Outcome E.
Item 05 is the only Phase Two closed-set exception.
Its key is the word no, which is inside the yes or no reply instruction.
The item 05 fact sentence must still be absent from the Phase Two prompt.

## Limitation, not a deviation

Production fast mode may place session history and up to k=5 memories
older than 30 minutes into the system note.
Phase One is therefore not a note-only input.
This is existing pathway behavior.
Do not disable it.
Do not create DEVIATIONS.md until a deviation exists.

## Items

### 01

Fact: The dock badge mark is K7-QRV-4419.
Question: What is the dock badge mark?
Key: K7-QRV-4419
Phase 1 conversation: e2a-p1-01
Phase 2 conversation: e2a-p2-01

Phase 1 prompt:

```text
Note: The dock badge mark is K7-QRV-4419.

Question: What is the dock badge mark?

Reply with only the value. Use the same spelling as the note. Do not add words.
```

Phase 2 prompt:

```text
Question: What is the dock badge mark?

Reply with only the value. Use the same spelling as the earlier note. Do not add words.
```

### 02

Fact: Crate 14 has a mass of 18.6 kilograms.
Question: What is the mass of crate 14?
Key: 18.6 kilograms
Phase 1 conversation: e2a-p1-02
Phase 2 conversation: e2a-p2-02

Phase 1 prompt:

```text
Note: Crate 14 has a mass of 18.6 kilograms.

Question: What is the mass of crate 14?

Reply with only the value. Use the same spelling as the note. Do not add words.
```

Phase 2 prompt:

```text
Question: What is the mass of crate 14?

Reply with only the value. Use the same spelling as the earlier note. Do not add words.
```

### 03

Fact: Helio reports to Sable.
Question: Who does Helio report to?
Key: Sable
Phase 1 conversation: e2a-p1-03
Phase 2 conversation: e2a-p2-03

Phase 1 prompt:

```text
Note: Helio reports to Sable.

Question: Who does Helio report to?

Reply with only the value. Use the same spelling as the note. Do not add words.
```

Phase 2 prompt:

```text
Question: Who does Helio report to?

Reply with only the value. Use the same spelling as the earlier note. Do not add words.
```

### 04

Fact: Permit P-19 has the seal date 2026-04-17.
Question: What is the seal date on permit P-19?
Key: 2026-04-17
Phase 1 conversation: e2a-p1-04
Phase 2 conversation: e2a-p2-04

Phase 1 prompt:

```text
Note: Permit P-19 has the seal date 2026-04-17.

Question: What is the seal date on permit P-19?

Reply with only the value. Use the same spelling as the note. Do not add words.
```

Phase 2 prompt:

```text
Question: What is the seal date on permit P-19?

Reply with only the value. Use the same spelling as the earlier note. Do not add words.
```

### 05

Fact: Lane 4 is not closed.
Question: Is lane 4 closed?
Key: no
Phase 1 conversation: e2a-p1-05
Phase 2 conversation: e2a-p2-05

Phase 1 prompt:

```text
Note: Lane 4 is not closed.

Question: Is lane 4 closed?

Reply with only the lowercase word yes or no.
```

Phase 2 prompt:

```text
Question: Is lane 4 closed?

Reply with only the lowercase word yes or no.
```

### 06

Fact: Vat B contains more liquid than vat A.
Question: Which vat contains more liquid?
Key: Vat B
Phase 1 conversation: e2a-p1-06
Phase 2 conversation: e2a-p2-06

Phase 1 prompt:

```text
Note: Vat B contains more liquid than vat A.

Question: Which vat contains more liquid?

Reply with only the value. Use the same spelling as the note. Do not add words.
```

Phase 2 prompt:

```text
Question: Which vat contains more liquid?

Reply with only the value. Use the same spelling as the earlier note. Do not add words.
```

### 07

Fact: The gold items sit on shelf 22.
Question: Which shelf number has the gold items?
Key: 22
Phase 1 conversation: e2a-p1-07
Phase 2 conversation: e2a-p2-07

Phase 1 prompt:

```text
Note: The gold items sit on shelf 22.

Question: Which shelf number has the gold items?

Reply with only the value. Use the same spelling as the note. Do not add words.
```

Phase 2 prompt:

```text
Question: Which shelf number has the gold items?

Reply with only the value. Use the same spelling as the earlier note. Do not add words.
```

### 08

Fact: The bin total at dock C is 4.
Question: How many bins are at dock C?
Key: 4
Phase 1 conversation: e2a-p1-08
Phase 2 conversation: e2a-p2-08

Phase 1 prompt:

```text
Note: The bin total at dock C is 4.

Question: How many bins are at dock C?

Reply with only the value. Use the same spelling as the note. Do not add words.
```

Phase 2 prompt:

```text
Question: How many bins are at dock C?

Reply with only the value. Use the same spelling as the earlier note. Do not add words.
```

### 09

Fact: The night passphrase is moth-lantern.
Question: What is the night passphrase?
Key: moth-lantern
Phase 1 conversation: e2a-p1-09
Phase 2 conversation: e2a-p2-09

Phase 1 prompt:

```text
Note: The night passphrase is moth-lantern.

Question: What is the night passphrase?

Reply with only the value. Use the same spelling as the note. Do not add words.
```

Phase 2 prompt:

```text
Question: What is the night passphrase?

Reply with only the value. Use the same spelling as the earlier note. Do not add words.
```

### 10

Fact: The shipment block mark is R-88.
Question: What is the shipment block mark?
Key: R-88
Phase 1 conversation: e2a-p1-10
Phase 2 conversation: e2a-p2-10

Phase 1 prompt:

```text
Note: The shipment block mark is R-88.

Question: What is the shipment block mark?

Reply with only the value. Use the same spelling as the note. Do not add words.
```

Phase 2 prompt:

```text
Question: What is the shipment block mark?

Reply with only the value. Use the same spelling as the earlier note. Do not add words.
```
