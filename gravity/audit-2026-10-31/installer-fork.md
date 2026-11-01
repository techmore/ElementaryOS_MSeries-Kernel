# Omarchy Mac installer fork for the M4 Mac mini (J773g)

Date: 2026-10-31.

- **Fork:** https://github.com/techmore/omarchy-mac-installer (forked from omacom/omarchy-mac-installer)
- **Branch:** `elementaryos-mseries`, cut from upstream `main` at `982094e`. Head: `b43d033`.
- **Local clone:** `/private/tmp/claude-501/installer/omarchy-mac-installer`
- **Upstream:** nothing was opened or posted (no PRs, issues or comments), and no repository settings were changed.

Commits are authored as `techmore <9263712+techmore@users.noreply.github.com>`, with a Claude co-author line.

## Commits (oldest first)

| Commit | What it does |
|---|---|
| `020f3b9` | **Engine admits `j773gap`.** Draft 01b: the regenerated runtime patch adds `CHIP_MIN_VER[0x8132]="26.6.2"` and `DEVICES["j773gap"]`, and adds `j773gap` to the existing 26.6.2/25G83 IPSW entry. This gives a 6 GB stub. Firmware tests were added for the mini: it takes 26.6.2, a newer macOS still takes 26.6.2, and a payload without 26.6.2 offers no firmware. |
| `11d45ab` | **Developer catalogs admit `apple,j773g`.** Draft 02: the `developer` entry in `supported-models.json`, `MacModelNames`, and the developer release-inputs template. The catalog test is updated. |
| `0dcb41e` | **Raw Stage 1 for the mini.** Draft 03: `BOARD_STAGE1["j773gap"]` uses `esp/aurora/stage1-j773g.bin` on 26.6.2. Tests cover filling the block and refusing a missing or invalid Stage 1. |
| `4fa5213` | **`-nca` for `j773gap` (optional item i).** Kept, because the audit's reasoning holds: our m1n1 reads `aura-proxy` and `aura-debug` from iBoot boot-args (`src/boot_options.c`), and with no T8132 display driver the USB proxy is the bring-up path. The allowed boards are now one set, `omarchy_recovery.CUSTOM_BOOT_ARGUMENT_BOARDS`. Tests were added and `Recovery/README.md` updated. |
| `4e811b3` | **Image builder.** Draft 04: the policy requires `t8132-j773g`, the builder stages `stage1-j773g.bin`, and inspection checks it. `mac-image-check` now also requires the member and that it equals the J700 Stage 1, keeping the checker in step with the engine. Fixtures, counts (35→36) and engine-contract tests were updated. |
| `6f53739` | **Install timing.** Draft 06, with fixes. The ESP copy is registered before it is written, so it is created 0644. The Linux log is root:wheel 0664 in a 0775 directory, not 1777, so the user session can append, and the directory's group is set in the target chroot. First boot is idempotent by phase rather than by file presence. There is a `uptime` override for tests, Python tests (`TimingTests`) and a shell test, and `swift-format` fixes. |
| `4935d68` | **Coordinator item: desktop and Claude Code timing.** Omarchy quattro's Hyprland config is Lua and has no `exec-once` line, so the "exec-once" is a post-boot hook in `/etc/skel/.config/omarchy/hooks/post-boot.d/50-install-timing`, which Hyprland's start handler runs through `omarchy-hook post-boot`. It records `desktop_ready` and starts `omarchy-first-login-claude-code` in the background. That script runs `curl -fsSL https://claude.ai/install.sh \| bash`, retries 20×15 s and again at the next login, then records `claude_code_answering` once. To opt out: `~/.config/omarchy/no-claude-code`, delete the hook, or build with `first_login_claude_code=0`. Tested with fakes. |
| `792dab9` | **Coordinator item: Wi-Fi/BT (new overlay module `omarchy_j773g_radio`, `j773gap` only).** (a) Wi-Fi firmware is read from macOS 26 Recovery's `AppleBCMWLAN.dext/Firmware` first; the upstream path `usr/share/firmware/wifi` is empty there. (b) Machine-scoped plain aliases `brcmfmac4388{c0,c2}-pcie.{bin,txt,clm_blob,txcap_blob,sig}` point at Gravity's qualified sakhalin files (WLMT/USI/X0). (c) The factory BWCl `WCAL`/`BTBF` calibration is bound to the `/chosen` addresses and stored as `brcm/brcmfmac4388-<addr>-cal.bin` and `brcm/brcmbt4388-<addr>-bf.bin`. Records that disagree are refused, and each radio stands alone. All failures are warnings, because Ethernet is the network. 11 module tests and 4 adapter tests. |
| `ea6f65f` | **Engine pin `v0.9.2-omarchy.20261031.e937542d0809`.** Archive `installer-v0.9.2-omarchy.20261031.e937542d0809.tar.gz`, 17,907,304 bytes, sha256 `57384034…c9f3`. |
| `b21ff9a` | **Developer trust root and guide.** `Release/developer-j773g/{trust-root.ed25519.pub,release.json}` (public half only, ad hoc descriptor). The template's main group shares the J773g payload, so no edge payload is needed. Adds `docs/j773g-developer-build.md`. The identity test exempts the generated descriptor and checks that it regenerates exactly. |
| `b43d033` | **Coordinator item: debug SSH.** The image carries only `openssh`, `omarchy-ssh-debug`, its unit and `/etc/omarchy/ssh-debug.conf` (`GITHUB_USER=techmore`). It carries no key, no authorized_keys and no enabled sshd, so the lab-access scan passes (tested). Details are under "Debug SSH" below. |

