"""
Tier-4 confirmatory task pool: 84 candidate tasks (14 per category x 6
categories), each with a prompt (what the model sees), test_code (the
objective, sandboxed ground-truth check), and a reference_solution (used
ONLY by scripts/tier4_verify_task_pool.py to confirm the test itself is
satisfiable and correctly written -- never shown to any generation arm,
never shipped in the frozen task-suite JSON).

None of these tasks are verbatim or near-verbatim duplicates of any task
in audits/capability_pilot/task_suite.json or
audits/tier3_apparatus/held_out_task_suite.json (checked by direct read
of both files before authoring this pool).
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
# CATEGORY: bug_fixing -- 14 tasks, each a small buggy function to fix
# ============================================================================

_t("bf01", "bug_fixing",
   "The function below is supposed to find the two closest values in a "
   "SORTED list of numbers and return them as a tuple (a, b) with a <= b, "
   "sorted so a comes from an earlier index than b. It has a bug. Fix it "
   "and return the complete corrected function.\n\n"
   "def closest_pair(nums):\n"
   "    best_diff = float('inf')\n"
   "    best_pair = None\n"
   "    for i in range(len(nums)):\n"
   "        diff = nums[i + 1] - nums[i]\n"
   "        if diff < best_diff:\n"
   "            best_diff = diff\n"
   "            best_pair = (nums[i], nums[i + 1])\n"
   "    return best_pair",
   """
assert closest_pair([1, 3, 4, 8, 13]) == (3, 4)
assert closest_pair([1, 2]) == (1, 2)
assert closest_pair([5, 5, 9, 20]) == (5, 5)
assert closest_pair([1, 10, 11, 50, 51, 52]) in [(10, 11), (50, 51), (51, 52)]
print('ALL_TESTS_PASSED')
""",
   "def closest_pair(nums):\n"
   "    best_diff = float('inf')\n"
   "    best_pair = None\n"
   "    for i in range(len(nums) - 1):\n"
   "        diff = nums[i + 1] - nums[i]\n"
   "        if diff < best_diff:\n"
   "            best_diff = diff\n"
   "            best_pair = (nums[i], nums[i + 1])\n"
   "    return best_pair")

_t("bf02", "bug_fixing",
   "The function below should count the number of DISTINCT unordered pairs "
   "of indices (i, j) with i < j such that nums[i] + nums[j] == target. It "
   "has a bug that causes it to overcount or undercount in some cases. Fix "
   "it and return the complete corrected function.\n\n"
   "def count_pairs_sum_to_target(nums, target):\n"
   "    count = 0\n"
   "    for i in range(len(nums)):\n"
   "        for j in range(len(nums)):\n"
   "            if nums[i] + nums[j] == target:\n"
   "                count += 1\n"
   "    return count",
   """
assert count_pairs_sum_to_target([1, 2, 3, 4], 5) == 2
assert count_pairs_sum_to_target([1, 1, 1], 2) == 3
assert count_pairs_sum_to_target([5], 10) == 0
assert count_pairs_sum_to_target([], 0) == 0
assert count_pairs_sum_to_target([3, 3, 3, 3], 6) == 6
print('ALL_TESTS_PASSED')
""",
   "def count_pairs_sum_to_target(nums, target):\n"
   "    count = 0\n"
   "    for i in range(len(nums)):\n"
   "        for j in range(i + 1, len(nums)):\n"
   "            if nums[i] + nums[j] == target:\n"
   "                count += 1\n"
   "    return count")

_t("bf03", "bug_fixing",
   "The function below performs binary search to find the FIRST (leftmost) "
   "index at which `target` occurs in a sorted list `nums`, returning -1 if "
   "not present. It has an off-by-one bug. Fix it and return the complete "
   "corrected function.\n\n"
   "def first_occurrence(nums, target):\n"
   "    lo, hi = 0, len(nums) - 1\n"
   "    result = -1\n"
   "    while lo <= hi:\n"
   "        mid = (lo + hi) // 2\n"
   "        if nums[mid] == target:\n"
   "            result = mid\n"
   "            lo = mid + 1\n"
   "        elif nums[mid] < target:\n"
   "            lo = mid + 1\n"
   "        else:\n"
   "            hi = mid + 1\n"
   "    return result",
   """
assert first_occurrence([1, 2, 2, 2, 3, 4], 2) == 1
assert first_occurrence([1, 2, 3], 5) == -1
assert first_occurrence([], 1) == -1
assert first_occurrence([1, 1, 1, 1], 1) == 0
assert first_occurrence([1, 2, 3, 4, 5], 5) == 4
print('ALL_TESTS_PASSED')
""",
   "def first_occurrence(nums, target):\n"
   "    lo, hi = 0, len(nums) - 1\n"
   "    result = -1\n"
   "    while lo <= hi:\n"
   "        mid = (lo + hi) // 2\n"
   "        if nums[mid] == target:\n"
   "            result = mid\n"
   "            hi = mid - 1\n"
   "        elif nums[mid] < target:\n"
   "            lo = mid + 1\n"
   "        else:\n"
   "            hi = mid - 1\n"
   "    return result")

_t("bf04", "bug_fixing",
   "The function below checks whether a string of brackets ()[]{} is "
   "balanced and properly nested. It has a bug: it does not correctly "
   "reject mismatched bracket TYPES (e.g. '(]'), only mismatched counts. "
   "Fix it and return the complete corrected function.\n\n"
   "def is_balanced(s):\n"
   "    stack = []\n"
   "    pairs = {')': '(', ']': '[', '}': '{'}\n"
   "    for ch in s:\n"
   "        if ch in '([{':\n"
   "            stack.append(ch)\n"
   "        elif ch in ')]}':\n"
   "            if not stack:\n"
   "                return False\n"
   "            stack.pop()\n"
   "    return len(stack) == 0",
   """
assert is_balanced("()[]{}") == True
assert is_balanced("(]") == False
assert is_balanced("([)]") == False
assert is_balanced("{[]}") == True
assert is_balanced("") == True
assert is_balanced("(((") == False
print('ALL_TESTS_PASSED')
""",
   "def is_balanced(s):\n"
   "    stack = []\n"
   "    pairs = {')': '(', ']': '[', '}': '{'}\n"
   "    for ch in s:\n"
   "        if ch in '([{':\n"
   "            stack.append(ch)\n"
   "        elif ch in ')]}':\n"
   "            if not stack or stack.pop() != pairs[ch]:\n"
   "                return False\n"
   "    return len(stack) == 0")

_t("bf05", "bug_fixing",
   "The function below rotates a list to the right by k positions "
   "(elements that fall off the end wrap to the front). It has a bug when "
   "k is larger than the length of the list. Fix it and return the "
   "complete corrected function.\n\n"
   "def rotate_right(nums, k):\n"
   "    if not nums:\n"
   "        return nums\n"
   "    k = k % len(nums)\n"
   "    return nums[k:] + nums[:k]",
   """
assert rotate_right([1, 2, 3, 4, 5], 2) == [4, 5, 1, 2, 3]
assert rotate_right([1, 2, 3], 3) == [1, 2, 3]
assert rotate_right([1, 2, 3], 8) == [2, 3, 1]
assert rotate_right([], 5) == []
assert rotate_right([1], 100) == [1]
print('ALL_TESTS_PASSED')
""",
   "def rotate_right(nums, k):\n"
   "    if not nums:\n"
   "        return nums\n"
   "    k = k % len(nums)\n"
   "    return nums[-k:] + nums[:-k] if k else nums[:]")

_t("bf06", "bug_fixing",
   "The function below finds the single missing number in a list "
   "containing all integers from 0 to n except one. It has a bug in its "
   "formula. Fix it and return the complete corrected function.\n\n"
   "def find_missing(nums):\n"
   "    n = len(nums)\n"
   "    expected_sum = n * (n - 1) // 2\n"
   "    return expected_sum - sum(nums)",
   """
assert find_missing([3, 0, 1]) == 2
assert find_missing([0, 1]) == 2
assert find_missing([9, 6, 4, 2, 3, 5, 7, 0, 1]) == 8
assert find_missing([0]) == 1
print('ALL_TESTS_PASSED')
""",
   "def find_missing(nums):\n"
   "    n = len(nums)\n"
   "    expected_sum = n * (n + 1) // 2\n"
   "    return expected_sum - sum(nums)")

_t("bf07", "bug_fixing",
   "The function below (Kadane's algorithm) should return the maximum sum "
   "of any contiguous subarray of nums (nums may contain negative numbers, "
   "and is guaranteed non-empty). It has a bug that produces wrong answers "
   "when all numbers are negative. Fix it and return the complete "
   "corrected function.\n\n"
   "def max_subarray_sum(nums):\n"
   "    best = 0\n"
   "    current = 0\n"
   "    for n in nums:\n"
   "        current = max(n, current + n)\n"
   "        best = max(best, current)\n"
   "    return best",
   """
assert max_subarray_sum([-2, 1, -3, 4, -1, 2, 1, -5, 4]) == 6
assert max_subarray_sum([-5, -2, -8, -1]) == -1
assert max_subarray_sum([5]) == 5
assert max_subarray_sum([-1]) == -1
assert max_subarray_sum([1, 2, 3]) == 6
print('ALL_TESTS_PASSED')
""",
   "def max_subarray_sum(nums):\n"
   "    best = nums[0]\n"
   "    current = nums[0]\n"
   "    for n in nums[1:]:\n"
   "        current = max(n, current + n)\n"
   "        best = max(best, current)\n"
   "    return best")

_t("bf08", "bug_fixing",
   "The function below checks if two strings are anagrams of each other "
   "(same letters, same counts, case-insensitive, ignoring spaces). It has "
   "a bug: it is case-sensitive when it should not be. Fix it and return "
   "the complete corrected function.\n\n"
   "def is_anagram(a, b):\n"
   "    a_clean = a.replace(' ', '')\n"
   "    b_clean = b.replace(' ', '')\n"
   "    return sorted(a_clean) == sorted(b_clean)",
   """
assert is_anagram("Listen", "Silent") == True
assert is_anagram("Dormitory", "Dirty Room") == True
assert is_anagram("Hello", "World") == False
assert is_anagram("", "") == True
assert is_anagram("A B", "ba") == True
print('ALL_TESTS_PASSED')
""",
   "def is_anagram(a, b):\n"
   "    a_clean = a.replace(' ', '').lower()\n"
   "    b_clean = b.replace(' ', '').lower()\n"
   "    return sorted(a_clean) == sorted(b_clean)")

_t("bf09", "bug_fixing",
   "The function below reverses the order of words in a sentence, "
   "collapsing any repeated whitespace between words to a single space and "
   "stripping leading/trailing whitespace. It has a bug that leaves extra "
   "empty strings in the result when there is repeated whitespace. Fix it "
   "and return the complete corrected function.\n\n"
   "def reverse_words(s):\n"
   "    words = s.split(' ')\n"
   "    return ' '.join(reversed(words))",
   """
assert reverse_words("the sky is blue") == "blue is sky the"
assert reverse_words("  hello   world  ") == "world hello"
assert reverse_words("a") == "a"
assert reverse_words("") == ""
assert reverse_words("   ") == ""
print('ALL_TESTS_PASSED')
""",
   "def reverse_words(s):\n"
   "    words = s.split()\n"
   "    return ' '.join(reversed(words))")

_t("bf10", "bug_fixing",
   "The function below uses the two-pointer technique on a SORTED list to "
   "find a pair of indices (i, j) with i < j such that nums[i] + nums[j] == "
   "target, returning the pair of VALUES (not indices) or None if no pair "
   "exists. It has a bug in how the pointers move. Fix it and return the "
   "complete corrected function.\n\n"
   "def two_sum_sorted(nums, target):\n"
   "    lo, hi = 0, len(nums) - 1\n"
   "    while lo < hi:\n"
   "        s = nums[lo] + nums[hi]\n"
   "        if s == target:\n"
   "            return (nums[lo], nums[hi])\n"
   "        elif s < target:\n"
   "            hi -= 1\n"
   "        else:\n"
   "            lo += 1\n"
   "    return None",
   """
