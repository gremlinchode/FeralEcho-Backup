"""
SCRATCH calibration-only variant of a second, deliberately non-canonical
task family, tried after "merge overlapping intervals" (v1) saturated at
or near 100% for every locally available model, at two difficulty levels.
This file is calibration-only; if this family is adopted it will be
promoted into tasks.py properly (with a documented rename) rather than
silently left as a "_scratch" file feeding the sealed experiment.
"""
import random

def reference_solve(records):
    # records: list of [label:str, amount:int]
    from collections import defaultdict
    even_sum = defaultdict(int)
    odd_count = defaultdict(int)
    labels = set()
    for label, amount in records:
        labels.add(label)
        if amount % 2 == 0:
            even_sum[label] += amount
        else:
            odd_count[label] += 1
    out = []
    for label in sorted(labels):
        score = even_sum[label] - odd_count[label]
        if score != 0:
            out.append([label, score])
    return out

def gen_instance(rng, n_records, n_labels):
    labels = [chr(ord('a') + i) for i in range(n_labels)]
    records = []
    for _ in range(n_records):
        label = rng.choice(labels)
        amount = rng.randint(-9, 9)
        records.append([label, amount])
    return records

if __name__ == "__main__":
    rng = random.Random(1)
    tasks = []
    for i in range(5):
        recs = gen_instance(rng, 12, 4)
        tasks.append({"id": f"calib_v2_{i:02d}", "records": recs, "expected": reference_solve(recs)})
    import json
    print(json.dumps(tasks, indent=1))
