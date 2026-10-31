#!/bin/bash
# First-boot check for Omarchy on the Mac mini M4 (J773g). Read-only.
# Run on the Mac (or over SSH): bash first-boot-check.sh
# Prints one PASS/FAIL/INFO line per release-gate item, then the evidence.
set -u
pass() { printf 'PASS  %s\n' "$*"; }
fail() { printf 'FAIL  %s\n' "$*"; }
info() { printf 'INFO  %s\n' "$*"; }
have() { command -v "$1" >/dev/null 2>&1; }

echo "== $(hostname) $(uname -r) $(date -u +%FT%TZ)"
model=$(tr -d '\0' </proc/device-tree/compatible 2>/dev/null | head -c 80)
[[ $model == *j773g* ]] && pass "board: $model" || fail "board: $model"
[[ $(uname -r) == 7.3.0-90-* ]] && pass "kernel $(uname -r)" || info "kernel $(uname -r)"

# Display: DCP/dcpext driving a connector, and a GPU render node
for c in /sys/class/drm/card*-*/status; do
  [[ -e $c ]] || continue
  s=$(<"$c"); n=${c%/status}; n=${n##*/}
  [[ $s == connected ]] && pass "display connector $n connected ($(head -1 "${c%/status}/modes" 2>/dev/null))" || info "connector $n $s"
done
ls /dev/dri/renderD* >/dev/null 2>&1 && pass "GPU render node: $(ls /dev/dri/renderD* | tr '\n' ' ')" || fail "no GPU render node"
drv=$(for d in /sys/class/drm/card*/device/driver; do basename "$(readlink -f "$d")"; done 2>/dev/null | sort -u | tr '\n' ' ')
info "DRM drivers: $drv"
if have vulkaninfo; then
  vk=$(vulkaninfo --summary 2>/dev/null | grep -E "deviceName|driverName" | head -2 | tr -s ' ' | tr '\n' ' ')
  [[ -n $vk ]] && pass "Vulkan: $vk" || fail "vulkaninfo found no device"
fi
pgrep -x Hyprland >/dev/null && pass "Hyprland (desktop) running" || fail "Hyprland not running"

# Audio, Bluetooth, Wi-Fi, Ethernet
aplay -l 2>/dev/null | grep -q card && pass "audio: $(aplay -l 2>/dev/null | grep -m1 card)" || fail "no ALSA playback card"
lsmod | grep -q snd_t8132_speaker && pass "speaker driver loaded" || info "snd_t8132_speaker not loaded"
[[ -d /sys/class/bluetooth/hci0 ]] && pass "Bluetooth hci0 present" || fail "no Bluetooth adapter"
journalctl -k -b 2>/dev/null | grep -qi "brcmbt4388.*bf.bin\|taurus.*cal" && info "BT calibration: $(journalctl -k -b | grep -i -m1 'bf.bin\|taurus')"
wl=$(ls /sys/class/net | grep -E '^wl' | head -1)
[[ -n $wl ]] && pass "Wi-Fi interface $wl" || fail "no Wi-Fi interface"
journalctl -k -b 2>/dev/null | grep -i -m1 "Calibration blob\|no calibration blob" | sed 's/^/INFO  wifi: /'
eth=$(ls /sys/class/net | grep -E '^(en|eth)' | head -1)
[[ -n $eth ]] && info "Ethernet $eth: $(cat /sys/class/net/$eth/operstate 2>/dev/null)"
ping -c1 -W3 1.1.1.1 >/dev/null 2>&1 && pass "network reaches the internet" || fail "no internet"

# Power button (SMC) and watchdog
journalctl -k -b 2>/dev/null | grep -qi "macsmc.*input\|power button" && pass "SMC power button registered" || info "power button not seen in kernel log"
[[ -e /dev/watchdog0 ]] && info "watchdog present"

# AI gate: Claude Code, MLX runtime
cc=$(ls /home/*/.local/bin/claude 2>/dev/null | head -1)
[[ -n $cc ]] && pass "Claude Code installed: $($cc --version 2>/dev/null | head -1)" || fail "Claude Code not installed yet"
pacman -Q omarchy-mlx-vulkan-aurora >/dev/null 2>&1 && pass "MLX runtime: $(pacman -Q omarchy-mlx-vulkan-aurora)" || info "MLX runtime package not installed"

# Install timing (release gate)
t=/var/log/omarchy/install-timing.jsonl
if [[ -r $t ]]; then
  pass "install timing recorded ($(wc -l <"$t") milestones)"; cat "$t"
else
  fail "no $t"
fi

echo "== errors this boot"
journalctl -b -p err --no-pager 2>/dev/null | tail -25
echo "== kernel warnings (dcp, gpu, asahi, apple)"
journalctl -k -b --no-pager 2>/dev/null | grep -iE "dcp|asahi|agx|apple.*(fail|error|timeout)|iommu fault|dart" | tail -25
