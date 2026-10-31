# Latest Aurora J773g diagnostic build

The diagnostic build uses Aurora `2dd4aab661e42eccf3eef0f4dd765bcc72e5832a` with the local mini, USB, Air and display draft patches. `Image modules dtbs` completed successfully for `7.2.11-elementary-latest-m4-draft`. The separately compiled J773g DTB uses the same source and configuration plus `latest-j773g-import-marker.patch`.

| Artifact | SHA-256 |
| --- | --- |
| Image | `c74a5bfadddddb6ec03231bbe6f152021857218bc6592b796b8027f650693b1d` |
| config | `50f62120b686d5c53bf09e0c0b87093079680a27221e9071ec7faea0d72c92a3` |
| marked J773g DTB | `bd2944eb28934771aedc4d771f439b3a6352583b9b7774241c371fe1755dfb86` |

On the Gravity development machine, these are staged with 1,016 installed modules and depmod metadata under `/home/sdolbec/.cache/m4-kernel/latest-aurora/latest-module-stage/root/usr/lib/modules/7.2.11-elementary-latest-m4-draft`. The corresponding source, build output and artifact manifest are under `/home/sdolbec/.cache/m4-kernel/latest-aurora/`. These local cache paths are not portable release artifacts.

A separate experimental `atlantic.ko` was built externally against the completed build with `CONFIG_AQTION=m`; its vermagic matches the release and its PCI alias matches the live AQC113 Ethernet controller (1d6a:04c0). Its SHA-256 is `7dea5735e36be5726895bbe365f0c5a7bb1746e2d1b9fa37daf7ea944bfbf407`. It is not included in the staged module tree. The build configuration itself disables the Aquantia vendor option; `j773g-ethernet.config` records the options needed for a future integrated build.

This is a diagnostic artifact, not a qualified boot or Omarchy release. It lacks G16 and native Apple DRM; USB nodes are disabled; NVMe requires a matching loader import; and the mini PCIe/DART description and handoff are unresolved, so the Ethernet module alone does not establish network access. No artifact was installed on the Gravity system.
