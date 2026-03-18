from common import read_sentences

if __name__ == "__main__":
    contain_proper_noun, total = 0, 0
    for sentence in read_sentences():
        total += 1
        if any(word.istitle() for word in sentence.split()[1:]):
            contain_proper_noun += 1

    print(contain_proper_noun / total)
