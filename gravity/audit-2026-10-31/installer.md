# Omarchy Mac installer fork for the M4 Mac mini (J773g): audit

Date: 2026-10-31. Report and drafts only: nothing was forked, pushed or posted.
Working copies are in `/private/tmp/claude-501/kern/audit/installer/`:
`omarchy/` (omacom/omarchy-mac-installer `main`, local branch `audit/j773g-draft` with the
draft edits applied, not committed), `gravity/` (GravityLinux/installer), `asahi/`
(AsahiLinux/asahi-installer at the pinned `dffbb38`, Omarchy patch applied, plus the J773g edit),
`m1n1-ours/` (techmore/m1n1 `elementaryos-mseries`, shallow), `mesa/` (sparse omacom/mesa at
the mesa-aurora pin), `pkgs/` (omacom/omarchy-pkgs PKGBUILDs, a=original, b=draft).

Draft diffs (`installer/NN-*.diff`):

| File | What |
|---|---|
| `01-engine-main-py-j773g.diff` | asahi `src/main.py` (as patched): `CHIP_MIN_VER[0x8132]`, `DEVICES["j773gap"]`, `j773gap` on the 26.6.2 IPSW |
| `01b-engine-runtime-patch-regenerated.diff` | the same change as a diff of `Engine/patches/0001-omarchy-engine-runtime.patch` (regenerated with `git diff`; also adds `index` lines to the osinstall hunk) |
| `02-admit-j773g-models-catalog.diff` | `scripts/supported-models.json` (`developer` board), `MacModelNames.swift`, a developer release-inputs template |
| `03-engine-board-stage1-j773g.diff` | `omarchy_asahi.py` `BOARD_STAGE1["j773gap"]` |
| `04-image-builder-j773g.diff` | candidate policy `device_trees += t8132-j773g`, `build-mac-image` stages `esp/aurora/stage1-j773g.bin`, inspection checks it |
| `05-omarchy-pkgs-pkgbuilds.diff` | `linux-aurora`, `m1n1-aurora`, `mesa-aurora` re-pinned to our kernel, our m1n1 and aurora-silicon Mesa |
| `06-install-timing.diff` | wall-clock phase records, ESP copy of the timing log, app launch mark, first-boot Linux timing unit |

Checks run: the engine overlay suites `test_omarchy_asahi`, `test_omarchy_firmware`,
`test_omarchy_stage1` and `test_omarchy_image` pass with the drafts applied (170 + 8 tests).
`bash -n` passes on the builder and the timing script. The Swift changes were **not compiled**:
the sandbox refused `swift build`. No image, engine archive or app was built.

---

## 1. How the installer works today

**Is this Mac supported?** There are three gates, applied in order:

1. **App, before reading any catalog.** `AppleSiliconHostInspector` reads `hw.targettype` and
   makes it `apple,<target>` (`Sources/OmarchyAppleInstaller/MacHostInspection.swift:119-138`).
   It refuses only `explicitlyUnsupportedDevices = ["apple,j614s"]` (the same list is in
   `InstallerAssetPreparer.swift:114`, `ClosedEngineHelperServer.swift:130`,
   `ClosedEngineProcessAdapter.swift:75` and `OmarchyRemovalDiskOperator.swift:42`). For any
   other Mac the result is `.requiresSignedCatalog`, so `apple,j773g` already passes this gate.
2. **Signed catalog.** The catalog's `models[].deviceIdentifier` with `status: enabled` decides
   which Macs get an image. `scripts/supported_models.py` and `scripts/make-unsigned-catalog.py`
   require a channel catalog to enable exactly the 35 boards in `scripts/supported-models.json`.
   `developer` boards are allowed only in a developer build's sealed catalog
   (`make-unsigned-catalog.py --developer`, `developer_models` groups, lines 178-226). The
   catalog is verified with the Ed25519 `Release/trust-root.ed25519.pub`. `Packaging/build-app.sh`
   embeds a sealed `catalog.json` + `.sig` (lines 98-142), and `OMARCHY_DEVELOPER_BUILD=1` builds
   require one.
3. **Engine** (asahi-installer v0.9.2 plus `Engine/patches/0001-omarchy-engine-runtime.patch`
   plus `Engine/overlay/src`). In `main.py`, `CHIP_MIN_VER` (keyed by chip id) and `DEVICES`
   (keyed by `device_class`, for example `j700ap`) must both match. Otherwise the engine reports
   `supported=False` to `omarchy_runtime.inspect` and stops (patch hunk at `main.py` `@@ -970`).
   The app runs the same pinned engine as its inspection engine, generated from
   `Engine/source-lock.json` (`ValidationEngineArtifact.swift`, `OmarchyEnginePinGenerator`). So a
   new board needs a new engine archive, not only a new catalog.

