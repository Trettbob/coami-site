"""Generate reviewable page pins; NEVER run automatically in CI or update digests.

Usage: python3 -I -B scripts/generate_page_pins.py --source ../in/base --destination legal/page-pins
Copy the printed digest mapping into page_pins.py only after reviewing the source.
"""
import argparse
import hashlib
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from site_common import HTML_PAGES, read_page
from page_pins import skeleton_bytes, head_bytes, head_errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--destination', type=Path, required=True)
    args = parser.parse_args()
    pins = {}
    for name in HTML_PAGES:
        page = read_page(args.source / name)
        if page.errors or head_errors(page):
            parser.error(f'{name}: {page.errors + head_errors(page)}')
        pins[name] = (skeleton_bytes(page), head_bytes(page))
    args.destination.mkdir(parents=True, exist_ok=True)
    for index, (mapping, suffix) in enumerate((('PAGE_SHA256', '.txt'),
                                               ('HEAD_SHA256', '.head.txt'))):
        print(mapping + ' = {')
        for name, data in pins.items():
            (args.destination / (name + suffix)).write_bytes(data[index])
            print(f'    {name!r}: {hashlib.sha256(data[index]).hexdigest()!r},')
        print('}')


if __name__ == '__main__':
    main()