## Debug SSH

The first-boot oneshot `omarchy-ssh-debug.service` runs after `network-online.target`. It retries 30×10 s, then every minute through `Restart=on-failure`, until the marker `/var/lib/omarchy/ssh-debug/done` exists.

What it does:

1. Waits for the first user: the lowest UID ≥1000 with a login shell.
2. Fetches `https://github.com/techmore.keys` and validates each line: a known key type, a blob that carries the same type, no options, and `ssh-keygen -l` accepts it.
3. Appends new keys to `~/.ssh/authorized_keys` (directory 0700, file 0600, owned by the user). Keys the user added are never changed or duplicated, and it refuses to follow symlinks.
4. Writes `/etc/ssh/sshd_config.d/20-omarchy-ssh-debug.conf` with `PasswordAuthentication no`, `KbdInteractiveAuthentication no`, `PermitRootLogin no` and `PubkeyAuthentication yes`.
5. Requires `sshd -t` to pass and `sshd -T` to show all four settings, then runs `systemctl enable --now sshd`.
6. Sets up mDNS: Omarchy already ships `avahi-daemon` and `nss-mdns`, and resolved's `MulticastDNS=yes` is the fallback.
7. Opens the firewall: `ufw limit 22/tcp` and `ufw allow 5353/udp` (Omarchy's UFW denies incoming by default).
8. Logs to `/var/log/omarchy/ssh-debug.log` and records `ssh_ready` (user, GitHub user, key count) in the install-timing log.

To opt out, do any of these:

- `touch /etc/omarchy/no-ssh-debug`
- create `omarchy-no-ssh-debug` at the ESP root from macOS before the first boot
- build with `ssh_debug=0` (`ssh_debug_github_user` is the setting for the GitHub account)

It is documented in `image-builder/README.md#debug-ssh-developer-image` and tested by `image-builder/test/ssh-debug-test.sh` (8 checks).

## Test results (macOS, Darwin 27.0, Python 3.14.3, Bash 5.3.20 from Homebrew, Swift 6.3.2 Command Line Tools)

- **`bash test/all`: pass.** It needs Bash 5 (macOS `/bin/bash` is 3.2): `PATH=/opt/homebrew/bin:$PATH bash test/all`. The engine overlay suite ran 415 tests, all OK (1 skipped). One recovery test compiles C through `xcrun`: inside the sandbox, `xcrun` could not locate the macOS SDK. Outside the sandbox it passes.
- **`bash image-builder/test/all`: pass.** This covers candidate, channel, inspection, mac-image-check, the engine contract, release guard, and the install-timing and ssh-debug shell tests.
- **Engine:**
  - `verify-source-lock.py` passes against the locked asahi checkout.
  - `engine_pin.py check` passes.
  - `prepare-engine.py` reproduced the archive twice byte-identically, and archive modes and Mach-O verification passed.
- **Swift:**
  - `swift build` (debug) and `swift build -c release`: build complete.
  - `swift format lint --strict -r Sources Tests`: clean.
  - **`swift test`: not run.** `XCTest` is missing because only the Command Line Tools are installed, and `xcodebuild` needs Xcode. AGENTS.md asks for Swift tests in debug and release through XcodeBuildMCP, so that requirement is still open.
- **Structural dry run:** an `OMARCHY_DEVELOPER_BUILD=1 Packaging/build-app.sh` run with a sealed catalog signed by the new key built and validated an ad hoc app. The catalog used a random 1 MB stand-in payload in scratch only, and the app was deleted afterwards. That catalog is not a deliverable, and no payload digest was committed.
- **CI:** none ran. `checks.yml` runs only on pushes and PRs to `main`, and `mac-app-release.yml` only on `v*` tags. Actions are enabled on the fork, but nothing triggers for this branch, and no run was dispatched.

## Built vs not built

**Built:**

- The engine archive, at `/private/tmp/claude-501/installer/engine-artifacts/` and in the clone's `Engine/artifacts/` (gitignored).
- Debug and release Swift builds.
- The developer catalog key:
  - private key: `/private/tmp/claude-501/keys/j773g-developer-catalog.ed25519` (0600, outside the repo; checked absent from git as both hex and base64)
  - public key: `/private/tmp/claude-501/keys/j773g-developer-catalog.ed25519.pub`
  - fingerprint: `sha256:e983d95d1fa6e82ae6bdb10c5fef77e13a4c074e6d370b4aeaecafbb29c3e379`
- The locked asahi checkout, at `/private/tmp/claude-501/installer/asahi-locked`.

**Not built:**

- The packages (kernel, m1n1 and Mesa from techmore/aurora-silicon).
- The signed candidate set or package repository.
- The J773g image payload.
- The sealed developer catalog.
- The developer app with an embedded payload, and its `.pkg`.
- The engine GitHub release (`engine-<version>`), which only channel catalogs need.

Nothing was installed or run on the Mac.

## Remaining steps to a runnable developer app and payload

The exact commands are in `docs/j773g-developer-build.md` on the branch.

1. **Packages.** Build `linux-aurora` and its headers (techmore/linux-m1pro-touchid), `m1n1-aurora` (techmore/m1n1) and `mesa-aurora`/`vulkan-aurora` (aurora-silicon/mesa `aurora-wip`) from the draft-05 PKGBUILDs on an aarch64 Arch builder, with versions above the channel's.
2. **Candidate set.** Sign the candidate set with our own GPG key using omarchy-mac-pkgs' candidate-set tool. Then, in `image-builder/builder/candidate-trust/policy.json`:
   - set `boot_repository` to our PKGBUILD fork (for example `techmore/omarchy-pkgs`)
   - set `primary_fingerprint`, `signing_fingerprint` and `public_key_sha256` to our key's
   - replace `public.asc` with our public key
   - add our repository to `source_repositories`/`platform_repositories` only if the runtime packages are not built from omacom commits
3. **Image.** Run `mac-image-inputs resolve`, then `build-mac-image --candidates`, then `mac-image-check payload edge …`. `INSPECTION` must pass, and the payload must contain `stage1-j773g.bin` and `t8132-j773g.dtb`.
   - **Fallback (lab shortcut):** repack an edge payload. `pacman -U` our packages in a chroot of `root.img`, run `mkinitcpio -P` and `update-m1n1`, refresh the UKI, copy the raw Stage 1 to `esp/aurora/stage1-j773g.bin`, re-zip, then run `mac-image-check`. Treat the result as lab-only.
4. **Sealed developer catalog.**
   - Copy the engine archive, the payload, `installer_data.json` and the same file as `installer_data-j773g.json` into an assets directory.
   - Edit the template copy: set `downstream_revision` to the pushed commit, and set the payload name.
   - Run `make-unsigned-catalog.py --developer`.
   - Sign with `swift scripts/catalog-signing.swift sign /private/tmp/claude-501/keys/j773g-developer-catalog.ed25519 …`, then run `verify` against `Release/developer-j773g/trust-root.ed25519.pub`.
5. **App and package.** Put `Release/developer-j773g/*` plus `catalog.json` and `.sig` in a release directory, with an `offline-artifacts/` folder holding the engine, metadata and payload. Run `OMARCHY_DEVELOPER_BUILD=1 OMARCHY_OFFLINE_BUILD=1 Packaging/build-app.sh RELEASE OUT`, then `Packaging/build-developer-pkg.sh APP OUT.pkg`. The result is ad hoc signed and for local use only.
6. **Swift tests on a Mac with Xcode.** Run them in debug and release (`swift test` / XcodeBuildMCP).
7. **Owner at the Mac.** Install the `.pkg` (it registers the helper), back up Gravity, reclaim the disk, install, then walk the gate checklist. The timing logs are `~/Library/Logs/omarchy-installer-timing.jsonl`, ESP `asahi/install-timing.jsonl` and `/var/log/omarchy/install-timing.jsonl`.

Shell note: macOS's login shell is zsh, so use `${var}` (not `$var:x`) when pasting. `/bin/bash` is 3.2, and the repo's test scripts need Homebrew's Bash 5.

## Known gaps and risks

- **Radio calibration has no consumer yet.** `hci_bcm4377` refuses to probe without `brcm,taurus-bf-cal-blob`, so Bluetooth stays off. `brcmfmac` runs without `brcm,cal-blob`, likely with degraded TX. The J773g ADT carries neither (no `wifi-calibration-msf`; macOS has it in FDR, as `wifi-calibration-fdr`). The engine now packages both blobs, but neither our kernel nor uboot-aurora reads them. Gravity's U-Boot injects them. Needed: a U-Boot loader for `vendorfw/…/brcm*-<addr>-{cal,bf}.bin`, or a kernel fallback through `request_firmware`.
- **Wi-Fi firmware names.** These are unverified until the first boot: the kernel picks `4388c2` for chip revision 6 and `4388c0` otherwise, and the OTP-based board names. Both the generic board-specific names and the plain aliases are shipped.
- **First boot unknowns:**
  - `openssh` is now installed by the builder. The installed-system verifier should accept it, but this has not been exercised in a real build.
  - The post-boot hook reaches only users created from `/etc/skel`.
- **Still open from the audit:** no T8132 display driver; Mesa UAPI vs. kernel unverified; raw Stage 1 on 26.6.2 iBoot and the app on macOS 27 unverified on hardware.
