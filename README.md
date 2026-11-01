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

`check_v5.py --check features|claims|purple|motion -- .` exposes the individual
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

Verification: 211 passing tests (all 191 existing tests retained, with only
required normalisation/claim-exception updates), and 169/169 mutants caught.
The 20 added tests exercise claim scope/pin integrity and purple palette, hue,
selector, SVG/HTML-attribute, parser and CI wiring guards. The 18 added mutants
remove individual protections; a catch requires an assertion failure, never a
syntax/import/runtime error. Each mutant gets a fresh automatically removed
temporary tree. Git writes use only temporary repositories under TMPDIR, removed
at completion. No network, installation or workspace Git write was used.

See `../test.txt`, `../tree-run.txt` and `../DIFF-r1-to-r2.patch`.
The complete-tree links, no-third-party, privacy-text and invariants CI entries
pass. The authors entry passes against a synthetic noreply-only history of the
complete out tree, stored solely in a temporary Git directory; actual publication
history is unavailable in this job. HTML and accessibility package validators are
unavailable offline (`ENOTCACHED`). Their complete-tree commands are attempted
with `--offline --no-install` replacing npx's `--yes`; neither packages nor a
local HTTP server are installed/started. All seven CI entries and the limitations
are recorded in tree-run.txt. The strict HTML preflight runs over all eight pages
and the three SVG assets, but does not replace the unavailable package/browser
checks. Browser visual acceptance, WCAG verification and hosted settings remain
unverified locally.
