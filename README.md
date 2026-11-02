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

`check_v5.py --check features|claims|purple|motion|pages|visibility|hero-contrast -- .` exposes the individual
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
CSS visibility pin SHA256: `ecb176cbd33db5b40a53008ece251bbb0ce452d9d8256a5ef33e20e0822c269a`.
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

Round 4 added reduced motion to settle `arrive` and the scroll-driven
`enter-view` animation during audits. The subsequent browser/axe finding for
this round identifies the four home hero errors as incomplete background
resolution caused by the hero's own gradient, not animation or failed contrast.
The generated pa11y config continues to add Chromium's
`--force-prefers-reduced-motion` launch argument, activating the existing
reduced-motion CSS (no animation, full opacity) before measurement. It retains
all trusted defaults: WCAG2AA, axe, autocomplete-valid, avoid-inline-spacing,
target-size, 30000ms timeout and --no-sandbox. The trusted `.pa11yci.json`,
html-validate@9.0.0 and pa11y-ci@4.0.0 pins remain unchanged. Candidate configs
are still ignored; generated config/logs stay outside the served tree and are
removed automatically. No contrast rule is ignored or relaxed.

Round 4 verification: 249 passing tests (all 247 prior methods plus two regressions);
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


Round 5 moves the home glow from `.hero` to its empty decorative `::before`.
The exact radial-gradient arguments and both `--glow` theme values are retained.
The hero is positioned relatively and isolated; the absolute pseudo-element
uses `inset: 0`, `z-index: -1` and `pointer-events: none`. It occupies the same
padding box as the original background, adds no layout dimensions or overflow,
and paints below the hero copy, actions and enso inside the isolated stack.
No rule or page depends on the hero owning a background. The text and ring
retain their existing styles and stacking above the decoration.

All eight pages and all stylesheets/SVGs were inspected: this is the only
background gradient or glow-token use. Other surfaces use solid paper/card/
primary/neutral fills or box shadows; the ring uses fills/strokes. They require
no changes. These are static CSS/markup findings; browser rendering and axe
confirmation remain unavailable offline. The reported browser finding is
supplied with the task, not independently reproduced here.

Only `style.css` changes the rendered site. Its new SHA256 is
`ecb176cbd33db5b40a53008ece251bbb0ce452d9d8256a5ef33e20e0822c269a`,
re-pinned in `scripts/check_privacy_text.py` and above. All HTML, page-pin files,
page-pin hashes, Legal bytes, colours, typography, spacing, breakpoints and
animation rules remain byte-identical to this round's input. The pa11y `wait`
and generated `--force-prefers-reduced-motion` argument are retained, with no
rule disabled or relaxed. The existing visibility audit already permits a
negative decorative z-index; no checker exemption or weakening is needed.

Round 5 verification: 252 passing tests (all 249 prior methods plus three
regressions); 206/206 mutants caught (all 202 prior IDs plus M203–M206). The new
regressions first failed before the CSS fix. Parsed CSS checks confine every
background/background-image gradient to the decorative pseudo-element, retain
the exact gradient, and require its bounded, isolated stacking and pointer
behaviour. Visibility checks accept that decoration while still rejecting
hidden hero text. M203 restores the content-bearing gradient, M204 removes
isolation, M205 raises the glow to the content layer and M206 incorrectly marks
the decorative negative layer as hiding. Assertion failures alone count as
mutant catches. No network, installs or workspace Git writes are used.

Round 5 artifacts were `../test.txt`, `../tree-run.txt` and
`../DIFF-r4-to-r5.patch` (superseded below). The tree run attempts all seven CI entries using the
complete `out` tree. Package invocations use `--offline --no-install` and a
temporary npm cache; html-validate and pa11y-ci are unavailable (ENOTCACHED).
Links, no-third-party, privacy-text and invariants pass. The a11y entry stops
because localhost binding raises `PermissionError`; a separate dependency probe
stubs only server startup/readiness and invokes the real generated pa11y config,
returning ENOTCACHED. Author checking passes using only a synthetic noreply
history in an automatically deleted `$TMPDIR` repository. Commands and actual
entry results are recorded in `tree-run.txt`; publication history, hosted checks
and visual/browser confirmation are not verified by this offline run.


Round 6 addresses axe's reported incomplete background resolution beneath the
hero pseudo-element. `scripts/ci_checks.py` copies the whole candidate into the
existing temporary directory, appends exactly one rule to that copy's stylesheet:
`.hero::before { display: none !important; }`, and serves the copy. The source
candidate is never opened for writing. Config and logs remain outside both the
candidate and the served copy; the entire temporary directory is removed on
success or failure. The published glow, all page words, CSS bytes, pins,
validator versions, trusted config, rules, wait and reduced-motion setting are
unchanged. No axe rule or incomplete-result handling is disabled.

