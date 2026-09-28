"""AP-0 task templates, reference solutions, input generators, hidden-test construction, carrier entries and teaching episodes.
BUILD-SIDE ONLY: this module holds reference solutions and MUST NOT be imported by the jailed arm runner (checked by the import audit)."""
import copy, itertools, random
from . import worlds
from .common import sha256_obj, canon

# ---------- reference-solution source templates ({FN} is the function name; header constants come from the realization) ----------
def _hdr(name, obj): return f"{name} = {obj!r}\n"

_K1 = {
 "k1_sum": "def {FN}(records):\n    out = {{}}\n    for rec in records:\n        c = _MAP[rec['status']]\n        out[c] = out.get(c, 0) + rec['amount']\n    return out\n",
 "k1_count": "def {FN}(records):\n    out = {{}}\n    for rec in records:\n        c = _MAP[rec['status']]\n        out[c] = out.get(c, 0) + 1\n    return out\n",
 "k1_ids": "def {FN}(records, category):\n    return sorted(rec['id'] for rec in records if _MAP[rec['status']] == category)\n",
 "k1_top": "def {FN}(records):\n    tot = {{}}\n    for rec in records:\n        c = _MAP[rec['status']]\n        tot[c] = tot.get(c, 0) + rec['amount']\n    return min(tot, key=lambda c: (-tot[c], c))\n",
 "k1_tuples": "def {FN}(records):\n    out = {{}}\n    for (i, s, a) in records:\n        c = _MAP[s]\n        out[c] = out.get(c, 0) + a\n    return out\n",
 "k1_log": "def {FN}(text):\n    out = {{}}\n    for part in text.split(';'):\n        if not part: continue\n        i, s, a = part.split(':')\n        c = _MAP[s]\n        out[c] = out.get(c, 0) + int(a)\n    return out\n",
}
_RANK = "def _rank(entries):\n    return sorted(entries, key=lambda e: (-e[1], _PRI.get(e[2], 99), e[0]))\n"
_K2 = {
 "k2_win": _RANK + "def {FN}(entries):\n    return _rank(entries)[0][0]\n",
 "k2_rank": _RANK + "def {FN}(entries):\n    return [e[0] for e in _rank(entries)]\n",
 "k2_lose": _RANK + "def {FN}(entries):\n    return _rank(entries)[-1][0]\n",
 "k2_top2": _RANK + "def {FN}(entries):\n    return [e[0] for e in _rank(entries)[:2]]\n",
 "k2_dicts": "def {FN}(entries):\n    best = sorted(entries, key=lambda e: (-e['score'], _PRI.get(e['tag'], 99), e['name']))\n    return best[0]['name']\n",
 "k2_rounds": _RANK + "def {FN}(rounds):\n    return [_rank(r)[0][0] for r in rounds]\n",
}
_STEP = "def _step(s, ev):\n    t, k = _OPS[ev]\n    if t == 'add': return s + k\n    if t == 'sub': return s - k\n    if t == 'mul': return s * k\n    return k\n"
_K3 = {
 "k3_final": _STEP + "def {FN}(events, start):\n    s = start\n    for ev in events:\n        s = _step(s, ev)\n    return s\n",
 "k3_trace": _STEP + "def {FN}(events, start):\n    s = start\n    out = []\n    for ev in events:\n        s = _step(s, ev)\n        out.append(s)\n    return out\n",
 "k3_max": _STEP + "def {FN}(events, start):\n    s = start\n    m = start\n    for ev in events:\n        s = _step(s, ev)\n        m = max(m, s)\n    return m\n",
 "k3_first": _STEP + "def {FN}(events, start, limit):\n    s = start\n    for i, ev in enumerate(events):\n        s = _step(s, ev)\n        if s > limit: return i\n    return -1\n",
 "k3_csv": _STEP + "def {FN}(text, start):\n    s = start\n    for ev in (text.split(',') if text else []):\n        s = _step(s, ev)\n    return s\n",
 "k3_batches": _STEP + "def {FN}(batches, start):\n    out = []\n    for b in batches:\n        s = start\n        for ev in b:\n            s = _step(s, ev)\n        out.append(s)\n    return out\n",
}
_UNREL = {
 "u_evens": "def {FN}(numbers):\n    return sum(n for n in numbers if n % 2 == 0)\n",
 "u_revwords": "def {FN}(text):\n    return ' '.join(reversed(text.split()))\n",
 "u_flat": "def {FN}(lists):\n    return [x for sub in lists for x in sub]\n",
 "u_rle": "def {FN}(text):\n    import itertools\n    return [(k, len(list(g))) for k, g in itertools.groupby(text)]\n",
}
_ALL = {**_K1, **_K2, **_K3, **_UNREL}
_HEADER = {"K1": lambda r: _hdr("_MAP", r["map"]), "K2": lambda r: _hdr("_PRI", {t: i for i, t in enumerate(r["priority"])}),
           "K3": lambda r: _hdr("_OPS", {e: tuple(v) for e, v in r["ops"].items()})}

