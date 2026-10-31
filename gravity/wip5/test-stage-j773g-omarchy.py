#!/usr/bin/env python3
"""Check direct-root staging rejects unsafe root selection before writing output."""
import json
import os
from pathlib import Path
import subprocess
import shutil
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
        (self.root / 'etc/passwd').write_text('sample:x:1000:1000:Sample:/home/sample:/bin/bash\n')
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

    def prepare_recorded_fixture(self):
        cache = Path.home() / '.cache/m4-kernel'
        graphics = cache / 'latest-aurora/graphics/build'
        dtb = graphics / 'arch/arm64/boot/dts/apple/t8132-j773g.dtb'
        image = graphics / 'arch/arm64/boot/Image'
        stage2 = cache / 'wip5-source/m1n1/j773g-loader-draft/stage2-esp-usb2-trial.bin'
        stage1 = cache / 'wip5-source/m1n1/j773g-loader-draft/stage1-release-gpu-handoff.bin'
        asahi = graphics / 'drivers/gpu/drm/asahi/asahi.ko'
        if not all(p.is_file() for p in (dtb, image, stage1, stage2, asahi)):
            self.skipTest('recorded local graphics artifacts unavailable')
        module = self.root / 'usr/lib/modules' / RELEASE / 'kernel/drivers/gpu/drm/asahi/asahi.ko'
        module.parent.mkdir(parents=True)
        shutil.copyfile(asahi, module)
        lsblk = self.bin / 'lsblk'
        lsblk.write_text('#!/bin/sh\nprintf "%s\n" 22222222-2222-2222-2222-222222222222\n')
        lsblk.chmod(0o755)
        site = self.bin / 'sitecustomize.py'
        site.write_text("import os, pathlib\n_original=pathlib.Path.stat\ndef fake(self,*a,**k):\n r=_original(self,*a,**k)\n if str(self)==os.environ.get('TEST_SUBVOL'):\n  v=list(r);v[1]=256;return os.stat_result(v)\n return r\npathlib.Path.stat=fake\n")
        fill = self.base / 'fill.py'
        fill.write_text("import pathlib,sys\np=pathlib.Path(sys.argv[sys.argv.index('--output')+1]);p.write_bytes(b'test-stage1')\n")
        for option, value in (('--image', image), ('--dtb', dtb), ('--stage1', stage1), ('--stage2', stage2), ('--fill-tool', fill)):
            self.args[self.args.index(option)+1] = str(value)
        return module

    def run_recorded_fixture(self):
        env = dict(os.environ, PATH=str(self.bin)+os.pathsep+os.environ['PATH'], PYTHONPATH=str(self.bin), TEST_SUBVOL=str(self.root), PYTHONDONTWRITEBYTECODE='1')
        return subprocess.run(self.args, text=True, capture_output=True, env=env)

    def test_recorded_direct_pair_and_wrong_stage2(self):
        self.prepare_recorded_fixture()
        wrong = self.base / 'wrong-stage2'; wrong.write_bytes(b'not direct stage2')
        stage2_index = self.args.index('--stage2') + 1
        correct = self.args[stage2_index]; self.args[stage2_index] = str(wrong)
        bad = self.run_recorded_fixture()
        self.assertNotEqual(bad.returncode, 0)
        self.assertIn('not a recorded direct J773g', bad.stderr)
        self.assertFalse((self.base / 'output').exists())
        self.args[stage2_index] = correct
        good = self.run_recorded_fixture()
        self.assertEqual(good.returncode, 0, good.stderr)
        self.assertIn(b'root=PARTUUID=', (self.base / 'output/stage2.bin').read_bytes())

    def test_wrong_dtb_rejected(self):
        self.prepare_recorded_fixture()
        wrong = self.base / 'wrong-dtb'; wrong.write_bytes(b'unrelated device tree')
        self.args[self.args.index('--dtb') + 1] = str(wrong)
        result = self.run_recorded_fixture()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('DTB does not match', result.stderr)
        self.assertFalse((self.base / 'output').exists())

    def test_wrong_stage1_rejected(self):
        self.prepare_recorded_fixture()
        wrong = self.base / 'wrong-stage1'; wrong.write_bytes(b'unrelated stage1')
        self.args[self.args.index('--stage1') + 1] = str(wrong)
        result = self.run_recorded_fixture()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('stage1 is not the recorded', result.stderr)
        self.assertFalse((self.base / 'output').exists())

    def test_unprovisioned_root_rejected(self):
        self.prepare_recorded_fixture()
        (self.root / 'etc/passwd').write_text('root:x:0:0:root:/root:/bin/bash\n')
        result = self.run_recorded_fixture()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('needs a provisioned local login user', result.stderr)
        self.assertFalse((self.base / 'output').exists())

    def test_wrong_asahi_rejected(self):
        module = self.prepare_recorded_fixture()
        module.write_bytes(b'wrong module')
        result = self.run_recorded_fixture()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Asahi module does not match', result.stderr)
        self.assertFalse((self.base / 'output').exists())

    def test_rootflags_comma_rejected(self):
        self.args[-1] = 'ordinary-directory,ro'
        result = self.run_stage()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('relative path without delimiters', result.stderr)
        self.assertFalse((self.base / 'output').exists())

if __name__ == '__main__':
    unittest.main()
