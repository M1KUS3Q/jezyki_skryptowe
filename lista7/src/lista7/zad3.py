import random
from typing import Iterator


class PasswordGenerator(Iterator):
    def __init__(self, length, charset, count):
        self.length = length
        self.charset = charset
        self.count = count
        self.generated = 0
        
    def __iter__(self):
        return self
    
    def __next__(self):
        if self.generated >= self.count:
            raise StopIteration
        self.generated += 1
        return ''.join(random.choice(self.charset) for _ in range(self.length))
    
if __name__ == "__main__":
    n = 5
    charset = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    generator = PasswordGenerator(8, charset, n)
    
    def check(x):
        return len(x) == 8 and all(c in charset for c in x)
    
    for _ in range(n):
        assert(check(next(generator)))
    
    try:
        next(generator)
        assert False, "Should have raised StopIteration"
    except StopIteration:
        pass
        