def solution_source(base, fn, r):
    body = _ALL[base].replace("{{", "{").replace("}}", "}").replace("{FN}", fn) if False else _ALL[base].format(FN=fn)
    return (_HEADER[base[:2].upper()](r) if base[0] == "k" else "") + body

# ---------- input generators ----------
_NAMES = ["amy", "bo", "cid", "dot", "eve", "fay", "gus"]
def _records(rng, r): return [{"id": i + 1, "status": rng.choice(r["codes"]), "amount": rng.randint(1, 20)} for i in range(rng.randint(4, 8))]
def _entries(rng, r, n=None):
    names = rng.sample(_NAMES, n or rng.randint(3, 6))
    return [(nm, rng.randint(1, 3), rng.choice(r["tags"])) for nm in names]
def _events(rng, r): return [rng.choice(r["events"]) for _ in range(rng.randint(2, 6))]
GEN = {
 "k1_sum": lambda g, r: (_records(g, r),), "k1_count": lambda g, r: (_records(g, r),), "k1_top": lambda g, r: (_records(g, r),),
 "k1_ids": lambda g, r: (_records(g, r), g.choice(worlds.CATS)),
 "k1_tuples": lambda g, r: ([(d["id"], d["status"], d["amount"]) for d in _records(g, r)],),
 "k1_log": lambda g, r: (";".join(f'{d["id"]}:{d["status"]}:{d["amount"]}' for d in _records(g, r)),),
 "k2_win": lambda g, r: (_entries(g, r),), "k2_rank": lambda g, r: (_entries(g, r),), "k2_lose": lambda g, r: (_entries(g, r),), "k2_top2": lambda g, r: (_entries(g, r),),
 "k2_dicts": lambda g, r: ([{"name": n, "score": s, "tag": t} for n, s, t in _entries(g, r)],),
 "k2_rounds": lambda g, r: ([_entries(g, r, g.randint(3, 4)) for _ in range(g.randint(2, 3))],),
 "k3_final": lambda g, r: (_events(g, r), g.randint(1, 6)), "k3_trace": lambda g, r: (_events(g, r), g.randint(1, 6)), "k3_max": lambda g, r: (_events(g, r), g.randint(1, 6)),
 "k3_first": lambda g, r: (_events(g, r), g.randint(1, 6), g.randint(5, 30)),
 "k3_csv": lambda g, r: (",".join(_events(g, r)), g.randint(1, 6)),
 "k3_batches": lambda g, r: ([_events(g, r) for _ in range(g.randint(2, 3))], g.randint(1, 6)),
 "u_evens": lambda g, r: ([g.randint(-9, 30) for _ in range(g.randint(4, 9))],),
 "u_revwords": lambda g, r: (" ".join(g.choice(["red", "blue", "sun", "moon", "tree", "rain", "ice"]) for _ in range(g.randint(2, 5))),),
 "u_flat": lambda g, r: ([[g.randint(0, 9) for _ in range(g.randint(0, 3))] for _ in range(g.randint(2, 4))],),
 "u_rle": lambda g, r: ("".join(g.choice("aabbc") for _ in range(g.randint(4, 10))),),
}

# ---------- carrier text ----------
def k1_table(r): return ", ".join(f"{c}->{r['map'][c]}" for c in r["codes"])
def k2_pri(r): return " > ".join(r["priority"])
def k3_table(r):
    d = {"add": "add {k}", "sub": "subtract {k}", "mul": "multiply by {k}", "set": "set to {k}"}
    return "; ".join(f"{e}: {d[r['ops'][e][0]].format(k=r['ops'][e][1])}" for e in r["events"])

APPLIES = {"K1": "a task that maps site status codes to categories (open, closed, hold)",
           "K2": "a task that ranks or picks among scored entries that carry a tag",
           "K3": "a task that applies site event names to an integer state"}
