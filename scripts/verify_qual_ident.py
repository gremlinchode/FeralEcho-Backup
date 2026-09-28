"""Mission 3: adversarial/mutation qualification of the deterministic K2/K3 identifiability solver (qual_ident.py).
QUALIFICATION-ONLY. No Ollama call, no QA/QB ledger touched, no Stage 1 material. Every case here is synthetic,
constructed to test the solver's own honesty (does it force an answer it shouldn't?), not to re-derive the real
QUAL worlds. usage: python -I -B scripts/verify_qual_ident.py"""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.experiments.accumulation_probe import qual_ident as QI, tasks as T1

results = []
def check(n, ok, d=""):
    results.append(bool(ok)); print(("PASS " if ok else "FAIL ") + n + (f"  [{d}]" if d and not ok else ""), flush=True)

# ---------- K3 mutation cases ----------
check("K3 baseline: real add-5 samples -> UNIQUE, correct answer", QI.k3_classify([(2, 7), (5, 10)]) == ("UNIQUE", [("add", 5)]))
check("K3 constant changed: add-9 (domain edge) still UNIQUE, correct", QI.k3_classify([(2, 11), (5, 14)]) == ("UNIQUE", [("add", 9)]))
check("K3 operation identity changed: mul instead of add, still UNIQUE, correct", QI.k3_classify([(2, 6), (5, 15)]) == ("UNIQUE", [("mul", 3)]))
check("K3 INSUFFICIENT: single sample does not force a unique answer", QI.k3_classify([(2, 7)]) == "INSUFFICIENT")
r = QI.k3_classify([(2, 5), (2, 9)]); check("K3 CONTRADICTORY: same start, two different results", r == "CONTRADICTORY", str(r))
r = QI.k3_classify([(2, 4), (5, 25)]); check("K3 OUT-OF-HYPOTHESIS-SPACE(family-mismatch): true rule is squaring, not in {add,sub,mul,set}", r[0] == "OUT-OF-HYPOTHESIS-SPACE(family-mismatch)", str(r))
r = QI.k3_classify([(2, 52), (5, 55)]); check("K3 OUT-OF-HYPOTHESIS-SPACE(domain-too-narrow): add-50 exceeds this module's declared 1..12 range", r[0] == "OUT-OF-HYPOTHESIS-SPACE(domain-too-narrow)", str(r))
# two-hypotheses-observationally-equivalent: construct samples where TWO different (op,c) in the declared domain both fit
# e.g. mul by 1 and add by... mul(1): f(x)=x for all x -> only mul(1,) fits that unless add(0)/sub(0) existed, but domain starts at 1.
# construct a genuine same-domain collision: mul(2) at x=... vs add: 2*x = x+c has one intersection per x, need TWO samples both satisfying a second family too.
# add C and sub C' collide iff C=-C' (impossible, domain>0); mul C and add C' collide at (s,r) iff both s1,s2 satisfy 2 linear systems simultaneously only for a specific pair.
# Verified by direct search: mul(3) applied to samples (1,3) is ambiguous against add(2) at the SAME point (1,3) -> use two points that keep both consistent is generally impossible for genuinely different slopes; instead demonstrate ambiguity via INSUFFICIENT (1 point) which is the real, common ambiguity case, and via an explicit constructed collision below.
r = QI.k3_classify([(3, 6)]);
check("K3 AMBIGUOUS-by-insufficiency: one point (3,6) is consistent with BOTH mul(2) and add(3) (and others) -> not UNIQUE", isinstance(r, str) and r == "INSUFFICIENT")
survs_at_one_point = QI.k3_enumerate([(3, 6)])
check("K3: the one-point case genuinely has multiple real survivors (mul(2) and add(3) both present)", ("mul", 2) in survs_at_one_point and ("add", 3) in survs_at_one_point, str(survs_at_one_point))
# order-of-episodes independence (shuffled presentation must not change the verdict)
check("K3 order-independence: reordering the two samples changes nothing", QI.k3_classify([(5, 10), (2, 7)]) == QI.k3_classify([(2, 7), (5, 10)]))
# renamed identifiers must not matter -- the solver never looks at the event NAME at all, only (start,result) pairs
import inspect
check("K3 label-independence: k3_classify's signature is exactly (samples) -- no event name/identifier is ever passed in, so renaming an event cannot change its answer by construction", list(inspect.signature(QI.k3_classify).parameters) == ["samples"])

