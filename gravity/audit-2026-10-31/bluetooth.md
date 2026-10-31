# Bluetooth calibration on the Mac mini M4 (J773g, BCM4388C2 over PCIe)

Date: 2026-10-31.

## Result

- **Kernel fix:** techmore/linux-m1pro-touchid branch **`mini/bt`**, commit `b6c82ddf28a6`, on `elementaryos-mseries` `7ca15d034fc0`. Worktree: `/private/tmp/claude-501/wt/bt`. It changes one file, `drivers/bluetooth/hci_bcm4377.c` (+101/−6).
- **m1n1:** no change. Its ADT→DT copy is not tied to any board, and nothing in it can supply this Mac's calibration (see below). m1n1's CI is unaffected.
- **DT:** no change. The J773g `bluetooth0` node from `a694e343cb50` already has what is needed: the `bluetooth0` alias, `brcm,board-type = "apple,sakhalin"`, and a placeholder `local-bd-address`.
- **CI:** `elementaryos-mseries kernel` was dispatched on `mini/bt` as run 41213517087 (https://github.com/techmore/linux-m1pro-touchid/actions/runs/41213517087). The build passed; see CI below.
- Nothing was opened or posted upstream. No settings were changed.

## How Asahi/Aurora deliver Bluetooth calibration

- **m1n1** (`src/kboot.c`, `dt_set_bluetooth` / `dt_set_bluetooth_cal`) copies these ADT properties onto the DT node behind the `bluetooth0` alias:
  - `/arm-io/bluetooth` `bluetooth-taurus-calibration-bf` → `brcm,taurus-bf-cal-blob`
  - `/arm-io/bluetooth` `bluetooth-taurus-calibration` → `brcm,taurus-cal-blob`
  - Wi-Fi: `/arm-io/wlan` `wifi-calibration-msf` → `brcm,cal-blob`.

  The copy is **not gated to any board**; it skips only T8140, whose radio is MediaTek. When a property is missing it prints "Failed to get … Replaced module?" and carries on. `dt_set_mac_addresses` sets `local-bd-address` from `/chosen` `mac-address-bluetooth0`, byte-reversed.
- **Kernel** (`hci_bcm4377.c`): for BCM4388 (device ID 0x5f72), `bcm4388_send_calibration` always sends the **beamforming** blob, and `brcm,taurus-cal-blob` is optional. Before this fix, `bcm4377_probe_of` failed with `-ENOENT` whenever `brcm,taurus-bf-cal-blob` was missing.

## Why that path cannot work on J773g

- `adt-j773.txt` `/arm-io/bluetooth` has no `bluetooth-taurus-calibration*` properties.
- `/arm-io/wlan` has no `wifi-calibration-msf`.
- macOS's `ioreg.plist` has no taurus key either. It has `wifi-calibration-fdr` and `wlan.is.fdr.cal`, meaning macOS takes radio calibration from FDR/factory data, not from iBoot's ADT.

So admitting J773g in m1n1 would change nothing: m1n1 has no data to copy.

## How GravityLinux does it

- **Installer** (`gravity_firmware/radio_calibration.py`): extracts the `BTBF` (and `WCAL`) payload from the Mac's `BWCl-sakhalin-4388-C2-*` factory records, bound to `/chosen` `mac-address-bluetooth0`. It writes the result to the ESP as `vendorfw/u-boot/brcm/brcmbt4388-<12 lowercase hex address digits>-bf.bin`.
- **U-Boot** (GravityLinux/u-boot, commits `6e594cafea` and `a2f6913694`, branch `gravity-alpha-20260925`, function `apple_bluetooth_calibration`):
  - acts only on `apple,j773g`, and only when the DT has no `brcm,taurus-bf-cal-blob`
  - builds the file name from the DT `local-bd-address`, **reversed**
  - requires the size to be 4 B–32 KiB and the data to start with `BLOB`
  - sets `brcm,taurus-bf-cal-blob`; their J773g blob is 15040 bytes.

  Wi-Fi goes the same way, into `brcm,cal-blob`.
- **Gravity Linux and bootloader (m1n1)**: same as Aurora. The kernel consumes only the DT property, and m1n1 copies only from the ADT.

## Choice: a kernel fallback, not a U-Boot fork

Our chain is m1n1 → stock aurora-silicon U-Boot → Limine UKI. We have no U-Boot fork, and the installer fork (`792dab9`) puts `brcm/brcmbt4388-<addr>-bf.bin` in the **vendor firmware package**, next to `brcmbt4388c2-apple,sakhalin-a.{bin,ptb}`. `omarchy-vendor-firmware`/`omarchy-vendorfw` extract that package from `ESP/vendorfw/firmware.tar` for Linux. The kernel already loads the BT firmware with `request_firmware`, so the calibration loads the same way, with no new boot-chain component.

What the commit does:

- `bcm4377_probe_of` reads `local-bd-address` before the calibration check.
- On a BCM4388 without `brcm,taurus-bf-cal-blob`, `bcm4388_prepare_bf_cal_file` reverses the address into factory order and records the name `brcm/brcmbt4388-%6phN-bf.bin`. It rejects a zero address or one with the multicast bit set, as the installer and Gravity do.
- `bcm4388_send_calibration` loads the file (`firmware_request_nowarn`) during HCI setup, the same point where the BT firmware and PTB load. It checks the size and the `BLOB` marker as Gravity does, then caches the file so post-reset reloads reuse it. A devm action releases it on unbind.
- A DT property still takes precedence, and other chips keep the old error.
- checkpatch reports only the branch's usual trailer warnings (Co-Authored-By, no Signed-off-by).

## Still open

- **Not run on hardware.** The file name depends on m1n1 filling `local-bd-address` from a non-zero `/chosen` `mac-address-bluetooth0`. The ADT dump here has it zeroed, as it does the serials, and Gravity validated the live value on J773g. The installer must have written the file for the same address.
- **Wi-Fi calibration:** handled by the Wi-Fi twin on `mini/wifi` (see below).
- `mini/bt` is merged into `elementaryos-mseries` (fb0b8e6).

## CI

Run 41213517087 on `mini/bt` (self-hosted runner `m4mini-kbuild-2`) passed these steps: Configure (Aurora config + asahi.config, `CONFIG_BT_HCIBCM4377=m`), **Build Image, modules and DTBs**, Check the J773g device tree, Stage artifacts. So the changed driver compiles as a module. When this note was written (16:11 UTC), the artifact upload was still running.

m1n1: nothing was pushed. The coordinator's CI commit `4eba195` on `elementaryos-mseries` does not affect this work.

## Wi-Fi twin (`mini/wifi`)

Commit `48be8a810854` on techmore/linux-m1pro-touchid `mini/wifi`, cut from `elementaryos-mseries` `4e2d375ab53d` (worktree `/private/tmp/claude-501/wt/wifi`). It touches only `brcmfmac` `common.c`, `common.h` and `of.c` (+60 lines), and checkpatch reports 0 problems.

- **File name and address:** `brcm/brcmfmac4388-<address>-cal.bin`. `<address>` is the DT `local-mac-address` on the `wifi0` node, written as 12 lowercase hex digits **in its own byte order**. m1n1 copies `/chosen` `mac-address-wifi0` there without swapping it. The installer keys on the same raw `/chosen` value. This is the same as GravityLinux/u-boot `a2f6913694` (`reverse=false` for Wi-Fi). Bluetooth is keyed differently: its address is the **reverse** of the little-endian `local-bd-address`, and its key is `mac-address-bluetooth0`.
- **What the code does:**
  - `brcmf_of_probe`: when an Apple node (one with `brcm,board-type`) has no `brcm,cal-blob`, it saves `local-mac-address` in `settings->cal_mac`.
  - `brcmf_c_load_cal_file`: runs from `brcmf_c_process_cal_blob` during preinit, the point where the DT blob would be downloaded. It acts only when `bus->chip == 0x4388`, the address passes `is_valid_ether_addr` (nonzero and unicast, as Gravity requires), and there is no DT blob. It loads the file with `firmware_request_nowarn`, size-checks it (4 B–32 KiB) and checks the `BLOB` magic. Then it sets `cal_blob`/`cal_size`, which the existing `calload` path uses.
  - A missing or invalid file only logs, and Wi-Fi runs as before.
  - The firmware stays in the settings, which survive `brcmf_pcie_reset`, and is released in `brcmf_release_module_param`.
- **Without hardware, these can't be checked:** whether the live `local-mac-address` is non-zero and matches the installer's file, and whether the firmware accepts `calload` with this blob. Gravity reports that it does (`brcmfmac loads its platform calibration`).
- **CI:** run 41218774797 on `mini/wifi` was **cancelled** at 17:08 UTC, about 52 minutes into a cold build of a new `~/kbuild/mini-wifi` tree. I did not cancel it. Before the cancel, `brcmfmac/common.o` compiled with no warnings. Then, in the `kbuild` VM, I built `brcmfmac/of.o` in the same tree (`make ARCH=arm64 LLVM=1 CC="ccache clang" O=~/kbuild/mini-wifi …/of.o …/common.o`), and it also compiled with no warnings. That make re-synced `kernel.release` and regenerated the Rust bindings with the VM's own bindgen, so the next CI run on `mini/wifi` redoes a little of that work.
- Correction for `mini/bt`: run 41213517087 is recorded as **cancelled**. The build, DT check and staging all passed, and the cancel came during artifact upload.
