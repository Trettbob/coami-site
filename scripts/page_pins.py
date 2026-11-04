"""Complete ordered body skeletons and public head text. Digests are trusted code, never candidate config.

Each JSON line records tag, ordered classes, every other attribute, path and
content slots. A slot is exact direct text (including whitespace) or a child
path. Thus nesting, empty elements, and text on either side of an inline child
are pinned too. All body descendants, including SVG, count regardless of CSS.
"""
import hashlib
import json
from pathlib import Path

from site_common import HTML_PAGES, read_page
from legal_visibility import node_path
from allowlist import CSP

PAGE_SHA256 = {
    '404.html': '48e4744b44872d238aeda8a8c204bc8fc035ad9be485127c72f5607f2472fc5c',
    'about.html': '7a99f8632b3b397e693a0c81a1b08ecb22794f69096c0233486d05b6460169e6',
    'contact.html': 'c047c28a06232fc67d00df557ece820a26a24f7e8db989fd5b569f4c6a967adf',
    'features.html': '1fe64caf15792dd90d29ec1377afaa7fc27ece35d28dac22c3a3f206cfc61588',
    'how-it-works.html': '153facbc21fd7989e8eb03d048a68abe7e1239028ace707f1ace05664f56d544',
    'index.html': 'b8ef814cddc21ad5c428efe0cc611f4170d7a750f4837631879fe6c784d0aef6',
    'pilot.html': 'e8b93ce758e9744ce91465ec4e0d636d19fe6bddb376309c9e98db42a7035801',
    'privacy.html': '8f5b8f32432a88b1255e25bd620a766c6ec663c0bb520a19ece49a5c79973101',
}


# Exact current head vocabulary, attributes and order. Description content is
# authenticated separately per page; no new search-visible metadata is allowed.
HEAD_ELEMENTS = [
    ('meta', [('charset', 'utf-8')]),
    ('meta', [('content', 'width=device-width, initial-scale=1'), ('name', 'viewport')]),
    ('meta', [('content', CSP), ('http-equiv', 'Content-Security-Policy')]),
    ('meta', [('content', 'no-referrer'), ('name', 'referrer')]),
    ('title', []),
    ('meta', [('content', None), ('name', 'description')]),
    ('link', [('href', 'favicon.ico'), ('rel', 'icon'), ('sizes', '48x48')]),
    ('link', [('href', 'coami-icon.svg'), ('rel', 'icon'), ('type', 'image/svg+xml')]),
    ('link', [('href', 'apple-touch-icon.png'), ('rel', 'apple-touch-icon')]),
    ('link', [('href', 'style.css'), ('rel', 'stylesheet')]),
]

HEAD_SHA256 = {
    '404.html': 'ff8947135db27de76b348baddc7e778867043c14e6218e3bebebb0c72aa81094',
    'about.html': '657e106bc70d5717c54cdf8b13d1536f3e60c9f2ba2a971ae29bd73509c236b6',
    'contact.html': '2f88d8dcaa88b8de4164ed91034f7c2b5bd47cb5e83854817d947c84143817b0',
    'features.html': 'ac852ae8bf62d906bd643d9319fc1010900f83c45a0c4cf83992220e8af9b2c9',
    'how-it-works.html': 'af08387396c1d5d66f80c5177004c3c96316f449b07a47286308d663956bb362',
    'index.html': 'e989c9ffbb9080985c693a46d1c59952a0e2125ff05b3f5a29af9abbdbfcd754',
    'pilot.html': 'b93366777c9267da7f403ba48d426fdc19a2270bb911d7ea4916e0ceb9d681c7',
    'privacy.html': '6faf0bded997aec90381c23f89494859c5ba595eaa03c6120e211dde39d55579',
}


def head_nodes(page):
    return [n for n in page.nodes if n.tag != 'head' and
            any(a.tag == 'head' for a in n.ancestors())]


def head_record(page):
    nodes = head_nodes(page)
    return {'title': ''.join(c for n in nodes if n.tag == 'title'
                             for c in n.children if isinstance(c, str)),
            'description': ''.join(n.attr.get('content') or '' for n in nodes
                                  if n.tag == 'meta' and n.attr.get('name') == 'description')}


def head_bytes(page):
    return (json.dumps(head_record(page), ensure_ascii=False, separators=(',', ':')) + '\n').encode('utf-8')


def head_errors(page):
    nodes = head_nodes(page)
    errors = []
    for tag in ('title', 'description'):
        matches = [n for n in nodes if (n.tag == 'title' if tag == 'title' else
                   n.tag == 'meta' and n.attr.get('name') == 'description')]
        if len(matches) != 1:
            errors.append(f'head requires exactly one {tag}')
        if not head_record(page)[tag].strip():
            errors.append(f'head {tag} must be non-empty')
    layout = [(n.tag, sorted((k, None if n.tag == 'meta' and
               n.attr.get('name') == 'description' and k == 'content' else v)
               for k, v in n.attrs)) for n in nodes]
    if layout != HEAD_ELEMENTS:
        errors.append('head elements/attributes differ from allowlist')
    return errors


def head_pin_errors(root, name, page):
    errors = head_errors(page)
    path = Path(root) / 'legal' / 'page-pins' / (name + '.head.txt')
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != HEAD_SHA256.get(name):
        errors.append('head pin sha256 mismatch or missing')
    elif head_bytes(page) != path.read_bytes():
        errors.append('public head text differs from head pin')
    return errors


def body_nodes(page):
    return [n for n in page.nodes if any(a.tag == 'body' for a in n.ancestors())]


def skeleton_records(page):
    return [dict(path=node_path(n), tag=n.tag,
                 classes=(n.attr.get('class') or '').split(),
                 attributes=sorted([k, v] for k, v in n.attrs if k != 'class'),
                 content=[c if isinstance(c, str) else {'element': node_path(c)}
                          for c in n.children]) for n in body_nodes(page)]


def skeleton_bytes(page):
    return ''.join(json.dumps(record, ensure_ascii=False, separators=(',', ':')) + '\n'
                   for record in skeleton_records(page)).encode('utf-8')


def load_pin(root, name):
    path = Path(root) / 'legal' / 'page-pins' / (name + '.txt')
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != PAGE_SHA256.get(name):
        return None
    try:
        return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]
    except (ValueError, UnicodeError):
        return None


def page_pin_errors(root):
    errors = []
    for name in HTML_PAGES:
        approved = load_pin(root, name)
        if approved is None:
            errors.append(f'{name}: page pin sha256 mismatch or missing')
            continue
        path = Path(root) / name
        if not path.is_file():
            errors.append(f'{name}: missing pinned page')
            continue
        page = read_page(path)
        errors.extend(f'{name}: {e}' for e in page.errors)
        errors.extend(f'{name}: {e}' for e in head_pin_errors(root, name, page))
        if skeleton_records(page) != approved:
            errors.append(f'{name}: complete body skeleton differs from page pin')
    return errors
