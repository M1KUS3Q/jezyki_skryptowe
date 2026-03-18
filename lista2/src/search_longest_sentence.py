from common import read_sentences, read_words


if __name__ == "__main__":
    res = next(read_sentences())
    res_len = len(res)

    for sentence in read_sentences():
        if len(sentence) > len(res):
            res_len = len(sentence)
            res = sentence

    print(res)