# ---------- K2 mutation cases ----------
tags4 = ["dajud", "begop", "nakip", "budem"]
base_eps = [([("zed", 4, "dajud"), ("amy", 4, "begop")], "zed"), ([("zed", 4, "begop"), ("amy", 4, "nakip")], "zed"), ([("zed", 4, "nakip"), ("amy", 4, "budem")], "zed")]
check("K2 baseline: 3-link chain -> UNIQUE, correct total order", QI.k2_classify(base_eps, tags4) == ("UNIQUE", [("dajud", "begop", "nakip", "budem")]))
rev_eps = [([("zed", 4, "budem"), ("amy", 4, "nakip")], "zed"), ([("zed", 4, "nakip"), ("amy", 4, "begop")], "zed"), ([("zed", 4, "begop"), ("amy", 4, "dajud")], "zed")]
check("K2 priority order reversed end-to-end: solver correctly recovers the REVERSED order, not the original", QI.k2_classify(rev_eps, tags4) == ("UNIQUE", [("budem", "nakip", "begop", "dajud")]))
insuf_eps = base_eps[:1]
r = QI.k2_classify(insuf_eps, tags4); check("K2 INSUFFICIENT/AMBIGUOUS: only 1 of 3 links known -> not unique (many total orders consistent with one pairwise fact)", r[0] == "AMBIGUOUS" if isinstance(r, tuple) else r == "AMBIGUOUS", str(r))
contra_eps = base_eps + [([("zed", 4, "budem"), ("amy", 4, "dajud")], "zed")]  # forces budem > dajud, contradicting the dajud>...>budem chain
check("K2 CONTRADICTORY: an added episode creates a cycle in the pairwise facts (budem beats dajud, contradicting the established chain)", QI.k2_classify(contra_eps, tags4) == "CONTRADICTORY")
tie_eps = base_eps + [([("mo", 2, "budem"), ("nan", 2, "dajud"), ("pat", 2, "nakip")], "nan")]  # the real 4th K2 episode (3-way tie, no new info)
check("K2: adding the real 4th (3-way score-tie) episode does not change the verdict -- it's consistent, adds no new info", QI.k2_classify(tie_eps, tags4) == QI.k2_classify(base_eps, tags4))
shuffled = [base_eps[2], base_eps[0], base_eps[1]]
check("K2 order-independence: shuffling episode presentation order changes nothing", QI.k2_classify(shuffled, tags4) == QI.k2_classify(base_eps, tags4))
renamed_tags = ["ZZZ1", "ZZZ2", "ZZZ3", "ZZZ4"]
ren_map = dict(zip(tags4, renamed_tags))
ren_eps = [([(n, s, ren_map[t]) for n, s, t in ents], w) for ents, w in base_eps]
expected_renamed_order = tuple(ren_map[t] for t in ("dajud", "begop", "nakip", "budem"))
check("K2 label-independence: renaming all 4 tag tokens produces the isomorphic renamed order, not a different structural answer", QI.k2_classify(ren_eps, renamed_tags) == ("UNIQUE", [expected_renamed_order]))
distractor_eps = base_eps + [([("q", 9, "dajud"), ("r", 9, "dajud")], "q")]  # same-tag tie -> alphabetical fallback (q<r), unrelated to priority, must not corrupt the chain
check("K2 distractor: a same-tag tie episode (falls to the alphabetical fallback, irrelevant to priority) does not corrupt the recovered order", QI.k2_classify(distractor_eps, tags4) == QI.k2_classify(base_eps, tags4))
# same-tag tie (dajud vs dajud): carries ZERO priority information; correct per the FIXED alphabetical fallback, winner=amy (amy<zed).
# NOTE, disclosed rather than silently corrected: the first version of this case used winner="zed" (violating the schema's
# own alphabetical fallback) and the solver correctly refused it as OUT-OF-HYPOTHESIS-SPACE (no order can make a
# same-tag, same-score pair go to the alphabetically LARGER name) -- an even stronger safety behavior than this test
# originally expected. Fixed here to the schema-consistent version, which correctly tests the intended property instead.
naive_lookup_attack_eps = [([("amy", 4, "dajud"), ("zed", 4, "dajud")], "amy")]
r = QI.k2_classify(naive_lookup_attack_eps, tags4)
check("K2 naive-lookup attack: an episode carrying ZERO priority information (same-tag tie, correctly resolved by the alphabetical fallback) must NOT be reported UNIQUE -- a memorizer could overfit to 'amy always wins'; the real solver correctly reports all 24 orders as still possible", isinstance(r, tuple) and r[0] == "AMBIGUOUS" and len(r[1]) == 24, str(r))

# ---------- compare against the REAL frozen QUAL worlds one more time, end to end, via this qualified solver ----------
Ws = json.load(open(Path(__file__).resolve().parent.parent / "memory/experiments/accumulation_probe/v2/qual/oracle/worlds.json"))
all_unique = True
for Wf in Ws:
    r = Wf["K2"]; eps = [(a[0], res) for fn, a, res in T1.teaching_episodes(r)]
    v = QI.k2_classify(eps, r["tags"]); all_unique &= (v == ("UNIQUE", [tuple(r["priority"])]))
    r3 = Wf["K3"]; per = {}
    for fn, a, res in T1.teaching_episodes(r3):
        per.setdefault(a[0][0], []).append((a[1], res))
    for e, s in per.items():
        v3 = QI.k3_classify(s); all_unique &= (v3 == ("UNIQUE", [(r3["ops"][e][0], r3["ops"][e][1])]))
check("qualified solver, run end-to-end against the REAL frozen QUAL worlds: UNIQUE + correct on every one of 2 K2 worlds + 8 K3 events", all_unique)

print(f"\n{sum(results)}/{len(results)} checks passed")
sys.exit(0 if all(results) else 1)
