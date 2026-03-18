from common import extract_preambule, read_contents

if __name__ == "__main__":
    extract_preambule()
    text = next(read_contents())[:-5]  # remove the trailing "-----"
    print(text)
