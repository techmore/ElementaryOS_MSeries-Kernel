# WIP5 and J773g SMC: full source replay

2026-10-30, local source and DT compiler check only; no kernel build or boot.

- Source: `omacom/linux-aurora` commit `2f725546d6ac6afe0bd5abfa1a844971519f0076`.
  The full codeload archive SHA-256 was
  `3f1b9cd779cc4ff94b8ff0575388223e1da0894160763133eb6b836352272bad`,
  matching `mseries/aurora/unified72/series.json` revision 7.
- Verified all five WIP5 patch hashes against that manifest. Each passed
  `git apply --check` and applied in manifest order to the extracted full tree.
  Then `0001-j773g-smc-forward-port.patch`, SHA-256
  `3e8b6afa3c9c9cbf25719bf3e0a7d3ee21361850e37ba15a436e62c11c2666fd`,
  passed `git apply --check` and applied on top.
- In a separate build output directory, ran `make ARCH=arm64 defconfig` and
  `make ARCH=arm64 -j1 apple/t8132-j773g.dtb`. The DTB built successfully with
  SHA-256 `c732cc4e058f1494b28272ccef1a7313adff009b078c283306168482740952ad`.
  That matches the prior check using identical input blobs.

The DT compiler check used defconfig, not the release package config, and did
not run `dtbs_check`/binding schemas, compile a kernel or test hardware. The
SMC draft does not include reboot/PMU cells. The output is an experimental
artifact in a private build directory and must not be installed as a qualified
boot payload. Further J773g storage, USB, display, GPU, firmware and power
work is still required before a boot candidate exists.
