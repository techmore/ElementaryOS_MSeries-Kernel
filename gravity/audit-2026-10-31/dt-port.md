# Mac mini M4 (J773g / T8132) device tree: porting Gravity onto Aurora

Status: draft plan plus draft diffs. Nothing has been pushed and no branch has been changed.
All git use was read-only (`git show`, `git grep`, `git archive` into a scratch directory).

## 0. Inputs and one change to the base

| Ref | Commit | Notes |
|---|---|---|
| Aurora base `elementaryos-mseries` | **1b90344fe637** | The branch moved during this audit. It is now cfd21dd36b57 plus one commit, "t8132-j773g: name the ANS storage nodes for the loader", which adds the `ans`, `ans-mbox` and `sart-ans` aliases. The drafts are rebased onto it. |
| Gravity new | `gravity/replacement/000-devicetree` (305cb6b90c71) | Includes 898c9da9c905 (J773g +104 lines, t8132-usb4.dtsi, pmgr +18) and d1d4269fcce1 |
| Gravity topic branches checked | `replacement/171-dptxphy`, `200-dcp`, `170-atc`, `260-spmi-typec`, `160-usb`, `115-pmp` | Used to work out which drivers Gravity depends on |
| Gravity old | `m4-mini-gravity` | 300-line J773g file. It already has the hpm3 select=65 fix from 4cb9998f58. The new file differs only by adding the jack codec, the usb4 include and the PMP research votes. |
| ADT | `adt-j773.txt` (macOS 26.6.2) | Parsed with `audit/tools/adt.py` (applies the arm-io `ranges`: bus addresses below 0x3a0000000 gain +0x200000000; addresses from 0x4xxxxxxxx up are identity-mapped) and `audit/tools/pmgr.py` (decodes the pmgr device table into absolute PS register addresses) |

Build check: I built dtc 1.7.2 from the kernel's `scripts/dtc` and preprocessed with clang (`audit/tools/compile.sh`).
- `t8132-j773g` and `t8132-j713` compile at every stage s1 to s13, so the series bisects.
- `j604`, `j623`, `j624` and `j715` also compile at s13.
- The series applies cleanly with `patch -p1` in order.
- `dt_binding_check` was **not** run.

## 1. Node-by-node comparison: Gravity's newest J773g/T8132 tree vs Aurora

Gravity keeps most of the M4 SoC in `t8132.dtsi` and `t8132-jxxx.dtsi`. Its jxxx file holds typec0/1, wifi0/bt0 and every dcp alias. Aurora keeps the SoC minimal and J713-shaped. Aurora defines the display only in `t8132-j713-display.dtsi`, and Type-C, Wi-Fi and BT only in `t8132-j713.dts`.

"ADT" in the table means I checked the value against adt-j773.txt.

