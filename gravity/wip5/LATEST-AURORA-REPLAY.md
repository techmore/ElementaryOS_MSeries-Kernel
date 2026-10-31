# Latest omacom Aurora integration replay

On 2026-10-30, `refs/heads/integration/aurora` of `omacom/linux-aurora` resolved to `2dd4aab661e42eccf3eef0f4dd765bcc72e5832a`; the GitHub comparison reports it is 92 commits ahead of the WIP5 source pin `2f725546d6ac6afe0bd5abfa1a844971519f0076`. The source archive SHA-256 is `fdeb48ce693199f18c435b17567e80ec8dccd53bd826b531c1260ea2200ee16f`.

In a separate source tree, the following patches applied cleanly in this order:

1. The local mini SMC, NVMe flush, NVMe handoff ordering and disabled NVMe placeholder patches `0001`–`0004`.
2. `usb-0001-j773g-rear-draft.patch` and `air-forward-combined-snapshot-draft.patch`.
3. The five WIP5 display patches from the hub's `mseries/aurora/unified72/series.json`, applied in their recorded order. Checking the fourth alone initially failed because it depends on the third; the complete ordered sequence applied cleanly.

The resulting mini DTB compiled with clang preprocessing and WIP5's `dtc`, SHA-256 `6b8125fa86b4a6cb1d53cadfaccdafb45578b7b12d6a34e7a749761909c456b1`. It retains the known duplicate-unit-address warning on the disabled loader placeholders `/soc/mbox@0` and `/soc/spmi@0`.

The local source is `/home/sdolbec/.cache/m4-kernel/latest-aurora/mini-air-forward`. The old NVMe reject requested `cold_reset` and the broken-FUA quirk; both are already present in this tree, making that reject stale. The T8132 CLPC floor values are also present, but the newer GPU sampling and backoff behavior differs from the rejected Air hunk and needs semantic review. Clean patch application is not semantic review. No latest-source kernel Image, module, full binding check, loader pairing or hardware qualification is claimed. The earlier WIP5 builds remain separate and do not validate this newer source. This is not a bootable release.

A separate latest-source one-job build compiled the DART, ATC PHY, PMGR power-state, PMP report, Apple CPU-frequency, Apple PCIe and BCM4377 Bluetooth objects and the J773g DTB successfully. It used Fedora clang 22.1.8 and a diagnostic J713-oriented config with Rust and unrelated Nouveau disabled; its `.config` SHA-256 is `d2c595ed5d1e006ab99449501e3fc5968bcf72afc6356fbc04db7dc77e411b65`. This checks those objects against the newer source and includes the DART range guard. It does not compile Rust graphics, link the Image or establish mini hardware safety. The resulting DTB has the same SHA-256 shown above.

A source inspection after replay confirmed the newer upstream DART retirement warning, PCIe tunnel scan handling, PMP display sleep handling and Rust debugfs binding include remain present alongside the local changes. This is not a full semantic review of the 92 upstream commits.

The same diagnostic output also compiled `drivers/nvme/host/apple.o`, `drivers/soc/apple/clpc.o`, and `drivers/spi/spi-apple-qspi.o` successfully. These object builds do not validate the NVMe handoff or qualify the newer CLPC GPU-floor policy on the mini.

A separate latest-source build of `Image modules dtbs` was started with two low-priority jobs in `/home/sdolbec/.cache/m4-kernel/latest-aurora/latest-kernel-build`. Its diagnostic config is derived from the J713-focused draft with Rust enabled, Nouveau disabled, and local version `-elementary-latest-m4-draft`; the post-`olddefconfig` SHA-256 is `50f62120b686d5c53bf09e0c0b87093079680a27221e9071ec7faea0d72c92a3`. It does not include the in-progress G16 graphics integration, is not an Omarchy release configuration and must not be installed as a boot candidate merely because it builds. The running Gravity kernel and boot files are unchanged. The build log is `latest-kernel-build/build.log`; no result is claimed until the process exits.

`latest-j773g-import-marker.patch` adds `/chosen/u-boot,j773g-dtb-source` with the latest source identity to the latest replay. It adapts 0008 to the changed J773g DTS and uses `2dd4aab661e42eccf3eef0f4dd765bcc72e5832a`, not the older WIP5 identity. The marked DTB compiled in a separate source copy and its property was read back; SHA-256 `bd2944eb28934771aedc4d771f439b3a6352583b9b7774241c371fe1755dfb86`. The same disabled-placeholder duplicate-address warning remains.

The marker only requests the import. Activating the disabled NVMe placeholders requires the matched J773g m1n1 and U-Boot handoff bundle and its runtime checks to succeed; a valid marked DTB alone is not a storage handoff or a qualified boot image. The in-progress latest Image/modules build started before this marker and uses a separate source tree; its own DTB is unmarked. No loader or boot file was installed.

The marked mini DTB was subsequently rebuilt with kernel `make` in `latest-marker-dtb-build` using a copy of the in-progress latest Image build's config. Both resulting configs have SHA-256 `50f62120b686d5c53bf09e0c0b87093079680a27221e9071ec7faea0d72c92a3`; the DTB hash and source-identity marker match the preceding record. This establishes a config-matched DTB artifact, not a successful completed Image/modules build or a qualified loader pairing.

To prioritize the newer source, the older generic WIP5 `Image modules dtbs` build was intentionally terminated after approximately 41 minutes. Its output directory remains available for incremental resume; its make process exited 143 and did not complete. The separate focused WIP5 Image build already finished. The latest-source `Image modules dtbs` build continues at two low-priority jobs; it was not restarted.
