# J773g GPU inspection with rear USB2 trial

This is a separate, explicit experiment based on the recorded graphics keyboard
rescue DTB, SHA-256
`97f2733b7006858c4a095ad7fd78f2f6f89253004ec6f298a63fbf31c7030be2`.
The diagnostic target DTB SHA-256 is
`963a6adaa8a858fe898f4da1a4f49a33dad0730329e646ec9175d0ceb8b789ec`.
A decoded-tree comparison against that exact keyboard DTB shows one change:
the empty GPU diagnostic-only marker. The existing rear USB2 trial enables the
selected SPMI controller/connector, ATC PHY, DWC3 and its DART nodes; other
connectors stay as described by that keyboard DTB. GPU status remains disabled
and the GPU resource-handoff opt-in is absent on the destination.

The source DTB and packed m1n1/U-Boot stage 2 are exactly the existing GPU
inspection build. The source DTB leaves USB disabled. That m1n1 source has the
recorded J773g two-bank USB2 gate: the synthetic gate fixture passed and it
does not publish USB3 calibration for that profile. The J773g U-Boot import
does not import USB2 calibration; it retains the destination trial nodes rather
than proving their firmware handoff. A new real-libfdt synthetic full-import
fixture verifies the destination trial SPMI, PHY, DWC3 and two DART status
properties survive alongside GPU diagnostic transfer. It checks tree handling,
not the actual hardware, calibration, USB ownership or device binding.

The assembler now requires `--usb2-trial` to select this exact target hash. A
second local rescue draft is at
`~/.cache/m4-kernel/latest-aurora/gpu-early-diag/inspection-usb2-rescue-stage/`.
Its configured stage 1 (SHA-256
`92d457b4c6ad9e5c93aac114d7f9abcee244f790a83941172dbdb4f655c0a187`) points
to the separate ESP path `aurora/j773g-gpu-inspection-usb2/stage2.bin`; the
packed stage 2 SHA-256 remains
`8d8198ae8175a15717b1719320d3be869dd2e14c6c222a10d481943509087229`.
The U-Boot script uses that same separate path and the observed ESP PARTUUID;
its wrapped image SHA-256 is
`e8f0b58cbb22d0e58b4342d2ebf1b6114086e17db29ae006b857cb45bed1750c`.
It loads the same matching Image and module-equipped rescue initramfs as the
non-USB draft. Script syntax and image CRC were checked; neither script has
been run in U-Boot Hush.

Nothing is installed or booted. The initramfs starts an unauthenticated
RAM-only shell if a console works; it is not an Omarchy root. The enabled
experimental USB/DART path could fail or disrupt the diagnostic, and no actual
keyboard, display, storage, firmware, or recovery behavior is verified. This
artifact does not make a boot attempt safe or establish working GPU support.
