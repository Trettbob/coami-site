"""Check author AND committer emails without printing email addresses."""
import argparse
import re
import subprocess
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))

from site_common import ROOT

NOREPLY = re.compile(r'[0-9]+\+[A-Za-z0-9-]+@users\.noreply\.github\.com', re.ASCII)


def allowed(email):
    return email == 'noreply@github.com' or NOREPLY.fullmatch(email) is not None


def check(root, revision):
    result = subprocess.run(
        ['git', 'log', '--no-use-mailmap', '-z', '--format=%H%x00%ae%x00%ce', revision, '--'],
        cwd=root, capture_output=True, text=True)
    if result.returncode:
        return ['Cannot read commit range; ensure full history and the base ref are available']
    fields = result.stdout.split('\0')
    if fields[-1] == '':
        fields.pop()
    errors = []
    if len(fields) % 3:
        return ['Cannot parse commit metadata']
    for index in range(0, len(fields), 3):
        commit, author, committer = fields[index:index + 3]
        for role, email in [('author', author), ('committer', committer)]:
            if not allowed(email):
                errors.append(f'{commit}: {role} email is not an approved noreply address')
    return errors


def revision_for_push(before, after):
    if not before or not after:
        raise ValueError('Push checks require both before and after commit IDs')
    return after if re.fullmatch(r'0+', before) else f'{before}..{after}'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('revision', nargs='?', help='Explicit commit range (for example origin/main..HEAD)')
    parser.add_argument('--base', help='PR base branch; checks origin/<base>..HEAD')
    parser.add_argument('--before')
    parser.add_argument('--after')
    parser.add_argument('--root', type=Path, default=ROOT)
    args = parser.parse_args()
    if sum([bool(args.revision), args.base is not None,
            args.before is not None or args.after is not None]) != 1:
        parser.error('Supply one of revision, --base, or --before with --after')
    try:
        revision = (args.revision if args.revision else f'origin/{args.base}..HEAD'
                    if args.base is not None else revision_for_push(args.before, args.after))
    except ValueError as error:
        parser.error(str(error))
    if revision.startswith('-'):
        parser.error('Revision cannot start with a dash')
    errors = check(args.root, revision)
    print('\n'.join(errors) if errors else 'PASS: author and committer noreply addresses')
    return bool(errors)


if __name__ == '__main__':
    raise SystemExit(main())