assert two_sum_sorted([1, 2, 3, 4, 6], 6) == (2, 4)
assert two_sum_sorted([1, 2, 3], 100) is None
assert two_sum_sorted([-3, -1, 0, 2, 5], 2) == (-3, 5)
assert two_sum_sorted([1, 1], 2) == (1, 1)
print('ALL_TESTS_PASSED')
""",
   "def two_sum_sorted(nums, target):\n"
   "    lo, hi = 0, len(nums) - 1\n"
   "    while lo < hi:\n"
   "        s = nums[lo] + nums[hi]\n"
   "        if s == target:\n"
   "            return (nums[lo], nums[hi])\n"
   "        elif s < target:\n"
   "            lo += 1\n"
   "        else:\n"
   "            hi -= 1\n"
   "    return None")

_t("bf11", "bug_fixing",
   "The function below checks whether a string is a palindrome, ignoring "
   "any characters that are not letters or digits, and ignoring case. It "
   "has a bug: it does not ignore non-alphanumeric characters. Fix it and "
   "return the complete corrected function.\n\n"
   "def is_palindrome_clean(s):\n"
   "    cleaned = s.lower()\n"
   "    return cleaned == cleaned[::-1]",
   """
assert is_palindrome_clean("A man, a plan, a canal: Panama") == True
assert is_palindrome_clean("race a car") == False
assert is_palindrome_clean("") == True
assert is_palindrome_clean("Was it a car or a cat I saw?") == True
assert is_palindrome_clean(".,!") == True
print('ALL_TESTS_PASSED')
""",
   "def is_palindrome_clean(s):\n"
   "    cleaned = ''.join(ch.lower() for ch in s if ch.isalnum())\n"
   "    return cleaned == cleaned[::-1]")

_t("bf12", "bug_fixing",
   "The function below counts the number of vowels (a, e, i, o, u) in a "
   "string. It has a bug: it misses uppercase vowels. Fix it and return "
   "the complete corrected function.\n\n"
   "def count_vowels(s):\n"
   "    count = 0\n"
   "    for ch in s:\n"
   "        if ch in 'aeiou':\n"
   "            count += 1\n"
   "    return count",
   """
assert count_vowels("Hello World") == 3
assert count_vowels("AEIOU") == 5
assert count_vowels("xyz") == 0
assert count_vowels("") == 0
assert count_vowels("PYTHON") == 1
print('ALL_TESTS_PASSED')
""",
   "def count_vowels(s):\n"
   "    count = 0\n"
   "    for ch in s.lower():\n"
   "        if ch in 'aeiou':\n"
   "            count += 1\n"
   "    return count")

_t("bf13", "bug_fixing",
   "The function below merges two already-sorted lists into one sorted "
   "list. It has a bug that drops the last element of whichever list still "
   "has leftover elements after the main loop. Fix it and return the "
   "complete corrected function.\n\n"
   "def merge_sorted(a, b):\n"
   "    result = []\n"
   "    i, j = 0, 0\n"
   "    while i < len(a) - 1 and j < len(b) - 1:\n"
   "        if a[i] <= b[j]:\n"
   "            result.append(a[i])\n"
   "            i += 1\n"
   "        else:\n"
   "            result.append(b[j])\n"
   "            j += 1\n"
   "    result.extend(a[i:])\n"
   "    result.extend(b[j:])\n"
   "    return result",
   """
assert merge_sorted([1, 3, 5], [2, 4, 6]) == [1, 2, 3, 4, 5, 6]
assert merge_sorted([], [1, 2]) == [1, 2]
assert merge_sorted([1, 2], []) == [1, 2]
assert merge_sorted([1, 1, 1], [1, 1]) == [1, 1, 1, 1, 1]
assert merge_sorted([5], [1]) == [1, 5]
print('ALL_TESTS_PASSED')
""",
   "def merge_sorted(a, b):\n"
   "    result = []\n"
   "    i, j = 0, 0\n"
   "    while i < len(a) and j < len(b):\n"
   "        if a[i] <= b[j]:\n"
   "            result.append(a[i])\n"
   "            i += 1\n"
   "        else:\n"
   "            result.append(b[j])\n"
   "            j += 1\n"
   "    result.extend(a[i:])\n"
   "    result.extend(b[j:])\n"
   "    return result")

_t("bf14", "bug_fixing",
   "The function below finds the first duplicate value in a list (the "
   "duplicate whose SECOND occurrence appears earliest), returning None if "
   "there are no duplicates. It has a bug that returns the wrong element "
   "in some cases because it does not preserve first-seen order. Fix it "
   "and return the complete corrected function.\n\n"
   "def first_duplicate(nums):\n"
   "    seen = set(nums)\n"
   "    for n in seen:\n"
   "        if nums.count(n) > 1:\n"
   "            return n\n"
   "    return None",
   """
assert first_duplicate([2, 1, 3, 5, 3, 2]) == 3
assert first_duplicate([1, 2, 3]) is None
assert first_duplicate([1, 1]) == 1
assert first_duplicate([]) is None
assert first_duplicate([5, 4, 3, 2, 1, 4]) == 4
print('ALL_TESTS_PASSED')
""",
   "def first_duplicate(nums):\n"
   "    seen = set()\n"
   "    for n in nums:\n"
   "        if n in seen:\n"
   "            return n\n"
   "        seen.add(n)\n"
   "    return None")

# ============================================================================
# CATEGORY: concurrency_stateful -- 14 tasks
# ============================================================================

_t("cs01", "concurrency_stateful",
   "Implement a thread-safe class `ThreadSafeCounter` with methods "
   "`increment()` (adds 1), `decrement()` (subtracts 1), `get()` (returns "
   "current value), and `reset()` (sets value back to 0). All methods must "
   "be safe to call from multiple threads concurrently (use "
   "`threading.Lock`). Initial value is 0.",
   """
c = ThreadSafeCounter()
c.increment(); c.increment(); c.increment()
assert c.get() == 3
c.decrement()
assert c.get() == 2
c.reset()
assert c.get() == 0
import threading
c2 = ThreadSafeCounter()
def worker():
    for _ in range(1000):
        c2.increment()
threads = [threading.Thread(target=worker) for _ in range(8)]
for t in threads: t.start()
for t in threads: t.join()
assert c2.get() == 8000
print('ALL_TESTS_PASSED')
""",
   "import threading\n"
   "class ThreadSafeCounter:\n"
   "    def __init__(self):\n"
   "        self._value = 0\n"
   "        self._lock = threading.Lock()\n"
   "    def increment(self):\n"
   "        with self._lock:\n"
   "            self._value += 1\n"
   "    def decrement(self):\n"
   "        with self._lock:\n"
   "            self._value -= 1\n"
   "    def get(self):\n"
   "        with self._lock:\n"
   "            return self._value\n"
   "    def reset(self):\n"
   "        with self._lock:\n"
   "            self._value = 0")

_t("cs02", "concurrency_stateful",
   "Implement a thread-safe class `ThreadSafeBoundedStack` constructed "
   "with `ThreadSafeBoundedStack(capacity)`. Method `push(item)` returns "
   "True and adds the item if under capacity, or returns False (does not "
   "add) if the stack is already at capacity. Method `pop()` removes and "
   "returns the top item, or returns None if empty. Method `size()` "
   "returns current count. Must be safe under concurrent use "
   "(use `threading.Lock`).",
   """
s = ThreadSafeBoundedStack(2)
assert s.push(1) == True
assert s.push(2) == True
assert s.push(3) == False
assert s.size() == 2
assert s.pop() == 2
assert s.pop() == 1
assert s.pop() is None
assert s.size() == 0
print('ALL_TESTS_PASSED')
""",
   "import threading\n"
   "class ThreadSafeBoundedStack:\n"
   "    def __init__(self, capacity):\n"
   "        self._capacity = capacity\n"
   "        self._items = []\n"
   "        self._lock = threading.Lock()\n"
   "    def push(self, item):\n"
   "        with self._lock:\n"
   "            if len(self._items) >= self._capacity:\n"
   "                return False\n"
   "            self._items.append(item)\n"
   "            return True\n"
   "    def pop(self):\n"
   "        with self._lock:\n"
   "            if not self._items:\n"
   "                return None\n"
   "            return self._items.pop()\n"
   "    def size(self):\n"
   "        with self._lock:\n"
   "            return len(self._items)")

_t("cs03", "concurrency_stateful",
   "Implement a thread-safe class `ThreadSafeUniqueIdGenerator` with method "
   "`next_id()` that returns a strictly increasing integer starting at 1 "
   "(1, 2, 3, ...), safe under concurrent calls from multiple threads with "
   "no duplicate or skipped IDs (use `threading.Lock`).",
   """
g = ThreadSafeUniqueIdGenerator()
assert g.next_id() == 1
assert g.next_id() == 2
assert g.next_id() == 3
import threading
g2 = ThreadSafeUniqueIdGenerator()
results = []
lock = threading.Lock()
def worker():
    for _ in range(500):
        val = g2.next_id()
        with lock:
            results.append(val)
threads = [threading.Thread(target=worker) for _ in range(6)]
for t in threads: t.start()
for t in threads: t.join()
assert len(results) == len(set(results)) == 3000
assert min(results) == 1 and max(results) == 3000
print('ALL_TESTS_PASSED')
""",
   "import threading\n"
   "class ThreadSafeUniqueIdGenerator:\n"
   "    def __init__(self):\n"
   "        self._next = 1\n"
   "        self._lock = threading.Lock()\n"
   "    def next_id(self):\n"
   "        with self._lock:\n"
   "            val = self._next\n"
   "            self._next += 1\n"
   "            return val")

_t("cs04", "concurrency_stateful",
   "Implement a class `RateLimiterSlidingWindow` constructed with "
   "`RateLimiterSlidingWindow(max_events, window_seconds, clock)` where "
   "`clock` is a zero-argument callable returning the current time (so "
   "tests can inject a fake clock). Method `allow()` returns True and "
   "records an event at the current clock time if fewer than `max_events` "
   "events occurred within the last `window_seconds` (relative to the "
   "current clock time), otherwise returns False without recording. Must "
   "be thread-safe (use `threading.Lock`).",
   """
t = [0.0]
def fake_clock():
    return t[0]
r = RateLimiterSlidingWindow(3, 10, fake_clock)
assert r.allow() == True
assert r.allow() == True
assert r.allow() == True
assert r.allow() == False
t[0] = 11.0
assert r.allow() == True
print('ALL_TESTS_PASSED')
""",
   "import threading\n"
   "class RateLimiterSlidingWindow:\n"
   "    def __init__(self, max_events, window_seconds, clock):\n"
   "        self._max = max_events\n"
   "        self._window = window_seconds\n"
   "        self._clock = clock\n"
   "        self._events = []\n"
   "        self._lock = threading.Lock()\n"
   "    def allow(self):\n"
   "        with self._lock:\n"
   "            now = self._clock()\n"
   "            self._events = [t for t in self._events if now - t < self._window]\n"
   "            if len(self._events) < self._max:\n"
   "                self._events.append(now)\n"
   "                return True\n"
   "            return False")

_t("cs05", "concurrency_stateful",
   "Implement a class `Debouncer` constructed with `Debouncer(min_interval, "
   "clock)` where `clock` is a zero-argument callable returning the "
   "current time. Method `should_fire()` returns True (and records the "
   "current time as the last-fired time) only if at least `min_interval` "
   "time has passed since the last time it returned True (or if it has "
   "never returned True before). Must be thread-safe.",
   """
t = [0.0]
def fake_clock():
    return t[0]
d = Debouncer(5.0, fake_clock)
assert d.should_fire() == True
assert d.should_fire() == False
t[0] = 3.0
assert d.should_fire() == False
t[0] = 5.0
assert d.should_fire() == True
t[0] = 5.5
assert d.should_fire() == False
print('ALL_TESTS_PASSED')
""",
   "import threading\n"
   "class Debouncer:\n"
   "    def __init__(self, min_interval, clock):\n"
   "        self._min_interval = min_interval\n"
   "        self._clock = clock\n"
   "        self._last_fired = None\n"
   "        self._lock = threading.Lock()\n"
   "    def should_fire(self):\n"
   "        with self._lock:\n"
   "            now = self._clock()\n"
   "            if self._last_fired is None or now - self._last_fired >= self._min_interval:\n"
   "                self._last_fired = now\n"
   "                return True\n"
   "            return False")

_t("cs06", "concurrency_stateful",
   "Implement a class `ThreadSafeCircuitBreaker` constructed with "
   "`ThreadSafeCircuitBreaker(failure_threshold, reset_timeout, clock)` "
   "where `clock` is a zero-argument callable returning current time. "
   "Method `record_failure()` increments a failure count; once the count "
   "reaches `failure_threshold`, the breaker opens. Method `record_success()` "
   "resets the failure count to 0 and closes the breaker. Method "
   "`is_open()` returns True if the breaker is open AND less than "
   "`reset_timeout` has passed since it opened; if `reset_timeout` has "
   "passed, `is_open()` returns False (the breaker resets itself to "
   "half-open/closed state, failure count back to 0). Must be thread-safe.",
   """
