# J773g installer with Gravity's boot chain (built 2026-10-31, night)

**Package:** `Omarchy-J773g-developer.pkg`, 3,875,643,072 bytes, sha256 `39c608d59b0d13735a4a5dc4676163d554338f26a1dccd5da79b07c601a9f9d1`. It is ad hoc signed, with the offline payload, app 2.3.0.

| Piece | Source |
|---|---|
| Installer app + engine | techmore/omarchy-mac-installer `j773g/gravity-boot-chain` (827e58c, ce040cd + build-script fix). Engine `v0.9.2-omarchy.20261101.906d0e4497dc` (sha256 `bb92d545…`). On J773g it registers Gravity's raw Stage 1 (`esp/gravity/stage1-j773g.bin`, gravity-bootloader-stage1 1.6.1-110 `m1n1-asahi.bin`) with `chosen.gravity,efi-system-partition` + `chainload`, padded to 64 KiB. Registration happens in the stub's paired Recovery at the first boot ("Finish Installation"). Developer builds write `encrypt=0`. |
| OS payload | `omarchy-2026.11.01-aarch64-apple-silicon-mac-j773g-gravity-os-package.zip`, sha256 `0a7b0f6ccb7ceea3773a4cd6aab77d2e2b6aa7270e2fb3bc254876cad145b529`. Built locally with andreinita21/OmarchyM4Mini `70aa20e` (`tools/j773g-pkg.sh all`, `tools/j773g-image.sh`) plus [patch-linux-gravity-m4-u128.py](omarchy-gravity-port/patch-linux-gravity-m4-u128.py). Wrapped with [make-gravity-payload.py](omarchy-gravity-port/make-gravity-payload.py). |
| Packages in the image | linux-gravity-m4 7.1.13.gravity1-7, m1n1-gravity 1.6.1.gravity20261013-3, uboot-gravity 2026.07.asahi2.gravity203-1, mesa-gravity-m4 26.3.0_devel.gravity.alpha02-2, aquamarine 0.15.1-3 (patched), omarchy-j773g 20261017-1, omarchy-dev 4.0.0.r7519, openssh, ufw (899 packages) |
| Kernel line | `root=UUID=4f4d5801-… rw rootflags=subvol=@ … idle=nop nohlt arm64.nowfxt efi=noruntime quiet loglevel=0 …` (no splash) |
| Added to root.img | `omarchy-ssh-debug.service` (GITHUB_USER=techmore: key-only SSH, UFW 22, mDNS) from our image builder. journald is persistent (OmarchyM4Mini default). |

## Install
1. Install the .pkg (Gatekeeper: Open Anyway), open Omarchy Installer, and install into the free space. Do not resize macOS.
2. Shut down. Hold power, choose **Omarchy**. The first boot runs "Finish Installation" in Omarchy's paired Recovery, which registers Gravity's Stage 1. Follow its prompts.
3. Next boot of Omarchy: HDMI stays dark until the kernel's display driver starts, then Omarchy's first-boot owner setup appears. A hung boot may make iBoot say the stub "needs to be reinstalled"; pick Omarchy in the startup options again.
4. Debug: `ssh <owner>@<hostname>.local` once the owner account exists and the network is up.
