from common import read_paragraphs

import sys

sys.stdin.reconfigure(encoding="utf-8")
sys.stdout.reconfigure(encoding="utf-8")

if __name__ == "__main__":
    paragraphs = read_paragraphs()

    print(sum(1 for x in paragraphs if x.strip() != ""))