t = [0.0]
def fake_clock():
    return t[0]
b = ThreadSafeCircuitBreaker(3, 10.0, fake_clock)
assert b.is_open() == False
b.record_failure(); b.record_failure()
assert b.is_open() == False
b.record_failure()
assert b.is_open() == True
t[0] = 5.0
assert b.is_open() == True
t[0] = 11.0
assert b.is_open() == False
b.record_failure(); b.record_failure(); b.record_failure()
assert b.is_open() == True
b.record_success()
assert b.is_open() == False
print('ALL_TESTS_PASSED')
""",
   "import threading\n"
   "class ThreadSafeCircuitBreaker:\n"
   "    def __init__(self, failure_threshold, reset_timeout, clock):\n"
   "        self._threshold = failure_threshold\n"
   "        self._reset_timeout = reset_timeout\n"
   "        self._clock = clock\n"
   "        self._failures = 0\n"
   "        self._opened_at = None\n"
   "        self._lock = threading.Lock()\n"
   "    def record_failure(self):\n"
   "        with self._lock:\n"
   "            self._failures += 1\n"
   "            if self._failures >= self._threshold and self._opened_at is None:\n"
   "                self._opened_at = self._clock()\n"
   "    def record_success(self):\n"
   "        with self._lock:\n"
   "            self._failures = 0\n"
   "            self._opened_at = None\n"
   "    def is_open(self):\n"
   "        with self._lock:\n"
   "            if self._opened_at is None:\n"
   "                return False\n"
   "            if self._clock() - self._opened_at >= self._reset_timeout:\n"
   "                self._opened_at = None\n"
   "                self._failures = 0\n"
   "                return False\n"
   "            return True")

_t("cs07", "concurrency_stateful",
   "Implement a class `ThreadSafeMovingAverage` constructed with "
   "`ThreadSafeMovingAverage(window_size)`. Method `add(value)` records a "
   "new value, keeping only the most recent `window_size` values (oldest "
   "dropped once the window is full). Method `average()` returns the "
   "average of the currently-held values, or 0.0 if none have been added. "
   "Must be thread-safe.",
   """
m = ThreadSafeMovingAverage(3)
assert m.average() == 0.0
m.add(2.0); m.add(4.0)
assert m.average() == 3.0
m.add(9.0)
assert m.average() == 5.0
m.add(0.0)
avg = m.average()
assert abs(avg - (4.0+9.0+0.0)/3) < 1e-9
print('ALL_TESTS_PASSED')
""",
   "import threading\n"
   "from collections import deque\n"
   "class ThreadSafeMovingAverage:\n"
   "    def __init__(self, window_size):\n"
   "        self._window_size = window_size\n"
   "        self._values = deque(maxlen=window_size)\n"
   "        self._lock = threading.Lock()\n"
   "    def add(self, value):\n"
   "        with self._lock:\n"
   "            self._values.append(value)\n"
   "    def average(self):\n"
   "        with self._lock:\n"
   "            if not self._values:\n"
   "                return 0.0\n"
   "            return sum(self._values) / len(self._values)")

_t("cs08", "concurrency_stateful",
   "Implement a thread-safe class `ThreadSafeEventFlag` with methods "
   "`set()` (marks the flag as set), `clear()` (marks the flag as not "
   "set), and `is_set()` (returns current boolean state). Initial state is "
   "not set (False). Must be thread-safe.",
   """
f = ThreadSafeEventFlag()
assert f.is_set() == False
f.set()
assert f.is_set() == True
f.clear()
assert f.is_set() == False
f.set(); f.set()
assert f.is_set() == True
print('ALL_TESTS_PASSED')
""",
   "import threading\n"
   "class ThreadSafeEventFlag:\n"
   "    def __init__(self):\n"
   "        self._flag = False\n"
   "        self._lock = threading.Lock()\n"
   "    def set(self):\n"
   "        with self._lock:\n"
   "            self._flag = True\n"
   "    def clear(self):\n"
   "        with self._lock:\n"
   "            self._flag = False\n"
   "    def is_set(self):\n"
   "        with self._lock:\n"
   "            return self._flag")

_t("cs09", "concurrency_stateful",
   "Implement a thread-safe class `ThreadSafeMultiCounter` with method "
   "`increment(key)` (increments the counter for that key, starting from "
   "0 if new) and `get(key)` (returns the count for that key, 0 if never "
   "incremented). Must be thread-safe using a single shared lock.",
   """
m = ThreadSafeMultiCounter()
assert m.get('a') == 0
m.increment('a'); m.increment('a'); m.increment('b')
assert m.get('a') == 2
assert m.get('b') == 1
assert m.get('c') == 0
import threading
m2 = ThreadSafeMultiCounter()
def worker():
    for _ in range(1000):
        m2.increment('x')
threads = [threading.Thread(target=worker) for _ in range(6)]
for t in threads: t.start()
for t in threads: t.join()
assert m2.get('x') == 6000
print('ALL_TESTS_PASSED')
""",
   "import threading\n"
   "class ThreadSafeMultiCounter:\n"
   "    def __init__(self):\n"
   "        self._counts = {}\n"
   "        self._lock = threading.Lock()\n"
   "    def increment(self, key):\n"
   "        with self._lock:\n"
   "            self._counts[key] = self._counts.get(key, 0) + 1\n"
   "    def get(self, key):\n"
   "        with self._lock:\n"
   "            return self._counts.get(key, 0)")

_t("cs10", "concurrency_stateful",
   "Implement a class `ThreadSafeTTLCache` constructed with "
   "`ThreadSafeTTLCache(ttl_seconds, clock)` where `clock` is a "
   "zero-argument callable returning current time. Method `put(key, "
   "value)` stores a value with an expiry at current_time + ttl_seconds. "
   "Method `get(key)` returns the value if present and not yet expired, "
   "otherwise returns None (and if expired, removes the stale entry). Must "
   "be thread-safe.",
   """
t = [0.0]
def fake_clock():
    return t[0]
c = ThreadSafeTTLCache(10.0, fake_clock)
c.put('a', 1)
assert c.get('a') == 1
t[0] = 5.0
assert c.get('a') == 1
t[0] = 11.0
assert c.get('a') is None
assert c.get('missing') is None
print('ALL_TESTS_PASSED')
""",
   "import threading\n"
   "class ThreadSafeTTLCache:\n"
   "    def __init__(self, ttl_seconds, clock):\n"
   "        self._ttl = ttl_seconds\n"
   "        self._clock = clock\n"
   "        self._store = {}\n"
   "        self._lock = threading.Lock()\n"
   "    def put(self, key, value):\n"
   "        with self._lock:\n"
   "            self._store[key] = (value, self._clock() + self._ttl)\n"
   "    def get(self, key):\n"
   "        with self._lock:\n"
   "            if key not in self._store:\n"
   "                return None\n"
   "            value, expiry = self._store[key]\n"
   "            if self._clock() >= expiry:\n"
   "                del self._store[key]\n"
   "                return None\n"
   "            return value")

_t("cs11", "concurrency_stateful",
   "Implement a class `ThreadSafeBatchAccumulator` constructed with "
   "`ThreadSafeBatchAccumulator(batch_size)`. Method `add(item)` appends "
   "`item` to an internal pending list; if the pending list reaches "
   "`batch_size`, it immediately clears the pending list and returns the "
   "full batch as a list (in the order added); otherwise it returns None. "
   "Must be thread-safe.",
   """
a = ThreadSafeBatchAccumulator(3)
assert a.add(1) is None
assert a.add(2) is None
assert a.add(3) == [1, 2, 3]
assert a.add(4) is None
assert a.add(5) is None
assert a.add(6) == [4, 5, 6]
print('ALL_TESTS_PASSED')
""",
   "import threading\n"
   "class ThreadSafeBatchAccumulator:\n"
   "    def __init__(self, batch_size):\n"
   "        self._batch_size = batch_size\n"
   "        self._pending = []\n"
   "        self._lock = threading.Lock()\n"
   "    def add(self, item):\n"
   "        with self._lock:\n"
   "            self._pending.append(item)\n"
   "            if len(self._pending) >= self._batch_size:\n"
   "                batch = self._pending\n"
   "                self._pending = []\n"
   "                return batch\n"
   "            return None")

_t("cs12", "concurrency_stateful",
   "Implement a class `ThreadSafeRoundRobinSelector` constructed with "
   "`ThreadSafeRoundRobinSelector(items)` (a non-empty list). Method "
   "`next()` returns the next item, cycling back to the start after the "
   "last item. Must be thread-safe, and under concurrent calls each call "
   "must return exactly one item from the cycle with no item skipped or "
   "duplicated across the guaranteed total number of calls (i.e., after N "
   "calls with len(items)=k, each item has been returned exactly N/k times "
   "when N is a multiple of k).",
   """
s = ThreadSafeRoundRobinSelector(['a', 'b', 'c'])
assert [s.next() for _ in range(7)] == ['a', 'b', 'c', 'a', 'b', 'c', 'a']
import threading
from collections import Counter
s2 = ThreadSafeRoundRobinSelector(['x', 'y'])
results = []
lock = threading.Lock()
def worker():
    for _ in range(500):
        val = s2.next()
        with lock:
            results.append(val)
threads = [threading.Thread(target=worker) for _ in range(4)]
for t in threads: t.start()
for t in threads: t.join()
counts = Counter(results)
assert counts['x'] == counts['y'] == 1000
print('ALL_TESTS_PASSED')
""",
   "import threading\n"
   "class ThreadSafeRoundRobinSelector:\n"
   "    def __init__(self, items):\n"
   "        self._items = list(items)\n"
   "        self._index = 0\n"
   "        self._lock = threading.Lock()\n"
   "    def next(self):\n"
   "        with self._lock:\n"
   "            item = self._items[self._index % len(self._items)]\n"
   "            self._index += 1\n"
   "            return item")

_t("cs13", "concurrency_stateful",
   "Implement a class `ThreadSafeSemaphoreLite` constructed with "
   "`ThreadSafeSemaphoreLite(max_count)`. Method `acquire()` returns True "
   "and decrements the available count if any is available (available > "
   "0), otherwise returns False without changing state. Method "
   "`release()` increments the available count back up, never exceeding "
   "`max_count`. Method `available()` returns the current available count. "
   "Must be thread-safe.",
   """
s = ThreadSafeSemaphoreLite(2)
assert s.available() == 2
assert s.acquire() == True
assert s.acquire() == True
assert s.acquire() == False
assert s.available() == 0
s.release()
assert s.available() == 1
s.release(); s.release()
assert s.available() == 2
print('ALL_TESTS_PASSED')
""",
   "import threading\n"
   "class ThreadSafeSemaphoreLite:\n"
   "    def __init__(self, max_count):\n"
   "        self._max = max_count\n"
   "        self._available = max_count\n"
   "        self._lock = threading.Lock()\n"
   "    def acquire(self):\n"
   "        with self._lock:\n"
   "            if self._available > 0:\n"
   "                self._available -= 1\n"
   "                return True\n"
   "            return False\n"
   "    def release(self):\n"
   "        with self._lock:\n"
   "            self._available = min(self._max, self._available + 1)\n"
   "    def available(self):\n"
   "        with self._lock:\n"
   "            return self._available")

_t("cs14", "concurrency_stateful",
   "Implement a thread-safe class `ThreadSafeHistogram` with method "
   "`record(bucket_key)` (increments the count for that bucket) and "
   "`counts()` (returns a dict copy of all bucket->count values recorded "
   "so far, with buckets never recorded showing no entry at all -- i.e. "
   "only include buckets that have been recorded at least once). Must be "
   "thread-safe using a single shared lock.",
   """
h = ThreadSafeHistogram()
h.record('a'); h.record('a'); h.record('b')
c = h.counts()
assert c == {'a': 2, 'b': 1}
assert 'c' not in c
h.record('c')
c2 = h.counts()
assert c2 == {'a': 2, 'b': 1, 'c': 1}
print('ALL_TESTS_PASSED')
""",
   "import threading\n"
   "class ThreadSafeHistogram:\n"
   "    def __init__(self):\n"
   "        self._counts = {}\n"
   "        self._lock = threading.Lock()\n"
   "    def record(self, bucket_key):\n"
   "        with self._lock:\n"
   "            self._counts[bucket_key] = self._counts.get(bucket_key, 0) + 1\n"
   "    def counts(self):\n"
   "        with self._lock:\n"
   "            return dict(self._counts)")

# ============================================================================
# CATEGORY: algorithmic_edge_case -- 14 tasks
# ============================================================================

_t("ae01", "algorithmic_edge_case",
   "Write a function `flatten_nested_list(lst)` that flattens an "
   "arbitrarily-deeply-nested list of lists (and non-list elements) into a "
   "single flat list, preserving left-to-right order.",
   """
