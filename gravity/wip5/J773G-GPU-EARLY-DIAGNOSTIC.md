# J773g GPU DATA comparison before handoff admission

The existing diagnostic compares SGX's `gfx-data` reservation with gfx-asc's
DATA segment only after the register, interrupt and segment resource checks.
On this mini, an earlier difference prevents the comparison from running. The
existing U-Boot importer forwards that diagnostic only after a complete GPU
handoff. The earlier loader cannot diagnose a failed early check through U-Boot.

`m1n1-j773g-gpu-early-diagnostic-draft.patch` applies to the previously recorded
`gpu-diagnostic-loader-draft/m1n1` source, not the original upstream tree. It
moves the optional, opt-in comparison before Air-specific resource admission,
after both ADT nodes have been found. It reports `match`, `mismatch` or
`unavailable`, with the SGX size when both ranges are structurally valid. It
does not publish a physical address, alter GPU admission, enable the GPU or
touch GPU hardware. The diagnostic still requires the mini's disabled-node
opt-in; missing ADT nodes prevent the comparison. Output space errors can omit
the diagnostic.

The modified m1n1 built in a separate copy with the same recorded build flags.
The real-libfdt host harness passed prior admission cases plus mini register
and interrupt rejection with a retained comparison, and malformed segment names
with an `unavailable` comparison. This checks control flow on synthetic ADT
input, not real firmware or a loader boot. The binary is uninstalled at
`~/.cache/m4-kernel/latest-aurora/gpu-early-diag/m1n1/build/m1n1.bin`, SHA-256
`c55d8769cc73bce783dc5dec38ec083ae4cd0ad6f93b4180b4667a288ab2e194`.
It is raw and unconfigured. The U-Boot importer has not changed and still
discards diagnostics if the resource handoff fails, so this specifically helps
an appropriately configured direct m1n1 path; it is not yet an integrated boot
artifact. Storage, power, firmware identity and recovery remain unverified.
