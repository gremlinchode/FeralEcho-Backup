# import necessary modules from app.core directory into current script
from functools import lru_cache

def apply_to_code(code: str) -> str:
    @lru_cache(maxsize=None)
    def process_line(line: str) -> str:
        return re.sub(r'\s+', ' ', line).strip()

    with open('temp_code.txt', 'w') as file:
        file.writelines([f'{line}\n' for line in islice(code.split('\n'), 2, None)])

    return f'with open("temp_code.txt", "r") as file:\n\tcode = file.read()'