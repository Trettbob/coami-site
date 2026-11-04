"""Conservative CSS visibility audit over the finite pinned page class set.

No cascade override can excuse a hiding declaration. Class-bearing selectors
are conservatively associated with every occurrence of those classes (including
ancestors); selectors without classes are audited against every body node.
This deliberately also catches descendants, pseudo selectors, at-rules and
attribute-selector spellings without needing a browser or selector package.
"""
import hashlib
import json
from pathlib import Path
import re

from site_common import HTML_PAGES, normalized, read_page, site_files
from legal_visibility import node_path, VISIBILITY_ATTRIBUTES
from page_pins import body_nodes, load_pin, skeleton_records

# Exact original rule fingerprints, not a class-name exemption. Only matching
# pinned skip-link/logo nodes may use these rules, in their original contexts.
EXCEPTION_RULES = {'3b6a8b478120fc81ed1f485ca9539038f77492fa1e337967001ac23bafcf07ad': 'skip', 'a7c9a46105855a64586420e29721f0b5e840aa62e28c46701a1696602335282f': 'brand-dark', '6c5a1990965b5d384c9e188ec5a97b3d1f146e27851a64db87a55e401a34e89f': 'brand-light'}


def rule_digest(selectors, declarations, context):
    return hashlib.sha256(json.dumps([selectors, declarations, context],
                                    separators=(',', ':')).encode()).hexdigest()


def zero(value):
    match = re.fullmatch(r'([-+]?(?:\d+\.?\d*|\.\d+)(?:e[-+]?\d+)?)(?:[a-z%]+)?', value)
    return match is not None and float(match[1]) == 0


def distant(value):
    # Negative offsets can remove content; large positive translations/offsets
    # can do the same. Unresolved arithmetic/variables fail closed.
    if re.search(r'\b(?:var|calc|min|max|clamp|env)\(', value):
        return True
    for number, unit in re.findall(r'([-+]?(?:\d*\.)?\d+)(px|rem|em|vw|vh|vmin|vmax|%)?', value):
        amount = float(number)
        if amount < 0 or amount >= (100 if unit in {'%', 'vw', 'vh', 'vmin', 'vmax'} else 1000 if unit == 'px' else 50):
            return True
    return False


def hiding_reasons(declarations):
    """Audit all declarations, including duplicates and !important spellings."""
    values = {}
    for prop, value in declarations:
        values.setdefault(prop, []).append(normalized(re.sub(r'\s*!\s*important\s*$', '', value.lower())))
    reasons = []
    for prop, choices in values.items():
        for value in choices:
            unresolved = bool(re.search(r'\b(?:var|calc|env)\(', value))
            if ((prop == 'display' and (value == 'none' or unresolved)) or
                    (prop in {'visibility', 'content-visibility'} and (value in {'hidden', 'collapse'} or unresolved)) or
                    (prop in {'clip', 'clip-path'} and value not in {'auto', 'none'}) or
                    (prop in {'opacity', 'font-size'} and (zero(value) or unresolved)) or
                    (prop == 'font' and re.match(r'0(?:px|rem|em|%|/|\s)', value)) or
                    (prop == 'text-indent' and distant(value))):
                reasons.append(prop + ': ' + value)
    if any(set(v.split()) & {'hidden', 'clip'} for p in {'overflow', 'overflow-x', 'overflow-y', 'overflow-block'} for v in values.get(p, [])):
        if any(zero(v) or re.search(r'\b(?:var|calc|env)\(', v)
               for p in {'height', 'max-height', 'block-size', 'max-block-size'} for v in values.get(p, [])):
            reasons.append('zero height with clipped overflow')
    if any(v in {'absolute', 'fixed'} for v in values.get('position', [])):
        if any(distant(v) for p, choices in values.items()
               if p in {'top', 'right', 'bottom', 'left', 'inset', 'inset-inline', 'inset-block',
                        'inset-inline-start', 'inset-inline-end', 'inset-block-start', 'inset-block-end'}
               for v in choices):
            reasons.append('positioned offscreen')
    for prop in {'transform', 'translate'}:
        for value in values.get(prop, []):
            # Tiny hover/arrival movements in the approved CSS remain visible.
            if (prop == 'translate' or 'translate' in value) and (
                    re.search(r'\b(?:var|calc|env)\(', value) or
                    any(abs(float(n)) >= (100 if u in {'%', 'vw', 'vh'} else 1000 if u == 'px' else 50)
                        for n, u in re.findall(r'([-+]?(?:\d*\.)?\d+)(px|rem|em|vw|vh|%)', value))):
                reasons.append(prop + ': ' + value)
    return sorted(set(reasons))


def page_visibility_errors(root):
    # Late import keeps the shared CSS parser free of an import cycle.
    from check_v5 import css_rules
    errors, rules = [], []
    for path in site_files(root, '.css'):
        try:
            parsed, _ = css_rules(path.read_text(encoding='utf-8'))
            rules.extend((path.relative_to(root).as_posix(), *r) for r in parsed
                         if not any(c.startswith('@keyframes ') for c in r[2]))
        except (ValueError, StopIteration, UnicodeError) as exc:
            errors.append(f'Visibility: CSS parse failed: {exc}')
    for name in HTML_PAGES:
        pin = load_pin(root, name)
        if pin is None:
            errors.append(f'{name}: Visibility requires trusted page pin')
            continue
        path = Path(root) / name
        if not path.is_file():
            errors.append(f'{name}: Visibility missing page')
            continue
        page = read_page(path)
        errors.extend(f'{name}: {e}' for e in page.errors)
        approved = {r['path']: r for r in pin}
        records = {r['path']: r for r in skeleton_records(page)}
        for node in body_nodes(page):
            place = node_path(node)
            classes = set((node.attr.get('class') or '').split())
            # Accessibility-only SVGs in the pins are intentional. No added
            # visibility attribute, including on an ancestor, is permitted.
            for attr in VISIBILITY_ATTRIBUTES:
                if attr in node.attr and [attr, node.attr[attr]] not in approved.get(place, {}).get('attributes', []):
                    errors.append(f'{name}: Visibility unapproved {attr} at {place}')
            combined = []
            for css_name, selectors, declarations, context in rules:
                for selector in selectors:
                    mentioned = set(re.findall(r'\.([\w-]+)', selector))
                    if mentioned and not mentioned.intersection(classes):
                        continue
                    reasons = hiding_reasons(declarations)
                    allowed = (css_name == 'style.css' and
                               rule_digest((selector,), declarations, context) in EXCEPTION_RULES and
                               EXCEPTION_RULES[rule_digest((selector,), declarations, context)] in classes and
                               records.get(place) == approved.get(place))
                    if allowed:
                        continue
                    if reasons:
                        errors.append(f'{name}: Visibility hiding rule {selector}: {", ".join(reasons)} at {place}')
                    combined.extend(declarations)
            # Catch split-rule position/offset and height/overflow combinations.
            if hiding_reasons(combined):
                errors.append(f'{name}: Visibility hiding declarations at {place}')
    return errors
