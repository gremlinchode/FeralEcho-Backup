from .coding_basics import teach_basics
from .code_quality import teach_code_quality
from .best_practices import teach_best_practices
from .advanced_python import teach_advanced
from .examples import show_examples
from .debugging import teach_debugging
from .testing_and_validation import teach_testing

# ---- Lazy imports to avoid circular dependency ----
def get_self_edit_manager():
    from app.core import self_edit_manager
    return self_edit_manager

def get_temporal_environment():
    from app.core import temporal_environment
    return temporal_environment

