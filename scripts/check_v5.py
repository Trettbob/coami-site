"""Pinned Features copy, scoped claim ban, purple allowlist and motion coverage."""
import argparse
from collections import Counter
import colorsys
import hashlib
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from site_common import ROOT, BLOCKS, css_code, discovery_errors, normalized, read_page, site_files, visible_text, separated_text
from legal_pins import PINS, element_bytes
from check_invariants import FOOTER
from page_pins import page_pin_errors
from page_visibility import page_visibility_errors
from hero_contrast import hero_contrast_errors

FEATURES_PATH = Path('legal/approved-features-copy.txt')  # trusted constant, never candidate config
FEATURES_SHA256 = '1e70dd45e954473a3c81eb6d982757cecd2f402b0bbe906d2ac2aa03f2eaf83e'
CLAIMS = re.compile(r'\b(?:live|secure|checked|working\s+preview|available\s+now|guaranteed)\b', re.I)
LIVE_CHAT = re.compile(r'\blive chat\b', re.I)
STATUS_COUNTS = {'Planned for the private pilot': 6, 'Planned': 30, 'In the private pilot': 0}


def occurrences(phrase, value):
    return len(re.findall(r'(?<!\w)' + re.escape(phrase) + r'(?!\w)', value))


def feature_errors(root):
    path = root / FEATURES_PATH
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != FEATURES_SHA256:
        return ['Features approved-copy sha256 mismatch']
    try:
        approved = json.loads(path.read_text(encoding='utf-8'))
    except (ValueError, UnicodeError):
        return ['Features approved-copy data invalid']
    page_path = root / 'features.html'
    if not page_path.is_file():
        return ['Missing Features page']
    page = read_page(page_path)
    errors = list(page.errors)
    mains = [n for n in page.nodes if n.tag == 'main']
    expected = [approved[k] for k in ('heading', 'subheading', 'disclaimer')]
    for section in approved['sections']:
        expected.append(section['heading'])
        expected.extend(text for item in section['items'] for text in item)
    if len(mains) != 1 or normalized(visible_text(mains[0])) != normalized(' '.join(expected)):
        errors.append('Features complete visible copy/order differs from Legal')
    # Exact slots plus whole-page occurrence counts. Short titles now overlap
    # other approved strings (Ami, Email, and Building in the Legal footer).
    slots = [normalized(visible_text(n)) for n in page.nodes if n.tag in {'h1', 'h2', 'h3', 'p', 'span'}]
    all_text = normalized(visible_text(page.root))
    approved_text = normalized(' '.join(expected) + ' ' + FOOTER)
    for text in expected:
        if text not in STATUS_COUNTS and (slots.count(text) != 1 or
                occurrences(text, all_text) != occurrences(text, approved_text)):
            errors.append('Features item must occur exactly once: ' + text)
    rows = [n for n in page.nodes if n.tag == 'li' and
            set((n.attr.get('class') or '').split()) & {'feature-row', 'feature-tile'}]
    items = [item for section in approved['sections'] for item in section['items']]
    actual_rows = [normalized(visible_text(n)) for n in rows]
    if actual_rows != [normalized(' '.join(item)) for item in items]:
        errors.append('Features title/sentence/status association differs from Legal')
    statuses = Counter(normalized(visible_text(n)) for n in page.nodes
                       if 'status' in (n.attr.get('class') or '').split())
    if (statuses != Counter({k: v for k, v in STATUS_COUNTS.items() if v}) or
            any(occurrences(k, all_text) != occurrences(k, approved_text)
                for k in STATUS_COUNTS)):
        errors.append('Features status counts must be 6 pilot, 30 Planned, 0 in pilot')
    return errors


