import os
import sys

if __name__ == "__main__":
    args = [arg.lower() for arg in sys.argv[1:]]
    matched_env_keys = set()

    for env_key in os.environ:
        if not args:
            matched_env_keys.add(env_key)
            continue

        for arg in args:
            if arg in env_key.lower():
                matched_env_keys.add(env_key)

    # sorting and formatting KEY=VALUE
    for env_key in sorted(matched_env_keys):
        print(f"{env_key}={os.environ[env_key]}")
