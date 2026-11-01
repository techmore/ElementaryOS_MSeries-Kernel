# J773g (Mac mini M4) native HDMI — kernel side

Branch `mini/hdmi` on techmore/linux-m1pro-touchid, based on `elementaryos-mseries` (fa26b0f92ef6).
Worktree: `/private/tmp/claude-501/wt/hdmi`.

## Decision: drive HDMI from `dcpext0` (dispext0)

### What the ADT (26.6.2 boot, `/private/tmp/claude-501/kern/adt-j773.txt`) says

- `display-crossbar0` (`display-crossbar,t8132`, AAPL,phandle 184) has
  `ufp-endpoints` = dispext0..3 + scodec0 and `dfp-endpoints` = atc0..3, lpdptx, dptx.
- `dcp` → `dp-switch-ufp-endpoint = 0`, `dcpext0` → `= 1`, `dcpext1` → `= 2`. All three have `dp-switch-parent = 184`.
- `dptx-phy` (`dptx-phy,t8122`, reg 0x19A740000/0x19A700000) → `dp-switch-dfp-endpoint = 4`, `port-type = 6` (HDMI),
  `dp2hdmi-gpio-parent` → `dp2hdmi-gpio0`: `hdmi_hpd` = AOP GPIO 0x29, `hdmi_pwr_en` = SMC `gP0f`,
  `dp2hdmi_pwr_en` = SMC `gP1a`, `reset` = SMC `gP10`, `force-dpfu` = AOP GPIO 0x24, `pcon-stays-on = 1`.
- So **no pipe is hard-wired to HDMI**: the crossbar lets any of the three DCPs drive the PHY. That is why
  macOS 27 (dcpext1) and Gravity (main dcp) both work. The pipe is a software choice.
- All three nubs run the same image, UUID `81BAF476-679D-3CC0-8C6A-E6B6FA659D5E`.
- `pmgr` `bwr-agent` table: DISP_INT agent 0 (BIRQ 0x35), ISP 1, SC 2, DISP_EXT0 agent 3 (BIRQ 0x28),
  DISP_EXT1 agent 4 (BIRQ 0x89). This gives the dcpext0 `apple,bw-scratch` offset 0x20000 + 3·0x4000 = 0x2c000, the
  same value as Gravity's tree.

### Why dcpext0 rather than dcp or dcpext1

1. **It is the pipe the boot framebuffer runs on.** The minimal T8132 trees (Yureka Lilian, Asahi, 2026-08-11) set
   `framebuffer0` power-domains to `ps_dispext0_fe` + `ps_dptx_phy` "for the HDMI port", and Gravity keeps the same.
   `disp_sys`/`disp_fe` are always-on anyway, so adding DISPEXT0 makes sense only if iBoot scans out through dispext0.
   This is the same layout as the M2 mini (j473: dcpext) and M2 Pro mini (j474s: dcpext0). Taking over the pipe that is
   already lit and routed avoids re-routing the crossbar under a live scanout.
2. **It is the processor class Aurora already drives HDMI from.** `DCP_FIRMWARE_V_26_6_DESKTOP` drives T6041's HDMI from
   `dcpext0` ("desktop external processor": DPDEV/DPAVCTRL/DPSAC/AV/DPTX bring-up, fixed DP PHY power at probe, DP2HDMI
   GPIOs, EDID from sink metadata). The desktop *panel* path assumes a panel, which the mini doesn't have.
3. **It leaves the main `dcp` alone.** That keeps the J713 `iomfb_m4.c` path (apple,t8132-dcp) untouched.
4. **The firmware ABI matches.** Gravity drives T8132 (dcp and dcpext) and T6041 with one 26.6 path.
   Its 23 IOMFB methods are a subset of Aurora's `iomfb_v26_6_desktop.c` table, with the same numbers (Aurora adds A414
   and A474). Gravity's AFK also speaks compact EPIC on T8132. Gravity reported HDMI connected with 3840x2160 modes
   on this mini under Linux (kr6/gravity/HOST-OBSERVATION-2026-10-30.md).

Counter-evidence I weighed: macOS 27 drives the Dell from dcpext1, and Gravity uses dcp. Both are runtime choices that the
crossbar allows; neither says which pipe iBoot uses at handoff. If the first hardware boot shows that iBoot actually scans out
from disp0 (see "Verify on hardware"), the same driver path can be moved to dcpext1, or to dcp by adding `apple,t8132-dcp`
J773g data. The DT changes are local to the J773g board file.

## Commits (`origin/elementaryos-mseries..mini/hdmi`)

