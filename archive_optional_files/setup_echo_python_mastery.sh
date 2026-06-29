#!/bin/bash
# setup_echo_python_mastery.sh
# Run from the root of FeralEcho project

echo "Creating echo_python_mastery module inside app/core/..."

# Create the module folder
mkdir -p app/core/echo_python_mastery

# Create __init__.py
cat > app/core/echo_python_mastery/__init__.py <<EOL
"""
Echo Python Mastery Module
Teaches Echo to write, debug, and optimize Python like an expert.
"""

from .coding_basics import teach_basics
from .debugging import teach_debugging
from .advanced_python import teach_advanced
from .testing_and_validation import teach_testing
from .best_practices import teach_best_practices
from .code_quality import teach_code_quality
from .examples import show_examples

__all__ = [
    "teach_basics",
    "teach_debugging",
    "teach_advanced",
    "teach_testing",
    "teach_best_practices",
    "teach_code_quality",
    "show_examples"
]
EOL

# Helper function to create submodule files with a sample teach() function
create_module() {
    MODULE_NAME=$1
    FUNC_NAME="teach_${MODULE_NAME//_/}"  # remove underscores for function name
    MODULE_FILE=app/core/echo_python_mastery/$MODULE_NAME.py

    cat > $MODULE_FILE <<EOL
def $FUNC_NAME():
    """
    Teach $MODULE_NAME concepts to Echo.
    """
    tips = ["Example tip 1", "Example tip 2", "Example tip 3"]
    for tip in tips:
        print(f"[$MODULE_NAME] {tip}")
EOL
}

# Create all submodules
create_module "coding_basics"
create_module "debugging"
create_module "advanced_python"
create_module "testing_and_validation"
create_module "best_practices"
create_module "code_quality"
create_module "examples"

echo "echo_python_mastery module created successfully in app/core/"
echo "You can now import it in Echo scripts using:"
echo "from app.core.echo_python_mastery import teach_basics, teach_debugging, ..."

