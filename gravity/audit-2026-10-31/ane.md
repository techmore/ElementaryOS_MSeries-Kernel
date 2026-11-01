# M4 (H16 / T8132) Neural Engine: opt-in package for the Mac mini M4 (J773g)

Date: 2026-10-31.
Deliverable: techmore/omarchy-pkgs branch `elementaryos-mseries-ane` (based on `elementaryos-mseries` 34c27c6e), commits 20d5d75a and 4fba0663, package `pkgbuilds/ane-h16-experimental`.
Nothing was pushed anywhere else. No PRs, issues or comments were opened. linux-aurora, m1n1-aurora and mesa-aurora were not touched.

## Source

- The `ane/h16` code is a directory on joshuaswarren/omarchy-ane `main`, not a branch. `ane/h16` was already in tag **v0.5.7**: between v0.5.7 and `main` 5de4cee7 (2026-10-31) only comments changed. The package pins the v0.5.7 tarball (sha256 304d5768…, the same tarball omacom's `omarchy-ane-dkms` 0.5.7 uses). License: GPL-2.0-only OR MIT.
- **Build system:** an out-of-tree kbuild module (`obj-m := ane_h16.o`, built with `make -C <kernel> M=…`), not an in-tree driver. Upstream leaves it out of its own `dkms.conf` and package; the README says to build it by hand. A userspace simulation (`make sim`) compiles the real module source against a shim: positive and negative scenarios, plus mutation tests.
- **Not autoloaded:** no `MODULE_DEVICE_TABLE`. The probe refuses unless `optin=t8132`, and refuses if the node's `apple,ane-type` is not 0x100.
- **Stages:**

  | Stage | Hardware access |
  |---|---|
  | `dt` (0) | No MMIO. Parses the DT, and the boot ADT from m1n1's reserved-memory `adt` phram region (m1n1 `kboot.c` `dt_setup_mtd_phram` provides it). |
  | `status` (1, **upstream default**) | Powers the 5 ANE domains and polls the 5 pmgr state words. Only once all 5 read ACTUAL=0xf does it read RVBAR, CPU_STATUS, SCRATCH0-7 and the mbox ctrl words. No engine writes. |
  | `boot` (3) | Checks `segment-ranges`, then the firmware pin, then the preload diff. Then maps the DART at the ADT IOVAs, writes RVBAR, sets CPU_CONTROL 0 then 0x10, and polls SCRATCH7 for 0x08042006. Optionally answers RTKit HELLO/EPMAP/STARTEP. No inference. Once it runs, only a reboot clears it. |

- **Firmware:** `apple/ane/h16_ane_fw_leto_j7x.macho`, pinned by size and SHA-256 (0x17c000, 4b330c5f…). omarchy-ane's `omarchy-ane-firmware-fetch` gets it on the Mac from Apple's macOS 27.0 restore image, using HTTP range requests over the IPSW zip, then unwraps and pin-checks the IM4P. The package ships a copy of that script and runs it only on `ane-h16-experimental firmware`. Apple firmware is never redistributed.

## ADT verification (J773g ADT `/private/tmp/claude-501/kern/adt-j773.txt`, arm-io offset +0x200000000)

| Item | Upstream overlay | J773g ADT | Result |
|---|---|---|---|
| ANE engine | 0x500000000 + 0x2000000 | /arm-io/ane reg[0] 0x300000000 + 0x2000000 | ✅ |
| pmgr window | 0x380700000 + 0x18000 | reg[1] 0x180700000 + 0x18000 | ✅ The kernel's pmgr node is only 0x14000, but all ps words are inside it |
| ANE IRQs | 629, 642 | interrupts [629, 642] | ✅ |
| ane-type | 0x100 | 256 | ✅ |
| ANE_SYS | +0x570 | id 155, psreg 5, 0x380700570; parent AFISOCNI5 (virtual, no register) | ✅ Matches t8132-pmgr.dtsi `ps_ane_sys` (no parent) |
| ANE_MPM / CPU / TD | +0xc000 / +0xc008 / +0xc010 | ids 177/178/179, parent ANE_SYS | ✅ Matches dtsi |
| ANE_BASE | +0xc018 | id 180, parent ANE_TD | ✅ Matches dtsi |
| DARTs | 0x501800000 / 820000 / 840000, each +0xc000 | dart-ane reg 0x3018x0000 +0xc000 (DARTLLT/BRD/BWR) | ✅ |
| DART IRQ | 630 | 630 | ✅ |
| DART SID | iommus `<&dart 0>` | mapper-ane reg 0 (mapper-ane-mpm reg 11 is not described) | ✅ |
| Not described | DAPF 0x501810000, 0x18079c000 window | present in the ADT | Known gap (apple-dart does not program DAPF) |
| bypass SID | comment says bypass-15 (J604) | **bypass-10** on J773g | Not encoded in the overlay; doc only |
| **AIC target path** | `/soc/interrupt-controller@381180000` | ADT aic 0x181000000; our t8132.dtsi has `interrupt-controller@381000000` | ❌ **Upstream overlay fails on our DTB** (`FDT_ERR_NOTFOUND`, reproduced with fdtoverlay). Fixed in the package. |
| Power gates | – | ANE `power-gates [292, 396]` = ANE-SYS-V / ANE-SYS-V-PMP (virtual, psreg 0). ANE_SYS has `notify_pmp = True` and `on = False` | macOS routes ANE power through PMP; Linux flips the ps words directly. This is the most likely cause of a stage=status failure. |
| `segment-ranges` | – | TEXT {phys 0x10000ab8000, 0, remap 0x10000000000, **0x1000c0000**}; DATA {0x10000d78000, 0xc0000, 0x100000c0000, 0x2ac000}; `pre-loaded = 1` | ⚠ The module reads word 3 as a 64-bit size. 0x1000c0000 ≠ the pinned 0xc0000 (the upper dword is apparently a flag), so **stage=boot will refuse with `segment-ranges`** before any write, if the live ADT matches this dump. Not patched: that is upstream's call to make. |

## Kernel match (techmore/linux-m1pro-touchid `elementaryos-mseries` fa26b0f92ef6, 7.3.0)

- The APIs match 7.3:
  - `iommu_map(..., gfp)`
  - `sha256()` from `crypto/sha2.h`
  - void platform `.remove`
  - `of_device_get_match_data` in `of.h`
  - `dev_pm_domain_attach_by_id` / `device_link_add`

  CI confirmed it: the module was built with DKMS against our own `linux-aurora-headers` **7.3.0.aurora90-1**, seeded from elementaryos-mseries run 41207184159. vermagic is `7.3.0-90-1-ARCH SMP preempt mod_unload aarch64`. `CONFIG_MODULE_SIG` is off, so the module is unsigned and taints the kernel (O).
- **Bug found and patched:** the platform core attaches power domains only for a node with exactly one (`genpd_dev_pm_attach`, drivers/pmdomain/core.c). With 5, upstream's `pm_runtime_get_sync()` powers nothing, so stage=status could only end in `pmgr-actual-stuck`. Patch 0002 attaches the domains by index and links them, as upstream `ane_h15` does. It also keeps them on once stage=boot has touched the firmware.
- `CONFIG_APPLE_DART=y` (built in). Any overlay that adds the ANE DARTs makes apple-dart probe them on every boot. That probe powers ANE_SYS, resets the DARTs and requests IRQ 630, with or without the module loaded. This is why the package splits the overlay in two.
- The kernel is built with clang 18. dkms adds `LLVM=1`, so the package depends on clang, llvm and lld (CI run 1 failed without them).
- Side note for the image: omacom edge currently has `linux-aurora 7.2.11.aurora12-1`, so our 7.3.0.aurora90 sorts above it as intended.

## Package `ane-h16-experimental` 0.5.7-1 (aarch64)

- DKMS source in `/usr/src/ane-h16-experimental-0.5.7`, with two patches:
  - **0001:** the default stage is `dt`. Upstream defaults to `status`.
  - **0002:** multi-power-domain attach, plus sim shim stubs.
- `/usr/lib/modprobe.d/ane-h16-experimental.conf`: `blacklist ane_h16` and `options ane_h16 stage=dt`.
- Overlays in `/usr/lib/omarchy-mac-boot/dtb-overlays/t8132-j773g/` (J773g DTB only). Each is gated by an `omarchy,opt-in` key in `/etc/omarchy-mac-boot/dtb-overlays.opt-in` and by `omarchy,skip-if-compatible = "apple,t8132-ane"`:
  - `omarchy-ane-h16-dt.dtbo`, key `ane-h16-dt`: the ANE node only, with no DARTs and no `iommus`. With 5 power-domains and nothing built in that binds it, **applying it touches no hardware**. Enough for stage=dt and stage=status.
  - `omarchy-ane-h16-full.dtbo`, key `ane-h16-experimental` (upstream's key): the node plus DARTs, for stage=boot. It sorts after `-dt`, so if both keys are listed the dt overlay wins and the full one skips itself.
- `/usr/bin/ane-h16-experimental`:
  - `status`
  - `overlay dt|full|off`: edits the opt-in file and runs `update-m1n1`
  - `load dt|status|boot`: boot also needs the full overlay, the firmware and `--reboot-is-ok`
  - `unload`: refused after the firmware was touched
  - `firmware`
  - `log`
- Packaging:
  - Not in `omarchy-platform-apple-silicon`; install it by name.
  - `release/mac-inventory.txt` lists it as `none`, so it can never be promoted past edge.
  - `post_remove` deletes both keys and the fetched firmware.
  - On install and removal, omarchy-mac-boot's hook reruns `update-m1n1`. With no key listed, the DTBs are unchanged.

## Build result

Workflow `.github/workflows/elementaryos-mseries-ane.yml` (fork-only, ubuntu-24.04-arm, `bin/build --mirror edge`). It seeds `linux-aurora-headers` from the newest elementaryos-mseries `linux-aurora-aarch64-*` artifact and falls back to edge headers with a warning.

- Run 41211031617: **failed** at the DKMS build (no clang for `LLVM=1`). The sim and overlay checks passed.
- Run **41211270447: success.** `check()` passed all of these:
  - the upstream sim with both patches: 11/11 scenarios plus 4 mutation checks
  - both overlays apply with fdtoverlay to `t8132-j773g.dtb`, compiled from the kernel tarball at fa26b0f9, with every phandle checked (AIC and the 5 ps nodes)
  - the dt overlay has no `iommus`
  - DKMS build against our 7.3.0-90-1-ARCH headers, with no module alias and `stage` defaulting to dt
- Artifact `ane-h16-experimental-aarch64-4fba0663…` contains `ane-h16-experimental-0.5.7-1-aarch64.pkg.tar.zst`, sha256 `8e0dae381225897f2018971ed5ce557e53a87f5fe74333fd79aa29320b8756cd`. It is unsigned.
- The same overlay checks were also run locally: dtc 1.7.2 and fdtoverlay against the DTB built from refs/remotes/origin/elementaryos-mseries.

## How the owner tests it after first boot

1. Install the package from the artifact (local repo, trusted explicitly). DKMS builds `ane_h16`. Check `ane-h16-experimental status`.
2. `sudo ane-h16-experimental overlay dt`, then reboot. This is the only step that changes the boot DTB. If the Mac does not boot: from recovery/chroot delete `ane-h16-dt` from `/etc/omarchy-mac-boot/dtb-overlays.opt-in`, run `update-m1n1`, and reboot.
3. `sudo ane-h16-experimental load dt`. Expect `RESULT stage=0 … PASS reason=dt-parse-only` and, if iBoot preloaded the firmware, two `adt seg` lines. Zero hardware access. Save `ane-h16-experimental log`.
4. `sudo ane-h16-experimental load status`. This is the first hardware touch.
   - PASS: RVBAR, CPU_STATUS and SCRATCH values.
   - `FAIL pmgr-actual-stuck`: the engine was not touched. Likely the PMP-managed ANE power; report it.
   - A hang or SError: power-cycle, run `overlay off`, keep pstore.
5. Only if 4 passed and you accept a possible hang: `sudo ane-h16-experimental firmware`, `sudo ane-h16-experimental overlay full`, reboot, then `sudo ane-h16-experimental load boot --reboot-is-ok`. Expected today: `REFUSED reason=segment-ranges` (see the ADT table), with nothing written. Reboot after any boot run.
6. `sudo ane-h16-experimental overlay off` and reboot to return to stock.

Expectation for AI performance: this produces bring-up evidence only. No inference path exists for H16 yet (the 27.0 CSNE host contract is not derived). Local AI on the mini still runs on the CPU and the G16 GPU (MLX/Vulkan).
