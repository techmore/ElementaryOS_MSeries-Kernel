# Gravity → Aurora driver audit for the Mac mini M4 (J773g, T8132)

Target: `elementaryos-mseries` (aurora-wip 23e431a98962 + 3 J773g G16 commits).
Gravity refs: `gravity/replacement/*` and `gravity/bits/084-bcm4388-wifi`. Both share the base
`c03c1a14507d` (v7.3-rc3-2579).
Method: read-only `git show/grep/diff`, plus `git merge-tree --write-tree --merge-base=<c>^ elementaryos-mseries <c>`.
Nothing in the repo was modified.

## Main finding

What separates Aurora from Gravity on the mini is mostly **device tree, not driver code**. Aurora's
`t8132-j773g.dts` only has simplefb, PMP and the GPU. Aurora's `t8132.dtsi` has no `dptxphy`, `dcpext*`,
`sio`, `mca`, `admac`, `dart_audio`, `dwc3_2/3` or `atcphy2/3` nodes. J773g also has no Type-C controller,
wifi, ethernet, speaker amplifier or HDMI DCP properties. Aurora's own drivers already cover most
of the T8132 driver work (atcphy, dwc3, tipd SN201202x, PMP report, BCM4388 including C2). Most of the
Gravity commits listed are for the Neo (T8130/T8140, `apple,j700`) or the M4 Max, not the mini.

The two DCP stacks have diverged too far to merge: `a8aa5e2f7d1d` conflicts in 25+ files. Gravity
drives HDMI on the mini from the **main `t8132-dcp`** with firmware 26.6.2 using its generic `DCP_FIRMWARE_V_26_6`
path, which it shares with T6041. It also uses `phys=<&dptxphy>`, `apple,dptx-phy=<4>`, and the `hdmi-pwren`
(smc_gpio 15) and `dp2hdmi-pwren` (smc_gpio 26) GPIOs. Aurora's equivalent is its **`DCP_FIRMWARE_V_26_6_DESKTOP`** path,
which already drives HDMI on T6041 (M4 Pro/Max). It already has the `dp-phy`, `apple,dptx-phy`,
`hdmi-pwren`/`dp2hdmi-pwren` and `dcp_desktop_dp2hdmi_hpd` plumbing. Aurora currently pins `t8132-dcp` to `DCP_FIRMWARE_M4`
(`iomfb_m4.c`), and that path rejects any board other than J713.

## Ranked recommendations (HDMI, USB-C and speaker first)

