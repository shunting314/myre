import sys
from myre import match

if __name__ == "__main__":
    argv = sys.argv[1:]
    if len(argv) != 2:
        print(f"Usage: <script> <pattern> <path>")
        sys.exit(1)

    pattern, path = argv

    print(f"Pattern is {pattern}")

    with open(path, 'r') as f:
        for line in f:
            line = line.rstrip()
            # TODO: only build the NFA once
            match_obj = match(pattern, line)
            if match_obj:
                print(match_obj.color_text())
            else:
                # print(line)
                pass
    print("bye")
