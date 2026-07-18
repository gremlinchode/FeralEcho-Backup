import re

def apply_to_code(code: str) -> str:
    lines = [line for line in code.split('\n') if line.strip()]
    
    def tokenize():
        for i, line in enumerate(lines):
            if '=' in line or ':' in line:
                yield line
            elif re.search(r'\b(\w+(?:\W*\w+)*)\b', line):
                pass
            else:
                yield ''
                yield line

    return '\n'.join(tokenize())