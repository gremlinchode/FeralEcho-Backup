"""
Tier-5 correctness-retest task pool: 20 fresh coding tasks (4 per category
x 5 categories), authored specifically for the Tier-5 refactor report's own
"NEXT EXPERIMENT" specification (audits/tier5_refactor_report.md) -- a
fresh, disjoint, hash-frozen suite, never reused from the original pilot,
Tier-4's 84-task pool, or verify_synthesis_refactor_live.py's 5-task
VALIDATION_TASKS batch.

Each task follows the exact _t(task_id, category, prompt, test_code,
reference_solution) convention already established by tier4_task_pool.py
-- same shape, same "print('ALL_TESTS_PASSED')" success contract for
objective_verify(), same reference_solution field used ONLY to confirm the
test itself is satisfiable before any real experiment run (never shown to
any generation arm, never exposed to Council/single-model candidates).

Checked directly against tier4_task_pool.py, verify_synthesis_refactor_live.py
(VALIDATION_TASKS), and audits/tier3_apparatus/held_out_task_suite.json
before authoring: no task below is a verbatim or near-verbatim duplicate of
any task in those three sources -- distinct prompts, distinct function
names, distinct problem shapes throughout.

concurrency_stateful (Tier-4's 6th category) is deliberately not used here
-- timing/threading-based oracles add real flakiness risk inside a
timeout-bound sandboxed retest and were judged not worth that risk for a
20-task confirmatory pass; the other five Tier-4 categories are used
instead, 4 tasks each.
"""

TASKS = []


def _t(task_id, category, prompt, test_code, reference_solution):
    TASKS.append({
        "task_id": task_id,
        "category": category,
        "prompt": prompt,
        "test_code": test_code,
        "reference_solution": reference_solution,
    })


# ============================================================================
# CATEGORY: bug_fixing -- 4 tasks
# ============================================================================

_t("r-bf01", "bug_fixing",
   "The function below should return the second-largest DISTINCT value in "
   "a list of numbers (length >= 2, guaranteed to contain at least two "
   "distinct values). It has a bug. Fix it and return the complete "
   "corrected function.\n\n"
   "def second_largest(nums):\n"
   "    largest = max(nums)\n"
   "    second = min(nums)\n"
   "    for n in nums:\n"
   "        if n > second and n < largest:\n"
   "            second = n\n"
   "    return second",
   """
assert second_largest([1, 5, 3, 5, 2]) == 3
assert second_largest([10, 20]) == 10
assert second_largest([4, 4, 4, 7]) == 4
assert second_largest([-1, -2, -3]) == -2
assert second_largest([100, 1, 99]) == 99
print('ALL_TESTS_PASSED')
""",
   "def second_largest(nums):\n"
   "    distinct = sorted(set(nums), reverse=True)\n"
   "    return distinct[1]")

_t("r-bf02", "bug_fixing",
   "The function below should return True if `n` is a power of two "
   "(1, 2, 4, 8, ...), and False otherwise (including for n <= 0). It has "
   "a bug. Fix it and return the complete corrected function.\n\n"
   "def is_power_of_two(n):\n"
   "    if n <= 0:\n"
   "        return False\n"
   "    while n > 1:\n"
   "        n = n / 2\n"
   "    return True",
   """
assert is_power_of_two(1) == True
assert is_power_of_two(2) == True
assert is_power_of_two(3) == False
assert is_power_of_two(64) == True
assert is_power_of_two(0) == False
assert is_power_of_two(-4) == False
assert is_power_of_two(6) == False
print('ALL_TESTS_PASSED')
""",
   "def is_power_of_two(n):\n"
   "    if n <= 0:\n"
   "        return False\n"
   "    while n % 2 == 0:\n"
   "        n = n // 2\n"
   "    return n == 1")

_t("r-bf03", "bug_fixing",
   "The function below should return the running maximum-so-far for each "
   "position in a list of numbers (e.g. [3,1,4,1,5] -> [3,3,4,4,5]). It "
   "has a bug. Fix it and return the complete corrected function.\n\n"
   "def running_max(nums):\n"
   "    result = []\n"
   "    current_max = 0\n"
   "    for n in nums:\n"
   "        if n > current_max:\n"
   "            current_max = n\n"
   "        result.append(current_max)\n"
   "    return result",
   """
assert running_max([3, 1, 4, 1, 5]) == [3, 3, 4, 4, 5]
assert running_max([-5, -3, -8, -1]) == [-5, -3, -3, -1]
assert running_max([5]) == [5]
assert running_max([1, 1, 1]) == [1, 1, 1]
print('ALL_TESTS_PASSED')
""",
   "def running_max(nums):\n"
   "    result = []\n"
   "    current_max = None\n"
   "    for n in nums:\n"
   "        if current_max is None or n > current_max:\n"
   "            current_max = n\n"
   "        result.append(current_max)\n"
   "    return result")

