# Reusing Aurora's M4 Air work for the Mac mini

The owner's WIP-forward direction makes Aurora's existing J713 M4 Air work
important prior art. The exact [basic series #366](https://github.com/aurora-silicon/linux/pull/366)
(`98a8f830df94a7dcaf7de37bfa915240afa2dda8`) reports a J713 boot with NVMe
root, Wi-Fi, USB and Bluetooth using matched m1n1 and U-Boot handoffs. The
[graphics series #367](https://github.com/aurora-silicon/linux/pull/367)
(`49c5d9994fec1b94cdce004bfa19c950c06b119e`) reports bounded native M4 Air
GPU and internal-display tests. Both PRs are closed without being marked
merged; their exact heads are useful review inputs, not evidence that WIP5
already contains or supports their full stack. Neither report qualifies the
J773g mini's HDMI, storage, radio, speakers, power or boot firmware.

## Storage integration mismatch

WIP5 source `2f725546` has a T8132 entry in `drivers/nvme/host/apple.c` and
the NVMe binding, but its J773g DT lacks the ANS, SART and NVMe nodes. The
WIP driver marks T8132 `has_separate_nvmmu` and requires a named `nvmmu`
resource; its binding likewise requires three register regions. Gravity's
working-host T8132 DT supplies two regions, and its older driver accesses
NVMMU registers through the NVMe controller mapping. A direct copy of Gravity
patch 0010 would thus fail WIP's binding and driver requirements. This is a
source comparison, not a demonstrated WIP5 storage failure on hardware.

The Air integration branch `325ed68cf0011730852cbb113a06fab86a4a8e31` uses
disabled placeholder ANS/SART/NVMe nodes, with comments requiring m1n1 to fill
resources from the live Apple device tree. Its resource naming/order and loader
contract must be reconciled with WIP5's driver and binding. The matching
[m1n1 #35](https://github.com/aurora-silicon/m1n1/pull/35) and
[U-Boot #7](https://github.com/aurora-silicon/u-boot/pull/7) describe a J713
handoff; they cannot be assumed to admit J773g. The Gravity mini and Air's
different register layouts must not be combined by guessing an NVMMU address.
The next implementation step is to compare the actual J773g firmware's ANS
resources and handoff with the WIP driver and select a verified mapping or a
carefully scoped driver adaptation before enabling the internal disk.

The Air's basic-series T8132 driver also sets `NVME_QUIRK_BROKEN_FUA`, with a
source comment reporting that J713 needed explicit flushes for writes to
survive reset. The WIP5 T8132 entry lacks that setting (although its T8140
entry has it). Draft `0002-t8132-nvme-explicit-flush.patch` carries the same
conservative quirk into the T8132 entry; it does not add or enable the mini's
NVMe nodes. It passes `git apply --check` against the full pinned WIP5 source.
The modified driver object compiled in the separate `3bdf11d3` checkout, whose
unmodified `apple.c` Git blob is identical to WIP5's
`d3ef47fa840e49ee49f8a94afb66d5ae6303a1db`; this is not a complete WIP5
build. The J713 evidence motivates the change but does not prove J773g storage
durability. Qualify flush, reset and recovery on an appropriate test setup
before relying on the mini's internal disk.

## Integration drafts for a build

- `0003-nvme-allow-adt-handoff-resource-order.patch` carries the J713 series'
  binding allowance for the loader's `nvme`, `nvmmu`, `ans` order onto WIP5.
- `0004-j773g-nvme-adt-placeholders.patch` adds J773g-only ANS, SART and NVMe
  placeholders and aliases, with the T8132 SART binding. All three nodes stay
  disabled until a J773g-aware loader supplies validated resources.
- `0005-m1n1-j773g-ans-handoff.patch` is a separate loader draft against
  `aurora-silicon/m1n1` `cda8314d2121c0279e4ca811bc6c6293a663e5d0`. It admits
  J773g ANS only when the device-tree alias is present and applies the retained
  memory reservations before reusing the existing live-ADT resource transfer.
  It deliberately does not enable J713 PMU or display handoffs on the mini.
- `0006-m1n1-no-display-build-option.patch` exposes `NO_DISPLAY=1` in that
  loader's generated build configuration. Without it, the Makefile silently
  ignores the option and the intended framebuffer-preserving build is not made.
- `0007-uboot-j773g-storage-import.patch` adds a separate opt-in J773g storage
  importer against Aurora U-Boot `cc47d3b7c86deb4094dc186d26799602272e37fb`.
  It imports ANS resources and memory/CPU/framebuffer data into a scratch tree
  without applying J713 keyboard or display policy. Kernel draft
  `0008-j773g-uboot-import-marker.patch` opts into it; the marker records the
  WIP5 base and is not proof of source provenance.
- `0009-uboot-j773g-optional-keyboard.patch` makes the Air importer's
  keyboard-layout property optional for the mini only. The pinned m1n1
  `dt_set_ipd()` explicitly returns without setting it when no built-in
  keyboard exists; the current mini Linux tree also lacks the property.
  A present property must still have the required four-byte form. The patched
  U-Boot importer object compiled with `apple_m1_defconfig`.
  `python3 gravity/wip5/verify-uboot-mini-keyboard.py <patched-uboot-tree>`
  exercised the production chosen importer with real libfdt: the Air path
  rejects an absent property, the mini accepts absence, and the mini rejects
  a malformed value. This is not a handoff or boot test.

The currently booted Gravity tree exposes `gravity,efi-system-partition`, not
`asahi,efi-system-partition`; the importer requires the latter in the m1n1
source tree. The running Linux tree is not the original m1n1 source tree, so
this is a compatibility question, not proof that the draft handoff fails. The
actual proposed loader configuration and source FDT must be checked together
before attempting a boot. The pinned m1n1 `payload_run()` supplies the Asahi
property when a valid in-image stage1 configuration selects a target; its
factory-empty configuration has no target. The compiled stage binaries alone
are therefore not a configured chainload bundle. Preserve an explicitly
selected ESP identity when assembling one, rather than relying on U-Boot's
fallback to the first EFI partition on a multi-boot machine.

The kernel drafts apply to the current WIP5 source with the preceding SMC
patch; the board DTB compiles in the matching-input checkout. Both loader
patches apply to the pinned source archive (SHA-256
`5e853caee70e56ba082f33c1d557fa30d25e92c2c571251b8ff04bbbc356e244`). With
isolated Rust 1.99.1 and `aarch64-unknown-none-softfloat`, the complete loader
build produced both stages with `NO_DISPLAY`; stage 1 additionally has
`CHAINLOADING`. The temporary artifacts were copied to
`~/.cache/m4-kernel/wip5-source/m1n1/j773g-loader-draft/`: stage 1 SHA-256
`c1b853663bdc4450fa23db8978c6c2f0aabd6b9e301bfa8541f945ad2f39f5eb`, stage 2
`ce3e5d78163cb3ca7e7c469d5d4ceacde8bae0dbbda0bf95f488bc42a798d427`.
These are non-release local builds; compiler warnings were reported in T8140
display code. The patched U-Boot builds with `apple_m1_defconfig`; its draft
`u-boot-nodtb.bin` is staged at
`~/.cache/m4-kernel/wip5-source/uboot-j773g-draft/` with SHA-256
`049ed439eb8a51e12f0c9720c79d38c785c6ac3af0467ff7d79a7290a6525ae5`.
After applying `0009`, an incremental build relinked the loader as
`u-boot-nodtb-keyboard-fix.bin` in that directory; SHA-1
`658d335591953db8524d1bf6f45254185f83d60d`, SHA-256
`d3c82891abbaabe113fff1feab8f38986dc19817c0cdfd95cf8f878774b816fc`.
Neither binary has been installed or booted.
The running WIP5 kernel build started before the opt-in marker; rebuild its
DTB with the complete patch set before pairing. Boot selection, source
identity, framebuffer properties and actual J773g firmware resources remain
unverified. This is not a bootable or hardware-qualified storage path. Do not
install the draft loader.

## Sound on the current Gravity host

The running Gravity boot lists ALSA cards `T8132Speaker` and `DisplayPort`;
its journal reports the mini speaker limiter and a connected HDMI audio
service, and PipeWire/WirePlumber started. Early probe-defer and missing dummy
regulator messages are also present. These observations establish registration,
not audible playback or speaker safety qualification. No sound was played or
audio stack changed. The mini's speaker protection and its electrical limits
remain separate from the Air's internal audio design.
