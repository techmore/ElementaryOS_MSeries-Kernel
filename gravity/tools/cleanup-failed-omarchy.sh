#!/bin/bash
# Remove the partitions a failed Omarchy install left on this Mac mini M4, so the
# installer can use that space again. It checks every partition before touching
# it and stops at the first mismatch. It never touches disk0s1 (Apple system),
# disk0s2 (macOS) or disk0s7 (Apple Recovery).
set -euo pipefail

stop() { echo "STOPPED: $*" >&2; echo "Nothing more was changed. Send this output to Claude." >&2; exit 1; }

part_type() { diskutil info "$1" 2>/dev/null | awk -F': *' '/Partition Type:/{print $2}'; }
part_bytes() { diskutil info "$1" 2>/dev/null | sed -n 's/.*Disk Size:.*(\([0-9]*\) Bytes).*/\1/p'; }

check() { # identifier, expected type, min GB, max GB
  local t b
  t=$(part_type "$1"); b=$(part_bytes "$1")
  [[ $t == "$2" ]] || stop "$1 is '$t', expected '$2'"
  (( b >= $3 * 1000000000 && b <= $4 * 1000000000 )) || stop "$1 is $b bytes, expected $3-$4 GB"
  echo "ok: $1 $t $b bytes"
}

echo "== Before"
diskutil list disk0

# The four leftovers, checked before anything changes
check disk0s6 "Linux Filesystem" 70 80
check disk0s5 "Linux Filesystem" 2 3
check disk0s4 "EFI" 0 1
# Disk numbers change between boots: find the container whose physical store is disk0s3.
stub=$(diskutil list disk0 | awk '$NF=="disk0s3"{for(i=1;i<=NF;i++) if($i ~ /^disk[0-9]+$/) print $i}')
[[ $stub =~ ^disk[0-9]+$ ]] || stop "cannot find the APFS container on disk0s3"
store=$(diskutil info "$stub" 2>/dev/null | awk -F': *' '/APFS Physical Store:/{print $2}')
[[ $store == disk0s3 ]] || stop "$stub is not the container on disk0s3 (store: '$store')"
diskutil apfs list "$stub" | grep "Name: *Omarchy (Case" >/dev/null || stop "$stub has no volume named Omarchy"
diskutil apfs list "$stub" | grep -q "Name: *Macintosh HD" && stop "$stub holds Macintosh HD"
size=$(part_bytes disk0s3); (( size < 7000000000 )) || stop "disk0s3 is larger than the 6 GB stub"
echo "ok: $stub is the 6 GB Omarchy stub on disk0s3"

echo "== Removing (your Mac password may be requested)"
sudo diskutil eraseVolume free none disk0s6
sudo diskutil eraseVolume free none disk0s5
sudo diskutil eraseVolume free none disk0s4
sudo diskutil apfs deleteContainer "$stub"

echo "== After"
diskutil list disk0
echo "Done. Expect: Apple system, macOS (160.1 GB), free space, Apple Recovery."
