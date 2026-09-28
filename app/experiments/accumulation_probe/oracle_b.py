"""INDEPENDENT second implementation of every AP-0 task (different algorithms/idioms from tasks.py's reference sources).
Used only to cross-check the reference oracle (agreement on hidden cases + random inputs). BUILD-SIDE ONLY."""
import functools, itertools, re
from collections import Counter

def impl(base, r):
    if base.startswith("k1"):
        cat = lambda code: r["map"][code]
        def totals(records, key=lambda d: d["amount"], stat=lambda d: d["status"]):
            c = Counter()
            for d in records: c[cat(stat(d))] += key(d)
            return dict(c)
        if base == "k1_sum": return lambda records: totals(records)
        if base == "k1_count": return lambda records: totals(records, key=lambda d: 1)
        if base == "k1_ids": return lambda records, category: sorted([d["id"] for d in records if cat(d["status"]) == category])
        if base == "k1_top":
            def f(records):
                t = totals(records); best = max(t.values()); return min(k for k, v in t.items() if v == best)
            return f
        if base == "k1_tuples": return lambda records: totals(records, key=lambda t: t[2], stat=lambda t: t[1])
        if base == "k1_log":
            def f(text):
                rows = re.findall(r"(\d+):(\w+):(\d+)", text)
                c = Counter()
                for _, s, a in rows: c[cat(s)] += int(a)
                return dict(c)
            return f
    if base.startswith("k2"):
        idx = lambda tag: r["priority"].index(tag) if tag in r["priority"] else 99
        def cmp(a, b):
            if a[1] != b[1]: return b[1] - a[1]
            if idx(a[2]) != idx(b[2]): return idx(a[2]) - idx(b[2])
            return (a[0] > b[0]) - (a[0] < b[0])
        rank = lambda entries: sorted(entries, key=functools.cmp_to_key(cmp))
        if base == "k2_win": return lambda entries: rank(entries)[0][0]
        if base == "k2_rank": return lambda entries: [e[0] for e in rank(entries)]
        if base == "k2_lose": return lambda entries: rank(entries)[len(entries) - 1][0]
        if base == "k2_top2": return lambda entries: list(map(lambda e: e[0], rank(entries)))[:2]
        if base == "k2_dicts": return lambda entries: rank([(d["name"], d["score"], d["tag"]) for d in entries])[0][0]
        if base == "k2_rounds": return lambda rounds: [rank(rd)[0][0] for rd in rounds]
    if base.startswith("k3"):
        table = {"add": lambda k: (lambda s: s + k), "sub": lambda k: (lambda s: s - k), "mul": lambda k: (lambda s: s * k), "set": lambda k: (lambda s: k)}
        f = {e: table[t](k) for e, (t, k) in r["ops"].items()}
        states = lambda events, start: list(itertools.accumulate(events, lambda s, e: f[e](s), initial=start))
        if base == "k3_final": return lambda events, start: states(events, start)[-1]
        if base == "k3_trace": return lambda events, start: states(events, start)[1:]
        if base == "k3_max": return lambda events, start: max(states(events, start))
        if base == "k3_first":
            def g(events, start, limit):
                for i, s in enumerate(states(events, start)[1:]):
                    if s > limit: return i
                return -1
            return g
        if base == "k3_csv": return lambda text, start: states([e for e in text.split(",") if e], start)[-1]
        if base == "k3_batches": return lambda batches, start: [states(b, start)[-1] for b in batches]
    if base == "u_evens": return lambda numbers: sum(filter(lambda n: not n % 2, numbers))
    if base == "u_revwords": return lambda text: " ".join(text.split()[::-1])
    if base == "u_flat": return lambda lists: list(itertools.chain.from_iterable(lists))
    if base == "u_rle":
        def g(text):
            out = []
            for ch in text:
                if out and out[-1][0] == ch: out[-1] = (ch, out[-1][1] + 1)
                else: out.append((ch, 1))
            return out
        return g
    raise KeyError(base)
