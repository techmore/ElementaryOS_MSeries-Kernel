#!/usr/bin/env python3
"""Exercise artifact matching and rejection boundaries without hardware."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('check_build', Path(__file__).with_name('check-build.py'))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class BuildCheckTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.release = '7.1.13-m4-r8-ARCH'
        version = self.root / 'include/config/kernel.release'
        version.parent.mkdir(parents=True)
        version.write_text(self.release + '\n')
        config = self.root / '.config'
        config.write_text('\n'.join(['CONFIG_ARCH_APPLE=y', 'CONFIG_ARM64_16K_PAGES=y',
                                     'CONFIG_RUST=y', 'CONFIG_DRM_ASAHI_M4=m',
                                     'CONFIG_DRM_APPLE=m']) + '\n')
        self.receipt = {'commit': module.PIN, 'kernel_release': self.release,
                        'config_sha256': module.digest(config), 'artifacts': {}}
        for name, relative in module.ARTIFACTS.items():
            p = self.root / relative
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(name.encode())
            self.receipt['artifacts'][relative] = module.digest(p)

    def commands(self, argv, text):
        if argv[0] == 'fdtget':
            return 'apple,j773g apple,t8132 apple,arm-platform\n'
        return self.release + ' SMP\n'

    def test_matching_build(self):
        with patch.object(module.subprocess, 'check_output', side_effect=self.commands):
            self.assertEqual(module.check(self.root, self.receipt), self.release)

    def test_reject_old_non_arch_release(self):
        (self.root / 'include/config/kernel.release').write_text('7.1.13-elementary-m4-gravity1-r8\n')
        with self.assertRaisesRegex(ValueError, 'must end in -ARCH'):
            module.check(self.root, self.receipt)

    def test_reject_changed_gpu(self):
        (self.root / module.ARTIFACTS['gpu']).write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'artifact hash mismatch: gpu'):
            module.check(self.root, self.receipt)

    def test_reject_wrong_board_or_module(self):
        with patch.object(module.subprocess, 'check_output', return_value='apple,j713 apple,t8132'):
            with self.assertRaisesRegex(ValueError, 'J773g'):
                module.check(self.root, self.receipt)
        def wrong_release(argv, text):
            return 'apple,j773g apple,t8132' if argv[0] == 'fdtget' else 'other-release SMP'
        with patch.object(module.subprocess, 'check_output', side_effect=wrong_release):
            with self.assertRaisesRegex(ValueError, 'module release mismatch'):
                module.check(self.root, self.receipt)


if __name__ == '__main__':
    unittest.main()
