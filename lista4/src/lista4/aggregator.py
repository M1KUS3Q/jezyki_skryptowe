import sys
import os
import json
import subprocess
from collections import Counter

if __name__ == "__main__":
    # check if directory arg is provided
    if len(sys.argv) != 2:
        print("usage: python aggregator.py <directory_path>")
        sys.exit(1)

    target_dir = sys.argv[1]
    analyzer_script = os.path.join(os.path.dirname(__file__), "analyzer.py")

    file_paths = []

    # gather all file paths from the directory
    if os.path.exists(target_dir) and os.path.isdir(target_dir):
        for filename in os.listdir(target_dir):
            full_path = os.path.join(target_dir, filename)
            if os.path.isfile(full_path):
                file_paths.append(full_path)

    if not file_paths:
        print("no files to process.")
        sys.exit(0)

    results = []  # task d.iii: list of dictionaries
    total_files = 0
    total_chars = 0
    total_words = 0
    total_lines = 0

    # counters to track the "winners" from each file
    top_chars = Counter()
    top_words = Counter()

    # Run analyzer once per file and aggregate successful results.
    for file_path in file_paths:
        process = subprocess.run(
            [sys.executable, analyzer_script, file_path],
            text=True,
            capture_output=True,
        )

        line = process.stdout.strip()
        if not line:
            continue

        try:
            data = json.loads(line)

            # skip errors returned by child
            if "error" in data:
                continue

            # append dictionary to results list
            results.append(data)

            # aggregate stats
            total_files += 1
            total_chars += data["char_count"]
            total_words += data["word_count"]
            total_lines += data["line_count"]

            # collect most frequent items from this specific file
            if data["most_frequent_char"]:
                top_chars.update([data["most_frequent_char"]])
            if data["most_frequent_word"]:
                top_words.update([data["most_frequent_word"]])

        except json.JSONDecodeError:
            pass  # ignore invalid json output

    # determine overall most frequent items
    global_best_char = top_chars.most_common(1)[0][0] if top_chars else None
    global_best_word = top_words.most_common(1)[0][0] if top_words else None

    # prepare and print final summary (task d.iv)
    summary = {
        "files_read": total_files,
        "total_chars": total_chars,
        "total_words": total_words,
        "total_lines": total_lines,
        "most_frequent_char_overall": global_best_char,
        "most_frequent_word_overall": global_best_word,
    }

    print(json.dumps(summary, indent=4, ensure_ascii=False))
