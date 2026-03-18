from common import read_chars

if __name__ == "__main__":
    print(sum(1 for x in read_chars() if not x.isspace()))
        