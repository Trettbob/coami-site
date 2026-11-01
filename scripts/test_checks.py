"""Offline regressions. Fixture data lives in Python; probes only in $TMPDIR.

No network, installs or browser documents are created in the repo. Git writes
are confined to automatically removed temporary repositories under $TMPDIR.
"""
import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from xml.etree import ElementTree as ET
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_authors as authors
import check_invariants as invariants
import check_links as links
import check_no_third_party as resources
import check_privacy_text as privacy
import ci_checks
import site_common as common
import legal_visibility as visibility
import allowlist

SOURCE = Path(__file__).resolve().parents[1]
ASSETS = ['index.html', 'privacy.html', '404.html', *allowlist.IMAGE_HASHES, 'style.css',
          'CNAME', '.nojekyll', str(privacy.D26_PATH), *common.FONT_HASHES, *common.LEGAL_PINS]


class ChecksTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=os.environ.get('TMPDIR', tempfile.gettempdir()))
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in ASSETS:
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(SOURCE / name, target)

    def edit(self, name, old, new):
        p = self.root / name
        text = p.read_text()
        self.assertIn(old, text)
        p.write_text(text.replace(old, new, 1))

    def body(self, value, name='index.html'):
        self.edit(name, '</body>', value + '</body>')

    def error(self, checker, fragment):
        self.assertIn(fragment, '\n'.join(checker(self.root)))

    def test_logo_image_hashes(self):
        for name in allowlist.IMAGE_HASHES:
            path = self.root / name
            original = path.read_bytes()
            for data in [original + b'\n', None]:
                with self.subTest(name=name, missing=data is None):
                    if data is None:
                        path.unlink()
                    else:
                        path.write_bytes(data)
                    self.error(resources.check, 'Approved image sha256 mismatch: ' + name)
                    path.write_bytes(original)

    def test_logo_png_signature(self):
        for name in ['apple-touch-icon.png']:
            path = self.root / name
            original = path.read_bytes()
            self.assertTrue(original.startswith(b'\x89PNG\r\n\x1a\n'))
            path.write_bytes(b'not PNG!' + original[8:])
            self.error(resources.check, 'Approved PNG must start with PNG signature: ' + name)
            path.write_bytes(original)

    def test_favicon_ico_signature(self):
        path = self.root / 'favicon.ico'
        original = path.read_bytes()
        self.assertTrue(original.startswith(b'\x00\x00\x01\x00'))
        path.write_bytes(b'BAD!' + original[4:])
        self.error(resources.check, 'Approved ICO must start with ICO signature: favicon.ico')

    def test_favicon_links_exact(self):
        for name in ['index.html', 'privacy.html', '404.html']:
            original = (self.root / name).read_text()
            block = '\n'.join(allowlist.ICON_LINKS)
            self.assertIn(block, original)
            self.assertEqual(resources.check(self.root), [])
            ico, svg, apple = allowlist.ICON_LINKS
            variants = [
                '', '\n'.join([svg, ico, apple]), block + '\n' + ico,
                block.replace(' sizes="48x48"', ''),
                block.replace('48x48', '32x32'),
                block.replace(' type="image/svg+xml"', ''),
                block.replace('image/svg+xml', 'image/png'),
                block.replace(apple, apple.replace('>', ' sizes="180x180">')),
                block.replace(ico, ico.replace('>', ' media="all">')),
                block.replace(ico, '<link href="favicon.ico" rel="icon" sizes="48x48">'),
                block.replace('favicon.ico', './favicon.ico'),
                block.replace('coami-icon.svg', 'img/coami-logo.svg'),
                block.replace('apple-touch-icon.png', 'favicon.ico'),
            ]
            for variant in variants:
                with self.subTest(page=name, variant=variant):
                    (self.root / name).write_text(original.replace(block, variant))
                    self.error(resources.check, 'expected exact three icon links in order')
            (self.root / name).write_text(original)

    def test_favicon_links_head(self):
        for name in ['index.html', 'privacy.html', '404.html']:
            original = (self.root / name).read_text()
            for icon in allowlist.ICON_LINKS:
                with self.subTest(page=name, icon=icon):
                    # Moving the final icon preserves order/count/spelling, isolating placement.
                    text = original.replace(icon + '\n', '')
                    (self.root / name).write_text(text.replace('<body>', '<body>\n' + icon))
                    self.error(resources.check, 'icon links must be direct children of head')
            (self.root / name).write_text(original)

    def test_favicon_retired_files(self):
        for name in ['favicon.svg', 'favicon-dark.svg', 'favicon-32.png',
                     'apple-touch-icon-180.png']:
            with self.subTest(name=name):
                self.assertNotIn(name, allowlist.IMAGE_HASHES)
                self.assertNotIn(name, common.EXPECTED_DOCUMENTS)
                path = self.root / name
                path.write_bytes(b'retired')
                self.error(resources.check, 'Unapproved image file: ' + repr(name))
                path.unlink()

    def test_favicon_manifest(self):
        self.edit('index.html', '</head>', '<link rel="manifest" href="site.webmanifest"></head>')
        self.error(resources.check, 'forbidden link resource hint')
        self.error(resources.check, 'link rel must be byte-exact stylesheet or icon')

    def test_logo_img_source(self):
        original = (self.root / 'index.html').read_text()
        for src in ['https://evil.test/logo.svg', '//evil.test/logo.svg',
                    'data:image/svg+xml,x', 'unknown.png', 'unknown.svg',
                    '/img/coami-logo.svg', './img/coami-logo.svg',
                    'img/coami-logo.svg?x=1', 'img/coami-logo.svg#x',
                    'img/coami-logo.sv&#103;']:
            with self.subTest(src=src):
                (self.root / 'index.html').write_text(original)
                self.body('<img src="' + src + '" alt="CoAmi">')
                self.error(resources.check, 'img src must be byte-exact in pinned image set')
        (self.root / 'index.html').write_text(original)
        self.body('<img alt="CoAmi">')
        self.error(resources.check, 'img src must be byte-exact in pinned image set')

    def test_logo_unknown_image(self):
        for name in ['unknown.png', 'img/unknown.png', 'unknown.svg', 'img/unknown.svg', 'unknown.ico']:
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            source = ('coami-icon.svg' if name.endswith('.svg') else
                      'favicon.ico' if name.endswith('.ico') else 'apple-touch-icon.png')
            path.write_bytes((SOURCE / source).read_bytes())
            self.error(resources.check, 'Unapproved image file: ' + repr(name))
            path.unlink()

    def test_logo_icon_source(self):
        original = (self.root / 'index.html').read_text()
        for rel in ['icon', 'apple-touch-icon']:
            for href in ['unknown.png', 'https://evil.test/coami-icon.svg',
                         '//evil.test/coami-icon.svg', '/coami-icon.svg', './coami-icon.svg',
                         'coami-icon.svg?x=1', 'coami-icon.svg#x', 'coami-icon.sv&#103;']:
                with self.subTest(rel=rel, href=href):
                    (self.root / 'index.html').write_text(original)
                    self.edit('index.html', '</head>', '<link rel="' + rel + '" href="' + href + '"></head>')
                    self.error(resources.check, 'icon href must be byte-exact in pinned image set')

    def test_logo_img_attributes(self):
        original = (self.root / 'index.html').read_text()
        for attribute in ['title', 'style', 'onerror', 'srcset', 'data-logo', 'href']:
            (self.root / 'index.html').write_text(original)
            self.body('<img src="img/coami-logo.svg" alt="CoAmi" ' + attribute + '="x">')
            self.error(resources.check, 'forbidden attribute ' + attribute + ' on <img>')

    def test_logo_pinned_resources_accepted(self):
        for name in allowlist.IMAGE_HASHES:
            self.body('<img src="' + name + '" alt="CoAmi" class="probe" width="100" height="40">')
        self.assertEqual(resources.check(self.root), [])
        self.assertEqual(links.check(self.root), [])
        for name in allowlist.IMAGE_HASHES:
            if name.endswith('.svg'):
                self.assertEqual(common.read_page(self.root / name).errors, [])

    def test_logo_privacy_brand(self):
        original = (self.root / 'privacy.html').read_text()
        for old, new in [('alt="CoAmi"', 'alt="Other"'),
                         ('class="brand-light"', 'class="brand-dark"'),
                         ('aria-label="CoAmi home"', 'aria-label="Other"'),
                         ('src="img/coami-logo.svg"', 'src="coami-icon.svg"'),
                         ('href="index.html" aria-label="CoAmi home"', 'href="privacy.html" aria-label="CoAmi home"')]:
            (self.root / 'privacy.html').write_text(original)
            self.edit('privacy.html', old, new)
            self.error(privacy.check, 'Privacy header brand must match the approved theme images and home link')

    def test_v4_old_p4_csp(self):
        old = allowlist.CSP.replace(" font-src 'self';", '')
        self.edit('index.html', allowlist.CSP, old)
        self.markup_error('CSP content must be byte-exact ASCII policy', 'index.html')
        self.error(resources.check, 'CSP content must be byte-exact ASCII policy')

    def test_v4_extra_font(self):
        for name in ['extra.woff2', 'extra.txt', 'SOURCE.md', 'nested/OFL.txt']:
            path = self.root / 'fonts' / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'wOF2extra')
            self.error(resources.check, 'Unapproved font directory file')
            path.unlink()

    def test_v4_font_hash(self):
        for name in common.FONT_HASHES:
            original = (self.root / name).read_bytes()
            (self.root / name).write_bytes(original + b'x')
            self.error(resources.check, 'Approved font/license sha256 mismatch: ' + name)
            (self.root / name).write_bytes(original)
            (self.root / name).unlink()
            self.error(resources.check, 'Approved font/license sha256 mismatch: ' + name)
            (self.root / name).write_bytes(original)

    def test_v4_font_magic(self):
        name = 'fonts/urbanist-latin-var.woff2'
        (self.root / name).write_bytes(b'not a woff2')
        self.error(resources.check, 'woff2 must start with wOF2')

    def test_v4_font_face_origin(self):
        for url in ['https://evil.test/font.woff2', '//evil.test/font.woff2',
                    '/elsewhere.woff2', 'fonts/extra.woff2', 'data:font/woff2;base64,d09GMg==']:
            (self.root / 'style.css').write_bytes((SOURCE / 'style.css').read_bytes())
            self.edit('style.css', 'url(fonts/urbanist-latin-var.woff2)', 'url(' + url + ')')
            self.error(resources.check, 'forbidden CSS resource vector')

    def test_v4_font_face_cardinality(self):
        for rule in [resources.FONT_FACE, '@font-face{font-family:x;src:local(x)}']:
            (self.root / 'style.css').write_text((SOURCE / 'style.css').read_text() + rule)
            self.error(resources.check, 'forbidden CSS resource vector')

    def test_v4_legal_bytes(self):
        # Whitespace-free attribute spelling changes render identically but fail.
        for name, tag, checker in [('index.html', 'footer', invariants.check),
                                   ('privacy.html', 'article', privacy.check)]:
            original = (SOURCE / name).read_bytes()
            for old, new in [(b'<'+tag.encode()+b' class="', b'<'+tag.encode()+b' class ="'),
                             (b'<'+tag.encode()+b' class="', b'<'+tag.encode()+b' aria-label="Legal" class="'),
                             (b'<p>', b'<P>'), (b'<p>', b'<p >')]:
                (self.root / name).write_bytes(original)
                # Mutate only inside the protected element.
                import legal_pins
                chunk = legal_pins.element_bytes(original, tag)[0]
                self.assertIn(old, chunk)
                (self.root / name).write_bytes(original.replace(chunk, chunk.replace(old, new, 1), 1))
                self.error(checker, 'match its approved pin byte for byte')

    def test_v4_footer_svg(self):
        for name in ['index.html', 'privacy.html', '404.html']:
            for opening, closing in [('<svg><defs><text>', '</text></defs></svg>'),
                                     ('<svg><title>', '</title></svg>'),
                                     ('<svg><desc>', '</desc></svg>')]:
                (self.root / name).write_bytes((SOURCE / name).read_bytes())
                text = (self.root / name).read_text()
                start = text.index('<p>Trett Labs', text.index('<footer')) + 3
                end = text.index('<a href="mailto:hello@coami.ai">', start)
                (self.root / name).write_text(text[:start] + opening + text[start:end] + closing + text[end:])
                self.error(invariants.check, 'match its approved pin byte for byte')

    def test_v4_notice_svg(self):
        for tag in ['defs', 'title', 'desc']:
            (self.root / 'privacy.html').write_bytes((SOURCE / 'privacy.html').read_bytes())
            self.edit('privacy.html', 'There is no sign-up here.',
                      '<svg><' + tag + '>There is no sign-up here.</' + tag + '></svg>')
            self.error(privacy.check, 'match its approved pin byte for byte')

    def test_v4_second_legal_element(self):
        import legal_pins
        for name, tag, checker in [('index.html', 'footer', invariants.check),
                                   ('privacy.html', 'article', privacy.check)]:
            raw = (self.root / name).read_bytes()
            chunk = legal_pins.element_bytes(raw, tag)[0]
            (self.root / name).write_bytes(raw.replace(chunk, chunk + chunk))
            self.error(checker, 'must occur exactly once and match its approved pin')

    def test_v4_pin_semantics(self):
        self.edit('legal/approved-footer.html', '17310137', '00000000')
        self.error(invariants.check, 'Approved footer pin: Legal footer text')
        self.edit('legal/approved-privacy-notice.html', 'no cookies', 'some cookies')
        self.error(privacy.check, 'Approved privacy pin text differs from D26')

    def test_v4_pin_links(self):
        self.edit('legal/approved-footer.html', 'href="privacy.html"', 'href="index.html"')
        self.error(invariants.check, 'Approved footer pin: Legal footer links')

    def test_v4_pin_notice_links(self):
        pin = 'legal/approved-privacy-notice.html'
        for url, diagnostic in [(privacy.ICO, 'ICO link href'),
                                (privacy.GITHUB_PRIVACY, 'privacy statement link href')]:
            (self.root / pin).write_bytes((SOURCE / pin).read_bytes())
            self.edit(pin, url, 'https://evil.test/')
            self.error(privacy.check, 'Approved privacy pin: ' + diagnostic)

    def test_v4_missing_pins(self):
        (self.root / 'legal/approved-footer.html').unlink()
        self.error(invariants.check, 'Missing or invalid approved footer pin')
        (self.root / 'legal/approved-privacy-notice.html').unlink()
        self.error(privacy.check, 'Missing or invalid approved privacy notice pin')

    def test_v4_pin_validation(self):
        import legal_pins
        for tag, pin in legal_pins.PINS.items():
            original = (self.root / pin).read_bytes()
            for raw in [b'x' + original, original + original,
                        original.replace(b'<p>', b'<p hidden="">', 1),
                        original.replace(b'<p>', b'<p>\xff', 1)]:
                (self.root / pin).write_bytes(raw)
                self.assertIsNone(legal_pins.pin_page(self.root, tag))
            (self.root / pin).write_bytes(original)

    def test_v4_pin_notice_vocabulary(self):
        self.edit('legal/approved-privacy-notice.html', 'There is no sign-up here.',
                  '<svg><text>There is no sign-up here.</text></svg>')
        self.error(privacy.check, 'Approved privacy pin: forbidden notice element')

    def test_v4_pin_notice_visibility(self):
        self.edit('legal/approved-privacy-notice.html', 'class="legal text"', 'class="skip"')
        self.error(privacy.check, 'Approved privacy pin: Privacy notice visibility class placement')

    def test_v4_banned_aria_svg(self):
        for content in ['<svg viewBox="0 0 300 100" aria-hidden="true"><text x="0" y="50">GDPR certified secure</text></svg>',
                        '<svg><text>GDPR certified secure</text></svg>']:
            (self.root / 'index.html').write_bytes((SOURCE / 'index.html').read_bytes())
            self.edit('index.html', '</main>', content + '</main>')
            self.error(invariants.check, 'banned visible copy')
        self.assertEqual(common.copy_text(common.Page('<div hidden="">secure</div>').root), '')
        self.assertEqual(common.copy_text(common.Page('<template>secure</template>').root), '')

    def test_real_pages(self):
        for checker in [resources.check, privacy.check, links.check, invariants.check]:
            with self.subTest(checker=checker.__module__):
                self.assertEqual(checker(self.root), [])

    def markup_error(self, fragment, name='privacy.html'):
        self.assertIn(fragment, '\n'.join(common.read_page(self.root / name).errors))

    def strict_page(self, body='', head='', prefix='<!doctype html>'):
        return common.Page(prefix + '<html lang="en-GB"><head><meta charset="utf-8">'
                           '<meta http-equiv="Content-Security-Policy" content="'
                           + allowlist.CSP + '">' + head + '</head><body>'
                           + body + '</body></html>')

    def strict_error(self, body, diagnostic):
        self.assertIn(diagnostic, '\n'.join(self.strict_page(body).errors))

    def test_r6_sol_probes_all_checkers(self):
        probes = [
            ('<head>', '<head><![CDATA[><script>alert(1)</script>]]>', 'comments/marked sections forbidden'),
            ('<head>', '<head><![CDATA[><link rel="stylesheet" href="https://evil.test/hide.css">]]>', 'comments/marked sections forbidden'),
            ('<head>', '<head><![IGNORE[><p>Certified secure GDPR compliant</p>]]>', 'comments/marked sections forbidden'),
            ('<head>', '<head><![CDATA[><style>main,footer{display:none}</style>]]>', 'comments/marked sections forbidden'),
            ('<body>', '<body><div class="skip"/>', 'self-closing non-void'),
            ('<head>', '<head>hello', 'only whitespace text'),
            ('<head>', '<head><div></div>', 'head may contain only'),
        ]
        for old, new, diagnostic in probes:
            with self.subTest(probe=new):
                (self.root / 'privacy.html').write_bytes((SOURCE / 'privacy.html').read_bytes())
                self.edit('privacy.html', old, new)
                for checker in [resources.check, privacy.check, links.check, invariants.check]:
                    self.error(checker, diagnostic)
                # Every real CI entrypoint rejects before any command/server.
                for kind in ['html', 'links', 'no-third-party', 'a11y', 'authors', 'privacy-text', 'invariants']:
                    output = io.StringIO()
                    with patch.object(sys, 'argv', ['ci_checks.py', '--root', str(self.root), '--', kind]), \
                            patch.object(ci_checks, 'run') as run, \
                            patch.object(ci_checks, 'accessibility') as a11y, \
                            contextlib.redirect_stdout(output):
                        self.assertEqual(ci_checks.main(), 1, (new, kind))
                        run.assert_not_called()
                        a11y.assert_not_called()
                    self.assertIn(diagnostic, output.getvalue())

    def test_r6_declarations(self):
        for text in ['<!-- ordinary comment -->', '<!-- comment with > inside -->',
                     '<![CDATA[abc]]>', '<![IGNORE[abc]]>', '<!bogus>',
                     '<!DOCTYPE html>', '<!doctype html>', '<!>', '<!---->']:
            self.strict_error(text, 'comments/marked sections forbidden')
        self.assertFalse(self.strict_page().errors)

    def test_r6_doctype_byte_zero(self):
        for prefix in ['', '\ufeff<!doctype html>', ' <!doctype html>',
                       '\n<!doctype html>', '<!DOCTYPE html>', '<!doctype HTML>']:
            self.assertIn('doctype must be exactly', '\n'.join(self.strict_page(prefix=prefix).errors))

    def test_r6_processing_instructions(self):
        for text in ['<?xml version="1.0"?>', '<?bogus>', '<p><?xml</p>',
                     '<p class="<?xml">x</p>']:
            self.strict_error(text, 'processing instructions forbidden')

    def test_r6_selfclosing_html(self):
        for tag in ['div', 'p', 'section', 'a', 'span', 'main', 'ul', 'li', 'title', 'html', 'body', 'x']:
            self.strict_error('<' + tag + '/>', 'self-closing non-void HTML element')
        for text in ['<svg/>', '<svg><g/><circle/></svg>']:
            self.assertFalse(self.strict_page(text).errors, text)
        # hr/img are syntactically void but still excluded by the markup allowlist.
        for tag in common.HTML_VOID:
            self.assertNotIn('self-closing non-void', '\n'.join(self.strict_page('<' + tag + '/>').errors))

    def test_r6_stray_end(self):
        for tag in ['div', 'unknown', 'br', 'img']:
            self.strict_error('</' + tag + '>', 'unpaired or misnested end tag')

    def test_r6_misnested_end(self):
        self.strict_error('<div><section></div></section>', 'unpaired or misnested end tag')
        self.strict_error('<p><span></p></span>', 'unpaired or misnested end tag')

    def test_r6_unclosed(self):
        self.strict_error('<section>', 'unclosed non-void elements')
        self.strict_error('<svg><g>', 'unclosed non-void elements')

    def test_r6_document_root(self):
        page = self.strict_page()
        self.assertFalse(page.errors)
        text = '<!doctype html><html lang="en-GB"><head><meta charset="utf-8"></head><body></body></html>'
        for value in [text + '<div></div>', text + '<html></html>', text.replace('<html lang="en-GB">', '')]:
            self.assertIn('document requires exactly one root html', '\n'.join(common.Page(value).errors))

    def test_r6_head_body_cardinality(self):
        for head, body in [('', '<body></body>'), ('<head></head>', ''),
                           ('<head></head><head></head>', '<body></body>'),
                           ('<head></head>', '<body></body><body></body>')]:
            page = common.Page('<!doctype html><html lang="en-GB">' + head + body + '</html>')
            self.assertIn('document requires exactly one head followed by one body', '\n'.join(page.errors))

    def test_r6_head_body_order(self):
        page = common.Page('<!doctype html><html lang="en-GB"><body></body><head>'
                           '<meta charset="utf-8"></head></html>')
        self.assertIn('html must contain exactly head then body', '\n'.join(page.errors))

    def test_r6_head_body_parent(self):
        page = common.Page('<!doctype html><html lang="en-GB"><div><head>'
                           '<meta charset="utf-8"></head><body></body></div></html>')
        self.assertIn('head/body must be direct children of html', '\n'.join(page.errors))

    def test_r6_head_elements(self):
        for tag in ['div', 'svg', 'p', 'section', 'br']:
            self.assertIn('head may contain only meta, title and link', '\n'.join(
                self.strict_page(head='<' + tag + '></' + tag + '>').errors))

    def test_r6_structural_text(self):
        for body in ['<ul>hello</ul>', '<ol>hello</ol>']:
            self.strict_error(body, 'only whitespace text')
        self.assertIn('only whitespace text', '\n'.join(self.strict_page(head='hello').errors))
        page = common.Page('hello' + '<!doctype html><html><head></head><body></body></html>world')
        self.assertIn('only whitespace text', '\n'.join(page.errors))

    def test_r6_csp_before_link(self):
        self.edit('privacy.html', '<meta charset="utf-8">',
                  '<meta charset="utf-8"><link rel="icon" href="coami-icon.svg">')
        self.markup_error('CSP must precede every link')

    def test_r6_phrasing_models(self):
        for parent in ['p', 'h1', 'h2', 'h3', 'a', 'span', 'button', 'strong', 'em']:
            for child in ['div', 'p', 'h2', 'ul', 'section']:
                self.strict_error('<' + parent + '><' + child + '></' + child + '></' + parent + '>',
                                  'phrasing content required')
        self.assertFalse(self.strict_page('<p><span><a href="#main">text</a></span></p>').errors)

    def test_r6_list_models(self):
        for tag in ['ul', 'ol']:
            self.strict_error('<' + tag + '><p>text</p></' + tag + '>', 'ul/ol may contain only li')
        self.strict_error('<li>text</li>', 'li must be a direct child')
        self.strict_error('<ul><li><li>text</li></li></ul>', 'li must be a direct child')
        self.assertFalse(self.strict_page('<ul><li><span>Step</span> text</li></ul>').errors)

    def test_r6_li_allows_flow(self):
        # li may hold flow content such as h3/p (browsers parse it identically).
        for child in ['h3', 'p']:
            self.assertEqual(self.strict_page('<ul><li><' + child + '>text</' + child + '></li></ul>').errors, [])
        self.strict_error('<ul><li><meta charset="utf-8"></li></ul>',
                          'li requires explicitly nested flow content')

    def test_r6_immutable_subset_status(self):
        # Report the supplied conflict, never silently exempt it or alter HTML.
        for name in ['privacy.html', '404.html']:
            self.assertEqual(common.read_page(SOURCE / name).errors, [])
        self.assertEqual(common.read_page(SOURCE / 'index.html').errors, [])

    def test_r6_codeowners_discovery(self):
        shutil.copytree(SOURCE, self.root, dirs_exist_ok=True)
        self.assertTrue((self.root / '.github/CODEOWNERS').is_file())
        self.assertEqual(common.discovery_errors(self.root), [])
        result = self.cli('site_common.py')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_r6_li_flow(self):
        self.strict_error('<ul><li><meta charset="utf-8"></li></ul>', 'li requires explicitly nested flow content')

    def test_r6_nested_anchor(self):
        self.strict_error('<a href="#main"><span><a href="#main">x</a></span></a>', 'nested anchors forbidden')

    def test_r6_flow_models(self):
        self.strict_error('<div><title>x</title></div>', 'flow content required')
        self.strict_error('<meta name="description" content="x">', 'flow content required')

    def test_r6_title_rcdata(self):
        self.assertIn('HTML title must contain text only', '\n'.join(
            self.strict_page(head='<title><span>text</span></title>').errors))
        self.assertFalse(self.strict_page(head='<title>text &lt;span&gt;</title>').errors)

    def test_r6_svg_integration(self):
        for tag in ['title', 'desc', 'text']:
            self.strict_error('<svg><' + tag + '><circle/></' + tag + '></svg>',
                              'SVG title/desc/text must contain text only')
        self.assertFalse(self.strict_page('<svg><title>label</title><desc>description</desc>'
                                         '<text>&lt;text&gt;</text><g><circle/></g></svg>').errors)

    def test_r6_attributes_quoted(self):
        for body in ["<p class='x'>text</p>", '<p class=x>text</p>', '<p class>text</p>']:
            self.strict_error(body, 'attribute values must be double-quoted')

    def test_r6_attribute_separation(self):
        self.strict_error('<a class="x"href="#main">x</a>', 'attributes must be separated by whitespace')

    def test_r6_attribute_less_than(self):
        self.strict_error('<p class="a<b">text</p>', 'literal < forbidden in attribute values')
        self.assertFalse(self.strict_page('<p class="a&gt;b">text</p>').errors)

    def test_r6_controls(self):
        for code in list(range(32)) + list(range(127, 160)):
            if code not in [9, 10, 13]:
                self.strict_error('<p>a' + chr(code) + 'b</p>', 'NUL/control characters forbidden')
        self.assertFalse(self.strict_page('<p>line\r\nnext\ttab</p>').errors)

    def test_r6_references(self):
        for ref in ['&apos;', '&#65;', '&#x41;', '&#0;', '&#10;', '&copy;', '&amp', '&bogus;', '&', '&ampersand']:
            self.strict_error('<p>' + ref + '</p>', 'forbidden HTML character reference')
        page = self.strict_page('<p>&amp;&lt;&gt;&quot;&#39;</p>')
        self.assertFalse(page.errors)
        p = next(n for n in page.nodes if n.tag == 'p')
        self.assertEqual(p.children, ['&<>"' + "'"])
        self.assertEqual(common.HTML_REFERENCES, {'&amp;', '&lt;', '&gt;', '&quot;', '&#39;'})

    def test_r6_charset(self):
        self.edit('privacy.html', 'charset="utf-8"', 'charset="shift_jis"')
        self.markup_error('first head element must be the unique byte-exact UTF-8 charset meta')

    def test_r6_charset_sniff_window(self):
        self.edit('privacy.html', '<head>', '<head>' + ' ' * 1024)
        self.markup_error('UTF-8 charset declaration must finish within first 1024 bytes')

    def test_r6_malformed_tokens(self):
        for body, message in [('<p', 'malformed start tag'), ('<p @="x">', 'malformed attribute/start tag'),
                              ('<p>2 < 3</p>', 'malformed start tag'), ('</p x>', 'malformed end tag')]:
            self.strict_error(body, message)

    def test_r6_utf8_bytes(self):
        p = self.root / 'privacy.html'
        p.write_bytes(p.read_bytes() + b'\xff')
        for checker in [resources.check, privacy.check, links.check, invariants.check]:
            self.error(checker, 'invalid UTF-8 document bytes')

    def test_r6_document_whitespace(self):
        page = self.strict_page('<p>a\r\nb</p>')
        self.assertFalse(page.errors)
        # Browser insertion modes ignore leading layout whitespace and move
        # trailing whitespace into body; compare the actual resulting tree.
        source = '<!doctype html>\n<html lang="en-GB">\n<head><meta charset="utf-8">' + \
                 '<meta http-equiv="Content-Security-Policy" content="' + allowlist.CSP + \
                 '"></head>\n<body><p>x</p></body>\n</html>\n'
        page = common.Page(source)
        self.assertFalse(page.errors)
        self.assertEqual(len(page.root.children), 1)
        html = page.root.children[0]
        self.assertEqual([c.tag if isinstance(c, common.Node) else c for c in html.children],
                         ['head', '\n', 'body'])
        self.assertEqual(html.children[-1].children[-1], '\n\n')

    def test_r5_csp_keyword(self):
        for keyword in [' Content-Security-Policy ', 'Content-Security-Policy ',
                        ' Content-Security-Policy', 'content-security-policy',
                        'CONTENT-SECURITY-POLICY', 'Content-Security-Polic&#121;']:
            (self.root / 'privacy.html').write_bytes((SOURCE / 'privacy.html').read_bytes())
            self.edit('privacy.html', 'http-equiv="Content-Security-Policy"',
                      'http-equiv="' + keyword + '"')
            for checker in [resources.check, privacy.check, links.check, invariants.check]:
                self.error(checker, 'http-equiv must be byte-exact')

    def test_r5_shadow_template(self):
        self.edit('privacy.html', '<body>', '<body><template shadowrootmode="open">'
                  '<p>Certified secure GDPR compliant</p></template>')
        for checker in [resources.check, privacy.check, links.check, invariants.check]:
            self.error(checker, 'forbidden <template> element (markup allowlist)')

    def test_r5_extra_stylesheet_index(self):
        self.extra_stylesheet('index.html')

    def test_r5_extra_stylesheet_404(self):
        self.extra_stylesheet('404.html')

    def extra_stylesheet(self, name):
        (self.root / 'hide.css').write_text('footer { display: none; }')
        self.edit(name, '</head>', '<link rel="stylesheet" href="/hide.css"></head>')
        for checker in [resources.check, privacy.check, links.check, invariants.check]:
            self.error(checker, 'expected exactly one stylesheet on every page')

    def test_r5_body_background(self):
        self.edit('privacy.html', '<body>', '<body background="' + privacy.ICO + '">')
        for checker in [resources.check, privacy.check, links.check, invariants.check]:
            self.error(checker, 'forbidden attribute background on <body> (markup allowlist)')

    def test_r5_table_background(self):
        self.body('<table background="' + privacy.ICO + '"><tr><td>Test</td></tr></table>',
                  'privacy.html')
        for checker in [resources.check, privacy.check, links.check, invariants.check]:
            self.error(checker, 'forbidden <table> element (markup allowlist)')
            self.error(checker, 'forbidden attribute background on <table> (markup allowlist)')

    def test_r5_unknown_element(self):
        # Generated names ensure the policy fails closed beyond known probes.
        import random
        name = 'probe' + ''.join(random.Random(501).choices('abcdefghijklmnopqrstuvwxyz', k=16))
        self.body('<' + name + '>Test</' + name + '>', 'privacy.html')
        for checker in [resources.check, privacy.check, links.check, invariants.check]:
            self.error(checker, 'forbidden <' + name + '> element (markup allowlist)')

    def test_r5_unknown_attribute(self):
        import random
        name = 'probe' + ''.join(random.Random(502).choices('abcdefghijklmnopqrstuvwxyz', k=16))
        self.body('<p ' + name + '="value">Test</p>', 'privacy.html')
        for checker in [resources.check, privacy.check, links.check, invariants.check]:
            self.error(checker, 'forbidden attribute ' + name + ' on <p> (markup allowlist)')

    def test_r5_all_forbidden_elements(self):
        for tag in ['template', 'slot', 'iframe', 'object', 'embed', 'script', 'noscript',
                    'base', 'form', 'input', 'table', 'td', 'th', 'font', 'marquee',
                    'style', 'dialog', 'my-widget']:
            for position in ['head', 'body']:
                (self.root / 'privacy.html').write_bytes((SOURCE / 'privacy.html').read_bytes())
                self.edit('privacy.html', '</' + position + '>',
                          '<' + tag + '></' + tag + '></' + position + '>')
                self.markup_error('forbidden <' + tag + '> element (markup allowlist)')
        self.assertIn('forbidden <unknown> element (markup allowlist)',
                      '\n'.join(common.Page('</unknown>').errors))

    def test_r5_all_forbidden_attributes(self):
        for key in ['background', 'shadowrootmode', 'shadowroot', 'popover', 'hidden',
                    'inert', 'style', 'onclick', 'onanything', 'srcset', 'slot', 'is',
                    'nonce', 'data-future', 'class', 'href']:
            (self.root / 'privacy.html').write_bytes((SOURCE / 'privacy.html').read_bytes())
            self.edit('privacy.html', '<body>', '<body ' + key + '="value">')
            self.markup_error('forbidden attribute ' + key + ' on <body> (markup allowlist)')
        # An attribute approved on one element is not global permission.
        self.body('<p href="#main">Test</p>', 'privacy.html')
        self.markup_error('forbidden attribute href on <p> (markup allowlist)')

    def test_r5_svg_per_element_attributes(self):
        self.body('<svg><rect width="1" height="1"/></svg>', 'privacy.html')
        for name in ['privacy.html', 'coami-icon.svg']:
            self.edit(name, '<rect ', '<rect cx="1" ')
            self.markup_error('forbidden attribute cx on <rect> (markup allowlist)', name)

    def test_r5_allowlist_derivation(self):
        actual = {}
        for name in ['index.html', 'privacy.html', '404.html']:
            for node in common.read_page(SOURCE / name).nodes:
                if not any(n.tag == 'svg' for n in node.ancestors()):
                    actual.setdefault(node.tag, set()).update(node.attr)
        # Optional dimensions are approved for images, although the header is
        # sized by CSS height and its intrinsic SVG aspect ratio.
        actual['img'].update({'width', 'height'})
        self.assertEqual(actual, allowlist.HTML_ATTRIBUTES)
        # r4's permitted SVG elements remain available with no new attributes.
        for tag in allowlist.SVG_ELEMENTS:
            self.assertEqual(common.SVGPage('<svg xmlns="http://www.w3.org/2000/svg"><'
                                           + tag + '/></svg>').errors, [])

    def test_r5_csp_content_shared(self):
        self.edit('privacy.html', allowlist.CSP, allowlist.CSP + ';')
        self.markup_error('Markup allowlist: CSP content must be byte-exact ASCII policy')

    def test_r5_csp_count_shared(self):
        text = (self.root / 'privacy.html').read_text()
        csp = next(line for line in text.splitlines() if 'Content-Security-Policy' in line)
        for replacement in ['', csp + csp]:
            (self.root / 'privacy.html').write_text(text.replace(csp, replacement))
            self.markup_error('Markup allowlist: expected exactly one CSP meta')

    def test_r5_referrer_value(self):
        original = (self.root / 'privacy.html').read_text()
        for value in [' no-referrer', 'no-referrer ', 'NO-REFERRER', 'no-referr&#101;r']:
            (self.root / 'privacy.html').write_text(original.replace('content="no-referrer"',
                                                                    'content="' + value + '"'))
            self.markup_error('Markup allowlist: referrer must be byte-exact no-referrer')

    def test_r5_referrer_count(self):
        original = (self.root / 'privacy.html').read_text()
        meta = '<meta name="referrer" content="no-referrer">'
        for replacement in ['', meta + meta]:
            (self.root / 'privacy.html').write_text(original.replace(meta, replacement))
            self.markup_error('Markup allowlist: expected exactly one referrer meta')

    def test_r5_link_rel(self):
        original = (self.root / 'privacy.html').read_text()
        for rel in [' stylesheet', 'stylesheet ', 'STYLESHEET', 'alternate', 'icon stylesheet']:
            (self.root / 'privacy.html').write_text(original.replace('rel="stylesheet"',
                                                                    'rel="' + rel + '"'))
            self.markup_error('Markup allowlist: link rel must be byte-exact stylesheet or icon')

    def test_r5_stylesheet_target(self):
        original = (self.root / 'privacy.html').read_text()
        for href in [allowlist.STYLESHEET + ' ', ' ' + allowlist.STYLESHEET,
                     allowlist.STYLESHEET.upper(), 'other.css']:
            (self.root / 'privacy.html').write_text(original.replace('href="' + allowlist.STYLESHEET + '"',
                                                                    'href="' + href + '"'))
            self.markup_error('Markup allowlist: stylesheet href must be byte-exact')

    def test_r5_stylesheet_missing(self):
        self.edit('privacy.html', '<link rel="stylesheet" href="' + allowlist.STYLESHEET + '">', '')
        self.markup_error('Markup allowlist: expected exactly one stylesheet on every page')

    def test_r5_icon_target(self):
        self.edit('privacy.html', 'href="' + allowlist.FAVICON + '"', 'href="other.svg"')
        self.markup_error('Markup allowlist: icon href must be byte-exact')

    def test_r5_html_lang(self):
        original = (self.root / 'privacy.html').read_text()
        for value in ['en-gb', 'EN-GB', ' en-GB', 'en-GB ', 'en-G&#66;']:
            (self.root / 'privacy.html').write_text(original.replace('lang="en-GB"', 'lang="' + value + '"'))
            self.markup_error('Markup allowlist: html lang must be byte-exact en-GB')

    def test_r5_raw_attribute_bytes(self):
        # Decoding cannot replace the required literal attribute spelling.
        self.edit('privacy.html', 'rel="stylesheet"', 'rel="styleshe&#101;t"')
        self.markup_error('Markup allowlist: link rel must be byte-exact stylesheet or icon')

    def test_r5_complete_tree_commands(self):
        shutil.copytree(SOURCE, self.root, dirs_exist_ok=True)
        self.assertTrue((self.root / '.github/CODEOWNERS').is_file())
        for script in ['site_common.py', 'check_links.py', 'check_no_third_party.py',
                       'check_privacy_text.py', 'check_invariants.py']:
            with self.subTest(script=script):
                result = self.cli(script)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        # Exercise the real authors command using isolated synthetic history.
        env = dict(os.environ, GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull,
                   GIT_AUTHOR_NAME='Fixture', GIT_COMMITTER_NAME='Fixture',
                   GIT_AUTHOR_EMAIL='noreply@github.com', GIT_COMMITTER_EMAIL='noreply@github.com')
        for args in [['init', '--quiet'], ['-c', 'core.hooksPath=/dev/null', 'commit',
                                         '--quiet', '--allow-empty', '-m', 'fixture']]:
            subprocess.run(['git', *args], cwd=self.root, env=env, check=True, capture_output=True)
        result = subprocess.run([sys.executable, '-I', '-B', str(SOURCE / 'scripts/check_authors.py'),
                                 '--root', str(self.root), '--', 'HEAD'], capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        # All seven matrix entrypoints must pass discovery and markup preflight.
        # npm/browser boundaries and the recursive suite call are recorded only;
        # the Python content commands and authors command above execute for real.
        with patch.object(ci_checks, 'run') as run, patch.object(ci_checks, 'accessibility'), \
                patch.dict(os.environ, EVENT_NAME='push', BEFORE='0' * 40, AFTER='HEAD'):
            for kind in ['html', 'a11y', 'links', 'no-third-party', 'authors', 'privacy-text', 'invariants']:
                with patch.object(sys, 'argv', ['ci_checks.py', '--root', str(self.root), '--', kind]):
                    self.assertEqual(ci_checks.main(), 0, kind)
            self.assertEqual(run.call_count, 7)

    def test_r5_unknown_github_file(self):
        shutil.copytree(SOURCE, self.root, dirs_exist_ok=True)
        for name in ['extra', 'extra.txt', 'CODEOWNERS.bak', 'workflows/extra.yml']:
            target = self.root / '.github' / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text('unknown')
            for script in ['site_common.py', 'check_links.py', 'check_no_third_party.py',
                           'check_privacy_text.py', 'check_invariants.py']:
                result = self.cli(script)
                self.assertEqual(result.returncode, 1, (name, script, result.stdout, result.stderr))
                self.assertIn(b'Unsupported .github file', result.stdout + result.stderr)
            with patch.object(sys, 'argv', ['ci_checks.py', '--root', str(self.root), '--', 'html']), \
                    patch.object(ci_checks, 'run') as run, contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(ci_checks.main(), 1)
                run.assert_not_called()
            target.unlink()
        for name in ['CODEOWNERS', 'nested/.github/CODEOWNERS']:
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text('unknown')
            self.assertTrue(common.discovery_errors(self.root))
            target.unlink()

    def test_all_document_suffixes_and_no_exclusions(self):
        for parent in ['scripts/fixtures', '.github', 'node_modules', '.venv', 'nested', 'legal']:
            for suffix in ['.HTML', '.htm', '.XHTML', '.SVG']:
                with self.subTest(parent=parent, suffix=suffix):
                    p = self.root / parent / ('extra' + suffix)
                    p.parent.mkdir(parents=True, exist_ok=True)
                    p.write_text('<script/>')
                    self.assertIn(p, common.site_files(self.root))
                    self.error(resources.check, 'Unexpected document')
                    p.unlink()
        git = self.root / '.git'
        git.mkdir()
        (git / 'ignored.HTML').write_text('<script/>')
        self.assertEqual(common.discovery_errors(self.root), [])

    def test_missing_document(self):
        (self.root / '404.html').unlink()
        self.error(resources.check, 'Missing document: 404.html')

    def test_unsupported_types(self):
        for suffix in ['.xml', '.pdf', '.js', '.woff2', '.mhtml', '.png', '.unknown']:
            p = self.root / ('extra' + suffix)
            p.write_text('fixture')
            self.error(resources.check, 'Unsupported served file type')
            p.unlink()

    def test_raw_markdown_and_nojekyll_discovery(self):
        p = self.root / 'raw.md'
        p.write_text('# Raw, not rendered')
        self.assertNotIn(p, common.site_files(self.root))
        (self.root / '.nojekyll').unlink()
        self.assertIn(p, common.site_files(self.root))
        self.error(resources.check, 'Unexpected document')

    def test_symlink(self):
        (self.root / 'alias.txt').symlink_to('index.html')
        self.error(resources.check, 'Unsupported symlink')

    def test_option_injection_filename(self):
        p = self.root / '--version\nprobe.html'
        p.write_text('<script/>')
        self.error(resources.check, 'Unsafe served path')
        result = self.cli('site_common.py')
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, b'')
        p.unlink()
        for name in ['space name.html', 'unicodé.html', 'control\x01.html']:
            p = self.root / name
            p.write_text('fixture')
            self.error(resources.check, 'Unsafe served path')
            p.unlink()

    def cli(self, script, *args):
        return subprocess.run([sys.executable, '-I', '-B', str(SOURCE / 'scripts' / script),
                               *args, '--', str(self.root)], capture_output=True)

    def test_discovery_nul_and_prefix(self):
        result = self.cli('site_common.py')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, b'./404.html\0./coami-icon.svg\0'
                         b'./img/coami-logo-light-on-dark.svg\0./img/coami-logo.svg\0'
                         b'./index.html\0./privacy.html\0')

    def test_svg_is_checked(self):
        self.edit('coami-icon.svg', '</svg>', '<script/></svg>')
        self.error(resources.check, 'forbidden <script>')

    def test_svg_xml_vectors(self):
        self.edit('coami-icon.svg', '<svg ', '<?xml-stylesheet href="https://evil.test/a.css"?><svg ')
        self.error(resources.check, 'forbidden XML processing instruction')
        for tag in ['svg:script', 'animate', 'set']:
            (self.root / 'coami-icon.svg').write_text((SOURCE / 'coami-icon.svg').read_text())
            self.edit('coami-icon.svg', '</svg>', '<' + tag + '/></svg>')
            self.error(resources.check, 'invalid SVG XML' if ':' in tag else 'forbidden <' + tag)

    def test_csp_exact_ascii(self):
        for content in [resources.CSP.replace(' ', '\u00a0'),
                        '; '.join(reversed(resources.CSP.split('; '))),
                        resources.CSP + ';', resources.CSP.replace("'", '&#39;'), "default-src 'none'"]:
            original = (SOURCE / 'index.html').read_text()
            (self.root / 'index.html').write_text(original.replace(resources.CSP, content))
            self.error(resources.check, 'byte-exact ASCII policy')

    def test_csp_template_noscript_and_body(self):
        for wrapper in ['template', 'noscript', 'div']:
            original = (SOURCE / 'index.html').read_text()
            tag = next(line for line in original.splitlines() if 'Content-Security-Policy' in line)
            (self.root / 'index.html').write_text(original.replace(tag, f'<{wrapper}>{tag}</{wrapper}>'))
            self.error(resources.check, 'CSP must be active')
        original = (SOURCE / 'index.html').read_text()
        tag = next(line for line in original.splitlines() if 'Content-Security-Policy' in line)
        (self.root / 'index.html').write_text(original.replace(tag, '').replace('<body>', '<body>' + tag))
        self.error(resources.check, 'CSP must be active')

    def test_csp_in_inactive_head(self):
        original = (SOURCE / 'index.html').read_text()
        for opening, closing in [('<template><head>', '</head></template>'),
                                 ('<noscript><head>', '</head></noscript>'),
                                 ('<body><head>', '</head></body>')]:
            (self.root / 'index.html').write_text(original.replace('<head>', opening).replace('</head>', closing))
            self.error(resources.check, 'CSP must be active')

    def test_csp_two_or_missing(self):
        original = (SOURCE / 'index.html').read_text()
        tag = next(line for line in original.splitlines() if 'Content-Security-Policy' in line)
        for replacement in ['', tag + tag]:
            (self.root / 'index.html').write_text(original.replace(tag, replacement))
            self.error(resources.check, 'exactly one CSP')

    def test_csp_duplicate_content(self):
        self.edit('index.html', 'content="' + resources.CSP + '"',
                  'content="' + resources.CSP + '" content="' + resources.CSP + '"')
        self.error(resources.check, 'byte-exact ASCII policy')

    def test_csp_after_stylesheet(self):
        self.edit('index.html', '<meta http-equiv="Content-Security-Policy"',
                  '<link rel="stylesheet" href="style.css"><meta http-equiv="Content-Security-Policy"')
        self.error(resources.check, 'CSP must be active')

    def test_all_refresh_rejected(self):
        for delay in ['.0;url=', '0..;url=', '0;url=', '0, URL=', '']:
            original = (SOURCE / 'index.html').read_text()
            (self.root / 'index.html').write_text(original.replace('</head>',
                f'<meta http-equiv="refresh" content="{delay}https://external.example/"></head>'))
            self.error(resources.check, 'forbidden meta refresh')
        self.edit('index.html', 'https://external.example/', '/privacy.html')
        self.error(resources.check, 'forbidden meta refresh')

    def test_exact_navigation_origins(self):
        for url in ['https://coami.ai:444/', 'https://coami.ai/', '//ico.org.uk/make-a-complaint/',
                    'http://ico.org.uk/make-a-complaint/', 'https://ico.org.uk:444/make-a-complaint/',
                    'https://ico.org.uk:443/make-a-complaint/', 'https://ico.org.uk.evil/',
                    'https://ico.org.uk@evil.test/', 'https://elsewhere.test/',
                    'mailto:other@coami.ai', 'javascript:alert(1)', 'https:&#10;//evil.test/',
                    r'\\evil.test/']:
            original = (SOURCE / 'index.html').read_text()
            (self.root / 'index.html').write_text(original.replace('</body>', f'<a href="{url}">Test</a></body>'))
            self.error(resources.check, 'forbidden navigation URL')
        for url in resources.ABSOLUTE_LINKS:
            self.assertTrue(resources.navigation_allowed(url))
        for url in ['#main', '/privacy.html', 'privacy.html', '/?a=b#main']:
            self.assertTrue(resources.navigation_allowed(url))

    def test_resource_absolute_urls(self):
        for tag in ['<img src="{}">', '<link href="{}">', '<input action="{}">', '<img data="{}">']:
            for url in ['https://coami.ai/a', '//evil.test/a', 'data:image/png,x',
                        'https:&#10;//evil.test/a', r'\\evil.test/a']:
                (self.root / 'index.html').write_text((SOURCE / 'index.html').read_text())
                self.body(tag.format(url))
                self.error(resources.check, 'forbidden resource URL')

    def test_svg_image_href(self):
        for attr in ['href', 'xlink:href']:
            (self.root / 'index.html').write_text((SOURCE / 'index.html').read_text())
            self.body(f'<svg><image {attr}="local.png"/></svg>')
            self.error(resources.check, 'forbidden SVG image reference')

    def test_svg_use_off_document(self):
        for attr in ['href', 'xlink:href']:
            (self.root / 'index.html').write_text((SOURCE / 'index.html').read_text())
            self.body(f'<svg><use {attr}="other.svg#id"/></svg>')
            self.error(resources.check, 'forbidden off-document SVG use')
        (self.root / 'index.html').write_text((SOURCE / 'index.html').read_text())
        self.body('<svg><use href="#main"/></svg>')
        self.error(resources.check, 'forbidden off-document SVG use')

    def test_r4_dtd_entities(self):
        for replacement in ['<script xmlns="http://www.w3.org/2000/svg">alert(1)</script>',
                            '<image xmlns="http://www.w3.org/2000/svg" href="https://evil.test/x"/>']:
            document = ('<!DOCTYPE svg [<!ENTITY payload \'' + replacement + '\'>]>'
                        '<svg xmlns="http://www.w3.org/2000/svg">&payload;</svg>')
            (self.root / 'coami-icon.svg').write_text(document)
            self.error(resources.check, 'forbidden DTD/entity declaration')
            self.error(resources.check, 'invalid SVG XML')
        for value in ['<!DOCTYPE html [<!ENTITY payload "text">]>', '<!ENTITY payload "text">']:
            self.assertIn('forbidden DTD/entity declaration', common.Page(value).errors)

    def test_r4_xml_parser_refuses_dtd(self):
        # Exercise the parser itself, independently of the lexical preflight.
        with self.assertRaisesRegex(ValueError, 'forbidden DTD/entity declaration'):
            ET.fromstring('<!DOCTYPE svg [<!ENTITY x "expanded">]><svg>&x;</svg>',
                          parser=ET.XMLParser(target=common.NoDTDTreeBuilder()))

    def test_r4_entities_html_and_svg(self):
        for entity in ['&nbsp;', '&copy;', '&payload;', '&#xnothex;', '&amp']:
            for name in ['index.html', 'coami-icon.svg']:
                (self.root / name).write_text((SOURCE / name).read_text())
                end = '</svg>' if name.endswith('.svg') else '</body>'
                self.edit(name, end, entity + end)
                self.error(resources.check, 'forbidden entity reference')
        self.assertEqual(common.markup_errors('&amp; &lt; &gt; &apos; &quot; &#65; &#x41;'), [])
        page = common.SVGPage('<svg xmlns="http://www.w3.org/2000/svg"><text>'
                              '&amp;&lt;&gt;&apos;&quot;&#65;&#x41;</text></svg>')
        self.assertEqual(page.errors, [])

    def test_r4_svg_xml_well_formed(self):
        for text in ['<svg xmlns="http://www.w3.org/2000/svg"><rect></svg>',
                     '<svg xmlns="http://www.w3.org/2000/svg" viewBox="x" viewBox="y"/>',
                     '<svg xmlns="http://www.w3.org/2000/svg"/><svg/>']:
            (self.root / 'coami-icon.svg').write_text(text)
            self.error(resources.check, 'invalid SVG XML')

    def test_r4_svg_duplicate_attribute_case(self):
        page = common.SVGPage('<svg xmlns="http://www.w3.org/2000/svg" fill="red" FILL="blue"/>')
        self.assertIn('duplicate attribute name in SVG', page.errors)

    def test_r4_svg_xml_allowlist(self):
        for text, diagnostic in [
                ('<SVG/>', 'SVG root must be svg'),
                ('<svg xmlns="http://www.w3.org/2000/svg"><a/></svg>', 'forbidden <a> SVG element'),
                ('<svg xmlns="http://www.w3.org/2000/svg"><RECT/></svg>', 'forbidden <rect> SVG element'),
                ('<svg xmlns="http://www.w3.org/2000/svg"><g xmlns="urn:other"/></svg>', 'SVG element'),
                ('<svg xmlns="http://www.w3.org/2000/svg" unknown="x"/>', 'forbidden SVG attribute'),
                ('<svg xmlns="http://www.w3.org/2000/svg" FILL="red"/>', 'forbidden SVG attribute')]:
            with self.subTest(text=text):
                self.assertIn(diagnostic, '\n'.join(common.SVGPage(text).errors))

    def test_r4_inline_svg_allowlist(self):
        self.body('<svg><a/></svg>')
        self.error(resources.check, 'forbidden <a> SVG element')
        self.body('<svg mystery="x"></svg>')
        self.error(resources.check, 'forbidden SVG attribute mystery')

    def test_r4_svg_resource_elements(self):
        for tag in ['image', 'feImage', 'use', 'foreignObject', 'script', 'animate', 'animateColor', 'set']:
            for key in ['href', 'xlink:href']:
                for url in ['https://ico.org.uk/make-a-complaint/', '#local']:
                    for name in ['index.html', 'coami-icon.svg']:
                        (self.root / name).write_text((SOURCE / name).read_text())
                        element = f'<{tag} {key}="{url}"/>'
                        if name.endswith('.svg'):
                            self.edit(name, '<svg ', '<svg xmlns:xlink="http://www.w3.org/1999/xlink" ')
                            self.edit(name, '</svg>', element + '</svg>')
                        else:
                            self.body('<svg>' + element + '</svg>')
                        self.error(resources.check, 'forbidden <' + tag.lower())

    def test_r4_non_navigation_hrefs(self):
        for element in ['<div href="{}"></div>', '<p xlink:href="{}"></p>',
                        '<svg><g href="{}"/></svg>', '<svg><g src="{}"/></svg>']:
            (self.root / 'index.html').write_text((SOURCE / 'index.html').read_text())
            self.body(element.format(privacy.ICO))
            self.error(resources.check, 'forbidden resource URL')
        self.assertTrue(resources.navigation_allowed(privacy.ICO))

    def test_r4_attribute_urls(self):
        for value in ['url(https://evil.test/x)', "url('https://ico.org.uk/make-a-complaint/')",
                      r'u\72l(//evil.test/x)', 'u/**/rl(https://evil.test/x)']:
            for name, tag in [('coami-icon.svg', '<circle fill="{}"/>'),
                              ('index.html', '<svg><circle fill="{}"/></svg>'),
                              ('index.html', '<p data-paint="{}">text</p>')]:
                (self.root / name).write_text((SOURCE / name).read_text())
                end = '</svg>' if name.endswith('.svg') else '</body>'
                self.edit(name, end, tag.format(value) + end)
                self.error(resources.check, 'forbidden CSS resource vector in attribute')

    def test_r4_duplicate_attributes(self):
        for name in ['index.html', 'privacy.html', '404.html']:
            for old, new in [
                    ('http-equiv="Content-Security-Policy"',
                     'http-equiv="content-type" HTTP-EQUIV="Content-Security-Policy"'),
                    ('content="' + resources.CSP + '"',
                     'content="' + resources.CSP + '" CONTENT="' + resources.CSP + '"'),
                    ('<body>', '<body id="one" ID="two">')]:
                (self.root / name).write_text((SOURCE / name).read_text())
                self.edit(name, old, new)
                self.error(resources.check, 'duplicate attribute name')

    def test_r4_markup_all_checkers(self):
        self.edit('privacy.html', '<body>', '<body id="first" ID="second">')
        for checker in [resources.check, privacy.check, links.check, invariants.check]:
            with self.subTest(checker=checker.__module__):
                self.error(checker, 'duplicate attribute name')

    def test_r4_validator_directives(self):
        for directive in ['[html-validate-disable-next no-dup-attr,attribute-allowed-values]',
                          'HTML-VALIDATE disable', 'h t m l - v a l i d a t e-disable',
                          'eslint-disable', 'pa11y ignore', 'axe-disable']:
            (self.root / 'index.html').write_text((SOURCE / 'index.html').read_text())
            self.body('<!-- ' + directive + ' -->')
            self.error(resources.check, 'forbidden inline validator directive')
        # Round 6 deliberately replaces r4's ordinary-comment permission.
        self.assertIn('comments/marked sections forbidden', '\n'.join(
            common.Page('<!-- ordinary comment -->').errors))

    def test_r4_ci_markup_preflight(self):
        self.body('<!-- [html-validate-disable-next no-dup-attr] -->')
        with patch.object(sys, 'argv', ['ci_checks.py', '--root', str(self.root), '--', 'html']), \
                patch.object(ci_checks, 'run') as run, contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(ci_checks.main(), 1)
        run.assert_not_called()

    def test_r4_privacy_visibility(self):
        for old in ['<main id="main"', '<body', '<article class="legal text"', '<p class="meta"']:
            for attr in ['popover', 'hidden', 'inert', 'aria-hidden="false"', 'style=""']:
                (self.root / 'privacy.html').write_text((SOURCE / 'privacy.html').read_text())
                self.edit('privacy.html', old + '>', old + ' ' + attr + '>')
                self.error(privacy.check, 'Privacy notice visibility')

    def test_r4_footer_visibility(self):
        for name in ['index.html', 'privacy.html', '404.html']:
            for old in ['<footer class="site"', '<body', '<html lang="en-GB"']:
                for attr in ['popover', 'hidden', 'inert', 'aria-hidden="false"', 'style=""']:
                    (self.root / name).write_text((SOURCE / name).read_text())
                    self.edit(name, old + '>', old + ' ' + attr + '>')
                    self.assertTrue(invariants.check(self.root), (name, old, attr))
            (self.root / name).write_text((SOURCE / name).read_text())
            self.edit(name, '<footer class="site">', '<footer class="site skip">')
            self.error(invariants.check, 'Legal footer visibility class placement')

    def test_r4_visibility_attributes_guard(self):
        # aria-hidden=false is forbidden by Legal even though hidden() is false.
        page = common.Page('<html><body><footer class="site" aria-hidden="false"></footer></body></html>')
        footer = next(n for n in page.nodes if n.tag == 'footer')
        self.assertIn('Legal footer visibility is not approved', '\n'.join(
            visibility.visibility_errors(page, 'index.html', footer, 'Legal footer')))

    def test_r4_class_placement(self):
        for old, new in [('<main id="main">', '<main id="main" class="meta">'),
                         ('<body>', '<body class="wrap">'),
                         ('<p class="meta">', '<p class="plain">'),
                         ('<article class="legal text">', '<article class="meta">'),
                         ('<p>This notice', '<p class="meta">This notice')]:
            (self.root / 'privacy.html').write_text((SOURCE / 'privacy.html').read_text())
            self.edit('privacy.html', old, new)
            self.error(privacy.check, 'Privacy notice visibility class placement')

    def test_r4_class_pins_match_approved_pages(self):
        for name in ['index.html', 'privacy.html', '404.html']:
            page = common.Page((SOURCE / name).read_text())
            protected = [n for n in page.nodes if n.tag == 'footer' or
                         (name == 'privacy.html' and n.tag == 'main')]
            nodes = {n for element in protected for n in page.nodes
                     if element in n.ancestors() or n in element.ancestors()}
            actual = {visibility.node_path(n): tuple(n.attr['class'].split())
                      for n in nodes if n.attr.get('class')}
            self.assertEqual(actual, visibility.LEGAL_CLASSES[name])

    def test_r4_github_privacy_href(self):
        self.edit('privacy.html', privacy.GITHUB_PRIVACY, '/index.html')
        self.error(privacy.check, 'privacy statement link href')

    def test_r4_banned_metadata(self):
        for old, new in [
                ('<title>', '<title>Certified secure GDPR compliant '),
                ('name="description" content="', 'name="description" content="Certified secure GDPR compliant '),
                ('</head>', '<meta name="OG:description" content="Certified secure GDPR compliant"></head>'),
                ('</head>', '<meta name="twitter:title" content="Certified secure GDPR compliant"></head>'),
                ('</head>', '<meta property="og:title" content="Certified secure GDPR compliant"></head>'),
                ('</head>', '<meta property="TWITTER:description" content="Certified secure GDPR compliant"></head>'),
                ('<body>', '<body title="Certified secure GDPR compliant">'),
                ('<body>', '<body aria-label="Certified secure GDPR compliant">'),
                ('</body>', '<img alt="Certified secure GDPR compliant"></body>')]:
            (self.root / 'index.html').write_text((SOURCE / 'index.html').read_text())
            self.edit('index.html', old, new)
            self.error(invariants.check, 'banned public metadata/attribute copy')

    def test_css_resource_vectors(self):
        for rule in ['a{background:image-set("local.png" 1x)}',
                     'a{background:-webkit-image-set("https://evil.test/x" 1x)}',
                     'a{background:url(local.png)}', '@import "local.css";',
                     r'a{background:u\72l(local.png)}', r'@im\70ort "local.css";',
                     'a{background:u/**/rl(local.png)}']:
            (self.root / 'style.css').write_text(rule)
            self.error(resources.check, 'forbidden CSS resource vector')

    def test_inline_css_resource_vectors(self):
        for value in ['<style>a{background:url(local.png)}</style>',
                      '<p style="background:image-set(\'local.png\' 1x)">Test</p>']:
            (self.root / 'index.html').write_text((SOURCE / 'index.html').read_text())
            self.body(value)
            self.error(resources.check, 'forbidden CSS resource vector')

    def test_srcset_poster_ping(self):
        for attr in ['srcset', 'poster', 'ping']:
            (self.root / 'index.html').write_text((SOURCE / 'index.html').read_text())
            self.body(f'<a {attr}="local.png">Test</a>')
            self.error(resources.check, f'forbidden resource vector {attr}')

    def test_link_resource_hints(self):
        for rel in ['preload', 'prefetch', 'preconnect', 'dns-prefetch', 'modulepreload', 'manifest']:
            (self.root / 'index.html').write_text((SOURCE / 'index.html').read_text())
            self.body(f'<link rel="alternate {rel.upper()}" href="/index.html">')
            self.error(resources.check, 'forbidden link resource hint')

    def test_event_handlers(self):
        for attr in ['onclick', 'onload', 'onerror', 'onanimationstart', 'ONFOCUS']:
            (self.root / 'index.html').write_text((SOURCE / 'index.html').read_text())
            self.body(f'<p {attr}="">Test</p>')
            self.error(resources.check, 'forbidden attribute')

    def test_static_content(self):
        for tag in ['script', 'iframe', 'embed', 'object', 'form', 'style', 'base', 'foreignObject']:
            (self.root / 'index.html').write_text((SOURCE / 'index.html').read_text())
            self.body(f'<{tag}></{tag}>')
            self.error(resources.check, 'forbidden <' + tag.lower())
        self.body('<p style="">Test</p>')
        self.error(resources.check, 'forbidden attribute style')

    def test_links_and_fragments(self):
        self.body('<a href="/privacy.html#absent">Bad</a>')
        self.error(links.check, 'missing fragment')
        self.body('<a href="missing.html">Bad</a>')
        self.error(links.check, 'missing file')
        self.body('<a href="%2e%2e/outside.html">Bad</a>')
        self.error(links.check, 'path leaves repository')
        self.body('<a href="mailto:">Bad</a>')
        self.error(links.check, 'mailto needs an address')

    def test_privacy_hidden_notice(self):
        for old, new in [('<main id="main">', '<main id="main" hidden>'),
                         ('<body>', '<body aria-hidden="true">'),
                         ('<article class="legal text">', '<article class="legal text" inert>'),
                         ('<main id="main">', '<main id="main" style="display:none">'),
                         ('<article class="legal text">', '<article class="legal text invisible">'),
                         ('<main id="main">', '<template><main id="main">'),
                         ('<main id="main">', '<details><main id="main">'),
                         ('<main id="main">', '<noscript><main id="main">')]:
            (self.root / 'privacy.html').write_text((SOURCE / 'privacy.html').read_text())
            self.edit('privacy.html', old, new)
            self.error(privacy.check, 'Privacy notice visibility')

    def test_privacy_css_visibility(self):
        with (self.root / 'style.css').open('a') as f:
            f.write('\n.legal{display:none}')
        self.error(privacy.check, 'approved style.css hash')

    def test_privacy_additional_stylesheet(self):
        self.edit('privacy.html', '</head>', '<link rel="stylesheet" href="hide.css"></head>')
        self.error(privacy.check, 'only the approved stylesheet')

    def test_privacy_exact_text(self):
        for old, new in [('no cookies', 'some cookies'), ("visitors' IP", 'visitors’ IP'),
                         ('EU–US', 'EU-US')]:
            (self.root / 'privacy.html').write_text((SOURCE / 'privacy.html').read_text())
            self.edit('privacy.html', old, new)
            self.error(privacy.check, 'Privacy visible text differs')

    def test_privacy_extra_text(self):
        self.body('<p>We also track visitors.</p>', 'privacy.html')
        self.error(privacy.check, 'Extra visible text')

    def test_privacy_header(self):
        self.edit('privacy.html', '>Contact<', '>Other<')
        self.error(privacy.check, 'Privacy header visible text')

    def test_ico_href(self):
        self.edit('privacy.html', privacy.ICO, 'https://ico.org.uk/')
        self.error(privacy.check, 'ICO link href')

    def test_stale_privacy_folder(self):
        (self.root / 'privacy').mkdir()
        (self.root / 'privacy/index.html').write_text((self.root / 'privacy.html').read_text())
        self.edit('privacy.html', 'no cookies', 'some cookies')
        self.error(privacy.check, 'Legacy privacy/ folder')
        self.error(privacy.check, 'Privacy visible text differs')
        self.error(invariants.check, 'Legacy privacy/ folder')
        self.error(resources.check, 'Unexpected document')

    def test_privacy_main_structure(self):
        for old, new in [('<main id="main">', '<section id="main">'),
                         ('</main>', ''), ('</main>', '</main><main></main>')]:
            (self.root / 'privacy.html').write_text((SOURCE / 'privacy.html').read_text())
            self.edit('privacy.html', old, new)
            self.error(privacy.check, 'exactly one complete')

    def test_d26_hash(self):
        with (self.root / privacy.D26_PATH).open('a') as f:
            f.write('\n')
        self.error(privacy.check, 'D26 sha256 differs')

    def test_cname(self):
        for value in [b'attacker.example', b'coami.ai\n\n', b'coami.ai\r\n', b'coami.ai ']:
            (self.root / 'CNAME').write_bytes(value)
            self.error(invariants.check, 'CNAME must be exactly')
        for value in [b'coami.ai', b'coami.ai\n']:
            (self.root / 'CNAME').write_bytes(value)
            self.assertEqual(invariants.check(self.root), [])
        (self.root / 'CNAME').unlink()
        self.error(invariants.check, 'CNAME must be exactly')

    def test_nojekyll(self):
        (self.root / '.nojekyll').write_text('not empty')
        self.error(invariants.check, '.nojekyll must exist and be empty')
        (self.root / '.nojekyll').unlink()
        self.error(invariants.check, '.nojekyll must exist and be empty')

    def test_legal_footer_every_page(self):
        for name in ['index.html', 'privacy.html', '404.html']:
            p = self.root / name
            before, footer = p.read_text().split('<footer', 1)
            p.write_text(before + '<footer' + footer.replace('17310137', '00000000'))
            self.error(invariants.check, name + ': Legal footer text')

    def test_footer_links(self):
        self.edit('404.html', 'href="privacy.html"', 'href="/index.html"')
        self.error(invariants.check, 'Legal footer links must be exact')

    def test_banned_copy(self):
        for text in ['MFA', '2FA', 'TOTP', 'WebAuthn', 'OTP', 'secure', 'compliant',
                     'GDPR', 'certified', 'UK-hosted', '®', 'Testimonials', '100 users']:
            (self.root / 'index.html').write_text((SOURCE / 'index.html').read_text())
            self.body(f'<p>{text}</p>')
            self.error(invariants.check, 'banned visible copy')

    def test_cli_isolated(self):
        for name in ['site_common.py', 'ci_checks.py']:
            result = self.cli(name, '--help')
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for name in ['check_links.py', 'check_no_third_party.py', 'check_privacy_text.py', 'check_invariants.py']:
            result = self.cli(name)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.body('<script/>')
        result = self.cli('check_no_third_party.py')
        self.assertEqual(result.returncode, 1)


