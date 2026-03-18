from common import read_sentences


if __name__ == "__main__":
    sentences = read_sentences()
    for _ in range(20):
        print(next(sentences))
