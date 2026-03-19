import subprocess
import sys
import os

SCRIPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "src")


def run_script(script_name: str, input_text: str) -> str:
    script_path = os.path.join(SCRIPTS_DIR, script_name)
    result = subprocess.run(
        [sys.executable, script_path],
        input=input_text,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.returncode != 0:
        print(f"Error running {script_name}:\n{result.stderr}", file=sys.stderr)
    result.check_returncode()
    return result.stdout.strip()


def test_extract_text():
    # Needs a 10-line preamble (or one ending in \r\n\r\n\r\n etc.) followed by text ending with -----
    input_text = "Line 1\nLine 2\nLine 3\n\n\nHello World!-----"
    output = run_script("extract_text.py", input_text)
    assert output == "Hello World!"


def test_filter_first_20():
    input_text = ".\n".join([f"Sentence {i}" for i in range(1, 25)]) + "."
    output = run_script("filter_first_20.py", input_text)
    lines = output.splitlines()
    assert len(lines) == 20
    assert lines[0] == "Sentence 1."
    assert lines[19] == "Sentence 20."


def test_filter_many_conjunctions():
    input_text = "To jest test i sprawdzanie, oraz weryfikacja.\nTo tylko jedno i nic wiecej.\nAle to, lub tamto, że tak."
    output = run_script("filter_many_conjunctions.py", input_text)
    lines = output.splitlines()
    assert len(lines) == 2
    assert lines[0] == "To jest test i sprawdzanie, oraz weryfikacja."
    assert lines[1] == "Ale to, lub tamto, że tak."


def test_filter_questions_exclaims():
    input_text = "Is this a question? Yes it is. Awesome! Standard sentence."
    output = run_script("filter_questions_exclaims.py", input_text)
    lines = output.splitlines()
    assert len(lines) == 2
    assert lines[0] == "Is this a question?"
    assert lines[1] == "Awesome!"


def test_filter_short_sentences():
    input_text = "One two three.\nOne two three four five six.\nShort one here."
    output = run_script("filter_short_sentences.py", input_text)
    lines = output.splitlines()
    assert len(lines) == 2
    assert "One two three." in lines
    assert "Short one here." in lines


def test_reduce_count_chars():
    input_text = "a b c \n d"
    # non-space chars: 'a', 'b', 'c', 'd' -> 4
    output = run_script("reduce_count_chars.py", input_text)
    assert output == "4"


def test_reduce_count_paragraphs():
    input_text = "Para 1\nline 2\n\nPara 2\n\nPara 3"
    output = run_script("reduce_count_paragraphs.py", input_text)
    assert output == "3"


def test_reduce_proper_noun_sentences():
    # sentence 1: "John went." (first word capitalized, no properly capitalized word inside) -> 0
    # sentence 2: "the boy John went." ('John' is capitalized inside) -> 1
    input_text = "John went.\nThe boy John went.\nShe saw Mary there."
    # 3 sentences total, 2 contain proper noun (not counting first word)
    output = run_script("reduce_proper_noun_sentences.py", input_text)
    assert output == str(2 / 3)


def test_search_longest_sentence():
    input_text = "Short.\nThis is a remarkably long sentence.\nMedium sentence."
    output = run_script("search_longest_sentence.py", input_text)
    assert output == "This is a remarkably long sentence."


def test_search_longest_varied_sentence():
    # The varied sentence means words cannot start with the same letter consecutively.
    # sentence 1: valid
    # sentence 2: not valid (same same)
    input_text = "A big cat dies.\nSam saw some small swans."
    output = run_script("search_longest_varied_sentence.py", input_text)
    assert output == "A big cat dies."


def test_search_subordinate_clauses():
    input_text = "Here is one, with multiple, commas, to be found.\nOnly one, comma."
    output = run_script("search_subordinate_clauses.py", input_text)
    assert output == "Here is one, with multiple, commas, to be found."


def test_pipeline():
    # Testing cat data/calineczka.txt | python src/extract_text.py | python src/filter_many_conjunctions.py
    # using our run_script
    calineczka_path = os.path.join(
        os.path.dirname(SCRIPTS_DIR), "data", "calineczka.txt"
    )
    if os.path.exists(calineczka_path):
        with open(calineczka_path, "r", encoding="utf-8") as f:
            content = f.read()

        extracted = run_script("extract_text.py", content)
        assert len(extracted) > 0

        conjunctions = run_script("filter_many_conjunctions.py", extracted)
        assert len(conjunctions) > 0
