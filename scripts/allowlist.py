"""Owner-reviewed markup vocabulary shared by every content check.

Derived from the approved v5 HTML, retaining r4's SVG element vocabulary. Changes
need owner review (/scripts/ is owned in CODEOWNERS), including later P2/P3
pages, fonts/*.woff2, navigation or inline SVG marks. Extend these data tables
and the corresponding resource/visibility/discovery policies together.
"""

# Attribute names use the strict tokenizer's ASCII-lowercase representation.
HTML_ATTRIBUTES = {
    'a': {'aria-label', 'aria-current', 'class', 'href'},
    'article': {'class'}, 'body': set(), 'div': {'class'},
    'footer': {'class'}, 'h1': {'id'}, 'h2': {'class', 'id'}, 'h3': set(),
    'head': set(), 'header': {'class'}, 'html': {'lang'}, 'li': {'class'},
    'img': {'src', 'alt', 'class', 'width', 'height'},
    'link': {'href', 'rel', 'type', 'sizes'}, 'main': {'id', 'tabindex'},
    'meta': {'charset', 'content', 'http-equiv', 'name'},
    'nav': {'aria-label'}, 'ol': {'class'}, 'p': {'class'},
    'section': {'aria-labelledby', 'id', 'class'}, 'span': {'class'},
    'title': set(), 'ul': {'class'},
}
# Preserve r4's SVG XML policy (XML names are case-sensitive). Per-element
# attribute sets below narrow this vocabulary for both inline and XML SVG.
SVG_ELEMENTS = {'svg', 'g', 'rect', 'text', 'circle', 'ellipse', 'path', 'line',
                'polyline', 'polygon', 'title', 'desc', 'defs', 'clipPath'}
SVG_ATTRIBUTES = {'id', 'class', 'role', 'aria-hidden', 'aria-label', 'aria-labelledby',
                  'focusable', 'viewBox', 'width', 'height', 'x', 'y', 'rx', 'ry',
                  'cx', 'cy', 'r', 'd', 'points', 'x1', 'y1', 'x2', 'y2',
                  'fill', 'fill-rule', 'stroke', 'stroke-width', 'stroke-linecap',
                  'stroke-linejoin', 'opacity', 'transform', 'clip-path',
                  'font-family', 'font-size', 'font-weight', 'text-anchor'}
SVG_ELEMENT_ATTRIBUTES = {
    **{tag.lower(): set() for tag in SVG_ELEMENTS},
    'svg': {'aria-hidden', 'class', 'focusable', 'viewbox', 'role', 'aria-label'},
    'rect': {'fill', 'height', 'rx', 'width', 'x', 'y'},
    'path': {'d', 'fill', 'class'},
    'text': {'fill', 'font-family', 'font-size', 'font-weight', 'text-anchor', 'x', 'y'},
    'circle': {'class', 'cx', 'cy', 'fill', 'r'},
}
# Approved v5 relative resources and Security ruling addendum 2 CSP.
CSP = "default-src 'self'; img-src 'self' data:; style-src 'self'; font-src 'self'; script-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'"
STYLESHEET = 'style.css'
FAVICON = 'coami-icon.svg'
# Q-039 M3: exact icon markup, in order, directly in each page's head.
ICON_LINKS = (
    '<link rel="icon" href="favicon.ico" sizes="48x48">',
    '<link rel="icon" href="coami-icon.svg" type="image/svg+xml">',
    '<link rel="apple-touch-icon" href="apple-touch-icon.png">',
)
# Q-036/D1 header logos and Q-039 M3 icons: immutable source bytes.
IMAGE_HASHES = {
    'img/coami-logo.svg': '527ee10f422218feb0e9502118f307344af463c02e4f1f2dde941467e2381b9f',
    'img/coami-logo-light-on-dark.svg': '8ec03393a75f01463c117703c952cc681495417007fed5901866cdeccbbcd31b',
    'favicon.ico': 'bfc15f77ff3ae64db194b62f091e77f9f3be2b801c635b0274a1391b511f65aa',
    'coami-icon.svg': '8434ecc8523aa9902a6a604b329292b30dd7a6458b26239b72e039393b5c8d9d',
    'apple-touch-icon.png': 'caed8633b8439dac826370cf9275496e43c879cc184d8fe2c085edbd85b6645f',
}

