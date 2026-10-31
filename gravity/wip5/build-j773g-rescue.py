#!/usr/bin/env python3
"""Build a non-installing J773g diagnostic initramfs from local ARM64 binaries."""
import argparse, gzip, os, pathlib, re, stat, subprocess
root = pathlib.Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument('--module-root', type=pathlib.Path, help='offline modules_install root for keyboard trial')
parser.add_argument('--release', help='matching kernel release (required with --module-root)')
parser.add_argument('--output', type=pathlib.Path, default=root / 'j773g-rescue.cpio.gz')
args = parser.parse_args()
if bool(args.module_root) != bool(args.release):
    parser.error('--module-root and --release must be supplied together')
programs = ['bash', 'mount', 'ls', 'cat', 'grep', 'dmesg', 'blkid', 'setsid', 'tty', 'find', 'sleep', 'uname']
if args.module_root:
    programs.append('modprobe')
entries = {}
for name in ['dev', 'proc', 'sys', 'tmp', 'run', 'mnt', 'usr', 'usr/bin', 'lib', 'lib64', 'etc']:
    entries[name] = (stat.S_IFDIR | 0o755, b'', 0, 0)
entries['bin'] = (stat.S_IFLNK | 0o777, b'usr/bin', 0, 0)
entries['usr/bin/sh'] = (stat.S_IFLNK | 0o777, b'bash', 0, 0)
entries['dev/console'] = (stat.S_IFCHR | 0o600, b'', 5, 1)
entries['dev/null'] = (stat.S_IFCHR | 0o666, b'', 1, 3)
entries['etc/passwd'] = (stat.S_IFREG | 0o644, b'root:x:0:0:root:/root:/usr/bin/bash\n', 0, 0)
init = r'''#!/usr/bin/bash
export PATH=/usr/bin
export HOME=/
export TERM=linux
mount -t devtmpfs devtmpfs /dev
mount -t proc proc /proc
mount -t sysfs sysfs /sys
mount -t tmpfs tmpfs /tmp
'''
if args.module_root:
    init += r'''
printf 'Loading experimental keyboard drivers...\n'
modprobe -a spmi-apple-controller sn201202x phy-apple-atc dwc3-apple hid-apple || printf 'Module load failed; inspect dmesg.\n'
'''
init += r'''
printf '\nJ773g rescue initramfs: RAM-only shell; disks not mounted.\n'
printf 'Kernel: '; uname -r
printf 'Check: ls /dev; blkid -c /dev/null; dmesg; cat /proc/cmdline\n'
printf 'Console and keyboard availability depend on this kernel and boot chain.\n'
active=''
if [[ -r /sys/class/tty/console/active ]]; then
  IFS= read -r active </sys/class/tty/console/active
fi
if [[ $active == *ttyS* || $active == *ttyAMA* ]]; then
  if [[ -c /dev/tty1 ]]; then
    /usr/bin/setsid -c /usr/bin/bash --noprofile --norc -i </dev/tty1 >/dev/tty1 2>&1 &
  fi
fi
while :; do
  /usr/bin/bash --noprofile --norc -i </dev/console >/dev/console 2>&1
  printf '\nShell exited; restarting.\n' >/dev/console
  sleep 1
done
'''
init = init.encode()
entries['init'] = (stat.S_IFREG | 0o755, init, 0, 0)
for name in programs:
    path = pathlib.Path('/usr/bin') / name
    if not path.is_file(): raise SystemExit(f'missing {path}')
    entries[str(path).lstrip('/')] = (stat.S_IFREG | 0o755, path.read_bytes(), 0, 0)
    out = subprocess.check_output(['ldd', str(path)], text=True)
    if 'not found' in out: raise SystemExit(f'missing library for {path}: {out}')
    for dep in re.findall(r'(?:=>\s*)?(/(?:lib|lib64)/\S+)', out):
        lib = pathlib.Path(dep)
        entries[dep.lstrip('/')] = (stat.S_IFREG | 0o755, lib.read_bytes(), 0, 0)

if args.module_root:
    module_dir = pathlib.Path('lib/modules') / args.release
    source_dir = args.module_root / module_dir
    for name in ('spmi-apple-controller', 'sn201202x', 'phy-apple-atc', 'dwc3-apple', 'hid-apple'):
        output = subprocess.check_output(['modprobe', '-d', str(args.module_root), '-S', args.release,
                                          '--show-depends', name], text=True)
        for line in output.splitlines():
            if line.startswith('insmod '):
                source = pathlib.Path(line.split()[1])
                rel = source.relative_to(args.module_root)
                entries[str(rel)] = (stat.S_IFREG | 0o644, source.read_bytes(), 0, 0)
    for source in source_dir.glob('modules.*'):
        if source.is_file():
            entries[str(source.relative_to(args.module_root))] = (stat.S_IFREG | 0o644, source.read_bytes(), 0, 0)
    for name in list(entries):
        parent = pathlib.PurePosixPath(name).parent
        while str(parent) != '.':
            entries.setdefault(str(parent), (stat.S_IFDIR | 0o755, b'', 0, 0))
            parent = parent.parent

def pad(n): return b'\0' * (-n % 4)
def record(name, mode, data, rmajor, rminor, ino):
    rawname = name.encode() + b'\0'
    fields = [ino, mode, 0, 0, 1, 0, len(data), 0, 0, rmajor, rminor, len(rawname), 0]
    header = b'070701' + b''.join(f'{v:08x}'.encode() for v in fields)
    return header + rawname + pad(len(header) + len(rawname)) + data + pad(len(data))
with open(args.output, 'wb') as output:
    with gzip.GzipFile(filename='', mode='wb', fileobj=output, mtime=0) as archive:
        for i, name in enumerate(sorted(entries), 1):
            mode, data, major, minor = entries[name]
            archive.write(record(name, mode, data, major, minor, i))
        archive.write(record('TRAILER!!!', 0, b'', 0, 0, len(entries) + 1))
print('wrote', args.output, 'with', len(entries), 'entries')
