# Omarchy ARM root staging

On 2026-10-30 the official [Omarchy 4.5.0-rc2 ARM release](https://github.com/omacom/omarchy/releases/tag/v4.5.0-rc2) was staged under `~/.cache/m4-omarchy-root-staging/`, without mounting or changing partitions. The downloaded ISO matched the release SHA-256 `ee885285d6cba0dfc9a9ead22cf5bcc203b9f460970721b3c0b8a1dca4c867a8` and its embedded compressed root matched `dfe0ca883c2a3c62436306fcca42661e683c2bfe9f11334ad98ccc9650af9168`. The decompressed Btrfs image is 6,502,219,776 bytes; SHA-1 `2dbd79b41ff8fd815b2e9b12ba1f656cb92b8288`, SHA-256 `4b66dcfb84cc725e8bc11f27f3ecd452608e4753d13b3abfdab7124dbdb99b4e`.

A full read-only `btrfs check --check-data-csum` found no errors. An unprivileged `btrfs restore` preview of `/etc/os-release` failed because btrfs-progs 7.1 mishandles an inline zstd frame; independent decoding of the full frame succeeded and produced the expected file. The behavior matches [btrfs-progs issue #1171](https://github.com/kdave/btrfs-progs/issues/1171). The failed preview was discarded and the verified source image remains intact. The generic ARM release-candidate root is not yet a bootable J773g system: it needs matched kernel, modules, DTB, firmware, provisioning, storage and input support, and a reviewed boot chain. Check duplicate filesystem UUID handling before any attachment; do not use the raw image as an installed root without resolving that and preparing its mini-specific configuration.

A private corrected `btrfs restore` build now restores the actual
`/etc/os-release` successfully and rejects truncated, short and oversized zstd
frames in host checks. The [btrfs-progs issue #1171](https://github.com/kdave/btrfs-progs/issues/1171)
fix draft is saved locally as `btrfs-restore-inline-zstd.patch`, SHA-1
`2acc015a27837af9a1e82035341e03d3c3d01ace` and SHA-256
`2bd28cc6af3c77a2d13fc616ec14862674cea5a7d3b2cacdae917d1d160262ee`;
`RESTORE-PATCH-TESTS.md` beside the staged image records the commands.
Unprivileged restore cannot preserve root ownership, so this is not a complete
root installation. The image uses 4 KiB sectors and the candidate uses 16 KiB
pages. Source review indicates the inspected inline frame is decoded using a
4 KiB sector buffer, but actual mount and reads remain untested. Include the
matching Btrfs module and dependencies in an initramfs when it is modular.
