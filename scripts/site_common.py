"""Offline discovery. With .nojekyll, Markdown is served raw, never rendered."""
import argparse
import hashlib
import re
import sys
from dataclasses import dataclass, field
from html import unescape
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
DOCUMENT_SUFFIXES = {'.html', '.htm', '.xhtml', '.svg'}
HTML_PAGES = ('index.html', 'features.html', 'how-it-works.html', 'pilot.html', 'about.html', 'contact.html', 'privacy.html', '404.html')
EXPECTED_DOCUMENTS = {*HTML_PAGES, 'coami-icon.svg',
                      'img/coami-logo.svg', 'img/coami-logo-light-on-dark.svg'}
FONT_HASHES = {
    'fonts/urbanist-latin-var.woff2': '0de96f83a43992027ec811e68a9ff1617580d3438cf6740448421683e66b4785',
    'fonts/OFL.txt': 'ee1221b1c2d08920e5f9ca764eb228dafa5c8090df9cf665373c2287b9cb8f49',
}
LEGAL_PINS = {'legal/approved-footer.html', 'legal/approved-privacy-notice.html'}
GITHUB_FILES = {'.github/CODEOWNERS', '.github/workflows/site-checks.yml'}
# Source/config/data files are raw downloads with .nojekyll. No executable or
# additional browser document formats are supported by these static checks.
RAW_SUFFIXES = {'.md', '.txt', '.py', '.yml', '.yaml', '.json', '.css', '.patch'}
VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link',
        'meta', 'param', 'source', 'track', 'wbr'}
