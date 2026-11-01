"""Check Pages metadata, Legal's footer and the design note's banned copy."""
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from site_common import ROOT, discovery_errors, normalized, read_page, site_files, visible_text, copy_text
from legal_visibility import visibility_errors
from legal_pins import pin_errors, pin_page

FOOTER = 'Trett Labs Limited. Registered in England and Wales, company number 17310137. Registered office: The 1812 Building, Wheatley Park, Mirfield, West Yorkshire, WF14 8HE. hello@coami.ai · ICO registration ZC276667 · Privacy'
BANNED = re.compile(r'\b(?:MFA|2FA|TOTP|WebAuthn|OTP|secure|compliant|GDPR|certified|UK-hosted|testimonials?)\b|®|\b[0-9][0-9,]*\s+(?:users|customers|workspaces)\b', re.I)


def footer_errors(page, name):
    footers = [n for n in page.nodes if n.tag == 'footer']
    if len(footers) != 1 or normalized(visible_text(footers[0])) != FOOTER:
        return ['Legal footer text must be exact and visible, exactly once']
    errors = visibility_errors(page, name, footers[0], 'Legal footer')
    links = [(normalized(visible_text(n)), n.attr.get('href')) for n in page.nodes
             if n.tag == 'a' and footers[0] in list(n.ancestors())]
    if links != [('hello@coami.ai', 'mailto:hello@coami.ai'), ('Privacy', 'privacy.html')]:
        errors.append('Legal footer links must be exact')
    return errors


def check(root):
    root = Path(root)
    errors = discovery_errors(root)
    cname = root / 'CNAME'
    if not cname.is_file() or cname.read_bytes() not in {b'coami.ai', b'coami.ai\n'}:
        errors.append('CNAME must be exactly coami.ai with optional newline')
    nojekyll = root / '.nojekyll'
    if not nojekyll.is_file() or nojekyll.read_bytes() != b'':
        errors.append('.nojekyll must exist and be empty')
    if (root / 'privacy').exists():
        errors.append('Legacy privacy/ folder is forbidden')
    approved = pin_page(root, 'footer')
    if approved is None:
        errors.append('Missing or invalid approved footer pin')
    else:
        errors.extend('Approved footer pin: ' + e for e in footer_errors(approved, 'index.html'))
    for path in site_files(root):
        page = read_page(path)
        name = str(path.relative_to(root))
        errors.extend(f'{name}: {e}' for e in page.errors)
        if path.suffix.lower() != '.svg':
            errors.extend(f'{name}: {e}' for e in footer_errors(page, name))
            errors.extend(pin_errors(root, path, page, 'footer'))
        for match in BANNED.finditer(normalized(copy_text(page.root))):
            errors.append(f'{name}: banned visible copy: {match[0]!r}')
        public_copy = []
        for node in page.nodes:
            if node.tag == 'title':
                public_copy.append(''.join(c for c in node.children if isinstance(c, str)))
            if node.tag == 'meta':
                key = (node.attr.get('name') or '').lower()
                prop = (node.attr.get('property') or '').lower()
                if key == 'description' or key.startswith(('og:', 'twitter:')) or prop.startswith(('og:', 'twitter:')):
                    public_copy.append(node.attr.get('content') or '')
            public_copy.extend(value for key, value in node.attrs
                               if key in {'alt', 'title', 'aria-label'} and value)
        for value in public_copy:
            for match in BANNED.finditer(normalized(value)):
                errors.append(f'{name}: banned public metadata/attribute copy: {match[0]!r}')
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', nargs='?', type=Path, default=ROOT)
    errors = check(parser.parse_args().root)
    print('\n'.join(errors) if errors else 'PASS: Pages metadata, Legal footers and banned copy')
    return bool(errors)


if __name__ == '__main__':
    raise SystemExit(main())
