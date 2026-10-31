#!/usr/bin/env bash
# Stage the verified generic ARM root into a new subvolume; never change boot.
set -euo pipefail

if (( EUID != 0 )); then
  echo 'Run as root: sudo bash stage-omarchy-root.sh /absolute/path/to/staging-directory' >&2
  exit 1
fi
if (( $# != 1 )) || [[ $1 != /* || ! -d $1 ]]; then
  echo 'Provide the existing absolute path to the Omarchy staging directory.' >&2
  exit 1
fi
stage=$(realpath -e -- "$1")
image="$stage/omarchy-root.img"
target="$stage/omarchy-root-subvolume"
expected=4b66dcfb84cc725e8bc11f27f3ecd452608e4753d13b3abfdab7124dbdb99b4e
[[ -f $image && ! -e $target ]] || { echo 'Missing image or target already exists.' >&2; exit 1; }
[[ $(findmnt -n -o FSTYPE -T "$stage") == btrfs ]] || { echo 'Target must reside on Btrfs.' >&2; exit 1; }
available=$(df -B1 --output=avail "$stage" | tail -1 | tr -d ' ')
(( available >= 15 * 1024 * 1024 * 1024 )) || { echo 'At least 15 GiB free is required.' >&2; exit 1; }
printf '%s  %s\n' "$expected" "$image" | sha256sum -c -
image_uuid=$(blkid -p -s UUID -o value "$image")
[[ -n $image_uuid ]] || { echo 'Cannot identify image UUID.' >&2; exit 1; }
if findmnt -rn -t btrfs -o UUID | grep -Fxiq -- "$image_uuid"; then
  echo 'Image filesystem UUID is already mounted; refusing duplicate mount.' >&2
  exit 1
fi

mountpoint=$(mktemp -d /tmp/omarchy-image.XXXXXXXX)
mounted=0
cleanup() {
  if (( mounted )); then umount -- "$mountpoint" || echo "Unmount failed: $mountpoint" >&2; fi
  rmdir -- "$mountpoint" || true
}
trap cleanup EXIT
mount -t btrfs -o ro,rescue=nologreplay,loop,subvolid=256 -- "$image" "$mountpoint"
mounted=1
btrfs subvolume create "$target"
echo "Copying to $target; a failure leaves the partial subvolume for inspection."
rsync -aHAX --numeric-ids -- "$mountpoint/" "$target/"
echo 'Copy completed. Checking metadata and contents with a dry run.'
report=$(mktemp "$stage/omarchy-rsync-check.XXXXXXXX")
rsync -aHAXnci --numeric-ids -- "$mountpoint/" "$target/" | tee "$report"
if [[ -s $report ]]; then
  echo "Copy verification found differences; inspect $report before continuing." >&2
  exit 1
fi
echo "Rsync reported no differences; check record: $report"
echo 'Staged generic ARM root only. Nested subvolume layout, provisioning, kernel and boot remain to be handled.'
