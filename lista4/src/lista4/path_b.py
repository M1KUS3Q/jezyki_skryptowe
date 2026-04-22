import os


def b():
    for dirpath in os.getenv("PATH").split(os.pathsep):
        print(f"Directory: {dirpath}")
        try:
            for filename in os.listdir(dirpath):
                filepath = os.path.join(dirpath, filename)
                if os.path.isfile(filepath) and os.access(filepath, os.X_OK):
                    print(f" - {filename}")
        except FileNotFoundError:
            pass
        except PermissionError:
            pass
        print()


if __name__ == "__main__":
    b()
