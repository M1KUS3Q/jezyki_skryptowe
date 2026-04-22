import os


def a():
    for path in os.getenv("PATH").split(os.pathsep):
        print(path)


if __name__ == "__main__":
    a()
