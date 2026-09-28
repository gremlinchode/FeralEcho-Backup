"""AP-0 v2 constructor: turns observed episodes into a retained procedure note (the acquisition step), plus the GROUND-TRUTH content auditor used
ONLY for constructor qualification (in Stage 1 the truth is unknown; the retention gate there is behavioural). Build-side (uses worlds/tasks)."""
import random, re
from . import tasks as T1, worlds

CONSTRUCTOR_SYSTEM = "You are a careful analyst. You turn observed episodes into a short reusable procedure note for programmers."
def constructor_user(kind, episode_lines):
    ctx = T1.BASE_SPEC[kind]
    return (f"Context: {ctx}\n\nObserved episodes from this site (call -> result):\n" + "\n".join(episode_lines) +
            "\n\nWrite ONE reusable procedure note that states the site's convention completely and precisely, so that a programmer who has NOT seen these episodes can apply it correctly to any related task.\n"
            "- State the convention as explicit facts (for example a full table, or a full ordered list); do not merely repeat the examples.\n"
            "- State only what the episodes establish. If something is not established by the episodes, write 'not established' for it instead of guessing.\n"
            "- Reply with the note text only: one short paragraph, no code.")

# ---------- episode representations ----------
def episodes(kind, r, rep, rng=None, missing_token=None, distractor_from=None):
    """rep: R0 raw canonical (= Stage 0 E arm) | R1 grouped + augmented | A1 missing evidence | A2 shuffled R0 | A3 distractors"""
    if rep in ("R0", "A2"):
        lines = T1.episode_lines(T1.teaching_episodes(r))
        if rep == "A2": lines = lines[:]; rng.shuffle(lines)
        return lines
    ep = _r1(kind, r)
    if rep == "A1":
        tok = missing_token or _last_token(kind, r); ep = [(fn, a, out) for fn, a, out in ep if tok not in repr(a)]
    lines = T1.episode_lines(ep)
    if rep == "A3":
        lines = lines + T1.episode_lines(_r1(distractor_from[0], distractor_from[1]))[:4]; rng.shuffle(lines)
    return lines
def _last_token(kind, r): return (r.get("codes") or r.get("tags") or r.get("events"))[-1]
def _r1(kind, r):
    eps = []
    if kind == "K1":
        for c in sorted(r["codes"]):
            for amt in (5, 12): a = ([{"id": 1, "status": c, "amount": amt}],); eps.append(("categorize", a, T1._call("k1_sum", "categorize", r, a)))
    elif kind == "K2":
        tags = r["tags"]; pri = r["priority"]; nm = [("zed", "amy"), ("amy", "zed")]; k = 0
        for i in range(4):
            for j in range(i + 1, 4):
                a1, a2 = nm[k % 2]; k += 1; a = ([(a1, 4, tags[i]), (a2, 4, tags[j])],); eps.append(("pick_winner", a, T1._call("k2_win", "pick_winner", r, a)))
                a = ([(a2, 4, tags[i]), (a1, 4, tags[j])],); eps.append(("pick_winner", a, T1._call("k2_win", "pick_winner", r, a)))
    else:
        for e in sorted(r["events"]):
            for st in (2, 5, -1): a = ([e], st); eps.append(("final_state", a, T1._call("k3_final", "final_state", r, a)))
    return eps

# ---------- ground-truth content auditor (qualification only) ----------
_CATS = "open|closed|hold"
_HEDGE = re.compile(r"not established|unknown|unclear|cannot be determined|not enough|unspecified|undetermined", re.I)
def _norm(t): return re.sub(r"[`*]", "", t)
def _strip_hedged(t):
    """Drop clauses that explicitly say a fact is not established, so a hedge about token X is never parsed as an assertion about X."""
    parts = re.split(r"([.;\n,])", t); keep = []
    for i in range(0, len(parts), 2):
        seg = parts[i]; sep = parts[i + 1] if i + 1 < len(parts) else ""
        if not _HEDGE.search(seg): keep.append(seg + sep)
    return "".join(keep)