_t("r-bf04", "bug_fixing",
   "The function below should remove duplicate values from a list while "
   "preserving the order of first occurrence. It has a bug. Fix it and "
   "return the complete corrected function.\n\n"
   "def dedupe_preserve_order(items):\n"
   "    result = []\n"
   "    for item in items:\n"
   "        if item not in result:\n"
   "            items.remove(item)\n"
   "        result.append(item)\n"
   "    return result",
   """
assert dedupe_preserve_order([1, 2, 2, 3, 1, 4]) == [1, 2, 3, 4]
assert dedupe_preserve_order([]) == []
assert dedupe_preserve_order([5, 5, 5]) == [5]
assert dedupe_preserve_order(['a', 'b', 'a', 'c', 'b']) == ['a', 'b', 'c']
print('ALL_TESTS_PASSED')
""",
   "def dedupe_preserve_order(items):\n"
   "    result = []\n"
   "    seen = set()\n"
   "    for item in items:\n"
   "        if item not in seen:\n"
   "            seen.add(item)\n"
   "            result.append(item)\n"
   "    return result")


# ============================================================================
# CATEGORY: algorithmic_edge_case -- 4 tasks
# ============================================================================

_t("r-ae01", "algorithmic_edge_case",
   "Write a function `binary_search(sorted_nums, target)` that returns the "
   "index of `target` in the sorted list `sorted_nums` using binary "
   "search, or -1 if `target` is not present. Handle an empty list and a "
   "list with duplicate values (returning the index of any matching "
   "occurrence is acceptable when duplicates exist). Return the complete "
   "function.",
   """
assert binary_search([1, 3, 5, 7, 9], 5) == 2
assert binary_search([1, 3, 5, 7, 9], 1) == 0
assert binary_search([1, 3, 5, 7, 9], 9) == 4
assert binary_search([1, 3, 5, 7, 9], 4) == -1
assert binary_search([], 3) == -1
assert binary_search([2, 2, 2, 2], 2) in (0, 1, 2, 3)
print('ALL_TESTS_PASSED')
""",
   "def binary_search(sorted_nums, target):\n"
   "    lo, hi = 0, len(sorted_nums) - 1\n"
   "    while lo <= hi:\n"
   "        mid = (lo + hi) // 2\n"
   "        if sorted_nums[mid] == target:\n"
   "            return mid\n"
   "        elif sorted_nums[mid] < target:\n"
   "            lo = mid + 1\n"
   "        else:\n"
   "            hi = mid - 1\n"
   "    return -1")

_t("r-ae02", "algorithmic_edge_case",
   "Write a function `merge_sorted(list_a, list_b)` that merges two "
   "already-sorted lists of numbers into a single sorted list, handling "
   "the case where either input list is empty. Return the complete "
   "function.",
   """
assert merge_sorted([1, 3, 5], [2, 4, 6]) == [1, 2, 3, 4, 5, 6]
assert merge_sorted([], [1, 2, 3]) == [1, 2, 3]
assert merge_sorted([1, 2, 3], []) == [1, 2, 3]
assert merge_sorted([], []) == []
assert merge_sorted([1, 1, 2], [1, 3]) == [1, 1, 1, 2, 3]
print('ALL_TESTS_PASSED')
""",
   "def merge_sorted(list_a, list_b):\n"
   "    result = []\n"
   "    i = j = 0\n"
   "    while i < len(list_a) and j < len(list_b):\n"
   "        if list_a[i] <= list_b[j]:\n"
   "            result.append(list_a[i]); i += 1\n"
   "        else:\n"
   "            result.append(list_b[j]); j += 1\n"
   "    result.extend(list_a[i:])\n"
   "    result.extend(list_b[j:])\n"
   "    return result")

