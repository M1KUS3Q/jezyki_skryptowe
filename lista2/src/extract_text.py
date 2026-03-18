from common import extract_preamble, read_contents
import sys

sys.stdin.reconfigure(encoding="utf-8")
sys.stdout.reconfigure(encoding="utf-8")

if __name__ == "__main__":
    extract_preamble()
    try:
        text = next(read_contents())[:-5]  # remove the trailing "-----"
        print(text)
    except StopIteration:
        print("Błąd: brak wymaganego separatora w pliku.", file=sys.stderr)
