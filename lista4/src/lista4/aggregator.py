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
    analyzer_script = "analyzer.py" # path to the script from task a-c

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

    # prepare stdin payload (paths separated by newline)
    paths_input = "\n".join(file_paths) + "\n"

    # run child process and feed paths to its stdin
    process = subprocess.run(
        [sys.executable, analyzer_script],
        input=paths_input,
        text=True,
        capture_output=True
    )

    results = [] # task d.iii: list of dictionaries
    total_files = 0
    total_chars = 0
    total_words = 0
    total_lines = 0
    
    # counters to track the "winners" from each file
    top_chars = Counter()
    top_words = Counter()

    # parse child script output line by line
    for line in process.stdout.strip().split('\n'):
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
            total_chars += data["liczba_znakow"]
            total_words += data["liczba_slow"]
            total_lines += data["liczba_wierszy"]
            
            # collect most frequent items from this specific file
            if data["najczestszy_znak"]:
                top_chars.update([data["najczestszy_znak"]])
            if data["najczestsze_slowo"]:
                top_words.update([data["najczestsze_slowo"]])
                
        except json.JSONDecodeError:
            pass # ignore invalid json output

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
        "most_frequent_word_overall": global_best_word
    }
    
    print(json.dumps(summary, indent=4, ensure_ascii=False))