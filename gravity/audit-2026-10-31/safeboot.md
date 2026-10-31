# Safe first boot kit for the Mac mini M4 (2026-10-31)

Goal: every first boot of a new kernel or install on J773g falls back to a known-good entry on any failure, following chriskearney/maclab (MIT; joshuaswarren's fork adds nothing). It is part of the boot-ready Omarchy installer for the mini.

## Delivered

- **techmore/omarchy-pkgs**, new branch `elementaryos-mseries-safeboot` (from `elementaryos-mseries` 34c27c6e), commit `0184a4222e25`:
  - `pkgbuilds/omarchy-trial-boot/`: the `omarchy-trial-boot` script (arm, stage, disarm, status, collect, hold, watch, complete), units `omarchy-trial-boot-{watch,complete,collect}.service`, `README.md`, `test.sh`, `PKGBUILD` (aarch64, `check()` runs the tests) and `.omarchy/package.json` (local, sync false).
  - `release/mac-inventory.txt`: `omarchy-trial-boot none`, as the mlx branch did for its package.
  - `.github/workflows/elementaryos-mseries-safeboot.yml`, two jobs:
    - test: `shellcheck -S error`, and `test.sh` as a user and as root with the real grub-editenv;
    - build: `bin/build --mirror edge --arch aarch64` on ubuntu-24.04-arm, with the artifact `omarchy-trial-boot-aarch64-<sha>`.
  - linux-aurora, m1n1-aurora and mesa-aurora are untouched.
- **techmore/ElementaryOS_MSeries-Kernel** `gravity-series-validation`, commit `8a66f14`: `gravity/FIRST-BOOT-PROCEDURE.md`, the owner's attended procedure. It covers fresh-install and kernel-trial paths, success and failure signs with timings, reading the collected logs, recovery from the startup picker and first-run observations.

## Design (maclab's pieces, adapted)

| Piece | Implementation |
|---|---|
| One-shot, Limine | `LoaderEntryOneShot` (BLI GUID, NV\|BS\|RT, UTF-16) via efivarfs. U-Boot keeps variables in RAM, so `VarToFile` (magic `UbEfiVa` at +8) is written to the ESP file `RTStorageVolatile` names (`ubootefi.var`), and arm verifies the one-shot is in it. Limine's `bli.c` erases the variable when it reads it, before the boot. The trial is a top-level `/omarchy-trial` entry in a marked block at the end of `limine.conf`, so no index moves. It copies the kernel entry's options (`path: boot():/EFI/Linux/omarchy_linux-aurora.efi#hash`) and adds a `cmdline:`, which systemd-stub honours with Secure Boot off; omarchy-mac-installer's menus already use `cmdline:`. |
| One-shot, GRUB | `omarchy_trial_next` in `omarchy-trial.env` on the FAT ESP, read and cleared by a marked `custom.cfg` hook, with the entry in `/boot/grub/omarchy-trial.cfg` (btrfs subvolume paths from findmnt). Needs `41_custom`. |
| Panic | `panic=10` on the trial command line. |
| Early hang | `watchdog.open_timeout=180` (`--open-timeout`). The default owner `trial` adds `systemd.watchdog_sec=0` and the watch unit opens `/dev/watchdog0`. It feeds it while PID 1 answers (`systemctl show -p Version`), releases it with the magic close `V` on completion, and leaves it armed after a missed deadline. `systemd` owner (`systemd.watchdog_sec=30`) is the default for a stage from macOS or a foreign root, where the watch unit may be absent. |
| Deadline | `omarchy-trial-boot-watch.service`: early, `DefaultDependencies=no`, `After=local-fs.target`, `IgnoreOnIsolate=yes`, conditioned on `omarchy.trial`. The deadline is uptime-based (`omarchy.trial_deadline=900`). It runs `journalctl --sync` every 15 s and reboots with `systemctl --no-block reboot`. `-complete.service` runs after multi-user, graphical and boot-complete and runs `/etc/omarchy-trial-boot/checks.d/*`. |
| Collection | `-collect.service` on the next non-trial boot, when `pending` exists. It saves the journal, kernel log and warnings for each trial boot (from the watch unit's record, or a grep of the kernel log for the marker), `/sys/fs/pstore` and `/var/lib/systemd/pstore`, writes `summary.txt` and gives a verdict: PASSED, FAILED (deadline), CRASHED OR HUNG, NO TRIAL BOOT REACHED THE ROOT FILESYSTEM, NOT ATTEMPTED (then clears the one-shot) or HELD. |
| Refusals | `arm` refuses when: the kernel has no `apple_wdt` (modules.builtin or modules.dep of the pkgbase; `--force` overrides); `remember_last_entry: yes`; a Limine config hash is enrolled; U-Boot's file lacks the one-shot; GRUB has no 41_custom. |
| macOS | `stage --esp "/Volumes/EFI - …"` and `disarm` run on macOS bash 3.2. They can write the entry but not the one-shot, so the owner picks the entry in the Limine menu, with macOS as the startup disk serving as the firmware-level fallback. |

## Kernel and DT checks (read-only)

- `/private/tmp/claude-501/kern/linux` (`elementaryos-mseries`, 44b199b51db0): `arch/arm64/configs/asahi.config:50 CONFIG_APPLE_WATCHDOG=y`. `t8132.dtsi:565` `wdt: watchdog@3882b0000` has compatible `"apple,t8132-wdt", "apple,t8103-wdt"`, and `apple_wdt.c` matches `apple,t8103-wdt`, as U-Boot's driver does.
- omarchy-pkgs `pkgbuilds/linux-aurora/config` ("alarm-aurora"), with asahi.config merged on top by configure.sh, has:
  - `CONFIG_APPLE_WATCHDOG=y`, `CONFIG_WATCHDOG_CORE=y`, `CONFIG_WATCHDOG_HANDLE_BOOT_ENABLED=y`, `CONFIG_WATCHDOG_OPEN_TIMEOUT=0`, NOWAYOUT off;
  - `CONFIG_PSTORE=y`, `CONFIG_PSTORE_RAM=m`, `CONFIG_EFI_VARS_PSTORE_DEFAULT_DISABLE=y`, `CONFIG_EFIVAR_FS=y`, `CONFIG_PANIC_TIMEOUT=0` (hence `panic=10` on the command line).
- No config change is needed.

## Tests

`test.sh`, 20 groups (40 `ok` lines across the two CI runs), passed on macOS (bash 5, with the stage path under /bin/bash 3.2) and in CI on Ubuntu as a user and as root. It uses fixture ESPs, efivars, U-Boot variable files, mounts, a journal stand-in and real grub-editenv. CI run 41211083243 (https://github.com/techmore/omarchy-pkgs/actions/runs/41211083243): the test job passed, and the aarch64 build passed (makepkg `check()` reran the tests) and produced `omarchy-trial-boot-0.1.0-1-aarch64.pkg.tar.zst` (23 KB) as the artifact `omarchy-trial-boot-aarch64-0184a4222e25d4f88b7e409091c31c7de1997fb6`.

## Not verified on hardware (M4)

- U-Boot arming the watchdog on T8132.
- Limine on the mini consuming the one-shot, and U-Boot persisting the erase to `ubootefi.var`.
- The `cmdline:` override reaching the kernel (check `/proc/cmdline` for `omarchy.trial=`).
- Reset paths returning to the default startup disk rather than Recovery (one GPU hang landed in Recovery before Gravity 0067).
- m1n1 disarming the secondary iBoot watchdog.

The procedure lists each as a first-run observation. maclab measured one-shot clearing and recovery times on an M1 Air only.

## Caveats

- A fresh install has no Linux known-good entry. The fallback there is the macOS startup disk with a one-time pick in the startup picker. The procedure says to keep Gravity until the install passes, if the disk allows.
- Trial kernels must be installed **beside** the known-good one (their own pkgbase or UKI); trialling in place over linux-aurora gives no fallback.
- No pstore on Apple Silicon (no ramoops region), so panic text is captured only on screen. Use `--verbose` and photograph it.
- The package is unsigned (fork CI) and not promoted; `omarchy-trial-boot none` is in the Mac inventory.
