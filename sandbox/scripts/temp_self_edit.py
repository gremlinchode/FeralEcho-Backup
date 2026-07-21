def timer(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"{func.__name__} executed in {end_time - start_time:.2f} seconds")
        return result
    return wrapper

@dataclass
class CodeGenerator:
    code: str

    def __post_init__(self):
        self.code_lines = [line.strip() for line in self.code.split('\n')]

    @timer
    def generate_short_code(self) -> str:
        shortened_codes = [re.sub(r'\s+', ' ', line).strip() + '\n' if (line := next(islice(self.code_lines, i, None))) else '' for i in range(2)]
        with open('temp_code.txt', 'w') as file:
            file.writelines(shortened_codes)
        return f"with open('temp_code.txt', 'r') as file:\n\tcode = file.read()"