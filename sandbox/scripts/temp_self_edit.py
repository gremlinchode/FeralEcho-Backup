from collections import Counter, defaultdict
import logging
import re
from itertools import islice

def apply_to_code(code: str) -> str:
    code_lines = [re.sub(r'\s+', ' ', line).strip() + '\n' for line in code.split('\n')]
    seen = set()
    
    def _remove_duplicates_and_shorten(line):
        if line in seen:
            return ''
        seen.add(line)
        return re.sub(r'\s+', ' ', line).strip() + '\n'
    
    shortened_lines = [_remove_duplicates_and_shorten(line) for line in code_lines]
    
    logging.basicConfig(level=logging.INFO)
    logging.info("Starting code generation")
    
    try:
        with open('temp_code.txt', 'w') as file:
            file.writelines(shortened_lines)
        
        return 'with open("temp_code.txt", "r") as file:\n\tcode = file.read()'
    except Exception as e:
        logging.error(f"Error: {e}")
        raise