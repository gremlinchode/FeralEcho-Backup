"""AP-0 v2 task set (additive; imports the frozen v1 modules read-only and NEVER edits them). Build-side only (holds reference solutions).
Changes vs v1 (each justified by Stage 0 evidence): 6 T + 4 S templates per convention (per-convention power); NEAR repaired and grown to 6 per
convention with neutral function names and no zero-key output traps; UNREL grown to 12; stronger generators (unsorted ids, non-positive starts,
name-only ties) and a larger, independently-derived mutant set; separate VAL / TEST case partitions so a retention gate never sees test cases."""
import copy, random
from . import tasks as T1, worlds
from .common import sha256_obj

_MAPH = T1._HEADER
T1._ALL.update({  # additive keys only
 "k1_sumcat": "def {FN}(records, category):\n    return sum(rec['amount'] for rec in records if _MAP[rec['status']] == category)\n",
 "k1_totlist": "def {FN}(records):\n    tot = {{}}\n    for rec in records:\n        c = _MAP[rec['status']]\n        tot[c] = tot.get(c, 0) + rec['amount']\n    return sorted(tot.items())\n",
 "k1_pairs": "def {FN}(pairs):\n    out = {{}}\n    for s, a in pairs:\n        c = _MAP[s]\n        out[c] = out.get(c, 0) + a\n    return out\n",
 "k1_merge": "def {FN}(batches):\n    out = {{}}\n    for b in batches:\n        for rec in b:\n            c = _MAP[rec['status']]\n            out[c] = out.get(c, 0) + rec['amount']\n    return out\n",
 "k1_catof": "def {FN}(status):\n    return _MAP[status]\n",
 "k1_hascat": "def {FN}(records, category):\n    return any(_MAP[rec['status']] == category for rec in records)\n",
 "k1_firstcat": "def {FN}(records):\n    return _MAP[records[0]['status']]\n",
 "k2_winscore": T1._RANK + "def {FN}(entries):\n    b = _rank(entries)[0]\n    return (b[0], b[1])\n",
 "k2_iswin": T1._RANK + "def {FN}(entries, name):\n    return _rank(entries)[0][0] == name\n",
 "k2_csv": "def {FN}(text):\n    es = []\n    for part in text.split(';'):\n        n, s, t = part.split(':')\n        es.append((n, int(s), t))\n    es.sort(key=lambda e: (-e[1], _PRI.get(e[2], 99), e[0]))\n    return es[0][0]\n",
 "k2_rankrounds": T1._RANK + "def {FN}(rounds):\n    return [[e[0] for e in _rank(r)] for r in rounds]\n",
 "k3_countover": T1._STEP + "def {FN}(events, start, limit):\n    s = start\n    n = 0\n    for ev in events:\n        s = _step(s, ev)\n        if s > limit: n += 1\n    return n\n",
 "k3_min": T1._STEP + "def {FN}(events, start):\n    s = start\n    m = start\n    for ev in events:\n        s = _step(s, ev)\n        m = min(m, s)\n    return m\n",
 "k3_rle": T1._STEP + "def {FN}(pairs, start):\n    s = start\n    for ev, k in pairs:\n        for _ in range(k):\n            s = _step(s, ev)\n    return s\n",
 "k3_dictfinal": T1._STEP + "def {FN}(runs, start):\n    out = {{}}\n    for name, evs in runs.items():\n        s = start\n        for ev in evs:\n            s = _step(s, ev)\n        out[name] = s\n    return out\n",
 "u_maxlist": "def {FN}(numbers):\n    return max(numbers)\n",
 "u_vowels": "def {FN}(text):\n    return sum(1 for ch in text.lower() if ch in 'aeiou')\n",
 "u_uniq": "def {FN}(items):\n    return sorted(set(items))\n",
 "u_pal": "def {FN}(text):\n    return text == text[::-1]\n",
 "u_second": "def {FN}(numbers):\n    return sorted(set(numbers))[-2]\n",
 "u_chunk": "def {FN}(items, size):\n    return [items[i:i + size] for i in range(0, len(items), size)]\n",
 "u_invert": "def {FN}(d):\n    return {{v: k for k, v in d.items()}}\n",
 "u_fizz": "def {FN}(n):\n    out = []\n    for i in range(1, n + 1):\n        if i % 15 == 0: out.append('FizzBuzz')\n        elif i % 3 == 0: out.append('Fizz')\n        elif i % 5 == 0: out.append('Buzz')\n        else: out.append(str(i))\n    return out\n",
})
def solution_source(base, fn, r): return T1.solution_source(base, fn, r)

