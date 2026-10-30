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

## Sound on the current Gravity host

The running Gravity boot lists ALSA cards `T8132Speaker` and `DisplayPort`;
its journal reports the mini speaker limiter and a connected HDMI audio
service, and PipeWire/WirePlumber started. Early probe-defer and missing dummy
regulator messages are also present. These observations establish registration,
not audible playback or speaker safety qualification. No sound was played or
audio stack changed. The mini's speaker protection and its electrical limits
remain separate from the Air's internal audio design.
