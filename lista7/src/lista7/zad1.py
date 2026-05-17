# Functional, no for, while, if, unless ternary operator or list/dict comprehension

def acronym(s: list[str]) -> str:
    return ''.join([word[0] for word in s])

def median(s: list[int]) -> float:
    sort = sorted(s)
    n = len(sort)
    is_even = n % 2 == 0
    
    return (sort[n // 2 - 1] + sort[n // 2]) / 2 if is_even else sort[n // 2]

def newton_sqrt(n: float, epsilon: float = 1e-10, result = 1) -> float:
    # formula from https://en.wikipedia.org/wiki/Newton%27s_method
    new = 0.5 * (result + n / result) 
    error = abs(new * new - n)
    
    return new if error <= epsilon else newton_sqrt(n, epsilon, new)

# "on i ona" -> {'o': ['on', 'ona'], 'n': ['on', 'ona'], 'i': ['i'], 'a': ['ona']}
def make_alpha_dict(input: str) -> dict[str,list[str]]:
    words = input.split()
    chars = set(''.join(words))
    return {char: [word for word in words if char in word] for char in chars}

def flatten(x) -> list:
    def is_scalar(x):
        return not (isinstance(x, list) or isinstance(x,tuple))
    
    # [EXPR for A in B for C in D] -> for A in B: for C in D: EXPR
    return [x] if is_scalar(x) else [item for sublist in x for item in flatten(sublist)]

def group_anagrams(x: list[int]) -> dict[str,list[str]]:
    anagrams = set(''.join(sorted(word)) for word in x)
    return {anagram: [word for word in x if ''.join(sorted(word)) == anagram] for anagram in anagrams}

if __name__ == '__main__':
    print(acronym(['Central', 'Intelligence', 'Agency']))
    print(median([1, 3, 5, 7, 9]))
    print(newton_sqrt(3,0.1))
    print(make_alpha_dict("on i ona"))
    print(flatten([1, [2, 3], [[4, 5], 6]]))
    print(group_anagrams(["kot", "tok", "pies", "kep", "pek"]))