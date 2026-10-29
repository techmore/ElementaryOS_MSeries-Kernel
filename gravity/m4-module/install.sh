#!/bin/bash
# Install the patched asahi_m4 for the running kernel (run with sudo), then reboot.
# Undo with: sudo bash ~/m4-build/revert.sh
set -euo pipefail
KREL=7.1.13-509.gravity.fc44.aarch64+16k
SRC=${SRC:-$(getent passwd "${SUDO_USER:-$USER}" | cut -d: -f6)/m4-build/out/asahi_m4.ko}
[ "$(uname -r)" = "$KREL" ] && [ -f "$SRC" ]
IMG=/boot/initramfs-$KREL.img
[ -f "$IMG.pre-m4fix" ] || cp -a "$IMG" "$IMG.pre-m4fix"
install -D -m 0644 "$SRC" /lib/modules/$KREL/updates/asahi_m4.ko
depmod -a "$KREL"
dracut -f "$IMG" "$KREL"
echo "chosen module: $(modinfo -n asahi_m4 -k $KREL)"
echo "initramfs: $(lsinitrd "$IMG" | grep -c updates/asahi_m4) patched copy (want 1). Reboot now."
