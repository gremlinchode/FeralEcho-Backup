import ast
from collections import defaultdict

# Parse the code using AST (Abstract Syntax Tree)
tree = ast.parse("""
def hello(name: str):
    print(f"Hello, {name}!")

class Greeting:
    def __init__(self, name: str):
        self.name = name

    def say_hello(self) -> None:
        print(f"Hello, {self.name}!")
""")  # Replace with the parsed code string