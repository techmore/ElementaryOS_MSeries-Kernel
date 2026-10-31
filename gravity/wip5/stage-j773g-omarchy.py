#!/usr/bin/env python3
"""Stage an uninstalled direct-root J773g experiment; never modify boot files."""
import argparse
import hashlib
import json
import pathlib
import shutil
import subprocess
import uuid

p = argparse.ArgumentParser(description=__doc__)
for option in ('image', 'dtb', 'stage1', 'stage2', 'fill-tool', 'output', 'root-directory'):
    p.add_argument('--' + option, type=pathlib.Path, required=True)
for option in ('esp-partuuid', 'root-partuuid', 'esp-directory', 'root-subvol'):
    p.add_argument('--' + option, required=True)
a = p.parse_args()
esp = str(uuid.UUID(a.esp_partuuid))
root = str(uuid.UUID(a.root_partuuid))
for name in ('esp_directory', 'root_subvol'):
    value = getattr(a, name)
    if any(not part or part in ('.', '..') for part in value.split('/')) or any(c in value for c in ';,\\\n\r \t'):
        p.error(name + ' must be a relative path without delimiters or dot components')
if not a.output.resolve().is_relative_to(pathlib.Path.home().resolve()):
    p.error('output must be a new directory under home')
release = '7.2.11-elementary-m4-graphics-draft'
if not (a.root_directory / 'etc/os-release').is_file() or not (a.root_directory / 'usr/lib/modules' / release / 'modules.dep').is_file():
    p.error('staged root or matching modules are missing')
root_dir = a.root_directory.resolve(strict=True)
mounts = json.loads(subprocess.check_output(
    ['findmnt', '-J', '-T', str(root_dir), '-o', 'TARGET,SOURCE,FSROOT,FSTYPE'], text=True))
mount = mounts['filesystems'][0]
if mount['fstype'] != 'btrfs':
    p.error('staged root must be on a mounted Btrfs filesystem')
# Btrfs assigns inode 256 to the root directory of each subvolume.
if root_dir.stat().st_ino != 256:
    p.error('staged root must be the root directory of a Btrfs subvolume')
mountpoint = pathlib.Path(mount['target']).resolve(strict=True)
try:
    relative = root_dir.relative_to(mountpoint)
except ValueError:
    p.error('staged root is outside its reported mountpoint')
subvol = (pathlib.PurePosixPath(mount['fsroot']) / relative.as_posix()).as_posix().lstrip('/')
if subvol != a.root_subvol:
    p.error('root subvolume does not match the staged root path and mount FSROOT')
device = mount['source'].split('[', 1)[0]
actual_partuuid = subprocess.check_output(['lsblk', '-dn', '-o', 'PARTUUID', device], text=True).strip()
if not actual_partuuid or str(uuid.UUID(actual_partuuid)) != root:
    p.error('root PARTUUID does not match the staged root device')
expected = 'd7503a309985d172374c3ef1045fdab7fb1e4b370118d0f48fbe021221107de7'
if hashlib.sha256(a.image.read_bytes()).hexdigest() != expected:
    p.error('Image does not match the graphics module release')
a.output.mkdir(parents=True, exist_ok=False)
for source, name in ((a.image, 'Image'), (a.dtb, 't8132-j773g.dtb')):
    shutil.copyfile(source, a.output / name)
boot = f'boot={esp};{a.esp_directory}/Image;{a.esp_directory}/t8132-j773g.dtb;-\n'
args = f'root=PARTUUID={root} rootfstype=btrfs rootflags=subvol={a.root_subvol} rootwait rw console=tty0 loglevel=7'
(a.output / 'stage2.bin').write_bytes(a.stage2.read_bytes() + (boot + f'chosen.bootargs={args}\n').encode())
subprocess.run(['python3', str(a.fill_tool), '--input', str(a.stage1), '--output', str(a.output / 'stage1-configured.bin'), '--esp-partuuid', esp, '--stage2-path', a.esp_directory + '/stage2.bin', '--window-ms', '5000'], check=True)
artifacts = {}
for name in ('Image', 't8132-j773g.dtb', 'stage1-configured.bin', 'stage2.bin'):
    data = (a.output / name).read_bytes()
    artifacts[name] = {'bytes': len(data), 'sha1': hashlib.sha1(data).hexdigest(), 'sha256': hashlib.sha256(data).hexdigest()}
(a.output / 'manifest.json').write_text(json.dumps({'status': 'uninstalled, unbooted direct-root experiment', 'artifacts': artifacts, 'limits': ['mount mapping and subvolume root checked; contents still require verification', 'storage, display, input, firmware and recovery unverified', 'not a qualified Omarchy installation']}, indent=2) + '\n')
print(f'Staged experiment in {a.output}; no boot files changed')
