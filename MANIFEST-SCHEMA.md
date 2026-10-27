# kernel-manifest.json (schema 1)

Published with every Kernel release. The OS repo pins one copy as `mseries/kernel-pin.json` and verifies every checksum; it never builds against a branch.

Required fields: `schema`, `channel`, `kernel_repo_commit`, `kernel_release`, `source` (`url`, `commit`, `sha256`), `packages[]` (`name`, `version`, `arch`, `format`, `file`, `sha256`), `boot.m1n1_bootbin` (`file`, `sha256`), `qualification` (`devices`, `evidence`, `status` = candidate | qualified | frozen), `supersedes`.

Firmware blobs are never redistributed; the installer extracts them from macOS.
