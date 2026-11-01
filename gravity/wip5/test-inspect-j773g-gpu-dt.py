#!/usr/bin/env python3
"""Check metadata parsing using a synthetic tree; no hardware access."""
import importlib.util
from pathlib import Path
import struct
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('inspector', Path(__file__).with_name('inspect-j773g-gpu-dt.py'))
inspector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inspector)

class GpuDtInspection(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.put(self.root, 'compatible', b'apple,j773g\0apple,t8132\0')
        self.r = self.root / 'reserved-memory'; self.r.mkdir()
        self.put(self.r, '#address-cells', struct.pack('>I', 2)); self.put(self.r, '#size-cells', struct.pack('>I', 2))
        self.g = self.root / 'soc/gpu@302600000'; self.g.mkdir(parents=True)
        names = ['ttbs', 'pagetables', 'l2', 'handoff', 'firmware']
        self.put(self.g, 'memory-region-names', b''.join(n.encode() + b'\0' for n in names))
        self.put(self.g, 'memory-region', struct.pack('>5I', *range(1, 6)))
        for i, name in enumerate(names, 1):
            node = self.r / name; node.mkdir()
            self.put(node, 'phandle', struct.pack('>I', i)); self.put(node, 'reg', struct.pack('>QQ', i * 0x10000, 0x4000))
        for prop, idx in [('gpu-region', 1), ('gfx-shared-region', 2), ('gfx-shared-l2-region', 3), ('gfx-handoff', 4)]:
            self.put(self.g, 'apple,sgx-' + prop + '-base', struct.pack('<Q', idx * 0x10000))
            self.put(self.g, 'apple,sgx-' + prop + '-size', struct.pack('<Q', 0x4000))
        adt = self.r / 'adt'; adt.mkdir()
        self.put(adt, 'compatible', b'phram\0'); self.put(adt, 'label', b'adt\0'); self.put(adt, 'reg', struct.pack('>QQ', 0x90000, 0x4000))

    @staticmethod
    def put(node, name, value):
        (node / name).write_bytes(value)

    def test_valid_mapping_and_overlap_detection(self):
        result = inspector.inspect(self.root)
        self.assertTrue(all(result['gravity_range_matches'].values()))
        self.assertTrue(result['adt_phram']['disjoint_from_described_gpu_regions'])
        self.put(self.r / 'adt', 'reg', struct.pack('>QQ', 0x10000, 0x4000))
        self.assertFalse(inspector.inspect(self.root)['adt_phram']['disjoint_from_described_gpu_regions'])

    def test_malformed_reference_rejected(self):
        self.put(self.g, 'memory-region', struct.pack('>5I', 1, 2, 3, 4, 99))
        with self.assertRaises(ValueError): inspector.inspect(self.root)

if __name__ == '__main__':
    unittest.main()
