"""Compare the visitor-visible privacy notice and links with approved D26."""
import argparse
import hashlib
import re
import sys
from html import unescape
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from site_common import ROOT, hidden, normalized, visible_text, discovery_errors, read_page, site_files
from check_invariants import footer_errors
from legal_visibility import visibility_errors
from legal_pins import pin_errors, pin_page

D26_SHA256 = '6842c06ee3bd94f90a16f4fe5b040b1454716e3a54f103cf2474a9075adc8852'
D26_PATH = Path('legal/D26-website-privacy-notice.md')
# A conservative visibility proof: approve CSS changes explicitly, rather than
# pretending that an offline HTML parser implements the browser CSS cascade.
CSS_SHA256 = '9221d0b9649615378c1d4b2d12dacaaab20ae61fd0ab346bde4da6fcbdb9d82b'
ICO = 'https://ico.org.uk/make-a-complaint/'
GITHUB_PRIVACY = 'https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement'
NOTICE_TAGS = {'html', 'body', 'main', 'div', 'article', 'h1', 'h2', 'p', 'ul',
               'li', 'a', 'strong', 'em'}


def markdown_text(text):
    # Match the shared extractor's boundaries around Markdown links, including
    # punctuation immediately after a link. No Legal source bytes change.
    text = re.sub(r'!?\[([^\]]*)\]\([^\n)]*\)', r' \1 ', text)
    text = re.sub(r'^\s{0,3}#{1,6}\s+', '', text, flags=re.M)
    text = re.sub(r'^\s*[-+*]\s+', '', text, flags=re.M)
    text = re.sub(r'([*_`~])', '', text)
    return unescape(text)


def notice_link_errors(page, main):
    errors = []
    ico = [n for n in page.nodes if n.tag == 'a' and normalized(visible_text(n)) == 'ICO'
           and main in list(n.ancestors())]
    if len(ico) != 1 or ico[0].attr.get('href') != ICO:
        errors.append('ICO link href must equal the D26 URL exactly')
    github = [n for n in page.nodes if n.tag == 'a' and normalized(visible_text(n)) == 'privacy statement'
              and main in n.ancestors()]
    if len(github) != 1 or github[0].attr.get('href') != GITHUB_PRIVACY:
        errors.append('privacy statement link href must equal the D26 URL exactly')
    return errors


