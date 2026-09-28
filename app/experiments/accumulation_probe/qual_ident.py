"""AP-0 QUALIFICATION-ONLY deterministic identifiability solver for K2/K3 (Mission 1/2/3/4 of the 2026-09-22 diagnostic
investigation). Purely symbolic: reads only the already-frozen QUAL oracle (memory/experiments/accumulation_probe/v2/qual/oracle/worlds.json)
and its own synthetic mutation-test fixtures. NEVER calls Ollama, NEVER writes to any QA/QB ledger, NEVER touches Stage 1
(no Stage 1 material exists to touch). Its purpose is to determine whether the K2/K3 latent conventions are recoverable
FROM THE EPISODES ALONE under a declared, pre-stated hypothesis space -- not to make Echo/QA/QB look better.

Disclosure (required by the mission's own honesty standard): the author of this module had already read the true K2/K3
answers (via the earlier hand adjudication) before choosing the numeric domains below. To keep the domains from being
covertly reverse-engineered from those answers, they are set by an explicit, stated principle -- "the smallest round
range a programmer would try first for a toy integer convention" -- rather than copied from worlds.py's real generation
bounds (add in [2,9], sub in [1,5], mul in [2,4], set in [3,9]; NOT read by this module). The chosen domain (1..12 for
add/sub/set, 1..12 for mul) is WIDER than the true generation range on every side, which if anything makes the
identifiability question HARDER (more candidate hypotheses to rule out), not easier -- a solver reverse-engineered to
know the answer would use the narrower true range and thereby collide with fewer false candidates.
"""
import itertools

# ---------- K2: tag priority (permutation search over the 4 tags actually seen in the episodes) ----------
def k2_predict(order, entries):
    """order: candidate priority list, best->worst. entries: [(name, score, tag), ...]. Same logic as the real k2_win
    (BASE_SPEC's rule, which IS given to the constructor): highest score wins; ties -> higher tag priority; ties -> alphabetically smaller name."""
    rank = {t: i for i, t in enumerate(order)}
    # comparator: maximize score, then minimize rank index (higher priority = smaller index -> better), then minimize name
    def key(e):
        name, score, tag = e
        return (score, -rank.get(tag, 999), tuple(-ord(c) for c in name))
    return max(entries, key=key)[0]

def k2_enumerate(episodes, tags):
    """episodes: [(entries, observed_winner_name), ...]. tags: the 4 tag tokens seen. Returns all permutations of `tags`
    consistent with every episode (the declared hypothesis space is exactly 'some strict total order of these 4 known
    tags' -- given directly by BASE_SPEC's own stated rule, not assumed by this solver)."""
    survivors = []
    for order in itertools.permutations(tags):
        if all(k2_predict(order, entries) == winner for entries, winner in episodes):
            survivors.append(order)
    return survivors

# ---------- K3: per-event operation + constant (independent per event; declared hypothesis space stated in the mission) ----------
_DOMAIN_ADD_SUB_SET = range(1, 13)   # 1..12, a round a-priori range -- see module docstring
_DOMAIN_MUL = range(1, 13)           # 1..12 (includes the degenerate mul-by-1 case deliberately, not excluded post hoc)

def k3_hypotheses():
    hs = []
    for c in _DOMAIN_ADD_SUB_SET: hs.append(("add", c)); hs.append(("sub", c)); hs.append(("set", c))
    for c in _DOMAIN_MUL: hs.append(("mul", c))
    return hs

def k3_apply(hyp, start):
    op, c = hyp
    return start + c if op == "add" else start - c if op == "sub" else start * c if op == "mul" else c

def k3_enumerate(samples):
    """samples: [(start, result), ...] for ONE event. Returns all (op, c) consistent with every sample."""
    return [h for h in k3_hypotheses() if all(k3_apply(h, s) == r for s, r in samples)]

