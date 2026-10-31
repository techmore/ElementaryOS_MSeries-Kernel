# J773g direct rescue boot draft

The local directory `~/.cache/m4-kernel/latest-aurora/j773g-direct-rescue-draft/`
contains an isolated diagnostic bundle: the latest Aurora framebuffer kernel
Image, config-matched marked J773g DTB, RAM-only initramfs, ESP stage 2 and a
stage 1 configured for a separate rescue path on the machine's current ESP.
Its local `manifest.json` records file sizes and SHA-1/SHA-256. Nothing was
installed, enrolled or booted. The stage 1 and stage 2 contain machine-specific
ESP identity, so the artifacts themselves are not committed.

The stage 2 uses m1n1's documented `boot=` format to load the Image, DTB and
initramfs from that separate ESP path. The initramfs provides a RAM-only shell
and discovery commands and does not mount internal disks automatically. Archive
integrity, binary dependencies and stage 2 parameter structure were checked.
This is **not Omarchy**: the full verified Omarchy ARM root is staged separately
as described in `OMARCHY-ROOT-STAGING.md`.

The Image and 1,016 matching modules were produced by the completed latest
Aurora build; the module tree is staged separately and is not in this RAM-only
bundle. The mini's storage handoff, display,
serial and keyboard have not been exercised on this kernel. In particular,
rear USB controller/DART ownership is unresolved and the GPU is disabled.
The configured stage 1 is not known to be compatible with the installed Gravity
boot chain. Before attempting a boot, establish and preserve the actual current
ESP/GRUB and recovery configuration, finish the matched kernel artifacts, and
confirm a viable recovery and input or diagnostic path. The bundle is an
unverified draft, not an instruction to replace the current boot object.

`build-j773g-rescue.py` records the local ARM64 initramfs recipe. It packages
host binaries and libraries, so it is a diagnostic artifact specific to the
build environment and is not a reproducible Omarchy userspace. The staged
archive passed gzip, newc, shell syntax and packaged-library checks; physical
console and input remain untested.

An optional rear-keyboard experiment is recorded in
`0017-j773g-usb2-keyboard-trial.patch` and
`0018-m1n1-usb2-calibration-gate.patch`. The running Gravity system enumerates
the keyboard on rear controller 1 at USB2 speed. The trial enables only that
port and compiles a DTB; it leaves the mouse's controller disabled. The m1n1
change avoids applying old-format USB3 calibration to the mini's two-bank
USB2 profile and passed its host gate checks. Both are opt-in drafts, not
included in the rescue bundle. The mini DARTs expose 0x4000-byte windows but
their actual version is unknown; the newer driver must reject any v2 register
access beyond that range. Mini power ownership and physical input remain
unverified.

The bundle also contains a separate serial-plus-framebuffer variant. Its boot
arguments use `ttySAC0`, the Samsung UART console selected by the mini's
`serial0` alias, plus `tty0`. The running Gravity kernel logs confirm that
Linux device name; physical access and UART speed remain unverified.
The rescue init starts a tty1 shell when it detects a serial console. Source
review indicates the patched m1n1 direct-kernel path fills ANS/SART/mailbox
resources from the live J773g ADT and does not require U-Boot for that step;
the actual handoff is untested. If configured stage 1 cannot load its target,
it falls to the m1n1 proxy, not automatically back to Gravity. This must be
accounted for in any recovery plan.

A second local bundle, `~/.cache/m4-kernel/latest-aurora/j773g-keyboard-rescue-draft/`,
uses the optional rear USB2 keyboard DTB and an ESP stage 2 with the USB2
calibration gate. Its DTB SHA-1 is `a399dc6e91244487cced595d80914c66c2b98cfd`
and SHA-256 is `55da61de1a351c5eeb36360ec822d153f8f665bb3c775adcef61bcad069361d5`.
Its untouched source baseline matched the latest build's original DTB
byte-for-byte; the trial adds the import marker and keyboard-only include.
The DART version, port power ownership, physical keyboard and fallback remain
unverified. This variant is a diagnostic experiment and was not installed.

A separate source/format review verified both rescue variants' stage 1
configuration CRCs, stage 2 boot fields, Image headers, DT identities and
artifact hashes. For the keyboard variant, the observed DWC3, DART and SPMI
addresses and IRQs agree with the running Gravity DT, the enabled ATC and SPMI
power-domain labels and offsets match it, and the relevant drivers are built
in. This does not establish firmware ownership or safe resets. The newer
driver's DART bounds guard should refuse an incompatible
short v2 aperture. That could leave no keyboard; it does not establish power,
PHY behavior, console access or a safe recovery boot.
