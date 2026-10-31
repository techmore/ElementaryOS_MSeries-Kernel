#!/usr/bin/env python3
"""Assemble an uninstalled GPU inspection loader; no boot files are changed."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import shutil

p = argparse.ArgumentParser(description=__doc__)
for name in ('stage1', 'stage2', 'uboot', 'source-dtb', 'target-dtb', 'image', 'output'):
    p.add_argument('--' + name, type=Path, required=True)
p.add_argument('--usb2-trial', action='store_true', help='explicitly select the untested rear USB2 target DTB')
a = p.parse_args()
expected = {
    'stage1': '78f2977b1545a38dad54b4cf0f27875d422779805102ed2d4bfb33d346eb8db0',
    'stage2': 'c55d8769cc73bce783dc5dec38ec083ae4cd0ad6f93b4180b4667a288ab2e194',
    'uboot': '192255d6aeb196089f8e699ec90543ef15cf13474a0745ad4cc0aec6a9c2ecf9',
    'image': 'd7503a309985d172374c3ef1045fdab7fb1e4b370118d0f48fbe021221107de7',
    'source_dtb': '56a8d2613d1cdecf319607ffd13cafaba46f65d5c0c7709dc56ef50d707898ef',
    'target_dtb': ('963a6adaa8a858fe898f4da1a4f49a33dad0730329e646ec9175d0ceb8b789ec'
                   if a.usb2_trial else '2ba45795b6da0156a3eaef2101f2f45bacc4f77e2992474c59df107b680d5c4d'),
}
for name, want in expected.items():
    if hashlib.sha256(getattr(a, name).read_bytes()).hexdigest() != want:
        p.error(name + ' does not match the recorded build')
if not a.output.resolve().is_relative_to(Path.home().resolve()):
    p.error('output must be a new directory under home')
if a.source_dtb.read_bytes() == a.target_dtb.read_bytes():
    p.error('source and target DTBs must be distinct')
a.output.mkdir(parents=True, exist_ok=False)
for src, name in ((a.stage1, 'stage1-unconfigured.bin'), (a.target_dtb, 'kernel-target.dtb'),
                  (a.image, 'Image')):
    shutil.copyfile(src, a.output / name)
payload = a.stage2.read_bytes() + a.source_dtb.read_bytes() + gzip.compress(a.uboot.read_bytes(), mtime=0)
(a.output / 'stage2-packed.bin').write_bytes(payload)
artifacts = {}
for f in sorted(a.output.iterdir()):
    data = f.read_bytes()
    artifacts[f.name] = {'bytes': len(data), 'sha1': hashlib.sha1(data).hexdigest(),
                         'sha256': hashlib.sha256(data).hexdigest()}
(a.output / 'manifest.json').write_text(json.dumps({
    'status': 'uninstalled and unbooted diagnostic draft; stage1 unconfigured',
    'warning': 'No root, boot command, working display, input or recovery is established.',
    'usb2_trial': a.usb2_trial,
    'artifacts': artifacts,
}, indent=2) + '\n')
print('Staged', a.output, '; no boot files changed')