def claim_errors(root):
    errors = []
    pin = root / FEATURES_PATH
    approved_items = []
    if pin.is_file() and hashlib.sha256(pin.read_bytes()).hexdigest() == FEATURES_SHA256:
        approved_items = [normalized(' '.join(item)) for section in
                          json.loads(pin.read_text(encoding='utf-8'))['sections'] for item in section['items']]
    for path in site_files(root):
        page = read_page(path)
        errors.extend(page.errors)
        # Exempt only a byte-identical, single Legal element in its proper page.
        exempt = set()
        for tag, pin_name in PINS.items():
            pin = root / pin_name
            nodes = [n for n in page.nodes if n.tag == tag]
            if (tag != 'article' or path.name == 'privacy.html') and pin.is_file() and len(nodes) == 1 and element_bytes(path.read_bytes(), tag) == [pin.read_bytes()]:
                exempt.add(nodes[0])
        # Match complete pinned rows, including hidden text. Only phrase case may
        # vary here; the separate Features check still enforces exact Legal copy.
        chat_rows = set()
        def raw_text(n):
            return separated_text(n)
        if path.relative_to(root).as_posix() == 'features.html':
            rows = [n for n in page.nodes if n.tag == 'li' and
                    set((n.attr.get('class') or '').split()) & {'feature-row', 'feature-tile'} and
                    any(a.tag == 'main' for a in n.ancestors())]
            for row, approved in zip(rows, approved_items):
                if LIVE_CHAT.sub('live chat', normalized(raw_text(row))) == approved:
                    chat_rows.add(row)
        def text(n, boundaries=True):
            if n in exempt:
                # The existing Legal exception covers other claim words, but
                # "live" has only the pinned feature-item exception above.
                return ' ' + ' '.join(m[0] for m in re.finditer(r'\blive\b', raw_text(n), re.I)) + ' '
            # Retain the original inline-joined scan as an additional guard:
            # se<span>cure</span> must still fail, as in the existing tests.
            value = (separated_text(n, text) if boundaries else
                     ''.join(c if isinstance(c, str) else text(c, False) for c in n.children))
            if n in chat_rows:
                value = LIVE_CHAT.sub('chat', value)
            return ' ' + value + ' ' if not boundaries and (n.tag in BLOCKS or n.tag == 'title') else value
        values = [normalized(text(page.root)), normalized(text(page.root, False))]
        values.extend(value for n in page.nodes if not any(a in exempt for a in n.ancestors())
                      for key, value in n.attrs if value is not None)
        values.extend(m[0] for n in page.nodes if any(a in exempt for a in n.ancestors())
                      for key, value in n.attrs if value is not None
                      for m in re.finditer(r'\blive\b', value, re.I))
        for value in values:
            for match in CLAIMS.finditer(normalized(value)):
                errors.append(f'{path.relative_to(root)}: banned claim word: {match[0]!r}')
    return errors


# CSS tokenizer: delimiters inside strings/functions are not structural tokens.
def split_css(source, delimiters):
    start, quote, depth, escaped = 0, None, 0, False
    for i, char in enumerate(source):
        if escaped:
            escaped = False
        elif char == '\\':
            escaped = True
        elif quote:
            if char == quote:
                quote = None
        elif char in {'"', "'"}:
            quote = char
        elif char in '([':
            depth += 1
        elif char in ')]':
            depth -= 1
            if depth < 0:
                raise ValueError('unbalanced CSS function')
        elif depth == 0 and char in delimiters:
            yield source[start:i].strip(), char
            start = i + 1
    if quote or depth or escaped:
        raise ValueError('unterminated CSS string/function')
    yield source[start:].strip(), ''


def css_rules(source):
    """Consume balanced blocks; emit selector declarations and enclosing at-rules."""
    tokens = iter(split_css(css_code(source), '{}'))
    rules, keyframes = [], set()
    def walk(context=(), closing=False):
        for prelude, delimiter in tokens:
            if delimiter == '}':
                if not closing or prelude:
                    raise ValueError('unexpected CSS closing block')
                return
            if not delimiter:
                if prelude or closing:
                    raise ValueError('incomplete CSS block')
                return
            if prelude.startswith('@') and not prelude.startswith('@font-face'):
                if prelude.startswith('@keyframes '):
                    name = prelude.split()[1]
                    if name in keyframes:
                        raise ValueError('duplicate keyframes')
                    keyframes.add(name)
                elif not prelude.startswith(('@media ', '@supports ')):
                    raise ValueError('unsupported CSS at-rule')
                walk((*context, prelude), True)
                continue
            body, end = next(tokens)
            if end != '}':
                raise ValueError('unexpected nested CSS rule')
            declarations = []
            for declaration, _ in split_css(body, ';'):
                if not declaration:
                    continue
                if ':' not in declaration:
                    raise ValueError('invalid CSS declaration')
                key, value = declaration.split(':', 1)
                declarations.append((key.strip().lower(), normalized(value)))
            rules.append((tuple(s for s, _ in split_css(prelude, ',')), declarations, context))
        if closing:
            raise ValueError('unclosed CSS block')
    walk()
    return rules, keyframes


# Frozen from the pre-neutral stylesheet and logo/icon SVGs. Alpha does not
# change palette identity; this also catches equivalent hex/rgb spellings.
PURPLE_HEX = ('#7a4fa0', '#68408c', '#c9a6ec', '#e2cff3')
PURPLE_RGB = {tuple(bytes.fromhex(value[1:])) for value in PURPLE_HEX}
PURPLE_ASSETS = {'img/coami-logo.svg', 'img/coami-logo-light-on-dark.svg',
                 'coami-icon.svg', 'favicon.ico', 'apple-touch-icon.png'}
