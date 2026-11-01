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
from page_pins import skeleton_bytes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--destination', type=Path, required=True)
    args = parser.parse_args()
    pins = {}
    for name in HTML_PAGES:
        page = read_page(args.source / name)
        if page.errors:
            parser.error(f'{name}: {page.errors}')
        pins[name] = skeleton_bytes(page)
    args.destination.mkdir(parents=True, exist_ok=True)
    print('PAGE_SHA256 = {')
    for name, data in pins.items():
        (args.destination / (name + '.txt')).write_bytes(data)
        print(f'    {name!r}: {hashlib.sha256(data).hexdigest()!r},')
    print('}')


if __name__ == '__main__':
    main()
