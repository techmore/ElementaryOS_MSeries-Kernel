#!/usr/bin/env python3
"""Reconstruct an uninstalled J773g m1n1 source snapshot."""
import argparse
import hashlib
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ARCHIVE_HASH = '5e853caee70e56ba082f33c1d557fa30d25e92c2c571251b8ff04bbbc356e244'
COMMON = [
    ('0005-m1n1-j773g-ans-handoff.patch', '48af1ad00dff04954a9f13170bd56c7c8bf80ff31426f75028c013f2205998d4'),
    ('0006-m1n1-no-display-build-option.patch', '3b22cb16755e47193bced112a2ca59821484763ef760b2404e562c95fa7da86c'),
    ('0010-m1n1-j773g-gpu-resource-draft.patch', '41058bfc5115e88321c955b90406f60f8f94cad0a2297f64bb5d6ad27fdeb836'),
]
PMP = ('0014-m1n1-j773g-pmp-inspection.patch', '19d4e1bdc1aa09ccf8e34eb9d0c2de798bc7135f54f2bd70981f33e40d0a75ea')
USB2 = ('0018-m1n1-usb2-calibration-gate.patch', '3db2f59c5e5f0301f0ce4192ece7088845d6bfebcb7bb163ec6ee9c0263b6770')
INLINE = ('0019-m1n1-j773g-inline-nvme.patch', '9f7057dec8c7436272f5b9b32f2123bf33b2688528272b8330c2ad58c1fcbe0f')

def verify(path, expected):
    with path.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    if digest != expected:
        raise SystemExit(f'SHA-256 mismatch: {path}')

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--archive', required=True, type=Path)
parser.add_argument('--output', required=True, type=Path, help='new source directory')
parser.add_argument('--profile', choices=('diagnostic', 'direct-stage2', 'direct-stage2-inline'),
                    default='diagnostic', help='recorded patch series (default: diagnostic)')
args = parser.parse_args()
patches = COMMON + ([PMP] if args.profile == 'diagnostic' else []) + [USB2]
if args.profile == 'direct-stage2-inline':
    patches += [INLINE]
verify(args.archive, ARCHIVE_HASH)
for name, digest in patches:
    verify(HERE / name, digest)
args.output.mkdir(parents=True, exist_ok=False)
subprocess.run(['tar', '-xzf', str(args.archive.resolve()), '--strip-components=1', '-C', str(args.output.resolve())], check=True)
for name, _ in patches:
    print('Applying', name, flush=True)
    subprocess.run(['git', 'apply', '--unidiff-zero', str(HERE / name)], cwd=args.output.resolve(), check=True)
print(f'Replayed {args.profile} source only; no loader was installed or booted.')