| # | Item | Mini relevance | Aurora today | Port difficulty | Recommendation |
|---|------|----------------|--------------|-----------------|----------------|
| 1 | `d4f1cfe0f816` dptx.c T8122 PHY activation (+143/−6) | **Required for HDMI.** On Gravity the mini's `dptxphy` is `apple,t8122-dptx-phy`. This commit adds the cold-activation sequence, the link-rate tweaks, runtime PM, and no-op callbacks until activation completes. | Stock dptx.c (T8112/T6020 only). There is no t8122/t8132 compatible and no binding. | **Applies cleanly** (merge-tree rc=0). | **Port as-is**, then add a node to `t8132.dtsi` (reg 0x39a700000/0x39a740000, `ps_dptx_phy`). Consider removing or hiding the `t8122_activation_stage` debug parameter. The `apple,t8122-dptx-phy` binding is still missing upstream and in Aurora. SoB: Cody Ho. |
| 2 | HDMI DCP enablement (concept from `a8aa5e2f7d1d` and the Gravity J773g DTS) | **Required for HDMI.** | Aurora has the desktop 26.6 and DP2HDMI machinery for T6041. `t8132-dcp` goes through iomfb_m4 and is gated to J713 only. | Do not merge `a8aa5e2f7d1d` (25+ conflicting files, Neo-centred). | **Adapt** instead: add a J773g-gated `t8132-dcp` hw-data variant that selects `DCP_FIRMWARE_V_26_6_DESKTOP` (fw/compat 26.6.2) with `num_dptx_ports = 2`. Add DT for `dcp`, `dcp_dart`, `dcp_mbox`, `disp0_dart`, `dptxphy`, the pwren GPIOs and `apple,connector-type="HDMI-A"`. Open questions to check on hardware: whether HDMI is on `dcp` (Gravity) or `dispext0` (simplefb power domains), and whether the T8132 firmware's ABI really matches the T6041 one (Gravity treats them as the same). Medium-large effort. |
| 3 | `b99716311d0a` dptxep/av (+7/−4) | It makes M4 firmware default to 4 lanes before Type-C, and treats av 14.7 as -ENODEV. | Aurora's `get_max_lane_count` already defaults to 4 lanes. | Conflicts. | **Skip.** It is already equivalent. It also has no Signed-off-by. |
| 4 | `d1d4269fcce1` audio subset: `sound/soc/apple/t8132/*`, MCA `apple,t8132-mca` variant (+208 in mca.c), TAS2764 protected-attenuation exports (+63), Kconfig, `t8132-audio.config`, `apple,j773g-speaker.yaml` | **The mini's internal speaker**, specific to J773g: MCA TX0 → SN012776 on i2c3@0x38, shutdown GPIO pinctrl_ap 15, in-kernel voice-coil thermal limiter, ceiling_dvc default −10 dB. | No t8132 MCA, no speaker driver, no audio DT nodes. Aurora already has `apple,t8132-admac` and the SN012776 TAS2764 support. | The whole commit is a 49-file baseline with 15 conflicts. Taking only the sound files: the new `t8132/` directory adds cleanly, while `mca.c` and `tas2764.c` conflict (Aurora diverged by +38/−39 and +194/−28). | **Adapt (cherry-pick by path).** Take `t8132/`, the Kconfig/Makefile hunks and the binding. Hand-merge the MCA variant table and the three TAS2764 exports. Add DT for `pmgr_audio`, `dart_audio`, `mca`, `admac`, `i2c3` and `speaker_amp`. Keep it `=m`, off by default and labelled experimental: the thermal model is unvalidated and has no speakersafetyd. Provenance: SoB Cody Ho, "Assisted-By: LLM"; the binding names Niklas Sheth as maintainer, so confirm the original author before submitting. The `apple-sio.c` and `apple-admac.c` hunks in the same commit are only needed for DP audio (SIO); skip them. |
| 5 | USB-C DT (Gravity `t8132-jxxx.dtsi` and J773g) | **Needed for working USB-C ports.** hpm0 @0xc (irq 11/13/17/19) and hpm1 @0xa (37/39/43/45) on `nub_spmi_a0`; hpm3 @0x8 (63/65/69/71) for back-right; front ports behind a host-only hub on dwc3_2/atcphy2 (hub GPIO hogs 101 and 198). | Aurora's drivers support T8132 atcphy, dwc3 and `apple,t8132-sn201202x`, but J773g has no Type-C or USB DT, and `t8132.dtsi` lacks dwc3_2/3 and atcphy2/3. | DT only. Aurora's atcphy binding differs (reg 0x402a90000 vs Gravity's 0x403000000), so write it against Aurora's binding. | **Adapt in DT.** Use the `apple,t8132-sn201202x` compatible. For the front hub, use Aurora's `fixed_usb2` model, not Gravity's `apple,fixed-usb3`. |
| 6 | `6fb65d04c626` / `f8a1b1678a3b` ATC PHY (+718) | Neo (T8130) USB3/DP lane modes, plus Gravity's `fixed-usb3` / `fixed-lane-swap`. On Gravity the mini uses the generic t8122 path. | Aurora has its own T8132 atcphy (banks, BIST, cold start, fixed-hub). | Both conflict. | **Skip.** Only reuse the `fixed-lane-swap` idea if the front hub's SuperSpeed path turns out to need it. |
| 7 | `9ac24677df3c` / `8ca0d7d07e85` dwc3 (+280) | Neo shared-host ports (`apple,j700`, `apple,shared-host-ports`), plus a modpost fix for that code. | Aurora's dwc3-apple has T8132 handling throughout. | Conflicts. | **Skip.** It is Neo-specific. |
| 8 | `81c7d6bb4cf4` tipd (+24/−6) | `cd321x_mux_set` (role NONE before mux, not on J700) and a `ti,tps66993` match. | Aurora's tipd has a much larger SN201202x/T8132 implementation. | Conflicts. | **Skip.** Revisit the role-before-mux idea only if DP alt-mode on the mini's USB-C needs it. The commit has no Signed-off-by. |
| 9 | `e6337f4995de` tipd `read_power_status` (+1) | Prevents a NULL call on SN201202x. | **Already present** in Aurora's `tipd_sn201202x_data`. | — | **Skip** (not needed). |
| 10 | `e8ad72de4e50` PMP report (+130) and RTKit (+115) | Post-ready "finalize" bit flips for T8132 PMP (research), plus RTKit adopt/reuse APIs. | Aurora has its own `apple,t8132-pmp-v2-report` and `apple_rtkit_adopt_running`, and our branch already admits J773g. | Conflicts in pmp-report.c and rtkit.c. | **Skip.** It is experimental, has no Signed-off-by, and duplicates Aurora's API with different signatures. Read it only as a reference if PMP idle power becomes a goal. |
| 11 | `6f0d9dc10e1b` BCM4388 base, `fb50041b5899` 4388C2 / DPP / port-authorized, `a3b22cf5758c` (wifi-only split: `BRCMF_BSS_INFO_MAX_VERSION` 112→116) | Wifi on all M4 machines. | Aurora already has 4388 B0/C0/C2, the OTP read, DPP, `cfg80211_port_authorized` and the T8132 IOVA aperture fixes. | All conflict, because the changes are already there. | **Skip 6f0d/fb50.** `a3b2` is a 1-line candidate if scans drop BSS-info v113–116 entries; check firmware logs first. The real gap is DT: J773g has no `wifi0`/`bluetooth0` (Gravity uses `brcm,board-type="apple,sakhalin"`) and no `port02` ethernet or `pcie2_dart`. |

## Notes

- `a3b22cf5758c` is titled "drm/apple: bring up T8132 DCP hotplug [wifi]" but contains only the wifi
  hunk from the split. The DCP part of Niklas's original commit (877c574d / 6dea1d39) is folded
  into Gravity's baseline `d332256c62d5` and into `a8aa5e2f7d1d`; neither original commit object is in the clone.
- Several "EXPERIMENTAL: retain original M4 changes" commits (`b99716311d0a`, `81c7d6bb4cf4`, `e8ad72de4e50`,
  `fb50041b5899`) have **no Signed-off-by**, so they cannot be taken as-is for DCO. Every Gravity commit is marked
  "Assisted-By: LLM". All touched files are GPL-2.0(-only) or GPL-2.0 OR MIT, which is compatible with Aurora.
- Suggested order: (1) dptx.c + dptxphy DT → (2) J773g DCP desktop-26.6 variant + HDMI DT → (3) USB-C DT →
  (4) speaker (opt-in) → (5) wifi/BT/ethernet DT.
