"""Fail-closed proof for the decorative glow omitted from the browser audit.

This is a bounded parser for the pinned site's palette and hero paint contract,
not a general CSS cascade engine. Unsupported forms require explicit review.
"""
from pathlib import Path
import re

TOKENS = {'--paper', '--glow', '--ink', '--soft', '--primary', '--primary-text',
          '--primary-hover', '--neutral', '--strong-line'}
DARK = ('@media (prefers-color-scheme: dark)',)
DECORATION = {
    'content': '""', 'position': 'absolute', 'inset': '0', 'z-index': '-1',
    'background': 'radial-gradient(ellipse 75% 65% at 50% 47%, var(--glow), transparent)',
    'pointer-events': 'none',
}
# Colour references must still describe the text/surfaces actually being proved.
PAINT = {
    'body': {'background': 'var(--paper)', 'color': 'var(--ink)'},
    'a': {'color': 'var(--link)'},
    'h1, h2, h3': {'color': 'var(--ink)'},
    'p': {'color': 'var(--soft)'},
    '.btn': {'color': 'var(--primary-text)', 'background': 'var(--primary)',
             'border': '1px solid var(--primary)'},
    '.btn:hover': {'background': 'var(--primary-hover)', 'border-color': 'var(--primary-hover)'},
    '.btn.line': {'color': 'var(--ink)', 'background': 'transparent', 'border-color': 'var(--strong-line)'},
    '.btn.line:hover': {'background': 'var(--neutral)', 'border-color': 'var(--ink)'},
}
# Remaining approved colour rules. Freeze their selector, value and context:
# arbitrary CSS selector matching is outside this bounded proof. These rules
# style non-hero text or the empty decorative enso in the pinned page skeleton.
# All other colour declarations must go through PAINT, even when their selector
# does not mention hero (for example, `main section p` or `*`).
OTHER_COLOURS = {
    (('.skip',), (('color', 'var(--link)'),), ()),
    (('.enso',), (('color', '#7a4fa0'),), ()),
    (('.enso',), (('color', '#c9a6ec'),), DARK),
    (('.icon-tile',), (('color', 'var(--ink)'),), ()),
    (('.step-number',), (('color', 'var(--soft)'),), ()),
    (('.statement p',), (('color', 'var(--ink)'),), ()),
    (('.plain',), (('color', 'var(--soft)'),), ()),
    (('.copy-slot',), (('color', 'var(--soft)'),), ()),
    (('.status-pilot',), (('color', 'var(--ink)'),), ()),
    (('.status-planned',), (('color', 'var(--soft)'),), ()),
}


def colour(value, glow=False):
    """Return unrounded sRGB channels and alpha; reject unsupported CSS."""
    if not glow and re.fullmatch(r'#[0-9a-fA-F]{6}', value):
        return tuple(int(value[i:i + 2], 16) / 255 for i in (1, 3, 5)), 1.0
    match = re.fullmatch(r'rgb\((\d+) (\d+) (\d+) / (\d+(?:\.\d+)?)%\)', value)
    if glow and match:
        channels = tuple(int(match[i]) / 255 for i in (1, 2, 3))
        alpha = float(match[4]) / 100
        if all(0 <= c <= 1 for c in channels) and 0 <= alpha <= 1:
            return channels, alpha
    raise ValueError('unparsable colour/token: ' + value)


def luminance(rgb):
    return sum(weight * (c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
               for weight, c in zip((0.2126, 0.7152, 0.0722), rgb))


def contrast(first, second):
    a, b = sorted((luminance(first), luminance(second)))
    return (b + 0.05) / (a + 0.05)


def hero_contrast_report(root):
    from check_v5 import css_rules
    rules, _ = css_rules((Path(root) / 'style.css').read_text(encoding='utf-8'))
    palettes = {'light': {}, 'dark': {}}
    decorations, paints = [], {}
    for selectors, declarations, context in rules:
        selector = ', '.join(selectors)
        for prop, value in declarations:
            if prop in TOKENS:
                if selectors != (':root',) or context not in ((), DARK):
                    raise ValueError('unsupported hero token scope')
                palette = palettes['dark' if context else 'light']
                if prop in palette:
                    raise ValueError('duplicate hero token: ' + prop)
                palette[prop] = value
        if any('hero' in s and ('::before' in s or ':before' in s) for s in selectors):
            decorations.append((selectors, declarations, context))
            continue
        colours = tuple((p, v) for p, v in declarations if p == 'color')
        if colours and 'color' not in PAINT.get(selector, {}) and (selectors, colours, context) not in OTHER_COLOURS:
            raise ValueError('unsupported hero paint colour rule: ' + selector)
        if selector in PAINT and any(p in PAINT[selector] for p, _ in declarations):
            if context or selector in paints:
                raise ValueError('unsupported hero paint override: ' + selector)
            paints[selector] = {p: v for p, v in declarations if p in PAINT[selector]}
        elif any(re.search(r'hero|eyebrow|\.btn|#home-h', s) for s in selectors) and selector != '.hero::before':
            if any(p in {'color', 'background', 'background-image', 'border', 'border-color',
                         'filter', 'mix-blend-mode', 'backdrop-filter'} for p, _ in declarations):
                raise ValueError('unsupported hero paint: ' + selector)
    if len(decorations) != 1 or decorations[0][0] != ('.hero::before',) or decorations[0][2] or sorted(decorations[0][1]) != sorted(DECORATION.items()):
        raise ValueError('hero::before must be exactly the empty decorative layer')
    if paints != PAINT:
        raise ValueError('hero text/surface colour references changed')
    report = {}
    for theme, values in palettes.items():
        if set(values) != TOKENS:
            raise ValueError(theme + ': missing hero token')
        parsed = {p: colour(v, p == '--glow') for p, v in values.items()}
        rgb = {p: v[0] for p, v in parsed.items()}
        glow, alpha = parsed['--glow']
        paper = rgb['--paper']
        peak = tuple(alpha * g + (1 - alpha) * p for g, p in zip(glow, paper))
        # Monotone channels make endpoint luminances bound every radial stop.
        if not (all(g >= p for g, p in zip(glow, paper)) or all(g <= p for g, p in zip(glow, paper))):
            raise ValueError(theme + ': unsupported non-monotone glow')
        pairs = {
            'ink / peak glow': (rgb['--ink'], peak, 4.5),
            'soft / peak glow': (rgb['--soft'], peak, 4.5),
            'outline / peak glow': (rgb['--strong-line'], peak, 3.0),
            'primary text / fill': (rgb['--primary-text'], rgb['--primary'], 4.5),
            'primary text / hover': (rgb['--primary-text'], rgb['--primary-hover'], 4.5),
            'outline text / hover': (rgb['--ink'], rgb['--neutral'], 4.5),
        }
        ratios = {}
        for label, (foreground, background, threshold) in pairs.items():
            ratio = contrast(foreground, background)
            minimum = ratio
            if label.endswith('peak glow'):
                minimum = min(ratio, contrast(foreground, paper))
                lo, hi = sorted((luminance(paper), luminance(peak)))
                if lo <= luminance(foreground) <= hi:
                    minimum = 1.0
            if minimum < threshold:
                raise ValueError(f'{theme}: {label} contrast {minimum:.4f}:1 < {threshold}:1')
            ratios[label] = ratio
        report[theme] = {'peak_rgb': tuple(c * 255 for c in peak), 'ratios': ratios}
    return report


def hero_contrast_errors(root):
    try:
        hero_contrast_report(root)
    except (OSError, UnicodeError, ValueError, StopIteration) as exc:
        return ['Hero contrast: ' + str(exc)]
    return []
