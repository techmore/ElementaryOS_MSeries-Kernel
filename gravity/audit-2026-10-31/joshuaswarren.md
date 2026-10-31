# Joshua Warren repositories: audit for the Mac mini M4 (J773g / T8132)

Date: 2026-10-31. Read-only audit: nothing was pushed, forked, starred or commented.
Target: techmore/linux-m1pro-touchid `elementaryos-mseries` (aurora-silicon/linux
`aurora-wip` @ 23e431a98962 + 3 J773g G16 commits). Current aurora-silicon `aurora-wip` is
acc3050081e5, 2 merge commits ahead of our base.

How it was checked:
- Branch tips and dates come from GraphQL.
- "Merged" means a patch with the same subject is in aurora-silicon/linux `aurora-wip` (AS) or
  omacom/linux-aurora `integration/aurora` (OM). Mesa was checked against aurora-silicon/mesa
  `aurora-wip`.
- Comparisons ran in a separate scratch repo (`audit/ja-git`, with alternates pointing at the
  shared clone, which was left untouched) and in `audit/mesa-git`.
- Raw lists: `audit/ja-branches.tsv`, `audit/branch-commits.txt`, `audit/mesa-branches.tsv`,
  `audit/mesa-branch-commits.txt`, `audit/forks.txt`.

## What changed since the 2026-10-12 review

- There are now 164 public repos (the review had 148). Most new repos are Omarchy plugins,
  themes, or agent and inference tools with no kernel content.
- The new hardware-relevant work is all about the **M6 Mac mini (T8152, J873g)**:
  - linux-aurora `m6-*` and `w7*` branches
  - m1n1 `m6-bringup`
  - omarchy-m6-bringup, linux-omarchy-m6
  - omarchy-mac-installer `w7C/m6-*`