The `invariants` CI entry now also enforces `hero-contrast` through `check_v5.py`.
Its pure-Python implementation in `scripts/hero_contrast.py` consumes the existing
CSS parser, requires both complete theme palettes, and parses six-digit opaque
hex surface/text colours and space-separated RGB glow channels with percentage
alpha. Missing/duplicate/scoped tokens, unsupported colour forms, out-of-range
channels/alpha, malformed CSS and unreadable CSS fail closed. The bounded hero
paint contract checks the actual ink/soft/button colour references and surfaces.
The pseudo-element must be exactly the empty, absolute, inset-zero decoration,
with `content: ""`, `pointer-events: none`, `z-index: -1` and the original gradient;
text, extra declarations, different stacking or a second decoration rule fail.
The independent stylesheet hash and all prior page/visibility checks still run.

The calculation composites unrounded sRGB channels as
`peak = alpha * glow + (1 - alpha) * paper`, then applies WCAG sRGB linearisation
and relative luminance. Peak RGB is (242.55, 242.8, 243.35) in light mode and
(30.4, 29.2, 33.84) in dark mode. Monotone channel direction is required; endpoint
luminances and a foreground-crossing check additionally cover every intermediate
radial stop. Ratios below are computed at peak alpha, without rounding before
comparison. Filled buttons use their opaque fill, which covers the glow.

| Hero colour pair | Light ratio | Dark ratio | Enforced minimum |
| --- | --- | --- | --- |
| Ink / peak glow (heading and outlined-button text) | 14.786630:1 | 14.454961:1 | 4.5:1 |
| Soft / peak glow (12px eyebrow, 18–20px description) | 5.992412:1 | 8.387435:1 | 4.5:1 |
| Primary button text / fill | 16.438550:1 | 14.223653:1 | 4.5:1 |
| Primary button text / hover fill | 12.736615:1 | 12.162296:1 | 4.5:1 |
| Outlined-button text / hover fill | 14.223653:1 | 13.036719:1 | 4.5:1 |
| Non-text button border / peak glow | 3.846526:1 | 6.155360:1 | 3:1 |

Every text role is checked at 4.5:1, including the heading; the implementation
uses no large-text exemption. WCAG allows 3:1 only for large text (24 CSS px,
or about 18.67 CSS px when bold); the small eyebrow, description and buttons
retain 4.5:1. The border row is a non-text graphical boundary, checked at its
separate 3:1 requirement. If 4.5:1 was intended for the border itself as well as
the outlined button's text, that cannot be met with the required unchanged CSS:
the existing light border is 3.846526:1. No text threshold is reduced for it.

Round 6 verification: **266 passing tests**, comprising all 252 prior methods
and 14 new methods; **227/227 mutants caught**, retaining all 206 prior mutants
and adding M207–M227. Tests cover excessive glow, invalid/missing/scoped tokens,
colour maths and peak blends, both theme thresholds, small text, button states,
non-text borders, non-decorative pseudo-elements, parse failures, CI wiring,
and the exact temporary-copy override and preservation of every candidate byte,
including cleanup after validator failure. Only assertion failures count as
mutant catches; each mutant also needs a passing focused baseline.

Current artifacts are `../test.txt` (tests and mutants), `../tree-run.txt`
(all seven CI entries), and `../DIFF-r5-to-r6.patch` (`diff -ru ./in/base ./out`
from the job folder). The tree run forces
`--offline --no-install` with empty temporary npm caches. html-validate@9.0.0
and pa11y-ci@4.0.0 fail offline with ENOTCACHED. The full a11y entry also cannot
bind localhost in this sandbox (PermissionError); a separate dependency probe
mocks only server startup/readiness and invokes the real generated config and
package command against the actual audit copy. This does not constitute a
browser validation. Links, no-third-party, privacy-text and invariants pass.
Authors passes against an automatically removed synthetic noreply-only history
under `$TMPDIR`; publication history is unavailable. No network, installs or
workspace Git writes were used; temporary repos/caches/copies are deleted.


Round 7 pins the public head without changing any page, CSS, original Legal
file or existing body pin. Each `legal/page-pins/<page>.head.txt` is one UTF-8
JSON record containing the exact decoded title and description, followed by a
newline. `scripts/page_pins.py` authenticates every head pin with a fixed
SHA256 mapping and compares its canonical bytes with the parsed page. Missing,
duplicate or empty/whitespace-only titles and descriptions fail independently
of text equality. The exact current head element/attribute sequence is an
allowlist: charset, viewport, CSP, referrer, title, description, three icon links
and stylesheet. Additions, omissions, changed attributes and unlisted meta/link
elements fail. No Open Graph or Twitter metadata currently exists; adding it
requires explicit trusted review rather than silently adding public text.

