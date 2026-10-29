#!/bin/bash
# Remove the patched asahi_m4 and restore the original initramfs (run with sudo), then reboot.
set -euo pipefail
KREL=7.1.13-509.gravity.fc44.aarch64+16k
IMG=/boot/initramfs-$KREL.img
rm -f /lib/modules/$KREL/updates/asahi_m4.ko
depmod -a "$KREL"
if [ -f "$IMG.pre-m4fix" ]; then cp -a "$IMG.pre-m4fix" "$IMG"; else dracut -f "$IMG" "$KREL"; fi
echo "chosen module: $(modinfo -n asahi_m4 -k $KREL). Reboot now."
