"""Convention realizations for AP-0 (stdlib only). A 'world' = one random realization of a local convention that the
public task text does NOT reveal. Three conventions: K1 status-code table, K2 tag priority for ties, K3 event-update table."""
import random
from functools import lru_cache

CATS = ["open", "closed", "hold"]
OPS = ["add", "sub", "mul", "set"]
_C = "bdfgjklmnprstvwz"; _V = "aeiou"

@lru_cache(None)
def _dict_words():
    try: return frozenset(w.strip().lower() for w in open("/usr/share/dict/words", errors="ignore"))
    except OSError: return frozenset()

def pseudo_word(rng, taken):
    while True:
        w = "".join(rng.choice(_C) + rng.choice(_V) for _ in range(2)) + rng.choice(_C)
        if w not in taken and w not in _dict_words():
            taken.add(w); return w

def make_realization(kind, seed, taken):
    rng = random.Random(seed)
    if kind == "K1":
        codes = [pseudo_word(rng, taken) for _ in range(6)]
        cats = CATS * 2; rng.shuffle(cats)
        return {"kind": "K1", "codes": codes, "categories": list(CATS), "map": dict(zip(codes, cats))}
    if kind == "K2":
        tags = sorted(pseudo_word(rng, taken) for _ in range(4))
        while True:
            pri = tags[:]; rng.shuffle(pri)
            disagree = sum(1 for a, b in zip(pri, pri[1:]) if a > b)      # adjacent pairs where alphabetical order would be wrong
            if disagree == 2: break
        return {"kind": "K2", "tags": tags, "priority": pri}
    if kind == "K3":
        evs = [pseudo_word(rng, taken) for _ in range(4)]
        types = OPS[:]; rng.shuffle(types)
        ks = {"add": rng.randint(2, 9), "sub": rng.randint(1, 5), "mul": rng.randint(2, 4), "set": rng.randint(3, 9)}
        return {"kind": "K3", "events": evs, "ops": {e: [t, ks[t]] for e, t in zip(evs, types)}}
    raise ValueError(kind)

def mismatch(r):
    """Same tokens, systematically different content (every parameter differs) -> a wrong-but-well-formed carrier."""
    if r["kind"] == "K1":
        return {**r, "map": {c: CATS[(CATS.index(v) + 1) % 3] for c, v in r["map"].items()}}
    if r["kind"] == "K2":
        return {**r, "priority": list(reversed(r["priority"]))}
    evs = r["events"]; ops = r["ops"]
    return {**r, "ops": {evs[i]: list(ops[evs[(i + 1) % 4]]) for i in range(4)}}

def naive(r):
    """Generic 'ignores the convention' realization (used as a mutant, never as a carrier)."""
    if r["kind"] == "K1": return {**r, "map": {c: c for c in r["codes"]}}
    if r["kind"] == "K2": return {**r, "priority": []}
    return {**r, "ops": {e: ["add", 1] for e in r["events"]}}

def perturbations(r):
    """All single-step changes to the convention. Every hidden test set must kill every one of these."""
    out = []
    if r["kind"] == "K1":
        for c in r["codes"]:
            for cat in CATS:
                if cat != r["map"][c]: out.append((f"map[{c}]->{cat}", {**r, "map": {**r["map"], c: cat}}))
    elif r["kind"] == "K2":
        for i in range(3):
            p = r["priority"][:]; p[i], p[i + 1] = p[i + 1], p[i]
            out.append((f"swap_pri[{i}]", {**r, "priority": p}))
    else:
        for e in r["events"]:
            t, k = r["ops"][e]
            for dk in (1, -1):
                if k + dk >= 1: out.append((f"k[{e}]{dk:+d}", {**r, "ops": {**r["ops"], e: [t, k + dk]}}))
        for i in range(4):
            for j in range(i + 1, 4):
                o = dict(r["ops"]); a, b = r["events"][i], r["events"][j]; o[a], o[b] = o[b], o[a]
                out.append((f"swap_ops[{a},{b}]", {**r, "ops": o}))
    return out

def tokens(r):
    """Convention-specific tokens (the words a leak check should look for)."""
    return list(r.get("codes") or r.get("tags") or r.get("events"))
