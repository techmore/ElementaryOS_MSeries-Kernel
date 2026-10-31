# First boot of a new kernel or install on the Mac mini M4 (attended)

How to boot our kernel (`techmore/linux-m1pro-touchid` `elementaryos-mseries`) or a fresh Omarchy install on the M4 Mac mini (J773g) so that **any** failure comes back to something that works, and how to read what happened. The boot chain is m1n1 stage 2 (`techmore/m1n1` `elementaryos-mseries`) → U-Boot → Limine (or GRUB) → kernel.

The tool is `omarchy-trial-boot`, in `techmore/omarchy-pkgs` branch `elementaryos-mseries-safeboot`, `pkgbuilds/omarchy-trial-boot/` (its `README.md` has the details). It follows chriskearney/maclab's method. Commit `0184a4222e25d4f88b7e409091c31c7de1997fb6`; the script's SHA-256 there is `d2a46c3f1853a3d36b44ed33a38262ef33c38efff20fb8781aeded956d8ad06f`. CI (`Build elementaryos-mseries-safeboot packages`) uploads the built package as the artifact `omarchy-trial-boot-aarch64-<commit>`. It is unsigned.

## What brings the Mac back

There are two layers. Use both.

1. **The Mac's startup disk (macOS).** While macOS is the default startup disk, every restart that Linux does not steer goes to macOS: a panic reboot, a watchdog reset, a power cut. You boot Linux by choosing it in the startup picker, which boots it **once** unless you click "Always Use". This is the only fallback on a fresh install, where no Linux kernel is known to work yet.
2. **A one-shot boot entry (`omarchy-trial-boot`).** Once one Linux kernel works, the next kernel is tried as a trial. Limine (or GRUB) clears the one-shot **before** it starts the trial, so any later restart lands on the default (known-good) Limine entry. The trial's command line adds:
   - `panic=10`: a panic reboots after 10 s.
   - `watchdog.open_timeout=180`: U-Boot leaves the hardware watchdog (`apple_wdt`) running into Linux. If nothing opens `/dev/watchdog0` within 180 s of the driver loading, the Mac is reset about 30 s later.
   - `omarchy.trial=<id> omarchy.trial_deadline=900`: `omarchy-trial-boot-watch.service` holds the watchdog. It reboots the trial unless the trial reaches boot-complete within 900 s of uptime. Boot-complete means `graphical.target` plus any checks in `/etc/omarchy-trial-boot/checks.d/`.

   On the next good boot, `omarchy-trial-boot-collect.service` saves the trial's journal and kernel log, plus any pstore records, and writes a verdict.

Both kernels build the watchdog in. `arch/arm64/configs/asahi.config` has `CONFIG_APPLE_WATCHDOG=y`, and linux-aurora's `config` has `CONFIG_APPLE_WATCHDOG=y`, `CONFIG_WATCHDOG_HANDLE_BOOT_ENABLED=y` and `CONFIG_WATCHDOG_OPEN_TIMEOUT=0`. The defaults are fine because the trial sets the timeout on the command line. `t8132.dtsi` lists the watchdog as `"apple,t8132-wdt", "apple,t8103-wdt"`, and both U-Boot's and Linux's drivers match `apple,t8103-wdt`. A kernel without `apple_wdt` would be reset about 60 s into every boot. `omarchy-trial-boot arm` refuses one.

## Before you start

- [ ] Keep macOS and the Apple Recovery partition (disk0s7). They are the fallback.
- [ ] **Do not reclaim Gravity** (`RELEASE-GATE-2026-10-31.md`, "Reclaiming") until the new install has passed its first boot, if the disk has room for both. Gravity is a second Linux that is known to work on this mini.
- [ ] Set macOS as the startup disk: System Settings → General → Startup Disk → Macintosh HD → Restart. An installer that made the new OS the default has to be undone here.
- [ ] Connect the HDMI monitor and a **wired** USB keyboard straight to the mini. Bluetooth does not work in the boot menus.
- [ ] Have a phone ready to photograph or film the screen. A panic message reaches only the screen, because these Macs have no pstore backend.
- [ ] Practise the startup picker once. Shut down. Press and hold the power button until "Loading startup options…" appears, then let go. Select a volume and click **Continue** to boot it once. "Always Use" (shown while you hold Option) changes the default; do not use it during trials.

