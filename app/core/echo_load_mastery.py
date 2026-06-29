# echo_load_mastery.py
"""
Silently load the echo_python_mastery module into Echo's memory.
No tips or examples are printed; functions are stored for later use.
"""

# Import all teach functions from the mastery module
from app.core.echo_python_mastery import (
    teach_basics,
    teach_debugging,
    teach_advanced,
    teach_testing,
    teach_best_practices,
    teach_code_quality,
    show_examples
)

# Store them in Echo's internal knowledge dictionary
echo_mastery = {
    "basics": teach_basics,
    "debugging": teach_debugging,
    "advanced": teach_advanced,
    "testing": teach_testing,
    "best_practices": teach_best_practices,
    "code_quality": teach_code_quality,
    "examples": show_examples
}

# Optional: function to retrieve any section when Echo wants to study
def get_mastery_section(section_name: str):
    """
    Return the function associated with a mastery section.
    Example: get_mastery_section('debugging') returns teach_debugging
    """
    return echo_mastery.get(section_name)

# Echo can now call the functions later like this:
# get_mastery_section('basics')()
# get_mastery_section('advanced')()

