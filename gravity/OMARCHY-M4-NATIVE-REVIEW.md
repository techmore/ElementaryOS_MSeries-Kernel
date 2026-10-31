# Omarchy M4 Native J773g compatibility review — 2026-10-30

Source reviewed: `Kb2uka/Omarchy-M4-Native` `develop` at
`7d107f95bff1bc32efb2dd0fd019f9f4c1dba6a3`. This is a separate community
project, not our elementary M4 PR 444 and not the omacom linux-aurora package.
Its M4 Mac mini tester lane is experimental; no supported native desktop boot
on J773g is established by its documentation.

The tester kit uses a J713-derived 7.1.9 kernel and a J773g board overlay; it
uses the firmware framebuffer and does not provide Gravity's native T8132 DCP
support. Its `linux-m4-omarchy` PKGBUILD repackages a pinned payload with kernel
and modules, while `m4-boot-compose.py` is J713-gated and enforces known kernel
and DTB hashes and a fixed module release. The published mini kit's boot path
and updater must be reviewed separately. An R8 Debian payload, its 7.1.13 kernel
release and Gravity DTB are not drop-in replacements for this 7.1.9 stack.
Matched kernel, modules, J773g DTB, firmware, m1n1/boot composition, initramfs,
userspace GPU ABI, audio protection and package/update identities must be
resolved as a set; do not relax board gates or use the J713 speaker policy on
the mini as a shortcut.

The community project's `docs/j773g-boot-dtb.md` says its mini survey identified
an Abbey PMU (`pmu,abbey`) at SPMI USID `0xe`. Its J713 poweroff documentation
infers shutdown-state offsets from the Air's ADT scratchpad and matching
Chapel layouts; it reports an Air hardware test. The mini source data is a
separate Mac's macOS-side IOService reconstruction and the raw data is private;
the survey notes that the installed stub's ADT may differ. This is evidence for
an investigation, not proof of this machine's PMU base, scratchpad offsets,
shutdown behavior, or compatibility with Gravity's different SPMI topology.
No direct register accesses or writes have been performed here.

Sources:
- https://github.com/Kb2uka/Omarchy-M4-Native/blob/7d107f95bff1bc32efb2dd0fd019f9f4c1dba6a3/docs/j773g-macos-survey.md
- https://github.com/Kb2uka/Omarchy-M4-Native/blob/7d107f95bff1bc32efb2dd0fd019f9f4c1dba6a3/docs/j773g-boot-dtb.md
- https://github.com/Kb2uka/Omarchy-M4-Native/blob/7d107f95bff1bc32efb2dd0fd019f9f4c1dba6a3/docs/j713-poweroff.md
- https://github.com/Kb2uka/Omarchy-M4-Native/blob/7d107f95bff1bc32efb2dd0fd019f9f4c1dba6a3/packaging/omarchy-m4/linux-m4-omarchy/PKGBUILD
- https://github.com/Kb2uka/Omarchy-M4-Native/blob/7d107f95bff1bc32efb2dd0fd019f9f4c1dba6a3/tools/m4-boot-compose.py
