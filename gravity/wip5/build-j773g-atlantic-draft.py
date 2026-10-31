#!/usr/bin/env python3
"""Build an uninstalled Atlantic module against the recorded graphics kernel."""
import argparse
import hashlib
from pathlib import Path
import shutil
import subprocess

RELEASE = '7.2.11-elementary-m4-graphics-draft'
EXPECTED = {
    '.config': '709eb97d0118b096afc335ba8daef28a819177bb2c76e0926c59d69f18dbdb99',
    'Module.symvers': '2b6690501e605775ce33adf35958c13b745ee8194da123f5a1f6060d679a77d5',
    'arch/arm64/boot/Image': 'd7503a309985d172374c3ef1045fdab7fb1e4b370118d0f48fbe021221107de7',
}
DRIVER_HASH = '69e76daf557e4aae1973ccd98c78cb1859b6875d347f0ecf89a2e7cfc7f9eb59'

def digest(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def driver_digest(root):
    h = hashlib.sha256()
    for f in sorted(root.rglob('*')):
        if f.is_symlink():
            raise SystemExit(f'Unexpected source symlink: {f}')
        if f.is_file():
            h.update(f.relative_to(root).as_posix().encode() + b'\0')
            h.update(bytes.fromhex(digest(f)))
    return h.hexdigest()

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--kernel-source', type=Path, required=True)
p.add_argument('--kernel-build', type=Path, required=True)
p.add_argument('--output', type=Path, required=True, help='new directory for external module')
p.add_argument('--jobs', type=int, default=2)
a = p.parse_args()
if a.jobs < 1:
    p.error('--jobs must be positive')
source = a.kernel_source.resolve(strict=True)
build = a.kernel_build.resolve(strict=True)
if not (build / 'source').is_symlink() or (build / 'source').resolve(strict=True) != source:
    p.error('Kernel build source symlink does not match --kernel-source')
driver = source / 'drivers/net/ethernet/aquantia/atlantic'
if driver_digest(driver) != DRIVER_HASH:
    p.error('Atlantic source differs from recorded candidate')
for name, expected in EXPECTED.items():
    if digest(build / name) != expected:
        p.error(f'Kernel build {name} differs from recorded candidate')
if (build / 'include/config/kernel.release').read_text().strip() != RELEASE:
    p.error('Kernel release mismatch')
out = a.output.absolute()
shutil.copytree(driver, out, dirs_exist_ok=False)
subprocess.run(['make', '-C', str(source), f'O={build}', 'ARCH=arm64', 'CC=clang',
                'LD=ld', 'HOSTCC=clang', f'-j{a.jobs}', f'M={out}', 'CONFIG_AQTION=m', 'modules'], check=True)
module = out / 'atlantic.ko'
vermagic = subprocess.check_output(['modinfo', '-F', 'vermagic', str(module)], text=True).strip()
aliases = subprocess.check_output(['modinfo', '-F', 'alias', str(module)], text=True).splitlines()
if not vermagic.startswith(RELEASE + ' ') or 'pci:v00001D6Ad000004C0sv*sd*bc*sc*i*' not in aliases:
    raise SystemExit('Module release or AQC113 PCI alias mismatch')
symbols = subprocess.check_output(['nm', '-u', str(module)], text=True).splitlines()
undefined = {line.split()[-1] for line in symbols if line.split()}
exports = {line.split()[1] for line in (build / 'Module.symvers').read_text().splitlines() if len(line.split()) >= 2}
missing = sorted(undefined - exports)
if missing:
    raise SystemExit('Missing kernel exports: ' + ', '.join(missing))
print(f'{module}: sha256={digest(module)}; {len(undefined)} undefined symbols found in kernel exports')
print('Uninstalled draft only; PCIe/DART ownership and hardware operation remain unverified.')
