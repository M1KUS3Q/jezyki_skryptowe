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

def read_until(predicate: Callable[[str, str], bool]):
    buffer = ""
    for char in read_chars():
        should_end = predicate(buffer, char)
        if not should_end:
            buffer += char
            continue
        
        cleaned = buffer.strip()
        if cleaned:
            yield cleaned
        buffer = ""
    yield buffer.strip()

def read_words():
    return read_until(lambda _, char: char.isspace())
        
def read_sentences():
    return read_until(lambda _, char: char in ".!?")
        
def read_paragraphs():
    return read_until(lambda buffer, _: buffer.endswith("\n\n") or buffer.endswith("\r\n\r\n"))

def read_contents():
    return read_until(lambda buffer, _: buffer.endswith("-----"))


# TODO: rewrite this to not consume lines (requiring seek) if the preambule is not found.
def extract_preambule() -> Optional[str]:
    PREAMBULE_ESCAPES = ["\r\n" * 3, "\n" * 3]
    lines = ""
    stream = sys.stdin
    
    for _ in range(10):
        line = stream.readline()
        if not line:
            break
        
        lines += line
        
        if any(lines.endswith(escape) for escape in PREAMBULE_ESCAPES):
            return lines
    
    # if we reach this point, it means we have read 10 lines without finding the end of the preambule
    # we reset the stream to the beginning to not consume any lines that might be part of the actual text
    stream.seek(0)
    return None