**Which macOS stub and firmware (IPSW).** `IPSW_VERSIONS` in the patched `main.py` adds 26.6
(`j700ap`) and 26.6.2 (`j613ap`, `j615ap`, `j700ap`; 25G83 restore image). The selection logic
moved to `Engine/overlay/src/omarchy_firmware.py`:

- `available_ipsws()` keeps the versions at or above max(chip minimum, device minimum) that are
  also in the payload's `supported_fw` and list this `device_class`. It then filters them by this
  Mac's iBoot, macOS and SFR versions.
- The non-expert install takes the last remaining version.
- `stub_size()` makes a 6 GB stub (`STUB_SIZE_MACOS26`) whenever the chip minimum is 26.0 or later.

The image's `installer_data.json` carries `supported_fw: 13.5 14.8.3 26.6.2`
(`image-builder/bin/build-mac-image:36`). macOS 26 recoveryOS and ExclaveOS archives are AEA
encrypted. The app's signed `omarchy-restore-image` helper decrypts them with Apple's FCS
release keys (`omarchy_apple_aea.py`, `Engine/RestoreImage`), so the host's macOS version does
not matter.

**m1n1 Stage 1 and Stage 2.**

- **Asahi Stage 1:** `Engine/build-locked-engine.sh:144-148` builds the pinned
  `AsahiLinux/m1n1@06a4601` with `RELEASE=1 CHAINLOADING=1` into the engine.
- **Aurora Stage 1:** boards in `BOARD_STAGE1` (`omarchy_asahi.py:437-449`; `j700ap`, and
  `j613ap` on 26.6.2 only) get Aurora's raw Stage 1 from the payload's `esp/aurora/stage1-*.bin`
  instead. `fill_aurora_stage1` fills its `AURORA-S1-CFG01` block (ESP PARTUUID and Stage 2 path)
  and `install_board_stage1` writes it as the boot object.
- **Stage 2:** this is the image's `esp/m1n1/boot.bin`. `update-m1n1` builds it as m1n1-aurora
  Stage 2, then every linux-aurora DTB in C order, then uboot-aurora and `/etc/m1n1.conf`.
  Per-board replacements are in `BOARD_STAGE2` (`omarchy_asahi.py:540`).

**Image and packages.** `image-builder/bin/build-mac-image` (described in `docs/image-producer.md`)
builds an Arch Linux ARM root containing:

- the Omarchy runtime (`omarchy`, `omarchy-settings`, `omarchy-mac`, `omarchy-mac-boot`)
- a signed boot candidate set: `linux-aurora`, `linux-aurora-headers`, `m1n1-aurora`,
  `uboot-aurora` and `limine-mkinitcpio-hook`, built from omacom/omarchy-pkgs and verified
  against `image-builder/builder/candidate-trust/policy.json` (trust only from the repository)
- the support packages `mesa-aurora`, `vulkan-aurora`, `aurora-audio`, `omarchy-aurora-firmware`
  and others
- Limine behind m1n1 and U-Boot, as a UKI `omarchy_linux-aurora.efi`

The payload zip holds `boot.img`, `root.img` and the `esp/` tree, plus `installer_data.json`.

## 2. Every place a fork must change