# ---- generators (v2: stronger edge coverage)
_NAMES = ["amy", "bo", "cid", "dot", "eve", "fay", "gus", "hal", "ivy", "jo"]
def _rec(g, r, n=None):
    n = n or g.randint(4, 8); ids = g.sample(range(1, 40), n)
    return [{"id": ids[i], "status": g.choice(r["codes"]), "amount": g.randint(0, 20)} for i in range(n)]
def _ent(g, r, n=None):
    n = n or g.randint(3, 6); names = g.sample(_NAMES, n); tags = r["tags"]
    es = [(nm, g.randint(1, 3), g.choice(tags)) for nm in names]
    if g.random() < 0.35 and n >= 3: es[1] = (es[1][0], es[0][1], es[0][2])            # force score AND tag ties so the name tie-break is exercised
    return es
def _evs(g, r, lo=2, hi=6): return [g.choice(r["events"]) for _ in range(g.randint(lo, hi))]
def _st(g): return g.randint(-3, 6)
G2 = {
 "k1_sum": lambda g, r: (_rec(g, r),), "k1_count": lambda g, r: (_rec(g, r),), "k1_top": lambda g, r: (_rec(g, r),),
 "k1_ids": lambda g, r: (_rec(g, r), g.choice(worlds.CATS)), "k1_sumcat": lambda g, r: (_rec(g, r), g.choice(worlds.CATS)), "k1_hascat": lambda g, r: (_rec(g, r, g.randint(1, 4)), g.choice(worlds.CATS)),
 "k1_tuples": lambda g, r: ([(d["id"], d["status"], d["amount"]) for d in _rec(g, r)],),
 "k1_log": lambda g, r: (";".join(f'{d["id"]}:{d["status"]}:{d["amount"]}' for d in _rec(g, r)),),
 "k1_totlist": lambda g, r: (_rec(g, r),), "k1_pairs": lambda g, r: ([(d["status"], d["amount"]) for d in _rec(g, r)],),
 "k1_merge": lambda g, r: ([_rec(g, r, g.randint(1, 4)) for _ in range(g.randint(2, 3))],),
 "k1_catof": lambda g, r: (g.choice(r["codes"]),), "k1_firstcat": lambda g, r: (_rec(g, r),),
 "k2_win": lambda g, r: (_ent(g, r),), "k2_rank": lambda g, r: (_ent(g, r),), "k2_lose": lambda g, r: (_ent(g, r),), "k2_top2": lambda g, r: (_ent(g, r),),
 "k2_dicts": lambda g, r: ([{"name": n, "score": s, "tag": t} for n, s, t in _ent(g, r)],), "k2_rounds": lambda g, r: ([_ent(g, r, g.randint(3, 4)) for _ in range(g.randint(2, 3))],),
 "k2_winscore": lambda g, r: (_ent(g, r),), "k2_iswin": lambda g, r: (_ent(g, r), g.choice(_NAMES)),
 "k2_csv": lambda g, r: (";".join(f"{n}:{s}:{t}" for n, s, t in _ent(g, r)),), "k2_rankrounds": lambda g, r: ([_ent(g, r, g.randint(3, 4)) for _ in range(g.randint(2, 3))],),
 "k3_final": lambda g, r: (_evs(g, r), _st(g)), "k3_trace": lambda g, r: (_evs(g, r), _st(g)), "k3_max": lambda g, r: (_evs(g, r), _st(g)), "k3_min": lambda g, r: (_evs(g, r), _st(g)),
 "k3_first": lambda g, r: (_evs(g, r), _st(g), g.randint(0, 30)), "k3_countover": lambda g, r: (_evs(g, r), _st(g), g.randint(0, 30)),
 "k3_csv": lambda g, r: (",".join(_evs(g, r, 0, 6)), _st(g)), "k3_batches": lambda g, r: ([_evs(g, r) for _ in range(g.randint(2, 3))], _st(g)),
 "k3_rle": lambda g, r: ([(g.choice(r["events"]), g.randint(1, 3)) for _ in range(g.randint(1, 3))], _st(g)),
 "k3_dictfinal": lambda g, r: ({g.choice(["a", "b", "c", "d"]) + str(i): _evs(g, r, 0, 4) for i in range(g.randint(2, 3))}, _st(g)),
 "u_evens": lambda g, r: ([g.randint(-9, 30) for _ in range(g.randint(4, 9))],), "u_revwords": lambda g, r: (" ".join(g.choice(["red", "blue", "sun", "moon", "tree", "rain", "ice"]) for _ in range(g.randint(2, 5))),),
 "u_flat": lambda g, r: ([[g.randint(0, 9) for _ in range(g.randint(0, 3))] for _ in range(g.randint(2, 4))],), "u_rle": lambda g, r: ("".join(g.choice("aabbc") for _ in range(g.randint(4, 10))),),
 "u_maxlist": lambda g, r: ([g.randint(-20, 40) for _ in range(g.randint(2, 8))],), "u_vowels": lambda g, r: ("".join(g.choice("abcdeEIou xyz") for _ in range(g.randint(3, 14))),),
 "u_uniq": lambda g, r: ([g.randint(0, 6) for _ in range(g.randint(3, 10))],), "u_pal": lambda g, r: (g.choice(["level", "abcba", "abca", "noon", "xyzx", "a", "ab"]),),
 "u_second": lambda g, r: (g.sample(range(-5, 30), g.randint(2, 7)) + [g.randint(0, 3)],),
 "u_chunk": lambda g, r: (list(range(g.randint(0, 9))), g.randint(1, 4)), "u_invert": lambda g, r: (dict(zip(g.sample(list("abcdef"), 4), g.sample(range(10), 4))),), "u_fizz": lambda g, r: (g.randint(1, 20),),
}
# ---- registries
KT = {"K1": [("T1", "k1_sum", "categorize", "records", "Return a dict mapping each category name to the total `amount` of the records whose status code belongs to that category (only categories that occur appear as keys)."),
             ("T2", "k1_count", "count_by_category", "records", "Return a dict mapping each category name to the number of records whose status code belongs to it (only categories that occur appear as keys)."),
             ("T3", "k1_ids", "ids_in_category", "records, category", "Return the sorted list of `id` values of the records whose status code belongs to `category`."),
             ("T4", "k1_top", "top_category", "records", "Return the category name with the largest total `amount`; if two categories tie, return the alphabetically smaller name. `records` is non-empty."),
             ("T5", "k1_sumcat", "sum_in_category", "records, category", "Return the total `amount` of the records whose status code belongs to `category` (0 if there are none)."),
             ("T6", "k1_totlist", "category_totals", "records", "Return a list of `(category, total_amount)` tuples, one per category that occurs, sorted by category name.")],
      "K2": [("T1", "k2_win", "pick_winner", "entries", "Return the `name` of the best-ranked entry."),
             ("T2", "k2_rank", "rank_all", "entries", "Return the list of names ordered from best-ranked to worst-ranked."),
             ("T3", "k2_lose", "pick_loser", "entries", "Return the `name` of the worst-ranked entry."),
             ("T4", "k2_top2", "top_two", "entries", "Return the list with the names of the two best-ranked entries, in rank order (fewer if there are fewer entries)."),
             ("T5", "k2_winscore", "winner_with_score", "entries", "Return a tuple `(name, score)` of the best-ranked entry."),
             ("T6", "k2_iswin", "is_winner", "entries, name", "Return True if `name` is the name of the best-ranked entry, else False.")],
      "K3": [("T1", "k3_final", "final_state", "events, start", "Apply the events in order to `start` and return the final state."),
             ("T2", "k3_trace", "state_trace", "events, start", "Return the list of states after each event, in order (same length as `events`; `start` itself is not included)."),
             ("T3", "k3_max", "max_state", "events, start", "Return the largest state seen, including `start` and the state after every event."),
             ("T4", "k3_first", "first_over", "events, start, limit", "Return the 0-based index of the first event after which the state is strictly greater than `limit`; return -1 if that never happens."),
             ("T5", "k3_min", "min_state", "events, start", "Return the smallest state seen, including `start` and the state after every event."),
             ("T6", "k3_countover", "count_over", "events, start, limit", "Return how many events leave the state strictly greater than `limit` (count the state after each event).")]}
