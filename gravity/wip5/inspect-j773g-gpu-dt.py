#!/usr/bin/env python3
"""Inspect J773g GPU handoff metadata; do not access physical memory or MMIO."""
import argparse
import json
from pathlib import Path
import struct


def data(node, prop):
    p = node / prop
    return p.read_bytes() if p.is_file() else None


def cells(raw):
    if raw is None or len(raw) % 4:
        raise ValueError('missing or malformed 32-bit cell array')
    return struct.unpack('>' + 'I' * (len(raw) // 4), raw)


def strings(raw):
    if raw is None or not raw.endswith(b'\0'):
        raise ValueError('missing or malformed string list')
    return [s.decode('ascii') for s in raw[:-1].split(b'\0')]


def region(node):
    c = cells(data(node, 'reg'))
    if len(c) != 4:
        raise ValueError('expected one 64-bit-address/64-bit-size range')
    start, size = (c[0] << 32) | c[1], (c[2] << 32) | c[3]
    if not size or start + size > 1 << 64:
        raise ValueError('empty or overflowing range')
    return start, size


def inspect(root):
    if 'apple,j773g' not in strings(data(root, 'compatible')):
        raise ValueError('device tree is not J773g')
    reserved, gpu = root / 'reserved-memory', root / 'soc/gpu@302600000'
    if cells(data(reserved, '#address-cells')) != (2,) or cells(data(reserved, '#size-cells')) != (2,):
        raise ValueError('unexpected reserved-memory cell layout')
    phandles = {}
    for node in reserved.iterdir():
        if not node.is_dir():
            continue
        p = data(node, 'phandle')
        if p is not None:
            (handle,) = cells(p)
            if not handle or handle in phandles:
                raise ValueError('invalid or duplicate reserved-memory phandle')
            phandles[handle] = node
    names = strings(data(gpu, 'memory-region-names'))
    handles = cells(data(gpu, 'memory-region'))
    if len(names) != len(handles) or len(names) != len(set(names)):
        raise ValueError('GPU region names and references differ')
    refs = {}
    for name, handle in zip(names, handles):
        if handle not in phandles:
            raise ValueError('GPU region points outside reserved-memory')
        refs[name] = phandles[handle]
    checks = {}
    for prop, region_name in (('gpu-region', 'ttbs'), ('gfx-shared-region', 'pagetables'),
                              ('gfx-handoff', 'handoff'), ('gfx-shared-l2-region', 'l2')):
        base = data(gpu, 'apple,sgx-' + prop + '-base')
        size = data(gpu, 'apple,sgx-' + prop + '-size')
        checks[prop] = (len(base or b'') == 8 and len(size or b'') == 8 and region_name in refs and
                        (int.from_bytes(base, 'little'), int.from_bytes(size, 'little')) == region(refs[region_name]))
    phram = [n for n in reserved.iterdir() if n.is_dir() and data(n, 'compatible') == b'phram\0' and data(n, 'label') == b'adt\0']
    adt = {'count': len(phram)}
    if len(phram) == 1:
        start, size = region(phram[0]); end = start + size
        others = [region(n) for n in refs.values()]
        adt.update({'nonzero_base': start != 0, 'aligned_16k': not ((start | size) & 0x3fff), 'size_within_2m': size <= 0x200000,
                    'enabled': data(phram[0], 'status') in (None, b'okay\0', b'ok\0'),
                    'not_reusable_or_no_map': data(phram[0], 'reusable') is None and data(phram[0], 'no-map') is None,
                    'disjoint_from_described_gpu_regions': all(end <= b or start >= b + n for b, n in others)})
    draft_names = ['ttbs', 'pagetables', 'handoff', 'shared-l2', 'fw-text', 'fw-data']
    return {'machine': 'apple,j773g', 'gpu_status': strings(data(gpu, 'status')) if data(gpu, 'status') else ['implicit okay'],
            'gpu_region_names': names,
            'gpu_region_flags': {name: {'no_map': data(node, 'no-map') is not None,
                                        'reusable': data(node, 'reusable') is not None,
                                        'enabled': data(node, 'status') in (None, b'okay\0', b'ok\0')}
                                 for name, node in refs.items()},
            'gravity_range_matches': checks, 'adt_phram': adt,
            'draft_six_region_names_match': names == draft_names,
            'draft_version_present': data(gpu, 'apple,g16-handoff-version') is not None,
            'draft_segment_metadata_present': all(data(gpu, x) is not None for x in ('apple,firmware-segment-vas', 'apple,firmware-segment-flags')),
            'qualification': 'metadata only; firmware identity, physical ownership, power and runtime are not validated'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tree', type=Path, default=Path('/sys/firmware/devicetree/base'))
    args = parser.parse_args()
    try:
        print(json.dumps(inspect(args.tree), indent=2))
    except (OSError, ValueError, UnicodeError, struct.error) as exc:
        parser.exit(1, f'Cannot inspect GPU metadata: {exc}\n')


if __name__ == '__main__':
    main()
