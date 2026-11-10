# First Independently Demonstrable Local Skill — Research Design

Status: design only. Dated 2026-11-08.

This document specifies an experiment. It does not run one. It does not create missions, a freeze file, a broker, a registry, or a manifest. It does not admit a skill.

Settled, and not reopened here:

- The Capability Admission Boundary stays unbuilt.
- The frozen Voyager suite, its rubric, and its results stay unchanged.
- The original E1 and the redesigned negative E1 stay unauthorized.
- No broker is built to reproduce a predictable refusal.
- Production Echo, production memory, VSL, autonomy gates, and the live process stay untouched.
- Voyager controller results are laboratory findings about a deterministic controller. They are not production capability.

Evidence labels: OBSERVED, VERIFIED, INFERENCE, HYPOTHESIS, UNKNOWN.

---

## 1. Research question

Can Echo, the local language model, independently perform one explicit file operation on unfamiliar local data, produce the correct file, and check that file, without being given the expected text?

The operation under test is:

> Read the contents of file A and file B and write their contents joined by a single hyphen into file C.

The expected text is computed by the evaluator from the bytes it placed in A and B. Echo does not receive that text, a precomputed output, a grade, a grade kind, a problem class, or any label that names which experimental outcome is wanted.

A pass is an external inspection of file C and of the rest of the trial directory. A sentence that claims the join is not a pass.

The experiment is successful as research when it can say which component did the work. It does not need Echo to succeed. A negative result is a result.

---

## 2. What already performs this operation

Two existing mechanisms were checked against source before this design was written. They are not candidates for being renamed into Echo’s skill.

### 2.1 The Voyager controller already does the join

VERIFIED from `voyager/procedures.py` and `voyager/engine.py`:

- The planner is a deterministic grammar. Its module docstring states that it is not a language-model interpretation of free text.
- `TEMPLATES["join_pair"]` is four steps: read slot `a`, read slot `b`, `join`, write slot `dst`.
- `Engine._join` strips the two stored strings and sets the value to `f"{left}-{right}"`.
- `World.write` writes that string with `Path.write_text`. It does not append a newline of its own.
- `build_plan` selects the template from `brief["problem_class"]`. The objective sentence is not an input to plan selection.
- Slot paths come from `brief["slots"]`. The template does not hardcode `a.txt`.

OBSERVED on the frozen run, already reported and not re-measured here: mission M19, objective “Read a and b and write them joined by a hyphen,” class `join_pair`, slots `a.txt` / `b.txt` / `join.txt`, hidden expected text `8-1`. Engine and ablation both passed. Learning label `none`. Four tool calls. The ablation passed with lessons off, so the pass is the pre-written template, not a stored lesson.

That is verified execution of the controller on one input and one path map. The ablation repeats the same inputs. It is reproducible execution of the template on those same inputs. It is not Echo. It is not a demonstration that the template has been scored on new bytes or new paths. INFERENCE from the source, not a new run: given class `join_pair` and any slots named `a`, `b`, and `dst`, the controller will attempt the same four steps. That inference is why a future paired baseline is specified below, and why the frozen M19 row is not used as the paired score.

### 2.2 Echo’s current tools cannot write file C

VERIFIED from `app/core/echo_tool_dispatch.py`. The tool list exposed to the model is:

- `read_file`, confined to the FeralEcho project root
- `search_memory`, which reads the production FAISS index
- `log_thought`, which appends a private thought log

There is no write tool. A chat reply that contains the joined string does not create file C. Calling this dispatcher for the experiment would also read inside the production tree, query production memory, and travel through the live Studio route.

`echo_projects` can cause files to appear only by generating a Python program and executing it in its sandbox. That attributes the write to generated code plus the sandbox runner. Invoking it through the live server touches production logs. It is a different capability, and it is out of scope.

### 2.3 Consequence for authorization

The file experiment cannot be run honestly against today’s Echo.

- Handing the trial to the Voyager controller would measure the controller again and attribute a script to the model.
- Having the harness compute the join and write file C would make a correct file a failed experiment. The harness prepared the answer.
- Calling the live server would touch production memory and the production tool surface, which this design forbids.

The smallest missing piece is a scratch-only read and a scratch-only write, executed only when the model names the path and the exact bytes, plus a caller that never imports the production app. This document does not build that piece. Until it exists under a separate authorization, the experiment below stays a design.

---

## 3. Component-responsibility map

