from app.core.self_edit_outcome_tracker import record_pending_outcome, evaluate_pending_outcomes
import re

def apply_to_code(code):
    def strip_leading_prose(line):
        if line.startswith('#'):
            return ''
        else:
            return line

    lines = (line.strip() for line in code.split('\n'))
    sentences = [re.sub(r'^\s*([A-Za-z].*\.)', '', line) for line in lines]
    return '\n'.join(sentences)

class self_edit_generated:
    def __init__(self):
        pass

    @staticmethod
    def apply_to_code(code: str) -> str:
        logging.info('Prose detection guard applied')
        return strip_leading_prose_in_code(code)

def strip_leading_prose_in_code(code):
    def detect_and_strip_prose(line):
        if line.strip().startswith('import') or line.strip().startswith('from'):
            return ''
        else:
            return line

    output_lines = []
    for line in code.split('\n'):
        while True:
            if not line.strip():
                break
            elif detect_and_strip_prose(line).strip():
                break
            line = line.lstrip()
        output_lines.append(line)
    return '\n'.join(output_lines)