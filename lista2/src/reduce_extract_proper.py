from common import extract_preamble, read_sentences, split_scalar


if __name__ == "__main__":
    extract_preamble()

    for sentence in read_sentences():
        if sentence.startswith("-----"):
            break

        split = split_scalar(sentence)

        try:
            next(split)  # skip first word
        except Exception as _:
            continue

        for word in split:
            if word[0].isupper():
                print(word)