class WorkflowTest(unittest.TestCase):
    def setUp(self):
        self.workflow = (SOURCE / '.github/workflows/site-checks.yml').read_text()
        self.temp = tempfile.TemporaryDirectory(dir=os.environ.get('TMPDIR', tempfile.gettempdir()))
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'site').mkdir()
        (self.root / 'base').mkdir()

    def test_base_checkout_and_trust(self):
        self.assertIn('ref: ${{ github.event.pull_request.base.sha }}', self.workflow)
        self.assertIn('path: base', self.workflow)
        self.assertEqual(self.workflow.count('persist-credentials: false'), 2)
        self.assertIn('checks="$GITHUB_WORKSPACE/base"', self.workflow)
        self.assertIn('python3 -I -B "$CHECKS/scripts/ci_checks.py"', self.workflow)
        self.assertNotIn('pull_request_target', self.workflow)
        self.assertIn('contents: read', self.workflow)
        for line in self.workflow.splitlines():
            if 'uses:' in line:
                self.assertRegex(line, r'actions/[a-z-]+@[0-9a-f]{40}\b')

    def test_workflow_selection(self):
        # Execute the actual workflow shell block, with no Git or network.
        block = self.workflow.split('      - name: Select enforcement source\n', 1)[1]
        block = block.split('        run: |\n', 1)[1].split('      - name:', 1)[0]
        shell = '\n'.join(line[10:] for line in block.splitlines())
        for event, marker, expected, warning in [('push', False, 'site', False),
                                                ('pull_request', False, 'site', True),
                                                ('pull_request', True, 'base', False)]:
            if marker:
                (self.root / 'base/scripts').mkdir(exist_ok=True)
            envfile = self.root / 'env.txt'
            envfile.write_text('')
            result = subprocess.run(['bash', '-e', '-c', shell], capture_output=True, text=True,
                                    env=dict(os.environ, EVENT_NAME=event,
                                             GITHUB_WORKSPACE=str(self.root), GITHUB_ENV=str(envfile)))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(envfile.read_text().strip(), 'CHECKS=' + str(self.root / expected))
            self.assertEqual('WARNING:' in result.stdout, warning)

    def test_change_report(self):
        self.assertIn('CHECK FILE CHANGES', self.workflow)
        self.assertIn('continue-on-error: true', self.workflow)
        for name in ['.github/', 'scripts/', '.htmlvalidate.json', '.pa11yci.json', 'legal/']:
            self.assertIn("'" + name + "'", self.workflow)
        self.assertIn("'--name-only', '-z'", self.workflow)
        self.assertIn("print('\\n'.join(repr(p)", self.workflow)

    def test_trusted_commands(self):
        base = self.root / 'base'
        root = self.root / 'site'
        (root / 'index.html').write_text('candidate')
        html = ci_checks.commands('html', base, root)[0]
        self.assertIn(str(base / '.htmlvalidate.json'), html)
        self.assertEqual(html[-2:], ['--', './index.html'])
        command = ci_checks.commands('no-third-party', base, root)[0]
        self.assertEqual(command[1:3], ['-I', '-B'])
        self.assertEqual(command[3], str(base / 'scripts/check_no_third_party.py'))
        self.assertEqual(command[-2:], ['--', str(root)])
        self.assertIn(str(base / 'scripts/test_checks.py'), ci_checks.commands('links', base, root)[0])
        self.assertEqual(ci_checks.commands('invariants', base, root)[0][3],
                         str(base / 'scripts/check_invariants.py'))
        self.assertIn('invariants]', self.workflow)

    def test_runner_rejects_unsafe_discovery(self):
        candidate = self.root / 'site'
        for name in ASSETS:
            p = candidate / name
            p.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(SOURCE / name, p)
        (candidate / '--version\nprobe.html').write_text('fixture')
        output = io.StringIO()
        with patch.object(sys, 'argv', ['ci_checks.py', '--root', str(candidate), '--', 'html']), \
                patch.object(ci_checks, 'run') as run, contextlib.redirect_stdout(output):
            self.assertEqual(ci_checks.main(), 1)
        run.assert_not_called()
        self.assertIn('Unsafe served path', output.getvalue())

    def test_candidate_cannot_replace_validator(self):
        base = self.root / 'base'
        candidate = self.root / 'site'
        shutil.copytree(SOURCE / 'scripts', base / 'scripts')
        (candidate / 'scripts').mkdir()
        (candidate / 'scripts/check_no_third_party.py').write_text('raise SystemExit(0)')
        for name in ASSETS:
            p = candidate / name
            p.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(SOURCE / name, p)
        p = candidate / 'index.html'
        p.write_text(p.read_text().replace('</body>', '<script src="https://evil.test/x"></script></body>'))
        result = subprocess.run(ci_checks.commands('no-third-party', base, candidate)[0], capture_output=True)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn(b'forbidden <script>', result.stdout)

    def test_accessibility_trusted_config(self):
        base, candidate = self.root / 'base', self.root / 'site'
        (base / '.pa11yci.json').write_text('{"defaults":{"trusted":true}}')
        (candidate / '.pa11yci.json').write_text('{"defaults":{"trusted":false}}')
        (candidate / '.nojekyll').write_text('')
        (candidate / 'index.html').write_text('fixture')
        server = MagicMock()
        server.poll.return_value = None
        response = MagicMock()
        response.__enter__.return_value.status = 200
        seen = []

        def capture(command, cwd):
            config = Path(command[command.index('--config') + 1])
            seen.append((json.loads(config.read_text()), config))
            self.assertEqual(cwd, base)
            self.assertFalse(config.is_relative_to(candidate))
            self.assertEqual(command[-1], '--')

        with patch.object(ci_checks.subprocess, 'Popen', return_value=server) as popen, \
                patch.object(ci_checks, 'urlopen', return_value=response), \
                patch.object(ci_checks, 'run', side_effect=capture):
            ci_checks.accessibility(base, candidate)
        self.assertEqual(seen[0][0]['defaults'], {'trusted': True})
        self.assertEqual(seen[0][0]['urls'], ['http://127.0.0.1:8080/index.html'])
        self.assertFalse(seen[0][1].exists())
        self.assertIn('--', popen.call_args.args[0])
        server.terminate.assert_called_once()