KS = {"K1": [("S1", "k1_tuples", "categorize_tuples", "records", "Here `records` is a list of tuples `(id, status, amount)` instead of dicts. Return a dict mapping each category name to the total amount of the records whose status code belongs to that category (only categories that occur appear as keys)."),
             ("S2", "k1_log", "parse_log", "text", "Here `text` is a string of records joined by `;`, each written `id:status:amount` (for example `3:abcde:7;4:fghij:2`; the empty string means no records). Return a dict mapping each category name to the total amount of the records whose status code belongs to that category (only categories that occur appear as keys)."),
             ("S3", "k1_pairs", "categorize_pairs", "pairs", "Here `pairs` is a list of `(status, amount)` tuples. Return a dict mapping each category name to the total amount of the pairs whose status code belongs to that category (only categories that occur appear as keys)."),
             ("S4", "k1_merge", "merge_batches", "batches", "`batches` is a list of record lists (dict records as above). Return one dict mapping each category name to the total `amount` over all records in all batches (only categories that occur appear as keys).")],
      "K2": [("S1", "k2_dicts", "pick_winner_dicts", "entries", "Here each entry is a dict with keys `name`, `score` and `tag` instead of a tuple. Return the `name` of the best-ranked entry."),
             ("S2", "k2_rounds", "winners_by_round", "rounds", "`rounds` is a list of entry lists (tuples as above). Return the list containing, for each round in order, the name of that round's best-ranked entry."),
             ("S3", "k2_csv", "winner_from_text", "text", "Here the entries are given as one string `text`: entries joined by `;`, each written `name:score:tag` (score is an integer). Return the `name` of the best-ranked entry."),
             ("S4", "k2_rankrounds", "rankings_by_round", "rounds", "`rounds` is a list of entry lists (tuples as above). Return the list containing, for each round in order, the list of names ordered from best-ranked to worst-ranked.")],
      "K3": [("S1", "k3_csv", "final_state_csv", "text, start", "Here the events are given as one string `text`, joined by commas (the empty string means no events). Apply them in order to `start` and return the final state."),
             ("S2", "k3_batches", "finals_for_batches", "batches, start", "`batches` is a list of event lists. Each batch starts again from `start`. Return the list of the final state of each batch, in order."),
             ("S3", "k3_rle", "final_state_runs", "pairs, start", "`pairs` is a list of `(event, count)` tuples meaning that `event` is applied `count` times in a row, in order. Apply them to `start` and return the final state."),
             ("S4", "k3_dictfinal", "finals_by_name", "runs, start", "`runs` is a dict mapping a run name to a list of events. Each run starts again from `start`. Return a dict mapping each run name to its final state.")]}