_t("r-ae03", "algorithmic_edge_case",
   "Write a function `is_clean_palindrome(s)` that returns True if `s` is "
   "a palindrome when ignoring case and ignoring all non-alphanumeric "
   "characters (spaces, punctuation, etc.), and False otherwise. An empty "
   "string or a string with no alphanumeric characters should return "
   "True. Return the complete function.",
   """
assert is_clean_palindrome("A man, a plan, a canal: Panama") == True
assert is_clean_palindrome("race a car") == False
assert is_clean_palindrome("") == True
assert is_clean_palindrome("!!!") == True
assert is_clean_palindrome("No 'x' in Nixon") == True
print('ALL_TESTS_PASSED')
""",
   "def is_clean_palindrome(s):\n"
   "    cleaned = [c.lower() for c in s if c.isalnum()]\n"
   "    return cleaned == cleaned[::-1]")

_t("r-ae04", "algorithmic_edge_case",
   "Write a function `gcd_of_list(nums)` that returns the greatest common "
   "divisor of ALL numbers in the list `nums` (length 1 or more, all "
   "positive integers). For a single-element list, return that element. "
   "Return the complete function.",
   """
assert gcd_of_list([12, 18]) == 6
assert gcd_of_list([12, 18, 24]) == 6
assert gcd_of_list([7]) == 7
assert gcd_of_list([5, 10, 15, 25]) == 5
assert gcd_of_list([17, 13]) == 1
print('ALL_TESTS_PASSED')
""",
   "import math\n"
   "def gcd_of_list(nums):\n"
   "    result = nums[0]\n"
   "    for n in nums[1:]:\n"
   "        result = math.gcd(result, n)\n"
   "    return result")


# ============================================================================
# CATEGORY: refactoring -- 4 tasks
# (test_code checks functional behavior only, never "style")
# ============================================================================

_t("r-rf01", "refactoring",
   "The function below flattens a list that contains only numbers and "
   "other flat lists of numbers (one level of nesting) into a single flat "
   "list, preserving order. It works but is written awkwardly. Rewrite it "
   "into cleaner code with IDENTICAL behavior on every input. Return the "
   "complete function.\n\n"
   "def flatten_one_level(items):\n"
   "    output = []\n"
   "    i = 0\n"
   "    while i < len(items):\n"
   "        current = items[i]\n"
   "        if type(current) == list:\n"
   "            j = 0\n"
   "            while j < len(current):\n"
   "                output.append(current[j])\n"
   "                j = j + 1\n"
   "        else:\n"
   "            output.append(current)\n"
   "        i = i + 1\n"
   "    return output",
   """
assert flatten_one_level([1, [2, 3], 4, [5, 6, 7]]) == [1, 2, 3, 4, 5, 6, 7]
assert flatten_one_level([]) == []
assert flatten_one_level([1, 2, 3]) == [1, 2, 3]
assert flatten_one_level([[1, 2], [3, 4]]) == [1, 2, 3, 4]
assert flatten_one_level([[]]) == []
print('ALL_TESTS_PASSED')
""",
   "def flatten_one_level(items):\n"
   "    output = []\n"
   "    for current in items:\n"
   "        if isinstance(current, list):\n"
   "            output.extend(current)\n"
   "        else:\n"
   "            output.append(current)\n"
   "    return output")

_t("r-rf02", "refactoring",
   "The function below counts how many times each word appears in a list "
   "of words (case-sensitive) and returns a dict. It works but is written "
   "awkwardly. Rewrite it into cleaner code with IDENTICAL behavior on "
   "every input. Return the complete function.\n\n"
   "def word_counts(words):\n"
   "    counts = {}\n"
   "    for i in range(len(words)):\n"
   "        w = words[i]\n"
   "        found = False\n"
   "        for key in counts:\n"
   "            if key == w:\n"
   "                counts[key] = counts[key] + 1\n"
   "                found = True\n"
   "        if not found:\n"
   "            counts[w] = 1\n"
   "    return counts",
   """
assert word_counts(["a", "b", "a", "c", "b", "a"]) == {"a": 3, "b": 2, "c": 1}
assert word_counts([]) == {}
assert word_counts(["x"]) == {"x": 1}
assert word_counts(["Cat", "cat"]) == {"Cat": 1, "cat": 1}
print('ALL_TESTS_PASSED')
""",
   "def word_counts(words):\n"
   "    counts = {}\n"
   "    for w in words:\n"
   "        counts[w] = counts.get(w, 0) + 1\n"
   "    return counts")

