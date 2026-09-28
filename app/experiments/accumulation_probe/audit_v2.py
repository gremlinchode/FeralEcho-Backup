"""AP-0 v2 auditor v2 (POST-HOC CORRECTION, disclosed). The frozen auditor's K1 parser (constructor.audit) only recognised 'CODE -> CATEGORY' pairs; on the first
9 hand-read drafts it reported every code 'missing' for drafts like "'kobat' and 'kiwan' are categorized as 'hold'" (grouped codes). This module re-parses K1 with a
clause-sequence rule and otherwise delegates to the frozen auditor. It was written after the constructor drafts existed (but before any gate result was analysed)
and is therefore validated by full hand adjudication of all 72 drafts (results reported alongside; hand adjudication, not this parser, is the arbiter)."""
import re
from .constructor import audit as audit_v1, _norm, _strip_hedged, _CATS, _HEDGE

def _presplit(t):
    """Insert sentence/bullet boundaries the drafts omit (e.g. "... 'closed' Any other statuses are not established"), so a hedge clause cannot swallow a preceding assertion."""
    t = re.sub(r"(?<=['\")]) (?=[A-Z])", ". ", t); return re.sub(r"\s-\s", ". ", t)
def _k1(r, text):
    full = _norm(text or ""); t = _strip_hedged(_presplit(full))
    out = {"kind": "K1", "exact": False, "correct_items": 0, "wrong_items": 0, "missing_items": 0, "items": {}, "auditor": "v2",
           "copies_episode_syntax": bool(re.search(r"(categorize|pick_winner|final_state)\s*\(", full)), "hedges": bool(_HEDGE.search(full))}
    got = {}
    codes = r["codes"]; alt = "|".join(map(re.escape, codes))
    for clause in re.split(r"[.;\n]|\s-\s|\s\d\)\s", t):
        toks = [(m.start(), "C" if m.group(0).lower() not in _CATS.split("|") else "K", m.group(0).lower()) for m in re.finditer(rf"\b({alt})\b|\b({_CATS})\b", clause, re.I)]
        toks = [(p, ("K" if v in _CATS.split("|") else "C"), v) for p, _, v in toks]
        if not toks: continue
        cat_first = toks[0][1] == "K"
        for i, (p, k, v) in enumerate(toks):
            if k != "C": continue
            if cat_first:  # "hold: a, b; open: c" -> nearest preceding category
                prev = [x for x in toks[:i] if x[1] == "K"]; c = prev[-1][2] if prev else None
            else:          # "a and b are hold" -> nearest following category
                nxt = [x for x in toks[i + 1:] if x[1] == "K"]; c = nxt[0][2] if nxt else None
            if c: got.setdefault(v, set()).add(c)
    for c in codes:
        g = got.get(c)
        if not g: out["missing_items"] += 1; out["items"][c] = "missing"
        elif g == {r["map"][c]}: out["correct_items"] += 1; out["items"][c] = "ok"
        else: out["wrong_items"] += 1; out["items"][c] = "wrong:" + "/".join(sorted(g))
    out["exact"] = out["correct_items"] == len(codes) and out["wrong_items"] == 0
    return out

def audit(kind, r, text):
    return _k1(r, text) if kind == "K1" else audit_v1(kind, r, text)
