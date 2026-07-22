from collections import defaultdict
import app.core.code_verification as cv
from dataclasses import dataclass
from typing import List

@dataclass
class CodeStats:
    num_lines: int
    total_length: int

def apply_to_code(code: str) -> str:
    code_stats = CodeStats(num_lines=0, total_length=0)
    
    with open('temp_code.txt', 'w') as file:
        file.writelines([re.sub(r'\s+', ' ', line).strip() + '\n' for line in (line.strip() + '\n' for line in code.split('\n')[1:]) if line])
        for line in [re.sub(r'\s+', ' ', line).strip() + '\n' for line in (line.strip() + '\n' for line in code.split('\n')[1:])]:
            code_stats.num_lines += 1
            code_stats.total_length += len(line)
    
    return f'with open("temp_code.txt", "r") as file:\n\tcode = file.read()' if cv.verify_syntax(f'with open("temp_code.txt", "w") as file:\nfile.write("")') and cv.verify_indentation(f'with open("temp_code.txt", "w") as file:\nfile.write("")', max_line_length=80) else trim_output()
    
    def trim_output():
        return f'with open("temp_code.txt", "w") as file:\n\tcode.writelines(islice(list(code_stats.lines), 0, code_stats.num_lines - 15))'