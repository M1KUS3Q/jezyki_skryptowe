import json
import os
import sys
from collections import Counter

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(
            json.dumps(
                {"error": "Usage: python -m lista4.analyzer <path_to_file>"},
                ensure_ascii=False,
            )
        )
        sys.exit(1)

    path = sys.argv[1].strip()

    if not path:
        print(
            json.dumps(
                {"error": "Path cannot be empty."},
                ensure_ascii=False,
            )
        )
        sys.exit(1)

    abs_path = os.path.abspath(path)

    char_count = 0
    word_count = 0
    line_count = 0
    char_counter = Counter()
    word_counter = Counter()

    try:
        with open(path, "r", encoding="utf-8") as plik:
            for line in plik:
                line_count += 1
                char_count += len(line)

                # Counts every char including white spaces.
                char_counter.update(line)

                words = line.split()
                word_count += len(words)
                word_counter.update(words)

    except FileNotFoundError:
        print(
            json.dumps(
                {"error": f"File doesn't exist: {abs_path}"},
                ensure_ascii=False,
            )
        )
        sys.exit(1)
    except Exception as e:
        print(
            json.dumps(
                {"error": f"Error reading file {abs_path}: {str(e)}"},
                ensure_ascii=False,
            )
        )
        sys.exit(1)

    most_freq_char = char_counter.most_common(1)[0][0] if char_counter else None
    most_freq_word = word_counter.most_common(1)[0][0] if word_counter else None

    result = {
        "absolute_path": abs_path,
        "char_count": char_count,
        "word_count": word_count,
        "line_count": line_count,
        "most_frequent_char": most_freq_char,
        "most_frequent_word": most_freq_word,
    }

    print(json.dumps(result, ensure_ascii=False))