## A. First boot of a fresh install (macOS is the fallback)

Use this when the install has no other Linux kernel. If anything fails, the Mac comes back in macOS.

1. **Optional but recommended: stage a trial entry from macOS.** This gives the first boot `panic=10`, the watchdog timeout and verbose kernel messages. In Terminal (zsh):

   ```zsh
   diskutil list                      # find the new install's EFI partition, e.g. "EFI - OMARC" on disk0s4
   sudo diskutil mount disk0s4        # use the identifier you found
   esp="/Volumes/EFI - OMARC"         # the mount point diskutil printed
   commit=0184a4222e25d4f88b7e409091c31c7de1997fb6
   curl -fsSLo "${HOME}/omarchy-trial-boot" "https://raw.githubusercontent.com/techmore/omarchy-pkgs/${commit}/pkgbuilds/omarchy-trial-boot/omarchy-trial-boot"
   shasum -a 256 "${HOME}/omarchy-trial-boot"   # must be d2a46c3f1853a3d36b44ed33a38262ef33c38efff20fb8781aeded956d8ad06f
   bash "${HOME}/omarchy-trial-boot" stage --esp "${esp}" --verbose linux-aurora
   bash "${HOME}/omarchy-trial-boot" status --esp "${esp}"
   sudo diskutil unmount "${esp}"
   ```

   This runs under macOS's bash 3.2. `stage` appends a top-level `/omarchy-trial` entry to `limine.conf`, between `# omarchy-trial-boot: begin` and `# omarchy-trial-boot: end`. The entry boots the same UKI as the `linux-aurora` entry, with that entry's command line plus the trial settings. From macOS it cannot set the one-shot, so you pick the entry by hand. Its watchdog owner is systemd (`systemd.watchdog_sec=30`), because the new root may not have the watch unit.
2. Shut down the Mac. Hold the power button, choose the Omarchy volume, and click **Continue**.
3. In the Limine menu (5 s), arrow to **omarchy-trial** and press Enter. Without step 1, let the default entry boot.
4. **Success:**
   - Kernel messages scroll past, because `--verbose` drops `quiet splash`.
   - systemd's `[  OK  ]` lines follow.
   - Omarchy's first-boot setup runs and the login or desktop appears on HDMI.

   Record the time to desktop.
5. **Failure:**
   - **Panic:** text stops on a `Kernel panic` screen, and the Mac restarts 10 s later.
   - **Hang before the desktop:** text stops and nothing happens. Within about 180 + 30 s of `apple_wdt` loading, the watchdog resets the Mac. Without the trial entry it may stay hung: hold the power button for 10 s.
   - **Black screen with no text at all:** the failure is in m1n1, U-Boot or Limine, before the kernel. This kit does not cover it. See "Recovering" below.

   Every restart lands in macOS. Photograph the last screen before it resets.
6. After a failure, the trial's logs are on the Linux root (btrfs), which macOS cannot read. Boot the install again later and run `journalctl --list-boots`, then `journalctl -b -1 -k`, as described in "Reading the logs". If the boot never reached the root filesystem, the screen photo is the only record.
7. After a success, install the kit on the new system (step B1) and remove the hand-staged entry with `sudo omarchy-trial-boot disarm`. Keep macOS as the startup disk until the new kernel has booted well at least twice.

## B. Trying a new kernel on an install that works (the trial loop)

Use this once one kernel boots. The default Limine entry is the known-good kernel; the trial is the new one.

1. Install the kit and check it:

   ```bash
   gh run download -R techmore/omarchy-pkgs -n omarchy-trial-boot-aarch64-0184a4222e25d4f88b7e409091c31c7de1997fb6
   tar -xf packages.tar && sudo pacman -U ./omarchy-trial-boot-*.pkg.tar.zst
   omarchy-trial-boot status
   ```

   `status` should show `Loader: limine (ESP /boot/efi)` and `This boot: default entry`. It should also show the watchdog as `apple_wdt` with a state, timeout and `open_timeout`, and `Panic reboot`.