def k3_raw_contradiction(samples):
    """True iff the SAME start value was observed with two DIFFERENT results -- a contradiction independent of any
    hypothesis space (no function at all, of any kind, could satisfy this)."""
    seen = {}
    for s, r in samples:
        if s in seen and seen[s] != r: return True
        seen[s] = r
    return False

def k3_unbounded_fit_exists(samples):
    """True iff SOME add/sub/mul/set hypothesis fits, ignoring this module's declared domain caps -- distinguishes
    'right family, constant just outside our declared range' (a domain limit) from 'no such op-family fits at all'
    (a genuine out-of-hypothesis-language case, e.g. a squaring or XOR rule)."""
    if len(samples) < 2:
        return None  # can't determine with a single point; every family has SOME constant that fits one point
    (s1, r1), (s2, r2) = samples[0], samples[1]
    checks = [r1 - s1 == r2 - s2, s1 - r1 == s2 - r2, r1 == r2, (s1 != 0 and s2 != 0 and r1 / s1 == r2 / s2)]
    return any(checks)

def k3_classify(samples):
    """Full mission-required classification for one K3 event's samples, using ALL available signal (not just survivor
    count), so the solver is not merely 'zero survivors -> pick a label by default'."""
    if len(samples) < 2:
        return "INSUFFICIENT"
    if k3_raw_contradiction(samples):
        return "CONTRADICTORY"
    surv = k3_enumerate(samples)
    if len(surv) == 1: return "UNIQUE", surv
    if len(surv) > 1: return "AMBIGUOUS", surv
    # zero survivors within the declared domain
    if k3_unbounded_fit_exists(samples): return "OUT-OF-HYPOTHESIS-SPACE(domain-too-narrow)", []
    return "OUT-OF-HYPOTHESIS-SPACE(family-mismatch)", []

# ---------- K2 contradiction detection (transitivity-cycle check on the pairwise-comparable episodes) ----------
def k2_pairwise_facts(episodes):
    """Extract direct 'tag A beats tag B' facts from episodes where score is tied between exactly two entries whose
    tags differ (the only episodes that pin down a DIRECT pairwise tag relation without depending on the unknown order)."""
    facts = []
    for entries, winner in episodes:
        tied = [e for e in entries if e[1] == max(x[1] for x in entries)]
        if len(tied) != 2: continue
        (n1, s1, t1), (n2, s2, t2) = tied
        if t1 == t2: continue
        w = next(e for e in tied if e[0] == winner); loser_tag = t2 if w[2] == t1 else t1
        facts.append((w[2], loser_tag))  # (better_tag, worse_tag)
    return facts

def k2_has_cycle(facts):
    """A cycle among the direct pairwise facts means the episodes are mutually contradictory -- no total order,
    however chosen, could satisfy them all."""
    graph = {}
    for a, b in facts: graph.setdefault(a, set()).add(b)
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {}
    def visit(n):
        color[n] = GRAY
        for m in graph.get(n, ()):
            if color.get(m, WHITE) == GRAY: return True
            if color.get(m, WHITE) == WHITE and visit(m): return True
        color[n] = BLACK
        return False
    return any(color.get(n, WHITE) == WHITE and visit(n) for n in graph)

def k2_classify(episodes, tags):
    if len(episodes) < 1:
        return "INSUFFICIENT"
    facts = k2_pairwise_facts(episodes)
    if k2_has_cycle(facts): return "CONTRADICTORY"
    surv = k2_enumerate(episodes, tags)
    if not surv: return "OUT-OF-HYPOTHESIS-SPACE"  # BASE_SPEC's own rule structure doesn't fit these episodes at all
    if len(surv) == 1: return "UNIQUE", surv
    return "AMBIGUOUS", surv

# ---------- generic classification (kept for backward-compat with the first exploratory run) ----------
def classify(survivors):
    if not survivors: return "CONTRADICTORY-OR-OUT-OF-SPACE"
    if len(survivors) == 1: return "UNIQUE"
    return "AMBIGUOUS"