- New omarchy-ane content includes an **H16 (M4) ANE bring-up module with a T8132 DT overlay**.
- **There are two upstream lines.** omacom/linux-aurora `integration/aurora` and aurora-silicon
  `aurora-wip` diverge at 44d5afc79da7 (7.2.10 unify, 2026-10-20). OM has 168 patches
  (matched by subject) that are not in AS. These include Joshua's eGPU series (OM PR #188,
  merged) and his asahi_stats debugfs (OM #281). Neither is in our base.

## Ranked findings for J773g

| # | Item | M4 relevance | Upstream status | Rec. |
|---|---|---|---|---|
| 1 | **maclab** (fork of chriskearney/maclab, MIT) | Safer boot-testing workflow (see below) | Joshua's fork is 0 ahead / 9 behind upstream; use **chriskearney/maclab** | **Take (as a method or tool)** |
| 2 | **M6 SMC/power pattern** (linux-aurora `w7Y/m6-all`: 308a7f0a9a94 macsmc cells + table-driven pcIO; 7ac6ec8a7b43 nvmem `shutdown_flag` poweroff; 017d8cebaee1 opt-in SMC notifications / power button; 449fbe39add3 SMC AC-power/heatpipe hwmon keys) | J773g in our tree has **only** `smc-hwmon` + `smc-gpio`. It has no `smc-reboot`, `smc-rtc`, PMU nvmem or power-button input, and `nub_spmi` is disabled. Same gap the M6 had. | Not merged (OM PRs #191–#198 open, T8152-specific) | **Take the pattern, not the code.** T8122 (t8122.dtsi ~l.989–1100) already has the in-tree template for stowe-pmic nvmem + smc-reboot/rtc. Joshua's M6 commits show the ADT-key method and the poweroff bit caveat (bit 3 vs bit 4). |
| 3 | **omarchy-ane `ane/h16`** (ane_h16.ko + `t8132-ane-experimental.dts`) | Written specifically for T8132 (engine, pmgr ps words, DART, IRQ from the ADT). Staged, `stage=dt` touches no MMIO. Untested on silicon (sim only). Firmware `h16_ane_fw_leto_j7x.macho`. | Out of tree, opt-in only | **Watch / optional lab trial.** Local AI only, no desktop performance. Needs maclab-style rollback. Not a kernel-tree merge. |
| 4 | **eGPU series** (OM #188: `drm/ttm, drm/amdgpu: honor non-posted BARs…`, `PCI: apple: wait for tunneled slot links`, `…prefetchable window on cold-initialized tunnel ports`, identity 64-bit tunnel windows; `egpu-nonposted-bars`; `config/udmabuf-zero-copy-host-memory`) | Generic amdgpu/ttm non-posted-BAR code would apply. But **T8132 has no USB4/ACIO/PCIe-tunnel nodes in our tree**, so it has no use until M4 USB4 exists. The DT fixes are T600x/T602x only. | Merged in OM, **not in AS** | **Watch.** Pick up when T8132 USB4 lands or when we rebase onto OM. |
| 5 | **M6 USB4/PCIe-C/Type-C PHY** (`m6-usb4`, `m6-pcie`, `m6-phy`: ACIO MXWrap start, NHI `pdf` optional, T8152 Type-C PHY, dwc3 PWRDNSCALE) | Possible template for T8132 USB4. T8132 uses the older atcphy/`t8132-pcie` IP, so the MXWrap/Gen3-DART parts don't carry over. | Open OM PRs #192/#197/#198 | **Watch** (already partly checked). |
| 6 | **mesa-1 Honeykrisp branches** (`map-placed-length`, `capture-replay-va-main`, `tf-null-counter`, `aurora-memory-fixes`/OM-mesa #15, `aurora-correctness-fixes`) | Mostly generation-independent Honeykrisp correctness fixes: placed-map bounds, capture/replay VA range, NULL XFB counter array, free-memory reserve, image-texel visibility, exact fdiv/log/sin. They would also apply on G16G. | All **unmerged** in aurora-silicon/mesa (omacom/mesa PRs #8/#9/#10/#14/#18 open; #15 merged into omacom/mesa but not in AS mesa by subject) | **Watch; cherry-pick only on a concrete bug.** The bug fixes (#8, #9, #10) are the low-risk ones. |
| 7 | **mesa-1 perf branches** (`agx-fold-g14`, `honeykrisp-omarchy-v3`, `hk/agx-wait-batching*`, `agent/*` CDM-barrier variants, coopmat/bf16) | Tuned and gated for **G13/G14** (M1/M2): CDM barrier trims, sub-format folds, coopmat. M4 runs the AGX3/HAL200 path. | Unmerged; many are diag/variant branches | **Skip for M4.** |
| 8 | **Mesa support for M4 G16** | aurora-silicon/mesa `aurora-wip` already has native G16G: 662048cacc8 "asahi: enable native G16G on the shared AGX3 path" (2026-10-17), plus G16G store follow-ups. No Joshua branch targets G16G. | n/a | Use aurora-silicon/mesa, not mesa-1. |
| 9 | **omarchy-mac-pkgs `feat/cpu-governor-on-ac`** (62c9527cba udev → `performance` governor when `macsmc-ac` online) | Trivial for an always-on-AC mini, but it depends on a `macsmc-ac` supply J773g may not expose. Benefit is unmeasured and costs power and heat. | Not merged upstream | **Skip** (or test as a one-line sysfs experiment). |
| 10 | linux-aurora `agent/jw16-pmp-pm-protocol` 77e3ff6991 | Our `drivers/soc/apple/pmp.rs` still replies on fixed `PMP_ENDPOINT` (0x20) at l.477. The callback ignores `_ep` (l.627), and only 0x20 is started (l.201), so the patch is a no-op today. | Not merged | **Skip** (revisit only if another app endpoint is started). |
| 11 | asahi stats debugfs (OM #281, `w73/gpu-stats-aurora`), `agx_stats` sysfs (AS #168, merged) | Implemented for the G13/G14 `channel.rs` stats path; the commit says G17/M3 backends expose nothing. G16 uses its own `g16/` backend. | debugfs only in OM | **Skip** for G16. |
| 12 | m1n1 `m6-bringup` (072526cfe6 T8152 RVBAR veneer SMP start), `w7C/m1n1-t6032-*` | T8152/T6032 only | Not in aurora-silicon/m1n1 | Skip |
| 13 | aurora-u-boot `mtp-kbd-filter-a/b` | MTP keyboard (laptops), not the mini | Unmerged | Skip |
| 14 | Merged already (no action): `ane-*`, `tbnet-rx`, `config/rdma-soft-roce`, `gpu-g14x-compute-preempt*`, `installer-resume-download`, `w73/ane-call-poll`, `w73/adt-ane-nodes`, `cve-2026-98432-7.1` (AS PR #576 open, but the subject is already in AS) | — | In AS | — |
| 15 | omarchy-mlx / coreglass / metal2vk / ane-linux-experiments / omarchy-egpu / omarchy-m-testing | omarchy-mlx README: M4 "Not yet (no Linux GPU driver)". Kernels are tuned for G13C/G14C, so a G16 Vulkan run is unqualified. coreglass recently added SMC power-rail ledger rows, which are useful for power measurement on the mini via `hwmon-mini`. omarchy-m-testing `w7b/compute-mlx-ane-checks` adds MLX/ANE checks. | User-space | **Watch.** Re-run the MLX tester kit now that the G16 GPU is up; coreglass is optional for power measurement. |
| 16 | omarchy-mac-installer, omarchy-pkgs, omarchy-mac, modelctl, TensorFold, themes and plugins | Installer refuses M4. The rest is Arch/Omarchy packaging or apps. | — | Skip |

## maclab: could it make boot-testing safer on the mini?

Yes, as a method; the full tool needs adapting. The relevant pieces:

- **One-shot boot that clears itself before the entry runs.** For GRUB, `maclab_next=` is
  stored in `maclab.env` on the FAT ESP, because GRUB cannot write `grubenv` on btrfs. Any
  reset, for any reason, then lands on the known-good kernel. elementary uses GRUB, so this
  path applies directly.
- **Automatic recovery without OOB hardware:**
  - `panic=10`
  - `watchdog.open_timeout=N`: Asahi U-Boot leaves `apple_wdt` armed into Linux. Our
    t8132.dtsi has `apple,t8132-wdt`, so the test kernel must build `apple_wdt`.
  - An early systemd deadline unit that reboots the test boot.
  - pstore/journal collection from the failed boot.
- **Optional hard reset and serial** through a second Mac running `macvdmtool` on the DFU port.
  Verified from M3/M5 hosts against an M1 Air. Not verified on an M4 mini target.
- **Limits:**
  - Families stop at M3; M4 is "not counted".
  - The agent and installer assume Omarchy/Arch (`pacman`) and Hyprland GUI tests.
  - Real suspend can't be tested unattended (no RTC wake alarm).

Recommendation: adopt the GRUB one-shot + `panic=10` + `watchdog.open_timeout` + deadline-unit
pattern for mini kernel trials now. Evaluate labd/lab-agent from upstream chriskearney/maclab
(Joshua's fork adds nothing).

## Side note: the two upstream lines (not Joshua's code)

Beyond Joshua's patches, the 168 OM-only patches include DjDeveloperr CLPC GPU-floor work. It
is gated to T8140, so T8132 is not affected yet. They also include a T8132 `apple,pmc` binding
tweak; our tree already has an equivalent `apple,t8132-clpc`. If the team ever moves the base
from AS `aurora-wip` to OM `integration/aurora`, items 4 and 11 come along for free.