NAMED_PURPLES = {
    'purple': '#800080', 'rebeccapurple': '#663399', 'indigo': '#4b0082',
    'blueviolet': '#8a2be2', 'darkorchid': '#9932cc', 'darkviolet': '#9400d3',
    'darkmagenta': '#8b008b', 'mediumorchid': '#ba55d3', 'mediumpurple': '#9370db',
    'orchid': '#da70d6', 'violet': '#ee82ee', 'magenta': '#ff00ff',
    'fuchsia': '#ff00ff', 'slateblue': '#6a5acd', 'mediumslateblue': '#7b68ee',
    'darkslateblue': '#483d8b', 'plum': '#dda0dd', 'thistle': '#d8bfd8',
}
COLOUR = re.compile(r'#[0-9a-f]{3,8}\b|\b(?:rgba?|hsla?|hwb|color)\([^()]*\)|\b(?:' +
                    '|'.join(NAMED_PURPLES) + r')\b', re.I)


def purple_colours(source):
    """Recognize palette RGB identities and the inclusive HSL hue/lightness guard."""
    source = css_code(source)
    if re.search(r'\b(?:lab|lch|oklab|oklch|color-mix|light-dark|device-cmyk)\s*\(', source, re.I):
        raise ValueError('unsupported colour expression')
    matches = list(COLOUR.finditer(source))
    starts = {m.start() for m in matches}
    if any(m.start() not in starts for m in re.finditer(r'\b(?:rgba?|hsla?|hwb|color)\s*\(', source, re.I)):
        raise ValueError('unsupported nested colour expression')
    def channel(value):
        return min(1, max(0, float(value[:-1]) / 100 if value.endswith('%') else float(value) / 255))
    for match in matches:
        literal = match[0]
        value = NAMED_PURPLES.get(literal.lower(), literal.lower())
        try:
            if value.startswith('#'):
                digits = value[1:]
                if len(digits) in {3, 4}:
                    digits = ''.join(c * 2 for c in digits)
                if len(digits) not in {6, 8}:
                    continue
                rgb = tuple(c / 255 for c in bytes.fromhex(digits[:6]))
            else:
                function, arguments = value.split('(', 1)
                parts = arguments[:-1].replace(',', ' ').replace('/', ' / ').split()
                if function in {'rgb', 'rgba'}:
                    rgb = tuple(channel(c) for c in parts[:3])
                elif function == 'color':
                    if parts[0] not in {'srgb', 'srgb-linear'}:
                        raise ValueError('unsupported colour space')
                    rgb = tuple(float(c[:-1]) / 100 if c.endswith('%') else float(c) for c in parts[1:4])
                    if parts[0] == 'srgb-linear':
                        rgb = tuple(12.92*c if c <= .0031308 else 1.055*c**(1/2.4)-.055 for c in rgb)
                else:
                    angle = parts[0]
                    units = re.fullmatch(r'([-+.\d]+)(deg|grad|rad|turn)?', angle)
                    if not units:
                        raise ValueError('unsupported hue')
                    hue = float(units[1]) * {None: 1, 'deg': 1, 'grad': .9,
                                              'rad': 180 / 3.141592653589793, 'turn': 360}[units[2]] / 360 % 1
                    first, second = (float(c.removesuffix('%')) / 100 for c in parts[1:3])
                    if function == 'hwb':
                        rgb = colorsys.hsv_to_rgb(hue, 1, 1)
                        rgb = tuple((c * (1-first-second) + first) if first+second < 1
                                    else first/(first+second) for c in rgb)
                    else:
                        rgb = colorsys.hls_to_rgb(hue, second, first)
            if len(rgb) != 3:
                raise ValueError('colour needs three channels')
            hue, lightness, saturation = colorsys.rgb_to_hls(*rgb)
            palette = tuple(round(c * 255, 6) for c in rgb) in PURPLE_RGB
            if palette or (260 - 1e-9 <= hue * 360 <= 300 + 1e-9 and
                           saturation > .25 and .2 - 1e-9 <= lightness <= .8 + 1e-9):
                yield literal
        except (ValueError, IndexError) as exc:
            # Unsupported colour expressions cannot silently escape this guard.
            raise ValueError('unresolved colour: ' + literal) from exc


