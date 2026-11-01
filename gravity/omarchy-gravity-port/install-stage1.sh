#!/bin/sh
# Run in macOS Recovery (Options → Utilities → Terminal):
#   diskutil mount "EFI - OMARC"
#   sh "/Volumes/EFI - OMARC/gravity/install-stage1.sh"
# Installs Gravity's m1n1 stage 1 as the Omarchy stub's boot object (same kmutil call as the
# Asahi and Gravity installers). Prints SUCCESS, or the reason it stopped.
ESP="/Volumes/EFI - OMARC"
OBJ="$ESP/gravity/gravity-stage1.bin"
SYS="/Volumes/Omarchy"

if [ ! -f "$OBJ" ]; then
  echo "STOPPED: $OBJ not found. Run: diskutil mount \"EFI - OMARC\"   then run this script again."
  exit 1
fi
if [ ! -d "$SYS/System" ]; then
  echo "Omarchy volume not mounted; mounting it..."
  diskutil mount Omarchy || true
fi
if [ ! -d "$SYS" ]; then
  echo "STOPPED: cannot find the Omarchy volume. Volumes present:"; ls /Volumes
  exit 1
fi
ls -l "$OBJ"
if ! grep -q "chosen.gravity,efi-system-partition" "$OBJ"; then
  echo "STOPPED: $OBJ is not the Gravity stage 1 object"; exit 1
fi
echo "Installing Gravity stage 1 into $SYS. Authenticate when asked."
if kmutil configure-boot -c "$OBJ" --raw --entry-point 2048 --lowest-virtual-address 0 -v "$SYS"; then
  echo
  echo "SUCCESS: Gravity stage 1 installed. Shut down, then hold power and boot Omarchy."
else
  echo
  echo "FAILED: kmutil returned an error (shown above). Photograph this screen."
  exit 1
fi