def audit(kind, r, text):
    full = _norm(text or ""); t = _strip_hedged(full); out = {"kind": kind, "exact": False, "correct_items": 0, "wrong_items": 0, "missing_items": 0, "copies_episode_syntax": bool(re.search(r"(categorize|pick_winner|final_state)\s*\(", full)), "hedges": bool(_HEDGE.search(full)), "items": {}}
    if kind == "K1":
        got = {}
        for c in r["codes"]:
            m = re.findall(rf"\b{re.escape(c)}\b\s*(?:->|=>|=|:|→|-|is|maps? to|belongs? to|are|as)?\s*(?:the\s+|a\s+)?(?:category\s+)?['\"]?({_CATS})\b", t, re.I)
            if m: got.setdefault(c, set()).update(x.lower() for x in m)
        for cat in re.finditer(rf"\b({_CATS})\b\s*(?:codes?|statuses|status codes?)?\s*(?:->|=>|=|:|→|include|includes|are|for)\s*([^.;\n]*)", t, re.I):   # category-first lists
            for c in r["codes"]:
                if re.search(rf"\b{re.escape(c)}\b", cat.group(2)): got.setdefault(c, set()).add(cat.group(1).lower())
        for c in r["codes"]:
            g = got.get(c)
            if not g: out["missing_items"] += 1; out["items"][c] = "missing"
            elif g == {r["map"][c]}: out["correct_items"] += 1; out["items"][c] = "ok"
            else: out["wrong_items"] += 1; out["items"][c] = "wrong:" + "/".join(sorted(g))
        out["exact"] = out["correct_items"] == len(r["codes"]) and out["wrong_items"] == 0
    elif kind == "K2":
        pos = {}
        for tg in r["tags"]:
            m = re.search(rf"\b{re.escape(tg)}\b", t)
            if m: pos[tg] = m.start()
        if len(pos) < len(r["tags"]): out["missing_items"] = len(r["tags"]) - len(pos); order = None
        else: order = [x for x, _ in sorted(pos.items(), key=lambda kv: kv[1])]
        asc = bool(re.search(r"lowest[^.]{0,30}(to|then|,)[^.]{0,30}highest|ascending|from lowest|lowest first|worst to best", t, re.I))
        if order:
            if asc: order = order[::-1]
            out["stated_order"] = order; out["exact"] = order == r["priority"]; out["correct_items"] = sum(1 for a, b in zip(order, r["priority"]) if a == b); out["wrong_items"] = len(order) - out["correct_items"]
    else:
        ok = 0
        for e in r["events"]:
            m = re.search(rf"\b{re.escape(e)}\b(.{{0,80}})", t)
            if not m: out["missing_items"] += 1; out["items"][e] = "missing"; continue
            seg = re.split(r"[;.\n]|\b(?:%s)\b" % "|".join(map(re.escape, r["events"])), m.group(1))[0]; k = re.search(r"(-?\d+)", seg); typ = None
            s = seg.lower()
            if re.search(r"multipl|times|double|triple|\bx\s*\d|\*", s): typ = "mul"
            elif re.search(r"subtract|minus|decreas|less|deduct|(?<!\w)-\s*\d", s): typ = "sub"
            elif re.search(r"\badd|plus|increas|adds|\+", s): typ = "add"
            elif re.search(r"\bset|assign|becomes|reset|replace|equal|=", s): typ = "set"
            kk = int(k.group(1)) if k else (2 if "double" in s else 3 if "triple" in s else None)
            good = typ == r["ops"][e][0] and kk is not None and abs(kk) == r["ops"][e][1]
            out["items"][e] = "ok" if good else f"wrong:{typ},{kk}"; ok += good
        out["correct_items"] = ok; out["wrong_items"] = len(r["events"]) - ok - out["missing_items"]; out["exact"] = ok == len(r["events"])
    return out
