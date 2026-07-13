from app.core.memory_write_validator import detect_and_strip_prose, run_tool_dispatch
import re

class self_edit_generated:
    def strip_leading_prose_in_code(self, code_output):
        while True:
            if not re.match(r'^[a-zA-Z0-9_]+:', code_output):
                prose_detected = True
                break
            else:
                break
        
        if prose_detected:
            code_output = detect_and_strip_prose(code_output)
            run_tool_dispatch(code_output)