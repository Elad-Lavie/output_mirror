import sys
import time
import datetime


def main():
    for i in range(int(sys.argv[1])):
        print(f"stdout: {i} {datetime.datetime.now()}")

        time.sleep(1)

        print(f"stderr: {i} {datetime.datetime.now()}", file=sys.stderr)

        time.sleep(1)

    print(f"stdout: done {datetime.datetime.now()}")


if __name__ == "__main__":
    main()