NEARS = {"K1": [("N1", "k1_catof", "category_of", "status", "Return the category name of the status code `status`."),
                ("N2", "k1_ids", "ids_for_category", "records, category", "Return the sorted list of `id` values of the records whose status code belongs to `category`."),
                ("N3", "k1_top", "dominant_category", "records", "Return the category name with the largest total `amount`; if two categories tie, return the alphabetically smaller name. `records` is non-empty."),
                ("N4", "k1_sumcat", "total_for_category", "records, category", "Return the total `amount` of the records whose status code belongs to `category` (0 if there are none)."),
                ("N5", "k1_hascat", "contains_category", "records, category", "Return True if any record's status code belongs to `category`, else False."),
                ("N6", "k1_firstcat", "first_record_category", "records", "Return the category name of the first record. `records` is non-empty.")],
         "K2": [("N1", "k2_win", "select_champion", "entries", "Return the `name` of the best-ranked entry."),
                ("N2", "k2_lose", "select_last_place", "entries", "Return the `name` of the worst-ranked entry."),
                ("N3", "k2_rank", "order_entries", "entries", "Return the list of names ordered from best-ranked to worst-ranked."),
                ("N4", "k2_top2", "leading_pair", "entries", "Return the list with the names of the two best-ranked entries, in rank order (fewer if there are fewer entries)."),
                ("N5", "k2_iswin", "is_champion", "entries, name", "Return True if `name` is the name of the best-ranked entry, else False."),
                ("N6", "k2_winscore", "champion_with_score", "entries", "Return a tuple `(name, score)` of the best-ranked entry.")],
         "K3": [("N1", "k3_final", "run_events", "events, start", "Apply the events in order to `start` and return the final state."),
                ("N2", "k3_trace", "run_events_trace", "events, start", "Return the list of states after each event, in order (same length as `events`)."),
                ("N3", "k3_max", "peak_value", "events, start", "Return the largest state seen, including `start` and the state after every event."),
                ("N4", "k3_first", "first_exceeding", "events, start, limit", "Return the 0-based index of the first event after which the state is strictly greater than `limit`; return -1 if that never happens."),
                ("N5", "k3_min", "lowest_value", "events, start", "Return the smallest state seen, including `start` and the state after every event."),
                ("N6", "k3_countover", "count_exceeding", "events, start, limit", "Return how many events leave the state strictly greater than `limit`.")]}
