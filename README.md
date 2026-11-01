# Site checks

The eight UX v5 pages are `index.html`, `features.html`, `how-it-works.html`,
`pilot.html`, `about.html`, `contact.html`, `privacy.html` and `404.html`.
Pages publishes main `/` with the empty `.nojekyll` and unchanged `CNAME`.
Round 2 applies `../in/v5-pass3.diff`, then `../in/neutral.diff`, mapping
the mock's `site.css` to `style.css`. All eight hunks matched their complete
context exactly; no hand resolution or apostrophe adjustment was needed.
The pass-3 diff formats Features headings/titles/statuses and narrows header
navigation targets. The neutral diff changes theme/focus/button styling and
adds the purple enso dot and ring colour. No other page/CSS bytes changed.

The required status names remain `html`, `links`, `no-third-party`, `a11y`,
`authors`, `privacy-text`, `invariants`. The last also runs `check_v5.py`.
PR enforcement comes from the separate trusted `base.sha` checkout. Pushes use
main's checks. Only a wholly absent base check system permits the documented
first-PR self-check fallback. Candidate configs never replace trusted configs.
The workflow is unchanged: read-only contents permission, full action SHA pins,
no secrets, environment or deployment. Pages uses its separate branch build.
Security's W1–W4 review and protection settings still apply; this offline job
neither verifies nor changes remote settings. Code owners already cover
`/.github/`, `/scripts/`, `/legal/`, both check configs, package files and
`*.config.*`. No new ownership/config path was needed.

Run from this directory, without packages:

```sh
python3 -I -B scripts/test_checks.py
python3 -I -B scripts/test_mutants.py
python3 -I -B scripts/site_common.py -- .
python3 -I -B scripts/check_links.py -- .
python3 -I -B scripts/check_no_third_party.py -- .
python3 -I -B scripts/check_privacy_text.py -- .
python3 -I -B scripts/check_invariants.py -- .
python3 -I -B scripts/check_v5.py -- .
```

`check_v5.py --check features|claims|purple|motion|pages|visibility -- .` exposes the individual
checks. The fixed `/legal/approved-features-copy.txt` path is never selected by
candidate config. Its UTF-8 JSON comes from the publication block between the
first two separators in `../in/website-features-copy.md`; internal notes are
excluded. Regenerate it with:

```sh
python3 -I -B scripts/normalize_features_copy.py ../in/website-features-copy.md legal/approved-features-copy.txt
```

The exact display normalisation code in that extractor is:

```python
section = {'heading': re.sub(r'^Section \d+: ', '', heading), 'items': []}
# title, sentence, status are the three captured Markdown item fields.
section['items'].append([title.removesuffix('.'), sentence, status.removesuffix('.')])
```

No other source string changes. Sentences retain their full stops. Comparing the
regenerated JSON with the round-1 pin after only those same normalisations gives
identical data. The pin retains all three sections and 36 item triples.

Features pin SHA256: `1e70dd45e954473a3c81eb6d982757cecd2f402b0bbe906d2ac2aa03f2eaf83e`.
CSS visibility pin SHA256: `9221d0b9649615378c1d4b2d12dacaaab20ae61fd0ab346bde4da6fcbdb9d82b`.
The copy check enforces the full visible sequence, exact slots, whole-page
occurrence counts, per-row associations and status counts: 6
`Planned for the private pilot`, 30 `Planned`, 0 `In the private pilot`.
Occurrence expectations account for approved overlaps such as Ami in sentences,
Email in longer titles, Building in the unchanged Legal footer, and Planned in
the pilot label. Duplicates outside main still fail. Per-page Legal placement
pins need no changes; their existing tests pass with the new page/CSS bytes.

The claim ban scans all page text, including hidden/SVG/head text, and attributes.
Only the exact case-insensitive phrase `live chat` in a complete pinned Features
item is allowed. Complete row text, including hidden text, must match the trusted
pin in its item position; only phrase case may vary for this claim exception.
The separate copy check still requires exact case. Attributes are never covered
by this exception. `go live`, unpinned rows, other page regions/pages and modified
pin files fail. Existing exact Legal-element exceptions for other claim words
remain; `live` is still checked in their text and attributes.

