#!/usr/bin/env bash
# Opt-in offline desktop-manager experiment for the isolated Omarchy root.
set -euo pipefail
if (( EUID != 0 || $# != 2 )) || [[ $1 != /* || $2 != --enable-sddm ]]; then
  echo 'Usage: sudo bash enable-omarchy-sddm-draft.sh /absolute/path/to/omarchy-root-subvolume --enable-sddm' >&2
  exit 1
fi
target=$(realpath -e -- "$1")
[[ $target != / && ${target##*/} == omarchy-root-subvolume && -f $target/etc/os-release ]] || {
  echo 'Expected the isolated staged Omarchy root.' >&2; exit 1;
}
btrfs subvolume show "$target" >/dev/null
[[ $(stat -c %i "$target") == 256 ]] || { echo 'Target is not a subvolume root.' >&2; exit 1; }
for dir in etc etc/systemd etc/systemd/system usr usr/bin usr/lib usr/lib/systemd usr/lib/systemd/system; do
  [[ -d $target/$dir && ! -L $target/$dir ]] || { echo "Unexpected directory: $dir" >&2; exit 1; }
done
[[ -x $target/usr/bin/sddm && -x $target/usr/bin/start-hyprland && \
   -f $target/usr/lib/systemd/system/sddm.service && \
   -f $target/etc/sddm.conf.d/10-wayland.conf && \
   -f $target/usr/share/sddm/hyprland.lua ]] || {
  echo 'Staged SDDM and its Omarchy Wayland configuration are required.' >&2; exit 1;
}
link="$target/etc/systemd/system/display-manager.service"
[[ ! -e $link && ! -L $link ]] || { echo 'Display-manager selection already exists; refusing to replace it.' >&2; exit 1; }
ln -s -- /usr/lib/systemd/system/sddm.service "$link"
echo 'Enabled SDDM in the isolated root only; no boot files or live services changed.'
echo 'This is an untested desktop attempt, not GPU enablement or a verified display.'
echo 'SDDM conflicts with tty1 getty; keep an independent recovery path.'
