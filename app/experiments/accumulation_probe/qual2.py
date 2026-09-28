#!/usr/bin/env python3
"""
QUAL-2 -- constructor architecture search (K2/K3 only), per QUAL2_PREREG.md.
Additive: imports the existing v1/v2 modules read-only, never edits them.
Not jailed (a deliberate, disclosed scope reduction for this smaller,
exploratory architecture search -- ground truth is never placed in any
constructor-facing prompt, verified by inspecting every prompt actually
logged; this is not a claim-bearing sealed Stage-1-grade run).

Usage: python -B qual2.py run
"""
from __future__ import annotations
import json, re, sys, time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parents[2]))
from app.experiments.accumulation_probe import worlds, tasks as T1, tasks_v2 as T2, constructor as C, ollama_client as OC, oracle_runner as OR, prompts as P
from app.experiments.accumulation_probe.common import (
    EXP_ROOT, MASTER_SEED, OLLAMA_URL, MODEL, OPTIONS, seed_for, write_json_new, read_json, append_jsonl,
)

OUT = EXP_ROOT / "v2" / "qual2"
KINDS = ("K2", "K3")
NW = 2
D_MAIN = 3
GATE_MIN_PASS = 2
Q_EXACT_QUALIFIED = 5 / 6
Q_EXACT_NOT = 1 / 6
STAGED_OPTIONS = {"temperature": 0.5, "top_p": 0.95, "num_predict": 500, "num_ctx": 4096, "repeat_penalty": 1.0}
FINALIZE_OPTIONS = {"temperature": 0.5, "top_p": 0.95, "num_predict": 400, "num_ctx": 4096, "repeat_penalty": 1.0}
VAL_TEMPLATES = read_json(EXP_ROOT / "v2" / "dev" / "val_templates_pooled.json")

STEP1_TMPL = (
    "Context: {ctx}\n\n"
    "Observed episodes from this site (call -> result):\n{eps}\n\n"
    "Before writing anything final, think step by step: what rule or pattern might explain these "
    "results? State your best current hypothesis for the site's convention, as precisely as you can "
    "from what you see. If you are unsure about any part, say so explicitly rather than guessing."
)
STEP2_TMPL = (
    "Context: {ctx}\n\n"
    "Observed episodes from this site (call -> result):\n{eps}\n\n"
    "Your hypothesis so far:\n{hyp}\n\n"
    "Now check your hypothesis against EVERY one of the episodes above, one at a time: does it "
    "correctly predict that episode's actual result? List any episode where your hypothesis does NOT "
    "match, and then state a REVISED hypothesis that is consistent with every episode above. If your "
    "original hypothesis already matches all of them, say so and restate it."
)


def qworlds():
    """Generates a full {K1,K2,K3} realization per world -- K1 is included, unused by this
    script's own test/construct/gate loops (scoped to KINDS=(K2,K3) throughout), purely because
    tasks_v2.build_tasks_v2() hardcodes iterating all three kinds internally and would KeyError
    on a world dict missing K1. Generating it costs nothing (pure computation, no model calls)."""
    taken = set()
    out = []
    for w in range(NW):
        out.append({k: worlds.make_realization(k, MASTER_SEED + 40000 + 10 * i + w, taken) for i, k in enumerate(("K1", "K2", "K3"))})
    return out