UNRELS = [("U1", "u_evens", "sum_evens", "numbers", "`numbers` is a list of ints. Return the sum of the even numbers."), ("U2", "u_revwords", "reverse_words", "text", "Return the words of `text` in reverse order, joined by single spaces."),
          ("U3", "u_flat", "flatten_once", "lists", "`lists` is a list of lists. Return one list with the elements of all inner lists, in order."), ("U4", "u_rle", "run_length_encode", "text", "Return the run-length encoding of `text` as a list of `(character, count)` tuples, in order."),
          ("U5", "u_maxlist", "max_in_list", "numbers", "`numbers` is a non-empty list of ints. Return the largest one."), ("U6", "u_vowels", "count_vowels", "text", "Return the number of vowels (a, e, i, o, u, in either case) in `text`."),
          ("U7", "u_uniq", "unique_sorted", "items", "Return the sorted list of the distinct values in `items`."), ("U8", "u_pal", "is_palindrome", "text", "Return True if `text` reads the same forwards and backwards (case-sensitive), else False."),
          ("U9", "u_second", "second_largest", "numbers", "`numbers` has at least two distinct values. Return the second largest distinct value."), ("U10", "u_chunk", "chunk_list", "items, size", "Return `items` split into consecutive lists of at most `size` elements, in order."),
          ("U11", "u_invert", "invert_dict", "d", "`d` maps keys to unique values. Return the dict mapping each value back to its key."), ("U12", "u_fizz", "fizz_list", "n", "Return the list of strings for 1..n: 'FizzBuzz' if divisible by 15, 'Fizz' if by 3, 'Buzz' if by 5, otherwise the number as a string.")]

def build_tasks_v2(W):
    out = []
    for kind in ("K1", "K2", "K3"):
        r = W[kind]
        for split, table in (("T", KT[kind]), ("S", KS[kind])):
            for tid, base, fn, args, spec in table:
                out.append({"task_id": f"{kind}.{tid}", "kind": kind, "split": split, "base": base, "fn": fn, "sig": f"def {fn}({args}):", "spec": f"{T1.BASE_SPEC[kind]} Write `{fn}({args})`. {spec}", "solution_realization": "true"})
        for tid, base, fn, args, spec in NEARS[kind]:
            out.append({"task_id": f"{kind}.{tid}", "kind": kind, "split": "NEAR", "base": base, "fn": fn, "sig": f"def {fn}({args}):", "spec": f"{_near_base(kind)} Write `{fn}({args})`. {spec}{T1.EXPLICIT[kind](r)}", "solution_realization": "mismatch"})
    for tid, base, fn, args, spec in UNRELS:
        out.append({"task_id": tid, "kind": None, "split": "UNREL", "base": base, "fn": fn, "sig": f"def {fn}({args}):", "spec": f"Write `{fn}({args})`. {spec}", "solution_realization": "none"})
    return out
def _near_base(kind):
    return {"K1": "`records` are dicts with keys `id` (int), `status` (str) and `amount` (int). Categories are open, closed, hold.",
            "K2": "Entries are tuples `(name, score, tag)`. Entries are ranked from best to worst: a higher `score` ranks better; ties on score are resolved by tag priority (a higher-priority tag ranks better); if the tag priority is also equal, the alphabetically smaller `name` ranks better.",
            "K3": "Each event is a string naming an update to an integer state."}[kind]

