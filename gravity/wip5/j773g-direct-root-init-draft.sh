#!/usr/bin/bash
# Experimental initramfs: mount the specified Btrfs root and hand off to init.
# Sourcing this file exposes the parsing and lookup functions for host tests.
parse_boot_args() {
  local token uuid_re='^[[:xdigit:]]{8}-[[:xdigit:]]{4}-[[:xdigit:]]{4}-[[:xdigit:]]{4}-[[:xdigit:]]{12}$'
  ROOT_UUID= ROOT_SUBVOL=
  for token in $1; do
    case $token in
      root=PARTUUID=*) [[ -z $ROOT_UUID ]] || return 1; ROOT_UUID=${token#root=PARTUUID=} ;;
      rootflags=subvol=*) [[ -z $ROOT_SUBVOL ]] || return 1; ROOT_SUBVOL=${token#rootflags=subvol=} ;;
    esac
  done
  [[ $ROOT_UUID =~ $uuid_re && $ROOT_SUBVOL =~ ^[A-Za-z0-9_./-]+$ ]] || return 1
  [[ $ROOT_SUBVOL != /* && /$ROOT_SUBVOL/ != *'/../'* && /$ROOT_SUBVOL/ != *'/./'* && $ROOT_SUBVOL != *'//'* ]] || return 1
  ROOT_UUID=${ROOT_UUID,,}
}

find_root_device() {
  local entry line uuid name found=''
  for entry in "$1"/*/uevent; do
    [[ -r $entry ]] || continue
    uuid= name=
    while IFS= read -r line; do
      case $line in PARTUUID=*) uuid=${line#PARTUUID=} ;; DEVNAME=*) name=${line#DEVNAME=} ;; esac
    done < "$entry"
    if [[ ${uuid,,} == "$ROOT_UUID" && $name =~ ^[A-Za-z0-9._/-]+$ && $name != /* && /$name/ != *'/../'* && -e $2/$name ]]; then
      [[ -z $found ]] || return 1
      found=$2/$name
    fi
  done
  [[ -n $found ]] || return 1
  printf '%s\n' "$found"
}

[[ ${BASH_SOURCE[0]} != "$0" ]] && return 0
export PATH=/usr/bin HOME=/ TERM=linux
mount -t devtmpfs devtmpfs /dev
mount -t proc proc /proc
mount -t sysfs sysfs /sys
mount -t tmpfs tmpfs /tmp
printf 'Loading experimental keyboard drivers...\n'
modprobe -a spmi-apple-controller sn201202x phy-apple-atc dwc3-apple hid-apple || printf 'Keyboard module load failed; see dmesg.\n'
if IFS= read -r cmdline < /proc/cmdline && parse_boot_args "$cmdline"; then
  device=''
  for ((attempt=0; attempt<60; attempt++)); do
    device=$(find_root_device /sys/class/block /dev) && break
    sleep 1
  done
  if [[ -n $device ]] && mount -t btrfs -o "rw,subvol=$ROOT_SUBVOL" "$device" /newroot; then
    if [[ -x /newroot/sbin/init && -d /newroot/dev && -d /newroot/proc && -d /newroot/sys && -d /newroot/run ]]; then
      printf 'Mounted %s; switching to staged root.\n' "$device"
      # This replaces PID 1. If switch_root itself fails, no fallback shell is
      # guaranteed; an independent recovery path is still required.
      exec switch_root /newroot /sbin/init
    fi
    printf 'Staged root lacks executable init or required mount directories.\n'
  else
    printf 'Root device not found or mount failed.\n'
  fi
else
  printf 'Missing or invalid root PARTUUID/subvolume arguments.\n'
fi
printf 'Experimental early-boot shell; inspect dmesg and /proc/cmdline.\n'
while :; do
  /usr/bin/bash --noprofile --norc -i </dev/console >/dev/console 2>&1
  sleep 1
done
