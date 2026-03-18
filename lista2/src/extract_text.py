from common import extract_preamble, read_contents

if __name__ == "__main__":
    extract_preamble()
    text = next(read_contents())[:-5]  # remove the trailing "-----"
    print(text)