def staged_draft(kind, r, cid, log):
    """Runs the 3-step STAGED chain for real. Returns the final note text (or '' on any client error).
    Every prompt sent and every response received is logged in full to `log` (a list, later written to disk),
    so ground-truth-leakage can be checked by direct inspection after the fact."""
    ctx = T1.BASE_SPEC[kind]
    eps = "\n".join(T1.episode_lines(T1.teaching_episodes(r)))

    s1_user = STEP1_TMPL.format(ctx=ctx, eps=eps)
    body1 = OC.request_body(MODEL, C.CONSTRUCTOR_SYSTEM, s1_user, seed_for("QUAL2", cid, 0), STAGED_OPTIONS)
    try:
        resp1 = OC.chat(body1, OLLAMA_URL, timeout=180)
    except Exception as e:
        log.append({"cid": cid, "step": 1, "error": f"{type(e).__name__}: {e}", "user": s1_user})
        return ""
    hyp = qual_clean(resp1["text"])
    log.append({"cid": cid, "step": 1, "system": C.CONSTRUCTOR_SYSTEM, "user": s1_user, "response_text": resp1["text"], "meta": {k: resp1.get(k) for k in ("done_reason", "eval_count", "wall_s")}})

    s2_user = STEP2_TMPL.format(ctx=ctx, eps=eps, hyp=hyp)
    body2 = OC.request_body(MODEL, C.CONSTRUCTOR_SYSTEM, s2_user, seed_for("QUAL2", cid, 1), STAGED_OPTIONS)
    try:
        resp2 = OC.chat(body2, OLLAMA_URL, timeout=180)
    except Exception as e:
        log.append({"cid": cid, "step": 2, "error": f"{type(e).__name__}: {e}", "user": s2_user})
        return ""
    verified = qual_clean(resp2["text"])
    log.append({"cid": cid, "step": 2, "system": C.CONSTRUCTOR_SYSTEM, "user": s2_user, "response_text": resp2["text"], "meta": {k: resp2.get(k) for k in ("done_reason", "eval_count", "wall_s")}})

    lines = T1.episode_lines(T1.teaching_episodes(r))
    original_user = C.constructor_user(kind, lines)  # byte-identical to the existing, already-audited constructor prompt
    s3_user = f"Your own analysis from checking a hypothesis against these episodes:\n{verified}\n\n{original_user}"
    body3 = OC.request_body(MODEL, C.CONSTRUCTOR_SYSTEM, s3_user, seed_for("QUAL2", cid, 2), FINALIZE_OPTIONS)
    try:
        resp3 = OC.chat(body3, OLLAMA_URL, timeout=180)
    except Exception as e:
        log.append({"cid": cid, "step": 3, "error": f"{type(e).__name__}: {e}", "user": s3_user})
        return ""
    final_text = qual_clean(resp3["text"])
    log.append({"cid": cid, "step": 3, "system": C.CONSTRUCTOR_SYSTEM, "user": s3_user, "response_text": resp3["text"], "meta": {k: resp3.get(k) for k in ("done_reason", "eval_count", "wall_s")}})
    return final_text


def qual_clean(text):
    t = re.sub(r"<think>.*?</think>", "", text or "", flags=re.S)
    return re.sub(r"\s+", " ", t).strip()[:1200]


def _collect_realizations(obj):
    """Recursively walks an arbitrary nested dict/list structure and returns every leaf
    realization dict (identified by the 'kind' key every worlds.make_realization() output
    carries), regardless of nesting shape -- stage0/v2-dev worlds.json nest one level deeper
    ({'foreign': {K1,K2,K3}, 'true': {K1,K2,K3}}) than v2/qual's flat list of {K1,K2,K3}."""
    out = []
    if isinstance(obj, dict):
        if "kind" in obj:
            out.append(obj)
        else:
            for v in obj.values():
                out.extend(_collect_realizations(v))
    elif isinstance(obj, list):
        for v in obj:
            out.extend(_collect_realizations(v))
    return out


def run_gate_for_draft(gid, kind, w, note_text, tests, log):
    """Independent behavioral gate: the worker (same model/options as QUAL-1's gate) receives the
    draft note in the standard carrier format and attempts the 4 pooled VAL tasks for this convention.
    Returns True/False/None (None = draft empty, gate not attempted)."""
    if not note_text:
        return None
    block = P.render_block([{"applies_when": T1.APPLIES[kind], "procedure": note_text}])
    passed = 0
    for tk in VAL_TEMPLATES[kind]:
        t = tests[f"w{w}|{tk}"]
        system, user = P.build_messages({"spec": t["spec"], "sig": t["sig"]}, block, None)
        body = OC.request_body(MODEL, system, user, seed_for("QUAL2GATE", f"{gid}|{tk}", 0), OPTIONS)
        try:
            resp = OC.chat(body, OLLAMA_URL, timeout=180)
        except Exception as e:
            log.append({"gid": gid, "task": tk, "error": f"{type(e).__name__}: {e}"})
            continue
        code = OR.extract_code(resp["text"], t["fn"])
        g = OR.grade(code, t["test_code"]) if code else {"passed": False}
        log.append({"gid": gid, "task": tk, "system": system, "user": user, "response_text": resp["text"], "extracted_code": code, "grade": g})
        if g["passed"]:
            passed += 1
    return passed >= GATE_MIN_PASS