BLOCKS = {'p', 'div', 'section', 'article', 'header', 'footer', 'h1', 'h2',
          'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'li', 'br', 'hr', 'main', 'nav'}
sys.path.insert(0, str(Path(__file__).resolve().parent))
from allowlist import SVG_ELEMENTS, SVG_ATTRIBUTES, IMAGE_HASHES, page_errors, vocabulary_errors, exact


def all_files(root):
    # Exclude only .git, even when it is nested. Do not follow symlinks.
    return sorted(p for p in Path(root).rglob('*')
                  if '.git' not in p.relative_to(root).parts and (p.is_file() or p.is_symlink()))


def site_files(root, suffix=None):
    documents = DOCUMENT_SUFFIXES | ({'.md'} if not (Path(root) / '.nojekyll').is_file() else set())
    return [p for p in all_files(root) if p.relative_to(root).as_posix() not in LEGAL_PINS and p.suffix.lower() in
            (documents if suffix is None else {suffix.lower()})]


def discovery_errors(root):
    root = Path(root)
    errors = []
    files = all_files(root)
    names = {p.relative_to(root).as_posix() for p in site_files(root)}
    for name in sorted(EXPECTED_DOCUMENTS - names):
        errors.append(f'Missing document: {name}')
    for name in sorted(names - EXPECTED_DOCUMENTS):
        errors.append(f'Unexpected document: {name!r}')
    for name, digest in IMAGE_HASHES.items():
        path = root / name
        data = path.read_bytes() if path.is_file() else b''
        if not path.is_file() or hashlib.sha256(data).hexdigest() != digest:
            errors.append(f'Approved image sha256 mismatch: {name}')
        if name.endswith('.png') and not data.startswith(b'\x89PNG\r\n\x1a\n'):
            errors.append(f'Approved PNG must start with PNG signature: {name}')
        if name.endswith('.ico') and not data.startswith(b'\x00\x00\x01\x00'):
            errors.append(f'Approved ICO must start with ICO signature: {name}')
    for name, digest in FONT_HASHES.items():
        path = root / name
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            errors.append(f'Approved font/license sha256 mismatch: {name}')
        if name.endswith('.woff2') and (not path.is_file() or path.read_bytes()[:4] != b'wOF2'):
            errors.append('Approved woff2 must start with wOF2 magic bytes')
    for p in files:
        name = p.relative_to(root).as_posix()
        if not re.fullmatch(r'[A-Za-z0-9._/-]+', name, re.ASCII):
            errors.append(f'Unsafe served path: {name!r}')
        if p.relative_to(root).parts[0] == '.github' and name not in GITHUB_FILES:
            errors.append(f'Unsupported .github file: {name!r}')
        if p.relative_to(root).parts[0] == 'fonts' and name not in FONT_HASHES:
            errors.append(f'Unapproved font directory file: {name!r}')
        if p.is_symlink():
            errors.append(f'Unsupported symlink: {name!r}')
        if p.suffix.lower() in {'.png', '.svg', '.ico'} and name not in IMAGE_HASHES:
            errors.append(f'Unapproved image file: {name!r}')
        if (p.suffix.lower() not in DOCUMENT_SUFFIXES | RAW_SUFFIXES and name not in FONT_HASHES and
                name not in IMAGE_HASHES and
                name not in {'CNAME', '.nojekyll', '.github/CODEOWNERS'}):
            errors.append(f'Unsupported served file type: {name!r}')
    return errors


def css_unescape(value):
    def replace(match):
        if match[1]:
            code = int(match[1], 16)
            return chr(code) if 0 < code <= 0x10ffff else '\ufffd'
        return match[2] or ''
    return re.sub(r'\\(?:([0-9a-fA-F]{1,6})[ \t\r\n\f]?|([^\n\r\f])|\r?\n)', replace, value)


def css_code(css):
    return css_unescape(re.sub(r'/\*.*?\*/', '', css, flags=re.S))


def css_references(css):
    pattern = r'''url\(\s*(?:"([^"]*)"|'([^']*)'|([^)]*?))\s*\)|@import\s+(?:"([^"]*)"|'([^']*)')'''
    return [next(x for x in m.groups() if x is not None).strip()
            for m in re.finditer(pattern, css_code(css), re.I)]


@dataclass(eq=False)
class Node:
    tag: str
    attrs: list
    line: int
    parent: object = None
    children: list = field(default_factory=list)
    closed: bool = False
    raw: str = ''
    raw_attrs: list = field(default_factory=list)

    @property
    def attr(self):
        return dict(self.attrs)

    def ancestors(self):
        node = self
        while node is not None:
            yield node
            node = node.parent


# Only layout TAB/LF/CR are permitted controls. HTML normalizes CR before
# tokenization; read_page must not use a different decoder/parser for a check.
SPACE = ' \t\n\r'
HTML_VOID = {'meta', 'link', 'br', 'hr', 'img'}
PHRASING = {'a', 'span', 'strong', 'em', 'br', 'svg', 'img'}
PHRASING_PARENTS = {'p', 'h1', 'h2', 'h3', 'a', 'span', 'strong', 'em', 'button'}
# li takes flow content (HTML parses <li><h3>/<p> without implicit closure); checked below.
FLOW = PHRASING | {'article', 'div', 'footer', 'header', 'main', 'nav', 'section',
                  'p', 'h1', 'h2', 'h3', 'ul', 'ol'}
# Owner-reviewed literal spellings, not arbitrary numeric/named references.
# The approved HTML has NO references, so there are no baseline additions.
HTML_REFERENCES = {'&amp;', '&lt;', '&gt;', '&quot;', '&#39;'}
NAME = r'[A-Za-z][A-Za-z0-9:-]*'
START = re.compile(r'<(' + NAME + r')(?=[ \t\r\n/>])')
END = re.compile(r'</(' + NAME + r')[ \t\r\n]*>')
ATTR = re.compile(r'''([A-Za-z_:][A-Za-z0-9_.:-]*)(?:[ \t\r\n]*=[ \t\r\n]*(?:"([^"]*)"|'([^']*)'|([^\s>]+)))?''')


class Page:
    """Strict HTML tokenizer: no HTMLParser recovery or second content parser.

    Errors are sticky. Rejected input may retain a diagnostic tree so existing
    checks can explain additional violations, but it can never pass preflight.
    Accepted input has explicit stack operations only; see README for the
    induction over HTML tree-builder modes (including the SVG boundary).
    """
    def __init__(self, text):
        self.root = Node('', [], 0)
        self.stack = [self.root]
        self.nodes, self.elements, self.css = [], [], []
        self.ids = set()
        self.processing_instructions, self.comments = [], []
        self.errors = markup_errors(text)  # Keep SVG/XML lexical defenses too.
        self.line = 1
        if not text.startswith('<!doctype html>'):
            self.fail('doctype must be exactly <!doctype html> at byte 0 (no BOM)')
        if text.count('<!') != 1 or not text.startswith('<!doctype html>'):
            self.fail('only the initial doctype declaration is allowed; comments/marked sections forbidden')
        if '<?' in text:
            self.fail('processing instructions forbidden')
        if re.search(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f\ud800-\udfff]', text):
            self.fail('NUL/control characters forbidden (except layout TAB/LF/CR)')
        for match in re.finditer(r'&(?:[^\s<>&;]*;?)', text):
            if match[0] not in HTML_REFERENCES:
                self.fail('forbidden HTML character reference: ' + match[0])
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        self.tokenize(text)
        if len(self.stack) != 1:
            self.fail('unclosed non-void elements: ' + ', '.join(n.tag for n in self.stack[1:]))
        self.document_shape()
        self.errors.extend(page_errors(self, document=False))

    def fail(self, message):
        self.errors.append(f'line {self.line}: strict HTML: {message}')

    def tokenize(self, text):
        pos = 0
        while pos < len(text):
            begin = pos
            self.line = text.count('\n', 0, pos) + 1
            if text.startswith('<!doctype html>', pos):
                if pos != 0:
                    self.fail('doctype must occur only at byte 0')
                pos += len('<!doctype html>')
            elif text.startswith('<!--', pos):
                # Diagnostic-only: all comments already failed the lexical gate.
                end = text.find('-->', pos + 4)
                end = len(text) if end < 0 else end
                data = text[pos + 4:end]
                self.comments.append(data)
                compact = re.sub(r'\s+', '', data).lower()
                if any(word in compact for word in ('html-validate', 'eslint', 'pa11y', 'axe')):
                    self.errors.append(f'line {self.line}: forbidden inline validator directive')
                pos = min(end + 3, len(text))
            elif text.startswith(('<!', '<?'), pos):
                end = text.find('>', pos)
                pos = len(text) if end < 0 else end + 1
            elif text.startswith('</', pos):
                match = END.match(text, pos)
                if not match:
                    self.fail('malformed end tag')
                    break
                tag = match[1].lower()
                svg = any(n.tag == 'svg' for n in self.stack)
                self.errors.extend(vocabulary_errors(Node(tag, [], self.line), svg))
                if len(self.stack) == 1 or self.stack[-1].tag != tag:
                    self.fail('unpaired or misnested end tag </' + tag + '>')
                else:
                    self.stack.pop().closed = True
                pos = match.end()
            elif text[pos] == '<':
                match = START.match(text, pos)
                if not match:
                    self.fail('malformed start tag or literal < in text')
                    break
                tag = match[1].lower()
                cursor, attrs, raw_attrs = match.end(), [], []
                while True:
                    previous = cursor
                    while cursor < len(text) and text[cursor] in SPACE:
                        cursor += 1
                    if text.startswith('/>', cursor) or text.startswith('>', cursor):
                        selfclosing = text.startswith('/>', cursor)
                        pos = cursor + (2 if selfclosing else 1)
                        break
                    attr = ATTR.match(text, cursor)
                    if not attr:
                        self.fail('malformed attribute/start tag')
                        return
                    if cursor == previous:
                        self.fail('attributes must be separated by whitespace')
                    key = attr[1].lower()
                    value = next((v for v in attr.groups()[1:] if v is not None), None)
                    if attr[2] is None:
                        self.fail('attribute values must be double-quoted')
                    if value is not None and '<' in value:
                        self.fail('literal < forbidden in attribute values')
                    attrs.append((key, unescape(value) if value is not None else None))
                    raw_attrs.append((key, value))
                    cursor = attr.end()
                self.start_tag(tag, attrs, raw_attrs, text[begin:pos], selfclosing)
                if tag == 'meta' and any(k == 'charset' for k, v in attrs):
                    if len(text[:pos].encode('utf-8', errors='replace')) > 1024:
                        self.fail('UTF-8 charset declaration must finish within first 1024 bytes')
            else:
                end = text.find('<', pos)
                pos = len(text) if end < 0 else end
                self.data(unescape(text[begin:pos]))

    def start_tag(self, tag, attrs, raw_attrs, raw, selfclosing):
        names = [key.lower() for key, value in attrs]
        if len(names) != len(set(names)):
            self.errors.append(f'line {self.line}: duplicate attribute name')
        parent = self.stack[-1]
        svg_parent = any(n.tag == 'svg' for n in self.stack)
        svg = svg_parent or tag == 'svg'
        if selfclosing and not svg and tag not in HTML_VOID:
            self.fail('self-closing non-void HTML element <' + tag + '/>')
        self.content_model(parent, tag, svg_parent)
        node = Node(tag, attrs, self.line, parent, raw=raw, raw_attrs=raw_attrs)
        parent.children.append(node)
        self.nodes.append(node)
        self.elements.append((tag, attrs, node.line))
        for key, value in attrs:
            if key == 'id' or (tag == 'a' and key == 'name'):
                self.ids.add(value)
            if key == 'style' and value:
                self.css.append(value)
        if (not svg and tag in VOID) or selfclosing:
            node.closed = True
        else:
            self.stack.append(node)

    def content_model(self, parent, tag, svg_parent):
        if svg_parent:
            # SVG title/desc are HTML integration points, and text has special
            # text semantics: accept text alone so namespace/parser modes agree.
            if parent.tag in {'title', 'desc', 'text'}:
                self.fail('SVG title/desc/text must contain text only')
            return
        if parent.tag == 'title':  # HTML title is RCDATA, NOT normal phrasing.
            self.fail('HTML title must contain text only (RCDATA)')
        if parent.tag in PHRASING_PARENTS and tag not in PHRASING:
            self.fail('phrasing content required in <' + parent.tag + '>')
        if parent.tag in {'ul', 'ol'} and tag != 'li':
            self.fail('ul/ol may contain only li and whitespace')
        if tag == 'li' and parent.tag not in {'ul', 'ol'}:
            self.fail('li must be a direct child of ul/ol')
        if parent.tag == 'li' and tag not in FLOW:
            self.fail('li requires explicitly nested flow content')
        if parent.tag in FLOW - PHRASING - {'ul', 'ol'} | {'body'} and tag not in FLOW:
            self.fail('flow content required in <' + parent.tag + '>')
        if tag == 'a' and any(n.tag == 'a' for n in self.stack):
            self.fail('nested anchors forbidden')

    def data(self, data):
        parent = self.stack[-1]
        if parent.tag in {'', 'html', 'head', 'ul', 'ol'} and data.strip(SPACE):
            self.fail('only whitespace text allowed in document/head/list structure')
        # Match the browser's whitespace insertion modes. Before html/head,
        # whitespace is ignored; after body/html, it belongs to body.
        if parent is self.root or (parent.tag == 'html' and
                                   any(n.tag == 'body' for n in self.nodes)):
            bodies = [n for n in self.nodes if n.tag == 'body']
            if not bodies:
                return
            parent = bodies[0]
        elif parent.tag == 'html' and not parent.children:
            return
        if parent.children and isinstance(parent.children[-1], str):
            parent.children[-1] += data
        else:
            parent.children.append(data)
        if parent.tag == 'style':
            self.css.append(data)

    def document_shape(self):
        roots = [n for n in self.root.children if isinstance(n, Node)]
        htmls = [n for n in self.nodes if n.tag == 'html']
        heads = [n for n in self.nodes if n.tag == 'head']
        bodies = [n for n in self.nodes if n.tag == 'body']
        if len(roots) != 1 or roots[0].tag != 'html' or len(htmls) != 1:
            self.fail('document requires exactly one root html')
        if len(htmls) != 1 or len(heads) != 1 or len(bodies) != 1:
            self.fail('document requires exactly one head followed by one body')
            return
        html, head, body = htmls[0], heads[0], bodies[0]
        if [c for c in html.children if isinstance(c, Node)] != [head, body]:
            self.fail('html must contain exactly head then body')
        if head.parent is not html or body.parent is not html:
            self.fail('head/body must be direct children of html')
        seen_csp = False
        for node in self.nodes:
            if node.parent is head:
                if node.tag not in {'meta', 'title', 'link'}:
                    self.fail('head may contain only meta, title and link')
                if node.tag == 'meta' and node.attr.get('http-equiv') == 'Content-Security-Policy':
                    seen_csp = True
                if node.tag == 'link' and not seen_csp:
                    self.fail('CSP must precede every link')
        charsets = [n for n in self.nodes if n.tag == 'meta' and 'charset' in n.attr]
        children = [c for c in head.children if isinstance(c, Node)]
        if (len(charsets) != 1 or not children or children[0] is not charsets[0] or
                not exact(charsets[0], 'charset', 'utf-8')):
            self.fail('first head element must be the unique byte-exact UTF-8 charset meta')

def markup_errors(text):
    errors = []
    # The sole allowed declaration is HTML's simple doctype. In particular no
    # internal subset, entity declaration or external DTD is ever interpreted.
    declarations = re.finditer(r'<!\s*(DOCTYPE|ENTITY)\b', text, re.I)
    if any(not re.match(r'<!doctype\s+html\s*>', text[m.start():], re.I)
           for m in declarations):
        errors.append('forbidden DTD/entity declaration')
    for match in re.finditer(r'&(?:#[^\s<>&;]*;?|[A-Za-z_:][\w:.-]*;?)', text):
        if not re.fullmatch(r'&(?:amp|lt|gt|apos|quot|#[0-9]+|#x[0-9a-fA-F]+);', match[0]):
            errors.append('forbidden entity reference: ' + match[0])
    return errors


class NoDTDTreeBuilder(ET.TreeBuilder):
    def doctype(self, name, pubid, system):
        raise ValueError('forbidden DTD/entity declaration')

    def pi(self, target, text=None):
        raise ValueError('forbidden XML processing instruction')


class SVGPage:
    """XML only: DTDs are refused before their declarations can be expanded."""
    def __init__(self, text):
        self.root = Node('', [], 0)
        self.nodes, self.elements, self.css = [], [], []
        self.ids = set()
        self.processing_instructions = []
        self.errors = markup_errors(text)
        try:
            element = ET.fromstring(text, parser=ET.XMLParser(target=NoDTDTreeBuilder()))
        except (ET.ParseError, ValueError) as exc:
            self.errors.append(f'invalid SVG XML: {exc}')
            return
        if element.tag != '{http://www.w3.org/2000/svg}svg':
            self.errors.append('SVG root must be svg in the SVG namespace')

        def xml_name(name):
            if name.startswith('{http://www.w3.org/2000/svg}'):
                return name.split('}', 1)[1].lower()
            if name == '{http://www.w3.org/1999/xlink}href':
                return 'xlink:href'
            return name.lower()  # Unknown namespace stays expanded and fails allowlists.

        def visit(element, parent):
            if element.tag not in {'{http://www.w3.org/2000/svg}' + t for t in SVG_ELEMENTS}:
                self.errors.append(f'forbidden <{xml_name(element.tag)}> SVG element')
            for key in element.attrib:
                if key not in SVG_ATTRIBUTES:
                    self.errors.append(f'forbidden SVG attribute {key}')
            attrs = [(xml_name(k), v) for k, v in element.attrib.items()]
            node = Node(xml_name(element.tag), attrs, 1, parent, closed=True)
            self.errors.extend(vocabulary_errors(node, svg=True))
            parent.children.append(node)
            self.nodes.append(node)
            self.elements.append((node.tag, attrs, node.line))
            names = [k for k, v in attrs]
            if len(names) != len(set(names)):
                self.errors.append('duplicate attribute name in SVG')
            if 'id' in node.attr:
                self.ids.add(node.attr['id'])
            if element.text:
                node.children.append(element.text)
            for child in element:
                visit(child, node)
                if child.tail:
                    node.children.append(child.tail)
        visit(element, self.root)


def read_page(path):
    try:
        text = path.read_bytes().decode('utf-8')
    except UnicodeDecodeError:
        page = Page('')
        page.errors.append('invalid UTF-8 document bytes')
        return page
    page = SVGPage(text) if path.suffix.lower() == '.svg' else Page(text)
    if path.suffix.lower() != '.svg':
        page.errors.extend(page_errors(page))
    return page


def hidden(node):
    for n in node.ancestors():
        a = n.attr
        if (n.tag in {'head', 'template', 'noscript', 'script', 'style'} or
                'hidden' in a or 'inert' in a or
                (a.get('aria-hidden') or '').lower() == 'true' or
                (n.tag == 'details' and 'open' not in a)):
            return True
    return False


def visible_text(node):
    if hidden(node):
        return ''
    return separated_text(node, visible_text)


def separated_text(node, extract=None):
    """Separate EVERY element boundary, including empty/inline/SVG elements.

    With no filter this includes head, hidden and accessibility-only text.
    Callers can supply their own visibility or narrowly pinned exemptions.
    """
    extract = extract or separated_text
    value = ''.join(c if isinstance(c, str) else ' ' + extract(c) + ' ' for c in node.children)
    if not node.tag and not value.strip():
        return ''
    return ' ' + value + ' '


def joined_text(node):
    """Retain inline-joined metadata scanning alongside separated words."""
    return ''.join(c if isinstance(c, str) else joined_text(c) for c in node.children)


def copy_text(node, boundaries=True):
    # aria-hidden affects accessibility, not visual rendering. SVG text counts.
    if node.tag in {'head', 'template'} or 'hidden' in node.attr:
        return ''
    if not boundaries:
        value = ''.join(c if isinstance(c, str) else copy_text(c, False) for c in node.children)
        return ' ' + value + ' ' if node.tag in BLOCKS else value
    return separated_text(node, copy_text)


def normalized(text):
    return ' '.join(text.split())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', nargs='?', type=Path, default=ROOT)
    parser.add_argument('--html-only', action='store_true')
    args = parser.parse_args()
    errors = discovery_errors(args.root)
    if errors:
        print('\n'.join(errors), file=sys.stderr)
        return 1
    for p in site_files(args.root):
        if not args.html_only or p.suffix.lower() in {'.html', '.htm', '.xhtml'}:
            sys.stdout.buffer.write(('./' + p.relative_to(args.root).as_posix()).encode('ascii') + b'\0')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
