def make_generator(f):
    def generator():
        i = 1
        while True:
            yield f(i)
            i += 1
    return generator()

def fibonacci_iterative(n):
    if n <= 0:
        return 0
    elif n == 1:
        return 0
    elif n == 2:
        return 1

    a = 0
    b = 1

    for _ in range(2, n):
        next_num = a + b
        a = b
        b = next_num

    return b

if __name__ == "__main__":
    # ciąg Fibonacciego 
    fib_gen = make_generator(fibonacci_iterative)
    for _ in range(5):
        print(next(fib_gen))

    # ciąg arytmetyczny (a_n = 3n - 1) 
    arithmetic_gen = make_generator(lambda n: 3 * n - 1)
    for _ in range(5):
        print(next(arithmetic_gen))

    # ciąg geometryczny (a_n = 2^n) 
    geometric_gen = make_generator(lambda n: 2 ** n)
    for _ in range(5):
        print(next(geometric_gen))

    # ciąg potęgowy (a_n = n^2) 
    power_gen = make_generator(lambda n: n ** 2)
    for _ in range(5):
        print(next(power_gen))