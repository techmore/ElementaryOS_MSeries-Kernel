# J773g ports as macOS sees them (2026-10-31)

Read-only enumeration on the owner's Mac mini M4 (Mac16,10, macOS 27.0 26A5421a) with `system_profiler`
(SPThunderboltDataType, SPUSBHostDataType, SPDisplaysDataType) and `ioreg -a -l`. Ground truth for the
J773g device tree and the Linux bring-up.

| Physical port | macOS controller (registry) | USB-PD addr | State during the run |
|---|---|---|---|
| HDMI | `AppleT8122DPTXPort` (`dptx-phy`) → `Port-HDMI@1` (PortType 6) | — | active: DisplayPort transport, 4 lanes, LinkRate 4, into the built-in DP-to-HDMI converter (`Transport = {Upstream=DP, Downstream=HDMI}`), Dell U2725QE at 3840x2160 @ 120 Hz |
| Rear USB-C 1 (Thunderbolt/USB4 receptacle 1, bus 0) | `AppleHPMDeviceHALType3@C` → `Port-USB-C@1` | 0xC | active: CC, USB2 (Logitech MX Vertical mouse on xHCI 0x00000000) |
| Rear USB-C 2 (receptacle 2, bus 1) | `AppleHPMDeviceHALType3@A` → `Port-USB-C@2` | 0xA | active: CC, USB2 (Magic Keyboard with Touch ID on xHCI 0x01000000) |
| Rear USB-C 4 (receptacle 4, bus 3) | `AppleHPMDeviceHALType3@8` → `Port-USB-C@4` | 0x8 | empty |
| Front USB-C 5, 6 | `AppleARMPE` → `Port-USB-C@5`, `@6` (no PD controller) | — | empty; USB2/USB3 only, behind Apple USB3 Gen2 hub 05ac:800c + USB2 hub 05ac:800b on xHCI 0x02000000 |

- Four xHCI controllers, all `AppleT8132USBXHCI` (location IDs 0x00, 0x01, 0x02, 0x03). Three
  Thunderbolt/USB4 rear ports at up to 40 Gb/s; no Thunderbolt device attached.
- The monitor runs over HDMI only. Nothing from the Dell enumerates on USB.

## What it confirms for the Linux port

- USB-PD controllers at SPMI 0xC, 0xA, 0x8 match Gravity's `hpm0`, `hpm1`, `hpm3` (`usb-pd@c`, `@a`, `@8`).
  Port 4 / `usb-pd@8` is the one Gravity's select-interrupt fix (4cb9998f58: second interrupt 65, not 64)
  applies to.
- The front ports have no PD controller and sit behind a host-only hub (Gravity: `dwc3_2`/`atcphy2`, GPIO hogs).
- The HDMI port is a DisplayPort output from a **T8122-type DP TX PHY** into a DP-to-HDMI converter. Aurora's
  `drivers/phy/apple/dptx.c` lacks T8122; Gravity's `d4f1cfe0f816` adds it and merges cleanly. HDMI also
  needs the converter's power GPIOs (Gravity: `hdmi-pwren`, `dp2hdmi-pwren`, SMC 15/26).

## Display blanking seen the same day

Two short blanks. At 09:27:16 macOS logged the display off, then on 3 s later with a full mode re-read and an
HDMI-CEC active-source change. A second blank left no macOS log at all, so the link or the monitor dropped.
Suspects: Dell auto input select or CEC switching, and 4K at 120 Hz over HDMI needing a 48 Gbps cable. Not
yet resolved.
