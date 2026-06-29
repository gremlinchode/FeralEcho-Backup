import os
import json
from logging_setup import log

SANDBOX_DIR = os.path.dirname(__file__)
INPUT_DIR = os.path.join(SANDBOX_DIR, 'inputs')
OUTPUT_DIR = os.path.join(SANDBOX_DIR, 'outputs')
os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

def safe_read_json(filename):
    path = os.path.join(INPUT_DIR, filename)
    try:
        with open(path, 'r') as f:
            data = json.load(f)
        log(f"Successfully read {filename}")
        return data
    except Exception as e:
        log(f"Error reading {filename}: {e}")
        return {}

def safe_write_json(filename, data):
    path = os.path.join(OUTPUT_DIR, filename)
    try:
        with open(path, 'w') as f:
            json.dump(data, f, indent=4)
        log(f"Successfully wrote {filename}")
    except Exception as e:
        log(f"Error writing {filename}: {e}")

