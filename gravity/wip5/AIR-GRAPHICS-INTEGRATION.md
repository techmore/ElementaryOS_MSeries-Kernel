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
