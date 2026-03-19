from common import read_sentences


if __name__ == "__main__":
    for sentence in read_sentences():
        if sentence.count(" ") <= 4:
            print(sentence)
