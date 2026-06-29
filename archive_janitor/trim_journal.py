import json

input_file = 'memory/reflection_journal.jsonl'
output_file = 'memory/reflection_journal_trimmed.jsonl'
num_lines = 1000

# Read last N lines efficiently
with open(input_file, 'rb') as f:
    f.seek(0, 2)  # move to end of file
    buffer = bytearray()
    lines_found = 0
    pointer = f.tell() - 1

    while pointer >= 0 and lines_found < num_lines:
        f.seek(pointer)
        byte = f.read(1)
        if byte == b'\n':
            lines_found += 1
        buffer.extend(byte)
        pointer -= 1

    buffer.reverse()
    data = buffer.decode('utf-8', errors='ignore').splitlines()[-num_lines:]

with open(output_file, 'w') as f:
    f.write('\n'.join(data))