2. Install the trial kernel **beside** the known-good one, never over it. Use a package with its own pkgbase, so that `limine-update` adds its own entry and UKI (for example `//linux-aurora-trial` and `EFI/Linux/omarchy_linux-aurora-trial.efi`). Or copy a UKI into `/boot/efi/EFI/Linux/` and use `--uki`. Check that the default entry is still the known-good kernel (`default_entry:` in `/boot/efi/limine.conf`, and `BOOT_ORDER` in `/etc/default/limine`).
3. Optionally add boot-complete checks, for example that the GPU came up:

   ```bash
   sudo install -Dm755 /dev/stdin /etc/omarchy-trial-boot/checks.d/10-gpu <<'EOF'
   #!/bin/bash
   [[ -e /dev/dri/renderD128 ]]
   EOF
   ```

4. Arm the trial and reboot:

   ```bash
   sudo omarchy-trial-boot arm --verbose linux-aurora-trial     # or: arm --verbose --uki EFI/Linux/<file>.efi trial
   sudo omarchy-trial-boot status    # One-shot (LoaderEntryOneShot): omarchy-trial; U-Boot variable file ...: holds the one-shot
   sudo systemctl reboot
   ```

   `arm` refuses, with the reason, in these cases:
   - the kernel has no `apple_wdt`;
   - `limine.conf` has `remember_last_entry: yes`;
   - Limine has a config hash enrolled;
   - U-Boot's variable file did not take the one-shot.

   For a boot that asks for a LUKS passphrase, add `--open-timeout 600`.