| Commit | What |
|---|---|
| `ba793becefcb` arm64: dts: apple: t8132: add the dispext0 display pipe and DPTX PHY | SoC nodes, all disabled: `dispext0_dart` (SID0/16), `dcpext0_dart` (SID23), `dcpext0_mbox` (IRQ 731–734), `pmgr_dcp`, `dcpext0` (`apple,t8132-dcpext`, dcp-index 1, bw-scratch 0x2c000, power domain DISPEXT0_FE), `dptxphy` (`apple,t8122-dptx-phy`) |
| `82f28154e06d` dt-bindings: display: apple,dcp: add apple,t8132-dcpext | binding enum |
| `4d100d3ece6e` drm/apple: drive the J773g HDMI processor through the desktop 26.6 path | `apple,t8132-dcpext` → `DCP_FIRMWARE_V_26_6_DESKTOP` **only on apple,j773g** with firmware 26.6.2 / compat 26.6.2 / UUID 81BAF476…; hw data as the T6041 dcpext (2 DPTX ports, sink-metadata EDID); counted as a desktop external processor. No ext fail-safe: a failed probe fails the DRM device and simpledrm stays. |
| `7fb3b0f98e74` iommu/apple-dart: take over the J773g HDMI pipe's DARTs only when locked | Applies only to J773g dart-dispext0/dart-dcpext0 (0x286300000/0x286340000). An unlocked DART refuses to probe before its first register write, so a reset can't kill the live scanout. A locked DART mirrors firmware root entries (`fw_mirror`), as on T6041. |
| `30a318e314a4` arm64: dts: apple: t8132-j773g: wire the HDMI port to dcpext0 | HDMI-A, `phys = <&dptxphy>`, `apple,dptx-phy = <4>`, hpd AOP 41, hdmi-pwren SMC 15, dp2hdmi-pwren SMC 26, `apple,iomfb-surfaces = <1 1 0 0>`; display-subsystem (`apple,display-subsystem`, `dispext0_dart 0`, dma-noncoherent); aliases dcpext0/disp0/dispext0_piodma. Only `dptxphy` is enabled. The rest is left for the loader to enable. |

J713 is unchanged: no J713 node gains a property, `apple,t8132-dcp`/`iomfb_m4.c` are untouched, and every new driver branch
checks `apple,j773g` (DCP) or the J773g DART addresses.

DT check: `/private/tmp/claude-501/kern/dtc-branch.sh` pointed at the worktree. All six T8132 boards (j773g, j713, j604,
j715, j623, j624) compile with 0 dtc errors. The only new warnings are the classes the existing J713 `dcp` already has
(unique_unit_address for `dcp-pmgr@382800000`, avoid_unnecessary_addr_size, simple_bus_reg).

CI: passed. See "CI result" below.

## What still blocks native HDMI: the loader (m1n1), not in this branch

The kernel side is inert until the boot loader hands dcpext0 over. Aurora's m1n1 (`dt_set_display`) returns early for
T8132 after the J713-only `dt_set_j713_dcp_handoff`, and it locks only dart-disp0. For J773g it needs to:

1. Reserve `/arm-io/dcpext0/iop-dcpext0-nub` `segment-ranges` (4 segments) as `apple,asc-mem` no-map regions, with
   `iommu-addresses` from the live dart-dcpext0 SID23 tables, and set `memory-region` on `dcpext0`.
2. Reserve the boot framebuffer (`/vram`) as `memory-region-names = "framebuffer"` on the display node (alias `disp0`),
   with its dart-dispext0 SID0 mapping, and the PIODMA SID16 mappings on `dispext0_piodma`.
3. Lock dart-dcpext0 and dart-dispext0.
4. Publish `apple,firmware-version = "26.6.2"`, `apple,firmware-compat = "26.6.2"` and `apple,firmware-uuid` on `dcpext0`.
5. Set `status = "okay"` on `dcpext0`, `dcpext0_mbox`, `dcpext0_dart`, `dispext0_dart` and the display node.

The templates are Gravity bootloader e8593fe (t8112 carveout table + `dt_reserve_dcpext_firmware` + VRAM for T8132) and
Aurora's own T6041 entry in `kboot_display_handoff.c`, which is the same pattern for a different nub/DART set.

## What only hardware can confirm

- **Which pipe iBoot lights.** Check from m1n1 that the dart-dispext0 SID0 TTBR is live and the dart-disp0 SID0 TTBR is not, or check the DISPEXT0 vs DISP PMGR states.
  If iBoot uses disp0, retarget the board wiring (see above).
- The desktop 26.6 IOMFB/compact-EPIC/DPTX sequence on the **T8132** dcpext image: start, `DPDEV`/`DPAVCTRL`
  endpoints, DPTX connect on HPD, EDID, modeset, swap.
- T8122 PHY activation with `apple,dcp-index = 1` (written to PHY core +0x10 as the DCP input select) through the crossbar.
- `apple,bw-scratch` 0x2c000 (from the bwr-agent table, not observed in use).
- Power: dcpext0 on DISPEXT0_FE only. On T6041, powering DISPEXT0 without a PMP ack hung the machine. Here it is already
  on at handoff (simplefb holds it), but a suspend/resume or a DPMS cycle is untested.
- `fw_mirror` on locked T8132 display DARTs.
- HPD interrupt on AOP GPIO 41, polarity of SMC 15/26. The converter `reset` (gP10) and `force-dpfu` (AOP 0x24) are not driven.
- 4K@120 through the converter (macOS: DP 4 lanes, LinkRate 4); a 48 Gbps HDMI cable may be needed.
- Not wired: HDMI audio (`sio`/`dpaudio`, SIO 26.6.2 rules missing in Aurora m1n1), CEC, and dcpext1 (USB-C DP alt mode).

## CI result

`elementaryos-mseries-kernel.yml` on `mini/hdmi` (head `30a318e314a4`), run
https://github.com/techmore/linux-m1pro-touchid/actions/runs/41209047846: **success**. It built the Image, modules,
`t8132-j773g.dtb` and `t8132-j713.dtb` with the Aurora config, and the J773g DT check passed. The log has no errors and
no warnings from `dcp.c` or `apple-dart.c`. No fix-up commits were needed.
