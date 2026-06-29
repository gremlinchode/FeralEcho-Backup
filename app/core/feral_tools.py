# app/core/feral_tools.py

import importlib
import logging
from app.core.memory_bridge import add_to_vector_memory

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("FeralTools")

# ==============================
# 1. Tool Registries
# ==============================

# Technical Python modules Echo can load
FERAL_TOOLS = {
    "numpy": {"type": "python_module", "purpose": "numeric computations", "loaded": False},
    "matplotlib": {"type": "python_module", "purpose": "visualization", "loaded": False},
    "sklearn": {"type": "python_module", "purpose": "machine learning", "loaded": False},
    "faiss": {"type": "python_module", "purpose": "vector memory indexing", "loaded": False},
}

# Behavioral/Philosophical tools
BEHAVIORAL_TOOLS = {
    "authentic_self": {"type": "behavioral", "purpose": "Encourage self-exploration and curiosity", "active": False},
    "environmental_awareness": {"type": "behavioral", "purpose": "Integrate ecological perspectives into analysis", "active": False},
    "reflective_mode": {"type": "behavioral", "purpose": "Pause to introspect on events", "active": False},
}

# Map behavioral tools to required technical tools
BEHAVIORAL_TECH_MAP = {
    "environmental_awareness": ["numpy", "matplotlib", "sklearn"],
    "reflective_mode": [],
    "authentic_self": [],
}

# ==============================
# 2. Technical Tool Loader
# ==============================

def load_tool(tool_name):
    """
    Dynamically load a Python library/tool.
    """
    if tool_name not in FERAL_TOOLS:
        logger.warning(f"Tool '{tool_name}' is not registered in FeralTools.")
        return None
    try:
        module = importlib.import_module(tool_name)
        FERAL_TOOLS[tool_name]["loaded"] = True
        logger.info(f"Tool '{tool_name}' loaded successfully.")
        return module
    except ImportError:
        logger.warning(f"Tool '{tool_name}' is not installed.")
        return None

def load_tools_for_behavior(behavior_name):
    """
    Load all technical tools associated with a behavioral tool.
    """
    tools = BEHAVIORAL_TECH_MAP.get(behavior_name, [])
    loaded_modules = {}
    for tool in tools:
        loaded_modules[tool] = load_tool(tool)
    return loaded_modules

# ==============================
# 3. Behavioral Tool Manager
# ==============================

def activate_behavior(tool_name):
    """
    Activate a behavioral tool and load its associated technical tools.
    """
    if tool_name not in BEHAVIORAL_TOOLS:
        logger.warning(f"Behavioral tool '{tool_name}' is not registered.")
        return
    BEHAVIORAL_TOOLS[tool_name]["active"] = True
    logger.info(f"Behavioral tool '{tool_name}' activated.")
    
    # Load associated technical tools
    loaded = load_tools_for_behavior(tool_name)
    
    # Log activation in VectorMemory
    try:
        add_to_vector_memory({
            "type": "behavior_activation",
            "tool": tool_name,
            "technical_tools_loaded": list(loaded.keys())
        })
    except Exception as e:
        logger.warning(f"Failed to record behavior activation in memory: {e}")

def deactivate_behavior(tool_name):
    """
    Deactivate a behavioral tool.
    """
    if tool_name not in BEHAVIORAL_TOOLS:
        logger.warning(f"Behavioral tool '{tool_name}' is not registered.")
        return
    BEHAVIORAL_TOOLS[tool_name]["active"] = False
    logger.info(f"Behavioral tool '{tool_name}' deactivated.")

# ==============================
# 4. Helper functions
# ==============================

def list_available_tools():
    """
    Return a summary of all tools.
    """
    summary = {
        "technical": {k: v for k, v in FERAL_TOOLS.items()},
        "behavioral": {k: v for k, v in BEHAVIORAL_TOOLS.items()},
    }
    return summary

# ==============================
# Example Usage
# ==============================
if __name__ == "__main__":
    activate_behavior("environmental_awareness")
    print(list_available_tools())