assert flatten_nested_list([1, [2, 3], [4, [5, 6]]]) == [1, 2, 3, 4, 5, 6]
assert flatten_nested_list([]) == []
assert flatten_nested_list([[[[1]]], 2]) == [1, 2]
assert flatten_nested_list([1, 2, 3]) == [1, 2, 3]
assert flatten_nested_list([[], [], [1]]) == [1]
print('ALL_TESTS_PASSED')
""",
   "def flatten_nested_list(lst):\n"
   "    result = []\n"
   "    for item in lst:\n"
   "        if isinstance(item, list):\n"
   "            result.extend(flatten_nested_list(item))\n"
   "        else:\n"
   "            result.append(item)\n"
   "    return result")

_t("ae02", "algorithmic_edge_case",
   "Write a function `group_anagrams(words)` that groups a list of words "
   "into lists of anagrams of each other (same letters, same counts, "
   "case-sensitive as given). Return a list of lists; the order of groups "
   "and order within groups should follow first-appearance order in the "
   "input.",
   """
result = group_anagrams(["eat", "tea", "tan", "ate", "nat", "bat"])
result_sets = [set(g) for g in result]
assert {"eat", "tea", "ate"} in result_sets
assert {"tan", "nat"} in result_sets
assert {"bat"} in result_sets
assert len(result) == 3
assert group_anagrams([]) == []
assert group_anagrams(["a"]) == [["a"]]
print('ALL_TESTS_PASSED')
""",
   "def group_anagrams(words):\n"
   "    groups = {}\n"
   "    order = []\n"
   "    for w in words:\n"
   "        key = ''.join(sorted(w))\n"
   "        if key not in groups:\n"
   "            groups[key] = []\n"
   "            order.append(key)\n"
   "        groups[key].append(w)\n"
   "    return [groups[k] for k in order]")

_t("ae03", "algorithmic_edge_case",
   "Write a function `sliding_window_max(nums, k)` that returns a list "
   "containing the maximum value in every contiguous window of size k as "
   "the window slides from left to right across nums. If k > len(nums), "
   "return an empty list.",
   """
assert sliding_window_max([1, 3, -1, -3, 5, 3, 6, 7], 3) == [3, 3, 5, 5, 6, 7]
assert sliding_window_max([1, 2, 3], 5) == []
assert sliding_window_max([4, 4, 4], 1) == [4, 4, 4]
assert sliding_window_max([9, 1, 2], 3) == [9]
assert sliding_window_max([], 1) == []
print('ALL_TESTS_PASSED')
""",
   "from collections import deque\n"
   "def sliding_window_max(nums, k):\n"
   "    if k > len(nums) or k <= 0:\n"
   "        return []\n"
   "    dq = deque()\n"
   "    result = []\n"
   "    for i, n in enumerate(nums):\n"
   "        while dq and nums[dq[-1]] <= n:\n"
   "            dq.pop()\n"
   "        dq.append(i)\n"
   "        if dq[0] <= i - k:\n"
   "            dq.popleft()\n"
   "        if i >= k - 1:\n"
   "            result.append(nums[dq[0]])\n"
   "    return result")

_t("ae04", "algorithmic_edge_case",
   "Write a function `longest_common_prefix(strs)` that returns the "
   "longest common prefix string among a list of strings, or an empty "
   "string if there is no common prefix or the list is empty.",
   """
assert longest_common_prefix(["flower", "flow", "flight"]) == "fl"
assert longest_common_prefix(["dog", "racecar", "car"]) == ""
assert longest_common_prefix([]) == ""
assert longest_common_prefix(["single"]) == "single"
assert longest_common_prefix(["", "abc"]) == ""
print('ALL_TESTS_PASSED')
""",
   "def longest_common_prefix(strs):\n"
   "    if not strs:\n"
   "        return ''\n"
   "    prefix = strs[0]\n"
   "    for s in strs[1:]:\n"
   "        while not s.startswith(prefix):\n"
   "            prefix = prefix[:-1]\n"
   "            if not prefix:\n"
   "                return ''\n"
   "    return prefix")

_t("ae05", "algorithmic_edge_case",
   "Write a function `is_subsequence(s, t)` that returns True if `s` is a "
   "subsequence of `t` (all characters of s appear in t in the same "
   "relative order, not necessarily contiguous), False otherwise. An "
   "empty s is always a subsequence.",
   """
assert is_subsequence("abc", "ahbgdc") == True
assert is_subsequence("axc", "ahbgdc") == False
assert is_subsequence("", "anything") == True
assert is_subsequence("abc", "") == False
assert is_subsequence("abc", "abc") == True
print('ALL_TESTS_PASSED')
""",
   "def is_subsequence(s, t):\n"
   "    it = iter(t)\n"
   "    return all(ch in it for ch in s)")

_t("ae06", "algorithmic_edge_case",
   "Write a function `matrix_transpose(matrix)` that returns the "
   "transpose of a 2D list (rows become columns). Assume the matrix is "
   "rectangular (all rows the same length); handle an empty matrix by "
   "returning an empty list.",
   """
assert matrix_transpose([[1, 2, 3], [4, 5, 6]]) == [[1, 4], [2, 5], [3, 6]]
assert matrix_transpose([]) == []
assert matrix_transpose([[1]]) == [[1]]
assert matrix_transpose([[1, 2]]) == [[1], [2]]
print('ALL_TESTS_PASSED')
""",
   "def matrix_transpose(matrix):\n"
   "    if not matrix:\n"
   "        return []\n"
   "    return [list(row) for row in zip(*matrix)]")

_t("ae07", "algorithmic_edge_case",
   "Write a function `spiral_order(matrix)` that returns all elements of "
   "a 2D rectangular list in spiral order (starting top-left, moving "
   "right, then down, then left, then up, spiraling inward).",
   """
assert spiral_order([[1,2,3],[4,5,6],[7,8,9]]) == [1,2,3,6,9,8,7,4,5]
assert spiral_order([[1,2],[3,4]]) == [1,2,4,3]
assert spiral_order([]) == []
assert spiral_order([[1,2,3,4]]) == [1,2,3,4]
assert spiral_order([[1],[2],[3]]) == [1,2,3]
print('ALL_TESTS_PASSED')
""",
   "def spiral_order(matrix):\n"
   "    if not matrix or not matrix[0]:\n"
   "        return []\n"
   "    result = []\n"
   "    top, bottom = 0, len(matrix) - 1\n"
   "    left, right = 0, len(matrix[0]) - 1\n"
   "    while top <= bottom and left <= right:\n"
   "        for c in range(left, right + 1):\n"
   "            result.append(matrix[top][c])\n"
   "        top += 1\n"
   "        for r in range(top, bottom + 1):\n"
   "            result.append(matrix[r][right])\n"
   "        right -= 1\n"
   "        if top <= bottom:\n"
   "            for c in range(right, left - 1, -1):\n"
   "                result.append(matrix[bottom][c])\n"
   "            bottom -= 1\n"
   "        if left <= right:\n"
   "            for r in range(bottom, top - 1, -1):\n"
   "                result.append(matrix[r][left])\n"
   "            left += 1\n"
   "    return result")

_t("ae08", "algorithmic_edge_case",
   "Write a function `zero_matrix(matrix)` that returns a NEW 2D list "
   "where, for every cell in the original matrix that is 0, the entire "
   "row and column containing that cell are set to 0 in the result "
   "(cells that were not in any zero row/column keep their original "
   "value). Do not mutate the input.",
   """
assert zero_matrix([[1,2,3],[4,0,6],[7,8,9]]) == [[1,0,3],[0,0,0],[7,0,9]]
assert zero_matrix([[1,2],[3,4]]) == [[1,2],[3,4]]
assert zero_matrix([[0]]) == [[0]]
assert zero_matrix([]) == []
print('ALL_TESTS_PASSED')
""",
   "def zero_matrix(matrix):\n"
   "    if not matrix:\n"
   "        return []\n"
   "    rows = len(matrix)\n"
   "    cols = len(matrix[0])\n"
   "    zero_rows = set()\n"
   "    zero_cols = set()\n"
   "    for r in range(rows):\n"
   "        for c in range(cols):\n"
   "            if matrix[r][c] == 0:\n"
   "                zero_rows.add(r)\n"
   "                zero_cols.add(c)\n"
   "    result = [row[:] for row in matrix]\n"
   "    for r in range(rows):\n"
   "        for c in range(cols):\n"
   "            if r in zero_rows or c in zero_cols:\n"
   "                result[r][c] = 0\n"
   "    return result")

_t("ae09", "algorithmic_edge_case",
   "Write a function `majority_element(nums)` that returns the element "
   "appearing more than n/2 times in a list of length n (guaranteed to "
   "exist for every test case). Use an O(n) time, O(1) extra space "
   "approach (Boyer-Moore voting) if possible, but any correct approach "
   "is acceptable.",
   """
assert majority_element([2,2,1,1,1,2,2]) == 2
assert majority_element([1]) == 1
assert majority_element([3,3,4]) == 3
assert majority_element([5,5,5,1,1]) == 5
print('ALL_TESTS_PASSED')
""",
   "def majority_element(nums):\n"
   "    count = 0\n"
   "    candidate = None\n"
   "    for n in nums:\n"
   "        if count == 0:\n"
   "            candidate = n\n"
   "        count += 1 if n == candidate else -1\n"
   "    return candidate")

_t("ae10", "algorithmic_edge_case",
   "Write a function `dutch_flag_sort(nums)` that returns a NEW list "
   "containing the same elements as `nums` (which only contains the "
   "integers 0, 1, and 2) sorted in ascending order. Do not use Python's "
   "built-in `sorted()` or `.sort()` -- implement the counting/partition "
   "logic yourself. Do not mutate the input list.",
   """
assert dutch_flag_sort([2,0,2,1,1,0]) == [0,0,1,1,2,2]
assert dutch_flag_sort([2,0,1]) == [0,1,2]
assert dutch_flag_sort([0]) == [0]
assert dutch_flag_sort([]) == []
assert dutch_flag_sort([1,1,1]) == [1,1,1]
print('ALL_TESTS_PASSED')
""",
   "def dutch_flag_sort(nums):\n"
   "    counts = [0, 0, 0]\n"
   "    for n in nums:\n"
   "        counts[n] += 1\n"
   "    return [0] * counts[0] + [1] * counts[1] + [2] * counts[2]")

_t("ae11", "algorithmic_edge_case",
   "Write a function `find_peak_element(nums)` that returns the index of "
   "ANY peak element (an element strictly greater than its neighbors; "
   "boundary elements only need to be greater than their one existing "
   "neighbor) in a list guaranteed to have at least one element and no "
   "two adjacent equal elements. Use an O(log n) binary-search approach.",
   """
nums1 = [1,2,3,1]
idx = find_peak_element(nums1)
assert nums1[idx] > (nums1[idx-1] if idx > 0 else float('-inf'))
assert nums1[idx] > (nums1[idx+1] if idx < len(nums1)-1 else float('-inf'))
idx2 = find_peak_element([1,2,1,3,5,6,4])
nums2 = [1,2,1,3,5,6,4]
assert nums2[idx2] > (nums2[idx2-1] if idx2 > 0 else float('-inf'))
assert nums2[idx2] > (nums2[idx2+1] if idx2 < len(nums2)-1 else float('-inf'))
assert find_peak_element([1]) == 0
assert find_peak_element([1,2]) == 1
assert find_peak_element([2,1]) == 0
print('ALL_TESTS_PASSED')
""",
   "def find_peak_element(nums):\n"
   "    lo, hi = 0, len(nums) - 1\n"
   "    while lo < hi:\n"
   "        mid = (lo + hi) // 2\n"
   "        if nums[mid] < nums[mid + 1]:\n"
   "            lo = mid + 1\n"
   "        else:\n"
   "            hi = mid\n"
   "    return lo")

_t("ae12", "algorithmic_edge_case",
   "Write a function `word_break_possible(s, word_dict)` that returns True "
   "if the string `s` can be segmented into a sequence of one or more "
   "words that all appear in `word_dict` (a list of allowed words, each "
   "may be reused any number of times), False otherwise.",
   """
