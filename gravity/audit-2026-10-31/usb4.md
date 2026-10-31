# Mac mini M4 (J773g / T8132): USB4/Thunderbolt on the rear USB-C ports

Branch: `techmore/linux-m1pro-touchid` **`mini/usb4`**, on `elementaryos-mseries` fa26b0f92ef6.
Worktree: `/private/tmp/claude-501/wt/usb4`. CI: `elementaryos-mseries-kernel.yml` run 41208881043 (see end).

## Bottom line for the Dell U2725QE

- **Nothing on this branch can make USB4 work on the mini yet.** Two blockers remain, and the ADT supplies neither:
  1. **CIO reset.** The T8132 layout is undecoded. The ACIO driver requires a reset, so the routers cannot probe.
  2. **ATC PHY USB4/TBT mode on T8132.** `atcphy_configure_t8132()` accepts only OFF, USB2, USB3 and USB3_DP. TBT and USB4 return `-EOPNOTSUPP`.
- **The dock's USB hub** should already enumerate on a rear port through the existing USB2/USB3 DT (dt-08/09, already on the base). That path needs no USB4.
- **Video from a USB-C dock monitor** most likely arrives as **DP Alt Mode**, not as a USB4 tunnel. Most "USB-C hub" monitors are DP Alt Mode only. I did not check whether the U2725QE negotiates USB4/TB: plug it into a rear port on macOS and rerun `system_profiler SPThunderboltDataType SPDisplaysDataType`. The T8132 ATC already has a USB3_DP mode (`apple,tunable-usb3-dp`). DP Alt Mode still needs the same display-side work as HDMI: dcpext for T8132, the display crossbar, and dptx T8122. That work belongs on the HDMI track, not here. **DP Alt Mode is the shorter route to dock video.**

## Commits (in order)

| # | Commit | What |
|---|---|---|
| 1 | `bcfac1dda8fc` thunderbolt, PCI: apple: add T8132 ACIO and PCIe-C entries | `apple,t8132-usb4-acio` gets `apple_cio_t8132_hw` with mxwrap, lstx_explicit, strict_fw_ready and DP IN **disabled**. `apple,t8132-pciec` gets `t8132_pciec_hw`, a copy of t8122_pciec_hw, plus an ADT-derived MSI slice check gated on `apple,t8132` and the ECAM base. reset-apple-cio: comment only, recording the ADT facts. **There is no T8132 reset entry.** |
| 2 | `04942800f17d` arm64: dts: apple: t8132: describe USB4 routers ACIO0/1/3 and PCIe-C | New opt-in `t8132-usb4.dtsi`. Every node is disabled. |
| 3 | `56268a15f24c` arm64: dts: apple: t8132-j773g: wire the rear USB-C ports to USB4 | Includes the dtsi, adds `usb4_N_{rc,nhi,pcie,pcie_adapter}` aliases for m1n1, and the Type-C graph typec0/1/3 `port@2` ↔ usb4_0/1/3 acio `port@1`. Routers stay **disabled**. |
| (3) | DP-in tunnel policy | **Not done; it does not fit cleanly.** T8132 has no qualified display crossbar or external DCP on this tree, so `.dp = &apple_dpin_disabled`. |

Other SoCs are unchanged. The new hw structs are reached only through the new compatibles, and the MSI check only for `t8132_pciec_hw`. The J713 DTB is byte-identical to the base.
DT build (`dtcbuild`, `dtc-branch.sh` flags): j773g, j713, j604, j715, j623 and j624 all compile with 0 errors. The only new warning is dtc `alias_paths` for the `usb4_N_*` names. The kernel suppresses that warning by default, t8122/t603x use the same names, and m1n1 requires the `usb4_N_pcie` spelling.

## Port mapping (ADT + macOS)

| Rear receptacle (macOS) | USB-PD | ATC | ACIO | PCIe-C | ADT acio port-number |
|---|---|---|---|---|---|
| 1, back-middle | hpm0 @0xC | atc-phy0 | acio0 / acio-cpu0 | apciec0 | 1 |
| 2, back-left | hpm1 @0xA | atc-phy1 | acio1 / acio-cpu1 | apciec1 | 2 |
| 4, back-right | hpm3 @0x8 | atc-phy3 | acio3 / acio-cpu3 | apciec3 | 4 |

