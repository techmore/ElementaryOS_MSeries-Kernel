#!/usr/bin/env bash
# Add the matching experimental kernel modules to an isolated staged root.
set -euo pipefail
if (( EUID != 0 || $# != 2 )); then
  echo 'Usage: sudo bash stage-graphics-modules.sh STAGED_ROOT MODULE_STAGE_ROOT' >&2
  exit 1
fi
target=$(realpath -e -- "$1")
source=$(realpath -e -- "$2")
release=7.2.11-elementary-m4-graphics-draft
[[ ${target##*/} == omarchy-root-subvolume && -f $target/etc/os-release ]] || {
  echo 'Expected the isolated staged Omarchy root.' >&2; exit 1;
}
btrfs subvolume show "$target" >/dev/null
[[ $(readlink "$target/lib") == usr/lib && -d $target/usr/lib/modules ]] || {
  echo 'Unexpected root module layout.' >&2; exit 1;
}
src="$source/lib/modules/$release"
dst="$target/usr/lib/modules/$release"
[[ -d $src && ! -e $dst ]] || { echo 'Module source missing or destination already exists.' >&2; exit 1; }
printf '%s  %s\n' f027e3050376e1d9da9ce83a4e88b1dc129077394f7a348cc709db203c0638e8 \
  "$src/kernel/drivers/gpu/drm/asahi/asahi.ko" | sha256sum -c -
[[ $(modinfo -F vermagic "$src/kernel/drivers/gpu/drm/asahi/asahi.ko") == "$release "* ]] || {
  echo 'Module release mismatch.' >&2; exit 1;
}
mkdir "$dst"
echo "Copying modules to $dst; errors leave the partial tree for inspection."
rsync -aHAX --numeric-ids -- "$src/" "$dst/"
depmod -b "$target" "$release"
echo 'Modules staged. Kernel image, firmware, initramfs and boot entry still require integration.'
