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
[[ ! -e $target/home/$username && ! -L $target/home/$username ]] || { echo 'Home path already exists; refusing to adopt it.' >&2; exit 1; }
printf '%s\n' 'Creating the user in wheel and adding a general password-required sudo rule; existing command-specific rules remain.'
# Validate a password-required sudo policy in the target before installing it.
policy=$(mktemp "$target/etc/sudoers.d/.90-omarchy-wheel.XXXXXXXX")
created_nodes=()
created_ids=()
cleanup() {
  [[ ! -e $policy ]] || unlink -- "$policy"
  for i in "${!created_nodes[@]}"; do
    node=${created_nodes[i]}
    if [[ -c $node && ! -L $node ]] &&
       [[ $(stat -c '%d:%i:%t:%T' "$node") == "${created_ids[i]}" ]]; then
      unlink -- "$node"
    fi
  done
}
trap cleanup EXIT
[[ -d $target/dev && ! -L $target/dev ]] || { echo 'Staged /dev must be a real directory.' >&2; exit 1; }
prepare_device() {
  local name=$1 major=$2 minor=$3 expected=$4 node="$target/dev/$1"
  if [[ -e $node || -L $node ]]; then
    [[ -c $node && ! -L $node && $(stat -c '%t:%T' "$node") == "$expected" ]] || {
      echo "Staged /dev/$name is not the expected character device." >&2; return 1;
    }
  else
    mknod -m 666 "$node" c "$major" "$minor"
    created_nodes+=("$node")
    created_ids+=("$(stat -c '%d:%i:%t:%T' "$node")")
  fi
}
prepare_device tty 5 0 5:0
prepare_device null 1 3 1:3
if ! chroot "$target" /usr/bin/bash -c 'exec 3<>/dev/tty 4<>/dev/null'; then
  echo 'Cannot open /dev/tty or /dev/null inside staged root; no account was created.' >&2
  exit 1
fi
if chroot "$target" /usr/bin/getent passwd "$username" >/dev/null; then
  echo 'That account already exists; refusing to modify it.' >&2; exit 1
fi
chroot "$target" /usr/bin/getent group wheel >/dev/null || { echo 'Staged wheel group is missing.' >&2; exit 1; }
chroot "$target" /usr/bin/visudo -cf /etc/sudoers >/dev/null
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
echo 'Staged account and general password-required wheel sudo rule created. Existing rules remain; verify effective access on a safe first boot.'
