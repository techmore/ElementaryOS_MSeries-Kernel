#!/usr/bin/env bash
# Attended preparation of an isolated Omarchy root; never installs boot files.
set -euo pipefail
if (( EUID != 0 || $# != 2 )) || [[ $1 != /* || $2 != /* ]]; then
  echo 'Usage: sudo bash prepare-omarchy-staged-root.sh /absolute/staging-directory /absolute/module-stage-root' >&2
  exit 1
fi
if [[ ! -t 0 || ! -t 1 ]]; then
  echo 'An interactive terminal is required for local user and password setup.' >&2
  exit 1
fi
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
stage=$(realpath -e -- "$1")
modules=$(realpath -e -- "$2")
[[ -d $stage && -d $modules && ! -e $stage/omarchy-root-subvolume && ! -L $stage/omarchy-root-subvolume ]] || {
  echo 'Staging directory or module source is invalid, or target already exists.' >&2; exit 1;
}
for name in stage-omarchy-root.sh stage-graphics-modules.sh provision-omarchy-user.sh; do
  [[ -f $script_dir/$name ]] || { echo "Missing helper: $name" >&2; exit 1; }
done
release=7.2.11-elementary-m4-graphics-draft
src="$modules/lib/modules/$release"
[[ -d $src ]] || src="$modules/usr/lib/modules/$release"
asahi="$src/kernel/drivers/gpu/drm/asahi/asahi.ko"
atlantic="$src/extra/atlantic.ko"
[[ -f $asahi && -f $atlantic ]] || { echo 'Matching graphics and Atlantic modules are required.' >&2; exit 1; }
printf '%s  %s\n' f027e3050376e1d9da9ce83a4e88b1dc129077394f7a348cc709db203c0638e8 "$asahi" | sha256sum -c -
printf '%s  %s\n' a150dcb959bb72b2aee1d67e90b3d0d8e41d6c078fbec2fad1ce9d6f806dfbfe "$atlantic" | sha256sum -c -
for module in "$asahi" "$atlantic"; do
  [[ $(modinfo -F vermagic "$module") == "$release "* ]] || { echo 'Module release mismatch.' >&2; exit 1; }
done
phase='root copy'
trap 'rc=$?; echo "Preparation stopped during $phase (exit $rc); any staged subvolume is retained for inspection." >&2; exit "$rc"' ERR
printf 'Preparing isolated root at %s/omarchy-root-subvolume\n' "$stage"
bash "$script_dir/stage-omarchy-root.sh" "$stage"
phase='matching module staging'
bash "$script_dir/stage-graphics-modules.sh" "$stage/omarchy-root-subvolume" "$modules"
phase='local account provisioning'
bash "$script_dir/provision-omarchy-user.sh" "$stage/omarchy-root-subvolume"
trap - ERR
echo 'Isolated root, matching modules and local account prepared. Boot files were not changed.'
echo 'Storage handoff, input, graphics, recovery and boot still require verification.'