The ADT pairs each acioN with its atc-phyN through `atc-phy-parent` (267/273/289). There is no acio2 or apciec2.

## Values: what the ADT verifies and what it does not

All arm-io addresses used are identity-mapped (the arm-io `ranges` cover 0x40N000000 and the PCI windows 1:1).

| Item | acio0 | acio1 | acio3 | Source |
|---|---|---|---|---|
| mailbox (acio-cpuN reg[0]) | 0x401108000, irq 1316-1319 | 0x409108000, 1378-1381 | 0x419108000, 1502-1505 | ADT ✔ (ADT lists them N+1,N,N+3,N+2; DT ascending as usual) |
| cpu / MxWrap (acio-cpuN reg[1]) | 0x401100000 | 0x409100000 | 0x419100000 | ADT ✔ (`iop,mxwrap-acio`) |
| sram | 0x401080000+0x20000 | 0x409080000 | 0x419080000 | ADT ✔: acio-cpuN `segment-ranges` __DATA, IOVA 0x10000000 = driver's `APPLE_CIO_SRAM_IOVA_BASE`. This **resolves** the audit's "sram unverified". |
| rc (acioN reg[2..4]) | 0x401ac0000+0xc000 | 0x409ac0000 | 0x419ac0000 | ADT ✔ |
| pcie-adapter (acioN reg[5]) | 0x401e44000 | 0x409e44000 | 0x419e44000 | ADT ✔ (`pcie_adapter_regs_tunables` sits on acioN, as on t6030). Gravity misnamed this as the PCIe-C "adapter". |
| nhi / pdf (acioN reg[0..1]) | 0x401f00000 / 0x401db0000+0x30004 | 0x409f… | 0x419f… | ADT ✔ |
| ACIO DART | 0x401a80000 irq 1314 | 0x409a80000 irq 1376 | 0x419a80000 irq 1500 | ADT ✔; 28 SIDs, TX N=SID N, RX N=SID 16+N ✔; vm-base 0x10000000000 ✔. **Window length 0x1000000000 is t6030's**; the ADT vm-size is 0x30000000000. |
| NHI ring IRQs | tx 1287-1298, rx 1299-1310 | tx 1349-1360, rx 1361-1372 | tx 1473-1484, rx 1485-1496 | **Not from the ADT.** The ADT lists the upper block first. TX = lower block follows Gravity and joshuaswarren's T8152 hardware observation (ring 0 only). |
| power-domains | atcN_cio, _cio_pcie, _cio_usb (+ atcN_pcie) | same | same | ADT power-gates ✔ (98/99/113, 116-118, 129/131/132); the 4th (ATCn_PCIE) follows t6030 and Gravity |
| LSTX pin | AOP 17 | AOP 19 | AOP 23 | ADT `gpio-lstx` ✔ for the pin; **function 1 is assumed** (t8122/t6030 convention) |
| PCIe-C config/rc/port0/fabric/debug | 0x1c50000000, 0x404034000, 0x404020000(+0x8000), 0x404038000, 0x404060000 | 0x1c60000000, 0x40c0… | 0x1c80000000, 0x41c0… | ADT reg[0..4] addresses ✔. **Names are inferred** from the T6030 order (rc→fabric +0x4000 matches). |
| PCIe-C reg[5..7] | 0x400020000 (inside the ATC0 aperture), 0x40402c000, 0x404028000 | … | … | **Unnamed, left out.** Gravity calls them adapter/ltssm/intr2axi, but that conflicts with T6030 offsets. oe-fabric is probably apciecN-piodma reg[3] (rc+0x8000, carries the oe-fabric tunables); also left out. |
| PCIe-C irq / DART | 1267 / 0x404000000 irq 1268 | 1329 / 0x40c000000 irq 1330 | 1453 / 0x41c000000 irq 1454 | ADT ✔; DART vm-base 0x10080000000, size 0x7ff00000 ✔ |
| MSI | AIC 1602, base 96 | AIC 1634, base 128 | AIC 1698, base 192 | ADT ✔ (`msi-vector-offset` 1506 + pcicN-bridge `msi-vector-base`, 32 vectors) |
| PCI windows | 64b 0x8_00000000+8G, 32b 0xa00100000, pref 0xa40000000 | 0xc / 0xe | 0x14 / 0x16 | ADT ✔ (the ADT stores bus addresses as hi, lo, mid) |
| **CIO reset** | — | — | — | **Not in the ADT.** acio-cpuN has `function-reconfig_req_interrupt = pmgr:RIRQ(0x152/0x153/0x155)` = CIO0/1/3_RECONFIG-V (338/339/341). The PMGR maps 0x180780000→**0x380780000** (reg[36], the same page as t8142). Offset and bits are unknown. The reset driver's own history says T8132 indexes a per-port table and is undecoded. **Left out.** |
| PCIe-C port registers (doorbell/PERST/RID2SID at t8103 offsets, t602x MSIMAP) | | | | **Not from the ADT**: Gravity's `t8132_tunnel_hw` and Aurora's T6030 (t8122_pciec_hw) both use this layout. Gravity's `max_rid2sid = 256` was **not** copied: 256 entries from 0x828 would run into PORT_TUNCTRL (0x988). Gravity's "TUNNEL_GATE" at port+0x1088 was not copied either. |
| ACIO start flags (lstx_explicit, strict_fw_ready) | | | | Copied from t6030 because the ADT traits match (mxwrap + LSTX GPIO). **Not measured.** jsw's T8152 entry had to skip the M3_STAT wait. If T8132 does the same, `strict_fw_ready` will time out and needs a T8152-style `m3_stat_optional`. |