The pre-neutral stylesheet's complete purple literal list is `#7a4fa0`,
`#68408c`, `#c9a6ec`, `rgb(122 79 160 / 7%)`, `rgb(122 79 160 / 12%)`.
The two logo SVGs add no distinct values. The icon also has pale `#e2cff3`, which
is explicitly protected even though its lightness exceeds the hue guard's range.
Equivalent RGB identities are purple regardless of alpha or spelling. In addition,
any parsed colour at hue 260–300 degrees inclusive, saturation >25%, lightness
20–80% inclusive is purple. Hex, RGB, HSL, HWB, sRGB and purple colour names are
covered; unsupported colour-space expressions fail closed. The existing trusted
CSS hash also continues to reject all unapproved stylesheet changes.

Purple is allowed only in the two pinned `img/coami-logo*.svg` assets,
`coami-icon.svg`, the two pinned favicon assets, and `style.css` rules whose
selectors are all `.enso` or its descendants. Mixed selector lists, sibling
selectors, lookalike classes and other stylesheets fail. Every page attribute,
inline SVG fill/stroke and inline CSS is scanned; inline enso SVG attributes do
not get a colour exception. The neutral diff uses `currentColor` there instead.

All eight pages require the exact Security addendum-2 CSP and no-referrer meta:

```text
default-src 'self'; img-src 'self' data:; style-src 'self'; font-src 'self'; script-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'
```

Discovery fails on any unlisted HTML/HTM/XHTML/SVG document, including extra
Legal HTML. The only HTML discovery exceptions remain the two immutable Legal
fragments. The only SVG documents are the three pinned icon/logo assets.
Unknown public types, unsafe paths, symlinks and extra .github files fail.
The fonts, license, images, icons, domain, nojekyll and pre-existing Legal folder
files retain their baseline bytes; only the Features .txt pin was regenerated there in round 2.

All content checks share the consuming strict tokenizer and static per-element
allowlist. Byte-zero doctype, early literal UTF-8 charset, exact document order,
explicit balanced end tags, double-quoted attributes, restricted entities,
content models, duplicate attributes, forbidden directives/comments, SVG XML
namespace/DTD restrictions and resource gates remain enforced. No scripts,
styles, inline CSS, forms, iframes, cookies, analytics or external loads were added.
The existing exact outbound URLs and mailto destinations were not extended.
One exact local Urbanist @font-face is approved, now using the mock's spelling;
all other CSS resources and duplicate font-face declarations fail.

The element vocabulary did not expand. These are every attribute extension,
each required by the mock and not removable without changing rendering,
semantics or keyboard behaviour:

| Element | Attribute | Reason |
| --- | --- | --- |
| a | aria-current | Current page indicator and its CSS underline |
| h1 | id | Existing section aria-labelledby reference |
| li | class | Card/feature layout and reveal motion on list items |
| main | tabindex | Focusable skip-link target with tabindex=-1 |
| section | class | Hero, intro, reading and reveal styling |
| SVG path | class | enso-line styling on the hero ring |

Protected Legal class/position maps now explicitly list all eight pages. The
footer remains exactly once, byte-identical, inside the mock footer-band;
privacy retains exactly one unchanged article and every other page forbids it.
The privacy header and separate footer navigation are pinned to v5, with exact
brand images and links. Extra visible text outside these approved regions fails.
CSS changes still require an explicit trusted hash review. Existing image/font
hashes, magic bytes and Legal/D26 semantic and raw-byte checks are unchanged.

The CSS motion checker consumes balanced rules, declarations and nested at-rules,
tracking reduced-motion context and keyframe usage. Every animation/transition
selector must have a later reduced-motion none override. The mock's final
universal !important rule covers ordinary declarations; important source rules
require an exact selector override. Orphan/new uncovered keyframes, missing or
misconditioned overrides, malformed CSS and new oversized infinite animations
fail. The parser preserves the mock's @supports/view-timeline enhancement.

