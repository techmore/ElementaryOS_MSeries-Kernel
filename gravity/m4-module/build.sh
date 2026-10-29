#!/bin/bash
# Build the patched asahi_m4 module for the running Gravity kernel.
# No sudo. Uses Fedora's rustc 1.98.1 (the compiler that built 7.1.13-509),
# unpacked under ~/m4-build/root. Output: ~/m4-build/out/asahi_m4.ko
set -euo pipefail
B=$HOME/m4-build
KREL=7.1.13-509.gravity.fc44.aarch64+16k
K=$B/root/usr/src/kernels/$KREL
[ "$(uname -r)" = "$KREL" ] || { echo "running kernel is $(uname -r), expected $KREL"; exit 1; }
export LD_LIBRARY_PATH=$B/root/usr/lib64
RUSTC=$B/root/usr/bin/rustc
"$RUSTC" --version
for tree in asahi_m4-stock asahi_m4-fix; do
  echo "== building $tree"
  make -s -C "$K" M="$B/$tree" RUSTC="$RUSTC" -j"$(nproc)" modules
done
mkdir -p "$B/out"
cp "$B/asahi_m4-fix/asahi_m4.ko" "$B/out/asahi_m4.ko"
echo "== sanity: stock rebuild vs shipped module"
xz -dc /lib/modules/$KREL/kernel/drivers/gpu/drm/asahi/asahi_m4.ko.xz > "$B/out/shipped.ko"
size "$B/out/shipped.ko" "$B/asahi_m4-stock/asahi_m4.ko" "$B/out/asahi_m4.ko"
modinfo -F vermagic "$B/out/asahi_m4.ko"
strings "$B/out/asahi_m4.ko" | grep -c "polling retired Work" >/dev/null && echo "patched build OK: $B/out/asahi_m4.ko"
