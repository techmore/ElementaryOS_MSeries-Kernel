#!/usr/bin/env python3
"""Exercise provisioning refusal paths without touching a real root or password."""
import os
import fcntl
import termios
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
            'stat': '#!/bin/sh\ncase "$2" in %t:%T) printf "5:0\\n";; *) printf "256\\n";; esac\n',
            'chroot': '#!/bin/sh\nprintf "%s\\n" "$*" >> "$FIXTURE_LOG"\ncase "$3" in passwd) exit 1;; group) exit 0;; esac\n[ "$2" = /usr/bin/passwd ] && [ "${FAIL_PASSWD:-0}" = 1 ] && exit 1\nexit 0\n',
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

    def run_bound(self, fail_passwd=False):
        tty = self.root / 'dev/tty'; tty.touch()
        env = dict(os.environ, PATH=str(self.bin) + os.pathsep + os.environ['PATH'], FIXTURE_LOG=str(self.log), FAIL_PASSWD='1' if fail_passwd else '0')
        master, slave = pty.openpty()
        def controlling_tty():
            os.setsid()
            fcntl.ioctl(slave, termios.TIOCSCTTY, 0)
        try:
            cmd = ['unshare', '-Urnm', 'sh', '-c', 'mount --bind /dev/tty "$1/dev/tty" || exit 90; exec bash "$2" "$1"', 'fixture', str(self.root), str(SCRIPT)]
            proc = subprocess.Popen(cmd, stdin=slave, stdout=slave, stderr=slave, env=env, preexec_fn=controlling_tty)
            os.close(slave); slave = -1
            os.write(master, b'sample\n')
            code = proc.wait(timeout=15)
            output = bytearray()
            while True:
                try: data = os.read(master, 4096)
                except OSError: break
                if not data: break
                output.extend(data)
            if code == 90:
                self.skipTest('user namespace cannot bind /dev/tty')
            return code, output.decode(errors='replace')
        finally:
            if slave >= 0: os.close(slave)
            os.close(master)

    def test_mocked_success_with_isolated_tty_bind(self):
        code, output = self.run_bound()
        self.assertEqual(code, 0, output)
        calls = self.log.read_text()
        self.assertIn('/usr/bin/useradd -m -G wheel -s /bin/bash -- sample', calls)
        self.assertIn('/usr/bin/passwd sample', calls)
        policy = self.root / 'etc/sudoers.d/90-omarchy-wheel'
        self.assertEqual(policy.read_text(), '%wheel ALL=(ALL:ALL) ALL\n')
        self.assertEqual(policy.stat().st_mode & 0o777, 0o440)
        self.assertTrue((self.root / 'dev/tty').is_file())

    def test_mocked_password_failure_leaves_no_sudo_policy(self):
        code, output = self.run_bound(fail_passwd=True)
        self.assertNotEqual(code, 0)
        self.assertIn('Password setup failed', output)
        calls = self.log.read_text()
        self.assertIn('/usr/bin/useradd', calls)
        self.assertIn('/usr/bin/passwd', calls)
        self.assertEqual(list((self.root / 'etc/sudoers.d').iterdir()), [])
        self.assertTrue((self.root / 'dev/tty').is_file())

    def test_missing_tty_creation_failure_makes_no_account(self):
        code, _ = self.run_interactive()
        self.assertNotEqual(code, 0)
        self.assertFalse((self.root / 'dev/tty').exists())
        self.assert_no_account_or_policy()

if __name__ == '__main__':
    unittest.main()
