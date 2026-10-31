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

Order: 1 first (smallest, DT only), then 7, then audio 2→5, then 6.

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