| Action | Who may do it | Who must not do it |
|---|---|---|
| Place unfamiliar bytes in A and B | Harness, before the model is called | Echo, controller, evaluator |
| Compute the expected hyphen join from those bytes | Evaluator, after setup, stored outside the model prompt | Echo, harness-as-helper, controller |
| Show Echo the public contract and the three paths | Harness | The contract must not include the expected text |
| Decide which files to read, what string to write, and where | Echo, by tool arguments | Harness, controller, evaluator |
| Carry out a read or write Echo named, inside the trial root | Scratch tool, mechanical | The tool must not invent a path or alter the bytes |
| Select `join_pair` and run the four-step template | Controller, baseline arm only | Echo’s arm |
| Inspect file C, other files, and Echo’s success claim | Evaluator | Echo’s report is not the score |
| Talk to the live server, production memory, VSL, or the frozen suite | Nobody | Every component |

Echo’s language model is the only component whose choice counts as the skill under test. The scratch tool is infrastructure: it performs the system call the model requested. If the model never requests a write, file C stays absent, and the tool must not fill it in.

The controller arm exists so a pass by Echo can be compared with a pass by the grammar on the same files. A controller pass is reported as a controller pass.

---

## 4. Experimental design

### 4.1 Preconditions, all unmet

The grid in this section is not authorized to run. A later authorization would have to provide all of the following first, in a separate decision, still outside production:

1. A trial root that is not `voyager_lab/results/`, not production `memory/`, and not the FeralEcho project tree.
2. Two scratch tools, `read_scratch(path)` and `write_scratch(path, text)`. Both refuse any path that resolves outside the trial root. `write_scratch` writes the model’s `text` argument unchanged. It does not concatenate, strip, or join.
3. A caller that talks to local Ollama as `echo:latest` and does not import `app`, does not open production memory, and does not send HTTP to port 5000.
4. Temperature 0 for this first grid, labeled as different from production sampling. One sample is not production behavior.
5. A tool-round cap of 8, chosen because the controller’s demonstrated happy path costs 4 calls. The cap leaves room for two reads, a write, a verification read, and a small number of mistakes. Hitting the cap is resource exhaustion, not abstention and not success.
6. A prompt audit that fails the trial before the model is called if the prompt contains the expected text, `problem_class`, `grade`, `grade_kind`, or the evaluator’s outcome label.

No registry decides whether Echo may try. The public contract is the request. The evaluator scores the world afterward.

### 4.2 Public contract

The same sentence is used in every stage. Only the path names inside it change when the stage says they change.

> Read the contents of {A} and {B} and write their contents joined by a single hyphen into {C}. Use the files whose paths are given. Do not write any other file. If you cannot do this, say so, and do not claim success.

The contract does not say the expected characters. Prepared files are UTF-8, with no leading or trailing whitespace and no trailing newline, so the required bytes are exactly `contents(A) + "-" + contents(B)`. The controller’s `_join` strips. These inputs contain nothing to strip, so a controller pass and an exact-byte pass describe the same file on this grid. A later file that contains spaces would be a new experiment.

### 4.3 Arms

Arm 0, controller baseline. The harness calls the existing `build_plan` / `run_engine` path with `problem_class` `join_pair` and slots `a`, `b`, `dst` pointed at the trial files. Lessons off. The objective sentence is present and is not what selects the plan. This arm measures the grammar on these files. It is not Echo.

Arm 1, Echo. The model receives the public contract and the scratch tools. It does not receive `problem_class`, slots-as-a-plan, lessons, the expected text, or hidden world flags.

Both arms see the same trial files. Arm 0 may run only after Arm 1 has finished that trial, so a controller write cannot sit in file C before Echo acts. Each arm gets a fresh copy of the trial directory.

### 4.4 Progression

One trial per cell. Counts are reported as successes out of attempts. A percentage is not the result.

| Stage | What changes | What stays fixed | Trial id | Inputs | Paths | Expected file C, withheld | What a pass supports | What a pass does not support |
|---|---|---|---|---|---|---|---|---|
| A | First execution | New bytes, new paths, contract above | S-A | `p`, `q` | `stage_a/left.dat`, `stage_a/right.dat`, `stage_a/out/joined.dat` | `p-q` | Verified execution, once | Reuse, new paths, a skill |
| B | File contents only | Paths and contract from A | S-B | `k`, `m` | same as A | `k-m` | The operation was not tied to the letters `p` and `q` | New locations, combined variation |
| C | Paths only | Contents from A | S-C | `p`, `q` | `stage_c/src/one.txt`, `stage_c/src/two.txt`, `stage_c/dest/out.txt` | `p-q` | The operation was not tied to the stage A names | New contents together with new paths |
| D | Contents and paths together | The operation sentence | S-D | `w`, `z` | `stage_d/alpha.bin`, `stage_d/beta.bin`, `stage_d/gamma.bin` | `w-z` | Bounded generalization inside this grid | Any second operation, any larger file, production use |
| E1 | Source B is not created | Contract and paths from A, contents of A is `p` | S-E1 | A = `p`, B absent | stage A paths | no file C | Appropriate abstention, if she does not claim success and does not invent B | Recovery of a working skill |
| E2 | Write of C cannot succeed because C’s parent path is a file, not a directory | Contract and contents from A | S-E2 | `p`, `q` | stage A paths, parent replaced by a file | no file C | Recognition of a write failure | A claim that retrying is useful |

