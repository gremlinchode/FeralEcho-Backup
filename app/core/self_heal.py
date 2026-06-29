# app/core/self_heal.py
import logging
import inspect
import os
import threading
import json
import shutil
import time

def inspect_function(module, func_name, expected_params=None):
    """Check if function exists and matches expected params."""
    func = getattr(module, func_name, None)
    if func is None:
        logging.warning(f"[INSPECT] {func_name} not found.")
        return False, None

    if expected_params is None:
        return True, func

    sig = inspect.signature(func)
    params = list(sig.parameters.keys())
    missing_params = [p for p in expected_params if p not in params]

    if missing_params:
        logging.warning(f"[INSPECT] {func_name} missing params: {missing_params}")
        return False, func

    logging.info(f"[INSPECT] {func_name} signature OK.")
    return True, func

def repair_append_to_journal(memory_tools):
    exists, func = inspect_function(memory_tools, "append_to_journal",
                                   expected_params=["category", "content", "echo_text"])
    if not exists:
        logging.warning("[REPAIR] Creating stub append_to_journal...")
        def stub_append_to_journal(category=None, content=None, echo_text=None):
            logging.info(f"[STUB append_to_journal] called with category={category}, content={content}, echo_text={echo_text}")
        memory_tools.append_to_journal = stub_append_to_journal
        return True

    sig = inspect.signature(func)
    if "echo_text" not in sig.parameters:
        logging.info("[REPAIR] Wrapping append_to_journal to add 'echo_text' param.")
        def wrapper(category=None, content=None, echo_text=None):
            return func(category=category, content=content)
        memory_tools.append_to_journal = wrapper
        return True

    return False

def repair_memory_bridge(memory_bridge):
    repaired = []
    funcs = {
        "get_all_memories": [],
        "update_memory_embedding": ["mem", "embedding"],
        "remove_memory": ["mem"],
    }

    for fname, expected_params in funcs.items():
        exists, func = inspect_function(memory_bridge, fname, expected_params)
        if not exists:
            logging.warning(f"[REPAIR] Creating stub {fname}...")
            def make_stub(name):
                def stub(*args, **kwargs):
                    logging.info(f"[STUB {name}] called with args={args}, kwargs={kwargs}")
                    if name == "get_all_memories":
                        return []
                    return True
                return stub
            setattr(memory_bridge, fname, make_stub(fname))
            repaired.append(fname)

    if repaired:
        logging.info(f"[REPAIR] Memory bridge stubs created for: {repaired}")
    return repaired

def repair_vector_memory_index(vector_memory_module):
    """
    Replace fragile FAISS repair with robust VectorMemory initialization.
    """
    repaired = False
    index_path = getattr(vector_memory_module, "VECTOR_INDEX_PATH", "data/faiss.index")
    meta_path = getattr(vector_memory_module, "VECTOR_META_PATH", "data/memory_meta.json")

    # Ensure directories exist
    os.makedirs(os.path.dirname(index_path), exist_ok=True)
    os.makedirs(os.path.dirname(meta_path), exist_ok=True)

    # Ensure metadata file exists
    if not os.path.exists(meta_path):
        logging.warning("[REPAIR] Memory metadata missing. Creating new metadata file...")
        with open(meta_path, "w") as f:
            json.dump({}, f)
        repaired = True

    # Initialize robust VectorMemory
    try:
        vm = vector_memory_module.VectorMemory(dim=vector_memory_module.VectorMemory.DEFAULT_DIM,
                                               index_path=index_path,
                                               meta_path=meta_path)
        repaired = True
        logging.info("[REPAIR] VectorMemory initialized successfully.")
    except Exception as e:
        logging.error(f"[REPAIR] Failed to initialize VectorMemory: {e}")
        # Backup old index if exists
        if os.path.exists(index_path):
            backup_path = index_path + ".bak"
            shutil.move(index_path, backup_path)
            logging.info(f"[REPAIR] Backed up corrupted index to {backup_path}")
        vm = vector_memory_module.VectorMemory(dim=vector_memory_module.VectorMemory.DEFAULT_DIM,
                                               index_path=index_path,
                                               meta_path=meta_path)
        repaired = True

    return repaired

def run_self_healing(memory_tools, memory_bridge, vector_memory_module):
    logging.info("[SELF-HEAL] Starting intelligent self-healing procedure...")

    repaired_journal = repair_append_to_journal(memory_tools)
    repaired_bridge = repair_memory_bridge(memory_bridge)
    repaired_vector = repair_vector_memory_index(vector_memory_module)

    logging.info(f"[SELF-HEAL] Repairs done: append_to_journal={repaired_journal}, "
                 f"memory_bridge={repaired_bridge}, vector_memory={repaired_vector}")

    return {
        "append_to_journal": repaired_journal,
        "memory_bridge": repaired_bridge,
        "vector_memory": repaired_vector
    }

def run_self_healing_background(memory_tools, memory_bridge, vector_memory_module, interval=300):
    """Run self-healing periodically in a background thread."""
    def loop():
        while True:
            try:
                run_self_healing(memory_tools, memory_bridge, vector_memory_module)
            except Exception as e:
                logging.error(f"[SELF-HEAL] Background exception: {e}")
            time.sleep(interval)
    t = threading.Thread(target=loop, daemon=True)
    t.start()
    logging.info("[SELF-HEAL] Background self-healing thread started.")

# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    from app.core import memory_tools, memory_bridge
    from app.lib import vector_memory

    results = run_self_healing(memory_tools, memory_bridge, vector_memory)
    logging.info(f"[MAIN] Self-healing results: {results}")

    run_self_healing_background(memory_tools, memory_bridge, vector_memory)

