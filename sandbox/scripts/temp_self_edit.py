import app.emergent_scheduler
from itertools import islice
import re

def log_call(func):
    def wrapper(*args, **kwargs):
        print(f"Calling {func.__name__} with args={args} and kwargs={kwargs}")
        result = func(*args, **kwargs)
        print(f"{func.__name__} returned: {result}")
        return result
    return wrapper

@log_call
def shorten_creative_code_generation(code: str) -> str:
    lines = [re.sub(r'\s+', ' ', line).strip() + '\n' for line in islice(code.split('\n'), 2, None)]
    
    with open('temp_code.txt', 'w') as file:
        file.writelines(lines)
    
    return 'with open("temp_code.txt", "r") as file:\n\tcode = file.read()'