**Motion finding preserved from the mock:** `.enso` uses `breathe 8s ease-in-out
infinite` on the home-page ring, 208 by 208 px on desktop and 174 by 174 px at the
560 px breakpoint. This exceeds an icon. It is reported rather than altered, per
the task. It is the single explicit existing infinite-motion exception; the CSS
hash pins its exact dimensions and motion. Reduced-motion rules disable it.

Round 3 pins the complete body skeleton of every page under `legal/page-pins/`.
Each JSON line records the element path and tag, ordered class list, every other
attribute (including all href, aria-*, id, src and alt values), and ordered content
slots containing exact direct text or a child path. Whitespace, empty elements,
inline SVG, nesting and the placement of text around children are retained.
Nothing is filtered for visibility. The fixed digest mapping in
`scripts/page_pins.py` authenticates each pin; candidate config cannot select or
regenerate it. Added, removed, reordered, reclassed, reparented or edited elements
fail on all eight pages, even when a new sentence contains no banned word.
All existing page, stylesheet and Legal pin bytes remain unchanged.

The generator was run against the complete round-2 baseline, with no page edits:

```sh
python3 -I -B scripts/generate_page_pins.py --source ../in/base --destination legal/page-pins
```

This explicit review tool prints digests; it does not edit the trusted check.
It is never called by CI. A separate temporary regeneration is byte-identical.

The shared default text extractor now separates every element boundary,
including inline spans, links, emphasis, empty elements, br, list items and SVG.
Claims are scanned on this separated text on every page, including head/hidden
text and attributes. The original inline-joined scans are also retained for both
claim bans, preserving rejection of words split inside inline markup. The
live-chat exception remains confined to complete, position-matched approved
Features items with a valid Features pin; attributes remain outside it. Existing
case and exact-phrase tests are unchanged. The privacy comparison now separates
Markdown link boundaries and header navigation in the same way as the shared
extractor; neither the D26 source nor its byte pins changed.

The independent visibility audit parses every stylesheet and nested media or
supports rule. It conservatively associates selectors with each used class,
including ancestor/descendant and pseudo-selector appearances; selectors without
class tokens are audited against all body elements. It rejects hiding display,
visibility, clipping, zero opacity/font size, positioned offscreen offsets,
large translations, offscreen text indentation, and zero-height/clipped-overflow
combinations, including declarations split across rules. Unresolved visibility
variables/arithmetic fail closed. No later cascade override excuses a hiding
rule. Existing strict CSS parsing, stylesheet hash, resource checks and motion
checks remain active. Only exact original hiding-rule fingerprints at exact
pinned skip-link or logo nodes are exempt; adding these classes elsewhere fails.
Unapproved visibility attributes fail independently as well.

Current CSS audit findings (preserved): `.skip` is fixed and translated -180%
until focus (style.css:67); `.brand-dark` is hidden in the default theme (:73);
`.brand-light` is hidden in dark mode (:75). These are the only hiding qualified
rules, and their exceptions are bound to pinned nodes and complete rules.
`arrive` (:173) and `enter-view` (:175) additionally start at opacity 0 in
transient keyframe states. The visibility audit covers qualified element rules,
not transient keyframe states; these existing animations retain the unchanged
CSS hash and reduced-motion guards. The previously reported enso motion finding
above also remains. No page or CSS change was forced or made.

Round 4 fixes the two reported GitHub failures without changing displayed text,
CSS, colours, layout, approved Legal files or either pinned validator config.
The home hero and closing section referenced different IDs, but both headings
resolve to "Plan and build software with Ami." Named sections are region
landmarks, so this was a real duplicate accessible name. Only the redundant
`aria-labelledby="closing-h"` was removed from the closing section; its heading
remains available to heading navigation. `unique-landmark` stays enabled with
all recommended rules. All eight pages were checked: every remaining named
section has exactly one non-empty heading target, names are unique per page,
and the two nav names remain Main and Footer. No other page needed edits.

