def apply_to_code(code: str) -> str:
    prose_pattern = r'^\s*\b(?!.*?)([A-Za-z\s]+(?:\.\s*[A-Za-z\s]+)*?)(?!\s*.*)'
    modified_code = '\n'.join([line if any(re.match(prose_pattern, line)) else line for line in code.split('\n')])
    python_token_pattern = re.compile(r'^(?:\s*(?:def|class|if|elif|else|for|while|try|except|finally|break|continue)\s*\(|::)|[a-zA-Z_][a-zA-Z0-9_\.]*)')