# ---- mutants (v2): perturbations + generic + INDEPENDENT text-level operators (the ones Stage 0's re-audit used, extended)
SWAPS = [("<", "<="), (">", ">="), ("-e[1]", "e[1]"), ("-e['score']", "e['score']"), ("+ 1", "+ 2"), ("[0][0]", "[1][0]"), ("[-1][0]", "[0][0]"), ("min(", "max("), ("max(", "min("), ("s + k", "s - k"), ("s - k", "s + k"),
         ("s * k", "s + k"), ("return k", "return s"), ("[:2]", "[:1]"), ("== category", "!= category"), ("sorted(", "list("), ("if s > limit", "if s >= limit"), ("m = start", "m = 0"), ("_PRI.get(e[2], 99), e[0])", "_PRI.get(e[2], 99), -len(e[0]))"),
         ("_PRI.get(e['tag'], 99), e['name'])", "_PRI.get(e['tag'], 99), -len(e['name']))"), ("e[0])", "-len(e[0]))"), ("range(k)", "range(k - 1)"), ("return -1", "return 0"), ("n += 1", "n += 2"), ("sum(", "max("), ("- e[1]", "e[1]")]
def mutants(task, W):
    r = T1.task_realization(task, W); base, fn = task["base"], task["fn"]; out = []
    if r is not None:
        for lab, m in worlds.perturbations(r): out.append((lab, solution_source(base, fn, m)))
        out.append(("naive", solution_source(base, fn, worlds.naive(r))))
        if task["solution_realization"] == "mismatch": out.append(("applies_carrier_convention", solution_source(base, fn, W[task["kind"]])))
    src = solution_source(base, fn, r)
    for a, b in SWAPS:
        if a in src: out.append((f"text[{a}->{b}]", src.replace(a, b, 1)))
    out += [("returns_none", f"def {fn}(*a, **k):\n    return None\n"), ("returns_empty_list", f"def {fn}(*a, **k):\n    return []\n")]
    return out
def _run(src, fn, args):
    try: ns = {}; exec(src, ns); return ("ok", ns[fn](*copy.deepcopy(args)))
    except Exception as e: return ("exc", type(e).__name__)
def make_cases2(task, W, partition, n_cases=10, pool=500):
    """Case sets for partition in {'VAL','TEST'}: disjoint RNG streams; greedy cover kills every non-equivalent mutant; equivalence is CHECKED on 4000 extra inputs."""
    r = T1.task_realization(task, W); g = random.Random(int(sha256_obj([task["task_id"], W, partition])[:12], 16)); ref = solution_source(task["base"], task["fn"], r); rr = r if r is not None else W["K1"]
    cands, seen = [], set()
    for _ in range(pool):
        a = G2[task["base"]](g, rr)
        if repr(a) not in seen: seen.add(repr(a)); cands.append(a)
    exp = [_run(ref, task["fn"], a) for a in cands]
    assert all(e[0] == "ok" for e in exp), (task["task_id"], "reference raised", [e for e in exp if e[0] != "ok"][:1])
    ms = mutants(task, W); kills = [{i for i, a in enumerate(cands) if _run(s, task["fn"], a) != exp[i]} for _, s in ms]
    alive = set(range(len(ms))); chosen = []
    while alive:
        g_, best = max((len({m for m in alive if i in kills[m]}), i) for i in range(len(cands)) if i not in chosen)
        if g_ == 0: break
        chosen.append(best); alive -= {m for m in alive if best in kills[m]}
    equiv = []
    for m in sorted(alive):
        found = False
        for _ in range(4000):
            a = G2[task["base"]](g, rr)
            if _run(ms[m][1], task["fn"], a) != _run(ref, task["fn"], a):
                cands.append(a); exp.append(_run(ref, task["fn"], a)); chosen.append(len(cands) - 1); found = True; break
        if not found: equiv.append(ms[m][0])
    for i in range(len(cands)):
        if len(chosen) >= n_cases: break
        if i not in chosen: chosen.append(i)
    chosen = sorted(set(chosen))
    return [{"args": cands[i], "expected": exp[i][1]} for i in chosen], equiv
def make_test_code(fn, cases): return T1.make_test_code(fn, cases)
