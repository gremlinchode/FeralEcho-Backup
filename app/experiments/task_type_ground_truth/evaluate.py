"""
Mission 34 — Conditions A/B/C evaluation (app/experiments/task_type_ground_truth/).

Runs ONLY after gold_labels.jsonl exists and is locked (Mission 33,
Section 11's blinding checkpoint). This module deliberately imports the
real production functions/classes — that is correct and required at this
stage (the comparison itself needs them); the blinding rule only bound
blind_label.py and the labeling step that preceded this file ever running.

Safety, per integrity-and-safety.md and Mission 32/33's own established
discipline:
  - Condition A / B are READ-ONLY calls against the real production code
    and the real persisted memory/task_type_classifier.pkl (predict()
    only — confirmed by source read, task_type_classifier.py:184, calls
    only predict_proba_one, never learn_one/.save()).
  - Condition C is a FRESH, isolated, in-memory TaskTypeClassifier
    instance — same real class, same real river pipeline — trained ONLY
    on the gold-labeled examples, NEVER loaded from and NEVER saved to
    memory/task_type_classifier.pkl. Confirmed by construction: this
    module never calls TaskTypeClassifier.load() or the singleton
    get_task_type_classifier() for Condition C, only TaskTypeClassifier()
    directly.
  - Condition C uses leave-one-out (LOO) evaluation rather than a single
    fixed train/eval split — a deliberate, disclosed deviation from
    Mission 33's simpler sketch, justified by the small real n: a fixed
    split at n~20-27 wastes too much of an already-scarce gold set, and
    LOO is standard, well-established small-sample-evaluation practice
    (every prediction is still genuinely out-of-sample for the specific
    model that produced it), not a shortcut.
"""
import sys
from app.experiments.task_type_ground_truth.schema import ConditionResult, LABEL_CHOICES
from app.experiments.task_type_ground_truth.blind_label import load_labels
from app.experiments.task_type_ground_truth.dataset import build_pool


def _prompt_lookup():
    return {ex.example_id: ex.prompt for ex in build_pool()}


def run_condition_a(prompts: dict) -> list[ConditionResult]:
    """Pure static heuristic — compute_intent_heatmap()'s own argmax,
    classifier never consulted. Mirrors Mission 33 Section 9's definition
    exactly, not the blended resolve_task_type() pipeline."""
    from app.core.echo_model_orchestrator import compute_intent_heatmap
    results = []
    for ex_id, prompt in prompts.items():
        heatmap = compute_intent_heatmap(prompt)
        primary = max(heatmap, key=heatmap.get)
        results.append(ConditionResult(ex_id, "A_heuristic", primary, heatmap[primary]))
    return results


def run_condition_b(prompts: dict) -> list[ConditionResult]:
    """Real, currently-persisted production classifier. Read-only —
    predict() only (task_type_classifier.py:184: predict_proba_one only,
    no learn_one/.save() anywhere in that method)."""
    from app.core.task_type_classifier import get_task_type_classifier
    clf = get_task_type_classifier()
    results = []
    for ex_id, prompt in prompts.items():
        label, conf = clf.predict(prompt)
        results.append(ConditionResult(ex_id, "B_classifier", label, conf if label else None))
    return results


