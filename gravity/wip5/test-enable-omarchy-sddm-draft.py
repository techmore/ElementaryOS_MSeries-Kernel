#!/usr/bin/env python3
"""Exercise offline SDDM opt-in and refusal without touching the live root."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).with_name('enable-omarchy-sddm-draft.sh').resolve()


class EnableSddm(unittest.TestCase):
    def setUp(self):
        if subprocess.run(['unshare', '-Ur', 'true'], capture_output=True).returncode:
            self.skipTest('unprivileged user namespace unavailable')
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        base = Path(self.tmp.name)
        self.root = base / 'omarchy-root-subvolume'
        for name in ('etc/systemd/system', 'etc/sddm.conf.d', 'usr/bin',
                     'usr/lib/systemd/system', 'usr/share/sddm'):
            (self.root / name).mkdir(parents=True, exist_ok=True)
        for name in ('etc/os-release', 'etc/sddm.conf.d/10-wayland.conf',
                     'usr/lib/systemd/system/sddm.service', 'usr/share/sddm/hyprland.lua'):
            (self.root / name).write_text('fixture\n')
        for name in ('sddm', 'start-hyprland'):
            path = self.root / 'usr/bin' / name
            path.write_text('#!/bin/sh\nexit 0\n')
            path.chmod(0o755)
        self.bin = base / 'bin'
        self.bin.mkdir()
        for name, script in {'btrfs': 'exit 0', 'stat': 'echo 256'}.items():
            path = self.bin / name
            path.write_text('#!/bin/sh\n' + script + '\n')
            path.chmod(0o755)
        self.link = self.root / 'etc/systemd/system/display-manager.service'

    def run_script(self, opt_in=True):
        env = dict(os.environ, PATH=str(self.bin) + os.pathsep + os.environ['PATH'])
        args = ['unshare', '-Ur', 'bash', str(SCRIPT), str(self.root)]
        if opt_in:
            args.append('--enable-sddm')
        return subprocess.run(args, env=env, capture_output=True, text=True)

    def test_opt_in_adds_only_display_manager_link(self):
        result = self.run_script()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(os.readlink(self.link), '/usr/lib/systemd/system/sddm.service')
        self.assertIn('not GPU enablement', result.stdout)

    def test_existing_display_manager_is_not_replaced(self):
        self.link.symlink_to('/some/other/manager')
        self.assertNotEqual(self.run_script().returncode, 0)
        self.assertEqual(os.readlink(self.link), '/some/other/manager')

    def test_explicit_opt_in_and_staged_program_are_required(self):
        self.assertNotEqual(self.run_script(opt_in=False).returncode, 0)
        (self.root / 'usr/bin/sddm').unlink()
        self.assertNotEqual(self.run_script().returncode, 0)
        self.assertFalse(self.link.exists())


if __name__ == '__main__':
    unittest.main()
