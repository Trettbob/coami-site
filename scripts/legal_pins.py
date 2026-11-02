"""Owner-reviewed Legal elements compared as exact UTF-8 bytes, no normalization.

Only these two .html files are raw baselines, never discovered as site pages.
Digests live in the trusted checker, never in candidate-controlled baselines.
The ordinary strict-subset parser and semantic Legal checks also validate them.
"""
import hashlib
import re
from site_common import Page

PINS = {'footer': 'legal/approved-footer.html',
        'article': 'legal/approved-privacy-notice.html'}
PIN_SHA256 = {
    'footer': 'e5d1ed29cf567fe379cee987346b0b60ee1b05967d5ff16b1ecd25ffc49982cf',
    'article': 'b8344c5f3e89d9f9dcf17cb9bff087fbf61dc827a73cd6eb1b8f7e572cef1a63',
}


def approved_bytes(root, tag):
    pin = root / PINS[tag]
    if not pin.is_file():
        return None
    raw = pin.read_bytes()
    if hashlib.sha256(raw).hexdigest() != PIN_SHA256[tag]:
        return None
    return raw


def element_bytes(raw, tag):
    return re.findall(rb'<' + tag.encode('ascii') + rb'\b[^>]*>.*?</' +
                      tag.encode('ascii') + rb'>', raw, re.S)


def pin_errors(root, path, page, tag):
    raw = approved_bytes(root, tag)
    if raw is None:
        return [f'{path.name}: Legal {tag} pin sha256 mismatch or missing']
    elements = [n for n in page.nodes if n.tag == tag]
    chunks = element_bytes(path.read_bytes(), tag)
    if (len(elements) != 1 or len(chunks) != 1 or chunks[0] != raw):
        return [f'{path.name}: Legal {tag} must occur exactly once and match its approved pin byte for byte']
    return []


def pin_page(root, tag):
    raw = approved_bytes(root, tag)
    if raw is None:
        return None
    if element_bytes(raw, tag) != [raw]:
        return None
    try:
        fragment = raw.decode('utf-8')
    except UnicodeDecodeError:
        return None
    if tag == 'article':
        fragment = '<main id="main"><div class="wrap">' + fragment + '</div></main>'
    if tag == 'footer':
        fragment = '<div class="footer-band">' + fragment + '</div>'
    page = Page('<!doctype html><html lang="en-GB"><head><meta charset="utf-8">'
                '</head><body>' + fragment + '</body></html>')
    if page.errors or sum(n.tag == tag for n in page.nodes) != 1:
        return None
    return page