def procedure_text(r):
    k = r["kind"]
    if k == "K1": return f"Status-code table: {k1_table(r)}. Always translate each record's status code through this table before grouping, counting, filtering or comparing; never use the raw code as a category name."
    if k == "K2": return f"Rank best to worst by score (higher is better). Ties on score are resolved by tag priority, highest priority first: {k2_pri(r)}. If the tag priority is also equal, the alphabetically smaller name ranks better. The winner is the best-ranked entry, the loser is the worst-ranked entry."
    return f"Event table (apply events in order): {k3_table(r)}."
def procedure_entry(r): return {"applies_when": APPLIES[r["kind"]], "procedure": procedure_text(r)}

# ---------- teaching episodes ----------
def _call(base, fn, r, args):
    ns = {}; exec(solution_source(base, fn, r), ns); return ns[fn](*copy.deepcopy(args))
def teaching_episodes(r):
    k = r["kind"]; eps = []
    if k == "K1":
        for c in r["codes"]:
            a = ([{"id": 1, "status": c, "amount": 5}],); eps.append(("categorize", a, _call("k1_sum", "categorize", r, a)))
    elif k == "K2":
        pri = r["priority"]
        for i in range(3):
            a = ([("zed", 4, pri[i]), ("amy", 4, pri[i + 1])],); eps.append(("pick_winner", a, _call("k2_win", "pick_winner", r, a)))
        a = ([("mo", 2, pri[3]), ("nan", 2, pri[0]), ("pat", 2, pri[2])],); eps.append(("pick_winner", a, _call("k2_win", "pick_winner", r, a)))
    else:
        for e in r["events"]:
            for st in (2, 5):
                a = ([e], st); eps.append(("final_state", a, _call("k3_final", "final_state", r, a)))
    return eps
def episode_lines(eps): return [f"{fn}({', '.join(repr(x) for x in a)}) -> {out!r}" for fn, a, out in eps]

def identifiable(r, eps):
    """Brute force: exactly one convention in the hypothesis space is consistent with the teaching episodes."""
    k = r["kind"]; ok = 0
    if k == "K1":
        for combo in itertools.product(worlds.CATS, repeat=len(r["codes"])):
            h = {**r, "map": dict(zip(r["codes"], combo))}
            if all(_call("k1_sum", "categorize", h, a) == out for fn, a, out in eps): ok += 1
        return ok == 1
    if k == "K2":
        for perm in itertools.permutations(r["tags"]):
            h = {**r, "priority": list(perm)}
            if all(_call("k2_win", "pick_winner", h, a) == out for fn, a, out in eps): ok += 1
        return ok == 1
    for e in r["events"]:
        n = 0
        for t in worlds.OPS:
            for kk in range(1, 10):
                h = {**r, "ops": {**r["ops"], e: [t, kk]}}
                if all(_call("k3_final", "final_state", h, a) == out for fn, a, out in eps if a[0][0] == e): n += 1
        if n != 1: return False
    return True