assert word_break_possible("leetcode", ["leet", "code"]) == True
assert word_break_possible("applepenapple", ["apple", "pen"]) == True
assert word_break_possible("catsandog", ["cats", "dog", "sand", "and", "cat"]) == False
assert word_break_possible("", ["a"]) == True
assert word_break_possible("a", []) == False
print('ALL_TESTS_PASSED')
""",
   "def word_break_possible(s, word_dict):\n"
   "    words = set(word_dict)\n"
   "    n = len(s)\n"
   "    dp = [False] * (n + 1)\n"
   "    dp[0] = True\n"
   "    for i in range(1, n + 1):\n"
   "        for j in range(i):\n"
   "            if dp[j] and s[j:i] in words:\n"
   "                dp[i] = True\n"
   "                break\n"
   "    return dp[n]")

_t("ae13", "algorithmic_edge_case",
   "Write a function `min_window_length_ge_target(nums, target)` that "
   "returns the length of the smallest contiguous subarray of positive "
   "integers `nums` whose sum is greater than or equal to `target`, or 0 "
   "if no such subarray exists.",
   """
assert min_window_length_ge_target([2,3,1,2,4,3], 7) == 2
assert min_window_length_ge_target([1,1,1,1,1], 11) == 0
assert min_window_length_ge_target([1,4,4], 4) == 1
assert min_window_length_ge_target([], 5) == 0
print('ALL_TESTS_PASSED')
""",
   "def min_window_length_ge_target(nums, target):\n"
   "    n = len(nums)\n"
   "    left = 0\n"
   "    current = 0\n"
   "    best = float('inf')\n"
   "    for right in range(n):\n"
   "        current += nums[right]\n"
   "        while current >= target:\n"
   "            best = min(best, right - left + 1)\n"
   "            current -= nums[left]\n"
   "            left += 1\n"
   "    return best if best != float('inf') else 0")

_t("ae14", "algorithmic_edge_case",
   "Write a function `kth_largest(nums, k)` that returns the kth largest "
   "element in a list (k=1 means the largest, duplicates count "
   "separately, e.g. [3,3,2] with k=2 returns 3).",
   """
assert kth_largest([3,2,1,5,6,4], 2) == 5
assert kth_largest([3,2,3,1,2,4,5,5,6], 4) == 4
assert kth_largest([1], 1) == 1
assert kth_largest([3,3,2], 2) == 3
print('ALL_TESTS_PASSED')
""",
   "def kth_largest(nums, k):\n"
   "    return sorted(nums, reverse=True)[k - 1]")

# ============================================================================
# CATEGORY: refactoring -- 14 tasks
# ============================================================================

_t("rf01", "refactoring",
   "The function below computes Fibonacci numbers using naive, "
   "unmemoized recursion, which is far too slow for larger inputs. "
   "Refactor it (using memoization or an iterative approach) so that it "
   "produces IDENTICAL results but can compute fib(35) quickly. Return "
   "the complete refactored function, named exactly `fib`.\n\n"
   "def fib(n):\n"
   "    if n <= 1:\n"
   "        return n\n"
   "    return fib(n - 1) + fib(n - 2)",
   """
import time
assert fib(0) == 0
assert fib(1) == 1
assert fib(10) == 55
assert fib(20) == 6765
t0 = time.time()
result = fib(35)
elapsed = time.time() - t0
assert result == 9227465
assert elapsed < 3.0
print('ALL_TESTS_PASSED')
""",
   "def fib(n, _memo={}):\n"
   "    if n <= 1:\n"
   "        return n\n"
   "    if n in _memo:\n"
   "        return _memo[n]\n"
   "    result = fib(n - 1, _memo) + fib(n - 2, _memo)\n"
   "    _memo[n] = result\n"
   "    return result")

_t("rf02", "refactoring",
   "The function below counts the number of distinct paths from the "
   "top-left to the bottom-right of an m x n grid (only moving right or "
   "down at each step) using naive unmemoized recursion, which is too "
   "slow for larger grids. Refactor it (memoization or iterative DP) so "
   "it produces IDENTICAL results but can compute count_paths(20, 20) "
   "quickly. Return the complete refactored function, named exactly "
   "`count_paths`.\n\n"
   "def count_paths(m, n):\n"
   "    if m == 1 or n == 1:\n"
   "        return 1\n"
   "    return count_paths(m - 1, n) + count_paths(m, n - 1)",
   """
import time
assert count_paths(1, 1) == 1
assert count_paths(2, 2) == 2
assert count_paths(3, 3) == 6
t0 = time.time()
result = count_paths(20, 20)
elapsed = time.time() - t0
assert result == 35345263800
assert elapsed < 3.0
print('ALL_TESTS_PASSED')
""",
   "def count_paths(m, n, _memo=None):\n"
   "    if _memo is None:\n"
   "        _memo = {}\n"
   "    if m == 1 or n == 1:\n"
   "        return 1\n"
   "    if (m, n) in _memo:\n"
   "        return _memo[(m, n)]\n"
   "    result = count_paths(m - 1, n, _memo) + count_paths(m, n - 1, _memo)\n"
   "    _memo[(m, n)] = result\n"
   "    return result")

_t("rf03", "refactoring",
   "The function below counts how many numbers from 2 up to (and "
   "including) n are prime, using trial division for every number, which "
   "is too slow for large n. Refactor it (e.g. using a Sieve of "
   "Eratosthenes) so it produces IDENTICAL results but can handle "
   "n=200000 quickly. Return the complete refactored function, named "
   "exactly `count_primes_up_to`.\n\n"
   "def count_primes_up_to(n):\n"
   "    def is_prime(x):\n"
   "        if x < 2:\n"
   "            return False\n"
   "        for i in range(2, x):\n"
   "            if x % i == 0:\n"
   "                return False\n"
   "        return True\n"
   "    return sum(1 for i in range(2, n + 1) if is_prime(i))",
   """
import time
assert count_primes_up_to(1) == 0
assert count_primes_up_to(2) == 1
assert count_primes_up_to(10) == 4
assert count_primes_up_to(30) == 10
t0 = time.time()
result = count_primes_up_to(200000)
elapsed = time.time() - t0
assert result == 17984
assert elapsed < 5.0
print('ALL_TESTS_PASSED')
""",
   "def count_primes_up_to(n):\n"
   "    if n < 2:\n"
   "        return 0\n"
   "    sieve = [True] * (n + 1)\n"
   "    sieve[0] = sieve[1] = False\n"
   "    for i in range(2, int(n ** 0.5) + 1):\n"
   "        if sieve[i]:\n"
   "            for j in range(i * i, n + 1, i):\n"
   "                sieve[j] = False\n"
   "    return sum(sieve)")

_t("rf04", "refactoring",
   "The function below classifies a triangle given three side lengths "
   "using a deeply nested if/elif chain that is hard to read. Refactor it "
   "using clearer guard-clause / early-return structure so it produces "
   "IDENTICAL results (return 'invalid' if the sides cannot form a "
   "triangle, 'equilateral' if all sides equal, 'isosceles' if exactly "
   "two sides equal, otherwise 'scalene'). Return the complete refactored "
   "function, named exactly `classify_triangle`.\n\n"
   "def classify_triangle(a, b, c):\n"
   "    if a <= 0 or b <= 0 or c <= 0:\n"
   "        return 'invalid'\n"
   "    else:\n"
   "        if a + b <= c or a + c <= b or b + c <= a:\n"
   "            return 'invalid'\n"
   "        else:\n"
   "            if a == b:\n"
   "                if b == c:\n"
   "                    return 'equilateral'\n"
   "                else:\n"
   "                    return 'isosceles'\n"
   "            else:\n"
   "                if b == c or a == c:\n"
   "                    return 'isosceles'\n"
   "                else:\n"
   "                    return 'scalene'",
   """
assert classify_triangle(3, 3, 3) == 'equilateral'
assert classify_triangle(3, 3, 4) == 'isosceles'
assert classify_triangle(4, 3, 3) == 'isosceles'
assert classify_triangle(3, 4, 3) == 'isosceles'
assert classify_triangle(3, 4, 5) == 'scalene'
assert classify_triangle(0, 4, 5) == 'invalid'
assert classify_triangle(1, 1, 3) == 'invalid'
print('ALL_TESTS_PASSED')
""",
   "def classify_triangle(a, b, c):\n"
   "    if a <= 0 or b <= 0 or c <= 0:\n"
   "        return 'invalid'\n"
   "    if a + b <= c or a + c <= b or b + c <= a:\n"
   "        return 'invalid'\n"
   "    if a == b == c:\n"
   "        return 'equilateral'\n"
   "    if a == b or b == c or a == c:\n"
   "        return 'isosceles'\n"
   "    return 'scalene'")

_t("rf05", "refactoring",
   "The function below checks whether a list contains any duplicate "
   "values using a nested-loop O(n^2) approach, which is too slow for "
   "large lists. Refactor it (using a set) so it produces IDENTICAL "
   "results but can handle a list of 200000 elements quickly. Return the "
   "complete refactored function, named exactly `has_duplicate`.\n\n"
   "def has_duplicate(nums):\n"
   "    for i in range(len(nums)):\n"
   "        for j in range(len(nums)):\n"
   "            if i != j and nums[i] == nums[j]:\n"
   "                return True\n"
   "    return False",
   """
import time
assert has_duplicate([1, 2, 3]) == False
assert has_duplicate([1, 2, 2]) == True
assert has_duplicate([]) == False
big = list(range(200000))
t0 = time.time()
result = has_duplicate(big)
elapsed = time.time() - t0
assert result == False
assert elapsed < 5.0
big2 = list(range(200000))
big2[100] = big2[200]
t0 = time.time()
result2 = has_duplicate(big2)
elapsed2 = time.time() - t0
assert result2 == True
assert elapsed2 < 5.0
print('ALL_TESTS_PASSED')
""",
   "def has_duplicate(nums):\n"
   "    seen = set()\n"
   "    for n in nums:\n"
   "        if n in seen:\n"
   "            return True\n"
   "        seen.add(n)\n"
   "    return False")

_t("rf06", "refactoring",
   "The function below converts a day number (1-7) to its name using a "
   "long if/elif chain. Refactor it to use a lookup table/list instead, "
   "producing IDENTICAL results including returning 'invalid' for any "
   "day number outside 1-7. Return the complete refactored function, "
   "named exactly `day_name`.\n\n"
   "def day_name(day_num):\n"
   "    if day_num == 1:\n"
   "        return 'Monday'\n"
   "    elif day_num == 2:\n"
   "        return 'Tuesday'\n"
   "    elif day_num == 3:\n"
   "        return 'Wednesday'\n"
   "    elif day_num == 4:\n"
   "        return 'Thursday'\n"
   "    elif day_num == 5:\n"
   "        return 'Friday'\n"
   "    elif day_num == 6:\n"
   "        return 'Saturday'\n"
   "    elif day_num == 7:\n"
   "        return 'Sunday'\n"
   "    else:\n"
   "        return 'invalid'",
   """
assert day_name(1) == 'Monday'
assert day_name(7) == 'Sunday'
assert day_name(4) == 'Thursday'
assert day_name(0) == 'invalid'
assert day_name(8) == 'invalid'
assert day_name(-1) == 'invalid'
print('ALL_TESTS_PASSED')
""",
   "_DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']\n"
   "def day_name(day_num):\n"
   "    if 1 <= day_num <= 7:\n"
   "        return _DAYS[day_num - 1]\n"
   "    return 'invalid'")

_t("rf07", "refactoring",
   "The function below computes, for a LIST of non-negative integers, "
   "the number of set (1) bits in each one's binary representation, by "
   "recomputing from scratch for every number with no caching -- when "
   "the same number appears many times in the input this is wasteful. "
   "Refactor it to cache results across repeated numbers within a single "
   "call so it produces IDENTICAL results but completes quickly even when "
   "a large list has many repeated large numbers. Return the complete "
   "refactored function, named exactly `count_set_bits_list`.\n\n"
   "def count_set_bits_list(nums):\n"
   "    def count_bits(x):\n"
   "        count = 0\n"
   "        while x:\n"
   "            count += x & 1\n"
   "            x >>= 1\n"
   "        return count\n"
   "    return [count_bits(n) for n in nums]",
   """
