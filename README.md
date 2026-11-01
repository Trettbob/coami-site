# Site checks

Pages publishes main `/` with `.nojekyll`. The pages use the approved UX v4
mock, the supplied Urbanist font, and Security ruling addendum 2 CSP. Require these status names: `html`, `links`, `no-third-party`, `a11y`,
`authors`, `privacy-text`, `invariants`.

On PRs the workflow checks out `github.event.pull_request.base.sha` separately
into `base/`, with credentials persistence disabled. Validators, regression tests,
HTML and accessibility configs come from that base, and inspect the candidate in
`site/`. Pushes to main use main's own checks. Only when the base has no checks
at all does the first PR use its own checks, with a prominent
`WARNING: BASE HAS NO CHECKS; THIS FIRST-PR RUN IS SELF-CHECKED` line. An incomplete
base check system fails closed. A report lists changed `.github/`, `scripts/`,
`.htmlvalidate.json`, `.pa11yci.json` and `legal/` paths without failing the run.

**Residual limit:** a PR can edit the workflow that chooses enforcement, and the
first PR is self-checked. Branch protection cannot distinguish a trustworthy
check implementation from a weakened one with the same status name. A PR
changing checks needs Security's read of those changes before merge, as required
by P3; require that review operationally. Base checks intentionally remain in
force until changes to checks merge. New check systems must be complete on base;
missing validators/runners fail rather than silently selecting PR code.

The workflow retains read-only permissions, pinned GitHub-owned action SHAs,
timeouts and concurrency cancellation. It has no secrets, environment or deploy
step. Pages uses its separate branch build.

Run offline from the repository root (Python 3.10+, no packages):

```sh
python3 -I -B scripts/test_checks.py
python3 -I -B scripts/test_mutants.py
python3 -I -B scripts/check_links.py -- .
python3 -I -B scripts/check_no_third_party.py -- .
python3 -I -B scripts/check_privacy_text.py -- .
python3 -I -B scripts/check_invariants.py -- .
python3 -I -B scripts/site_common.py -- .  # NUL-delimited ./ paths
```

Discovery excludes `.git/` and treats only the two exact owner-reviewed Legal
HTML pins as baseline data, validated by the Legal checks instead of as pages. Case-insensitive `.html`, `.htm`, `.xhtml` and
`.svg` are documents; the exact expected set is `index.html`, `privacy.html`,
`404.html`, `favicon.svg`. Unexpected/missing documents, symlinks, unsafe paths
and unsupported served file types fail. With `.nojekyll`, `.md` files are served
raw, not rendered as HTML. If `.nojekyll` disappears, discovery includes Markdown
as possible rendered documents and invariants also fail. Supported raw types are
`.md`, `.txt`, `.py`, `.yml`, `.yaml`, `.json`, `.css`, `.patch`, plus exact paths `CNAME`,
`.nojekyll`, `.github/CODEOWNERS`, and `fonts/urbanist-latin-var.woff2`; other types require an explicit checker change and Security review.
Test data is Python string data; there are no published test HTML fixtures.
Tests use isolated temporary directories under `$TMPDIR` and remove them. They
mock Git output for unit tests and create automatically removed temporary Git
repositories for the complete-tree authors smoke test. CLI discovery emits ASCII `./` paths
separated by NUL. Tool invocations use argument arrays and option terminators
where supported; page paths must match `^[A-Za-z0-9._/-]+$` and have no controls.

Every HTML page requires exactly one CSP meta, directly under an active head,
before resource-capable elements. The policy comes from Security ruling
addendum 2; the old P4 policy without font-src fails. Content must equal these ASCII bytes in this
order, with no whitespace or directive normalization:

```text
default-src 'self'; img-src 'self' data:; style-src 'self'; font-src 'self'; script-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'
```

