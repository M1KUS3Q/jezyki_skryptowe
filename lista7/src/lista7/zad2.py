from typing import Iterable


def forall(pred, iterable: Iterable):
    try:
        x = next(iterable)
        return pred(x) and forall(pred, iterable)
    except StopIteration:
        return True

def exists(pred, iterable: Iterable):
    try:
        x = next(iterable)
        return pred(x) or exists(pred, iterable)
    except StopIteration:
        return False

def atleast(n, pred, iterable: Iterable, current=0):
    try:
        new_current = current + (1 if pred(next(iterable)) else 0)
        return new_current >= n or atleast(n, pred, iterable, new_current)
    except StopIteration:
        return current >= n
    
def atmost(n, pred, iterable, current=0):
    try:
        new_current = current + (1 if pred(next(iterable)) else 0)
        return new_current <= n and atmost(n, pred, iterable, new_current)
    except StopIteration:
        return current <= n

if __name__ == "__main__":
    # print(forall(lambda x: x > 0, iter([1, 2, 3])))
    # print(exists(lambda x: x > 0, iter([1, -2, 3])))
    print(atmost(2, lambda x: x > 0, iter([1,2,3,-4,-5])))