| Gravity node (label) | Aurora equivalent | Missing in Aurora / differences | ADT |
|---|---|---|---|
| `pcie0` 3 ports (port0/1/2, phy0/1/2, irq 1231/1240/1249), `pcie0_dart`, `pcie1_dart`, `pcie2_dart` | `pcie0` with port0 only; `dart_apcie0` | port2, phy2, irqs 1240 and 1249, `dart_apcie2`, `port02`. Aurora sizes `config` at 0x10000000 and `port0` at 0x8000 (matches the ADT); Gravity uses 0x1000000 and 0x4000. Gravity also adds `pcie_pins` (clkreq 160/161/162) and the power domain `ps_apcie_phy_sw`. | ✔ port2 0x492028000+0x8000, phy2 0x497028000, dart-apcie2 0x492000000 irq 1250. ✗ no dart-apcie1 or bridge1 on J773g. |
| `port00` wifi0/bluetooth0 (in jxxx), `vreg_pcie0_port0` (smc_gpio 19) | J713 only, as an inline `pci@0,0` with `pwren-gpios` | J773g needs its own wifi0/bt0 with `brcm,board-type = "apple,sakhalin"` | ✔ ADT wlan `module-instance = sakhalin`; `reg_on` = SMC gP13 = 19; PERST GPIO 0xa3 = 163 |
| `port02` + `ethernet0` | none | all | ✔ pci-bridge2 PERST GPIO 0xa5 = 165, `lan-1gb`, clkreq 0xa2 |
| `atcphy0..3` (t8122-style "core/lpdptx/axi2af/usb2phy/pipehandler") | `atcphy0/1` with usb2phy and pipehandler only; J713 overrides atcphy1 with Aurora's own 7-bank SuperSpeed layout | atcphy2, atcphy3. Aurora's `atc.c` uses **different reg-names** (axi2af/lioa/fabric/common-config/core). Gravity's reg list must not be copied. | ✔ usb2phy and pipehandler for all 4 ports; core, axi2af, lioa, fabric and common-config fall inside the ADT `atc-phyN` apertures (0x40N3000000+0x58000, 0x40N0000000+0x1000000) |
| `dwc3_0..3` + `dwc3_N_dart_0/1` | dwc3_0/1 + darts | dwc3_2, dwc3_3 and their DARTs. Aurora uses DART size 0xc000, which matches the ADT; Gravity uses 0x4000. | ✔ irqs 1403/1407 and 1465/1469 |
| hpm0/hpm1 (jxxx), hpm3 (board) `apple,sn201202x` + `select` | J713 hpm0/1 `apple,t8132-sn201202x` with no select (the driver polls select on T8132) | all three nodes for J773g; hpm3 is new | ✔ hpm0 sid 0xc [11,17,19]; hpm1 0xa [37,43,45]; hpm3 0x8 [63,69,71]; port-location back-middle/back-left/back-right. ✗ the ADT lists **no select interrupt**. Gravity's 13/39/65 is inferred as irq+2 (4cb9998f58, tested on J773g). |
| Front hub: `dwc3_2` host, `atcphy2 apple,fixed-usb3/fixed-lane-swap`, GPIO hogs 101/198 | none | all; the `apple,fixed-usb3` property has no Aurora driver support | ✔ usb3hub_rst GPIO 0xc6, flash_oe 0x65 (gpio0) |
| `dcp`, `dcp_dart`, `disp0_dart`, `dcp_mbox`, `display` (HDMI on **disp0** in Gravity) | J713-only in `t8132-j713-display.dtsi`, internal-panel adoption | not in the SoC dtsi at all | ✔ same addresses |
| `dispext0_dart`, `dcpext0_dart`, `dcpext0_mbox`, `dcpext0` | none | all | ✔ 0x286300000/0x286340000, irq 750, mbox 731..734, dcpext0 regs. Power gate is **DISPEXT0_CPU**; Gravity uses dispext0_fe. ✗ bw-scratch offset 0x2c000 cannot be checked. |
| `dispext1_*`, `dcpext1` | none | not ported. Not needed for the HDMI port. | ✔ addresses exist in the ADT |
| `dptxphy` `apple,t8122-dptx-phy` | none | all | ✔ ADT `dptx-phy,t8122`: core 0x39a700000+0x4000, dptx 0x39a740000+0x10000, gate DPTX_PHY; `dp-switch-dfp-endpoint = 4` |
| HDMI GPIOs `hdmi-pwren` smc 15, `dp2hdmi-pwren` smc 26 | none | all; Gravity also omits `hdmi-hpd-gpios` | ✔ gP0f = 15, gP1a = 26; hpd = aop-gpio 0x29 = 41 (added in my draft); converter reset = SMC gP10 (not used) |
| `sio_dart`, `sio_mbox`, `sio`, `dpaudio0` (HDMI audio) | none | not ported (see risks) | ✔ sio 0x3ade00000, mbox irqs 1078..1081, dart 0x3ad060000 irq 1074. ✗ The SIO DMA channel 0x64 cannot be checked. ADT `dcpext0 audio` = dp-audio1 (DPA1), not dpaudio0. |
| `pmgr_audio` + `ps_audio_*` (pmgr.dtsi) | none | all | ✔ every offset decoded: audio_a 0x20, fr 0x90, p 0xb8, base_ns_a 0xd8, mca0/1/2_m 0xe8/0xf0/0xf8 at 0x388284000 (pmgr reg1 + 0x4000) |
| `dart_audio`, `admac`, `mca` | none | all | ✔ dart-aop 0x390f00000 (ADT size 0xc000) irq 457; admac 0x393800000+0x34000 irq 475. ✗ MCA at 0x393600000 is not in the ADT (audio is in an IOP). |
| speaker amp `ti,sn012776`@i2c3 0x38, jack `cirrus,cs42l84`@i2c1 0x4b, `speaker-audio` | none | all | ✔ amp reset gpio0 0xf; codec reset nub-gpio 0x11, irq gpio0 98 |
| `t8132-usb4.dtsi` (cio_reset syscon, usb4_1_mbox, usb4_1_acio, usb4_1_dart, usb4_1_nhi, usb4_1_pcie_dart, usb4_1_pcie `apple,t8132-pcie-tunnel`) | none for T8132 | all | ✔ mbox 0x409108000 irqs 1378..1381; rc 0x409ac0000 (3×0x4000); nhi 0x409f00000, pdf 0x409db0000+0x30004; DART 0x409a80000 irq 1376 with 24 streams; apciec1 config 0x1c60000000, rc, port0, fabric, debug, ltssm and intr2axi; irq 1329; DART 0x40c000000 irq 1330; msi-vector-offset 1506 (+128 = 1634). ✗ sram 0x409080000, cio_reset at 0x380780000+8, the NHI tx/rx IRQ order, and `adapter` = acio1 reg[5] (0x409e44000). |
| `nvme`, `ans_mbox`, `sart` (static addresses in Gravity) | placeholders filled by the loader; aliases on the base since 1b90344fe637 | none | Gravity's static `nvme` 0x4c5cc0000+0x60000 does **not** match the ADT (0x485cc0000+0x60000 and 0x4c5cc0000+0x10000), so Aurora's loader-filled design is safer |
| `smc` (enabled), `smc_hwmon`, hwmon-common/mini includes | `smc` disabled in the SoC, enabled by J713 | J773g must enable smc and smc_mbox; `smc_gpio` is needed for Wi-Fi and HDMI power | ✔ |
| `nub_spmi0` + `pmic1@e`, `nub_spmi_a1` | Aurora: loader-filled `nub_spmi` + J713 pmic1 | not ported. RTC/reboot are out of scope. The J773g ADT has no `nub-spmi-a1`. | ✔ pmu-main on nub-spmi0 |
| `ramoops`, PMP research `apple,always-on` votes, `pmp_report_*` entries | Aurora has its own PMP path (already in the J773g base) | intentionally not ported | — |
| `framebuffer0` → dispext0_fe + dptx_phy | already present in Aurora J773g | — | — |