Every SVG file is parsed as XML by stdlib `xml.etree.ElementTree`, with a custom
TreeBuilder that refuses every DTD before entities can expand and refuses XML
processing instructions. Malformed XML and a root outside the SVG namespace
fail. HTML and SVG also undergo a lexical check: no internal DTD subsets,
entity declarations or external DTDs; only HTML's simple `<!doctype html>` is
allowed. Only `amp`, `lt`, `gt`, `apos`, `quot` and decimal/hex numeric entity
references are allowed, with semicolons. Other HTML named entities also fail.
Duplicate attribute names fail case-insensitively, before dictionary conversion,
in every HTML element and SVG element. HTML comments containing validator text
(`html-validate`, `eslint`, `pa11y`, `axe`, case-insensitively with whitespace
removed) fail. The CI runner performs this markup preflight before validators
can read inline directives.

SVG element allowlist (XML names are case-sensitive; inline HTML SVG uses the
HTML parser's normalized names): `svg`, `g`, `rect`, `text`, `circle`, `ellipse`,
`path`, `line`, `polyline`, `polygon`, `title`, `desc`, `defs`, `clipPath`.
SVG attributes are now per element in `scripts/allowlist.py`, narrowed from r4:
`svg`: aria-hidden/class/focusable/viewBox; `rect`: fill/height/rx/width;
`text`: fill/font-family/font-size/font-weight/text-anchor/x/y;
`circle`: class/cx/cy/fill/r. The other permitted SVG elements accept no
attributes until owner review. The older XML vocabulary check remains as an
additional case-sensitive guard.
XML namespace declarations are consumed by ElementTree; elements must be in
`http://www.w3.org/2000/svg` and the permitted attributes are unqualified. Unknown
namespaces fail. The approved favicon and inline SVG pass. `feImage`, `image`,
`use`, `foreignObject`, `script`, `animate*` and `set` are excluded entirely,
including with fragment hrefs. SVG navigation receives no outbound exception.

HTML meta CSP and the Legal footer apply to the three HTML pages (they have no
effect as HTML constructs in an SVG image). No page has or needs a refresh; every meta
refresh is rejected, including local ones. Scripts, forms, frames, embeds,
objects, inline CSS, event attributes and resource hints are forbidden. `srcset`, `poster`, `ping`,
CSS `url()`, `image-set()` and `@import` fail even with local values, except
exactly one approved Urbanist @font-face declaration in root style.css. CSS comments
and escapes are decoded before scanning, including `style.css` and every HTML
and SVG attribute (including paint values such as `fill`). This retains r3's
strict resource guard for every other CSS resource function. All `href`, `xlink:href` and
`src` attributes require relative URLs, except HTML `<a href>` navigation.

Resource URLs must be relative. Navigation allows relative same-origin document
paths/fragments and only these existing absolute links (the ruling permits plain
outbound links but provides no enumerated allowlist). Full URL membership checks
scheme, host, port, path and query exactly, so alternative ports and lookalike
origins fail:

- `https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement`
- `https://ico.org.uk/make-a-complaint/`
- `mailto:hello@coami.ai`
- `mailto:hello@coami.ai?subject=CoAmi%20pilot`
- `mailto:privacy@coami.ai`
- `mailto:security@coami.ai`

The privacy check requires `privacy.html` and forbids any `privacy/` folder.
Its main visible text equals D26 with only interword whitespace normalized;
quotes and dashes remain exact. D26's approved SHA256 is
`6842c06ee3bd94f90a16f4fe5b040b1454716e3a54f103cf2474a9075adc8852`.
It rejects `hidden`, `popover`, `inert`, any `aria-hidden` value and any `style`
attribute on/inside/above the notice and every footer. It rejects templates,
noscript, closed details and unapproved notice tags. `legal_visibility.py` pins
classes separately for each page at exact DOM paths (same-tag sibling ordinals)
revalidated against the approved v4 pages (the protected paths/classes are unchanged). Unlisted places require no classes; approved classes
cannot migrate to other elements, and `skip` cannot hide Legal text.
It pins the approved `style.css`
SHA256 and permits only that stylesheet: this conservative visibility guard
rejects CSS changes for review instead of attempting to emulate CSS rendering.
The skip link, exact header and Legal footer are the only permitted visible text
outside main; both the "privacy statement" and "ICO" hrefs must equal their D26
URLs exactly, each appearing once inside main. CSS changes need a
visibility review and an updated trusted hash.

Invariants enforce `CNAME` as `coami.ai` with at most one LF, an existing empty
`.nojekyll`, the exact visible Legal footer and its links on every HTML page,
and the design note's banned copy. Banned tokens are checked case-insensitively
as words, including the registered mark, testimonials and numeric user claims.
The body copy scanner includes aria-hidden subtrees and SVG text; only head
metadata (scanned separately), true hidden elements and templates are excluded.
Hidden/template constructs still fail the markup allowlist.
The same check covers `<title>`, description metadata, `og:*` and `twitter:*`
metadata (both `name` and `property`), and all `alt`, `title` and `aria-label`
attribute values, even when the element is outside visible body text.

`test_mutants.py` makes a fresh temporary copy per guard removal and runs its
named regression. A caught mutant requires an assertion failure, never an
import/syntax/runtime error. The current report is `../MUTANTS.md`; no production
guard has a test-only disable flag. The workflow and its triggers are unchanged;
the enforcement-swap risk remains subject to Security W1–W4 settings/review.

The authors check reads raw author AND committer emails for every commit in
`base.sha..head.sha` on PRs or `before..after` on pushes (all reachable history
for an all-zero before). It allows only numeric GitHub noreply IDs with
`[A-Za-z0-9-]+` names, or `noreply@github.com`. Failures show commit and role
without printing private emails:

```sh
python3 -I -B scripts/check_authors.py --root . -- base-sha..head-sha
```

HTML validation uses html-validate 9.0.0 with the trusted explicit config;
accessibility uses pa11y-ci 4.0.0 with a temporary config derived from the trusted
base and the candidate's HTML paths. No new actions or dependencies were added.
Those existing Node/browser tools are unavailable locally; no network or
installs are used here. Every matrix entrypoint is attempted; see ../tree-run.txt
for the precise tool/server limitations. Complete-tree discovery, strict
preflight and Python content checks pass. Authors verification uses only a
synthetic temporary repository, not actual repository history. Full WCAG 2.2 AA and visual acceptance need manual
browser review. The offline suite covers validator behavior, trust selection,
command construction and attempted candidate validator replacement.

## Round 5: shared markup allowlist

`allowlist.py` holds the owner-reviewed element/attribute tables. Every content
checker and every CI matrix preflight reads it through `site_common.read_page`.
HTML permits exactly the elements/attributes observed in the three approved v4
pages; SVG retains r4's element vocabulary with the per-element attributes above.
Unknown names fail, including custom elements, every unused `data-*` name,
legacy backgrounds, templates/shadow DOM, popovers and inline CSS. End tags also
undergo vocabulary checks. Per-element tables prevent an attribute allowed on
one element from being used on another. These are static trusted data, never
inferred from candidate pages during checking.

HTML element attributes (empty means none):

| Element | Attributes |
| --- | --- |
| a | aria-label, class, href |
| article, div, footer, header, ol, p, span, ul | class |
| body, h1, h3, head, li, title | none |
| h2 | class, id |
| html | lang |
| link | href, rel, type |
| main | id |
| meta | charset, content, http-equiv, name |
| nav | aria-label |
| section | aria-labelledby, id |

Every HTML document requires one stylesheet, one CSP meta and one referrer meta.
Only exact `stylesheet` and `icon` rels pass. Sensitive attribute values compare
both the parsed value and the original token bytes: no trimming, case folding
or entity decoding can turn a changed spelling into the approved value.
`html lang` is exactly `en-GB`; referrer content is exactly `no-referrer`;
`http-equiv` is exactly `Content-Security-Policy`. Resource/CSP positioning,
D26, Legal visibility, links, banned copy, SVG XML, validator directive and
duplicate-attribute checks remain in place.

The v4 pages use exact relative `style.css` and `favicon.svg` links, and the
addendum 2 CSP above. Neither absolute resource spellings nor the old P4 policy
are approved alternatives.

Discovery permits only the two existing exact `.github/` paths:
`.github/CODEOWNERS` and `.github/workflows/site-checks.yml`. An extra file there
fails even if its suffix would otherwise be an allowed raw download. No other
extensionless CODEOWNERS path is exempted. The complete-tree regression copies
all of this proposed tree, including ownership/workflow/configs/scripts, runs
all Python content/discovery commands and the authors command (synthetic
noreply-only Git history in the temporary copy), and exercises all seven matrix
preflights. npm/browser execution and the recursive test-suite invocation are
stubbed only for those matrix preflight assertions; the content CLIs execute for
real. The separate unknown-file regression verifies rejection of extra `.github`
files with and without extensions.

For later P2/P3 pages, fonts under `fonts/` with OFL.txt, navigation or SVG mark
changes, extend the explicit tables, discovery/document set and any CSS hash or
resource rules together. `/scripts/` is already owned; no new check config path
is added. Owner review under W1–W4 remains required.


## Round 6: strict HTML subset before content checks

`site_common.Page` replaces HTMLParser with a consuming tokenizer and an explicit
stack. Every `read_page` caller and all seven CI matrix entrypoints use this
same implementation before checking content. Errors are sticky: rejected input
may retain a diagnostic tree to preserve existing detailed error messages, but
none of the content commands or CI preflights can accept it. The allowlist and
resource, link, Legal and copy checks all consume these same nodes and decoded
attributes. Exact-byte comparisons use the original attribute spellings saved
by this tokenizer; there is no secondary attribute parser. Standalone
`favicon.svg` remains XML, using the existing DTD-refusing stdlib parser and SVG
vocabulary; the HTML doctype/document rules apply to the three HTML documents.

The syntax is deliberately narrower than valid HTML:

- Exactly one literal `<!doctype html>` at byte zero; no BOM, other `<!`,
  comments, marked sections or `<?` anywhere. The approved pages have no comments,
  so no comment exception is needed. Validator directives remain forbidden too.
- All non-void elements have properly nested explicit end tags. HTML `/>` is
  permitted only for meta/link/br/hr/img; SVG foreign elements may self-close.
  The existing allowlist can still exclude a syntactically valid void element.
  Unknown elements, attributes and closing tags still fail that allowlist.
- Exactly one root html, containing head then body, with only layout whitespace
  between them. Head contains only meta/title/link and whitespace text; title
  contains text alone. CSP precedes every link. The first head element is the
  unique literal `charset="utf-8"` meta, completed within the first 1024 UTF-8
  bytes so browser encoding detection agrees with the checker. Invalid UTF-8
  fails closed instead of raising an uncaught decoding exception.
- p, h1–h3, a, span, strong, em and button have only phrasing children
  (a/span/strong/em/br/inline svg), with no nested anchors. ul/ol contain only li
  and whitespace; li must be a direct child of a list and accepts explicitly
  nested flow content, including h3 and p. Other body containers
  permit only the declared flow vocabulary. These content models are checked
  in addition to the narrower current markup allowlist.
- SVG title/desc/text have text alone. This excludes HTML integration-point
  and foreign-text mode transitions with child markup. No allowed SVG element
  can trigger an HTML foreign-content breakout; the vocabulary excludes those
  names and all foreignObject/script/animation/resource elements.
- Attribute values must be double-quoted, separated by whitespace, with no
  literal `<`; duplicates still fail case-insensitively. Literal controls fail
  except layout TAB/LF/CR, and CRLF/CR normalize to LF as in HTML input processing.
  The only allowed HTML character-reference spellings are `&amp;`, `&lt;`,
  `&gt;`, `&quot;`, `&#39;`. **No named or numeric references occur in the
  approved HTML**, so there are no baseline additions. Bare ampersands also
  fail, making the character rule unambiguous. The existing SVG XML reference
  policy is unchanged (five XML built-ins and numeric references).

### Why the accepted element tree agrees with HTML parsing

This is a proof by induction on tokens for conforming HTML parsers, under the
existing element/attribute vocabulary, rather than a claim about arbitrary
broken parsers. Interpret the checker's lowercase SVG names as the canonical
projection of browser-adjusted SVG names (e.g. viewBox), and its string children
as text nodes; the document's checked doctype is represented separately.

The byte-zero doctype selects standards mode. UTF-8 is explicit in the sniffing
window and invalid bytes are refused. Double quotes, mandatory delimiters,
restricted references, forbidden controls, and the declaration gate leave only
unambiguous start/end/text tokens; decoded `<` is text, never retokenized.
Before-html/before-head whitespace is ignored; after-head whitespace is attached
to html; after-body/after-html whitespace is attached to body, matching browser
insertion modes. The tokenizer merges adjacent strings as the DOM merges text.
Head tokens cannot leave the in-head mode before its explicit end tag, because
only whitespace and meta/title/link occur; title has no literal child markup.
The document order then enters body exactly once. In body, every stack push has
a matching top-of-stack pop. The content models exclude paragraph, heading,
anchor and list implicit closures and adoption-agency repairs. Table, form,
select, template, frameset and raw-text elements are absent from the vocabulary,
so their special insertion modes, foster parenting and script handling cannot
occur. Inside svg the allowed foreign tokens remain foreign, text integration
points have no child tags, and self-closing tokens are acknowledged. Thus each
accepted token has the same parent and stack effect in the tokenizer and a
browser. Existing checks operate on that tree. This argument does not substitute
for a full browser accessibility or visual review.

### UX v4 verification

The complete tree passes strict-subset preflight and all Python content checks.
All original 136 regressions remain; fixture asset lists, relative links, header
expectations and the rect-attribute probe follow the new approved pages. The li
flow-content rule is unchanged from the supplied final round-6 tree.

The markup element/attribute allowlist has **no extensions**. The public asset
vocabulary adds exactly `fonts/urbanist-latin-var.woff2` and `fonts/OFL.txt`.
Their SHA256 values are pinned from the supplied SOURCE.md; the woff2 also needs
wOF2 magic bytes. Any other file under fonts/ fails, regardless of suffix.
SOURCE.md and frame preview pages are not shipped. The exact @font-face source
is `fonts/urbanist-latin-var.woff2`; other font/resource URLs and duplicate
font-face declarations fail. The CSS hash is re-pinned for v4 plus the exact
requested font-face and explicit 600 brand weight. The supplied mock brand was
700: the task's explicit weight instruction takes priority. All colours,
spacing and breakpoints otherwise match the mock.

`legal/approved-footer.html` is the exact footer element shared by all three
pages. `legal/approved-privacy-notice.html` is the privacy article. Pin comparison
uses raw bytes with **no normalization**, including no indentation stripping.
Each page needs exactly one matching footer; privacy needs exactly one matching
article. The exact two baseline paths are excluded from page discovery, and are
strictly parsed as fragments inside valid document wrappers. Extra Legal HTML
files remain unexpected documents. Existing footer wording/link, visibility,
D26 and notice vocabulary checks also apply to the pin content. Pin changes
cannot silently change Legal wording. `/legal/ @Trettbob` already exists in
`.github/CODEOWNERS`; changes therefore require Lee's review when Security's
required code-owner review protection is enabled. No GitHub setting is verified
or changed in this local job.

Sol r6's defs/text, title and desc footer attacks fail byte pins, as do added
attributes, whitespace-free markup spelling changes and second footers. Banned
copy in aria-hidden SVG is scanned independently of accessibility visibility.

See `../test.txt`, `../tree-run.txt`, `../MUTANTS.md` and
`../DIFF-base-to-restyle.patch` for test/mutant counts, tool limitations and the
complete delivered diff. Browser visual approval and live operational settings
remain outside this offline verification.
