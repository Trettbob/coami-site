"""Complete ordered body skeletons. Digests are trusted code, never candidate config.

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
        if skeleton_records(page) != approved:
            errors.append(f'{name}: complete body skeleton differs from page pin')
    return errors
