#!/usr/bin/env python3
"""Write kernel-manifest.json (schema 1) and SHA256SUMS for the packages in --out."""
import argparse
import hashlib
import json
import re
from pathlib import Path

SOURCE_COMMIT = 'ce9f2eba72c061a50b2d790450e90af3439d8c24'  # AsahiLinux/linux, same pin as the build step
SOURCE_SHA256 = '20ce358acffff4b3de86201975cd68c7aaf241ae010ec3cca9422bbe2b7f34aa'


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def package(path):
    m = re.fullmatch(r'(?P<name>[^_]+)_(?P<version>[^_]+)_(?P<arch>[^_.]+)\.deb', path.name)
    if not m:
        raise SystemExit(f'unexpected package file name: {path.name}')
    return {'name': m['name'], 'version': m['version'], 'arch': m['arch'], 'format': 'deb',
            'file': path.name, 'sha256': sha256(path)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True, type=Path)
    ap.add_argument('--channel', required=True)
    ap.add_argument('--commit', required=True)
    ap.add_argument('--tunnel', default='false')
    a = ap.parse_args()
    debs = sorted(a.out.glob('*.deb'))
    pkgs = [package(p) for p in debs]
    kernel = next((p for p in pkgs if p['name'].startswith('linux-image-')), None)
    boot = a.out / 'fairydust-m1n1-boot.bin'
    if kernel is None or not boot.exists():
        raise SystemExit('missing kernel .deb or fairydust-m1n1-boot.bin')
    manifest = {
        'schema': 1,
        'channel': a.channel + ('-dptunnel' if a.tunnel == 'true' else ''),
        'kernel_repo': 'techmore/ElementaryOS_MSeries-Kernel',
        'kernel_repo_commit': a.commit,
        'kernel_release': kernel['name'][len('linux-image-'):],
        'source': {'url': f'https://codeload.github.com/AsahiLinux/linux/tar.gz/{SOURCE_COMMIT}',
                   'commit': SOURCE_COMMIT, 'sha256': SOURCE_SHA256},
        'packages': pkgs,
        'boot': {'m1n1_bootbin': {'file': boot.name, 'sha256': sha256(boot)}},
        'firmware': {'policy': 'never redistributed; installer extracts from macOS'},
        'qualification': {'devices': [], 'evidence': None, 'status': 'candidate'},
        'supersedes': None,
    }
    (a.out / 'kernel-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    lines = [f'{sha256(p)}  {p.name}' for p in sorted(a.out.iterdir())
             if p.is_file() and p.name != 'SHA256SUMS']
    (a.out / 'SHA256SUMS').write_text('\n'.join(lines) + '\n')


if __name__ == '__main__':
    main()