def purple_errors(root):
    errors = []
    for path in site_files(root, '.css'):
        name = path.relative_to(root).as_posix()
        try:
            rules, _ = css_rules(path.read_text(encoding='utf-8'))
            for selectors, declarations, context in rules:
                allowed = (name == 'style.css' and not any(c.startswith('@keyframes ') for c in context) and
                           all(re.fullmatch(r'\.enso(?:\s+(?![+~])[^,]+)?', s) for s in selectors))
                if any(list(purple_colours(c)) for c in context) or (not allowed and
                        any(list(purple_colours(s)) for s in selectors)):
                    errors.append(f'{name}: purple in CSS rule/at-rule prelude')
                for prop, value in declarations:
                    if list(purple_colours(value)) and not allowed:
                        errors.append(f'{name}: purple outside .enso rule: {", ".join(selectors)} / {prop}')
        except (ValueError, StopIteration, UnicodeError) as exc:
            errors.append(f'{name}: Purple: CSS/colour parse failed: {exc}')
    for path in site_files(root):
        if path.relative_to(root).as_posix() in PURPLE_ASSETS:
            continue
        page = read_page(path)
        errors.extend(page.errors)
        try:
            # Include all attributes (not just fill/stroke), and inline CSS.
            values = [v for n in page.nodes for k, v in n.attrs if v is not None]
            values.extend(page.css)
            for value in values:
                if list(purple_colours(value)):
                    errors.append(f'{path.relative_to(root)}: purple in page attribute/inline CSS')
        except ValueError as exc:
            errors.append(f'{path.relative_to(root)}: Purple: colour parse failed: {exc}')
    return errors


def motion_errors(root):
    path = root / 'style.css'
    if not path.is_file():
        return ['Motion: missing style.css']
    try:
        rules, keyframes = css_rules(path.read_text(encoding='utf-8'))
    except (ValueError, StopIteration, UnicodeError) as exc:
        return ['Motion: CSS parse failed: ' + str(exc)]
    errors, used_keyframes = [], set()
    reduce_context = ('@media (prefers-reduced-motion: reduce)',)
    for index, (selectors, declarations, context) in enumerate(rules):
        if any(c.startswith('@keyframes ') for c in context):
            continue
        for prop, value in declarations:
            kind = 'animation' if prop.startswith('animation') else 'transition' if prop.startswith('transition') else None
            if not kind or value in {'none', 'none !important'}:
                continue
            if context == reduce_context:
                errors.append('Motion: active motion in reduced-motion block')
                continue
            if kind == 'animation':
                used_keyframes.update(k for k in keyframes if re.search(r'(?<![\w-])' + re.escape(k) + r'(?![\w-])', value))
            for selector in selectors:
                covered = False
                for override_index, (targets, overrides, conditions) in enumerate(rules):
                    if conditions != reduce_context or override_index <= index:
                        continue
                    # A later universal !important beats ordinary animation;
                    # important source declarations require their exact selector.
                    if selector not in targets and not ('*' in targets and '!important' not in value and '::' not in selector):
                        continue
                    if any(p == kind and v == 'none !important' for p, v in overrides):
                        covered = True
                if not covered:
                    errors.append(f'Motion: {selector} needs reduced-motion {kind}: none')
            if kind == 'animation' and re.search(r'\binfinite\b', value):
                for selector in selectors:
                    # Existing mock finding: .enso is 208px / 174px, reported in
                    # README; preserve its motion per task. No broad exception.
                    if selector not in {'.line-icon', '.icon-tile', '.enso'}:
                        errors.append(f'Motion: infinite animation exceeds an icon: {selector}')
    if keyframes - used_keyframes:
        errors.append('Motion: keyframes without a covered animated selector: ' + ', '.join(sorted(keyframes - used_keyframes)))
    return errors


def check(root, kind='all'):
    root = Path(root)
    errors = discovery_errors(root)
    for name, checker in [('features', feature_errors), ('claims', claim_errors),
                          ('purple', purple_errors), ('motion', motion_errors),
                          ('pages', page_pin_errors), ('visibility', page_visibility_errors),
                          ('hero-contrast', hero_contrast_errors)]:
        if kind in {'all', name}:
            errors.extend(checker(root))
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', choices=['all', 'features', 'claims', 'purple', 'motion', 'pages', 'visibility', 'hero-contrast'], default='all')
    parser.add_argument('root', nargs='?', type=Path, default=ROOT)
    args = parser.parse_args()
    errors = check(args.root, args.check)
    print('\n'.join(errors) if errors else 'PASS: v5 ' + args.check)
    return bool(errors)


if __name__ == '__main__':
    raise SystemExit(main())
