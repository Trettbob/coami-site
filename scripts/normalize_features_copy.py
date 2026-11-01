"""Extract the cleared publication block and apply only its display formatting."""
import json
from pathlib import Path
import re
import sys


def extract(source):
    publication = source.split('\n---\n')[1]
    approved = {}
    section = None
    metadata = {'Heading': 'heading', 'Subheading': 'subheading',
                'Disclaimer (directly under the subheading)': 'disclaimer'}
    pending = None
    for line in publication.splitlines():
        if not line:
            continue
        if line.startswith('## '):
            heading = line[3:]
            if heading in metadata:
                pending = metadata[heading]
            else:
                assert re.match(r'^Section \d+: ', heading), heading
                section = {'heading': re.sub(r'^Section \d+: ', '', heading), 'items': []}
                approved.setdefault('sections', []).append(section)
        elif line.startswith('- '):
            match = re.fullmatch(r'- \*\*(.*?)\*\* (.*?) \*(.*?)\*', line)
            assert match and section is not None, line
            title, sentence, status = match.groups()
            section['items'].append([title.removesuffix('.'), sentence, status.removesuffix('.')])
        else:
            assert pending is not None, line
            approved[pending] = line
            pending = None
    return approved


if __name__ == '__main__':
    source, destination = map(Path, sys.argv[1:])
    destination.write_text(json.dumps(extract(source.read_text(encoding='utf-8')),
                                     ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