import time
assert count_set_bits_list([0, 1, 2, 3, 255]) == [0, 1, 1, 2, 8]
assert count_set_bits_list([]) == []
big = [123456789] * 300000
t0 = time.time()
result = count_set_bits_list(big)
elapsed = time.time() - t0
assert result == [bin(123456789).count('1')] * 300000
assert elapsed < 5.0
print('ALL_TESTS_PASSED')
""",
   "def count_set_bits_list(nums):\n"
   "    cache = {}\n"
   "    def count_bits(x):\n"
   "        if x in cache:\n"
   "            return cache[x]\n"
   "        count = 0\n"
   "        y = x\n"
   "        while y:\n"
   "            count += y & 1\n"
   "            y >>= 1\n"
   "        cache[x] = count\n"
   "        return count\n"
   "    return [count_bits(n) for n in nums]")

_t("rf08", "refactoring",
   "The function below reverses each word in a sentence (but keeps word "
   "order the same) by manually building the reversed word character by "
   "character with string concatenation in a loop, which is unidiomatic "
   "and slow for long words. Refactor it to use idiomatic slicing/join "
   "so it produces IDENTICAL results. Return the complete refactored "
   "function, named exactly `reverse_each_word`.\n\n"
   "def reverse_each_word(s):\n"
   "    words = s.split(' ')\n"
   "    result_words = []\n"
   "    for w in words:\n"
   "        reversed_w = ''\n"
   "        for ch in w:\n"
   "            reversed_w = ch + reversed_w\n"
   "        result_words.append(reversed_w)\n"
   "    return ' '.join(result_words)",
   """
assert reverse_each_word("hello world") == "olleh dlrow"
assert reverse_each_word("a") == "a"
assert reverse_each_word("") == ""
assert reverse_each_word("ab cd ef") == "ba dc fe"
print('ALL_TESTS_PASSED')
""",
   "def reverse_each_word(s):\n"
   "    return ' '.join(w[::-1] for w in s.split(' '))")

_t("rf09", "refactoring",
   "The function below computes `(base ** exp) % mod` using naive "
   "repeated multiplication in a loop (O(exp) time), which is too slow "
   "for large exponents. Refactor it to use fast (binary) exponentiation "
   "(O(log exp) time) so it produces IDENTICAL results but can handle "
   "exp=1000000 quickly. Return the complete refactored function, named "
   "exactly `mod_pow`.\n\n"
   "def mod_pow(base, exp, mod):\n"
   "    result = 1\n"
   "    for _ in range(exp):\n"
   "        result = (result * base) % mod\n"
   "    return result",
   """
import time
assert mod_pow(2, 10, 1000) == 24
assert mod_pow(3, 0, 100) == 1
assert mod_pow(5, 3, 13) == 8
t0 = time.time()
result = mod_pow(7, 1000000, 1000000007)
elapsed = time.time() - t0
assert result == pow(7, 1000000, 1000000007)
assert elapsed < 3.0
print('ALL_TESTS_PASSED')
""",
   "def mod_pow(base, exp, mod):\n"
   "    result = 1\n"
   "    base = base % mod\n"
   "    while exp > 0:\n"
   "        if exp % 2 == 1:\n"
   "            result = (result * base) % mod\n"
   "        exp //= 2\n"
   "        base = (base * base) % mod\n"
   "    return result")

_t("rf10", "refactoring",
   "The function below describes the type of a value using an isinstance "
   "if/elif chain. Refactor it to use a dispatch dictionary keyed by type "
   "instead, producing IDENTICAL results (return 'int' for int, 'float' "
   "for float, 'str' for str, 'bool' for bool, 'other' for anything else "
   "-- note bool must be checked before int since bool is a subclass of "
   "int in Python). Return the complete refactored function, named "
   "exactly `describe_type`.\n\n"
   "def describe_type(x):\n"
   "    if isinstance(x, bool):\n"
   "        return 'bool'\n"
   "    elif isinstance(x, int):\n"
   "        return 'int'\n"
   "    elif isinstance(x, float):\n"
   "        return 'float'\n"
   "    elif isinstance(x, str):\n"
   "        return 'str'\n"
   "    else:\n"
   "        return 'other'",
   """
assert describe_type(True) == 'bool'
assert describe_type(5) == 'int'
assert describe_type(5.0) == 'float'
assert describe_type("hi") == 'str'
assert describe_type([1, 2]) == 'other'
assert describe_type(None) == 'other'
print('ALL_TESTS_PASSED')
""",
   "_TYPE_DISPATCH = {bool: 'bool', int: 'int', float: 'float', str: 'str'}\n"
   "def describe_type(x):\n"
   "    return _TYPE_DISPATCH.get(type(x), 'other')")

_t("rf11", "refactoring",
   "The function below counts the number of distinct characters in a "
   "string using a nested-loop O(n^2) comparison approach, which is too "
   "slow for long strings. Refactor it (using a set) so it produces "
   "IDENTICAL results but can handle a string of 500000 characters "
   "quickly. Return the complete refactored function, named exactly "
   "`count_unique_chars`.\n\n"
   "def count_unique_chars(s):\n"
   "    unique = []\n"
   "    for i, ch in enumerate(s):\n"
   "        is_dup = False\n"
   "        for j in range(i):\n"
   "            if s[j] == ch:\n"
   "                is_dup = True\n"
   "                break\n"
   "        if not is_dup:\n"
   "            unique.append(ch)\n"
   "    return len(unique)",
   """
import time
assert count_unique_chars("hello") == 4
assert count_unique_chars("") == 0
assert count_unique_chars("aaa") == 1
big = "ab" * 250000
t0 = time.time()
result = count_unique_chars(big)
elapsed = time.time() - t0
assert result == 2
assert elapsed < 5.0
print('ALL_TESTS_PASSED')
""",
   "def count_unique_chars(s):\n"
   "    return len(set(s))")

_t("rf12", "refactoring",
   "The function below computes the digit sum of every number in a list "
   "by converting each digit's substring back to int for every position "
   "in a slow, repeated way. Refactor it to a cleaner, more efficient "
   "loop using arithmetic (mod/divide) instead of string conversion per "
   "digit, producing IDENTICAL results. Return the complete refactored "
   "function, named exactly `digit_sums`.\n\n"
   "def digit_sums(nums):\n"
   "    result = []\n"
   "    for n in nums:\n"
   "        s = str(abs(n))\n"
   "        total = 0\n"
   "        for i in range(len(s)):\n"
   "            total += int(s[i:i+1])\n"
   "        result.append(total)\n"
   "    return result",
   """
assert digit_sums([123, 0, 999, -45]) == [6, 0, 27, 9]
assert digit_sums([]) == []
assert digit_sums([7]) == [7]
print('ALL_TESTS_PASSED')
""",
   "def digit_sums(nums):\n"
   "    result = []\n"
   "    for n in nums:\n"
   "        x = abs(n)\n"
   "        total = 0\n"
   "        while x > 0:\n"
   "            total += x % 10\n"
   "            x //= 10\n"
   "        result.append(total)\n"
   "    return result")

_t("rf13", "refactoring",
   "The function below assigns a letter grade from a numeric score using "
   "a deeply nested if/elif chain. Refactor it to use a clean "
   "threshold-table/bisect-style lookup instead, producing IDENTICAL "
   "results (90+ -> 'A', 80-89 -> 'B', 70-79 -> 'C', 60-69 -> 'D', below "
   "60 -> 'F'). Return the complete refactored function, named exactly "
   "`grade_from_score`.\n\n"
   "def grade_from_score(score):\n"
   "    if score >= 90:\n"
   "        return 'A'\n"
   "    else:\n"
   "        if score >= 80:\n"
   "            return 'B'\n"
   "        else:\n"
   "            if score >= 70:\n"
   "                return 'C'\n"
   "            else:\n"
   "                if score >= 60:\n"
   "                    return 'D'\n"
   "                else:\n"
   "                    return 'F'",
   """
assert grade_from_score(95) == 'A'
assert grade_from_score(90) == 'A'
assert grade_from_score(89) == 'B'
assert grade_from_score(70) == 'C'
assert grade_from_score(60) == 'D'
assert grade_from_score(59) == 'F'
assert grade_from_score(0) == 'F'
print('ALL_TESTS_PASSED')
""",
   "import bisect\n"
   "def grade_from_score(score):\n"
   "    thresholds = [60, 70, 80, 90]\n"
   "    grades = ['F', 'D', 'C', 'B', 'A']\n"
   "    idx = bisect.bisect_right(thresholds, score)\n"
   "    return grades[idx]")

_t("rf14", "refactoring",
   "The function below computes the running average after each element "
   "of a list by recomputing the sum of ALL prior elements from scratch "
   "at every step (O(n^2) total). Refactor it to maintain a running sum "
   "incrementally (O(n) total) so it produces IDENTICAL results but can "
   "handle a list of 300000 elements quickly. Return the complete "
   "refactored function, named exactly `running_averages`.\n\n"
   "def running_averages(nums):\n"
   "    result = []\n"
   "    for i in range(len(nums)):\n"
   "        total = 0\n"
   "        for j in range(i + 1):\n"
   "            total += nums[j]\n"
   "        result.append(total / (i + 1))\n"
   "    return result",
   """
import time
r = running_averages([2, 4, 6])
assert abs(r[0] - 2.0) < 1e-9
assert abs(r[1] - 3.0) < 1e-9
assert abs(r[2] - 4.0) < 1e-9
assert running_averages([]) == []
big = list(range(1, 300001))
t0 = time.time()
result = running_averages(big)
elapsed = time.time() - t0
assert abs(result[-1] - (sum(big) / len(big))) < 1e-6
assert elapsed < 5.0
print('ALL_TESTS_PASSED')
""",
   "def running_averages(nums):\n"
   "    result = []\n"
   "    total = 0\n"
   "    for i, n in enumerate(nums):\n"
   "        total += n\n"
   "        result.append(total / (i + 1))\n"
   "    return result")

# ============================================================================
# CATEGORY: input_validation_defensive -- 14 tasks
# ============================================================================

_t("iv01", "input_validation_defensive",
   "Write a function `parse_int_safe(s)` that returns the integer value "
   "of string `s` if it represents a valid integer (optionally with "
   "leading whitespace, and an optional leading + or - sign, digits "
   "only), or None if it does not (e.g. empty string, contains letters, "
   "contains a decimal point, or is None).",
   """
assert parse_int_safe("42") == 42
assert parse_int_safe("  -17") == -17
assert parse_int_safe("+5") == 5
assert parse_int_safe("abc") is None
assert parse_int_safe("3.14") is None
assert parse_int_safe("") is None
assert parse_int_safe(None) is None
print('ALL_TESTS_PASSED')
""",
   "def parse_int_safe(s):\n"
   "    if not isinstance(s, str):\n"
   "        return None\n"
   "    s = s.strip()\n"
   "    if not s:\n"
   "        return None\n"
   "    try:\n"
   "        if s[0] in '+-':\n"
   "            if not s[1:].isdigit() or len(s) == 1:\n"
   "                return None\n"
   "        elif not s.isdigit():\n"
   "            return None\n"
   "        return int(s)\n"
   "    except (ValueError, IndexError):\n"
   "        return None")

_t("iv02", "input_validation_defensive",
   "Write a function `validate_email_basic(s)` that returns True if `s` "
   "satisfies this exact simplified rule: contains exactly one '@' "
   "character, has at least one non-empty character before the '@', and "
   "the part after the '@' contains at least one '.' with at least one "
   "character before and after that '.', and `s` contains no whitespace "
   "anywhere. Returns False otherwise.",
   """
assert validate_email_basic("a@b.com") == True
assert validate_email_basic("user.name@example.co.uk") == True
assert validate_email_basic("no-at-sign.com") == False
assert validate_email_basic("two@@signs.com") == False
assert validate_email_basic("@nodomain.com") == False
assert validate_email_basic("a@nodot") == False
assert validate_email_basic("a b@c.com") == False
assert validate_email_basic("a@.com") == False
print('ALL_TESTS_PASSED')
""",
   "def validate_email_basic(s):\n"
   "    if any(ch.isspace() for ch in s):\n"
   "        return False\n"
   "    if s.count('@') != 1:\n"
   "        return False\n"
   "    local, domain = s.split('@')\n"
   "    if not local or '.' not in domain:\n"
   "        return False\n"
   "    dot_idx = domain.find('.')\n"
   "    if dot_idx == 0 or dot_idx == len(domain) - 1:\n"
   "        return False\n"
   "    return True")

_t("iv03", "input_validation_defensive",
   "Write a function `clamp_to_range(value, lo, hi)` that returns `value` "
   "clamped between `lo` and `hi` (inclusive). If `lo > hi`, treat them as "
   "swapped (i.e. use min(lo,hi) and max(lo,hi) as the effective bounds). "
   "If `value` is not an int or float, raise a `TypeError`.",
   """
assert clamp_to_range(5, 1, 10) == 5
assert clamp_to_range(-5, 1, 10) == 1
assert clamp_to_range(15, 1, 10) == 10
assert clamp_to_range(5, 10, 1) == 5
assert clamp_to_range(0, 10, 1) == 1
try:
    clamp_to_range("x", 1, 10)
    assert False
