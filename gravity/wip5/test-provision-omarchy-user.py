#!/usr/bin/env python3
"""Exercise provisioning refusal paths without touching a real root or password."""
import os
import pty
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).with_name('provision-omarchy-user.sh').resolve()

class ProvisionRefusal(unittest.TestCase):
    def setUp(self):
        if subprocess.run(['unshare', '-Ur', 'true'], capture_output=True).returncode:
            self.skipTest('unprivileged user namespace unavailable')
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        base = Path(self.tmp.name)
        self.root = base / 'omarchy-root-subvolume'
        for name in ('etc/sudoers.d', 'usr/bin', 'dev', 'home'):
            (self.root / name).mkdir(parents=True)
        for name in ('os-release', 'passwd', 'shadow', 'group'):
            (self.root / 'etc' / name).write_text('fixture\n')
        (self.root / 'etc/sudoers').write_text('@includedir /etc/sudoers.d\n')
        for name in ('useradd', 'passwd', 'getent', 'sudo', 'visudo', 'bash'):
            p = self.root / 'usr/bin' / name
            p.write_text('#!/bin/sh\nexit 0\n'); p.chmod(0o755)
        self.bin = base / 'bin'; self.bin.mkdir()
        for name, text in {
            'btrfs': '#!/bin/sh\nexit 0\n',
            'stat': '#!/bin/sh\nprintf "256\\n"\n',
            'chroot': '#!/bin/sh\nprintf "%s\\n" "$*" >> "$FIXTURE_LOG"\ncase "$3" in passwd) exit 1;; group) exit 0;; esac\nexit 0\n',
            'mknod': '#!/bin/sh\nexit 1\n',
        }.items():
            p = self.bin / name; p.write_text(text); p.chmod(0o755)
        self.log = base / 'calls'

    def run_interactive(self):
        env = dict(os.environ, PATH=str(self.bin) + os.pathsep + os.environ['PATH'], FIXTURE_LOG=str(self.log))
        master, slave = pty.openpty()
        try:
            proc = subprocess.Popen(['unshare', '-Ur', 'bash', str(SCRIPT), str(self.root)], stdin=slave, stdout=slave, stderr=slave, env=env)
            os.close(slave); slave = -1
            os.write(master, b'sample\n')
            code = proc.wait(timeout=10)
            output = bytearray()
            while True:
                try:
                    data = os.read(master, 4096)
                except OSError:
                    break
                if not data: break
                output.extend(data)
            return code, output.decode(errors='replace')
        finally:
            if slave >= 0: os.close(slave)
            os.close(master)

    def assert_no_account_or_policy(self):
        calls = self.log.read_text() if self.log.exists() else ''
        self.assertNotIn('/usr/bin/useradd', calls)
        self.assertNotIn('/usr/bin/passwd', calls)
        self.assertFalse((self.root / 'etc/sudoers.d/90-omarchy-wheel').exists())
        self.assertEqual(list((self.root / 'etc/sudoers.d').iterdir()), [])

    def test_existing_regular_tty_is_preserved_and_rejected(self):
        tty = self.root / 'dev/tty'; tty.write_text('keep')
        code, out = self.run_interactive()
        self.assertNotEqual(code, 0)
        self.assertIn('not the expected character device', out)
        self.assertEqual(tty.read_text(), 'keep')
        self.assert_no_account_or_policy()

    def test_missing_tty_creation_failure_makes_no_account(self):
        code, _ = self.run_interactive()
        self.assertNotEqual(code, 0)
        self.assertFalse((self.root / 'dev/tty').exists())
        self.assert_no_account_or_policy()

if __name__ == '__main__':
    unittest.main()