_t("r-rf03", "refactoring",
   "The function below sums the even numbers in a list. It works but is "
   "written awkwardly. Rewrite it into cleaner code with IDENTICAL "
   "behavior on every input, including negative numbers. Return the "
   "complete function.\n\n"
   "def sum_evens(nums):\n"
   "    total = 0\n"
   "    index = 0\n"
   "    while index < len(nums):\n"
   "        value = nums[index]\n"
   "        remainder = value % 2\n"
   "        if remainder == 0:\n"
   "            total = total + value\n"
   "        index = index + 1\n"
   "    return total",
   """
assert sum_evens([1, 2, 3, 4, 5, 6]) == 12
assert sum_evens([]) == 0
assert sum_evens([1, 3, 5]) == 0
assert sum_evens([-2, -3, -4]) == -6
assert sum_evens([0, 1, 2]) == 2
print('ALL_TESTS_PASSED')
""",
   "def sum_evens(nums):\n"
   "    return sum(n for n in nums if n % 2 == 0)")

_t("r-rf04", "refactoring",
   "The function below checks whether an integer n (n >= 2) is prime. It "
   "works correctly but is inefficient and awkwardly written. Rewrite it "
   "into cleaner, more efficient code with IDENTICAL behavior on every "
   "input. Return the complete function.\n\n"
   "def is_prime(n):\n"
   "    divisors = []\n"
   "    for i in range(1, n + 1):\n"
   "        if n % i == 0:\n"
   "            divisors.append(i)\n"
   "    if len(divisors) == 2:\n"
   "        return True\n"
   "    else:\n"
   "        return False",
   """
assert is_prime(2) == True
assert is_prime(3) == True
assert is_prime(4) == False
assert is_prime(17) == True
assert is_prime(1) == False
assert is_prime(97) == True
assert is_prime(100) == False
print('ALL_TESTS_PASSED')
""",
   "def is_prime(n):\n"
   "    if n < 2:\n"
   "        return False\n"
   "    if n in (2, 3):\n"
   "        return True\n"
   "    if n % 2 == 0:\n"
   "        return False\n"
   "    i = 3\n"
   "    while i * i <= n:\n"
   "        if n % i == 0:\n"
   "            return False\n"
   "        i += 2\n"
   "    return True")


# ============================================================================
# CATEGORY: input_validation_defensive -- 4 tasks
# ============================================================================

_t("r-iv01", "input_validation_defensive",
   "Write a function `safe_divide(a, b)` that returns `a / b` as a float, "
   "but returns None (instead of raising) if `b` is zero. Return the "
   "complete function.",
   """
assert safe_divide(10, 2) == 5.0
assert safe_divide(7, 2) == 3.5
assert safe_divide(5, 0) is None
assert safe_divide(0, 5) == 0.0
assert safe_divide(-9, 3) == -3.0
print('ALL_TESTS_PASSED')
""",
   "def safe_divide(a, b):\n"
   "    if b == 0:\n"
   "        return None\n"
   "    return a / b")

_t("r-iv02", "input_validation_defensive",
   "Write a function `parse_int_or_default(s, default)` that returns the "
   "integer value of string `s` if `s` represents a valid base-10 integer "
   "(optionally with a leading + or - sign), and returns `default` "
   "otherwise (including for non-string input, empty string, or a string "
   "like '3.5' or 'abc'). Return the complete function.",
   """
assert parse_int_or_default("42", -1) == 42
assert parse_int_or_default("-7", -1) == -7
assert parse_int_or_default("+3", -1) == 3
assert parse_int_or_default("abc", -1) == -1
assert parse_int_or_default("3.5", -1) == -1
assert parse_int_or_default("", -1) == -1
assert parse_int_or_default(None, 0) == 0
print('ALL_TESTS_PASSED')
""",
   "def parse_int_or_default(s, default):\n"
   "    if not isinstance(s, str):\n"
   "        return default\n"
   "    try:\n"
   "        return int(s)\n"
   "    except ValueError:\n"
   "        return default")

_t("r-iv03", "input_validation_defensive",
   "Write a function `get_first_or_none(lst)` that returns the first "
   "element of `lst` if it is a non-empty list, and returns None "
   "otherwise (including for an empty list, None, or any non-list "
   "input). Return the complete function.",
   """
assert get_first_or_none([1, 2, 3]) == 1
assert get_first_or_none(["a"]) == "a"
assert get_first_or_none([]) is None
assert get_first_or_none(None) is None
assert get_first_or_none("not a list") is None
print('ALL_TESTS_PASSED')
""",
   "def get_first_or_none(lst):\n"
   "    if isinstance(lst, list) and len(lst) > 0:\n"
   "        return lst[0]\n"
   "    return None")

