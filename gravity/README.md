# Gravity M4 series (Mac mini J773g)

65 commits (0001-0065) from `GravityLinux/linux` branch `gravity-m4` (commit `4fc326f6`, 2026-10-09): the M4 / T8132 work that
Gravity Linux's image boots on the M4 Mac mini. They are exported oldest-first in `patches/`; `series.json` lists each
with its SHA-256 and upstream commit, like `aurora/enhancements/series.json`.

## Our patches

`0066` is ours, not Gravity's (`"local": true` in `series.json`). It stops the M4 GPU
driver from failing the GPU when a firmware notification is late. It runs on our M4
Mac mini as an out-of-tree module. See `GPU-HANG-2026-10-28.md`, and `m4-module/` for
the build and install scripts.

## Not boot-tested here

Nothing in this directory has been built or booted by this project. Gravity's own installer image is the known route.

## Overlap with Aurora

Replayed onto `aurora-silicon/linux` `m4/j713-t8132-integ-20261023`, 12 of the 65 apply cleanly and 53 conflict
(`applies_cleanly_to_aurora_m4` in `series.json`). The conflicts are the M4 GPU driver (`drm/asahi`), DCP and HDMI
audio, the T8132 device-tree base, NVMe and the dockchannel HID series: Aurora and Gravity implement the same M4
hardware differently. Do not apply this series on top of an Aurora tree without resolving those by hand.
A full merge of the two histories conflicts in 80 files, most because Gravity's base predates Aurora's by about
54,000 commits.

## Use

Apply to the tree at the base above, or use Gravity's `gravity-m4` branch directly. The OS repo consumes kernels by
pinned version and checksum (`MANIFEST-SCHEMA.md`); this series is not yet a release.

License: Linux kernel code (GPL-2.0). GitHub shows no license for the Gravity fork; the files keep their SPDX headers.
