# Mac mini M4 (J773g): first Omarchy boots, black screen. 2026-10-31

**Status:** unresolved. The boot chain works up to the Linux kernel. Linux then stops before it mounts its root filesystem. The HDMI screen stays dark the whole time, including during m1n1, U-Boot and the Limine menu.

## What happened
- **Install:** the fixed installer (`19f40c08…`, engine `a65af41744ea`, app 2.3.0) installed cleanly at 18:03–18:05 EDT.
- **Boot 1 (about 18:07–18:20):**
  - Picked Omarchy in Startup Options. Nothing ever appeared on HDMI.
  - The Mac never answered pings.
  - Forced off after up to 13 minutes.
- **Boot 2 (about 19:10–19:14):**
  - This time with a debug Limine entry: verbose, no splash, `x-systemd.device-timeout=90`, plus `initramfs_async=0 systemd.tty.term.console=dumb`.
  - Same result: dark screen.
  - An M1 Pro laptop on USB-C saw no m1n1 USB device.

## Evidence (read from macOS after each boot)
| Where | What it shows |
|---|---|
| ESP `ubootefi.var` (448 B, FAT date 2000-01-01) | Written by U-Boot (no RTC). It holds `Boot0000`, `BootOrder`, `PlatformLang` and **`LimineLastBootedEntry = "Omarchy debug (verbose, no splash)"`**. So boot 2 ran m1n1 stage 1 → stage 2 → U-Boot → Limine, and Limine launched the debug kernel entry. |
| btrfs root (disk0s6) superblock | Generation is still **15**, the same as the install image. `total_bytes` is still 13033799680, so it was never grown. **Never mounted read-write**, after either boot. No `/var/log/journal`, no pstore. |
| ext4 /boot (disk0s5) superblock | Mount count is still **1**, last mounted at image build (17:49 UTC). **Never mounted.** |
| ESP `m1n1/boot.bin` | Byte-identical to the package's copy (`af4eb468…`). Not rewritten at boot. |

**Conclusion:** m1n1, U-Boot and Limine work. The kernel is started and dies or hangs before the initramfs mounts root: an early kernel panic, an initramfs hang, or the internal SSD (ANS/NVMe) never appearing. The display is dark from m1n1 onward, so none of it is visible.

## Ruled out (checked statically)
- **SSD driver missing:** the initramfs has `nvme-apple` (it matches `apple,t8132-nvme-ans2`), `apple-sart`, `btrfs`, `apple-rtkit-helper`.
- **SSD not described:**
  - `nvme@40000` / `sart` / `ans_mbox` are `status = "disabled"` placeholders in `t8132.dtsi`, by design.
  - m1n1 `aac8189` `dt_set_ans_nvme()` (the `j773g_ans` path) fills them from the live ADT and enables them.
  - The m1n1 J773g DTB is byte-identical to the kernel's `t8132-j773g.dtb`.
- **U-Boot missing or unable to read the SSD:** U-Boot is in `boot.bin` (gzip). It matches `apple,t8132-nvme-ans2`, and it booted Limine from the ESP (see `ubootefi.var`).
- **Wrong m1n1:** stage 2 is `v1.6.1.aurora90-aac818930d32`.

## Image-builder bugs found (techmore/omarchy-mac-installer `elementaryos-mseries`)
1. **Hang fixes dropped from the kernel command line.**
   - `/etc/limine-entry-tool.d/omarchy-defaults.conf` adds `initramfs_async=0` and `systemd.tty.term.console=dumb`. Those are Omarchy's own fixes for an early-mount race and for the "black screen at Starting Switch Root until a key is pressed" hang.
   - `/etc/default/limine` then sets `KERNEL_CMDLINE[default]=` with `=`, and it is read after the drop-ins, so it replaces them.
   - The shipped UKI and limine.conf lack both. (Boot 2 added them and still failed, so this is not the whole cause.)
2. **Silent boot with an infinite wait.** `quiet splash loglevel=0 … rootflags=…,x-systemd.device-timeout=0`: a missing root waits forever, invisibly. Developer builds should be verbose with a finite timeout (`image-builder/builder/finalize-root:100`, `inspection.py:38`, `test_mac_image_check.py:714/734`).
3. **Initramfs built for the build VM.** HOOKS include `autodetect` while `mkinitcpio -P` runs in the image VM (`image-builder/bin/build-mac-image:1317`). The initramfs carries `virtio_*` and no `appledrm`, so there is no early display.

## Not yet known
Where the kernel stops. The screen is dark and m1n1's USB log never appeared. The m1n1 USB device code has no T8132-specific path (`src/usb.c` only special-cases T8140).

## Next
- Give the kernel a way to leave evidence the next macOS boot can read. Options:
  - an initramfs hook that writes `dmesg` to the ESP once the SSD appears;
  - a timeout that reboots after N seconds, so a hang and a crash look different from macOS.
- Fix builder bugs 1–3 for the next image.
- Get the display working before Linux:
  - m1n1/U-Boot framebuffer on the Mac mini's HDMI (dcpext);
  - `appledrm` in the initramfs.

## State of this Mac
- Omarchy is installed and untouched.
- The ESP `limine.conf` holds the debug menu (entry 1 debug, entry 2 normal). The original is `limine.conf.release`.
- To restore it: `bash omarchy-debug-boot.sh restore`.
