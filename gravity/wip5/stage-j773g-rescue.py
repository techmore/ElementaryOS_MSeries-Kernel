#!/usr/bin/env python3
"""Assemble a local direct-m1n1 rescue draft; never install it.

The stage1 tool comes from the exact pinned m1n1 source. The caller must choose
an ESP UUID and a separate FAT path after reviewing the installed boot chain.
The resulting rescue shell is not an Omarchy installation or a boot guarantee.
"""
import argparse
import hashlib
import json
import pathlib
import shutil
import subprocess
import uuid

parser = argparse.ArgumentParser(description=__doc__)
for option in ('image', 'dtb', 'initramfs', 'stage1', 'stage2', 'fill-tool', 'output'):
    parser.add_argument('--' + option, type=pathlib.Path, required=True)
parser.add_argument('--esp-partuuid', required=True)
parser.add_argument('--esp-directory', required=True, help='relative, separate FAT directory')
parser.add_argument('--serial', action='store_true', help='also request the mini ttySAC0 console')
args = parser.parse_args()
partuuid = str(uuid.UUID(args.esp_partuuid))
directory = args.esp_directory
parts = directory.split('/')
if not parts or any(not p or p in ('.', '..') for p in parts) or any(c in directory for c in ';\\\n\r'):
    parser.error('ESP directory must be a relative FAT path without dot components or delimiters')
if not args.output.resolve().is_relative_to(pathlib.Path.home().resolve()):
    parser.error('stage artifacts in a new directory under your home, not on the ESP')
args.output.mkdir(parents=True, exist_ok=False)
for source, name in [(args.image, 'Image'), (args.dtb, 't8132-j773g.dtb'), (args.initramfs, 'initramfs.cpio.gz')]:
    shutil.copyfile(source, args.output / name)
boot = f'boot={partuuid};{directory}/Image;{directory}/t8132-j773g.dtb;{directory}/initramfs.cpio.gz\n'
console = 'console=tty0 console=ttySAC0' if args.serial else 'console=tty0'
(args.output / 'stage2.bin').write_bytes(args.stage2.read_bytes() + (boot + f'chosen.bootargs={console} loglevel=7\n').encode())
subprocess.run(['python3', str(args.fill_tool), '--input', str(args.stage1), '--output', str(args.output / 'stage1-configured.bin'), '--esp-partuuid', partuuid, '--stage2-path', directory + '/stage2.bin', '--window-ms', '5000'], check=True)
files = ['Image', 't8132-j773g.dtb', 'initramfs.cpio.gz', 'stage2.bin', 'stage1-configured.bin']
artifacts = {}
for name in files:
    data = (args.output / name).read_bytes()
    artifacts[name] = {'bytes': len(data), 'sha1': hashlib.sha1(data).hexdigest(), 'sha256': hashlib.sha256(data).hexdigest()}
manifest = {'status': 'uninstalled, unbooted diagnostic draft', 'artifacts': artifacts,
            'limits': ['not an Omarchy root', 'input and storage unverified', 'automatic Gravity fallback unverified']}
(args.output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
print(f'Staged {len(files)} artifacts in {args.output}; no system boot files changed')
