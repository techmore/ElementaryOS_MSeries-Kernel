#!/usr/bin/env bash
# Prepare a separate Gravity-based source candidate. Does not build or install.
set -euo pipefail
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
if (( $# != 2 )); then
  echo "usage: $0 GRAVITY_GIT_CHECKOUT NEW_WORKTREE_PATH" >&2
  exit 2
fi
source_repo=$(realpath -e -- "$1")
output=$(realpath -m -- "$2")
pin=4fc326f6c25ccceb7515e2635c22e01fde5d3bac
[[ ! -e $output ]] || { echo "output already exists: $output" >&2; exit 1; }
[[ $(git -C "$source_repo" rev-parse --verify "$pin^{commit}") == "$pin" ]] || {
  echo 'Gravity source pin not found' >&2; exit 1;
}
python3 "$here/check_series.py"
patches=(
  "$here/patches/0066-drm-asahi-poll-M4-completion-when-a-firmware-notific.patch"
  "$here/patches/0067-arm64-dts-apple-t8132-add-the-SMC-reboot-node.patch"
)
git -C "$source_repo" worktree add --detach "$output" "$pin"
for patch in "${patches[@]}"; do
  git -C "$output" apply --check "$patch"
  git -C "$output" apply "$patch"
done
printf 'Prepared %s at %s with local patches 0066 and 0067. No build or installation performed.\n' "$output" "$pin"
