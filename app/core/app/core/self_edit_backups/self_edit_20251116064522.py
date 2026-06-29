import re  # regular expressions
import math  # for some mathematical wizardry
import random  # to add a dash of unpredictability

def greet(name):
    """Print a friendly message"""
    print(f"Hello, {name}! May the code be with you!")

def mathemagic():
    """Calculate the average of two numbers"""
    num1 = float(input("Enter the first number: "))
    num2 = float(input("Enter the second number: "))
    return (num1 + num2) / 2

def random_wizardry():
    """Generate a random number between 0 and 100"""
    return random.randint(0, 100)

class Person:
    def __init__(self, name, age):
        self.name = name
        self.age = age

    def introduce(self):
        print(f"Hi, my name is {self.name} and I'm {self.age} years old.")

print("Functions:", [greet.__name__, mathemagic.__name__, random_wizardry.__name__])
print("Classes:", ["Person"])
print("Imports:", ["re", "math", "random"])