The explicit generator now emits both body and head pins and prints both digest
maps. It rejects invalid heads and remains absent from CI. Regeneration from
`in/base` preserved all eight body pins byte-for-byte. New head pin SHA256 values:

| File under `legal/page-pins/` | SHA256 |
| --- | --- |
| `404.html.head.txt` | `ff8947135db27de76b348baddc7e778867043c14e6218e3bebebb0c72aa81094` |
| `about.html.head.txt` | `657e106bc70d5717c54cdf8b13d1536f3e60c9f2ba2a971ae29bd73509c236b6` |
| `contact.html.head.txt` | `2f88d8dcaa88b8de4164ed91034f7c2b5bd47cb5e83854817d947c84143817b0` |
| `features.html.head.txt` | `ac852ae8bf62d906bd643d9319fc1010900f83c45a0c4cf83992220e8af9b2c9` |
| `how-it-works.html.head.txt` | `af08387396c1d5d66f80c5177004c3c96316f449b07a47286308d663956bb362` |
| `index.html.head.txt` | `e989c9ffbb9080985c693a46d1c59952a0e2125ff05b3f5a29af9abbdbfcd754` |
| `pilot.html.head.txt` | `b93366777c9267da7f403ba48d426fdc19a2270bb911d7ea4916e0ceb9d681c7` |
| `privacy.html.head.txt` | `6faf0bded997aec90381c23f89494859c5ba595eaa03c6120e211dde39d55579` |

Both the banned-word scanner and availability-claim scanner check title text
and description content independently of the pins. Titles now receive both
separated and inline-joined banned-word scans; descriptions are plain attribute
text, checked as a complete string. The availability scanner already scans the
whole head in both text modes and all metadata attributes; direct regressions
now lock this down. The live-chat exception remains confined to position-matched,
complete pinned Features body items. Neither title nor description qualifies,
including on Features. The reported “Every feature is in the private pilot”
phrase fails the exact pin check in either field on every page, even though
that phrase contains none of the existing claim-ban words.

Round 7 verification: **283 passing tests**, retaining all 266 prior methods
and adding 17; **249/249 mutants caught**, retaining all 227 prior IDs and
adding M228–M249. Each mutation needs a passing focused baseline, and only an
assertion failure counts as a catch. Coverage includes title/description changes
on all eight pages, missing/duplicate/empty fields, head pin integrity, unlisted
meta/link elements (including social metadata), direct word and availability
scans, joined-word scans, live-chat scope and reproducible generation.

Round 7 left the Low finding at `scripts/hero_contrast.py:75` unresolved;
the Sol review fixes below now close it independently of stylesheet hashing.

Current artifacts are `../test.txt`, `../tree-run.txt` and
`../DIFF-r6-to-r7.patch` (`diff -ru ./in/base ./out` from the job folder).
All seven CI entries are attempted on the complete tree. Package commands force
`--offline --no-install` using an empty temporary npm cache; html-validate@9.0.0
and pa11y-ci@4.0.0 fail with ENOTCACHED. The a11y entry also cannot bind localhost
in this sandbox; its separate dependency probe mocks only server startup and
readiness, uses the real audit copy/config, and confirms ENOTCACHED. Links,
no-third-party, privacy-text and invariants pass. Authors passes against a full
candidate copy with synthetic noreply-only history in a temporary repository
under `$TMPDIR`; publication history is unavailable. Temporary repos, copies
and caches are deleted. No network, installs or workspace Git writes were used.
Package/browser checks and hosted CI/protection settings remain unverified.

The Sol read-only review fixes authenticate both raw Legal fragments with
SHA256 digests in the trusted `scripts/legal_pins.py` source before either
page comparison or fragment parsing. Candidate baseline edits cannot redefine
approval. Coordinated `<p>` to `<p >` edits across the footer baseline and all
eight pages, and `<h2>` to `<h2 >` edits across the privacy baseline and page,
are rejected even though their parsed page/head pins are unchanged. Existing
semantic/parser regression fixtures explicitly patch only the digest of their
temporary fragment so those independent guards remain exercised.

The hero proof now checks every `color` declaration against guarded paint rules
or the exact remaining approved selector/value/context tuples. The generic
anchor colour joins the paint contract. New selectors such as `main section p`,
universal/attribute/pseudo selectors, selector lists and conditional overrides
fail closed without needing a general CSS cascade engine. Existing decorative
layer validation still applies. No rendered site asset or Legal pin changes.

These fixes add three regressions and mutants M250–M252: 286 tests and an
expected 252/252 mutants. Current results are in `../test.txt`; all seven CI
entries, offline dependency limitations and unavailable publication history are
recorded in `../tree-run.txt`. `../CHANGED-FILES.txt` lists this job's changes.
