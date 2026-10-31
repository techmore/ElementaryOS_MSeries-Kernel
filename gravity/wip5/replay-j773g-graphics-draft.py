#!/usr/bin/env python3
"""Replay the recorded unbooted J773g graphics source into a new directory."""
import argparse
import hashlib
import pathlib
import shutil
import subprocess

HERE = pathlib.Path(__file__).resolve().parent
ARCHIVE_SHA256 = 'fdeb48ce693199f18c435b17567e80ec8dccd53bd826b531c1260ea2200ee16f'
CONFIG_SHA256 = '709eb97d0118b096afc335ba8daef28a819177bb2c76e0926c59d69f18dbdb99'
LOCAL_BEFORE = [
    ('0001-j773g-smc-forward-port.patch', '3e8b6afa3c9c9cbf25719bf3e0a7d3ee21361850e37ba15a436e62c11c2666fd'),
    ('0002-t8132-nvme-explicit-flush.patch', '071e10622373e9ec28bccf5665554b187bc42dcbf66d02a6225427eb102304cd'),
    ('0003-nvme-allow-adt-handoff-resource-order.patch', 'd9b99dd9f8522cf03816ea41287c6578eb49e73594b5523c66c2f4fed214af2b'),
    ('0004-j773g-nvme-adt-placeholders.patch', '9bfae9ce1b72c4e301ecc10914e193fb5e0712f447cc09f2300e7e538e522252'),
    ('usb-0001-j773g-rear-draft.patch', 'b5580ff924f967601b615a8da41e990136bf3a14ee90f8cf8fc42fcd753eb4d1'),
    ('air-forward-combined-snapshot-draft.patch', '0f9cd40c484d5ad6e883bc77739a0d387329615d0de377045517cf8735467818'),
]
HUB = [
    ('0001-drm-apple-srgb-external-display-colour.patch', '6dc8aadcdc0c7c39710d3b9164c388f11b0b2fa111b73e8e14a63bb759ba8fe1'),
    ('0002-drm-apple-free-dp-tunnel-route-from-silent-dcpext.patch', 'fdd6f9cd13ca90b4500130d289182eb69728e25afe5a5ed3f0c92571aa54fd1a'),
    ('0003-drm-apple-dcp-let-a-typec-port-with-hpd-take-over-a-held-pipeline.patch', '2273d0ee008bafc702358bfc553ecfdd8cd9ea8d665c4ce5fb2b3b36af4f9111'),
    ('0004-drm-apple-dcp-route-a-dp-alt-port-only-once-its-sink-asserts-hpd.patch', '111a8d0d4edca05367301e8e1afc3a487bf1638b015073ea81ae64cd1d4817ec'),
    ('0005-usb-typec-tipd-treat-enospc-as-a-taken-display-on-every-soc.patch', 'f6c63701d3197204abd1f3c3bd9fb9c44a0a7156afdd63cba2feb04c5522c037'),
]
LOCAL_AFTER = [
    ('graphics-0003-latest-platform-prerequisites.patch', '45d4938bb633846ff99cb3f2c71a5721fa26a50cdaf87bc81443ba5c12dacab4'),
    ('graphics-0001-pr367-partial-shared-gpu.patch', '94d87429e889e40cf44eb5336b551e1a51468dc32b36f5c3c86da09ca65b131b'),
    ('graphics-0002-g16-exploratory.patch', '462453ab25abdb60ae23639585cbeec82c51f55da8fdf3ca81505f19911a96ce'),
    ('graphics-0004-latest-debug-stats-fix.patch', 'eed7371c5c41fb63abe04949f42e8b5286e39bccf7bb27f6ba29e0c8ff3cf4d7'),
    ('0011-j773g-gpu-dt-draft.patch', '0097b12549ae2857170902b47eee4e757a1dd739389fa763aae70d96752f8682'),
    ('0013-j773g-latest-import-marker.patch', '9090aae56d16823629715a916246b4c38d249d81699275f6994df23649d177f6'),
]

def verify(path, expected):
    with path.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    if digest != expected:
        raise SystemExit(f'SHA-256 mismatch: {path}')

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--archive', type=pathlib.Path, required=True, help='pinned omacom 2dd4aab source archive')
p.add_argument('--hub', type=pathlib.Path, required=True, help='ElementaryOS_MSeries checkout')
p.add_argument('--output', type=pathlib.Path, required=True, help='new, empty-to-be-created output directory')
a = p.parse_args()
config = HERE / 'j773g-graphics-draft.config'
patches = [(HERE / name, digest) for name, digest in LOCAL_BEFORE]
patches += [(a.hub / 'mseries/aurora/unified72/patches' / name, digest) for name, digest in HUB]
patches += [(HERE / name, digest) for name, digest in LOCAL_AFTER]
verify(a.archive, ARCHIVE_SHA256)
verify(config, CONFIG_SHA256)
for path, digest in patches:
    verify(path, digest)
a.output.mkdir(parents=True, exist_ok=False)
source = a.output / 'source'
source.mkdir()
subprocess.run(['tar', '-xzf', str(a.archive.resolve()), '--strip-components=1', '-C', str(source)], check=True)
for patch, _ in patches:
    print('Applying', patch.name, flush=True)
    subprocess.run(['git', 'apply', '--unidiff-zero', str(patch.resolve())], cwd=source, check=True)
shutil.copyfile(config, a.output / 'recorded.config')
print('Source replayed and exact recorded config copied; no build or hardware boot was performed.')
