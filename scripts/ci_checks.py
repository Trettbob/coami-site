"""Run trusted validators/configs against an explicitly separate candidate tree."""
import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.parse import quote
from urllib.request import urlopen

sys.path.insert(0, str(Path(__file__).resolve().parent))
from site_common import discovery_errors, read_page, site_files


def run(command, cwd):
    subprocess.run(command, cwd=cwd, check=True)


def commands(kind, checks, root):
    python = [sys.executable, '-I', '-B']
    def script(name, *args):
        return python + [str(checks / 'scripts' / name), *args]
    if kind == 'links':
        return [script('test_checks.py', '--'), script('check_links.py', '--', str(root))]
    if kind == 'no-third-party':
        return [script('check_no_third_party.py', '--', str(root))]
    if kind == 'privacy-text':
        return [script('check_privacy_text.py', '--', str(root))]
    if kind == 'invariants':
        return [script('check_invariants.py', '--', str(root))]
    if kind == 'html':
        # Explicit trusted config disables candidate config discovery. ./ paths
        # come after the validator's option terminator; no shell splitting.
        pages = ['./' + p.relative_to(root).as_posix() for p in site_files(root)
                 if p.suffix.lower() != '.svg']
        return [['npx', '--yes', '--package=html-validate@9.0.0', '--', 'html-validate',
                 '--config', str(checks / '.htmlvalidate.json'), '--', *pages]]
    if kind == 'authors':
        args = (['--', os.environ['BASE_SHA'] + '..' + os.environ['HEAD_SHA']]
                if os.environ['EVENT_NAME'] == 'pull_request' else
                ['--before', os.environ['BEFORE'], '--after', os.environ['AFTER']])
        return [script('check_authors.py', '--root', str(root), *args)]
    return []


def accessibility(checks, root):
    # Temp files and logs never land in the served candidate tree.
    with tempfile.TemporaryDirectory(dir=os.environ.get('TMPDIR', tempfile.gettempdir())) as temp:
        temp = Path(temp)
        config = json.loads((checks / '.pa11yci.json').read_text())
        config['urls'] = ['http://127.0.0.1:8080/' + quote(p.relative_to(root).as_posix())
                          for p in site_files(root) if p.suffix.lower() != '.svg']
        config_path = temp / 'pa11y.json'
        config_path.write_text(json.dumps(config))
        with (temp / 'server.log').open('w') as log:
            server = subprocess.Popen([sys.executable, '-I', '-B', '-m', 'http.server',
                                       '--bind', '127.0.0.1', '--directory', str(root), '--', '8080'],
                                      stdout=log, stderr=log)
            try:
                for attempt in range(50):
                    if server.poll() is not None:
                        raise RuntimeError('Local server exited')
                    try:
                        with urlopen(config['urls'][0], timeout=1) as response:
                            if response.status == 200:
                                break
                    except OSError:
                        time.sleep(0.1)
                else:
                    raise RuntimeError('Local server did not become ready')
                run(['npx', '--yes', '--package=pa11y-ci@4.0.0', '--', 'pa11y-ci',
                     '--config', str(config_path), '--'], checks)
            finally:
                server.terminate()
                server.wait(timeout=10)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('kind', choices=['html', 'links', 'no-third-party', 'a11y',
                                        'authors', 'privacy-text', 'invariants'])
    parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    checks = Path(__file__).resolve().parents[1]
    errors = discovery_errors(root)
    if not errors:
        for path in site_files(root):
            errors.extend(f'{path.relative_to(root)}: {e}' for e in read_page(path).errors)
    if errors:
        print('\n'.join(errors))
        return 1
    for command in commands(args.kind, checks, root):
        run(command, root)
    if args.kind == 'a11y':
        accessibility(checks, root)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
