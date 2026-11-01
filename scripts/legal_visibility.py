"""Class placement pinned from each approved v4 page, never from candidate HTML."""
from site_common import hidden

# All unlisted places on/inside/above the notice or footer require NO classes.
# Paths use same-tag sibling ordinals, so a class cannot migrate to another p.
LEGAL_CLASSES = {
    'index.html': {
        'html[1]/body[1]/footer[1]': ('site',),
        'html[1]/body[1]/footer[1]/div[1]': ('wrap',),
    },
    '404.html': {
        'html[1]/body[1]/footer[1]': ('site',),
        'html[1]/body[1]/footer[1]/div[1]': ('wrap',),
    },
    'privacy.html': {
        'html[1]/body[1]/footer[1]': ('site',),
        'html[1]/body[1]/footer[1]/div[1]': ('wrap',),
        'html[1]/body[1]/main[1]/div[1]': ('wrap',),
        'html[1]/body[1]/main[1]/div[1]/article[1]': ('legal', 'text'),
        'html[1]/body[1]/main[1]/div[1]/article[1]/p[1]': ('meta',),
        'html[1]/body[1]/main[1]/div[1]/article[1]/ul[1]': ('plain',),
    },
}
VISIBILITY_ATTRIBUTES = {'hidden', 'popover', 'inert', 'aria-hidden', 'style'}


def node_path(node):
    parts = []
    for n in node.ancestors():
        if not n.tag:
            continue
        siblings = [c for c in n.parent.children if not isinstance(c, str) and c.tag == n.tag]
        parts.append(f'{n.tag}[{siblings.index(n) + 1}]')
    return '/'.join(reversed(parts))


def visibility_errors(page, name, element, label):
    errors = []
    pins = LEGAL_CLASSES.get(name, {})
    nodes = set(element.ancestors()) | {n for n in page.nodes if element in n.ancestors()}
    for node in nodes:
        if not node.tag:
            continue
        if VISIBILITY_ATTRIBUTES.intersection(node.attr) or hidden(node):
            errors.append(f'{label} visibility is not approved: <{node.tag}> line {node.line}')
        if tuple((node.attr.get('class') or '').split()) != pins.get(node_path(node), ()):
            errors.append(f'{label} visibility class placement is not approved: {node_path(node)} line {node.line}')
    return errors
