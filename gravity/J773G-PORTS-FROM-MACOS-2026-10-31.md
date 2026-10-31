# J773g connectors and devices as macOS sees them (2026-10-31)

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


## Every connector on the mini

| Connector | Where | Hardware behind it (macOS registry) | Linux status in `elementaryos-mseries` |
|---|---|---|---|
| HDMI | rear | `dispext1`/`dcpext1` display pipe → `dptx-phy@9A740000` (`AppleT8122DPTXPort`, T8122-type) → DP-to-HDMI converter; HDMI-CEC and HDMI audio also on `dcpext1` | boot framebuffer only; needs DPTX T8122 driver port, dcpext DT, converter power GPIOs (SMC 15/26) |
| Thunderbolt 4 / USB-C 1 | rear | USB-PD `AppleHPMDeviceHALType3@C`, USB4 bus 0 (`apciec0`), xHCI 0x00 | DT draft dt-08/09/10 (USB2/USB3/PD, no new driver); USB4 needs driver work |
| Thunderbolt 4 / USB-C 2 | rear | USB-PD `@A`, USB4 bus 1 (`apciec1`), xHCI 0x01 | same |
| Thunderbolt 4 / USB-C 4 | rear | USB-PD `@8`, USB4 bus 3 (`apciec3`), xHCI 0x03; Gravity's select-interrupt fix applies here | same |
| USB-C 5, 6 (USB 3, 10 Gb/s) | front | no PD controller; Apple USB3 Gen2 hub 05ac:800c + USB2 hub 05ac:800b on xHCI 0x02 | DT draft dt-02/08; front hub needs ATC `fixed-usb3` support |
| Ethernet (10 GbE) | rear | Apple AQC113, Aquantia/Marvell AQtion `1d6a:04c0`, PCIe Gen4 x1 on `apcie` bridge 2 (`port02`), firmware 1.4.33; SMBus side `aqc-a@32` (aqc107). Linked at 1000baseT during the run | DT draft dt-01/07; Linux driver `atlantic` (in tree) |
| 3.5 mm headphone jack | front | Cirrus `cs42l84` codec on I2C @0x4B (`AppleCS42L84Audio`, `…Mikey`), MCA streams `audio-codec-output`/`-input` | DT draft dt-03/11; codec driver in tree; MCA T8132 variant needs porting |
| Internal speaker | — | TI `sn012776` amp on I2C @0x38, MCA stream `audio-speaker` | DT draft dt-03/11; needs Gravity's `apple,j773g-speaker` driver (opt-in, thermal limiter unvalidated) |
| Wi-Fi | — | Broadcom BCM4388 (`0x14E4,0x4388`), PCIe on `apcie` bridge 0 (`wlan@0`), 802.11ax incl. 6 GHz, firmware 23.10.1039.0.41.51.239; board type sakhalin | DT draft dt-01/07; `brcmfmac` 4388 in tree |
| Bluetooth | — | Broadcom BCM4388C2 over PCIe (`bluetooth-pcie@0,1`), firmware 24.1.240.1883 | DT draft dt-07; `hci_bcm4377` in tree |
| Power, power button | rear / underside | internal PSU; SMC `gp00` keys for the button (Gravity gap 7) | not started |

PCIe layout seen: `apcie@B0000000` (`apcie,t8132`) with `pci-bridge0` (Wi-Fi + Bluetooth) and `pci-bridge2` (Ethernet);
`apciec0`, `apciec1`, `apciec3` are the PCIe-over-USB4 controllers for the three rear ports (no `apciec2`).

## Display pipe: an open question

macOS 27 drives the Dell from **`dispext1`/`dcpext1`** (the IOMobileFramebuffer with the Dell attached sits under
`dispext1@88000000`; its DPTX port, CEC and audio endpoints are on `dcpext1`). Gravity drives HDMI from the main `dcp`
(`disp0`); the device-tree audit draft (dt-12) wires it to `dcpext0`, and Aurora's J773g framebuffer powers
`dispext0`. Linux boots with 26.6.2 firmware, which may assign pipes differently from macOS 27, so confirm under
Linux before choosing.

## The monitor's dock (target)

The Dell U2725QE is also a USB-C dock (USB hub and more over its USB-C upstream). Today it is connected by HDMI only,
so none of the dock enumerates. Target for the release: the Dell on USB-C with video (DisplayPort alt mode or
USB4 tunnel) plus its USB hub. On the mini under Linux that needs: USB-C/PD and USB3 on the rear ports (DT drafts),
then DP alt mode on T8132 ATC or the USB4 path (`t8132-usb4.dtsi` from Gravity, plus T8132 support in
`thunderbolt/apple.c`, `pcie-apple.c` tunnel and CIO reset). To enumerate the dock from macOS, plug the Dell's USB-C
cable into a rear port and rerun the same `system_profiler`/`ioreg` checks.

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