| # | Place | Change | Draft |
|---|---|---|---|
| a | patched asahi `main.py` | `CHIP_MIN_VER[0x8132]="26.6.2"`; `DEVICES["j773gap"]=Device("26.6.2")`; add `j773gap` to the existing 26.6.2 IPSW entry. The stub automatically becomes 6 GB. | 01, 01b |
| b | `omarchy_asahi.py` `BOARD_STAGE1` | `"j773gap": BoardStage1("esp/aurora/stage1-j773g.bin", 0, "26.6.2", …)`. No `BOARD_STAGE2` entry is needed: the common `boot.bin` carries `t8132-j773g.dtb`. | 03 |
| c | `Engine/source-lock.json` | New sha256 values for the patch and changed overlay files, a new `downstream_overlay.version`, and the new archive's `validation_artifact` (`Engine/rebuild-python-overlay.py` from the authenticated `.28` base, then `verify-source-lock.py`). The app's engine pin is generated from this file. | (to regenerate) |
| d | `scripts/supported-models.json` | `apple,j773g` under `developer`, the same way the Neo first entered (merge `11c36ef`). It is not added to `supported`, because then every channel catalog would have to offer our J773g-only image to all 35 Macs. | 02 |
| e | `MacModelNames.swift` | `"apple,j773g": "Mac mini (M4, 2024)"` | 02 |
| f | Catalog and signing | Generate our own Ed25519 catalog key and `trust-root.ed25519.pub` with `release.json` (Release inputs). Run `make-unsigned-catalog.py --developer` with `scripts/release-inputs-j773g-developer.template.json`, then `catalog-signing.swift sign-keychain`. Build with `OMARCHY_DEVELOPER_BUILD=1` (+`OMARCHY_OFFLINE_BUILD=1` to embed the image), then `Packaging/build-developer-pkg.sh` (ad hoc, local only). | 02 |
| g | Image builder | Add `t8132-j773g` to `device_trees`, stage `stage1-j773g.bin` and inspect it. For our own candidate set, replace the candidate-trust key (`policy.json` fingerprints, `public.asc`) and set `boot_repository` to our package repository. | 04 |
| h | Packages | `linux-aurora` → techmore/linux-m1pro-touchid `cfd21dd`; `m1n1-aurora` → techmore/m1n1 `d896f4e` (move `build-qualification.json` too); `mesa-aurora` → aurora-silicon/mesa `aurora-wip` `68e7b67`. Set higher versions so the channel never replaces them. Recompute Mesa's `pkgver` count (it is a placeholder). | 05 |
| i | Optional | Allow `-nca` (custom boot arguments) for `j773gap` in `omarchy_asahi.py` (step2 script, line ~408) and `omarchy_recovery.py:215`, as the Neo does, for USB proxy debugging. | – |

**The IPSW pin compared with Gravity.** Both use the same restore image,
`UniversalMac_26.6.2_25G83_Restore.ipsw` (`gravity/src/main.py:38-44`). Gravity's entry is
`IPSW("26.6.2","26.5","0","0")`: it requires macOS 26.5 and does not check iBoot or SFR.
Omarchy's entry requires `mBoot-18000.161.10` and SFR `25.7.83.0.0,0`, which a mini on macOS 27
exceeds. Gravity decodes `022-22048-093.dmg.aea` with `/usr/bin/aea` against a pinned key
(`src/recovery.py`); Omarchy uses its FCS-key decoder, which already serves 26.6.2 for the Neo
and the M3 Airs. The only extra work for J773g is adding it to the device list.

**m1n1 for M4.** Gravity needed two fixes:

- `NO_DISPLAY=1`, because asahi's Stage 1 DCP init crashes the T8132 display firmware
  (Gravity commit 486e81b).
- Boot objects padded to 64 KiB for T8132 kmutil registration (Gravity commit 517c72a).

Our m1n1 already returns early from `display_init`/`display_shutdown` on T8132 (`src/display.c`
lines 276, 767 and 803). Its raw Stage 1 ends at STACKBOT and is 64 KiB aligned
(`m1n1-raw.ld` asserts `ALIGN(0x10000)`). So J773g must use the Aurora raw Stage 1 path (entry
b), never asahi's Stage 1 with appended variables. This still needs a hardware check.

## 3. Getting our kernel, m1n1 and Mesa into the image

**Exists:**

- **Kernel.** Our tree has `arch/arm64/boot/dts/apple/t8132-j773g.dts`. The linux-aurora
  PKGBUILD builds `Image modules dtbs` and installs every apple DTB, so re-pinning the PKGBUILD
  is enough.
- **m1n1.** Our m1n1 has T8132 support and J773g GPU, PMP and NVMe handoff (`d896f4e`). The
  m1n1-aurora PKGBUILD already builds both the raw Stage 1 and Stage 2.
- **Mesa.** aurora-silicon/mesa `aurora-wip` admits G16G for chip `0x8132` (commit
  `662048cacc83`).

**Missing or blocking:**

- **Mesa (blocker).** The channel's `mesa-aurora` (omacom/mesa `672657e`) refuses M4.
  `src/asahi/lib/agx_chip.c` `agx_params_driver_supported()` returns false for
  `chip_id == 0x8132` (and `0x6040`), so the desktop would fall back to llvmpipe. We must build
  mesa-aurora from aurora-silicon/mesa `aurora-wip` and match its DRM UAPI to our kernel.
- **No pacman packages.** The kernel CI artifact (`elementaryos-mseries-kernel.yml`) is
  `Image`, modules, two DTBs and the config. It is not a package, has no headers, and its
  `LOCALVERSION` is `-elementaryos-mseries`. We need a package repository (or a local candidate
  set) with linux-aurora, linux-aurora-headers, m1n1-aurora and mesa-aurora/vulkan-aurora, signed
  by our key, with the image builder's trust policy pointed at it.
