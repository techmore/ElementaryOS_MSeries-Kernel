#!/bin/bash
# Write Gravity Linux's M4 boot pieces onto the Omarchy EFI partition (disk0s4) from macOS.
#   bash install-gravity-boot.sh          install (backs up what it replaces, once)
#   bash install-gravity-boot.sh restore  put the Aurora boot.bin and the original limine.conf back
# Uses mtools (no mount; macOS here refuses its FAT driver for this partition).
# Stage 1 is installed separately from Recovery (see README.md): kmutil configure-boot.
set -euo pipefail
cd "$(dirname "$0")"
OUT=$HOME/omarchy-boot-diag/gravity-out
DEV=/dev/disk0s4
[[ $(diskutil info disk0s4 | awk -F': *' '/Partition Type:/{print $2}') == EFI ]] || { echo "STOPPED: disk0s4 is not EFI"; exit 1; }
[[ $(diskutil info disk0s4 | awk -F': *' '/Volume Name:/{print $2}') == "EFI - OMARC" ]] || { echo "STOPPED: disk0s4 is not the Omarchy EFI"; exit 1; }
[[ $(diskutil info disk0s4 | awk -F': *' '/Mounted:/{print $2}') == No ]] || { echo "STOPPED: disk0s4 is mounted"; exit 1; }
echo "== Your Mac password may be requested"; sudo -v
m() { sudo env MTOOLS_SKIP_CHECK=1 "$@"; }
exists() { m mdir -i "$DEV" "::/$1" >/dev/null 2>&1; }
put() { m mcopy -o -i "$DEV" "$1" "::/$2"; local w r; w=$(shasum -a 256 <"$1" | cut -c1-64)
        r=$(m mtype -i "$DEV" "::/$2" | shasum -a 256 | cut -c1-64); [[ $w == "$r" ]] || { echo "READ-BACK MISMATCH: $2"; exit 1; }
        echo "wrote and verified $2"; }

if [[ ${1:-} == restore ]]; then
  exists m1n1/boot.bin.aurora && { T=$(mktemp); m mcopy -n -i "$DEV" ::/m1n1/boot.bin.aurora "$T"; put "$T" m1n1/boot.bin; }
  exists limine.conf.release && { T=$(mktemp); m mcopy -n -i "$DEV" ::/limine.conf.release "$T"; put "$T" limine.conf; }
  echo "Restored. Stage 1 must also be restored from Recovery (see README.md)."; exit 0
fi

for f in boot.bin gravity.efi gravity-stage1.bin; do [[ -s $OUT/$f ]] || { echo "STOPPED: $OUT/$f missing"; exit 1; }; done
# Backups, once: the Aurora stage 2 and the installer's original menu
if ! exists m1n1/boot.bin.aurora; then T=$(mktemp); m mcopy -n -i "$DEV" ::/m1n1/boot.bin "$T"; put "$T" m1n1/boot.bin.aurora; fi
if ! exists limine.conf.release; then T=$(mktemp); m mcopy -n -i "$DEV" ::/limine.conf "$T"; put "$T" limine.conf.release; fi
exists gravity || m mmd -i "$DEV" ::/gravity
put "$OUT/gravity.efi" gravity/gravity.efi
put "$OUT/gravity-stage1.bin" gravity/gravity-stage1.bin
put "$OUT/boot.bin" m1n1/boot.bin
put limine-gravity.conf limine.conf
sync
echo "Done. Next: install stage 1 from Recovery (README.md), then boot Omarchy."
