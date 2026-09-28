"""Independent implementations for the v2-only bases (falls back to oracle_b for the v1 bases). Different idioms from tasks_v2's reference sources."""
import functools, itertools, re
from collections import Counter
from . import oracle_b
def impl(base, r):
    if base.startswith("k1"):
        cat = lambda c: r["map"][c]
        def tot(pairs):
            c = Counter()
            for s, a in pairs: c[cat(s)] += a
            return dict(c)
        if base == "k1_sumcat": return lambda records, category: sum(d["amount"] for d in records if cat(d["status"]) == category)
        if base == "k1_totlist": return lambda records: sorted(tot((d["status"], d["amount"]) for d in records).items())
        if base == "k1_pairs": return lambda pairs: tot(pairs)
        if base == "k1_merge": return lambda batches: tot((d["status"], d["amount"]) for b in batches for d in b)
        if base == "k1_catof": return lambda status: cat(status)
        if base == "k1_hascat": return lambda records, category: category in {cat(d["status"]) for d in records}
        if base == "k1_firstcat": return lambda records: cat(next(iter(records))["status"])
    if base.startswith("k2"):
        idx = lambda t: r["priority"].index(t) if t in r["priority"] else 99
        cmp = lambda a, b: (b[1] - a[1]) or (idx(a[2]) - idx(b[2])) or ((a[0] > b[0]) - (a[0] < b[0]))
        rank = lambda es: sorted(es, key=functools.cmp_to_key(cmp))
        if base == "k2_winscore": return lambda entries: tuple(rank(entries)[0][:2])
        if base == "k2_iswin": return lambda entries, name: rank(entries)[0][0] == name
        if base == "k2_csv": return lambda text: rank([(n, int(s), t) for n, s, t in (p.split(":") for p in text.split(";"))])[0][0]
        if base == "k2_rankrounds": return lambda rounds: [list(map(lambda e: e[0], rank(x))) for x in rounds]
    if base.startswith("k3"):
        tbl = {"add": lambda k: (lambda s: s + k), "sub": lambda k: (lambda s: s - k), "mul": lambda k: (lambda s: s * k), "set": lambda k: (lambda s: k)}
        f = {e: tbl[t](k) for e, (t, k) in r["ops"].items()}; st = lambda evs, s0: list(itertools.accumulate(evs, lambda s, e: f[e](s), initial=s0))
        if base == "k3_countover": return lambda events, start, limit: sum(1 for s in st(events, start)[1:] if s > limit)
        if base == "k3_min": return lambda events, start: min(st(events, start))
        if base == "k3_rle": return lambda pairs, start: st([e for e, k in pairs for _ in range(k)], start)[-1]
        if base == "k3_dictfinal": return lambda runs, start: {n: st(evs, start)[-1] for n, evs in runs.items()}
    if base == "u_maxlist": return lambda numbers: sorted(numbers)[-1]
    if base == "u_vowels": return lambda text: len(re.findall("[aeiouAEIOU]", text))
    if base == "u_uniq": return lambda items: sorted(dict.fromkeys(items))
    if base == "u_pal": return lambda text: all(text[i] == text[-1 - i] for i in range(len(text) // 2))
    if base == "u_second": return lambda numbers: sorted(set(numbers), reverse=True)[1]
    if base == "u_chunk": return lambda items, size: [items[i:i + size] for i in range(0, len(items), size)] if items else []
    if base == "u_invert": return lambda d: dict(zip(d.values(), d.keys()))
    if base == "u_fizz": return lambda n: [("Fizz" * (i % 3 == 0) + "Buzz" * (i % 5 == 0)) or str(i) for i in range(1, n + 1)]
    return oracle_b.impl(base, r)