class AuthorsTest(unittest.TestCase):
    GOOD = '12345+Test-User@users.noreply.github.com'

    def test_allowlist(self):
        for email in [self.GOOD, '1+a@users.noreply.github.com', 'noreply@github.com']:
            self.assertTrue(authors.allowed(email))
        for email in ['private@example.test', 'a@users.noreply.github.com',
                      '123+a@users.noreply.github.com.evil', '123+a@USERS.noreply.github.com',
                      'no-reply@github.com', self.GOOD + '\n', '１２３+a@users.noreply.github.com']:
            self.assertFalse(authors.allowed(email))

    def test_ranges(self):
        self.assertEqual(authors.revision_for_push('0' * 40, 'abc'), 'abc')
        self.assertEqual(authors.revision_for_push('abc', 'def'), 'abc..def')
        with self.assertRaises(ValueError):
            authors.revision_for_push('', '')

    def test_both_roles_all_commits_and_redaction(self):
        result = subprocess.CompletedProcess([], 0,
            'a\0private@example.test\0' + self.GOOD + '\0b\0' + self.GOOD + '\0hidden@example.test\0')
        with patch.object(authors.subprocess, 'run', return_value=result) as call:
            errors = authors.check(SOURCE, 'base..head')
        self.assertEqual(len(errors), 2)
        self.assertIn('a: author', errors[0])
        self.assertIn('b: committer', errors[1])
        self.assertNotIn('@', '\n'.join(errors))
        self.assertEqual(call.call_args.args[0][-2:], ['base..head', '--'])
        self.assertIn('--no-use-mailmap', call.call_args.args[0])

    def test_fail_closed(self):
        for result in [subprocess.CompletedProcess([], 1, ''), subprocess.CompletedProcess([], 0, 'malformed')]:
            with patch.object(authors.subprocess, 'run', return_value=result):
                self.assertTrue(authors.check(SOURCE, 'bad..head'))

    def test_isolated_cli(self):
        result = subprocess.run([sys.executable, '-I', '-B', str(SOURCE / 'scripts/check_authors.py'), '--help'],
                                capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main(verbosity=2)
