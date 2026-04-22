import argparse
from sys import stdin
from collections import deque


def tail(input, line_num, follow=False):
    if line_num <= 0:
        return

    # deque of size line_num will automatically discard old lines when new ones are added
    tail_lines = deque(maxlen=line_num)
    for line in input:
        tail_lines.append(line)

    # prints the last line_num lines
    for line in tail_lines:
        print(line, end="")

    # if follow is True, keep reading new lines and print them as they come
    while follow:
        line = input.readline()
        if not line:
            continue
        print(line, end="")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--lines", type=int, default=10)
    parser.add_argument("--follow", action="store_true")
    # no -- in name means that `file` is positional (takes first non-options argument)
    # nargs="?" means its optional (appears 0 or 1 times)
    parser.add_argument("file", nargs="?", type=str, default=None)
    args = parser.parse_args()

    if args.file:
        with open(args.file, "r") as f:
            tail(f, args.lines, args.follow)
    else:
        tail(stdin, args.lines)


if __name__ == "__main__":
    main()
