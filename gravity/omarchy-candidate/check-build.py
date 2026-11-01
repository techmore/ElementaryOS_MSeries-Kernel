#!/usr/bin/env python3
"""Validate build artifacts for a J773g Omarchy candidate; never install."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

PIN = '4fc326f6c25ccceb7515e2635c22e01fde5d3bac'
TIMEOUT_PATCH = '0011-m4-notification-timeout-rescue.patch'
TIMEOUT_SHA = '41b429c9a837a40586df02389432eade495f67201c1081b053bd0e42e1adeda2'
ARTIFACTS = {
    'image': 'arch/arm64/boot/Image',
    'dtb': 'arch/arm64/boot/dts/apple/t8132-j773g.dtb',
    'gpu': 'drivers/gpu/drm/asahi/asahi_m4.ko',
    'display': 'drivers/gpu/drm/apple/appledrm.ko',
    'ethernet': 'drivers/net/ethernet/aquantia/atlantic/atlantic.ko',
}


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def check(build, receipt):
    if receipt.get('commit') != PIN:
        raise ValueError('Gravity source pin mismatch')
    if receipt.get('compatibility_patches', {}).get(TIMEOUT_PATCH) != TIMEOUT_SHA:
        raise ValueError('R8 timeout-rescue patch receipt required')
    release = (build / 'include/config/kernel.release').read_text().strip()
    if not re.fullmatch(r'[A-Za-z0-9.+_-]+-ARCH', release):
        raise ValueError('Omarchy candidate release must end in -ARCH')
    if receipt.get('kernel_release') != release:
        raise ValueError('kernel release does not match receipt')
    config = build / '.config'
    if digest(config) != receipt.get('config_sha256'):
        raise ValueError('kernel config does not match receipt')
    settings = set(config.read_text().splitlines())
    if not {'CONFIG_ARCH_APPLE=y', 'CONFIG_ARM64_16K_PAGES=y',
            'CONFIG_RUST=y', 'CONFIG_DRM_ASAHI_M4=m',
            'CONFIG_DRM_APPLE=m'} <= settings:
        raise ValueError('required J773g kernel configuration missing')
    hashes = receipt.get('artifacts', {})
    for name, relative in ARTIFACTS.items():
        path = build / relative
        if not re.fullmatch(r'[0-9a-f]{64}', hashes.get(relative, '')):
            raise ValueError('missing recorded artifact hash: ' + name)
        if digest(path) != hashes[relative]:
            raise ValueError('artifact hash mismatch: ' + name)
    compatible = subprocess.check_output(
        ['fdtget', '-t', 's', str(build / ARTIFACTS['dtb']), '/', 'compatible'], text=True).split()
    if 'apple,j773g' not in compatible or 'apple,t8132' not in compatible:
        raise ValueError('J773g T8132 device tree required')
    for name in ('gpu', 'display', 'ethernet'):
        value = subprocess.check_output(
            ['modinfo', '-F', 'vermagic', str(build / ARTIFACTS[name])], text=True).split()
        if not value or value[0] != release:
            raise ValueError('module release mismatch: ' + name)
    return release


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, required=True)
    parser.add_argument('--receipt', type=Path, required=True)
    args = parser.parse_args()
    release = check(args.build, json.loads(args.receipt.read_text()))
    print(f'{release}: artifact preflight passed; no package or hardware qualification')


if __name__ == '__main__':
    main()
