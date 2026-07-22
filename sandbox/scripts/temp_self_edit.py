class HealthMonitor:
    _error_count = 0
    _warning_count = 0
    
    def __init__(self):
        self._error_count = 0
        self._warning_count = 0
    
    @property
    def error_count(self):
        return self._error_count
    
    @property
    def warning_count(self):
        return self._warning_count
    
    def log_error(self, msg: str) -> None:
        self._error_count += 1
        logging.error(msg)
    
    def log_warning(self, msg: str) -> None:
        self._warning_count += 1
        logging.warning(msg)

def apply_to_code(code: str) -> str:
    with open('temp_code.txt', 'w') as file:
        file.write('\n'.join([line for line in code.split('\n') if len(line.strip()) > 0]))
    
    return f'with open("temp_code.txt", "r") as file:\n\tcode = file.read()'