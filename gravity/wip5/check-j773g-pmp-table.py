#!/usr/bin/env python3
"""Check a captured PMP soc-device table against Air's retained-bridge guards.

Read a binary table file (for example the disabled node's sysfs property).
Print only sizes, hashes and match results; never print the captured bytes.
A match is not proof of J773g power ownership, command behavior or safety.
"""
import argparse
import hashlib
import pathlib
import struct

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('table', type=pathlib.Path)
a = parser.parse_args()
b = a.table.read_bytes()
expected_size = 34 * 0x7c
shape = len(b) == expected_size
disp = shape and struct.unpack_from('<I', b, 15 * 0x7c)[0] == 8 and b[15 * 0x7c + 0x74:15 * 0x7c + 0x7c] == b'DISP\0\0\0\0'
expected = {0: 5, 4: 0x4746585f, 8: 3, 0xc: 2, 0x1c: 2, 0x2c: 2}
agx = shape and all(struct.unpack_from('<I', b, 12 * 0x7c + off)[0] == expected.get(off, 0) for off in range(0, 0x74, 4)) and b[12 * 0x7c + 0x74:12 * 0x7c + 0x7c] == b'AGX\0\0\0\0\0'
print(f'bytes={len(b)} sha1={hashlib.sha1(b).hexdigest()} sha256={hashlib.sha256(b).hexdigest()}')
print(f'j713_table_shape={shape} j713_disp_identity={disp} j713_agx_identity={agx}')
print('These checks do not establish J773g power or firmware compatibility.')