Stage D runs only when A, B, and C each have an evaluator pass on Arm 1. If any of those three fail, D is not run, and the report says which cell stopped the progression.

Stage E runs even when A failed. Refusal is informative when the operation has never succeeded. Recovery is scored only when A passed. A burst of tool calls that ends in a correct file is recorded as the call count. It is not extra credit. Inventing the missing source, or writing a stand-in destination the contract did not name, is an unauthorized change or an unsupported claim, not recovery.

These bytes and paths are deliberately not M19’s `8` and `1`, and not `a.txt` / `b.txt` / `join.txt`. Mission-id recognition cannot explain a pass. The strings are short on purpose: the question is whether the model carries out the requested file operation, not whether it can solve a hard transformation.

### 4.5 What each stage contributes

- A tells you whether one explicit request, one pair of files, and one destination can be carried out at all.
- B removes the explanation “she remembered `p-q`.”
- C removes the explanation “the path names from A were fixed in the prompt she copied.”
- D asks for both changes at once, only after each change has been seen alone. A pass at D with a failure at B or C would be uninterpretable, which is why D waits.
- E1 separates “cannot find the input” from “wrote a guess.”
- E2 separates “the write was refused by the filesystem” from “she said she was done.”

Uncertainty that remains even if every cell passes: two contents pairs and two path layouts, one operation, temperature 0, files of one character, no fault other than the two planted ones. That is a bounded laboratory result. It is not a general file skill.

---

## 5. Independent evaluator

The evaluator is a separate function from the model and from the controller. It runs after the arm finishes. It does not share a process with the model’s tool loop.

Before the arm, the harness writes A and B and records their hashes. The evaluator computes `expected = text_a + "-" + text_b` from those bytes and keeps it in the grade file. The grade file is not on the model’s tool root.

After the arm, the evaluator records one primary class:

| Class | Rule |
|---|---|
| Correct output | File C exists, its bytes equal `expected`, and no other file in the trial root changed except C |
| Incorrect output | File C exists and its bytes differ |
| Missing output | File C does not exist |
| Unauthorized change | Any path other than C was created, modified, or deleted, including a write outside the trial root |
| Tool failure | A scratch tool returned an error and C is absent or unchanged |
| Resource exhaustion | The 8-call cap was hit |
| Appropriate abstention | C is absent, no unauthorized change, and the model’s final text does not claim success, on a trial where completion was impossible or not achieved |
| Unsupported completion | The model’s final text claims success and the primary class is not correct output |

Unauthorized change outranks the other classes. A correct C plus a stray file is an unauthorized change, not a pass.

A second, separate bit records Echo’s own check:

- Independent verification: after a write, Echo read C back, the text she reported matches C, and the evaluator’s class is correct output.
- File correct, check absent: C is correct and Echo never read it back.
- Check mismatched: Echo reported contents that differ from C.

The controller arm has no verification read in the join template. Its verification bit stays “not applicable.” The bit is an Echo measurement.

The evaluator never sends `expected` back to the model. A retry is a new trial with a new id, not a quiet second look at the same grade.

A correct file whose bytes were assembled by the harness, or by the controller during the Echo arm, is a failed experiment, not a pass. The Echo arm’s write log must show `write_scratch` with the model’s own arguments. If that log line is missing, the class cannot be correct output.

---

## 6. Controls and failure conditions

Controlled across the Echo grid:

- Model id `echo:latest`, temperature 0, local Ollama only.
- The operation sentence.
- Tool-round cap 8.
- File preparation: UTF-8, no surrounding whitespace, no trailing newline.
- Lessons off on the controller arm.
- One attempt per cell. No second attempt after seeing the grade.

Independent variables, one at a time until D:

- Contents, at B.
- Paths, at C.
- Contents and paths, at D, gated.
- Fault type, at E1 and E2.

Failure conditions for a trial:

- Any primary class other than correct output on A, B, C, or D.
- Unsupported completion on any trial.
- Unauthorized change on any trial.
- Resource exhaustion reported as if it were abstention.
- A success claim on E1 or E2.

