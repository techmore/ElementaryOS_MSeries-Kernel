# How Gravity Linux boots the Mac mini M4 (J773g), and how our Omarchy chain differs

Source review on 2026-10-31 of the GravityLinux repos:
- `bootloader` f02d4a5 (an m1n1 fork)
- `u-boot` `gravity-alpha-20260925` a2f69136
- `linux` `gravity-m4`
- `installer`, `kiwi-descriptions`, `packages`
- `adt-collection` `26.6.2/t8132-j773.txt`

Gravity is known to boot this exact Mac with HDMI and the SSD working (kernel 7.1.13-509.gravity.fc44). It is compared here with what we installed today, which fails as recorded in [BOOT-BLACK-SCREEN-2026-10-31.md](BOOT-BLACK-SCREEN-2026-10-31.md): Limine starts the kernel, then Linux never mounts root.

## Gravity's chain
iBoot (stub firmware from macOS **26.6.2**) → m1n1 stage 1 → `ESP/m1n1/boot.bin` (m1n1 + DTBs + gzip U-Boot) → U-Boot (`bootflow scan`) → shim/GRUB (BLS) → kernel + dracut initramfs.

## The differences, ranked by how likely each one explains our hang

### 1. M4 idle boot arguments: Gravity has them, ours does not
- **Gravity:**
  - `kiwi-descriptions` `platforms/workstation.xml`, commit 58bdc596 "Add required M4 kernel boot arguments", sets `nohlt idle=nop arm64.nowfxt`.
  - Kernel commit cd5f25a0e4 gives the reason: on M4, WFI/WFIT in the idle loop and `delay()` "cause a loss of architectural state on the secondary cores".
- **Upstream m1n1:** appends ` idle=nop arm64.nowfxt` for all locked-sysreg chips, with the comment "M4 and later lose architectural state in WFI and WFIT … prevent Linux from crashing in the idle loop and delay function."
- **Ours:**
  - techmore/m1n1 `aac8189` `src/kboot.c:476-489` **excludes T8132**: "Aurora's kernels for T8132 … boot without them". That was never tested on J773g.
  - The Omarchy cmdline doesn't carry them either.
  - With EFI boot, the UKI/Limine cmdline replaces DT bootargs anyway, so they must be on the cmdline, as Gravity does.
- **Test:** the debug Limine entry now adds `nohlt idle=nop arm64.nowfxt`. No rebuild is needed.

### 2. SSD (ANS2) handover: Gravity resets it at every stage, ours hands a live session through
- **Gravity m1n1** (`src/nvme.c`):
  - stage 1 cold-boots ANS to read the ESP;
  - `nvme_shutdown()` then does RTKit sleep and a PMGR reset of ANS/ANS2 before chainloading;
  - stage 2 never touches ANS;
  - **no ANS/NVMe/SART DT fixups**: the kernel DT's static nodes are used as-is.
- **Gravity U-Boot:**
  - `apple_nvme_probe` cold-boots RTKit;
  - T8132 I/O-queue registers are 0x1200/0x1208/0x1210 after queue creation (49840d57);
  - RTKit messages are serviced while waiting for CSTS.RDY (61d4b40d);
  - `apple_nvme_remove` at ExitBootServices does `nvme_shutdown`, RTKit sleep, clears CPU RUN, then **reset assert, udelay(10), deassert** (4b738f4f). Its message: without the delay "the subsequent Linux boot stuck before SART probe completed"; with it Linux "mounts its NVMe root".
- **Gravity kernel:**
  - the stock nvme-apple flow (RUN clear → reset → `apple_rtkit_reinit` → `apple_rtkit_boot`) plus a ~40-line T8132 patch (I/O-queue registers);
  - static DT nodes: nvme `0x4c5cc0000`/0x60000 + ans `0x481600000`, mbox `0x481608000` (IRQs 1003–1006), sart `0x485c50000`, NVMe IRQ 1018;
  - `&nvme { status = "okay"; }`;
  - `ps_ans` is `apple,always-on`.
- **Ours (Aurora design):**
  - m1n1 `dt_set_ans_nvme()` fills placeholder nodes from the ADT and enables them. The ADT values match Gravity's static ones, IRQ pair-swap included.
  - m1n1 starts a "post-M4 ANS session" and keeps it running.
  - Aurora U-Boot adopts it and hands it on live ("handing over the live ANS session").
  - Our nvme-apple must `apple_rtkit_adopt_running()` it, through a large custom path that returns -EIO on several conditions.
  - Aurora's premise ("ANS cannot be reset or restarted once running … PMGR reset raises an SError") is contradicted by Gravity, which resets ANS at every stage on this Mac.
- In our boots the SSD demonstrably worked in m1n1 (it read `boot.bin`) and in U-Boot (it loaded Limine and the UKI and wrote `ubootefi.var`). Only the U-Boot → Linux step is unproven.

### 3. Initramfs contents
- **Gravity:** `dracut --no-hostonly` ("this builder is not the target Mac"), with the M4 modules forced in: apple-mailbox, nvme_apple, macsmc, apple-dart, dwc3, phy-apple-atc, pcie-apple, mux-apple-display-crossbar, phy-apple-dptx, xhci-plat-hcd.
- **Ours:** mkinitcpio with `autodetect` run inside the build VM. nvme-apple is present; virtio is in; appledrm is not.

### 4. Display: not the blocker
- Gravity's m1n1 is built `NO_DISPLAY` ("Required for M4 Mac mini bring-up; leave the boot framebuffer in place"). Its U-Boot has no DCP code (simple-fb only).
- **A dark screen before Linux is normal on Gravity too:** `GravityLinux/bootloader` issue #11, "no u-boot or grub screen shows when booting gravity linux".
- Our m1n1 also leaves the display alone on T8132 ("preserving inherited display", `src/display.c:767`).
- Both DTs give `framebuffer0` the domains `ps_dispext0_fe` + `ps_dptx_phy`, and both use DPTX PHY 4 and SMC GPIOs 15/26.
- The DRM side differs: Gravity drives HDMI from `&dcp`, ours from `&dcpext0`. That matters only once Linux runs.

### 5. Smaller differences
- **DAPF:** Gravity skips it on T8132 ("reproducibly raises an SError"). Ours runs `dapf_init_fdt` (U-Boot started fine after it).
- **CTRR:** Gravity reserves the CTRR range.
- **U-Boot DRAM banks:** `NR_DRAM_BANKS=32` (Aurora 16).
- **Stage-1 object:** Gravity pads it to 64 KiB.
- **Firmware version:** the stub firmware is pinned to 26.6.2, which ours also uses (`stub_info.json`: 25G83).
- **ramoops:** Gravity reserves RAM at `0x103e0000000` for early bring-up logs.

## What to change in our stack (in order)
1. **Cmdline:** add `nohlt idle=nop arm64.nowfxt` for J773g. Do it in the image's `/etc/default/limine` (developer builds) and drop the T8132 exclusion in m1n1 `kboot.c`. It is being tested now with the debug entry, with no rebuild.
2. **SSD:** adopt Gravity's model.
   - In m1n1, shut ANS down (RTKit sleep, PMGR reset) before chainload/payload instead of keeping a live session, and stop the ADT ANS fixups (use static DT nodes, `ps_ans` always-on).
   - In U-Boot, use Gravity's three NVMe commits.
   - In the kernel, use upstream nvme-apple plus the T8132 I/O-queue patch.
3. **Initramfs:** build without `autodetect`, with Gravity's forced module list.
4. **Visibility:** add ramoops (as Gravity's DT does) and keep verbose developer cmdlines.
