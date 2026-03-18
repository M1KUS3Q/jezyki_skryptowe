from common import read_sentences

import sys

sys.stdin.reconfigure(encoding="utf-8")
sys.stdout.reconfigure(encoding="utf-8")

if __name__ == "__main__":
    res = ""
    res_len = 0

    for sentence in read_sentences():
        if len(sentence) > res_len:
            res_len = len(sentence)
            res = sentence

    print(res)
