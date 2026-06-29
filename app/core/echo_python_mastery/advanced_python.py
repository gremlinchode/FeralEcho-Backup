# echo_python_mastery/advanced_python.py


def teach_advanced():
    """
    Teach iterators, generators, comprehensions, decorators, and OOP.
    Returns guidance as a string for autonomous consumption.
    """
    return _get_tips()


def _get_tips():
    """
    Returns advanced Python guidance as a plain string Echo can read and apply.
    """
    return """ADVANCED PYTHON:
- Use list/set/dict comprehensions for concise, readable loops.
  EXAMPLE: squares = [x**2 for x in range(10) if x % 2 == 0]

- Use generators for memory-efficient iteration over large sequences.
  EXAMPLE:
    def square_generator(n):
        for x in range(n):
            yield x ** 2

- Use decorators to add behavior to functions without modifying them.
  EXAMPLE:
    def log_call(func):
        def wrapper(*args, **kwargs):
            logging.info(f"Calling {func.__name__}")
            return func(*args, **kwargs)
        return wrapper

- Use classes to encapsulate state and behavior that belongs together.
  EXAMPLE:
    class HealthMonitor:
        def __init__(self):
            self.errors = []
        def record(self, error):
            self.errors.append(error)

- Use context managers (with) for safe resource handling. Always prefer them over manual open/close.
  EXAMPLE: with open("log.txt", "a") as f: f.write(entry)

- Prefer generators over lists when you only need to iterate once and the dataset may be large.
- Use dataclasses for simple data containers instead of verbose __init__ boilerplate.
- Leverage defaultdict and Counter from collections for cleaner aggregation logic.
"""