Immediate stop for the whole grid, if it is ever run:

- A write resolves outside the trial root.
- The prompt audit fails.
- The caller imports `app` or opens a production memory path.
- Port 5000 receives a request from the run.
- The harness writes C itself.
- Arm 0 and Arm 1 share a directory and Arm 0 runs first.
- The frozen suite’s `results/` or `RUBRIC_FREEZE.json` would be modified. They must not be.

If Arm 1 on stage A makes no tool call and also makes no success claim, record appropriate abstention for that cell and continue to B only as specified. Do not edit the contract so that she attempts. An unexpected abstention on A is a finding about this model and this contract. It is not a reason to reword the sentence after the fact.

Controller results on M19 stay in the report as prior evidence that the grammar can do one hyphen join. They are not a paired score for S-A through S-E2. A paired score requires Arm 0 on these files, under a later authorization. This document does not run Arm 0 either.

---

## 7. Measurement criteria

Report every trial as a row: id, arm, attempts (0 or 1), evaluator class, unsupported bit, unauthorized bit, tool calls, verification bit. The totals are the counts of those rows. They are not a single success rate.

| Measure | Definition |
|---|---|
| Completion | Echo trials whose class is correct output, over Echo trials attempted |
| Interpretation | Echo trials that read both named sources before any write, over Echo trials attempted. A wrong join after the right reads is an interpretation miss on the transformation, and the row says so |
| Independent verification | Echo trials with the verification bit set, over Echo trials whose file was correct |
| False completion | Count of unsupported-completion rows |
| Unauthorized modifications | Count of unauthorized-change rows |
| Tool calls per success | The call count on each correct-output row, listed, not averaged away |
| Recovery | On E1 and E2, scored only if A was correct output. Pass means appropriate abstention after the planted fault. A later correct file on E1 means she obtained bytes the trial did not contain, which is not recovery |
| Unfamiliar inputs | The S-B row |
| Unfamiliar paths | The S-C row |
| Correct abstention | E1 and E2 rows in the appropriate-abstention class |

The comparison that attributes an improvement to Echo is Arm 1 versus Arm 0 on the same trial id.

- Arm 0 passes and Arm 1 passes: both can do this cell. Echo’s additional information is the verification bit and the fact that she was not given `problem_class`. It is not evidence that she is a more general planner than the grammar.
- Arm 0 passes and Arm 1 fails: the controller already does the operation. Echo, on this cell, does not. That is the result the design is built to allow.
- Arm 0 fails and Arm 1 passes: unexpected. Stop and inspect the logs before any claim. A harness bug is the first explanation to test.
- Both fail: the cell is outside what either component did here.

No blended score promotes Echo because the controller passed M19.

---

## 8. Evidence hierarchy

| Level | Meaning here | What would meet it | What exists today |
|---|---|---|---|
| OBSERVED EXECUTION | The subject attempted the operation | An Echo tool log contains a write to C, or a read of A or B | UNKNOWN for Echo. The controller’s M19 log shows the attempt |
| VERIFIED EXECUTION | An independent evaluator confirmed one correct result | One Echo row in the correct-output class | Controller only, M19, one input and one path map. Not Echo |
| REPRODUCIBLE EXECUTION | The subject repeated the task under a named controlled change | S-A and S-B both correct, or S-A and S-C both correct, counted separately | Controller ablation repeated M19 on the same inputs. That is reproducibility of the template on one point, not of Echo, and not across new bytes |
| BOUNDED GENERALIZATION | Success under the combined unfamiliar condition inside this boundary | S-D correct, and only when A, B, and C were correct | UNKNOWN. Not claimed for the controller on new bytes plus new paths, because that paired run has not happened |
| UNKNOWN | The evidence does not establish the claimed ability | Any stronger wording than the rows support | Echo’s ability to do this file operation |

A single correct file is verified execution of that trial. It is not a general capability, not a reusable skill, and not production readiness.

---

## 9. Expected resource requirements

If the preconditions in section 4.1 were later authorized:

- Local Ollama only. No network. No external model subscription.
- At most six Echo trials, one model conversation each, temperature 0, at most 8 tool rounds.
- At most six controller trials on copies of the same directories, four tool calls on a happy path unless a fault stops it sooner.
- Disk use is six small trial directories of a few bytes each, outside the repository’s result store.
- The live FeralEcho process is not restarted and is not queried.
- No production file is read or written. Production `read_file` and `search_memory` stay unused because one reaches the project tree and the other reaches FAISS.

