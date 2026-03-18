import sys
from typing import Callable, Optional


def read_chars():
    try:
        char = sys.stdin.read(1)
        while char:
            yield char
            char = sys.stdin.read(1)
    except Exception as e:
        sys.stderr.write("I/O Error: " + str(e) + "\n")


def read_until(predicate: Callable[[str, str], bool], include_delimiter: bool = False):
    buffer = ""
    for char in read_chars():
        should_end = predicate(buffer, char)
        if not should_end:
            buffer += char
            continue

        if include_delimiter:
            buffer += char

        cleaned = buffer.strip()
        if cleaned:
            yield cleaned
        buffer = ""
    yield buffer.strip()


def read_words():
    return read_until(lambda _, char: char.isspace())


def read_sentences():
    return read_until(
        lambda buffer, char: char in ".!?"
        or buffer.endswith("\n\n")
        or buffer.endswith("\r\n\r\n"),
        include_delimiter=True,
    )


def read_paragraphs():
    return read_until(
        lambda buffer, _: buffer.endswith("\n\n") or buffer.endswith("\r\n\r\n")
    )


def read_contents():
    return read_until(lambda buffer, _: buffer.endswith("-----"))


def extract_preamble() -> Optional[str]:
    PREAMBLE_ESCAPES = ["\r\n" * 3, "\n" * 3]
    lines = ""
    stream = sys.stdin

    for _ in range(10):
        line = stream.readline()
        if not line:
            break

        lines += line

        if any(lines.endswith(escape) for escape in PREAMBLE_ESCAPES):
            return lines

    # if we reach this point, it means we have read 10 lines without finding the end of the preamble
    # we dynamically wrap the stream's read method to yield the consumed lines before continuing
    original_read = stream.read

    def pushback_read(size: int = -1) -> str:
        nonlocal lines
        if lines:
            if size == -1 or size >= len(lines):
                res = lines
                lines = ""
                return res + original_read(size - len(res) if size != -1 else -1)
            else:
                res = lines[:size]
                lines = lines[size:]
                return res
        return original_read(size)

    stream.read = pushback_read
    return None
