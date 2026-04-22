import os
from pathlib import Path
import sys


import sys
import os
import json
from collections import Counter

if __name__ == "__main__":
    for path in sys.stdin:
        path = path.strip()
        
        # ignore empty lines
        if not path:
            continue
            
        abs_path = os.path.abspath(path)
        
        char_count = 0
        word_count = 0
        line_count = 0
        char_counter = Counter()
        word_counter = Counter()
        
        try:
            with open(path, 'r', encoding='utf-8') as plik:
                for line in plik:
                    line_count += 1
                    char_count += len(line)
                    
                    # counts every char including white spaces
                    char_counter.update(line)
                    
                    words = line.split() # list of words
                    word_count += len(words)
                    word_counter.update(words)
                    
        except FileNotFoundError:
            # if file does not exist, print error (in json) and move on to the next path
            print(json.dumps({"error": f"File doesn't exist: {abs_path}"}, ensure_ascii=False))
            continue
        except Exception as e:
            print(json.dumps({"error": f"Error reading file {abs_path}: {str(e)}"}, ensure_ascii=False))
            continue

    
        most_freq_char = char_counter.most_common(1)[0][0] if char_counter else None
        most_freq_word = word_counter.most_common(1)[0][0] if word_counter else None

        result = {
            "absolute path": abs_path,
            "char count": char_count,
            "word count": word_count,
            "line count": line_count,
            "most frequent char": most_freq_char,
            "most frequent word": most_freq_word
        }
        
        print(json.dumps(result, ensure_ascii=False))
