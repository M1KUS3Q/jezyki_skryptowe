from common import extract_preamble, read_sentences, split_non_scalar

import sys

sys.stdin.reconfigure(encoding="utf-8")
sys.stdout.reconfigure(encoding="utf-8")

if __name__ == "__main__":
    extract_preamble()

    for sentence in read_sentences():
        if sentence.startswith("-----"):
            break

        words = split_non_scalar(sentence)
        try:
            next(words)  # Skip the first word
        except StopIteration:
            continue

        for word in words:
            if word.istitle():
                print(word)
