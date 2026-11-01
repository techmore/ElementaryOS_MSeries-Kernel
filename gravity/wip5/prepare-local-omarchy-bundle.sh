#!/usr/bin/env bash
# Assemble a non-installed direct-root experiment from the local staged files.
set -euo pipefail
if (( $# > 1 )) || { (( $# == 1 )) && [[ $1 != --allow-unprovisioned ]]; }; then
  echo 'Usage: bash prepare-local-omarchy-bundle.sh [--allow-unprovisioned]' >&2
  exit 1
fi
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
cache="$HOME/.cache"
root="$cache/m4-omarchy-root-staging/omarchy-root-subvolume"
base="$cache/m4-kernel/latest-aurora"
loader="$cache/m4-kernel/wip5-source/m1n1/j773g-loader-draft"
[[ -d $root ]] || { echo 'The Omarchy root has not been staged.' >&2; exit 1; }
root=$(realpath -e -- "$root")
[[ $(findmnt -n -o FSTYPE -T "$root") == btrfs ]] || { echo 'Staged root is not on Btrfs.' >&2; exit 1; }
mountpoint=$(findmnt -n -o TARGET -T "$root")
fsroot=$(findmnt -n -o FSROOT -T "$root")
source=$(findmnt -n -o SOURCE -T "$root")
source=${source%%\[*}
relative=$(realpath --relative-to="$mountpoint" -- "$root")
[[ $relative != .. && $relative != ../* ]] || { echo 'Staged root is outside its mount.' >&2; exit 1; }
subvol="${fsroot%/}/$relative"
subvol=${subvol#/}
root_uuid=$(lsblk -dn -o PARTUUID "$source" | tr -d '[:space:]')
[[ $(findmnt -n -o FSTYPE -T /boot/efi) == vfat && $(findmnt -n -o TARGET -T /boot/efi) == /boot/efi ]] || {
  echo 'Expected a mounted FAT ESP at /boot/efi.' >&2; exit 1;
}
esp_source=$(findmnt -n -o SOURCE -T /boot/efi)
esp_source=${esp_source%%\[*}
esp_uuid=$(lsblk -dn -o PARTUUID "$esp_source" | tr -d '[:space:]')
extra=()
(( $# == 0 )) || extra+=("$1")
python3 "$script_dir/stage-j773g-omarchy.py" \
  --image "$base/j773g-graphics-rescue-draft/Image" \
  --dtb "$base/j773g-graphics-keyboard-rescue-draft/t8132-j773g.dtb" \
  --stage1 "$loader/stage1-release-gpu-handoff.bin" \
  --stage2 "$loader/stage2-esp-usb2-trial.bin" \
  --fill-tool "$base/m1n1-usb-experiment/tools/fill_stage1_config.py" \
  --output "$base/j773g-omarchy-direct-draft" --root-directory "$root" \
  --esp-partuuid "$esp_uuid" --root-partuuid "$root_uuid" \
  --esp-directory aurora/j773g-omarchy-direct --root-subvol "$subvol" "${extra[@]}"
echo 'Bundle is local and uninstalled; recovery and hardware handoff remain unverified.'
