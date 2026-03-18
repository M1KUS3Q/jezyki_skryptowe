from common import read_chars
import sys

sys.stdin.reconfigure(encoding='utf-8')
sys.stdout.reconfigure(encoding='utf-8')

if __name__ == "__main__":
    print(sum(1 for x in read_chars() if not x.isspace()))
