# Patched asahi_m4 module for a running Gravity kernel

Rebuilds only `asahi_m4.ko` with patch 0066 for `7.1.13-509.gravity.fc44.aarch64+16k`,
using the kernel-devel tree and the same Rust compiler that built the kernel. See
`../GPU-HANG-2026-10-28.md` for the details.

## One-time setup on the M4 (no sudo)

```bash
mkdir -p ~/m4-build/rpms ~/m4-build/root && cd ~/m4-build/rpms
curl -fLO https://kojipkgs.fedoraproject.org/packages/rust/1.98.1/1.fc44/aarch64/rust-1.98.1-1.fc44.aarch64.rpm
curl -fLO https://kojipkgs.fedoraproject.org/packages/rust/1.98.1/1.fc44/aarch64/rust-std-static-1.98.1-1.fc44.aarch64.rpm
dnf download kernel-16k-devel-7.1.13-509.gravity.fc44
cd ~/m4-build/root && for f in ../rpms/*.rpm; do rpm2cpio "$f" | cpio -idm --quiet; done
```

Put the driver sources in `~/m4-build/asahi_m4-stock/` (unpatched) and
`~/m4-build/asahi_m4-fix/` (with 0066). Each needs `asahi_m4.rs`, `float.rs`, `g16*.rs`
and `m4_*.rs` from `drivers/gpu/drm/asahi`, plus a `Kbuild` containing
`obj-m := asahi_m4.o`. The stock tree is a toolchain sanity check.

## Steps

| Step | Command |
| --- | --- |
| Build (no sudo) | `bash build.sh` → `~/m4-build/out/asahi_m4.ko` |
| Install (backs up the initramfs to `*.img.pre-m4fix`, then runs depmod and dracut) | `sudo bash install.sh`, then reboot |
| Undo | `sudo bash revert.sh`, then reboot |
| Login screen waits for HDMI | `sudo install -D -m644 wait-display.conf /etc/systemd/system/plasmalogin.service.d/wait-display.conf && sudo systemctl daemon-reload` |

The module is unsigned. Gravity's kernel loads it with a taint (`OE`), because
`module.sig_enforce` is off.
