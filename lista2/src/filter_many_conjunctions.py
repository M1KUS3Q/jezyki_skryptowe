from common import read_sentences, split_scalar

if __name__ == "__main__":
    CONJUNCTIONS = ["i", "oraz", "ale", "że", "lub"]

    for sentence in read_sentences():
        count = 0

        for conjunction in CONJUNCTIONS:
            if conjunction in split_scalar(sentence.lower()):
                count += 1

        if count >= 2:
            print(sentence)
