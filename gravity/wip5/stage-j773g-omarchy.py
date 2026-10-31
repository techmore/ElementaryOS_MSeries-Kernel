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
p.add_argument('--allow-unprovisioned', action='store_true', help='permit a diagnostic root without a local desktop user')
p.add_argument('--experimental-initramfs', type=pathlib.Path, help='include the recorded untested direct-root bootstrap')
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
# Accept the DTBs recorded alongside this exact graphics kernel build.
# The keyboard variant is an unqualified optional hardware trial.
known_dtbs = {
    'abff43e472901a55798b0c3ad833574d13c6fc52ea07a7cf7499180ba440cbc9',
    '97f2733b7006858c4a095ad7fd78f2f6f89253004ec6f298a63fbf31c7030be2',
}
if hashlib.sha256(a.dtb.read_bytes()).hexdigest() not in known_dtbs:
    p.error('DTB does not match a recorded graphics-kernel candidate')
expected = 'd7503a309985d172374c3ef1045fdab7fb1e4b370118d0f48fbe021221107de7'
if hashlib.sha256(a.image.read_bytes()).hexdigest() != expected:
    p.error('Image does not match the graphics module release')
# The fill tool must receive the recorded unconfigured stage-1 build.
expected_stage1 = '0597951acb4f9c6df2a3113e9e17f9814ab6e12b3cf754815224c4836a466b94'
if hashlib.sha256(a.stage1.read_bytes()).hexdigest() != expected_stage1:
    p.error('stage1 is not the recorded unconfigured J773g build')
# These are unconfigured direct ESP_STAGE2 m1n1 builds with J773g ANS and
# USB2 calibration gates; packed inline-U-Boot candidates are different.
known_direct_stage2 = {
    '1b85c2945fd32b7c007506fb847f7fe8581da053f600fcd413a815f581b1cbdd',
    '9ef4c475badbd2e52a59a2ad5f79c5569237b8b2021bf8f16f9178c392c02b37',
}
if hashlib.sha256(a.stage2.read_bytes()).hexdigest() not in known_direct_stage2:
    p.error('stage2 is not a recorded direct J773g ANS and USB2 build')
if a.experimental_initramfs:
    expected_initramfs = '3193e75261efbf3e60bd4fee0ca02ba55db44ba373f90f8cd561e2bd19b98c85'
    if hashlib.sha256(a.experimental_initramfs.read_bytes()).hexdigest() != expected_initramfs:
        p.error('initramfs is not the recorded direct-root bootstrap')
    if any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_./-' for c in a.root_subvol):
        p.error('root subvolume is unsupported by the experimental bootstrap')
asahi = root_dir / 'usr/lib/modules' / release / 'kernel/drivers/gpu/drm/asahi/asahi.ko'
expected_asahi = 'f027e3050376e1d9da9ce83a4e88b1dc129077394f7a348cc709db203c0638e8'
if not asahi.is_file() or hashlib.sha256(asahi.read_bytes()).hexdigest() != expected_asahi:
    p.error('staged Asahi module does not match the graphics kernel')
# The generic image has no regular user; require evidence of local provisioning.
passwd = root_dir / 'etc/passwd'
if not passwd.is_file() and not a.allow_unprovisioned:
    p.error('staged root is missing /etc/passwd')
has_login_user = False
for line in (passwd.read_text().splitlines() if passwd.is_file() else []):
    fields = line.split(':')
    if len(fields) != 7:
        continue
    try:
        uid = int(fields[2])
    except ValueError:
        continue
    home, shell = fields[5:7]
    if not (fields[0] and 1000 <= uid <= 59999 and home.startswith('/') and
            shell.startswith('/') and pathlib.PurePosixPath(shell).name not in ('false', 'nologin')):
        continue
    try:
        home_path = (root_dir / home.lstrip('/')).resolve(strict=True)
        shell_path = (root_dir / shell.lstrip('/')).resolve(strict=True)
    except (FileNotFoundError, OSError, RuntimeError):
        continue
    if (home_path.is_relative_to(root_dir) and shell_path.is_relative_to(root_dir) and
            home_path.is_dir() and shell_path.is_file()):
        has_login_user = True
        break
if not has_login_user and not a.allow_unprovisioned:
    p.error('staged root needs a provisioned local login user')
a.output.mkdir(parents=True, exist_ok=False)
for source, name in ((a.image, 'Image'), (a.dtb, 't8132-j773g.dtb')):
    shutil.copyfile(source, a.output / name)
initramfs_path = '-'
if a.experimental_initramfs:
    shutil.copyfile(a.experimental_initramfs, a.output / 'initramfs.cpio.gz')
    initramfs_path = a.esp_directory + '/initramfs.cpio.gz'
boot = f'boot={esp};{a.esp_directory}/Image;{a.esp_directory}/t8132-j773g.dtb;{initramfs_path}\n'
args = f'root=PARTUUID={root} rootfstype=btrfs rootflags=subvol={a.root_subvol} rootwait rw console=tty0 loglevel=7'
(a.output / 'stage2.bin').write_bytes(a.stage2.read_bytes() + (boot + f'chosen.bootargs={args}\n').encode())
subprocess.run(['python3', str(a.fill_tool), '--input', str(a.stage1), '--output', str(a.output / 'stage1-configured.bin'), '--esp-partuuid', esp, '--stage2-path', a.esp_directory + '/stage2.bin', '--window-ms', '5000'], check=True)
artifacts = {}
names = ['Image', 't8132-j773g.dtb', 'stage1-configured.bin', 'stage2.bin']
if a.experimental_initramfs:
    names.append('initramfs.cpio.gz')
for name in names:
    data = (a.output / name).read_bytes()
    artifacts[name] = {'bytes': len(data), 'sha1': hashlib.sha1(data).hexdigest(), 'sha256': hashlib.sha256(data).hexdigest()}
limits = ['mount and subvolume checked; login authentication and contents still require verification',
          'storage, display, input, firmware and recovery unverified', 'not a qualified Omarchy installation']
if not has_login_user:
    limits.append('unprovisioned diagnostic root; no local desktop user established')
if a.experimental_initramfs:
    limits.append('experimental initramfs: unauthenticated failure shell; switch_root and recovery unverified')
(a.output / 'manifest.json').write_text(json.dumps({'status': 'uninstalled, unbooted direct-root experiment', 'artifacts': artifacts, 'limits': limits}, indent=2) + '\n')
print(f'Staged experiment in {a.output}; no boot files changed')
