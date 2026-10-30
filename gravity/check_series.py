#!/usr/bin/env python3
"""Check the Gravity patch inventory and its recorded content hashes."""
import hashlib
import json
import re
import sys
from pathlib import Path

root = Path(__file__).resolve().parent
try:
    manifest = json.loads((root / 'series.json').read_text())
    patches = manifest['patches']
    if not isinstance(patches, list) or not patches:
        raise ValueError('patches must be a nonempty list')
    names = []
    for number, patch in enumerate(patches, 1):
        name = patch['file']
        if not isinstance(name, str) or not re.fullmatch(rf'{number:04d}-[^/]+\.patch', name):
            raise ValueError(f'patch {number}: invalid or out-of-order filename {name!r}')
        if name in names:
            raise ValueError(f'duplicate patch: {name}')
        names.append(name)
        digest = hashlib.sha256((root / 'patches' / name).read_bytes()).hexdigest()
        if digest != patch['sha256']:
            raise ValueError(f'{name}: SHA-256 mismatch')
    files = {p.name for p in (root / 'patches').glob('*.patch')}
    if files != set(names):
        raise ValueError(f'patch inventory mismatch: unlisted={sorted(files - set(names))}, missing={sorted(set(names) - files)}')
except (OSError, ValueError, KeyError, TypeError) as error:
    print(f'Gravity series validation failed: {error}', file=sys.stderr)
    sys.exit(1)
print(f'Gravity series: {len(names)} patches verified')
