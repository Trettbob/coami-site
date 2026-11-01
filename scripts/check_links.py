"""Check local HTML/CSS references without making network requests."""
import argparse
from pathlib import Path
from urllib.parse import unquote, urlsplit

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))

from site_common import ROOT, Page, css_references, site_files, discovery_errors, read_page


def check(root):
    root = Path(root).resolve()
    errors = discovery_errors(root)
    pages = {p.resolve(): read_page(p)
             for p in site_files(root)}
    for path, page in pages.items():
        errors.extend(f'{path.relative_to(root)}: {e}' for e in page.errors)

    def reference(source, value, location):
        value = value.strip()
        try:
            url = urlsplit(value)
        except ValueError:
            errors.append(f'{location}: invalid URL {value!r}')
            return
        if url.scheme.lower() == 'mailto':
            address = unquote(url.path)
            if not address or any(not part.strip() or '@' not in part or
                                  not all(part.rsplit('@', 1))
                                  for part in address.split(',')):
                errors.append(f'{location}: mailto needs an address: {value!r}')
            return
        if url.scheme or url.netloc:
            return  # External URLs are never fetched; resource policy is checked separately.
        path = unquote(url.path)
        target = ((root / path.lstrip('/')) if path.startswith('/')
                  else source.parent / path) if path else source
        target = target.resolve()
        if not target.is_relative_to(root):
            errors.append(f'{location}: path leaves repository: {value!r}')
            return
        if target.is_dir():
            target = target / 'index.html'
        if not target.is_file():
            errors.append(f'{location}: missing file: {value!r}')
        elif url.fragment:
            page = pages.get(target)
            if page is None and target.suffix.lower() == '.html':
                page = Page(target.read_text(encoding='utf-8'))
            if page is None or unquote(url.fragment) not in page.ids:
                errors.append(f'{location}: missing fragment: {value!r}')

    for path, page in pages.items():
        name = path.relative_to(root)
        for tag, attrs, line in page.elements:
            for key, value in attrs:
                if key in {'href', 'src'} and value is not None:
                    reference(path, value, f'{name}:{line}')
        for css in page.css:
            for value in css_references(css):
                reference(path, value, str(name))
    for path in site_files(root, '.css'):
        for value in css_references(path.read_text(encoding='utf-8')):
            reference(path, value, str(path.relative_to(root)))
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', nargs='?', type=Path, default=ROOT)
    args = parser.parse_args()
    errors = check(args.root)
    print('\n'.join(errors) if errors else 'PASS: local links and fragments')
    return bool(errors)


if __name__ == '__main__':
    raise SystemExit(main())
