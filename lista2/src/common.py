import sys
from typing import Callable, Optional

sys.stdin.reconfigure(encoding="utf-8")
sys.stdout.reconfigure(encoding="utf-8")


def split_non_scalar(
    text: str,
    predicate: Callable[[str], bool] = lambda c: c.isspace() or c in ',.!?;:"()[]{}',
):
    """
    Splits a string into components based on a given predicate function.

    Args:
        text (str): The string to split.
        predicate (Callable[[str], bool], optional): A function that returns True if a
            character is a delimiter. Defaults to whitespace and common punctuation.

    Yields:
        str: The separated components of the text.
    """
    buffer = ""
    for char in text:
        if predicate(char):
            if buffer:
                yield buffer
                buffer = ""
        else:
            buffer += char
    if buffer:
        yield buffer


def read_chars():
    """
    Reads characters one by one from standard input.

    Yields:
        str: A single character read from standard input.
    """

    try:
        char = sys.stdin.read(1)
        while char:
            yield char
            char = sys.stdin.read(1)
    except Exception as e:
        sys.stderr.write("I/O Error: " + str(e) + "\n")


def read_until(predicate: Callable[[str, str], bool], include_delimiter: bool = False):
    """
    Reads from standard input until a specified predicate condition is met.

    Args:
        predicate (Callable[[str, str], bool]): A function taking the current buffer
            and the latest character, returning True if reading should stop.
        include_delimiter (bool, optional): If True, includes the delimiting character
            in the yielded string. Defaults to False.

    Yields:
        str: Strings accumulated from standard input according to the predicate.
    """
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
    return read_until(lambda _, char: char.isspace() or char in ',.!?;:"()[]{}')


def read_sentences():
    return read_until(
        lambda buffer, char: char in ".!?"
        or (buffer.endswith("\n") and char == "\n")
        or (buffer.endswith("\r\n\r") and char == "\n"),
        include_delimiter=True,
    )


def read_paragraphs():
    return read_until(
        lambda buffer, char: (buffer.endswith("\n") and char == "\n")
        or (buffer.endswith("\r\n\r") and char == "\n")
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