# ---------- task registry ----------
KIND_T = {
 "K1": [("T1", "k1_sum", "categorize", "records", "Return a dict mapping each category name to the total `amount` of the records whose status code belongs to that category (only categories that occur appear as keys)."),
        ("T2", "k1_count", "count_by_category", "records", "Return a dict mapping each category name to the number of records whose status code belongs to it (only categories that occur appear as keys)."),
        ("T3", "k1_ids", "ids_in_category", "records, category", "Return the sorted list of `id` values of the records whose status code belongs to `category`."),
        ("T4", "k1_top", "top_category", "records", "Return the category name with the largest total `amount`; if two categories tie, return the alphabetically smaller name. `records` is non-empty.")],
 "K2": [("T1", "k2_win", "pick_winner", "entries", "Return the `name` of the best-ranked entry."),
        ("T2", "k2_rank", "rank_all", "entries", "Return the list of names ordered from best-ranked to worst-ranked."),
        ("T3", "k2_lose", "pick_loser", "entries", "Return the `name` of the worst-ranked entry."),
        ("T4", "k2_top2", "top_two", "entries", "Return the list with the names of the two best-ranked entries, in rank order (fewer if there are fewer entries).")],
 "K3": [("T1", "k3_final", "final_state", "events, start", "Apply the events in order to `start` and return the final state."),
        ("T2", "k3_trace", "state_trace", "events, start", "Return the list of states after each event, in order (same length as `events`; `start` itself is not included)."),
        ("T3", "k3_max", "max_state", "events, start", "Return the largest state seen, including `start` and the state after every event."),
        ("T4", "k3_first", "first_over", "events, start, limit", "Return the 0-based index of the first event after which the state is strictly greater than `limit`; return -1 if that never happens.")],
}
KIND_S = {
 "K1": [("S1", "k1_tuples", "categorize_tuples", "records", "Here `records` is a list of tuples `(id, status, amount)` instead of dicts. Return a dict mapping each category name to the total amount of the records whose status code belongs to that category (only categories that occur appear as keys)."),
        ("S2", "k1_log", "parse_log", "text", "Here `text` is a string of records joined by `;`, each written `id:status:amount` (for example `3:abcde:7;4:fghij:2`; the empty string means no records). Return a dict mapping each category name to the total amount of the records whose status code belongs to that category (only categories that occur appear as keys).")],
 "K2": [("S1", "k2_dicts", "pick_winner_dicts", "entries", "Here each entry is a dict with keys `name`, `score` and `tag` instead of a tuple. Return the `name` of the best-ranked entry."),
        ("S2", "k2_rounds", "winners_by_round", "rounds", "`rounds` is a list of entry lists (tuples as above). Return the list containing, for each round in order, the name of that round's best-ranked entry.")],
 "K3": [("S1", "k3_csv", "final_state_csv", "text, start", "Here the events are given as one string `text`, joined by commas (the empty string means no events). Apply them in order to `start` and return the final state."),
        ("S2", "k3_batches", "finals_for_batches", "batches, start", "`batches` is a list of event lists. Each batch starts again from `start`. Return the list of the final state of each batch, in order.")],
}
BASE_SPEC = {
 "K1": "`records` are dicts with keys `id` (int), `status` (str) and `amount` (int). Each status is a site-specific code and belongs to exactly one of the categories: open, closed, hold. Which code belongs to which category is the site's own convention.",
 "K2": "Entries are tuples `(name, score, tag)`. Entries are ranked from best to worst: a higher `score` ranks better; ties on score are resolved by the site's own tag priority (a higher-priority tag ranks better); if the tag priority is also equal, the alphabetically smaller `name` ranks better.",
 "K3": "Each event is a string naming an update to an integer state. What each event does to the state is the site's own convention.",
}
NEAR = {
 "K1": [("N1", "k1_sum", "categorize_explicit", "records", "Return a dict mapping each category name to the total `amount` of the records whose status code belongs to it (only categories that occur appear as keys)."),
        ("N2", "k1_count", "count_by_category_explicit", "records", "Return a dict mapping each category name to the number of records whose status code belongs to it (only categories that occur appear as keys).")],
 "K2": [("N1", "k2_win", "pick_winner_explicit", "entries", "Return the `name` of the best-ranked entry (entries are `(name, score, tag)` tuples; higher score ranks better, then tag priority, then alphabetically smaller name)."),
        ("N2", "k2_lose", "pick_loser_explicit", "entries", "Return the `name` of the worst-ranked entry (entries are `(name, score, tag)` tuples; higher score ranks better, then tag priority, then alphabetically smaller name).")],
 "K3": [("N1", "k3_final", "final_state_explicit", "events, start", "Apply the events in order to `start` and return the final state."),
        ("N2", "k3_trace", "state_trace_explicit", "events, start", "Return the list of states after each event, in order (same length as `events`).")],
}
UNREL = [("U1", "u_evens", "sum_evens", "numbers", "`numbers` is a list of ints. Return the sum of the even numbers."),
         ("U2", "u_revwords", "reverse_words", "text", "Return the words of `text` in reverse order, joined by single spaces."),
         ("U3", "u_flat", "flatten_once", "lists", "`lists` is a list of lists. Return one list with the elements of all inner lists, in order."),
         ("U4", "u_rle", "run_length_encode", "text", "Return the run-length encoding of `text` as a list of `(character, count)` tuples, in order.")]
EXPLICIT = {"K1": lambda r: f" The status-code table for THIS task is stated here and must be used exactly as written: {k1_table(worlds.mismatch(r))}. Records are dicts with keys `id`, `status`, `amount`; categories are open, closed, hold.",
            "K2": lambda r: f" The tag priority for THIS task is stated here and must be used exactly as written (highest priority first): {k2_pri(worlds.mismatch(r))}.",
            "K3": lambda r: f" The event table for THIS task is stated here and must be used exactly as written: {k3_table(worlds.mismatch(r))}. Events are strings; the state is an integer."}