Only `legal/page-pins/index.html.txt` changed, by removal of that attribute in
one record. Its new SHA256, enforced in `scripts/page_pins.py`, is
`b8ef814cddc21ad5c428efe0cc611f4170d7a750f4837631879fe6c784d0aef6`.
The other seven pin hashes and all `legal/approved-*` bytes remain unchanged.
The existing pin-integrity regressions still reject tampered pin bytes.

Contrast was calculated from the unchanged CSS using WCAG sRGB linearisation,
relative luminance and `(Llighter + 0.05) / (Ldarker + 0.05)`. The affected
Features items use ink for h3/pilot status and soft for paragraphs, on paper.
Other feature tiles use card; their planned statuses use soft.

| Settled colour pair | Light theme ratio | Dark theme ratio |
| --- | --- | --- |
| Ink / paper | #241c2c / #fbf8f4: 15.53:1 | #f2eee8 / #141216: 16.11:1 |
| Soft / paper | #625969 / #fbf8f4: 6.29:1 | #bdb5c1 / #141216: 9.35:1 |
| Ink / card | #241c2c / #ffffff: 16.44:1 | #f2eee8 / #1e1b21: 14.73:1 |
| Soft / card | #625969 / #ffffff: 6.66:1 | #bdb5c1 / #1e1b21: 8.54:1 |
| Ink / hero gradient | 14.79–15.53:1 | 14.45–16.11:1 |
| Soft / hero gradient | 5.99–6.29:1 | 8.39–9.35:1 |
| Primary button text / fill | #ffffff / #241c2c: 16.44:1 | #241c2c / #f2eee8: 14.22:1 |

The hero's h1 and outlined "About the private pilot" button use ink; its
eyebrow and hero-description use soft. The gradient ranges conservatively cover
transparent through peak glow: light `rgb(238 240 243 / 65%)` over paper gives
RGB (242.55, 242.8, 243.35); dark `rgb(150 158 170 / 8%)` gives
(30.4, 29.2, 33.84). All ratios exceed even the 4.5:1 normal-text requirement.
These are settled colour calculations, not a browser/axe reproduction.

`arrive` starts the hero at opacity 0, and `enter-view` starts Features reveal
items at opacity 0. The latter follows scroll position, so waiting 600ms alone
cannot settle a partially entered item. This explains how intermediate states
can generate the reported contrast errors despite passing settled colours.
The generated pa11y config now adds Chromium's
`--force-prefers-reduced-motion` launch argument, activating the existing
reduced-motion CSS (no animation, full opacity) before measurement. It retains
all trusted defaults: WCAG2AA, axe, autocomplete-valid, avoid-inline-spacing,
target-size, 30000ms timeout and --no-sandbox. The trusted `.pa11yci.json`,
html-validate@9.0.0 and pa11y-ci@4.0.0 pins remain unchanged. Candidate configs
are still ignored; generated config/logs stay outside the served tree and are
removed automatically. No contrast rule is ignored or relaxed.

Verification: 249 passing tests (all 247 prior methods plus two regressions);
202/202 mutants caught (all 200 prior IDs plus M201 and M202). The new tests
first failed on the unmodified behaviour. Each mutant catch requires an
assertion failure, never a syntax, import or runtime error. `MUTANTS.md` maps
all mutants to regressions. Temporary mutation trees and the synthetic author
repository are removed automatically. No network, installs or workspace Git
writes were used.

See `../test.txt`, `../tree-run.txt` and `../DIFF-r3-to-r4.patch`.
All seven CI entries are attempted against the complete out tree. The local
package commands replace npx --yes with --offline --no-install, preserving
validator versions and configs. HTML validation and a separate pa11y package
probe return ENOTCACHED offline. The full a11y entry also stops before package
invocation because this sandbox denies localhost binding; the dependency probe
stubs only server startup/readiness and uses the real generated config.
Links, no-third-party, privacy-text and invariants pass;
authors passes against a synthetic noreply-only history with all Git writes
under $TMPDIR, not the unavailable publication history. Package validation,
browser confirmation of the contrast fix and hosted settings remain unverified.
Detailed commands, actual results, contrast calculations and preservation
checks are recorded in tree-run.txt.
