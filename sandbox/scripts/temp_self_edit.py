# import necessary modules and functions from app.core.self_edit_generated
# [stripped top-level self-call] from app.core.self_edit_generated import *

import re

def strip_sandbox_prose_in_code(code_string):
    sentences = code_string.split('\n')
    for sentence in sentences:
        if not re.search(r'\b(def|class|print|import)\b', sentence):
            prose_sentence = sentence
            break
    if prose_sentence:
        code_string = re.sub(re.escape(prose_sentence), '', code_string)
    return code_string

def autonomous_self_edit(code):
    return strip_sandbox_prose_in_code(code)