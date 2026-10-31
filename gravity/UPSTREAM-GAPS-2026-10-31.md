# Gravity → Aurora aurora-wip: M4 mini gaps (2026-10-31)

Direction: Gravity's M4 work is ported **up** into Aurora's own code (Aurora's `drm/asahi/g16/` GPU backend,
Aurora's DCP), one focused commit per fix, so each can go to `aurora-silicon/linux` as a PR. Our fork's
`elementaryos-mseries` branch, based on `aurora-wip`, is where we do the work and get the mini booting.
**Nothing is ported until the owner approves this list.**

Compared: `aurora-silicon/linux` `aurora-wip` @ `23e431a98962` against `techmore/linux-m1pro-touchid`
`m4-mini-gravity` @ `6363990c4a45` (Gravity `gravity-m4` 4fc326f6 plus patches 0066/0067 and the modular DRM exports).

## Method

74 Gravity commits since 2026-09-10. Nine match Aurora by subject. The rest were checked by feature in
Aurora's tree, since Aurora often implements the same hardware under other titles.

## Already in Aurora (no port needed)

T8132 base and J773g board device trees, SMC, USB/ATC PHY and PCIe nodes; T8132 NVMe (ANS2); PCIe pwrctrl;
ADMAC split channel banks; DCP 26.6.x (`iomfb_v26_6`) and the 26.6.2 compatible string; the M4 G16 GPU
backend (Aurora's own design, `drm/asahi/g16/`); BCM4388 Bluetooth calibration; the M4 KVM SEIS workaround;
the dockchannel HID (MacBook Air M4 keyboard).

## Gaps to port (pending approval)

| # | Feature | Gravity commit(s) | Target in Aurora |
|---|---|---|---|
| 1 | USB-PD select interrupt on SPMI SID 8 | `4cb9998f58` | `t8132.dtsi` |
| 2 | T8132 audio controllers and power domains | `bab8e9680f` | `t8132.dtsi` |
| 3 | MCA T8132 banked TX path | `3abcc2c929` | `sound/soc/apple/mca.c` |
| 4 | TAS2764 fail-closed protected attenuation | `3d8f93470e` | `sound/soc/codecs/tas2764.c` |
| 5 | J773g kernel-protected speaker, enable in DT | `9cec671477`, `497a835b7c` | `sound/soc/apple/`, `t8132-j773g.dts` |
| 6 | T8132 HDMI audio over DCP | `49045c3465` | `drivers/gpu/drm/apple/{audio,av}.c` |
| 7 | SMC `gp00` GPIO keys (power button) | `3988dac166`, `f33138368c`, `ab76ccfdd0` | `mfd/macsmc`, `gpio-macsmc`, binding |

| 8 | **M4 GPU: the Gravity fixes that made it run well** — on a lost or late firmware notification, poll the completion stamps and rescue finished work instead of failing the pipeline; cap the wait at 250 ms while work is in flight (patch 0066, `071d8cfd40`; Gravity `replacement/210-gpu` `g16_drm_pump.rs`) | `071d8cfd40` | Aurora `drivers/gpu/drm/asahi/g16/` submission/retire path |

Order: 1 first (smallest, DT only), then 8 (the GPU, which Omarchy and elementary need), then 7, then audio 2→5, then 6.

Gap 8 is re-implemented in Aurora's driver, not copied: the two drivers share the idea, not the code. If
Aurora's loop turns out not to have the bug, gap 8 becomes "find why the mini GPU is disabled in this
draft's candidate" instead.

## GPU: not a straight port

Gravity's M4 GPU driver (flat `g16_*.rs`) and Aurora's (`g16/` directory) are separate designs; the kernel
can build only one. Upstream means fixing Aurora's backend, not replacing it.

- The 2026-10-28 GPU deaths (`GPU-HANG-2026-10-28.md`) are a bug in **Gravity's** driver: a notification
  wait timeout failed the pipeline before `retire()` polled completion. Patch 0066 fixes it there.
- To check next, in Aurora's `g16/`: whether its submission loop has the same "timeout before retire"
  pattern. A keyword search found timeout handling but proved nothing about this path.
- This draft's candidate keeps the mini GPU disabled. That matches the owner's report: the Omarchy install
  screen came up and then failed, because Hyprland needs a working GPU.

## Local state (not on GitHub)

- `elementaryos-mseries`: created locally at `aurora-wip` `23e431a98962`, no changes yet, not pushed.
- `ref/gravity-wholesale`: a trial merge that replaced Aurora's GPU and DCP trees with Gravity's (80
  conflicts, Gravity's graphics wholesale). **Rejected**: the wrong direction for upstreaming. Not pushed.

## Next, after approval

1. Push `elementaryos-mseries` (= `aurora-wip`) to `techmore/linux-m1pro-touchid`.
2. Port gaps 1–7 as separate commits on it, each written against Aurora's code.
3. Build with this repo's CI; boot on the mini with the HDMI fallback and the rescue entry.
4. Open one PR per gap against `aurora-silicon/linux` `aurora-wip`, after checking Aurora's open PRs for
   the same work.

## Correction (same day): the mini's board description is the main gap

The feature check above looked at the shared SoC file `t8132.dtsi`. The mini's own board file is where Aurora
is missing almost everything:

| Branch | `t8132-j773g.dts` |
|---|---|
| Aurora `aurora-wip` / `integration/aurora` | 25 lines: CPU and serial only (the mainline 7.4 minimal tree) |
| Gravity / `m4-mini-gravity` | 300 lines: display (DCP and external), HDMI audio, NVMe, USB-C with USB-PD, Wi-Fi, Bluetooth, speaker |

- 28 of the 34 node labels Gravity's mini board uses are not in Aurora's shared T8132 files (audio: admac,
  mca, sio, dart_audio; display: dcp, dcpext0/1, dispext0/1, dptxphy, dpaudio0; USB-C: atcphy2/3, dwc3_2/3,
  typec0/1; PCIe Wi-Fi: pcie2_dart, port02, wifi0, bluetooth0). Aurora defines dcp, wifi0, bluetooth0 and
  typec0/1 only in the J713 (MacBook Air) files.
- Aurora's G16 GPU node exists only in `t8132-j713-gpu.dtsi`, and m1n1 fills its UAT and firmware ranges
  at boot. **An Aurora kernel on the mini has no GPU node**, which matches the Omarchy installer bringing up
  a GUI and then failing on the GPU.
- All 15 of Aurora's open M4 PRs (checked 2026-10-31) are for J713. None cover J773g.
- Gap 1 (USB-PD select interrupt) applies to Gravity's `usb-pd@8` node, which Aurora does not have yet; it
  is folded into the USB-C work below.

### Revised port order (GPU first, as approved)

1. **GPU on J773g in Aurora**: a J773g GPU device-tree include on Aurora's pattern
   (`t8132-j713-gpu.dtsi`), plus m1n1 J773g GPU handoff. This draft's `wip5/0010-m1n1-j773g-gpu-resource-draft`,
   `0011-j773g-gpu-dt-draft` and `0012-uboot-j773g-gpu-import-draft` are the starting point. Values come from
   the J773g ADT (GravityLinux/adt-collection), not from J713.
2. **Gap 8**: the GPU notification-timeout fix in Aurora's `g16/` loop, if the bug is present there.
3. **Display and HDMI**: move dcp/disp nodes from the J713-only files into shared T8132 files, then enable
   them for J773g.
4. **USB-C** (with Gravity's USB-PD fix), **PCIe Wi-Fi and Bluetooth**, **NVMe** board wiring.
5. **Audio**: gaps 2 to 5, then HDMI audio (gap 6), then the SMC power keys (gap 7).