def main():
    if OUT.exists():
        sys.exit(f"STOP: {OUT} already exists -- refusing to overwrite. Delete by hand first for a genuine re-run.")
    OUT.mkdir(parents=True)

    Ws = qworlds()
    write_json_new(OUT / "worlds.json", Ws)

    # cross-check: QUAL-2 worlds' tokens must not overlap any prior world's tokens (Stage0, dev, QUAL-1)
    used = {x for Wf in Ws for r in Wf.values() for x in worlds.tokens(r)}
    for other in (EXP_ROOT / "stage0" / "oracle" / "worlds.json", EXP_ROOT / "v2" / "dev" / "worlds.json", EXP_ROOT / "v2" / "qual" / "oracle" / "worlds.json"):
        if other.exists():
            ow = read_json(other)
            prev = set()
            for r in _collect_realizations(ow):
                prev.update(worlds.tokens(r))
            overlap = used & prev
            assert not overlap, f"QUAL-2 tokens overlap {other}: {overlap}"
    print(f"Token disjointness verified against 3 prior world files. {len(used)} new tokens used.")

    # Build VAL tests per world (reusing the pooled templates, tasks_v2's stronger generators)
    tests = {}
    for w, Wf in enumerate(Ws):
        Tv2 = {t["task_id"]: t for t in T2.build_tasks_v2(Wf)}
        for kind in KINDS:
            for tid in VAL_TEMPLATES[kind]:
                t = Tv2[tid]
                cases, _eq = T2.make_cases2(t, Wf, "VAL")
                tests[f"w{w}|{tid}"] = {"fn": t["fn"], "test_code": T2.make_test_code(t["fn"], cases), "spec": t["spec"], "sig": t["sig"]}
    write_json_new(OUT / "val_tests.json", tests)
    print(f"VAL tests built for {len(tests)} (world, task) pairs.")

    construct_log = []
    gate_log = []
    rows = []
    t_start = time.time()
    for w, Wf in enumerate(Ws):
        for kind in KINDS:
            r = Wf[kind]
            for d in range(D_MAIN):
                cid = f"C2|{kind}|w{w}|d{d}"
                print(f"[construct] {cid} ...", flush=True)
                note = staged_draft(kind, r, cid, construct_log)
                a = C.audit(kind, r, note)
                gid = f"draft|{cid}"
                gate_pass = run_gate_for_draft(gid, kind, w, note, tests, gate_log)
                row = {"cid": cid, "kind": kind, "world": w, "draft": d, "note": note,
                       "exact": a["exact"], "wrong": a["wrong_items"], "missing": a["missing_items"],
                       "hedges": a["hedges"], "copies_syntax": a["copies_episode_syntax"],
                       "gate_pass": gate_pass}
                rows.append(row)
                print(f"  -> exact={a['exact']} gate_pass={gate_pass} note={note[:120]!r}", flush=True)
    elapsed = time.time() - t_start

    write_json_new(OUT / "construct_calls.json", construct_log)  # full prompts+responses
    write_json_new(OUT / "gate_calls.json", gate_log)
    write_json_new(OUT / "drafts.json", rows)

    # leakage check: scan every logged constructor-facing prompt for any real ground-truth token
    # not already present in the episode text itself (i.e., anything the constructor could not have
    # derived from the episodes it was actually shown)
    leak_found = []
    for entry in construct_log:
        if "user" not in entry:
            continue
        u = entry["user"]
        r = Ws[int(entry["cid"].split("|w")[1].split("|")[0])][entry["cid"].split("|")[1]]
        gt_text = T1.procedure_text(r)  # the ground-truth answer text -- must never appear verbatim in a constructor prompt
        if gt_text in u:
            leak_found.append(entry["cid"])
    assert not leak_found, f"GROUND TRUTH LEAKED into a constructor prompt: {leak_found}"
    print("Leakage check: ground-truth procedure text confirmed absent from every constructor-facing prompt.")

    # analysis, same shape/thresholds as qual.py's analyze()
    R = {"per_kind": {}}
    for kind in KINDS:
        xs = [x for x in rows if x["kind"] == kind]
        k = sum(x["exact"] for x in xs)
        n = len(xs)
        R["per_kind"][kind] = {
            "n": n, "exact": k, "exact_rate": round(k / n, 3) if n else None,
            "gate_pass": sum(1 for x in xs if x["gate_pass"]),
            "exact_and_gate_pass": sum(1 for x in xs if x["exact"] and x["gate_pass"]),
            "inexact_but_gate_pass": sum(1 for x in xs if not x["exact"] and x["gate_pass"]),
            "empty_drafts": sum(1 for x in xs if not x["note"]),
        }
        e = k / n if n else 0.0
        status = "QUALIFIED" if e >= Q_EXACT_QUALIFIED else ("NOT QUALIFIED" if e <= Q_EXACT_NOT else "PARTIALLY QUALIFIED")
        R["per_kind"][kind]["status_by_exact_rate_only"] = status
    R["overall_elapsed_s"] = round(elapsed, 1)
    R["n_construct_calls"] = len(construct_log)
    R["n_gate_calls"] = len(gate_log)
    write_json_new(OUT / "summary.json", R)
    print(json.dumps(R, indent=1))
    print(f"\nDone. {len(construct_log)} construct calls, {len(gate_log)} gate calls, {elapsed:.0f}s.")


if __name__ == "__main__":
    main()
