# Omarchy M4 port audit — 2026-10-30

This is a source review, not an Omarchy build or hardware qualification.

- Omarchy's `linux-aurora` recipe in `omacom/omarchy-pkgs` master at
  `fb0042d80acfe67dbc3db1360b278158faa3f4ca` pins
  `omacom/linux-aurora` at `3bdf11d3acb6ea1511b0611ddd40ac5336b7b215`.
  It installs the kernel, modules and Apple DTBs together and retains an `-ARCH`
  kernel release for boot-bundle discovery. Recipe:
  https://github.com/omacom/omarchy-pkgs/blob/fb0042d80acfe67dbc3db1360b278158faa3f4ca/pkgbuilds/linux-aurora/PKGBUILD
- `GravityLinux/linux` `gravity-m4` was checked through GitHub at
  `4fc326f6c25ccceb7515e2635c22e01fde5d3bac`, matching this series' source pin.
- The existing 12/65 clean-apply result is for Aurora's separate M4 integration
  branch at `325ed68cf0011730852cbb113a06fab86a4a8e31`, not for the Omarchy
  package pin above. Do not use it as an apply result for the packaged kernel.
  Aurora's M4 GPU backend is distinct from Gravity's; patch 0066 targets the
  Gravity implementation and is not a portable fix for Aurora's driver.
- Gravity 0067 adds a generic reboot child inside T8132's SMC node. Aurora's
  M4 integration base defines the SMC in `t8132.dtsi`, but its J713 board file
  already supplies a `reboot` child with four PMU nvmem cells. Adding 0067 to
  the shared SoC node would overlap that board-specific definition. The J713
  offsets and board wiring are not evidence for the J773g mini; do not copy
  them to the mini without independent hardware evidence.
  https://github.com/aurora-silicon/linux/blob/325ed68cf0011730852cbb113a06fab86a4a8e31/arch/arm64/boot/dts/apple/t8132-j713.dts
- The exact Omarchy pin's `t8132.dtsi` has no SMC node; 0067 cannot be applied
  there independently of the missing platform support. A source check of a
  single file is not a full M4 support assessment.
- At that exact pin, the Apple DT Makefile does list `t8132-j773g.dtb`, and
  the J773g board source exists. Its board-specific content identifies the
  Mac mini and keeps HDMI framebuffer power domains on; it includes the
  shared T8132 files. This is a minimal board description, not evidence that
  the packaged kernel supports the Gravity system's devices or GPU. The
  pinned Asahi Kconfig describes explicit M3 and G15 options but no M4 option;
  that observation alone does not establish the driver's full capabilities.
  Sources: https://github.com/omacom/linux-aurora/blob/3bdf11d3acb6ea1511b0611ddd40ac5336b7b215/arch/arm64/boot/dts/apple/t8132-j773g.dts
  and https://github.com/omacom/linux-aurora/blob/3bdf11d3acb6ea1511b0611ddd40ac5336b7b215/drivers/gpu/drm/asahi/Kconfig

Next: obtain a full checkout of the exact Omarchy source pin and the intended
J773g integration base, inventory board support and compare subsystem behavior;
then prepare a separately named candidate package with a matched Image, modules
and DTBs. Check the boot-chain and firmware requirements and retain a known-good
fallback before any attended hardware trial. Build, DT schema and real boot,
reboot, shutdown and GPU qualification remain open. The current Gravity module
and DTB observations do not qualify an Omarchy or Aurora build.

## Exact Omarchy pin apply check

A full clean checkout of `omacom/linux-aurora` at `3bdf11d3acb6ea1511b0611ddd40ac5336b7b215`
was obtained on 2026-10-30. Each of the 67 patches was checked **independently**
against that pristine tree with `git apply --check`; results and diagnostics are
in [omarchy-pin-apply-check-2026-10-30.json](omarchy-pin-apply-check-2026-10-30.json).
Four checks pass (0008, 0047, 0048, 0052), and 63 fail. This does not replay the
series, account for dependencies, or establish semantic compatibility; passing
patches are not candidates for automatic application. In particular, 0066
fails because its two Gravity GPU source files are absent, and 0067 fails because
its target SMC context is absent.

The pinned tree does have a `t8132-j773g.dts` listed in the Apple DTB Makefile,
but the file contains only board identity and a framebuffer power-domain
adjustment on the common T8132 base. That is not the Gravity mini's peripheral,
GPU and storage support. A whole-device integration is required before a
bootable Omarchy candidate can be inferred.
