#!/bin/bash
# Build Gravity Linux's proven M4 boot pieces for the installed Omarchy system on
# the Mac mini M4 (J773g). Runs inside an aarch64 Linux VM (Ubuntu, Lima "diag").
#
# Inputs (already downloaded and signature-checked, see PACKAGES.txt):
#   $G = Gravity RPMs unpacked: m1n1 stage 1/2, U-Boot, kernel 7.1.13-509 + modules + DTBs
#   $A/initrd.bin = the installed Omarchy UKI's initramfs (systemd userspace we reuse)
# Outputs in $O:
#   boot.bin              Gravity m1n1 stage 2 + DTBs + gzip U-Boot (their update-m1n1 recipe)
#   gravity-stage1.bin    Gravity m1n1 stage 1 + boot variables, padded to 64 KiB (their installer)
#   gravity.efi           UKI: Gravity kernel + Omarchy initramfs with Gravity's M4 modules
set -euo pipefail
H=/Users/sdolbec/omarchy-boot-diag
G=$H/gravity-root
A=$H/analysis
O=$H/gravity-out
V=7.1.13-509.gravity.fc44.aarch64+16k
ESP_UUID=dac5a463-154c-4516-b223-7cfddbd4ddec      # Omarchy ESP partition UUID (installer.log)
ROOT_UUID=4f4d5801-524f-4f54-8000-000000000001     # Omarchy btrfs root
mkdir -p "$O"

# Kernel command line: Gravity's required M4 args (kiwi-descriptions 58bdc596), efi=noruntime and
# no splash (andreinita21/OmarchyM4Mini docs/j773g-install.md: U-Boot's EFI runtime services and
# Plymouth's splash both hang the SMP boot through U-Boot and Limine), verbose for bring-up,
# finite root wait, crash -> reboot to macOS.
CMDLINE="root=UUID=$ROOT_UUID rw rootflags=subvol=@,x-systemd.device-timeout=90 rootfstype=btrfs \
nohlt idle=nop arm64.nowfxt efi=noruntime appledrm.hdmi_audio=1 console=tty0 loglevel=7 printk.time=1 \
systemd.show_status=true plymouth.enable=0 initramfs_async=0 systemd.tty.term.console=dumb panic=10"

# 1. Stage 2: m1n1 + DTBs + gzip U-Boot (GravityLinux/scripts update-m1n1)
DTB=$G/lib/modules/$V/dtb/apple
cat "$G/usr/lib64/m1n1/m1n1.bin" "$DTB"/t6*.dtb "$DTB"/t81*.dtb > "$O/boot.bin"
gzip -c "$G/usr/share/uboot/apple_m1/u-boot-nodtb.bin" >> "$O/boot.bin"
echo "boot.bin: $(stat -c %s "$O/boot.bin") bytes"

# 2. Stage 1 boot object: m1n1 + variables, zero-padded to 64 KiB (GravityLinux/installer src/m1n1.py)
{
  cat "$G/usr/lib64/m1n1-stage1/m1n1.bin"
  printf 'chosen.gravity,efi-system-partition=%s\n' "$ESP_UUID"
  printf 'chainload=%s;m1n1/boot.bin\n' "$ESP_UUID"
  printf '\0\0\0\0'
} > "$O/gravity-stage1.bin"
sz=$(stat -c %s "$O/gravity-stage1.bin"); pad=$(( (65536 - sz % 65536) % 65536 ))
head -c "$pad" /dev/zero >> "$O/gravity-stage1.bin"
echo "gravity-stage1.bin: $(stat -c %s "$O/gravity-stage1.bin") bytes"

# 3. Initramfs: Omarchy's systemd initramfs with Gravity's modules (and their deps) in place of Aurora's.
W=$(mktemp -d); unmkinitramfs "$A/initrd.bin" "$W/x"; R=$W/x
[[ -d $R/usr/lib/modules ]] || { echo "unexpected initramfs layout"; ls "$R"; exit 1; }
rm -rf "$R"/usr/lib/modules/*
MD=$R/usr/lib/modules/$V; mkdir -p "$MD"
cp "$G/lib/modules/$V"/modules.{builtin,builtin.modinfo,order} "$MD/"
depmod -b "$G" "$V"   # RPMs ship no modules.dep; Fedora runs depmod at install
WANT="nvme-apple apple-sart apple-rtkit-helper macsmc macsmc-rtkit gpio-macsmc rtc-macsmc macsmc-reboot apple-sio \
appledrm mux-apple-display-crossbar phy-apple-dptx phy-apple-atc dwc3 xhci-plat-hcd tps6598x \
usbhid hid-generic hid-apple atlantic tg3 apple_wdt"
for m in $WANT; do
  deps=$(modprobe -d "$G" -S "$V" --show-depends "$m" 2>/dev/null || true)
  [[ -n $deps ]] || echo "note: $m is not a module in $V (built in or absent)" >&2
  awk '$1=="insmod"{print $2}' <<<"$deps"
done | sort -u | while read -r ko; do
  rel=${ko#"$G/lib/modules/$V/"}; mkdir -p "$MD/$(dirname "$rel")"; cp "$ko" "$MD/$rel"
done
depmod -b "$R/usr" "$V"
printf '%s\n' $WANT > "$R/etc/modules-load.d/gravity-m4.conf" 2>/dev/null || { mkdir -p "$R/etc/modules-load.d"; printf '%s\n' $WANT > "$R/etc/modules-load.d/gravity-m4.conf"; }
echo "initramfs modules: $(find "$MD" -name '*.ko*' | wc -l)"
(cd "$R" && find . | LC_ALL=C sort | cpio -o -H newc --quiet | gzip -9) > "$O/initramfs-gravity.img"
rm -rf "$W"

# 4. UKI (no .dtb section: U-Boot passes m1n1's Gravity DTB through EFI)
ukify build --linux "$G/lib/modules/$V/vmlinuz" --initrd "$O/initramfs-gravity.img" \
  --cmdline "$CMDLINE" --uname "$V" --output "$O/gravity.efi"
ls -la "$O"; sha256sum "$O"/boot.bin "$O"/gravity-stage1.bin "$O"/gravity.efi