def run_condition_c_loo(prompts: dict, gold_labels: list) -> list[ConditionResult]:
    """Leave-one-out: for each gold-labeled example, train a FRESH,
    isolated, in-memory TaskTypeClassifier on every OTHER gold-labeled
    example, then predict on the held-out one. Never touches the real
    persisted pkl. Skips examples whose gold label is "ambiguous" or
    "none_of_these" for training purposes (river_deliberation's own
    TASK_TYPES has no such buckets) but still attempts a prediction for
    them, so their outcome is visible rather than silently dropped."""
    from app.core.task_type_classifier import TaskTypeClassifier, TASK_TYPES

    trainable = [g for g in gold_labels if g.label in TASK_TYPES]
    if len(trainable) < 2:
        raise RuntimeError(
            f"Only {len(trainable)} gold labels fall in TASK_TYPES "
            f"({TASK_TYPES}) — not enough to run leave-one-out."
        )

    results = []
    for held_out in gold_labels:
        train_set = [g for g in trainable if g.example_id != held_out.example_id]
        # Fresh instance every iteration — no state carries between folds.
        clf = TaskTypeClassifier()
        for g in train_set:
            clf.learn(prompts[g.example_id], g.label)
        prompt = prompts[held_out.example_id]
        # Bypass the trust-floor gate for this evaluation: with n<30 total,
        # is_well_observed()'s real thresholds (200/30) can never be met,
        # which would make Condition C trivially return (None, 0.0) for
        # every single example regardless of what the model actually
        # learned. That gate exists to protect PRODUCTION routing from an
        # undertrained model; it is not a property of "did the model learn
        # a useful decision boundary," which is what this experiment is
        # measuring. Read the raw proba directly instead, disclosed here
        # rather than silently reimplemented as if it were predict().
        if clf._model is None:
            results.append(ConditionResult(held_out.example_id, "C_independent", None, None))
            continue
        try:
            proba = clf._model.predict_proba_one(prompt)
        except Exception:
            proba = None
        if not proba:
            results.append(ConditionResult(held_out.example_id, "C_independent", None, None))
            continue
        label = max(proba, key=proba.get)
        results.append(ConditionResult(held_out.example_id, "C_independent", label, proba[label]))
    return results


def score(results: list[ConditionResult], gold_labels: list) -> dict:
    gold_by_id = {g.example_id: g.label for g in gold_labels}
    for r in results:
        gold = gold_by_id.get(r.example_id)
        # Bug caught before this was ever run: the original expression used
        # Python's chained-comparison semantics ("gold in X is False"),
        # which does NOT mean "gold not in X" — fixed to the explicit,
        # unambiguous form.
        scorable = r.prediction is not None and gold not in ("ambiguous", "none_of_these")
        r.matches_gold = (r.prediction == gold) if scorable else None
    n_scored = sum(1 for r in results if r.matches_gold is not None)
    n_correct = sum(1 for r in results if r.matches_gold is True)
    n_no_prediction = sum(1 for r in results if r.prediction is None)
    return {
        "n_total": len(results),
        "n_scored": n_scored,
        "n_correct": n_correct,
        "n_no_prediction": n_no_prediction,
        "accuracy_of_scored": round(n_correct / n_scored, 4) if n_scored else None,
        "accuracy_of_all": round(n_correct / len(results), 4) if results else None,
    }


def main():
    gold_labels = load_labels()
    prompts = _prompt_lookup()
    # sanity: every gold label must correspond to a real pool item
    missing = [g.example_id for g in gold_labels if g.example_id not in prompts]
    if missing:
        raise RuntimeError(f"gold_labels.jsonl references unknown example_ids: {missing}")

    labeled_prompts = {g.example_id: prompts[g.example_id] for g in gold_labels}

    a_results = run_condition_a(labeled_prompts)
    b_results = run_condition_b(labeled_prompts)
    c_results = run_condition_c_loo(labeled_prompts, gold_labels)

    print("=== Condition A (static heuristic) ===")
    print(score(a_results, gold_labels))
    print("=== Condition B (real production classifier, read-only) ===")
    print(score(b_results, gold_labels))
    print("=== Condition C (leave-one-out, independently gold-trained) ===")
    print(score(c_results, gold_labels))

    from app.experiments.task_type_ground_truth.dataset import build_pool
    provenance = {ex.example_id: ex.provenance for ex in build_pool()}
    print("\n=== Per-example detail ===")
    for g in gold_labels:
        a = next(r for r in a_results if r.example_id == g.example_id)
        b = next(r for r in b_results if r.example_id == g.example_id)
        c = next(r for r in c_results if r.example_id == g.example_id)
        print(f"{g.example_id:8s} [{provenance[g.example_id]:24s}] gold={g.label:14s} "
              f"A={str(a.prediction):12s} B={str(b.prediction):12s} C={str(c.prediction):12s}")


if __name__ == "__main__":
    main()
