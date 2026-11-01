# Mac mini M4 (J773g, T8132) Omarchy packages: CI build

Date: 2026-10-31. All three platform packages build in CI from our sources. They are **unsigned** and have **not been tested on hardware**.

## Where

- Fork: https://github.com/techmore/omarchy-pkgs (fork of omacom/omarchy-pkgs, base `master` @ dd63dc38)
- Branch: `elementaryos-mseries`
- Local clone: /private/tmp/claude-501/pkgs/omarchy-pkgs
- No PRs, issues or comments on any upstream repo. No repository settings changed.

Commits on the branch:

| Commit | Change |
|---|---|
| 7c55e243 | Pin linux-aurora, m1n1-aurora and mesa-aurora; add `.github/workflows/elementaryos-mseries.yml` |
| 524d2ca8 | m1n1-aurora re-pinned to 9347c1818082, at the coordinator's request |
| 10cc9256 | m1n1-aurora: build-qualification.json sha256 updated |
| 34c27c6e | CI: a push builds only the package directories it changed, and runs never cancel each other |

## Pinned sources

All three are GitHub `archive/<sha>.tar.gz` tarballs pinned by sha256. Before, the git sources were checked with `SKIP`.

| Package | Source @ commit | Tarball sha256 | pkgver (channel's) |
|---|---|---|---|
| linux-aurora, linux-aurora-headers | techmore/linux-m1pro-touchid `elementaryos-mseries` @ fa26b0f92ef60a9d2ee5fae2d49a7dd12ee2473e | e0308ca1560b9c623d20fe598a89a195c9095e0926e7e87a0fe06b8c40741e82 | 7.3.0.aurora90-1 (7.2.11.aurora12-1) |
| m1n1-aurora | techmore/m1n1 `elementaryos-mseries` @ 9347c18180823812a75868b36698985ef3441a63 | dc672de54955d81029f0bb4cf6726321d38ea89a4062f4188649c1e22c2b27ae | 1.6.1.aurora90-1 (1.6.1.aurora22-1) |
| mesa-aurora, vulkan-aurora | aurora-silicon/mesa `aurora-wip` @ 8990cdb219b296b713b41350bcb1f6522ce062fb (includes 662048cacc83, which admits G16G) | 0c7c407947449a0d8b567db3eee14de27b5aee660a8fbb8e7edf48a61a3f96f5 | 1:26.3.0_devel.20261031.231461.8990cdb219b-1 (1:…20261029.231476.672657e05e6-2) |

Notes:
- **Kernel:** the build recipe is omarchy-pkgs' own and is unchanged: LLVM 18, Rust 1.85 plus the 1.99 rustfmt, the private bindgen 0.73.2 from `tools/aurora-bindgen`, the channel's `config` merged with the tree's `asahi.config`, and validate-config. The only change is the source.
  - Kernel release: `7.3.0-90-1-ARCH`, which passes `_check_kernelrelease`.
  - The package ships `dtbs/t8132-j773g.dtb`.
  - `CONFIG_DRM_ASAHI=m`, `APPLE_PMP=m`, `NVME_APPLE=m`, `PHY_APPLE_DPTX=m`, `ARM64_16K_PAGES=y`, `RUST=y`.
- **m1n1:**
  - `prepare` no longer checks `git rev-parse`; the sha256 now pins the tree.
  - `M1N1_VERSION_TAG=v$pkgver-<sha12>` gives the build a version tag.
  - `build-qualification.json` `source_commit` is set to the new pin, still with `hardware_tested: false`.
  - The package ships Stage 1 (`/usr/share/m1n1-aurora/stage1/m1n1-raw.bin`, `.macho`, plus the `aura` compatibility paths) and Stage 2 (`/usr/lib/asahi-boot/m1n1.bin`).
- **Mesa:** the reachable commit count comes from the GitHub commits API. The date component (20261031) sorts above the channel's version.
- The earlier audit draft's commits (cfd21dd, d896f4e, 68e7b67) were stale and are superseded by these pins.

## CI

Workflow: `.github/workflows/elementaryos-mseries.yml`.
- **Triggers:** a push to `elementaryos-mseries` that touches the three package directories or the workflow itself, or `workflow_dispatch` with a `packages` input.
- **How it builds:** the same way as omacom's `build-pr.yml`. `bin/build --mirror edge --arch aarch64 --package X` runs in the omarchy-pkg-builder container, natively on `ubuntu-24.04-arm` with `OMARCHY_BUILD_JOBS=4`. omacom builds kernels on a Namespace runner, which this fork does not have.
- **Output:** each package is uploaded as an artifact holding `packages.tar` (as in build-pr.yml; the upload action rejects the `:` in mesa's epoch filenames) and `SHA256SUMS`. Artifacts are kept for 30 days.

**Signing:** build-pr.yml never signs; only publish.yml signs, on merge to omacom master with omacom's key. This workflow therefore needs no secret and signs nothing. No keys were created or uploaded.

## Runs

| Run | Commit | Outcome |
|---|---|---|
| 41207116486 | 7c55e243 | cancelled (superseded by the m1n1 re-pin) |
| 41207184159 | 524d2ca8 | **linux-aurora success** (44 min), **mesa-aurora success** (12 min, meson tests Ok 130 / Fail 0), m1n1-aurora failed (stale build-qualification.json checksum, fixed in 10cc9256) |
| 41207382453 | 34c27c6e | cancelled by me (duplicate of the run below) |
| 41207395943 | 34c27c6e (dispatch, m1n1-aurora) | **m1n1-aurora success** (1.5 min) |

Artifacts, each containing packages.tar and SHA256SUMS:
- `linux-aurora-aarch64-524d2ca8e716dc28c48dd487c0f54a5f3cab672a` (run 41207184159)
  - linux-aurora-7.3.0.aurora90-1-aarch64.pkg.tar.zst, sha256 d24a142ebccbbfb059b054a9c71ceb14f893366dfb9b41aba58f720089e90e02
  - linux-aurora-headers-7.3.0.aurora90-1-aarch64.pkg.tar.zst, sha256 51481d66560fd597f0e52f778182f19c7a73c7d2e3bd50650ef1b44a1d8981b5
- `mesa-aurora-aarch64-524d2ca8e716dc28c48dd487c0f54a5f3cab672a` (run 41207184159)
  - mesa-aurora-1:26.3.0_devel.20261031.231461.8990cdb219b-1-aarch64.pkg.tar.zst, sha256 595c5695cf0aa4b2f2a929b09fafe71a5c2dd5b54a7dcc9aa9a248fa468bd842
  - vulkan-aurora-1:…-1-aarch64.pkg.tar.zst, sha256 e69f8f5f6247af2d3e42310ed10b7f386bbec8c5f6cdb91359344aacc4d4b7f4
- `m1n1-aurora-aarch64-34c27c6e36c9d201cbef4e311a7dbcf47431e9b4` (run 41207395943)
  - m1n1-aurora-1.6.1.aurora90-1-aarch64.pkg.tar.zst, sha256 fced8005a9afb3b5ebe97d1a915ca4e447f38f5b14ed2f877a9bdb0d70e28dc5

To download: `gh run download <run> -R techmore/omarchy-pkgs -n <artifact>`, then `tar -xf packages.tar`.

Cosmetic: when it strips the headers package, binutils `strip` prints "bad subsection length" for LLVM-built host tools (modpost, fixdep, dtc and others). These messages do not stop the build, and the package is produced.

## What remains

1. **Signed repository.** The packages are unsigned. The installer image needs one of two things:
   - a techmore pacman repo signed with a key the owner generates and holds offline or as a repo secret (not done here), whose public key the image trusts; or
   - a local file repo baked into the image, with `SigLevel` relaxed for that repo only.
2. **Candidate-trust policy in the image builder.** omacom's builder only trusts packages published to its channels. It needs an explicit "use these candidate packages" input: an artifact URL plus the SHA256SUMS above, with versions that beat the channel (they already do: aurora90 and the 20261031 date). It also needs a pin on our repo for linux-aurora, m1n1-aurora, mesa-aurora and vulkan-aurora so that a later omacom channel bump cannot overtake them.
3. **Hardware qualification.**
   - None of these packages has been booted.
   - m1n1's build-qualification.json is honestly `hardware_tested: false`, so `validate-qualification.py` without `--build-only` blocks promotion.
   - The kernel has not been cold-boot qualified on M1/M2. It shares pkgbase linux-aurora, so installing it on other Macs would replace their kernel.
4. **Repinning.** When the source branches move, update the commit and the tarball sha256, and keep `_aurorarel` / pkgver increasing. The workflow rebuilds only the changed package.
5. **Retention.** Artifacts expire after 30 days. Re-run with `gh workflow run elementaryos-mseries.yml -R techmore/omarchy-pkgs --ref elementaryos-mseries -f packages="linux-aurora m1n1-aurora mesa-aurora"`.
