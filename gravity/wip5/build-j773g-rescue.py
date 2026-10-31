#!/usr/bin/env python3
"""Build a non-installing J773g diagnostic initramfs from local ARM64 binaries."""
import gzip, os, pathlib, re, stat, subprocess
root = pathlib.Path(__file__).resolve().parent
programs = ['bash', 'mount', 'ls', 'cat', 'grep', 'dmesg', 'blkid', 'setsid', 'tty', 'find', 'sleep', 'uname']
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
'''.encode()
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

def pad(n): return b'\0' * (-n % 4)
def record(name, mode, data, rmajor, rminor, ino):
    rawname = name.encode() + b'\0'
    fields = [ino, mode, 0, 0, 1, 0, len(data), 0, 0, rmajor, rminor, len(rawname), 0]
    header = b'070701' + b''.join(f'{v:08x}'.encode() for v in fields)
    return header + rawname + pad(len(header) + len(rawname)) + data + pad(len(data))
with open(root / 'j773g-rescue.cpio.gz', 'wb') as output:
    with gzip.GzipFile(filename='', mode='wb', fileobj=output, mtime=0) as archive:
        for i, name in enumerate(sorted(entries), 1):
            mode, data, major, minor = entries[name]
            archive.write(record(name, mode, data, major, minor, i))
        archive.write(record('TRAILER!!!', 0, b'', 0, 0, len(entries) + 1))
print('wrote', root / 'j773g-rescue.cpio.gz', 'with', len(entries), 'entries')
