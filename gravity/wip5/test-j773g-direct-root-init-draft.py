#!/usr/bin/env python3
"""Exercise only initramfs argument parsing and sysfs selection; never mount."""
import pathlib
import subprocess
import tempfile
import unittest

SCRIPT = pathlib.Path(__file__).with_name('j773g-direct-root-init-draft.sh')
UUID = '11111111-2222-3333-4444-555555555555'

def shell(script, *args):
    return subprocess.run(['bash', '-c', 'source "$1"; shift; ' + script, 'fixture', str(SCRIPT), *args],
                          text=True, capture_output=True)

class BootArgs(unittest.TestCase):
    def test_valid_and_reject_unsafe(self):
        for cmdline, expected in [
            (f'root=PARTUUID={UUID} rootfstype=btrfs rootflags=subvol=home/omarchy', True),
            (f'root=PARTUUID={UUID} rootflags=subvol=../host', False),
            (f'root=PARTUUID={UUID} rootflags=subvol=x,compress=zstd', False),
            (f'root=PARTUUID={UUID} root=PARTUUID={UUID} rootflags=subvol=x', False),
            ('root=/dev/nvme0n1p6 rootflags=subvol=x', False),
        ]:
            with self.subTest(cmdline=cmdline):
                self.assertEqual(shell('parse_boot_args "$1"', cmdline).returncode == 0, expected)

    def test_select_and_reject_duplicate(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            sys = root / 'sys'; dev = root / 'dev'
            (sys / 'part1').mkdir(parents=True); dev.mkdir()
            (dev / 'nvme0n1p6').touch()
            (sys / 'part1/uevent').write_text(f'DEVNAME=nvme0n1p6\nPARTUUID={UUID}\n')
            code = 'ROOT_UUID="$1"; find_root_device "$2" "$3"'
            found = shell(code, UUID, str(sys), str(dev))
            self.assertEqual(found.returncode, 0)
            self.assertEqual(found.stdout.strip(), str(dev / 'nvme0n1p6'))
            (sys / 'part2').mkdir()
            (sys / 'part2/uevent').write_text(f'DEVNAME=nvme0n1p6\nPARTUUID={UUID}\n')
            self.assertNotEqual(shell(code, UUID, str(sys), str(dev)).returncode, 0)

if __name__ == '__main__':
    unittest.main()