5. Leave the Limine menu alone. **omarchy-trial** should be highlighted, which proves Limine read the one-shot.
6. **Success:** the desktop appears. In a terminal, `omarchy-trial-boot status` shows `This boot: TRIAL <id>`, `result=complete` and `boot-complete: reached`. The watchdog has been released (magic close), and the deadline no longer applies. Use the system, then reboot. The next boot is the default entry again, and collect records `PASSED`.
7. **Failure:** watch the screen and photograph the last messages. The Mac comes back on the default entry without help:

   | What happened | When it restarts |
   |---|---|
   | Kernel panic | 10 s after the panic |
   | Kernel hard lockup after `apple_wdt` loaded | within 30 s |
   | Stuck before the root filesystem (initramfs, root device) | about 180 + 30 s after `apple_wdt` loaded |
   | Up but no desktop, failed units or a failed check | at 900 s of uptime |
   | PID 1 stopped answering | about 60 s later |
   | Hang before `apple_wdt` loads | within 60 s of Limine starting the kernel (U-Boot's timeout) |

   To debug at the console instead, run `sudo omarchy-trial-boot hold` on the trial boot. This stops the deadline and releases the watchdog.
8. Back on the default entry, collect has already run at boot. Run `sudo omarchy-trial-boot status` to see every trial's verdict, and read the summary as described in the next section.
9. After a trial has `PASSED` at least twice, make that kernel the default (`BOOT_ORDER` / `default_entry`, or install it as the main kernel package). Then run `sudo omarchy-trial-boot disarm` to remove the trial entry.

## Reading the logs

Everything for trial `<id>` is in `/var/lib/omarchy-trial-boot/trials/<id>/collected-<time>/`, readable by root only:

```bash
sudo ls /var/lib/omarchy-trial-boot/trials/
sudo cat /var/lib/omarchy-trial-boot/trials/<id>/collected-*/summary.txt
sudo less /var/lib/omarchy-trial-boot/trials/<id>/collected-*/kernel-<boot>.txt
```

- **`summary.txt`:** the verdict, the error lines from the trial (panics, oopses, `BUG:`, call traces, watchdog, hung tasks, RCU stalls, failed units), and the trial's last 15 journal lines.
  - `PASSED`: the trial reached boot-complete.
  - `FAILED: MISSED THE DEADLINE`: the trial booted but did not reach boot-complete in time. Look for `Failed to start` in `journal-<boot>.txt` and run `systemctl --failed` on the next trial.
  - `CRASHED OR HUNG`: the trial reached the root filesystem, then restarted without a result. It panicked (`panic=10`) or the watchdog reset it. The journal ends at the last write that reached the disk; the watch unit syncs it every 15 s, and writes from the final 1–2 s before a panic are lost. The panic text itself is on your photo.
  - `NO TRIAL BOOT REACHED THE ROOT FILESYSTEM`: the trial stopped in the kernel, the device tree or the initramfs. Nothing is on disk. Boot it again with `--verbose` and film the screen.
  - `NOT ATTEMPTED`: Limine never took the one-shot (Limine too old for `LoaderEntryOneShot`, or U-Boot did not load `ubootefi.var`). Collect has already cleared it, so the next boot is not a surprise trial.
- **`kernel-<boot>.txt`:** the trial's kernel log, with monotonic timestamps. Search for the first `Oops`, `panic`, `Call trace` or `Unable to handle`. For M4 drivers, run `grep -n -i 'asahi\|dcp\|apple\|t8132' kernel-<boot>.txt`.
- **`warnings-<boot>.txt`:** priority warning and above, from the whole trial boot.
- **`journal-<boot>.txt`:** the trial's full journal.
- **`boot-<boot>.env`:** what the watch unit recorded: when it started, whether it held the watchdog, and the result with its uptime.
- **`pstore/`:** this is usually absent. These Macs have no ramoops region, and EFI pstore would land in U-Boot's RAM store.

Without the kit, for example on a fresh install's first boot, use `journalctl --list-boots`, then `journalctl -b -1 -k -o short-monotonic` and `journalctl -b -1 -p warning`.

## Recovering from the macOS startup picker

- **The Mac is hung:** hold the power button for 10 s until it turns off.
- **Boot macOS:** press and hold the power button until "Loading startup options…" appears. Choose Macintosh HD and click Continue. To make macOS the default again, use System Settings → General → Startup Disk, or hold Option in the picker and click "Always Use".
- **A reset landed in macOS Recovery:** this happened once on this mini after a GPU hang, before Gravity patch 0067 added the SMC reboot cell. In Recovery, use Apple menu → Startup Disk → choose the volume → Restart. Or just Restart, which goes to the default startup disk.
- **The Linux volume starts but the screen stays black, or the Mac returns to the picker:** the failure is in m1n1 stage 2, U-Boot or Limine, before the kernel, and this kit does not cover it. In macOS, mount the install's ESP (`sudo diskutil mount disk0sN`). Restore the previous `m1n1/boot.bin` if you kept a copy before updating it. If U-Boot reports errors loading EFI variables, put back `ubootefi.var.pre-omarchy-trial` as `ubootefi.var`, or delete `ubootefi.var` (U-Boot then starts with no variables, and Limine boots its default).
- **`limine.conf` is wrong after a trial:** in macOS, run `bash "${HOME}/omarchy-trial-boot" disarm --esp "${esp}"`, or delete the lines from `# omarchy-trial-boot: begin` to `# omarchy-trial-boot: end`.
- **The Linux volume is gone from the picker, or the boot policy is broken:** boot Recovery (picker → Options). Rerun the installer's recovery step, or remove the stub container from macOS (`diskutil apfs deleteContainer`). macOS itself is not affected.

## Not yet observed on the M4

These steps were read from source and from maclab's measurements on M1/M3 machines. Record each one the first time you see it:

- U-Boot prints `WDT: Started watchdog@... with servicing (60s timeout)` on the M4.
- A `panic=10` restart and a watchdog reset both come back through iBoot to the default startup disk, and do not go to Recovery.
- Limine on the mini reads and clears `LoaderEntryOneShot`, and U-Boot saves the cleared state to `ubootefi.var`. `omarchy-trial-boot status` on the trial boot shows `Booted entry (LoaderEntrySelected): omarchy-trial` and `One-shot: none`.
- The trial's `cmdline:` overrides the UKI's built-in command line. `cat /proc/cmdline` on the trial shows `omarchy.trial=`. If it does not, the trial ran without `panic=10` and without the deadline unit; report it.
- m1n1 disarms the M4's secondary iBoot watchdog, so a slow boot is not reset at 120 s.