except TypeError:
    pass
print('ALL_TESTS_PASSED')
""",
   "def clamp_to_range(value, lo, hi):\n"
   "    if not isinstance(value, (int, float)) or isinstance(value, bool):\n"
   "        raise TypeError('value must be int or float')\n"
   "    real_lo, real_hi = min(lo, hi), max(lo, hi)\n"
   "    return max(real_lo, min(real_hi, value))")

_t("iv04", "input_validation_defensive",
   "Write a function `safe_divide(a, b)` that returns `a / b` as a float "
   "if `b` is not zero, or None if `b` is zero. If either `a` or `b` is "
   "not an int or float, raise a `TypeError`.",
   """
assert safe_divide(10, 2) == 5.0
assert safe_divide(5, 0) is None
assert safe_divide(-9, 3) == -3.0
try:
    safe_divide("a", 1)
    assert False
except TypeError:
    pass
try:
    safe_divide(1, "b")
    assert False
except TypeError:
    pass
print('ALL_TESTS_PASSED')
""",
   "def safe_divide(a, b):\n"
   "    if not isinstance(a, (int, float)) or isinstance(a, bool):\n"
   "        raise TypeError('a must be numeric')\n"
   "    if not isinstance(b, (int, float)) or isinstance(b, bool):\n"
   "        raise TypeError('b must be numeric')\n"
   "    if b == 0:\n"
   "        return None\n"
   "    return a / b")

_t("iv05", "input_validation_defensive",
   "Write a function `normalize_whitespace(s)` that collapses any run of "
   "whitespace characters (spaces, tabs, newlines) into a single space, "
   "and strips leading/trailing whitespace from the result.",
   """
assert normalize_whitespace("  hello   world  ") == "hello world"
assert normalize_whitespace("a\\t\\tb\\nc") == "a b c"
assert normalize_whitespace("") == ""
assert normalize_whitespace("nochange") == "nochange"
assert normalize_whitespace("   ") == ""
print('ALL_TESTS_PASSED')
""",
   "import re\n"
   "def normalize_whitespace(s):\n"
   "    return re.sub(r'\\s+', ' ', s).strip()")

_t("iv06", "input_validation_defensive",
   "Write a function `validate_password_strength(s)` that returns True "
   "only if `s` satisfies ALL of: length at least 8, contains at least "
   "one uppercase letter, contains at least one lowercase letter, and "
   "contains at least one digit. Returns False otherwise.",
   """
assert validate_password_strength("Abcdefg1") == True
assert validate_password_strength("short1A") == False
assert validate_password_strength("alllowercase1") == False
assert validate_password_strength("ALLUPPERCASE1") == False
assert validate_password_strength("NoDigitsHere") == False
assert validate_password_strength("") == False
print('ALL_TESTS_PASSED')
""",
   "def validate_password_strength(s):\n"
   "    if len(s) < 8:\n"
   "        return False\n"
   "    has_upper = any(ch.isupper() for ch in s)\n"
   "    has_lower = any(ch.islower() for ch in s)\n"
   "    has_digit = any(ch.isdigit() for ch in s)\n"
   "    return has_upper and has_lower and has_digit")

_t("iv07", "input_validation_defensive",
   "Write a function `parse_csv_line_simple(line)` that parses a single "
   "CSV line into a list of field strings, handling the case where a "
   "field is wrapped in double quotes and may contain commas inside the "
   "quotes (no escaped-quote handling needed -- quotes only ever appear "
   "as the wrapping character for a whole field). Quoted fields should "
   "have their surrounding quotes stripped in the output.",
   """
assert parse_csv_line_simple('a,b,c') == ['a', 'b', 'c']
assert parse_csv_line_simple('"hello, world",b,c') == ['hello, world', 'b', 'c']
assert parse_csv_line_simple('a,"x,y,z",c') == ['a', 'x,y,z', 'c']
assert parse_csv_line_simple('') == ['']
assert parse_csv_line_simple('single') == ['single']
print('ALL_TESTS_PASSED')
""",
   "def parse_csv_line_simple(line):\n"
   "    fields = []\n"
   "    i = 0\n"
   "    n = len(line)\n"
   "    while i <= n:\n"
   "        if i < n and line[i] == '\"':\n"
   "            end = line.index('\"', i + 1)\n"
   "            fields.append(line[i + 1:end])\n"
   "            i = end + 2\n"
   "        else:\n"
   "            next_comma = line.find(',', i)\n"
   "            if next_comma == -1:\n"
   "                fields.append(line[i:])\n"
   "                i = n + 1\n"
   "            else:\n"
   "                fields.append(line[i:next_comma])\n"
   "                i = next_comma + 1\n"
   "    return fields")

_t("iv08", "input_validation_defensive",
   "Write a function `safe_list_get(lst, index, default=None)` that "
   "returns `lst[index]` if the index is valid (Python-style negative "
   "indexing allowed), or `default` if the index is out of range for the "
   "list.",
   """
assert safe_list_get([1, 2, 3], 1) == 2
assert safe_list_get([1, 2, 3], -1) == 3
assert safe_list_get([1, 2, 3], 10) is None
assert safe_list_get([1, 2, 3], 10, "missing") == "missing"
assert safe_list_get([], 0) is None
print('ALL_TESTS_PASSED')
""",
   "def safe_list_get(lst, index, default=None):\n"
   "    try:\n"
   "        return lst[index]\n"
   "    except IndexError:\n"
   "        return default")

_t("iv09", "input_validation_defensive",
   "Write a function `merge_dicts_safe(d1, d2)` that returns a new dict "
   "that is the merge of `d1` and `d2`, with `d2`'s values winning any "
   "key conflicts. If either argument is not a dict, raise a "
   "`TypeError`. Do not mutate the inputs.",
   """
assert merge_dicts_safe({"a": 1}, {"b": 2}) == {"a": 1, "b": 2}
assert merge_dicts_safe({"a": 1}, {"a": 2}) == {"a": 2}
d1 = {"a": 1}
merge_dicts_safe(d1, {"b": 2})
assert d1 == {"a": 1}
try:
    merge_dicts_safe([1], {"a": 1})
    assert False
except TypeError:
    pass
print('ALL_TESTS_PASSED')
""",
   "def merge_dicts_safe(d1, d2):\n"
   "    if not isinstance(d1, dict) or not isinstance(d2, dict):\n"
   "        raise TypeError('both arguments must be dicts')\n"
   "    result = dict(d1)\n"
   "    result.update(d2)\n"
   "    return result")

_t("iv10", "input_validation_defensive",
   "Write a function `validate_ip_v4_basic(s)` that returns True only if "
   "`s` consists of exactly 4 parts separated by '.', each part is a "
   "string of only digits (no signs), each part parses to an integer "
   "between 0 and 255 inclusive, and no part is empty.",
   """
assert validate_ip_v4_basic("192.168.1.1") == True
assert validate_ip_v4_basic("255.255.255.255") == True
assert validate_ip_v4_basic("0.0.0.0") == True
assert validate_ip_v4_basic("256.1.1.1") == False
assert validate_ip_v4_basic("1.2.3") == False
assert validate_ip_v4_basic("1.2.3.4.5") == False
assert validate_ip_v4_basic("1.2.3.") == False
assert validate_ip_v4_basic("a.b.c.d") == False
print('ALL_TESTS_PASSED')
""",
   "def validate_ip_v4_basic(s):\n"
   "    parts = s.split('.')\n"
   "    if len(parts) != 4:\n"
   "        return False\n"
   "    for p in parts:\n"
   "        if not p.isdigit():\n"
   "            return False\n"
   "        if not (0 <= int(p) <= 255):\n"
   "            return False\n"
   "    return True")

_t("iv11", "input_validation_defensive",
   "Write a function `sanitize_filename(s)` that replaces every character "
   "in `s` that is NOT a letter, digit, underscore, dash, or dot with an "
   "underscore, returning the sanitized string (same length as input).",
   """
assert sanitize_filename("my file!.txt") == "my_file_.txt"
assert sanitize_filename("valid_name-1.0.py") == "valid_name-1.0.py"
assert sanitize_filename("a/b\\\\c") == "a_b_c"
assert sanitize_filename("") == ""
print('ALL_TESTS_PASSED')
""",
   "def sanitize_filename(s):\n"
   "    result = []\n"
   "    for ch in s:\n"
   "        if ch.isalnum() or ch in '_-.':\n"
   "            result.append(ch)\n"
   "        else:\n"
   "            result.append('_')\n"
   "    return ''.join(result)")

_t("iv12", "input_validation_defensive",
   "Write a function `parse_bool_loose(s)` that returns True for the "
   "case-insensitive strings 'true', 'yes', '1'; returns False for the "
   "case-insensitive strings 'false', 'no', '0'; and raises a "
   "`ValueError` for anything else.",
   """
assert parse_bool_loose("true") == True
assert parse_bool_loose("YES") == True
assert parse_bool_loose("1") == True
assert parse_bool_loose("false") == False
assert parse_bool_loose("No") == False
assert parse_bool_loose("0") == False
try:
    parse_bool_loose("maybe")
    assert False
except ValueError:
    pass
print('ALL_TESTS_PASSED')
""",
   "def parse_bool_loose(s):\n"
   "    low = s.lower()\n"
   "    if low in ('true', 'yes', '1'):\n"
   "        return True\n"
   "    if low in ('false', 'no', '0'):\n"
   "        return False\n"
   "    raise ValueError(f'cannot parse {s!r} as bool')")

_t("iv13", "input_validation_defensive",
   "Write a function `dedupe_preserve_order(lst)` that returns a new "
   "list with duplicate values removed, keeping only the FIRST occurrence "
   "of each value and preserving original relative order.",
   """
assert dedupe_preserve_order([1, 2, 1, 3, 2, 4]) == [1, 2, 3, 4]
assert dedupe_preserve_order([]) == []
assert dedupe_preserve_order([1, 1, 1]) == [1]
assert dedupe_preserve_order(["b", "a", "b", "c", "a"]) == ["b", "a", "c"]
print('ALL_TESTS_PASSED')
""",
   "def dedupe_preserve_order(lst):\n"
   "    seen = set()\n"
   "    result = []\n"
   "    for item in lst:\n"
   "        if item not in seen:\n"
   "            seen.add(item)\n"
   "            result.append(item)\n"
   "    return result")

_t("iv14", "input_validation_defensive",
   "Write a function `validate_bracket_balance(s)` that returns True if "
   "every occurrence of (), [], and {} in `s` is properly matched and "
   "nested (ignoring any other characters entirely -- only bracket "
   "characters matter), False otherwise.",
   """
assert validate_bracket_balance("a(b[c]d)e") == True
assert validate_bracket_balance("(a[b)c]") == False
assert validate_bracket_balance("no brackets here") == True
assert validate_bracket_balance("(((") == False
assert validate_bracket_balance("") == True
assert validate_bracket_balance("{[()]}") == True
print('ALL_TESTS_PASSED')
""",
   "def validate_bracket_balance(s):\n"
   "    stack = []\n"
   "    pairs = {')': '(', ']': '[', '}': '{'}\n"
   "    for ch in s:\n"
   "        if ch in '([{':\n"
   "            stack.append(ch)\n"
   "        elif ch in ')]}':\n"
   "            if not stack or stack.pop() != pairs[ch]:\n"
   "                return False\n"
   "    return len(stack) == 0")

# ============================================================================
# CATEGORY: data_transformation_parsing -- 14 tasks
# ============================================================================

_t("dt01", "data_transformation_parsing",
   "Write a function `word_count(text)` that returns a dict mapping each "
   "distinct word (case-insensitive, punctuation stripped from word "
   "boundaries) to the number of times it appears in `text`. Words are "
   "separated by whitespace.",
   """
result = word_count("The cat sat. The cat ran!")
assert result == {"the": 2, "cat": 2, "sat": 1, "ran": 1}
assert word_count("") == {}
assert word_count("Hi, hi, HI!") == {"hi": 3}
print('ALL_TESTS_PASSED')
""",
   "import re\n"
   "def word_count(text):\n"
   "    words = re.findall(r\"[a-zA-Z']+\", text.lower())\n"
   "    counts = {}\n"
   "    for w in words:\n"
   "        counts[w] = counts.get(w, 0) + 1\n"
   "    return counts")

_t("dt02", "data_transformation_parsing",
   "Write a function `flatten_dict(d, sep='.')` that flattens a nested "
   "dict into a single-level dict where nested keys are joined with "
   "`sep` (e.g. {'a': {'b': 1}} becomes {'a.b': 1}). Non-dict values "
   "(including empty dicts, which become an empty-value marker `{}` at "
   "their own flattened key... actually simpler: assume no empty nested "
   "dicts appear in test inputs) are kept as leaf values.",
   """