def exact(node, key, expected):
    # Original spellings and decoded values come from the SAME tokenizer.
    values = [value for name, value in node.raw_attrs if name == key]
    return node.attr.get(key) == expected and values == [expected]


def vocabulary_errors(node, svg=False):
    table = SVG_ELEMENT_ATTRIBUTES if svg else HTML_ATTRIBUTES
    errors = []
    if node.tag not in table:
        errors.append(f'line {node.line}: forbidden <{node.tag}> element (markup allowlist)')
    for key, value in node.attrs:
        if key not in table.get(node.tag, set()):
            errors.append(f'line {node.line}: forbidden attribute {key} on <{node.tag}> (markup allowlist)')
    return errors


def page_errors(page, document=True):
    """Fail closed for the entire parsed HTML document, including inert trees."""
    errors = []
    if not document:
        for node in page.nodes:
            svg = any(n.tag == 'svg' for n in node.ancestors())
            errors.extend(vocabulary_errors(node, svg))
        return errors
    htmls = [n for n in page.nodes if n.tag == 'html']
    if len(htmls) != 1 or not exact(htmls[0], 'lang', 'en-GB'):
        errors.append('Markup allowlist: html lang must be byte-exact en-GB, exactly once')
    policies, referrers, stylesheets, icons = [], [], [], []
    for node in page.nodes:
        attr = node.attr
        if node.tag == 'img':
            if not any(exact(node, 'src', name) for name in IMAGE_HASHES):
                errors.append('Markup allowlist: img src must be byte-exact in pinned image set')
        if node.tag == 'meta':
            if 'http-equiv' in attr:
                policies.append(node)
                if not exact(node, 'http-equiv', 'Content-Security-Policy'):
                    errors.append('Markup allowlist: http-equiv must be byte-exact Content-Security-Policy')
                if not exact(node, 'content', CSP):
                    errors.append('Markup allowlist: CSP content must be byte-exact ASCII policy')
            if (attr.get('name') or '').strip().lower() == 'referrer':
                referrers.append(node)
                if not exact(node, 'name', 'referrer') or not exact(node, 'content', 'no-referrer'):
                    errors.append('Markup allowlist: referrer must be byte-exact no-referrer')
        if node.tag == 'link':
            if exact(node, 'rel', 'stylesheet'):
                stylesheets.append(node)
                if not exact(node, 'href', STYLESHEET):
                    errors.append('Markup allowlist: stylesheet href must be byte-exact ' + STYLESHEET)
            elif exact(node, 'rel', 'icon') or exact(node, 'rel', 'apple-touch-icon'):
                icons.append(node)
                if not any(exact(node, 'href', name) for name in IMAGE_HASHES):
                    errors.append('Markup allowlist: icon href must be byte-exact in pinned image set')
            else:
                errors.append('Markup allowlist: link rel must be byte-exact stylesheet or icon or apple-touch-icon')
    if tuple(n.raw for n in icons) != ICON_LINKS:
        errors.append('Markup allowlist: expected exact three icon links in order')
    if any(n.parent.tag != 'head' for n in icons):
        errors.append('Markup allowlist: icon links must be direct children of head')
    if len(policies) != 1:
        errors.append('Markup allowlist: expected exactly one CSP meta')
    if len(referrers) != 1:
        errors.append('Markup allowlist: expected exactly one referrer meta')
    if len(stylesheets) != 1:
        errors.append('Markup allowlist: expected exactly one stylesheet on every page')
    return errors
