# Aurora M4 graphics integration draft

This work carries the [J713 graphics series #367](https://github.com/aurora-silicon/linux/pull/367)
forward onto this project's WIP5 base. The series is for the M4 Air, not proof
of Mac mini display or GPU support. The scratch tree is
`~/.cache/m4-kernel/wip5-source/graphics-integrated/source`; it is incomplete,
contains rejects, and must not be installed or booted.

The scratch starts from the Air basic-series integration draft, then applies
#367 patches 1–3, partially applies 4, and applies 5. The PMP report merge
retains WIP5's existing T8122/T6030 paths and limits the new T8132 path to
J713. Patch 4's platform-data and KUnit hunks still need the corresponding
#366 platform files. Patch 6 (display DART ownership) is partial: its
rejected hunks require the complete #366 radio and retained-domain code. The
other integration session is completing that prerequisite in a separate tree.

`graphics-0001-pr367-partial-shared-gpu.patch` records a partial three-way
merge of #367 patch 8 against WIP5: module registration retains both G15 and
G16 paths, the driver probe structure retains G15/M3/G17 alongside G16,
and six other shared GPU files merge automatically. The GEM draft retains
WIP5 memory accounting and the G15 cache-cleaning path while adding the Air
native-device preparation path; it requires compile and behavior review. This patch is
not the full series and cannot be built or used alone. The Air #366 head
`98a8f830df94a7dcaf7de37bfa915240afa2dda8` supplied the exact preimages;
their patch blob hashes were checked before merging. Remaining patch 8
conflicts include `mmu.rs` and `pgtable.rs`;
WIP5 already has `mmu/ppl.rs` identical to the Air patch, while its existing
`timestamp.rs` differs and needs review. Merging cannot be reduced to choosing
one side: retain WIP5's newer G15/G17 behavior and the Air G16 lifetime rules.

The partial patch passed `git apply --check` against the Air-forward scratch
snapshot. No GPU build or hardware test is claimed. After #366 is integrated,
replay the graphics series on the completed prerequisite, resolve each conflict,
compile the resulting drivers and only then prepare a hardware qualification.

`graphics-0002-g16-exploratory.patch` preserves the G16 source and an initial
WIP-first resolution of shared UAT/page-table conflicts, together with the
G16 Kconfig/Makefile integration. It is based on #367 patch 9 and the
preceding Air-forward snapshot; apply with `git apply --unidiff-zero` after
checking the exact base and applying the other prerequisites. It is an
experimental source record, not a deployable patch series: the ownership and
page-table conflict choices still need semantic review, and patch 6's display
DART merge is incomplete. The J713 firmware and board admission remain J713
specific; they do not qualify the J773g mini.

On 2026-10-30, an isolated WIP5-derived tree with these changes and the
partial #367 prerequisites built `drivers/gpu/drm/asahi/asahi.o` with
`CONFIG_DRM_ASAHI=m`, G15, G16 and UAT adoption enabled. This compiled Rust
and C and linked the driver object; it did not run final module modpost, build
an integrated kernel, verify DMA lifetime, or exercise hardware. The source
patch SHA-1 is `30d21d1a3565d08a648a0008098f7ad24a4d4127`.

`0010-m1n1-j773g-gpu-resource-draft.patch` adapts the pinned Air m1n1
`cda8314d2121c0279e4ca811bc6c6293a663e5d0` to publish validated mini GPU
resources only with an explicit empty opt-in property on a disabled node. It
keeps the device disabled and does not relax the firmware identity or PMP
board gates. The real m1n1 C object compiled, and its real-libfdt host harness
passed the existing Air cases and mini opt-in, missing/malformed opt-in and
already-enabled refusal cases. The patch passes `git apply --unidiff-zero
--check` against that pin; it requires mini DT placeholders and a U-Boot
GPU-resource importer before the handoff can be used. It has not been tested
on hardware and is not part of the built loader binary above.

The next handoff drafts are `0011-j773g-gpu-dt-draft.patch` and
`0012-uboot-j773g-gpu-import-draft.patch`. The first adds disabled mini GPU,
mailbox and six reservation placeholders; its DTB compiled in isolation. The
second imports an explicitly opted-in handoff after checking reservation
coverage, alignment, bounds, overlap and segment metadata; it leaves the GPU
disabled. Its U-Boot object compiled, host tests covered valid and invalid
imports and transactional rollback, and the existing 40 Air importer cases
passed. Both apply checks passed against their respective latest-source and
current loader drafts using `--unidiff-zero`. They do not qualify firmware,
mini PMP/TVM admission or a hardware boot.

The same combined G15/G16/G17 graphics object and the DART object compiled on
latest omacom integration `2dd4aab` after adapting the newer debug-statistics
field and reconciling three display DART hunks. This does not cover final
module linking, all display DART configurations, or GPU execution.

For the newer omacom base, `graphics-0003-latest-platform-prerequisites.patch`
records the partial #367 patches 1–6 on the exact `2dd4aab` mini/Air platform
snapshot. `graphics-0004-latest-debug-stats-fix.patch` restores the newer G17
initializer field after `graphics-0001`. These source records passed application
checks against those exact intermediate trees; use `--unidiff-zero` for 0003.
With `CONFIG_APPLE_DART_J713_DCP=y`, the reconciled retained-display DART
object also compiled. Both its ownership semantics and J773g applicability
still require review; this is not a completed native display handoff.

A combined storage + disabled-GPU handoff loader draft was linked locally:
`stage1-gpu-handoff.bin` (SHA-1 `c0317ef3b28da0c596f7d90712f26b7115099071`,
SHA-256 `f57d9a1de7f9899db0b8d8307d6896b375067c195769503d63af88ccb6a7b25d`)
and `stage2-gpu-handoff.bin` (SHA-1 `debeea719232cf7f72e49f7180fbccebaf768590`,
SHA-256 `85e403410ebd594fcce1fc3abdca7a4678b4c2e4df32540424a1b9f9c9398007`)
under `~/.cache/m4-kernel/wip5-source/m1n1/j773g-loader-draft/`, and
`u-boot-nodtb-gpu-import.bin` under the adjacent `uboot-j773g-draft/` (SHA-1
`f4bb4ca2fe619da7a33dcae44fdb5570146629d8`, SHA-256
`1b1e144483d6ad9c78b3902fb4a3725b48ec259965e112423b6f8117b166a45d`).
These are separate, unconfigured binaries, not an installed chain or a tested
GPU handoff. Stage1 uses `NO_DISPLAY=1 CHAINLOADING=1`; stage2 uses
`NO_DISPLAY=1`. USB calibration changes remain a separate draft.

On the `2dd4aab` mini/Air platform source (including its five WIP display
patches), the following draft sequence replays with `git apply --unidiff-zero`:
`graphics-0003`, `graphics-0001`, `graphics-0002`, `graphics-0004`,
`0011`, then `0013-j773g-latest-import-marker.patch`. A fresh replay matched
all 89 modified or added files byte-for-byte with the focused graphics source.
The last patch records the newer base in the NVMe import marker; the marker is
an opt-in, not cryptographic verification of the source or handoff. The
resulting J773g DTB compiled (SHA-1 `25f1d50cdd0e70b84d6511d9ac319dbb17d5bbc7`,
SHA-256 `abff43e472901a55798b0c3ad833574d13c6fc52ea07a7cf7499180ba440cbc9`)
and its GPU remains disabled. This sequence is experimental and still lacks
native display #367 patch 7 and mini power/firmware admission.

The m1n1 J713 documentation requires an ESP stage 2 built with `RELEASE=1`,
`CHAINLOADING=1` and `ESP_STAGE2=1`. A corrected `NO_DISPLAY=1` build is
staged as `stage2-esp-gpu-handoff.bin` (SHA-1
`0ad74a7876bc8f5c1491b9b06dcba322b5c2e0c9`, SHA-256
`d721e93e1a365bab3eedbe43028f378a8116dc8946c666488dbabb0e80522845`).
`stage2-esp-candidate.bin` appends the marked latest mini DTB and gzip-compressed
U-Boot in the documented order (SHA-1 `fd20e098e27d06b4ceac8478447f8fbe0e9a094a`,
SHA-256 `1dc71a2eee1b85f3495cc9cc3967c4053186ac76dc4e1f615f2d80b54c6165d1`).
The companion bare `stage1-release-gpu-handoff.bin` is unconfigured; it needs a
reviewed ESP identity and stage2 path. The bundle has not been installed or
booted, and it predates the separate USB calibration draft. Keep the previous
boot path available; do not assume the installed Gravity stage1 can load this
stage2.

Optional inspection-only patches `0014`–`0016` prepare a disabled J773g PMP
node and transfer its own ADT metadata through m1n1 and U-Boot without issuing
power commands. The loader objects and host fixtures compiled or passed, and
the optional DTB compiled; the normal candidate does not include this option.
`check-j773g-pmp-table.py` compares a captured raw table with the Air bridge's
identity guards while printing only size and hashes. No real mini PMP table was
available from the running system. A match would not establish mini TVM/power
sequencing or firmware compatibility and does not authorize enabling the GPU.

**Inline U-Boot handoff blocker:** source review after staging found that
`payload_run()` initializes an inline T8132 payload's NVMe session only for
J713, and sets `nvme_keep_running_for_linux` only for `boot=` payloads. The
packed `stage2-esp-candidate.bin` is an inline J773g U-Boot payload, so its
storage session initialization and retention are not established. Do not use
that packed bundle for a boot attempt. The separately staged direct rescue
uses `boot=`, whose `boot_storage_load()` initializes NVMe and whose successful
handoff sets the retention flag; that source path is also untested on hardware.

`0019-m1n1-j773g-inline-nvme.patch` addresses that source-level gap for an
explicit J773g/T8132, matching firmware target and ANS-alias opt-in: it
initializes the session, requires a live post-M4 controller before handoff,
retains it for the next stage and cleans up on failure. The payload object and
complete ESP stage 2 linked, and `verify-m1n1-inline-nvme.py` passed nine
mocked cases against the patched control-flow fragments. The revised raw stage
2 SHA-1 is `1a47b08343d866a871b14f812ba930dfc801cb3f`; a new packed
DTB/U-Boot candidate is SHA-1 `6f022a61c9d4ad599fe6bf5533f42f58addf5205`
and SHA-256 `d6dd789d1d2bb272d92010266027f565b58c8e7a8a9fca81406ae3302cacfafe`.
Both are staged locally. This corrects the identified source path but does not
prove live ANS initialization, U-Boot adoption, disk integrity or boot safety.
The older packed candidate retains the blocker and should not be used.
