from functools import cache
from typing import Generator

def make_generator(f) -> Generator[int, None, None]:
    i = 1
    while True:
        yield f(i)
        i += 1

def make_generator_mem(f) -> Generator[int, None, None]:
    memoized_f = cache(f) 
    return make_generator(memoized_f)

@cache
def fibonacci_recursive(n):
    if n <= 0: return 0
    if n == 1 or n == 2: return 1
    return fibonacci_recursive(n - 1) + fibonacci_recursive(n - 2)

if __name__ == "__main__":
    print("--- Ciąg Fibonacciego ---")
    fib_gen = make_generator_mem(fibonacci_recursive)
    for _ in range(5):
        print(next(fib_gen))
