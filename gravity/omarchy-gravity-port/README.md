# Omarchy on the Mac mini M4 (J773g) via Gravity Linux's boot chain

Gravity Linux boots this Mac. Our Aurora-based boot chain does not: see [../BOOT-BLACK-SCREEN-2026-10-31.md](../BOOT-BLACK-SCREEN-2026-10-31.md) and [../GRAVITY-BOOT-PATH-2026-10-31.md](../GRAVITY-BOOT-PATH-2026-10-31.md).

This port replaces every piece below Omarchy's userspace with Gravity's signed builds, the versions known to run on this Mac:

| Piece | Gravity package |
|---|---|
| m1n1 stage 1 (APFS stub boot object) | `gravity-bootloader-stage1` 1.6.1-110 |
| m1n1 stage 2 + DTBs + U-Boot (`ESP/m1n1/boot.bin`) | `gravity-bootloader` 1.6.1-110, `kernel-16k-core` DTBs, `uboot-images-armv8` 2026.07-203 |
| Kernel (`ESP/gravity/gravity.efi`, a UKI) | `kernel-16k-core` 7.1.13-509 + 29 modules from `kernel-16k-modules{,-core}`, inside the installed Omarchy initramfs |

The installed Omarchy root (btrfs) and `/boot` are untouched. Packages and checksums are in [PACKAGES.txt](PACKAGES.txt).

## Kernel command line
```
root=UUID=4f4d5801-524f-4f54-8000-000000000001 rw rootflags=subvol=@,x-systemd.device-timeout=90 rootfstype=btrfs
nohlt idle=nop arm64.nowfxt appledrm.hdmi_audio=1 console=tty0 loglevel=7 printk.time=1
systemd.show_status=true plymouth.enable=0 initramfs_async=0 systemd.tty.term.console=dumb panic=10
```
`nohlt idle=nop arm64.nowfxt` are Gravity's required M4 arguments.

## Steps
1. **Build** (in the aarch64 Lima VM `diag`): `sudo bash build-gravity-boot.sh` writes `~/omarchy-boot-diag/gravity-out/`.
2. **Write the ESP** (macOS): `bash install-gravity-boot.sh`. It backs up `m1n1/boot.bin` → `m1n1/boot.bin.aurora` and `limine.conf` → `limine.conf.release`, writes `boot.bin`, `gravity/gravity.efi`, `gravity/gravity-stage1.bin` and the new `limine.conf`, and verifies each by read-back.
3. **Install stage 1 (Recovery).**
   1. Shut down, then hold the power button until "Loading startup options…" appears.
   2. Choose **Options** → Continue, and log in.
   3. Open **Utilities → Terminal**.
   4. Run:
      ```
      diskutil mount disk0s4
      kmutil configure-boot -c "/Volumes/EFI - OMARC/gravity/gravity-stage1.bin" --raw --entry-point 2048 --lowest-virtual-address 0 -v /Volumes/Omarchy
      ```
   5. Authenticate when asked, then shut down.

   (`kmutil configure-boot … --raw --entry-point 2048 --lowest-virtual-address 0` is the command both the Asahi and Gravity installers use. The boot policy set at install time stays.)
4. **Boot.**
   1. Hold the power button, choose **Omarchy**, then Continue.
   2. As on Gravity, HDMI stays dark until Linux's display driver starts.
   3. Kernel text, then systemd lines, should follow.
   4. SSH is on, with keys from github.com/techmore.keys.

## Going back to the Aurora chain
In Recovery, run `/Volumes/Omarchy/aura` (Omarchy's recovery helper reinstalls its stage 1). Then in macOS run `bash install-gravity-boot.sh restore`.