## What is still needed for USB4 on the mini (in order)

1. **Decode the T8132 CIO reset** (macOS `ApplePMGR` RIRQ path for CIOn_RECONFIG-V, or a trace). Candidate for a *hardware experiment only*: Gravity's guess, the t6000/t8122 layout at 0x380780000+0x8, `BIT(slot)`/`BIT(16+slot)`. The t8142 layout at +0x30, `BIT(2*port)`, uses the same page. Do not ship either without a trace.
2. **ATC PHY USB4/TBT mode for T8132** in `drivers/phy/apple/atc.c`: CIO lane tunables (`apple,tunable-lane{0,1}-cio` exist for other generations) and the crossbar protocol 0x0/0x1.
3. Then enable `usb4_N_mbox` + `usb4_N_acio` in the board, and check ACIO firmware boot, M3_STAT behaviour (see above), the NHI ring IRQ order and the DROM fill by m1n1.
4. PCIe-C tunnel: name reg[5..7] or the oe-fabric from a trace. Then either have m1n1 hand off (`apple,pciec-preinit-status = 1`) or qualify `apple,pciec-kernel-init`. Then enable `usb4_N_pcie_dart`/`usb4_N_pcie`.
5. DP-in over USB4: needs T8132 dcpext and the display crossbar first (HDMI track). After that, add T8132 to `apple_dpin_qualified_soc` with a policy.

## Not run

There was no hardware boot. `dt_binding_check`/`dtbs_check` were not run: there are no binding YAMLs for `apple,t8132-usb4-acio`, `-usb4-nhi` or `-pciec`. m1n1's behaviour with these aliases was not tested on J773g. `dt_set_acio_tunables` loops acio0..7 and should fill rc, nhi, pcie-adapter and the DROM. `dt_set_pcie_tunables` fills debug, fabric, rc and the port tunable on `usb4_N_pcie`.

## CI

Run 41208881043 on `mini/usb4` @ 56268a15f24c: **success.** All steps passed: Configure, the Image/modules/DTBs build and the J773g DT check. `pcie-apple.o`, `reset-apple-cio.o` and `thunderbolt/apple.o` compiled without warnings. The only warnings in the log are pre-existing Rust `fetch_update` deprecations. Artifacts were uploaded.
