#!/usr/bin/env bash
# Attend local user provisioning inside an already staged Omarchy subvolume.
set -euo pipefail

if (( EUID != 0 || $# != 1 )) || [[ $1 != /* ]]; then
  echo 'Usage: sudo bash provision-omarchy-user.sh /absolute/path/to/omarchy-root-subvolume' >&2
  exit 1
fi
if [[ ! -t 0 || ! -t 1 ]]; then
  echo 'An interactive terminal is required for username and password prompts.' >&2
  exit 1
fi
target=$(realpath -e -- "$1")
[[ $target != / && ${target##*/} == omarchy-root-subvolume && -f $target/etc/os-release ]] || {
  echo 'Expected the isolated staged Omarchy root subvolume.' >&2; exit 1;
}
btrfs subvolume show "$target" >/dev/null
[[ $(stat -c %i "$target") == 256 && -f $target/etc/passwd && -f $target/etc/shadow && -f $target/etc/group ]] || {
  echo 'Staged root account database or subvolume identity is missing.' >&2; exit 1;
}
for command in useradd passwd getent sudo visudo; do
  [[ -x $target/usr/bin/$command ]] || { echo "Missing staged /usr/bin/$command." >&2; exit 1; }
done
[[ -d $target/etc/sudoers.d && -f $target/etc/sudoers && ! -e $target/etc/sudoers.d/90-omarchy-wheel && ! -L $target/etc/sudoers.d/90-omarchy-wheel ]] || {
  echo 'Expected sudoers, sudoers.d and no existing 90-omarchy-wheel policy.' >&2; exit 1;
}
grep -Eq '^[[:space:]]*(@includedir|#includedir)[[:space:]]+/etc/sudoers[.]d([[:space:]]|$)' "$target/etc/sudoers" || {
  echo 'Staged sudoers does not include /etc/sudoers.d.' >&2; exit 1;
}
[[ -x $target/usr/bin/bash ]] || { echo 'Staged bash is missing.' >&2; exit 1; }
printf 'Staged root: %s\n' "$target"
read -r -p 'New local username: ' username
[[ $username =~ ^[a-z_][a-z0-9_-]{0,30}$ ]] || { echo 'Invalid username.' >&2; exit 1; }
if chroot "$target" /usr/bin/getent passwd "$username" >/dev/null; then
  echo 'That account already exists; refusing to modify it.' >&2; exit 1
fi
chroot "$target" /usr/bin/getent group wheel >/dev/null || { echo 'Staged wheel group is missing.' >&2; exit 1; }
[[ ! -e $target/home/$username && ! -L $target/home/$username ]] || { echo 'Home path already exists; refusing to adopt it.' >&2; exit 1; }
printf '%s\n' 'Creating the user in wheel with password-required sudo in the staged root.'
chroot "$target" /usr/bin/visudo -cf /etc/sudoers >/dev/null
# Validate a password-required sudo policy in the target before installing it.
policy=$(mktemp "$target/etc/sudoers.d/.90-omarchy-wheel.XXXXXXXX")
tty_node="$target/dev/tty"
tty_created=0
tty_identity=''
cleanup() {
  [[ ! -e $policy ]] || unlink -- "$policy"
  if (( tty_created )) && [[ -c $tty_node && ! -L $tty_node ]] &&
     [[ $(stat -c '%d:%i:%t:%T' "$tty_node") == "$tty_identity" ]]; then
    unlink -- "$tty_node"
  fi
}
trap cleanup EXIT
[[ -d $target/dev && ! -L $target/dev ]] || { echo 'Staged /dev must be a real directory.' >&2; exit 1; }
if [[ -e $tty_node || -L $tty_node ]]; then
  [[ -c $tty_node && ! -L $tty_node && $(stat -c '%t:%T' "$tty_node") == 5:0 ]] || {
    echo 'Staged /dev/tty is not the expected character device.' >&2; exit 1;
  }
else
  mknod "$tty_node" c 5 0
  tty_identity=$(stat -c '%d:%i:%t:%T' "$tty_node")
  tty_created=1
fi
if ! chroot "$target" /usr/bin/bash -c 'exec 3<>/dev/tty'; then
  echo 'Cannot open /dev/tty inside staged root; no account was created.' >&2
  exit 1
fi
(umask 077; printf '%%wheel ALL=(ALL:ALL) ALL\n' > "$policy")
chmod 0440 "$policy"
chroot "$target" /usr/bin/visudo -cf "/etc/sudoers.d/${policy##*/}" >/dev/null
chroot "$target" /usr/bin/useradd -m -G wheel -s /bin/bash -- "$username"
echo 'Set the new account password at the local terminal.'
if ! chroot "$target" /usr/bin/passwd "$username"; then
  echo 'Password setup failed; the newly created account may remain locked. Inspect the staged root before retrying.' >&2
  exit 1
fi
mv -- "$policy" "$target/etc/sudoers.d/90-omarchy-wheel"
echo 'Staged account and password-required wheel sudo policy created. Verify access on a safe first boot.'
