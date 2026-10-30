#!/usr/bin/env python3
"""Stage a verified J773g Omarchy build in a new directory; never install."""
import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('check_build', HERE / 'check-build.py')
checks = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checks)
PKGBASE = 'linux-omarchy-m4'


def stage(source, build, receipt, output):
    source, build = source.resolve(strict=True), build.resolve(strict=True)
    output = output.resolve()
    if output.exists() or output.is_relative_to(source) or output.is_relative_to(build):
        raise ValueError('new output outside source and build required')
    if not (source / 'Makefile').is_file():
        raise ValueError('kernel source tree required')
    release = checks.check(build, receipt)
    output.mkdir(parents=True)
    marker = output / 'INCOMPLETE'
    marker.touch()
    root = output / 'root'
    root.mkdir()
    subprocess.run(['make', '-C', str(source), 'O=' + str(build), 'ARCH=arm64',
                    'INSTALL_MOD_PATH=' + str(root / 'usr'), 'modules_install'], check=True)
    modules = root / 'usr/lib/modules' / release
    if not modules.is_dir():
        raise ValueError('module installation did not create expected release directory')
    for link in ('build', 'source'):
        path = modules / link
        if path.is_symlink():
            path.unlink()
        elif path.exists():
            raise ValueError('unexpected non-symlink module build reference: ' + link)
    for name in ('gpu', 'display', 'ethernet'):
        relative = checks.ARTIFACTS[name]
        installed = modules / 'kernel' / relative
        if checks.digest(installed) != receipt['artifacts'][relative]:
            raise ValueError('installed module differs from verified build: ' + name)
    shutil.copyfile(build / checks.ARTIFACTS['image'], modules / 'vmlinuz')
    (modules / 'dtbs').mkdir(exist_ok=True)
    shutil.copyfile(build / checks.ARTIFACTS['dtb'], modules / 'dtbs/t8132-j773g.dtb')
    shutil.copyfile(build / '.config', modules / ('config-' + release))
    (modules / 'pkgbase').write_text(PKGBASE + '\n')
    (output / 'receipt.json').write_text(json.dumps({
        'kernel_release': release, 'pkgbase': PKGBASE,
        'source_commit': receipt['commit'], 'artifacts': receipt['artifacts'],
        'config_sha256': receipt['config_sha256'],
        'scope': 'staged files only; not an Arch package, installation, or hardware qualification',
    }, indent=2) + '\n')
    marker.unlink()
    return release


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('source', 'build', 'receipt', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    release = stage(args.source, args.build, json.loads(args.receipt.read_text()), args.output)
    print(f'{release}: staged only; no package, installation or boot test')


if __name__ == '__main__':
    main()