- **Display and HDMI driver.** Per the release gate this is not done yet. Until it is, the
  desktop relies on the iBoot framebuffer that m1n1 preserves (simpledrm, iBoot's mode), with
  the GPU render node separate.
- **Wi-Fi/Bluetooth.** The pinned `asahi_firmware` has no J773g aliases and no per-radio
  calibration. Gravity added them in `gravity_firmware/wifi.py` `MACHINE_ALIASES["j773g"]`
  (BCM4388 "sakhalin") and `radio_calibration.py`. Use Ethernet for the gate.

**Lab shortcut (plan B):** take a published edge payload, run `pacman -U` with our three
packages in a chroot of `root.img`, run `mkinitcpio -P`, `update-m1n1` and the Limine/UKI
refresh, add `esp/aurora/stage1-j773g.bin`, then re-zip and sign a developer catalog over the
new digests. This skips the builder's inspection.

## 4. Install-speed timing (draft 06)

**macOS side:**

- `omarchy_image.timing()` already writes `PERFORMANCE` JSON per phase to
  `OMARCHY_PERFORMANCE_LOG` (set to `<transcript>.performance.jsonl` in
  `PinnedAsahiEngineExecutor.swift:290`). The phases are `prepare_target`,
  `install_stub_and_esp`, `prepare_recovery_handoff`, `image_write`, `image_flush` and
  `image_readback`.
- Draft 06 adds UTC `started_at` and `ended_at` fields and a `mark()` helper.
- `mirror_to()` is called in `install_stub_and_esp` for each `idata_targets` directory, so the
  log so far, and every later record, lands on the new ESP as
  `/boot/efi/asahi/install-timing.jsonl` (next to the `installer.log` the engine already copies).
- `prepare_recovery_handoff` marks `recovery_handoff_begin`.
- `InstallerPerformance` (Swift) now also appends wall-clock records to
  `~/Library/Logs/omarchy-installer-timing.jsonl` (or `/var/log/…` for the root helper), and the
  app marks `app_launched` in `applicationDidFinishLaunching`.

**Linux side:**

- `build-mac-image` `stage_install_timing` installs `omarchy-install-timing` and a oneshot
  service. On first boot the service merges the ESP log into
  `/var/log/omarchy/install-timing.jsonl` and records `linux_first_boot` (`uname -r`,
  `systemd-analyze`).
- `omarchy-install-timing desktop` (a Hyprland `exec-once`) records `desktop_ready` with the EGL
  renderer, which also shows whether the GPU or llvmpipe is in use.
- `omarchy-install-timing claude` records Claude Code answering.

**Gaps:**

- The Recovery step-2 duration is visible only as the gap between the handoff mark and first boot.
- The app's user log stays in macOS. Copy it, or read it from macOS.
- The `exec-once` line is not in the draft.

## 5. Blockers and ordered plan

**Blockers:**

1. Mesa M4 refusal in the channel pin (use aurora-silicon `aurora-wip`).
2. No signed package repository or candidate set for our kernel, m1n1 and Mesa.
3. A new engine archive and source-lock are required, because the app's inspection engine
   refuses `j773gap`.
4. Our own catalog trust root and a developer build are required.
5. Kernel display/HDMI is not done.
6. Unverified on hardware: our raw Stage 1 boots on 26.6.2 iBoot (64 KiB, no DCP init); the
   app and engine run on macOS 27 (26A5421a); the kernel and Mesa UAPI match.

**Plan:**

1. Build packages from draft 05 (Arch aarch64 builder) into our signed repository, and boot-test
   the kernel and m1n1 by hand on Gravity's existing ESP before reclaiming the disk.
2. Apply drafts 01-03, regenerate the patch and `source-lock.json`, rebuild the engine overlay,
   and run `test/all` plus the engine tests.
3. Apply draft 04 plus our candidate trust key. Build the J773g image (or use the plan B
   repack). Check that `INSPECTION` passes and the payload carries `stage1-j773g.bin` and
   `t8132-j773g.dtb`.
4. Make our catalog key, a developer sealed catalog (draft 02 template) and an
   `OMARCHY_DEVELOPER_BUILD=1 OMARCHY_OFFLINE_BUILD=1` app, then the developer package.
5. Apply draft 06 timing.
6. The owner backs up Gravity, reclaims the disk (release-gate commands), installs, and walks
   the gate checklist. Repeat twice for timing.
7. Then add Wi-Fi/BT (port Gravity's J773g aliases and calibration) and HDMI native mode.
