#!/bin/bash
# Switch the Omarchy boot menu to a verbose debug entry, or put the original back.
#   bash omarchy-debug-boot.sh on       # debug entry first (15 s menu, no splash, kernel text on screen)
#   bash omarchy-debug-boot.sh restore  # the installer's original limine.conf
# Changes one file, limine.conf, on the Omarchy EFI partition (disk0s4). Nothing else.
# Uses mtools (no mount): macOS here refuses its own FAT driver for this partition.
set -euo pipefail
cd "$(dirname "$0")"
RELEASE_SHA=c3e60f3ed712d3554049a63f9dcba9ba5e0a263d2473947147f0b2b3e9740af8
DEV=${OMARCHY_ESP_DEV:-/dev/disk0s4}   # override only to test on an image file
mode=${1:-}
[[ $mode == on || $mode == restore ]] || { echo "usage: $0 on|restore"; exit 2; }
command -v mcopy >/dev/null || { echo "STOPPED: mtools missing (brew install mtools)"; exit 1; }
[[ $mode == restore ]] || [[ -f limine-debug.conf ]] || { echo "STOPPED: limine-debug.conf missing"; exit 1; }

SUDO=
if [[ $DEV == /dev/* ]]; then
  [[ $DEV == /dev/disk0s4 ]] || { echo "STOPPED: only /dev/disk0s4 is allowed"; exit 1; }
  [[ $(diskutil info disk0s4 | awk -F': *' '/Partition Type:/{print $2}') == EFI ]] || { echo "STOPPED: disk0s4 is not EFI"; exit 1; }
  [[ $(diskutil info disk0s4 | awk -F': *' '/Volume Name:/{print $2}') == "EFI - OMARC" ]] || { echo "STOPPED: disk0s4 is not the Omarchy EFI"; exit 1; }
  [[ $(diskutil info disk0s4 | awk -F': *' '/Mounted:/{print $2}') == No ]] || { echo "STOPPED: disk0s4 is mounted"; exit 1; }
  SUDO=sudo
  echo "== Your Mac password may be requested"
  sudo -v
fi
m() { $SUDO env MTOOLS_SKIP_CHECK=1 "$@"; }
T=$(mktemp -d); trap 'rm -rf "$T"' EXIT

m mcopy -n -i "$DEV" ::/limine.conf "$T/current"
cur=$(shasum -a 256 <"$T/current" | cut -c1-64)
has_backup=0; m mtype -i "$DEV" ::/limine.conf.release >/dev/null 2>&1 && has_backup=1

if [[ $mode == on ]]; then
  if [[ $has_backup == 0 ]]; then
    [[ $cur == "$RELEASE_SHA" ]] || { echo "STOPPED: limine.conf is not the installer's ($cur); not touching it"; exit 1; }
    m mcopy -i "$DEV" "$T/current" ::/limine.conf.release
  fi
  m mcopy -o -i "$DEV" limine-debug.conf ::/limine.conf
  want=$(shasum -a 256 <limine-debug.conf | cut -c1-64)
  echo "Debug boot ON. Original kept as limine.conf.release."
else
  [[ $has_backup == 1 ]] || { echo "Nothing to restore (no limine.conf.release)"; exit 0; }
  m mcopy -n -i "$DEV" ::/limine.conf.release "$T/release"
  m mcopy -o -i "$DEV" "$T/release" ::/limine.conf
  want=$(shasum -a 256 <"$T/release" | cut -c1-64)
  echo "Original boot menu restored."
fi
sync
m mcopy -n -i "$DEV" ::/limine.conf "$T/check"
[[ $(shasum -a 256 <"$T/check" | cut -c1-64) == "$want" ]] || { echo "WARNING: read-back does not match what was written"; exit 1; }
echo "Verified by read-back. Menu now:"
grep -E "^(timeout|quiet|default_entry):|^/" "$T/check"
