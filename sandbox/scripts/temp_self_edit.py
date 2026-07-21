import app.emergent_scheduler
from dataclasses import dataclass
from itertools import islice
from typing import Generator

@dataclass
class CodeChunk:
    content: str
    type: str = 'snippet'

def apply_to_code(code: str) -> Generator[CodeChunk, None, None]:
    import re
    
    def generator():
        chunks = [re.sub(r'\s+', ' ', line).strip() + '\n' for line in code.split('\n') if line]
        for chunk in chunks:
            yield CodeChunk(chunk)
    
    return generator()