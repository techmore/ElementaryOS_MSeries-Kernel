#!/usr/bin/env python3
"""Exercise attended staging order with disposable, mocked helper commands."""
import os
import pty
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).with_name('prepare-omarchy-staged-root.sh')
MODULES = Path.home() / '.cache/m4-kernel/latest-aurora/graphics-ethernet-stage/root/usr'
RELEASE = '7.2.11-elementary-m4-graphics-draft'

class PreparationFlow(unittest.TestCase):
    def setUp(self):
        if subprocess.run(['unshare', '-Ur', 'true'], capture_output=True).returncode:
            self.skipTest('unprivileged user namespace unavailable')
        if not (MODULES / 'lib/modules' / RELEASE / 'extra/atlantic.ko').is_file():
            self.skipTest('recorded local module artifacts unavailable')
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.stage = self.base / 'stage'; self.stage.mkdir()
        self.tools = self.base / 'tools'; self.tools.mkdir()
        shutil.copyfile(SCRIPT, self.tools / SCRIPT.name)
        self.log = self.base / 'calls'
        for filename, phase in (('stage-omarchy-root.sh', 'copy'), ('stage-graphics-modules.sh', 'modules'), ('provision-omarchy-user.sh', 'account')):
            p = self.tools / filename
            p.write_text('#!/bin/bash\nprintf "%s\\n" ' + phase + ' >> "$FIXTURE_LOG"\n' +
                         '[ "${FAIL_PHASE:-}" != ' + phase + ' ] || exit 8\n' +
                         ('mkdir "$1/omarchy-root-subvolume"\n' if phase == 'copy' else ''))

    def run_flow(self, fail=''):
        env = dict(os.environ, FIXTURE_LOG=str(self.log), FAIL_PHASE=fail)
        master, slave = pty.openpty()
        try:
            proc = subprocess.Popen(['unshare', '-Ur', 'bash', str(self.tools / SCRIPT.name), str(self.stage), str(MODULES)], stdin=slave, stdout=slave, stderr=slave, env=env)
            os.close(slave); slave = -1
            code = proc.wait(timeout=20)
            output = bytearray()
            while True:
                try: data = os.read(master, 4096)
                except OSError: break
                if not data: break
                output.extend(data)
            return code, output.decode(errors='replace')
        finally:
            if slave >= 0: os.close(slave)
            os.close(master)

    def calls(self):
        return self.log.read_text().splitlines() if self.log.exists() else []

    def test_success_runs_in_order(self):
        code, output = self.run_flow()
        self.assertEqual(code, 0, output)
        self.assertEqual(self.calls(), ['copy', 'modules', 'account'])
        self.assertTrue((self.stage / 'omarchy-root-subvolume').is_dir())

    def test_copy_failure_stops(self):
        code, output = self.run_flow('copy')
        self.assertNotEqual(code, 0)
        self.assertIn('stopped during root copy', output)
        self.assertEqual(self.calls(), ['copy'])

    def test_module_failure_retains_root(self):
        code, output = self.run_flow('modules')
        self.assertNotEqual(code, 0)
        self.assertIn('retained for inspection', output)
        self.assertEqual(self.calls(), ['copy', 'modules'])
        self.assertTrue((self.stage / 'omarchy-root-subvolume').is_dir())

    def test_account_failure_retains_root(self):
        code, output = self.run_flow('account')
        self.assertNotEqual(code, 0)
        self.assertIn('stopped during local account provisioning', output)
        self.assertEqual(self.calls(), ['copy', 'modules', 'account'])
        self.assertTrue((self.stage / 'omarchy-root-subvolume').is_dir())

    def test_existing_target_refused(self):
        (self.stage / 'omarchy-root-subvolume').mkdir()
        code, output = self.run_flow()
        self.assertNotEqual(code, 0)
        self.assertIn('target already exists', output)
        self.assertEqual(self.calls(), [])

if __name__ == '__main__':
    unittest.main()
