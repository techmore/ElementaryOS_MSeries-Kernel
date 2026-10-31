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
and six other shared GPU files merge automatically. This patch is
not the full series and cannot be built or used alone. The Air #366 head
`98a8f830df94a7dcaf7de37bfa915240afa2dda8` supplied the exact preimages;
their patch blob hashes were checked before merging. Remaining patch 8
conflicts include `file.rs`, `gem.rs`, `mmu.rs` and `pgtable.rs`;
WIP5 already has `mmu/ppl.rs` identical to the Air patch, while its existing
`timestamp.rs` differs and needs review. Merging cannot be reduced to choosing
one side: retain WIP5's newer G15/G17 behavior and the Air G16 lifetime rules.

The partial patch passed `git apply --check` against the Air-forward scratch
snapshot. No GPU build or hardware test is claimed. After #366 is integrated,
replay the graphics series on the completed prerequisite, resolve each conflict,
compile the resulting drivers and only then prepare a hardware qualification.
