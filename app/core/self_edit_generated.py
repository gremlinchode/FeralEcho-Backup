class self_edit_generated:
    def strip_leading_prose_in_code(self, code):
        def detect_and_strip_prose(line):
            if line.startswith('#'):
                return ''
            else:
                return line

        output_lines = []
        for line in code.split('\n'):
            while True:
                if line.strip().startswith('import') or line.strip().startswith('from'):
                    break
                elif not line.strip():
                    break
                else:
                    if detect_and_strip_prose(line).strip():
                        break
                    line = line.lstrip()
            output_lines.append(line)
        return '\n'.join(output_lines)

    def record_pending_outcome(self, outcome):
        pass