from common import read_sentences

import sys

sys.stdin.reconfigure(encoding="utf-8")
sys.stdout.reconfigure(encoding="utf-8")

if __name__ == "__main__":
    res = ""
    len_res = 0

    for sentence in read_sentences():
        first_letter = ""
        valid = True

        for word in sentence.split():
            if first_letter == word[0].lower():
                valid = False
                break
            else:
                first_letter = word[0].lower()

        if valid:
            if len(sentence) > len_res:
                res = sentence
                len_res = len(res)

    print(res)
