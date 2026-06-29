def modified_strip_sandbox_output(input_str: str) -> str:
    sandbox_output = copy(strip_sandbox_output)
    if len(sandbox_output) > 80:
        sandbox_output = sandbox_output[:79] + '...'
    return sandbox_output