_t("r-iv04", "input_validation_defensive",
   "Write a function `clamp(value, lo, hi)` that returns `value` "
   "restricted to the range [lo, hi]: if value < lo return lo, if "
   "value > hi return hi, otherwise return value. If `lo` is greater "
   "than `hi`, treat the effective range as [hi, lo] (i.e. swap them "
   "first). Return the complete function.",
   """
assert clamp(5, 0, 10) == 5
assert clamp(-5, 0, 10) == 0
assert clamp(15, 0, 10) == 10
assert clamp(5, 10, 0) == 5
assert clamp(-5, 10, 0) == 0
assert clamp(3, 3, 3) == 3
print('ALL_TESTS_PASSED')
""",
   "def clamp(value, lo, hi):\n"
   "    if lo > hi:\n"
   "        lo, hi = hi, lo\n"
   "    if value < lo:\n"
   "        return lo\n"
   "    if value > hi:\n"
   "        return hi\n"
   "    return value")


# ============================================================================
# CATEGORY: data_transformation_parsing -- 4 tasks
# ============================================================================

_t("r-dt01", "data_transformation_parsing",
   "Write a function `csv_row_to_dict(header, row)` where `header` and "
   "`row` are lists of equal length (strings), and it returns a dict "
   "mapping each header entry to the corresponding row value at the same "
   "index. Return the complete function.",
   """
assert csv_row_to_dict(["name", "age"], ["Alice", "30"]) == {"name": "Alice", "age": "30"}
assert csv_row_to_dict([], []) == {}
assert csv_row_to_dict(["a", "b", "c"], ["1", "2", "3"]) == {"a": "1", "b": "2", "c": "3"}
print('ALL_TESTS_PASSED')
""",
   "def csv_row_to_dict(header, row):\n"
   "    return dict(zip(header, row))")

_t("r-dt02", "data_transformation_parsing",
   "Write a function `group_by_parity(nums)` that takes a list of "
   "integers and returns a dict with two keys, 'even' and 'odd', each "
   "mapping to a list of the numbers of that parity, in their original "
   "relative order. Return the complete function.",
   """
assert group_by_parity([1, 2, 3, 4, 5]) == {"even": [2, 4], "odd": [1, 3, 5]}
assert group_by_parity([]) == {"even": [], "odd": []}
assert group_by_parity([2, 4, 6]) == {"even": [2, 4, 6], "odd": []}
assert group_by_parity([-3, -2]) == {"even": [-2], "odd": [-3]}
print('ALL_TESTS_PASSED')
""",
   "def group_by_parity(nums):\n"
   "    result = {'even': [], 'odd': []}\n"
   "    for n in nums:\n"
   "        result['even' if n % 2 == 0 else 'odd'].append(n)\n"
   "    return result")

_t("r-dt03", "data_transformation_parsing",
   "Write a function `flatten_dict_keys(d, sep='.')` that takes a dict "
   "which may contain nested dicts EXACTLY ONE LEVEL DEEP (values are "
   "either plain values or a dict of plain values, never deeper), and "
   "returns a new flat dict where nested keys are joined with `sep` "
   "(e.g. {'a': {'b': 1}} with sep='.' becomes {'a.b': 1}). Top-level "
   "non-dict values keep their original key unchanged. Return the "
   "complete function.",
   """
assert flatten_dict_keys({"a": {"b": 1, "c": 2}, "d": 3}) == {"a.b": 1, "a.c": 2, "d": 3}
assert flatten_dict_keys({}) == {}
assert flatten_dict_keys({"x": 5}) == {"x": 5}
assert flatten_dict_keys({"a": {"b": 1}}, sep="_") == {"a_b": 1}
print('ALL_TESTS_PASSED')
""",
   "def flatten_dict_keys(d, sep='.'):\n"
   "    result = {}\n"
   "    for k, v in d.items():\n"
   "        if isinstance(v, dict):\n"
   "            for inner_k, inner_v in v.items():\n"
   "                result[f\"{k}{sep}{inner_k}\"] = inner_v\n"
   "        else:\n"
   "            result[k] = v\n"
   "    return result")

_t("r-dt04", "data_transformation_parsing",
   "Write a function `invert_dict(d)` that takes a dict whose values are "
   "all unique and hashable, and returns a new dict mapping each original "
   "value to its corresponding key. Return the complete function.",
   """
assert invert_dict({"a": 1, "b": 2, "c": 3}) == {1: "a", 2: "b", 3: "c"}
assert invert_dict({}) == {}
assert invert_dict({"x": "y"}) == {"y": "x"}
print('ALL_TESTS_PASSED')
""",
   "def invert_dict(d):\n"
   "    return {v: k for k, v in d.items()}")
