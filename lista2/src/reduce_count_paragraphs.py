from common import read_paragraphs

if __name__ == "__main__":
    paragraphs = read_paragraphs()
    
    print(sum(1 for x in paragraphs if x.strip() != ""))