## 2. Driver support Aurora lacks (`git grep` on elementaryos-mseries)

| Need | Aurora state | Where support exists |
|---|---|---|
| **DCP for an external T8132 display** | `apple,t8132-dcp` → `iomfb_m4_init()` refuses unless `of_machine_is_compatible("apple,j713")` and firmware UUID 81BAF476…; there is no `apple,t8132-dcpext` match (falls back to generic `apple,dcpext`); DART display adoption is J713-gated (`apple-dart.c` j713_display) | Gravity `replacement/200-dcp` (dcp.c handles `apple,t8132-dcpext`) |
| **DPTX PHY T8122/T8132** (`apple,t8122-dptx-phy`) | `dptx.c` matches only t6020/t8112; `apple,dptx-phy` alone binds nothing | Gravity `replacement/171-dptxphy` d4f1cfe0f816 (adds `apple,t8122-dptx-phy`). It is **also missing from Gravity 000-devicetree**. |
| tipd `sn201202x` | ✔ `apple,t8132-sn201202x` with select polled on T8132 | — |
| ATC SuperSpeed | ✔ T8132 7-bank layout (no machine gating) | — |
| ATC `apple,fixed-usb3` / `fixed-lane-swap` (front hub) | ✗ | Gravity `replacement/170-atc` |
| dwc3 `apple,t8132-dwc3` | ✔ | — |
| **USB4 ACIO/NHI T8132** | `thunderbolt/apple.c` matches only `t8103-usb4-acio/nhi` fallbacks (no T8132 entry); the DP-in policy SoC allowlist excludes t8132 | Gravity apple.c (fallback only) |
| **PCIe-C tunnel T8132** | `pcie-apple.c` has t8103/t8112/t8122/t6000 pciec and no T8132; the tunnel's BAR attribute path checks `t8103` | Gravity 000-devicetree `apple,t8132-pcie-tunnel` / `t8132_tunnel_hw` (max_rid2sid 256, msi-vector-base) |
| **CIO reset T8132** | `reset-apple-cio.c`: "The t8132 layout has not been decoded." | Gravity uses the `t6000-cio-reset` fallback at 0x380780000 (not verified) |
| **MCA T8132** | `mca.c` matches only `t8103-mca`/`mca` | Gravity mca.c `mca_t8132_variant` (different cluster/switch layout) |
| **`apple,j773g-speaker` machine driver** | ✗ | Gravity `sound/soc/apple/t8132/*` (d1d4269fcce1) plus bindings `apple,j773g-speaker.yaml` and `apple,mca.yaml` |
| admac T8132, cs42l84, tas2764 (sn012776) | ✔ | — |
| SIO T8132 | generic `apple,sio` fallback only | Gravity apple-sio.c `apple,t8132-sio` |
| PCIe RC T8132, brcmfmac 4388, hci_bcm4377 0x5f72 | ✔ (the managed-SID path is J713-only; J773g takes the generic path) | — |
| NVMe `apple,t8132-nvme-ans2` | ✔ (loader-filled) | — |

