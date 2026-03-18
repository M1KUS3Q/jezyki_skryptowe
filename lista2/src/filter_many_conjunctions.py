from common import read_sentences

if __name__ == "__main__":
    CONJUNCTIONS = ["i", "oraz", "ale", "że", "lub"]

    for sentence in read_sentences():
        count = 0

        for conjunction in CONJUNCTIONS:
            if conjunction in sentence.lower().split():
                count += 1

        if count >= 2:
            print(sentence)