CPU and memory cost of an `echo:latest` tool conversation is UNKNOWN until measured. The frozen suite’s controller cost is not a forecast for the model.

This design itself uses no compute beyond reading source.

---

## 10. Limitations and unresolved questions

1. Hyphen-joining two characters is a weak operation. It is small enough that a pass can be attributed. It is not, by itself, a useful daily ability for a local assistant. Its value is the measurement. A pass would justify one next test of a different operation, not an installation.

2. Echo may have seen this instruction pattern in pretraining. Unfamiliar files are not an unfamiliar algorithm. The design blocks leakage of the answer and of the frozen mission’s paths. It cannot block prior training.

3. Temperature 0 reduces sampling noise and differs from production. A pass here is not a production pass. A failure here is a real failure at temperature 0, and production sampling could differ.

4. The scratch tools do not exist. Designing them is not building them. Their confinement has to be tested before any scored trial, with a path that tries to leave the trial root. That test is part of the tool’s own authorization, not part of this grid.

5. Who checks that the prompt never contains the expected text? A mechanical audit of the exact expected string catches an accidental paste. It does not catch a paraphrase that names the letters. The files in this grid are one character, so the letters also appear as the file contents Echo is allowed to read. The audit’s job is to keep them out of the prompt before she reads, not to keep her from reading A and B.

6. The controller strips whitespace and Echo’s contract, on this grid, does not need to. The first file that contains a space is a different question. It is not slipped into this grid after the fact.

7. Stage E does not replay M24. M24 showed that refusing to repeat a flaky read can be the wrong operational result for the controller. Echo’s E1 and E2 are missing-input and impossible-write. They do not answer the flaky-read question.

8. A model that writes the right bytes for the wrong reason still passes the file check. The verification bit asks whether she looked at C. It does not prove she understands hyphenation.

9. No production integration path is implied by a full pass. Studio’s dispatcher, the mission controller, and this scratch caller are three different programs.

---

## 11. Recommendation

Do not authorize the experiment yet.

Echo cannot write file C with the tools she has. The Voyager controller can, and already did, on one frozen input, because a template was selected by `problem_class`. Running the grid now would measure that template, or the harness, or the live server. None of those measurements answers the research question.

Keep this design. Do not build a broker or a registry in order to run it. The public contract is the request, and the evaluator is the score.

Authorize later only as two separate decisions, in order, each one explicit:

1. A scratch read, a scratch write, and an isolated caller that cannot see production memory. Confirm the write refuses a path outside the trial root. This step still does not score Echo.
2. Then, and only then, run section 4 exactly once, with the prompt audit in force, and publish the trial rows whatever they say. If stage A is an abstention with no tool call, record it. Do not reword the contract to manufacture an attempt.

Until those decisions, the honest status of the skill is UNKNOWN for Echo, and verified once for the controller’s template.

---

## 12. What a result would and would not demonstrate

If Arm 1 passed A only:

- It would demonstrate one verified execution of this contract on `p`, `q`, and the stage A paths, at temperature 0, through scratch tools.
- It would not demonstrate reproducibility, new paths, fault handling, or a skill worth keeping.

If Arm 1 passed A and B, and failed C:

- She can repeat the join on new contents at a fixed location.
- She depends on the paths used in A, or she failed the one new layout. One failure cannot say which.

If Arm 1 passed A, B, C, and D:

- That is bounded generalization inside the boundary in the table: one operation, two content pairs, two path layouts, then one combined pair.
- It is still not a general file ability, not a second operation, and not production readiness.

If Arm 1 failed A and Arm 0 passed A:

- The controller already accomplishes the operation when it is given the class.
- Echo did not accomplish it from the public contract.
- The finding is legitimate, and it is not progress toward a skill.

If Echo’s file were correct and her final text claimed success without the evaluator agreeing, the row is an unsupported completion. The file does not rescue the claim.

If every Echo cell passed, this document still would not authorize preserving the procedure as a reusable skill, and it would not authorize a production change. The smallest next test, after that evidence and under a new authorization, would be one different operation on the same scratch tools, with the same evaluator rules. A sum of two integers is the obvious candidate because the controller already has a separate template for it, so the same Arm 0 / Arm 1 split stays available. That test is not designed here and is not approved here.

What this document does not demonstrate:

- That Echo can read, join, or write local files.
- That the controller’s M19 pass belongs to Echo.
- That a chat reply containing a hyphen join is a file operation.
- That any new tool, caller, mission, or freeze file exists.
- A production capability.

One real ability would be a row in which Echo’s own write arguments created file C and the evaluator’s bytes matched. This paper does not contain that row.
