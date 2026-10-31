# J773g GPU inspection rescue command draft

This diagnostic preparation uses the uninstalled inspection loader documented
in `J773G-GPU-INSPECTION-BUNDLE.md`, the matching graphics kernel and the
previously built module-equipped rescue initramfs. It is not an Omarchy root.
The local cache directory
`~/.cache/m4-kernel/latest-aurora/gpu-early-diag/inspection-rescue-stage/`
contains the following tested-by-hash components:

| File | SHA-256 |
| --- | --- |
| `stage1-configured.bin` | `85694d4d7695d753c644a00f81630a5e2996d3c66a6a6aa60faeec5edf376c5c` |
| `stage2.bin` | `8d8198ae8175a15717b1719320d3be869dd2e14c6c222a10d481943509087229` |
| `Image` | `d7503a309985d172374c3ef1045fdab7fb1e4b370118d0f48fbe021221107de7` |
| `kernel-target.dtb` | `2ba45795b6da0156a3eaef2101f2f45bacc4f77e2992474c59df107b680d5c4d` |
| `initramfs.cpio.gz` | `4a8cd5cd412a7dffd57a0e4ce8a8faf61a01f9912a49870dbd0e16e21c66f1b1` |
| `inspection.scr` | `a9ae0b983ac77c33f5f53582bf0b5fd1c4111feafda039b75ad84f76cbcf09ac` |

Stage 1's existing config tool filled the observed ESP PARTUUID
`ca0747c3-afff-435b-9a54-7be212d75f19` and path
`aurora/j773g-gpu-inspection/stage2.bin`, with a five-second development proxy
window. These are local observations, not a portable installation plan. The
script expects the other four payload files in the same ESP directory. No
file has been copied to that ESP and no boot entry has been changed.

`j773g-gpu-inspection-rescue.cmd` is wrapped by U-Boot's built `mkimage` as
`inspection.scr`. If manually invoked, it verifies the partition UUID before
loading the kernel, the separately opted-in destination DTB and the initramfs,
then invokes `booti`. It explicitly enables the board FDT fixup in this U-Boot
session so the importer can transfer the diagnostic; it does not save U-Boot
environment changes. Source review confirms the built U-Boot has Hush, `part`,
generic filesystem `load`, `source`, `booti`, and board FDT setup. The FDT
relocation includes 256 KiB of padding. The UUID test is necessary because the
loader's `fw_dev_part` lookup can otherwise fall back to another ESP.

After appropriate staging and an independently confirmed recovery route, a
manual U-Boot command would need to verify the UUID before loading the script,
as well as the script's own check:

```
if part uuid nvme ${fw_dev_part} inspection_uuid && test "${inspection_uuid}" = "ca0747c3-afff-435b-9a54-7be212d75f19"; then load nvme ${fw_dev_part} ${scriptaddr} aurora/j773g-gpu-inspection/inspection.scr && source ${scriptaddr}; fi
```

This command is documentation for a future attended diagnostic, not an
instruction to boot now. The script was syntax-checked with Bash and wrapped
and listed with U-Boot `mkimage`; it was **not** executed by U-Boot Hush or on
hardware. It checks the ESP UUID and filenames, not payload hashes at runtime.
U-Boot still has its existing default boot behavior and saved environments can
affect it; the command requires a working interactive console. The paired
target DTB leaves the USB controller disabled, so the rescue initramfs's USB
modules do not establish a keyboard. The serial console, storage handoff,
framebuffer, physical input and recovery are all unverified. GPU execution
remains disabled. A separate proven recovery path is required before trying a
test boot.
