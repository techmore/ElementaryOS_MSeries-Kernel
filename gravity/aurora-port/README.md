# Port to Aurora: M4 mini (J773g) GPU, step 1

Kernel commits for `techmore/linux-m1pro-touchid` branch `elementaryos-mseries`, on top of
`aurora-silicon/linux` `aurora-wip` @ `23e431a98962`. The branch exists locally; pushing it needs a GitHub token
with the `workflow` scope (`gh auth refresh -h github.com -s workflow`), because Aurora's tree carries CI
workflow files. These patch files keep the work safe until then: `git am 000*.patch` on `aurora-wip`.

| File | What |
|---|---|
| `0001-…share-the-G16-GPU-nodes…` | Rename `t8132-j713-gpu.dtsi` to `t8132-gpu.dtsi`: it describes the SoC, not the Air |
| `0002-…t8132-j773g-describe-the-PMP-and-the-G16-GPU` | Mini board: pmp alias and DAPF hints, PMP DART/report/mailbox, MCC/PMC, include the GPU |
| `0003-soc-apple-pmp-admit-J773g…` | `apple_pmp_g16_board()` = J713 or J773g, used only on GPU paths; display votes stay J713-only |
| `m1n1-0001-kboot_gpu_m4-admit-J773g.patch` | For `aurora-silicon/m1n1` `aurora-wip`: accept `apple,j773g` in the G16 handoff |

## Why this should be enough for the GPU (static evidence)

The J773g ADT (GravityLinux/adt-collection, 26.6.2) matches every value Aurora's J713 path checks:
GPU at 0x300000000/0x4000000 and coprocessor at 0x302600000/0x88000 (after arm-io's 0x200000000 offset),
interrupts 994, 993, 996, 995, firmware segments `__TEXT;__DATA` at IOVA 0xfffffc0000000000 (0x60000 and
0x13c000, the sizes of the 25G83 firmware the G16 driver recognises), the four GPU region pairs (no
overlaps), and a 34-entry PMP table with GFX at entry 12 and DISP at entry 15. Every gate was a
board-name check.

## Not verified

- Nothing is built or booted. The mini has a 10-core GPU; the driver's firmware fingerprints include the
  general 25G83 image and an 8-core J713 variant, so the 10-core image should match the first, but only a
  boot shows it.
- `apple,static-voters = <3>` is copied from J713.
- GPU-adjacent J713 checks left as they are: `pmgr-pwrstate.c` (J713 loader-tree policy),
  `rtkit-helper.c` (J713 MTP/inherited buffers), `t8132-platform-handoff.c` (Apple-loader-tree adapter).
- Display, USB-C, Wi-Fi, Bluetooth, NVMe and audio for the mini are the next steps in
  `../UPSTREAM-GAPS-2026-10-31.md`.

## Building on a Mac

The Linux tree has file names that differ only in case (`xt_DSCP.h`, `xt_dscp.h`). On macOS's
case-insensitive disk these show as modified after checkout; never `git add -A` there. Build on Linux.

## Gap 8 (GPU timeout fix): not needed in Aurora

The 2026-10-28 GPU deaths on Gravity came from its submission worker failing the pipeline when a
firmware notification wait timed out, before it polled the completion stamps (patch 0066).

Aurora's G16 driver has no such wait. `drivers/gpu/drm/asahi/g16/poll.rs`: each pass retires work from
stage stamps, queue READ/WRITE pointers, submit-pipe frontiers and notifier/UMA receipts; an hrtimer
re-polls every `g16_resnap_us` (100 us) while anything is published, with a 1-jiffy delayed-work backup;
`run_poll()` fails only on an error from `poll()`; a hang is declared only when the stamps stop moving past
a deadline that `progress()` renews. A lost or late notification delays the next poll by at most that
period. No port.