Result: commits 01-02 and 06-10 can work with Aurora's current drivers, giving PCIe Wi-Fi/BT/Ethernet, USB-C PD and USB2/USB3. NVMe already depends only on the loader. Commits 03/11 (audio), 04/12 (HDMI) and 05/13 (USB4) are DT-ready but need the driver ports listed above.

## 3. Proposed commits on top of elementaryos-mseries (1b90344fe637)

Draft diffs are in `/private/tmp/claude-501/kern/audit/`. They are cumulative and apply in order with `git apply` / `patch -p1`. The builder is `tools/build.py` and the stage trees are `work/s0..s13`.

SoC commits (`t8132.dtsi`, `t8132-pmgr.dtsi`, new `t8132-usb4.dtsi`). Every new node is `status = "disabled"`.

| # | File | Content | Verified |
|---|---|---|---|
| 01 | `dt-01-t8132-pcie-port2.diff` | `dart_apcie2`; pcie0 `port2`/`phy2` reg + 3 port IRQs; disabled `port02` | all ADT |
| 02 | `dt-02-t8132-atc2-atc3-usb.diff` | atcphy2/3, dwc3_2/3, DARTs in Aurora's USB2-base style | all ADT |
| 03 | `dt-03-t8132-audio.diff` | `pmgr_audio` + 7 `ps_audio_*`; `dart_audio`, `mca`, `admac` | pmgr offsets, dart, admac: ADT; MCA addr: Gravity only |
| 04 | `dt-04-t8132-dispext0-dptx.diff` | dispext0/dcpext0 DARTs, mbox, `dcpext0` (`apple,t8132-dcpext`), `pmgr_dcp` (named `dcp-pmgr@` so it does **not** merge into Aurora's `pmc` node at the same address; I caught this when decompiling), `dptxphy` | ADT except bw-scratch offset |
| 05 | `dt-05-t8132-usb4-acio1.diff` | new opt-in `t8132-usb4.dtsi` in Aurora's convention (`apple,pcie-tunnel` → `usb4_1_pcie_tunnel` / `apciec1` `apple,t8132-pciec`, relative `ranges`) | see table above |

Board commits (`t8132-j773g.dts`):

| # | File | Content | Driver-ready? |
|---|---|---|---|
| 06 | `dt-06-j773g-smc-hwmon.diff` | binding headers; enable `smc`/`smc_mbox`; `smc_hwmon` + hwmon-common/mini | yes |
| 07 | `dt-07-j773g-pcie-wifi-bt-ethernet.diff` | dart_apcie0/2, pcie0 bus-range 0-2 + iommu-map (SID 16 on both DARTs, as in Aurora's default), port00 pwren/PERST + sakhalin wifi0/bt0, port02 Ethernet | yes |
| 08 | `dt-08-j773g-typec-usb2.diff` | hpm0/1/3 (`apple,t8132-sn201202x`, ADT IRQs), connectors and labels, atcphy0/1/3 + dwc3 host USB2 graph, front hub on ATC2 (USB2) + GPIO hogs | yes |
| 09 | `dt-09-j773g-typec-superspeed.diff` | 7-bank SS reg override for atcphy0/1/3 (J713 ATC1 layout), dwc3 USB3 phys | yes in the driver; on J713 only ATC1 SS was qualified |
| 10 | `dt-10-j773g-hpm-select-irq.diff` | **optional**: add `select` 13/39/65 (Gravity 4cb9998f58) | driver accepts it; untested on Aurora |
| 11 | `dt-11-j773g-audio.diff` | speaker-audio, i2c3 amp, i2c1 jack codec, enable audio DMA/MCA | needs MCA t8132 + machine driver |
| 12 | `dt-12-j773g-hdmi-dcpext0.diff` | enable dispext0/dcpext0/dptx; HDMI-A, `apple,dptx-phy = <4>`, pwren GPIOs, **hdmi-hpd** | needs dptx t8122 + DCP t8132-dcpext + DART admission |
| 13 | `dt-13-j773g-usb4-acio1.diff` | include t8132-usb4.dtsi, enable ACIO1, graph to typec1 | needs pciec/ACIO/CIO-reset for T8132 |

Suggested landing order: 01, 02, 06, 07, 08 first (functional with Aurora's drivers), then 09, then 10 if polling select proves slow. Hold 03/11, 04/12 and 05/13 until their driver commits are on the branch. Alternatively, land the SoC halves 03/04/05 alone, since they are disabled.

## 4. Risks and things I could not verify

1. **Which DCP drives HDMI.** Gravity drives HDMI from **disp0 (`&dcp`)** with `phys = <&dptxphy>` and never enables `&dcpext0`; it enables only that pipe's DART and mailbox. In the ADT, `disp0` has `external = 1`, both dcp (ufp-endpoint 0) and dcpext0 (ufp-endpoint 1) hang off display-crossbar0, and the dptx-phy dfp-endpoint is 4. The framebuffer power domains (dispext0_fe) suggest iBoot scans out on dispext0, which is why the draft uses dcpext0 as requested. If Aurora's DCP work goes the disp0 route instead, `t8132-j713-display.dtsi`'s dcp nodes must move to the SoC dtsi first. HDMI audio follows the same choice: dcpext0 pairs with dp-audio1 (DPA1), dcp with dp-audio0.
2. **select IRQ.** The ADT has no select line. Aurora deliberately polls on T8132, while Gravity's 13/39/65 is empirical. Commit 10 is therefore optional.
3. **PCIe SoC change touches J713.** Commit 01 adds port2 reg and IRQs to the shared `pcie0`. Those values are J773g-ADT-verified, not J713-verified. If that matters, move them into a board override. Port1 was left out because the J773g ADT has no bridge1 or dart-apcie1. MSI: ADT bridge2 has `msi-vector-base = 64`, while Aurora keeps 32 vectors from 1506.
4. **USB4.** NHI tx/rx IRQ order (the ADT lists 1361..1372 first), sram at 0x409080000, the `adapter` aperture, the CIO reset register (undecoded upstream) and the DART 1-cell + `apple,dma-range` form (Aurora's t8122 uses 5-cell) are all taken from Gravity. Gravity marks USB4 "EXPERIMENTAL", untested on J713.
5. **Front hub at USB2 only** until `apple,fixed-usb3` support is ported. The behaviour of atcphy2 with no Type-C mux is also untested on Aurora's atc.c.
6. **Audio.** The MCA address and the per-cluster layout come from Gravity only; `dart_audio` is the AOP's DART, shared with AOP firmware. The admac DMA channels 0/2/4 cannot be checked.
7. **dcpext0 values.** `apple,bw-scratch` offset 0x2c000 and `apple,dcp-index = <1>` come from Gravity. Aurora's J713 dcp uses `disp-4`/`iop-vbar` regs instead of bw-scratch, so the right form depends on the DCP port chosen.
8. **Not run:** `make dtbs_check`, any boot test, and the binding YAML for the new compatibles (`t8132-dcpext`, `t8132-pciec`, `t8132-usb4-*`, `t8132-cio-reset`, `j773g-speaker`, `t8132-mca`).
9. **Loader dependencies.** m1n1 must fill the Wi-Fi/BT/Ethernet MACs, the NVMe/ANS nodes (aliases already on the base), the Thunderbolt DROM and the DCP firmware properties for J773g. I did not check whether Aurora's m1n1 does this for J773g.

Supporting files: `adt-armio.txt` (translated arm-io nodes), `adt-pmgr.txt` (decoded PS addresses), `src/` (extracted sources), `tools/` (adt.py, pmgr.py, build.py, compile.sh), `work/s0..s13` (stage trees).
