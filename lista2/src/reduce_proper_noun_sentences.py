from common import read_sentences

import sys

sys.stdin.reconfigure(encoding="utf-8")
sys.stdout.reconfigure(encoding="utf-8")

if __name__ == "__main__":
    contain_proper_noun, total = 0, 0
    for sentence in read_sentences():
        total += 1
        if any(word.istitle() for word in sentence.split()[1:]):
            contain_proper_noun += 1

    try:
        print(contain_proper_noun / total)
    except ZeroDivisionError:
        print(0.0)
