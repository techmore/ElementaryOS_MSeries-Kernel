#!/usr/bin/env python3
"""Test candidate staging boundaries with a fake module installer."""
import importlib.util
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('stage_build', Path(__file__).with_name('stage-build.py'))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class StageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source, self.build = self.root / 'source', self.root / 'build'
        self.source.mkdir()
        self.build.mkdir()
        (self.source / 'Makefile').write_text('# fixture\n')
        (self.build / '.config').write_text('fixture\n')
        self.release = '7.1.13-omarchy-m4-r8-ARCH'
        self.receipt = {'commit': module.checks.PIN, 'config_sha256': module.checks.digest(self.build / '.config'),
                        'artifacts': {}}
        for name, path in module.checks.ARTIFACTS.items():
            target = self.build / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(name.encode())
            self.receipt['artifacts'][path] = module.checks.digest(target)

    def install(self, command, check):
        prefix = Path(next(s.split('=', 1)[1] for s in command if s.startswith('INSTALL_MOD_PATH=')))
        root = prefix / 'lib/modules' / self.release / 'kernel'
        for name in ('gpu', 'display', 'ethernet'):
            path = module.checks.ARTIFACTS[name]
            target = root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(self.build / path, target)

    def test_stages_matched_files(self):
        with patch.object(module.checks, 'check', return_value=self.release), \
             patch.object(module.subprocess, 'run', side_effect=self.install):
            module.stage(self.source, self.build, self.receipt, self.root / 'out')
        modules = self.root / 'out/root/usr/lib/modules' / self.release
        self.assertEqual((modules / 'pkgbase').read_text(), 'linux-omarchy-m4\n')
        self.assertEqual((modules / 'vmlinuz').read_bytes(), b'image')
        self.assertEqual((modules / 'dtbs/t8132-j773g.dtb').read_bytes(), b'dtb')
        self.assertFalse((self.root / 'out/INCOMPLETE').exists())

    def test_refuses_existing_output_and_preserves_failure_marker(self):
        with patch.object(module.checks, 'check', return_value=self.release), \
             patch.object(module.subprocess, 'run', side_effect=RuntimeError('failed installer')):
            with self.assertRaises(RuntimeError):
                module.stage(self.source, self.build, self.receipt, self.root / 'out')
        self.assertTrue((self.root / 'out/INCOMPLETE').exists())
        with self.assertRaisesRegex(ValueError, 'new output'):
            module.stage(self.source, self.build, self.receipt, self.root / 'out')


if __name__ == '__main__':
    unittest.main()
