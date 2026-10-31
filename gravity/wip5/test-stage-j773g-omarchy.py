#!/usr/bin/env python3
"""Check direct-root staging rejects unsafe root selection before writing output."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).with_name('stage-j773g-omarchy.py')
RELEASE = '7.2.11-elementary-m4-graphics-draft'

class DirectRootValidation(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=Path.home() / '.cache')
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.root = self.base / 'ordinary-directory'
        (self.root / 'etc').mkdir(parents=True)
        (self.root / 'etc/os-release').write_text('ID=omarchy\n')
        modules = self.root / 'usr/lib/modules' / RELEASE
        modules.mkdir(parents=True)
        (modules / 'modules.dep').write_text('')
        self.bin = self.base / 'bin'
        self.bin.mkdir()
        mount = {'filesystems': [{'target': str(self.base), 'source': '/dev/fake', 'fsroot': '/', 'fstype': 'btrfs'}]}
        findmnt = self.bin / 'findmnt'
        findmnt.write_text('#!/bin/sh\nprintf "%s\\n" ' + repr(json.dumps(mount)) + '\n')
        findmnt.chmod(0o755)
        self.args = ['python3', str(SCRIPT), '--image', str(self.base / 'image'), '--dtb', str(self.base / 'dtb'), '--stage1', str(self.base / 'stage1'), '--stage2', str(self.base / 'stage2'), '--fill-tool', str(self.base / 'fill'), '--output', str(self.base / 'output'), '--root-directory', str(self.root), '--esp-partuuid', '11111111-1111-1111-1111-111111111111', '--root-partuuid', '22222222-2222-2222-2222-222222222222', '--esp-directory', 'draft', '--root-subvol', 'ordinary-directory']

    def run_stage(self):
        env = dict(os.environ, PATH=str(self.bin) + os.pathsep + os.environ['PATH'])
        return subprocess.run(self.args, text=True, capture_output=True, env=env)

    def test_ordinary_directory_rejected(self):
        self.assertNotEqual(self.root.stat().st_ino, 256)
        result = self.run_stage()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('root directory of a Btrfs subvolume', result.stderr)
        self.assertFalse((self.base / 'output').exists())

    def test_rootflags_comma_rejected(self):
        self.args[-1] = 'ordinary-directory,ro'
        result = self.run_stage()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('relative path without delimiters', result.stderr)
        self.assertFalse((self.base / 'output').exists())

if __name__ == '__main__':
    unittest.main()
