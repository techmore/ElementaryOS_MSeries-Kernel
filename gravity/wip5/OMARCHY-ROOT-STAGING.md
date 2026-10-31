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

Read-only extraction from Btrfs root ID 256 shows the staged `/etc/fstab` and `/etc/crypttab` have no active entries. Its `/etc/mkinitcpio.conf` uses `HOOKS=(base systemd autodetect microcode modconf kms keyboard sd-vconsole block filesystems fsck)` with an empty explicit `MODULES` array. These are generic image defaults, not a configured mini installation. A future boot target needs an explicit root identity and an initramfs built for the exact candidate kernel; blindly running `autodetect` against the currently booted Gravity kernel may omit modules needed by that candidate. The latest diagnostic config has Apple NVMe, DART, SART and Btrfs built in, but its USB DT nodes remain disabled and firmware or network availability is not established. No root image, boot files or host configuration were changed by this inspection.

The same candidate is preserved here as
`btrfs-restore-inline-zstd-draft.patch` (SHA-1
`46ab7d261ce4736e129fb3fb9b7dac2fbd4ed4d7`); context formatting differs from
the cached original. It reverse-checks against the patched btrfs-progs v7.1
source with `git apply --unidiff-zero`, and needs broader review before an
upstream proposal.

A read-only comparison confirms the staged image's Btrfs filesystem UUID is
different from the currently mounted Gravity root. Cloning the image would
still duplicate its own UUID; attachment and installation must account for
that separately.

The practical metadata-correct staging path is a privileged, read-only loop
mount of the verified image followed by `rsync -aHAX --numeric-ids` into a new,
separately named Btrfs subvolume. Before any copy, recheck free space and all
mounted filesystem UUIDs; the image has about 10.16 GB referenced uncompressed
and two nested subvolumes (`portables` and `machines`) that need explicit
handling. Verify owners, setuid bits, hardlinks, ACLs, capabilities and special
files after copying. This does not provision a user, firmware or boot entry.
The detailed attended plan is in the local staging cache; no mount or target
subvolume has been created.
