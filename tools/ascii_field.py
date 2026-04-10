"""Dump a sensory field as ascii art.

    python3 tools/ascii_field.py path/to/screenshot.png
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipeline import field_from_screenshot


def main(path):
    field = field_from_screenshot(path)
    print(field.ascii())


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        raise SystemExit(1)
    main(sys.argv[1])
