from common import read_sentences, split_non_scalar

import sys

sys.stdin.reconfigure(encoding="utf-8")
sys.stdout.reconfigure(encoding="utf-8")

if __name__ == "__main__":
    contain_proper_noun, total = 0, 0
    for sentence in read_sentences():

        words = split_non_scalar(sentence)
        try:
            next(words)  # Skip the first word
            total += 1
        except StopIteration:
            continue

        if any(word.istitle() for word in words):
            contain_proper_noun += 1

    try:
        print(contain_proper_noun / total)
    except ZeroDivisionError:
        print(0.0)