def check(root):
    root = Path(root)
    errors = discovery_errors(root)
    pages = {p: read_page(p) for p in site_files(root)}
    for p, parsed in pages.items():
        if p.suffix.lower() != '.svg' and p != root / 'privacy.html' and any(n.tag == 'article' for n in parsed.nodes):
            errors.append(f'{p.name}: privacy notice is forbidden outside privacy.html')
        if p != root / 'privacy.html':
            errors.extend(f'{p.relative_to(root)}: {e}' for e in parsed.errors)
    if (root / 'privacy').exists():
        errors.append('Legacy privacy/ folder is forbidden')
    notice = root / D26_PATH
    if not notice.is_file():
        return errors + [f'Missing D26 notice: {D26_PATH}']
    raw = notice.read_bytes()
    if hashlib.sha256(raw).hexdigest() != D26_SHA256:
        errors.append('D26 sha256 differs from the approved public notice')
    path = root / 'privacy.html'
    if not path.is_file():
        return errors + ['Missing privacy page: privacy.html']
    page = pages[path]
    errors.extend(pin_errors(root, path, page, 'article'))
    approved = pin_page(root, 'article')
    if approved is None:
        errors.append('Missing or invalid approved privacy notice pin')
    elif normalized(visible_text(approved.root)) != normalized(markdown_text(raw.decode('utf-8'))):
        errors.append('Approved privacy pin text differs from D26')
    errors.extend(page.errors)
    mains = [n for n in page.nodes if n.tag == 'main']
    if len(mains) != 1 or not mains[0].closed:
        return errors + ['Privacy page must contain exactly one complete <main> element']
    main = mains[0]
    # Guard the complete notice and all ancestors. Decorative header SVG may
    # remain aria-hidden, and the approved CSS may hide the focusable skip link.
    notice_nodes = set(main.ancestors()) | {n for n in page.nodes if main in list(n.ancestors())}
    for n in notice_nodes:
        if not n.tag:
            continue
        if n.tag not in NOTICE_TAGS:
            errors.append(f'Privacy notice visibility is not approved: <{n.tag}> line {n.line}')
    errors.extend(visibility_errors(page, 'privacy.html', main, 'Privacy notice'))
    if approved is not None:
        errors.extend('Approved privacy pin: forbidden notice element' for n in approved.nodes
                      if n.tag not in NOTICE_TAGS | {'head', 'meta'})
        approved_main = next(n for n in approved.nodes if n.tag == 'main')
        errors.extend('Approved privacy pin: ' + e for e in notice_link_errors(approved, approved_main))
        errors.extend('Approved privacy pin: ' + e for e in
                      visibility_errors(approved, 'privacy.html', approved_main, 'Privacy notice'))
    css = root / 'style.css'
    if not css.is_file() or hashlib.sha256(css.read_bytes()).hexdigest() != CSS_SHA256:
        errors.append('Privacy visibility requires the approved style.css hash')
    stylesheets = [n.attr.get('href') for n in page.nodes
                   if n.tag == 'link' and 'stylesheet' in (n.attr.get('rel') or '').lower().split()]
    if stylesheets != ['style.css'] or any(n.tag == 'style' or 'style' in n.attr for n in page.nodes):
        errors.append('Privacy visibility requires only the approved stylesheet, no inline CSS')
    if normalized(visible_text(main)) != normalized(markdown_text(raw.decode('utf-8'))):
        errors.append('Privacy visible text differs from D26 exactly (whitespace only normalized)')
    errors.extend(notice_link_errors(page, main))
    headers = [n for n in page.nodes if n.tag == 'header']
    footers = [n for n in page.nodes if n.tag == 'footer']
    skips = [n for n in page.nodes if n.tag == 'a' and n.attr.get('class') == 'skip'
             and n.attr.get('href') == '#main' and normalized(visible_text(n)) == 'Skip to content']
    if len(headers) != 1 or normalized(visible_text(headers[0])) != 'Features How it works Pilot About Register interest':
        errors.append('Privacy header visible text must match the approved v5 navigation')
    brands = [n for n in page.nodes if n.tag == 'a' and n.attr.get('class') == 'brand'
              and any(h in n.ancestors() for h in headers)]
    expected_images = [
        {'class': 'brand-light', 'src': 'img/coami-logo.svg', 'alt': 'CoAmi'},
        {'class': 'brand-dark', 'src': 'img/coami-logo-light-on-dark.svg', 'alt': 'CoAmi'},
    ]
    if (len(brands) != 1 or brands[0].attr !=
            {'class': 'brand', 'href': 'index.html', 'aria-label': 'CoAmi home'} or
            [n.attr if not isinstance(n, str) and n.tag == 'img' else None
             for n in brands[0].children] != expected_images):
        errors.append('Privacy header brand must match the approved theme images and home link')
    errors.extend(footer_errors(page, 'privacy.html'))
    # Exact mock footer navigation is outside the immutable Legal footer.
    bands = [n for n in page.nodes if n.attr.get('class') == 'wrap footer-top']
    expected_band = '<div class="wrap footer-top"><a class="brand" href="index.html" aria-label="CoAmi home"><img class="brand-light" src="img/coami-logo.svg" alt="CoAmi"><img class="brand-dark" src="img/coami-logo-light-on-dark.svg" alt="CoAmi"></a><nav aria-label="Footer"><a href="index.html">Home</a><a href="contact.html">Contact</a><a href="privacy.html" aria-current="page">Privacy</a></nav></div>'
    # Strict tokens plus exact serialization prevent extra text/links in the band.
    def markup(n):
        return n.raw + ''.join(c if isinstance(c, str) else markup(c) for c in n.children) + '</' + n.tag + '>' if n.tag not in {'img', 'meta', 'link'} else n.raw
    if len(bands) != 1 or markup(bands[0]) != expected_band:
        errors.append('Privacy footer navigation must match the approved v5 markup')
    permitted = {main, *headers, *footers, *skips, *bands}

    def outside(n):
        if n in permitted or hidden(n):
            return ''
        return ''.join(c if isinstance(c, str) else outside(c) for c in n.children)

    if normalized(outside(page.root)):
        errors.append('Extra visible text outside privacy main/header/footer/skip link')
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', nargs='?', type=Path, default=ROOT)
    errors = check(parser.parse_args().root)
    print('\n'.join(errors) if errors else 'PASS: visitor-visible privacy text and D26 links')
    return bool(errors)


if __name__ == '__main__':
    raise SystemExit(main())