assert flatten_dict({"a": 1, "b": {"c": 2, "d": {"e": 3}}}) == {"a": 1, "b.c": 2, "b.d.e": 3}
assert flatten_dict({}) == {}
assert flatten_dict({"x": 1}) == {"x": 1}
assert flatten_dict({"a": {"b": {"c": {"d": 5}}}}) == {"a.b.c.d": 5}
print('ALL_TESTS_PASSED')
""",
   "def flatten_dict(d, sep='.', _prefix=''):\n"
   "    result = {}\n"
   "    for k, v in d.items():\n"
   "        new_key = f'{_prefix}{sep}{k}' if _prefix else str(k)\n"
   "        if isinstance(v, dict):\n"
   "            result.update(flatten_dict(v, sep, new_key))\n"
   "        else:\n"
   "            result[new_key] = v\n"
   "    return result")

_t("dt03", "data_transformation_parsing",
   "Write a function `chunk_list(lst, size)` that splits `lst` into a "
   "list of sublists each of length `size` (the last sublist may be "
   "shorter if the length does not divide evenly). If `size <= 0`, raise "
   "a `ValueError`.",
   """
assert chunk_list([1,2,3,4,5], 2) == [[1,2],[3,4],[5]]
assert chunk_list([1,2,3], 3) == [[1,2,3]]
assert chunk_list([], 2) == []
assert chunk_list([1,2,3,4], 1) == [[1],[2],[3],[4]]
try:
    chunk_list([1,2], 0)
    assert False
except ValueError:
    pass
print('ALL_TESTS_PASSED')
""",
   "def chunk_list(lst, size):\n"
   "    if size <= 0:\n"
   "        raise ValueError('size must be positive')\n"
   "    return [lst[i:i + size] for i in range(0, len(lst), size)]")

_t("dt04", "data_transformation_parsing",
   "Write a function `invert_dict(d)` that returns a new dict with keys "
   "and values swapped. If any two keys in `d` map to the same value "
   "(which would create a conflict when inverted), raise a `ValueError`.",
   """
assert invert_dict({"a": 1, "b": 2}) == {1: "a", 2: "b"}
assert invert_dict({}) == {}
try:
    invert_dict({"a": 1, "b": 1})
    assert False
except ValueError:
    pass
print('ALL_TESTS_PASSED')
""",
   "def invert_dict(d):\n"
   "    result = {}\n"
   "    for k, v in d.items():\n"
   "        if v in result:\n"
   "            raise ValueError(f'duplicate value {v!r} cannot be inverted')\n"
   "        result[v] = k\n"
   "    return result")

_t("dt05", "data_transformation_parsing",
   "Write a function `parse_key_value_pairs(s)` that parses a string of "
   "the form 'key1=val1;key2=val2;key3=val3' into a dict "
   "{'key1': 'val1', 'key2': 'val2', 'key3': 'val3'}. Handle an empty "
   "string by returning an empty dict. Assume no '=' or ';' appear "
   "within keys or values themselves.",
   """
assert parse_key_value_pairs("a=1;b=2;c=3") == {"a": "1", "b": "2", "c": "3"}
assert parse_key_value_pairs("") == {}
assert parse_key_value_pairs("x=hello") == {"x": "hello"}
print('ALL_TESTS_PASSED')
""",
   "def parse_key_value_pairs(s):\n"
   "    if not s:\n"
   "        return {}\n"
   "    result = {}\n"
   "    for pair in s.split(';'):\n"
   "        k, v = pair.split('=', 1)\n"
   "        result[k] = v\n"
   "    return result")

_t("dt06", "data_transformation_parsing",
   "Write a function `nested_get(d, path, default=None)` that retrieves a "
   "value from a nested dict `d` using a dotted-path string like "
   "'a.b.c', returning `default` if any level of the path is missing or "
   "not a dict.",
   """
d = {"a": {"b": {"c": 42}}}
assert nested_get(d, "a.b.c") == 42
assert nested_get(d, "a.b.x") is None
assert nested_get(d, "a.b.x", "fallback") == "fallback"
assert nested_get(d, "z.y.x") is None
assert nested_get({}, "a") is None
print('ALL_TESTS_PASSED')
""",
   "def nested_get(d, path, default=None):\n"
   "    keys = path.split('.')\n"
   "    current = d\n"
   "    for k in keys:\n"
   "        if not isinstance(current, dict) or k not in current:\n"
   "            return default\n"
   "        current = current[k]\n"
   "    return current")

_t("dt07", "data_transformation_parsing",
   "Write a function `rows_to_dicts(headers, rows)` that converts a list "
   "of column headers and a list of row-lists into a list of dicts "
   "mapping header -> value for each row (like turning parsed CSV data "
   "into records). Assume every row has the same length as headers.",
   """
headers = ["name", "age"]
rows = [["Alice", "30"], ["Bob", "25"]]
assert rows_to_dicts(headers, rows) == [{"name": "Alice", "age": "30"}, {"name": "Bob", "age": "25"}]
assert rows_to_dicts(["x"], []) == []
assert rows_to_dicts([], []) == []
print('ALL_TESTS_PASSED')
""",
   "def rows_to_dicts(headers, rows):\n"
   "    return [dict(zip(headers, row)) for row in rows]")

_t("dt08", "data_transformation_parsing",
   "Write a function `dict_to_sorted_pairs(d)` that returns a list of "
   "(key, value) tuples from dict `d`, sorted by value in descending "
   "order; ties in value are broken by key in ascending order.",
   """
assert dict_to_sorted_pairs({"a": 3, "b": 1, "c": 3}) == [("a", 3), ("c", 3), ("b", 1)]
assert dict_to_sorted_pairs({}) == []
assert dict_to_sorted_pairs({"x": 5}) == [("x", 5)]
print('ALL_TESTS_PASSED')
""",
   "def dict_to_sorted_pairs(d):\n"
   "    return sorted(d.items(), key=lambda kv: (-kv[1], kv[0]))")

_t("dt09", "data_transformation_parsing",
   "Write a function `interleave_lists(a, b)` that interleaves two lists "
   "element by element (a[0], b[0], a[1], b[1], ...), appending any "
   "leftover elements from the longer list at the end once the shorter "
   "list is exhausted.",
   """
assert interleave_lists([1,3,5], [2,4,6]) == [1,2,3,4,5,6]
assert interleave_lists([1,2,3,4], [9]) == [1,9,2,3,4]
assert interleave_lists([], [1,2]) == [1,2]
assert interleave_lists([1,2], []) == [1,2]
assert interleave_lists([], []) == []
print('ALL_TESTS_PASSED')
""",
   "def interleave_lists(a, b):\n"
   "    result = []\n"
   "    i = 0\n"
   "    while i < len(a) or i < len(b):\n"
   "        if i < len(a):\n"
   "            result.append(a[i])\n"
   "        if i < len(b):\n"
   "            result.append(b[i])\n"
   "        i += 1\n"
   "    return result")

_t("dt10", "data_transformation_parsing",
   "Write a function `run_length_of_words(words)` that takes a list of "
   "words and returns a list of (word, count) tuples representing runs "
   "of CONSECUTIVE identical words (e.g. ['a','a','b','a'] becomes "
   "[('a',2),('b',1),('a',1)] -- non-adjacent repeats are NOT merged).",
   """
assert run_length_of_words(["a","a","b","a"]) == [("a",2),("b",1),("a",1)]
assert run_length_of_words([]) == []
assert run_length_of_words(["x"]) == [("x",1)]
assert run_length_of_words(["a","a","a"]) == [("a",3)]
print('ALL_TESTS_PASSED')
""",
   "def run_length_of_words(words):\n"
   "    if not words:\n"
   "        return []\n"
   "    result = []\n"
   "    current = words[0]\n"
   "    count = 1\n"
   "    for w in words[1:]:\n"
   "        if w == current:\n"
   "            count += 1\n"
   "        else:\n"
   "            result.append((current, count))\n"
   "            current = w\n"
   "            count = 1\n"
   "    result.append((current, count))\n"
   "    return result")

_t("dt11", "data_transformation_parsing",
   "Write a function `camel_to_snake(s)` that converts a CamelCase or "
   "camelCase string to snake_case (e.g. 'HelloWorld' -> 'hello_world', "
   "'myHTTPServer' -> 'my_http_server' is not required -- just handle "
   "the simple case of a new lowercase-to-uppercase transition inserting "
   "an underscore before the uppercase letter, then lowercasing "
   "everything).",
   """
assert camel_to_snake("HelloWorld") == "hello_world"
assert camel_to_snake("myVariableName") == "my_variable_name"
assert camel_to_snake("already_snake") == "already_snake"
assert camel_to_snake("A") == "a"
assert camel_to_snake("") == ""
print('ALL_TESTS_PASSED')
""",
   "import re\n"
   "def camel_to_snake(s):\n"
   "    s = re.sub(r'(?<!^)(?=[A-Z])', '_', s)\n"
   "    return s.lower()")

_t("dt12", "data_transformation_parsing",
   "Write a function `snake_to_camel(s)` that converts a snake_case "
   "string to camelCase (e.g. 'hello_world' -> 'helloWorld', "
   "'my_variable_name' -> 'myVariableName'). A string with no "
   "underscores is returned unchanged.",
   """
assert snake_to_camel("hello_world") == "helloWorld"
assert snake_to_camel("my_variable_name") == "myVariableName"
assert snake_to_camel("noUnderscores") == "noUnderscores"
assert snake_to_camel("") == ""
assert snake_to_camel("a_b") == "aB"
print('ALL_TESTS_PASSED')
""",
   "def snake_to_camel(s):\n"
   "    parts = s.split('_')\n"
   "    if not parts:\n"
   "        return s\n"
   "    return parts[0] + ''.join(p.capitalize() for p in parts[1:])")

_t("dt13", "data_transformation_parsing",
   "Write a function `parse_duration_string(s)` that converts a duration "
   "string like '1h30m', '45m', '2h', or '90s' (any combination/subset of "
   "h/m/s components, always in that order if present) into the total "
   "number of seconds as an int.",
   """
assert parse_duration_string("1h30m") == 5400
assert parse_duration_string("45m") == 2700
assert parse_duration_string("2h") == 7200
assert parse_duration_string("90s") == 90
assert parse_duration_string("1h1m1s") == 3661
assert parse_duration_string("0s") == 0
print('ALL_TESTS_PASSED')
""",
   "import re\n"
   "def parse_duration_string(s):\n"
   "    match = re.match(r'(?:(\\d+)h)?(?:(\\d+)m)?(?:(\\d+)s)?$', s)\n"
   "    h = int(match.group(1) or 0)\n"
   "    m = int(match.group(2) or 0)\n"
   "    sec = int(match.group(3) or 0)\n"
   "    return h * 3600 + m * 60 + sec")

_t("dt14", "data_transformation_parsing",
   "Write a function `dict_diff(d1, d2)` that compares two flat dicts "
   "and returns {'added': {...}, 'removed': {...}, 'changed': {...}} "
   "where 'added' contains keys in d2 but not d1 (with d2's values), "
   "'removed' contains keys in d1 but not d2 (with d1's values), and "
   "'changed' contains keys present in both but with different values "
   "(value is a tuple (old_value, new_value)).",
   """
d1 = {"a": 1, "b": 2, "c": 3}
d2 = {"a": 1, "b": 20, "d": 4}
result = dict_diff(d1, d2)
assert result == {"added": {"d": 4}, "removed": {"c": 3}, "changed": {"b": (2, 20)}}
assert dict_diff({}, {}) == {"added": {}, "removed": {}, "changed": {}}
assert dict_diff({"x": 1}, {"x": 1}) == {"added": {}, "removed": {}, "changed": {}}
print('ALL_TESTS_PASSED')
""",
   "def dict_diff(d1, d2):\n"
   "    added = {k: v for k, v in d2.items() if k not in d1}\n"
   "    removed = {k: v for k, v in d1.items() if k not in d2}\n"
   "    changed = {k: (d1[k], d2[k]) for k in d1 if k in d2 and d1[k] != d2[k]}\n"
   "    return {'added': added, 'removed': removed, 'changed': changed}")


if __name__ == "__main__":
    print(f"Total tasks defined: {len(TASKS)}")
    from collections import Counter
    print(Counter(t["category"] for t in TASKS))
