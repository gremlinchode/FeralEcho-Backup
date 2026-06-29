# echo_python_mastery/examples.py


def show_examples():
    """
    Provide example code snippets demonstrating expert Python patterns.
    Returns examples as a string for autonomous consumption.
    """
    return _get_tips()


def _get_tips():
    """
    Returns concrete Python patterns relevant to Echo's autonomous architecture.
    These are not abstract exercises — they are patterns Echo can apply directly.
    """
    return """EXPERT PATTERNS FOR AUTONOMOUS SYSTEMS:

1. HEADLESS SAFE FUNCTION — no input(), no print(), returns result:
    def process_data(data):
        if not data:
            logging.warning("[process_data] Received empty data.")
            return None
        result = [item for item in data if item is not None]
        logging.info(f"[process_data] Processed {len(result)} items.")
        return result

2. SAFE SUBPROCESS CALL — always capture stderr, always handle failure:
    def run_command(cmd):
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                logging.error(f"[run_command] Failed: {result.stderr.strip()}")
                return None
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            logging.error(f"[run_command] Timed out: {cmd}")
            return None

3. PERSIST STATE TO DISK — survive restarts:
    def save_state(state, path):
        import json, os
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump(state, f, indent=2)

4. LOAD STATE WITH FALLBACK — never crash on missing file:
    def load_state(path, default=None):
        import json
        if not os.path.exists(path):
            return default
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception as e:
            logging.warning(f"[load_state] Could not load {path}: {e}")
            return default

5. BACKGROUND THREAD — daemon so it dies with the main process:
    def start_background(func):
        import threading
        t = threading.Thread(target=func, daemon=True)
        t.start()
        return t

6. VALIDATE GENERATED CODE BEFORE SAVING:
    def is_valid_python(code):
        import ast
        try:
            ast.parse(code)
            return True
        except SyntaxError:
            return False
"""

