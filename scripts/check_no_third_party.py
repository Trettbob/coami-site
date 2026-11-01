"""Enforce Security's static content, navigation, resource and exact CSP rules."""
import argparse
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))
from site_common import (ROOT, SVG_ATTRIBUTES, SVG_ELEMENTS, css_code,
                         discovery_errors, read_page, site_files)

from allowlist import CSP, exact

# These are the current pages' complete absolute navigation destinations.
ABSOLUTE_LINKS = {
    'https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement',
    'https://ico.org.uk/make-a-complaint/',
    'mailto:hello@coami.ai',
    'mailto:hello@coami.ai?subject=CoAmi%20pilot',
    'mailto:privacy@coami.ai',
    'mailto:security@coami.ai',
}
RESOURCE_TAGS = {'link', 'script', 'img', 'image', 'use', 'iframe', 'object',
                 'embed', 'audio', 'video', 'source', 'track', 'input', 'style', 'base'}
FONT_FACE = '@font-face{font-family:"Urbanist";src:url(fonts/urbanist-latin-var.woff2) format("woff2");font-weight:100 900;font-display:swap}'
LINK_RELS = {'preload', 'prefetch', 'preconnect', 'dns-prefetch', 'modulepreload', 'manifest'}


def relative_url(value):
    # Reject browser normalization ambiguities rather than interpreting them.
    if re.search(r'[\x00-\x20\x7f\\]', value):
        return False
    try:
        url = urlsplit(value)
        return not url.scheme and not url.netloc and not value.startswith('//')
    except ValueError:
        return False


def navigation_allowed(value):
    if relative_url(value):
        return True
    try:
        url = urlsplit(value)
        # Exact URL membership includes scheme, host and port; no hostname-only
        # comparison, protocol-relative exception or default-port normalization.
        origin = (url.scheme, url.hostname, url.port)
        return value in ABSOLUTE_LINKS and (origin in {
            ('https', 'docs.github.com', None), ('https', 'ico.org.uk', None),
            ('mailto', None, None)})
    except ValueError:
        return False


def check(root):
    root = Path(root).resolve()
    errors = discovery_errors(root)
    for path in site_files(root):
        page = read_page(path)
        name = path.relative_to(root)
        errors.extend(f'{name}: {e}' for e in page.errors)
        if page.processing_instructions:
            errors.append(f'{name}: forbidden XML processing instruction')
        policies = []
        heads = [n for n in page.nodes if n.tag == 'head']
        active_head = (heads[0] if len(heads) == 1 and heads[0].parent.tag == 'html'
                       and heads[0].parent.parent is page.root
                       and not any(n.tag == 'body' for n in page.nodes[:page.nodes.index(heads[0])])
                       else None)
        loaded = False
        for node in page.nodes:
            tag, attrs, attr = node.tag, node.attrs, node.attr
            location = f'{name}:{node.line}'
            svg = path.suffix.lower() == '.svg' or any(n.tag == 'svg' for n in node.ancestors())
            if svg:
                if tag not in {t.lower() for t in SVG_ELEMENTS}:
                    errors.append(f'{location}: forbidden <{tag}> SVG element')
                for key, value in attrs:
                    if key not in {a.lower() for a in SVG_ATTRIBUTES}:
                        errors.append(f'{location}: forbidden SVG attribute {key}')
            for key, value in attrs:
                if key in {'srcset', 'poster', 'ping'}:
                    errors.append(f'{location}: forbidden resource vector {key}')
                if value is None:
                    continue
                navigation = not svg and tag == 'a' and key == 'href'
                if key in {'src', 'action', 'data', 'href', 'xlink:href'} and not navigation:
                    if not relative_url(value):
                        errors.append(f'{location}: forbidden resource URL {value!r}')
                if svg and tag == 'image' and key in {'href', 'xlink:href'}:
                    errors.append(f'{location}: forbidden SVG image reference')
                if svg and tag == 'use' and key in {'href', 'xlink:href'}:
                    errors.append(f'{location}: forbidden off-document SVG use')
                if navigation and not navigation_allowed(value):
                    errors.append(f'{location}: forbidden navigation URL {value!r}')
                if re.search(r'url\s*\(', css_code(value), re.I):
                    errors.append(f'{location}: forbidden CSS resource vector in attribute {key}')
            if tag == 'link' and LINK_RELS.intersection((attr.get('rel') or '').lower().split()):
                errors.append(f'{location}: forbidden link resource hint')
            if tag == 'meta':
                equiv = (attr.get('http-equiv') or '').strip().lower()
                if equiv == 'refresh':
                    errors.append(f'{location}: forbidden meta refresh')
                if attr.get('http-equiv') == 'Content-Security-Policy':
                    policies.append(node)
                    if (not exact(node, 'content', CSP) or not (attr.get('content') or '').isascii() or
                            sum(k == 'content' for k, v in attrs) != 1):
                        errors.append(f'{location}: CSP content must be byte-exact ASCII policy')
                    if (node.parent is not active_head or
                            any(n.tag in {'template', 'noscript'} for n in node.ancestors()) or loaded):
                        errors.append(f'{location}: CSP must be active, direct child of head, before resources')
            if tag in RESOURCE_TAGS:
                loaded = True
        # SVG favicon is a constrained image, not an HTML page: meta CSP is not
        # effective in SVG. Scan all resource vectors but require CSP on HTML.
        if path.suffix.lower() != '.svg' and len(policies) != 1:
            errors.append(f'{name}: expected exactly one CSP meta (found {len(policies)})')
        for css in page.css:
            if re.search(r'url\s*\(|(?:-webkit-)?image-set\s*\(|@import\b', css_code(css), re.I):
                errors.append(f'{name}: forbidden CSS resource vector')
    for path in site_files(root, '.css'):
        css = css_code(path.read_text(encoding='utf-8'))
        # Exempt only the single exact approved declaration in the root CSS.
        if path == root / 'style.css' and css.count(FONT_FACE) == 1:
            css = css.replace(FONT_FACE, '', 1)
        if re.search(r'url\s*\(|(?:-webkit-)?image-set\s*\(|@import\b|@font-face\b', css, re.I):
            errors.append(f'{path.relative_to(root)}: forbidden CSS resource vector')
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', nargs='?', type=Path, default=ROOT)
    errors = check(parser.parse_args().root)
    print('\n'.join(errors) if errors else 'PASS: resources, navigation, static content and CSP')
    return bool(errors)


if __name__ == '__main__':
    raise SystemExit(main())
