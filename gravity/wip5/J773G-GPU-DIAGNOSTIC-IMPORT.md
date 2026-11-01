# J773g U-Boot diagnostic-only import draft

The previous importer requires a completed GPU resource handoff before it
copies the optional DATA comparison. The separate draft
`uboot-j773g-gpu-diagnostic-only-draft.patch` adds an explicit diagnostic-only
route to the existing combined U-Boot importer. A destination GPU node must
have an empty `apple,j773g-gpu-diagnostic-draft` opt-in, must be disabled and
compatible, and must omit the GPU-handoff marker and admitted epoch metadata.
The source GPU must be disabled, compatible, and have the existing empty m1n1
handoff-draft opt-in. Thus source failure or lack of an admitted epoch can be
inspected without admitting it at the destination. An invalid or conflicting
opt-in fails the same enclosing atomic import. The existing value validator
copies only the comparison and optional size; it never copies an additional
address. GPU handoff rejection remains unchanged. Other existing import steps,
including general reservation copying, still run as before.

The patch applies to the preserved combined source at
`~/.cache/m4-kernel/latest-aurora/gpu-diagnostic-loader-draft/uboot`, whose
`arch/arm/mach-apple/j713_fdt.c` SHA-256 is
`d2d04c8563ca6af08f30b02c3e23a113a6da33a74d0d52c83103e5f854108b28`.
Patch SHA-256 is `f1986107de6bf799f899c9782009ce86842a77115267ef7aabd1fb5d6a0b8872`.
The edited source file SHA-256 is
`8924befdc21aee25b7abe8b479dbda5201df00afbffc76ce62b89f38903eda9a`.

An isolated full build succeeded using the same cached toolchain and the exact
prior U-Boot configuration, SHA-256
`8219e7422b5bdad88eff07bd3799b2d89d3117b626c2177c2d6c109812721788`.
The resulting raw `~/.cache/m4-kernel/latest-aurora/gpu-early-diag/uboot-build-new/u-boot.bin`
has SHA-256 `192255d6aeb196089f8e699ec90543ef15cf13474a0745ad4cc0aec6a9c2ecf9`.
Real-libfdt host fixtures pass for diagnostic-only import without a source
epoch, malformed and conflicting opt-ins, unchanged GPU handoff rejection,
and the full storage import transaction. Inputs are synthetic, not real ADT.

This is an uninstalled, unbooted draft: no destination DTB currently contains
the new opt-in and no combined loader has been assembled from these binaries.
It does not enable GPU, prove firmware compatibility, validate hardware,
establish boot or recovery, or guarantee an observable display.
