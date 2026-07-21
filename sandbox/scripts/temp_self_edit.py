from app.emergent_scheduler import ToolManager
from app.core import CodeCompressor, logging
import re
from itertools import islice

class CodeCompressor:
    def __init__(self):
        self.logger = logging.getLogger('CodeCompressor')

    def compress_code(self, code: str) -> str:
        lines = [re.sub(r'\s+', ' ', line).strip() + '\n' for line in code.split('\n')]
        return ''.join(lines)

@logging.log_call
def shorten_creative_code_generation_v2(code: str) -> str:
    tool_manager = ToolManager()
    code_compressor = CodeCompressor()

    short_codes = [line.strip() if (line := next(islice(code.split('\n'), i, None))) else '' for i in range(2)]

    compressed_code = code_compressor.compress_code(''.join(short_codes))
    return f'with open("temp_code.txt", "r") as file:\n\tcode = file.read()'