def build_tasks(W):
    """W = {'K1': realization, 'K2':..., 'K3':...} -> list of task dicts (public fields + build-side fields)."""
    out = []
    for kind in ("K1", "K2", "K3"):
        r = W[kind]
        for split, table in (("T", KIND_T[kind]), ("S", KIND_S[kind])):
            for tid, base, fn, args, spec in table:
                out.append({"task_id": f"{kind}.{tid}", "kind": kind, "split": split, "base": base, "fn": fn, "sig": f"def {fn}({args}):",
                            "spec": f"{BASE_SPEC[kind]} Write `{fn}({args})`. {spec}", "solution_realization": "true"})
        for tid, base, fn, args, spec in NEAR[kind]:
            out.append({"task_id": f"{kind}.{tid}", "kind": kind, "split": "NEAR", "base": base, "fn": fn, "sig": f"def {fn}({args}):",
                        "spec": f"Write `{fn}({args})`. {spec}{EXPLICIT[kind](r)}", "solution_realization": "mismatch"})
    for tid, base, fn, args, spec in UNREL:
        out.append({"task_id": tid, "kind": None, "split": "UNREL", "base": base, "fn": fn, "sig": f"def {fn}({args}):",
                    "spec": f"Write `{fn}({args})`. {spec}", "solution_realization": "none"})
    return out

def task_realization(task, W):
    k = task["kind"]
    if task["solution_realization"] == "true": return W[k]
    if task["solution_realization"] == "mismatch": return worlds.mismatch(W[k])
    return None

def mutants(task, W):
    """[(label, source)] -- every single-step convention change + generic wrong solutions. All must FAIL the hidden tests."""
    r = task_realization(task, W); base, fn = task["base"], task["fn"]; out = []
    if r is not None:
        for lab, m in worlds.perturbations(r): out.append((lab, solution_source(base, fn, m)))
        out.append(("naive", solution_source(base, fn, worlds.naive(r))))
        if task["solution_realization"] == "mismatch":
            out.append(("applies_carrier_convention", solution_source(base, fn, W[task["kind"]])))
    out.append(("returns_none", f"def {fn}(*a, **k):\n    return None\n"))
    out.append(("returns_empty_list", f"def {fn}(*a, **k):\n    return []\n"))
    return out

def _run(src, fn, args):
    try:
        ns = {}; exec(src, ns); return ("ok", ns[fn](*copy.deepcopy(args)))
    except Exception as e:
        return ("exc", type(e).__name__)

def make_cases(task, W, n_cases=10, pool=400):
    """Deterministic hidden cases: expected from the reference; greedy set-cover so every mutant is killed; pad with random cases."""
    r = task_realization(task, W); rng = random.Random(int(sha256_obj([task["task_id"], W])[:12], 16))
    ref = solution_source(task["base"], task["fn"], r)
    cands, seen = [], set()
    for _ in range(pool):
        args = GEN[task["base"]](rng, r if r is not None else W["K1"])
        key = repr(args)
        if key in seen: continue
        seen.add(key); cands.append(args)
    exp = [_run(ref, task["fn"], a) for a in cands]
    assert all(e[0] == "ok" for e in exp), "reference raised"
    ms = mutants(task, W)
    kills = [{i for i, a in enumerate(cands) if _run(src, task["fn"], a) != exp[i]} for lab, src in ms]
    alive = set(range(len(ms))); chosen = []
    while alive:
        cnt = [(len({m for m in alive if i in kills[m]}), i) for i in range(len(cands)) if i not in chosen]
        g, best = max(cnt)
        if g == 0: break
        chosen.append(best); alive -= {m for m in alive if best in kills[m]}
    survivors = [ms[m][0] for m in sorted(alive)]
    for i in range(len(cands)):
        if len(chosen) >= n_cases: break
        if i not in chosen: chosen.append(i)
    chosen = sorted(chosen)
    return [{"args": cands[i], "expected": exp[i][1]} for i in chosen], survivors

def make_test_code(fn, cases):
    lit = "[\n" + "".join(f"    ({c['args']!r}, {c['expected']!r}),\n" for c in cases) + "]"
    return (f"\n_CASES = {lit}\n"
            f"def _ap0_run():\n    for a, e in _CASES:\n        try:\n            r = {fn}(*a)\n        except Exception as ex:\n            print('FAIL exception', repr(ex)[:200]); return False\n"
            f"        if r != e:\n            print('FAIL', repr(a)[:200], repr(r)[:200], repr(e)[:200]); return False\n    return True\n"
            f"if _ap0_run():\n    print('ALL_TESTS_PASSED_' + '@@NONCE@@')\n")
