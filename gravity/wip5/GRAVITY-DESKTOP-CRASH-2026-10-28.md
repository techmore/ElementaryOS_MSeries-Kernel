# Gravity desktop crash observation

The local coredump journal records a `kwin_wayland` SIGSEGV on 2026-10-28
20:32:37 EDT, PID 4266, followed by a `plasmashell` SIGABRT. The KWin
backtrace includes `agx_encoder_allocate` in `libgallium-26.3.0-devel.so`.
Two later KWin SIGABRT records exist at 21:07:59 and 21:42:27. The latter
available stack only shows the crash handler and does not identify an
underlying fault. KWin core files were inaccessible to this user; the journal
still provides the recorded stack for the first crash.

This is evidence that at least one desktop crash involved the Mesa AGX
graphics path. It does not identify whether Mesa, the kernel GPU driver,
firmware, or a different interaction caused the fault, and does not establish
that the current Plasma greeter has the same problem. No GPU workload or
changes to the running desktop were made for this inspection.

The crash journal identifies Gravity Mesa build `102`; the currently installed
package is build `103`. The archived build-102 binary and matching debug
package have build ID `600230e15a50bf5241f015700cd59d40360c6981`.
`eu-addr2line` resolves the journal's library-relative address `0x1506800`
to `src/gallium/drivers/asahi/agx_batch.c:87`, the `agx_bo_create` call in
`agx_encoder_allocate`. The next instruction in the archived binary is at
that address, immediately after the allocation call. The short recorded stack
does not establish the allocator's return value or the original faulting
instruction, so a null allocation or any specific GPU failure remains a
hypothesis. The exact build-102 packages were retrieved from the Gravity COPR
archive for offline inspection; no package was installed.

The user journal adds a relevant sequence for the same KWin PID: at
20:32:36.390 it logged repeated `DRM_IOCTL_ASAHI_VM_BIND` I/O errors and
`BO creation failed`, less than a second before the crash. In the matching
build-102 source, `agx_bo_create` prints that buffer-creation message and
returns NULL on allocation failure, while `agx_encoder_allocate` calls it and
then passes its result to `agx_bo_map` without an explicit NULL check. This
supports an allocation-failure propagation hypothesis, but the unavailable
core and short recorded stack do not prove that this particular allocation
returned NULL or explain why VM_BIND failed. Other applications continued to
report VM_BIND I/O errors after the crash; kernel-side logs are needed to
investigate the initiating failure.

The matching debug-source package for the currently installed Gravity Mesa
build `103` retains the same unchecked `agx_bo_create`/`agx_bo_map` sequence.
Its encoder allocator is used in batch initialization and in several draw and
compute paths. A fix must propagate allocation failure through those users and
the context's reset/error handling; simply returning an empty encoder would
leave callers with invalid command-buffer state. This source inspection does
not prove that the current build reproduces the old crash. No patch was applied
to the live Mesa installation.

Further review of the original build-103 source found that `agx_batch_discard`
marks a never-submitted batch submitted and invokes normal cleanup. That cleanup
also finishes queries and may read timestamp/statistics data, so discarded work
can be treated as completed for bookkeeping. In the render-flush failure path,
a batch that also contains compute work can proceed to submission rather than
being discarded. These are source-level failure-handling risks, not proof that
either path caused the KWin crash. The extracted `agx_batch.c` was byte-matched
against a fresh extraction of the build-103 debugsource package. A safe fix must
handle context failure, unsubmitted queries and mixed-engine batches together.

An isolated proposal is saved as `mesa103-failed-render-draft.patch`, SHA-256
`f2124540640a594e61ab76b7226c86419480c52ecf9abf6384f8d4dad61a9700`.
It discards the full mixed batch on render preparation failure, marks a context
fault and avoids publishing timestamp results for discarded work. A host
harness exercised the modified dispatch and query-cancellation functions with
stubs, and the patch applies to the extracted Gravity build-103 source. Its
three changed C files compiled against the exact source, but it has not been
GPU-tested or validated for real buffer lifetimes and state-tracker behavior.
It does not fix the separate unchecked
encoder allocation/mapping path or establish the original VM_BIND cause. Do
not deploy or upstream it as a validated fix.

The follow-up `mesa103-failed-render-v2-draft.patch` (SHA-256
`705a1d749a7f8253bbfbf56313145b1918c23098237fc7d90abbd576ba9f9a52`)
separates driver-side batch failure from the existing guilty-context flag and
reports an unknown context reset instead. It applies to the extracted build-103
source. Its three changed C files also compiled in the isolated build; it
remains untested on hardware. Reset propagation, subsequent submissions and
query-buffer semantics remain open.

The third draft, `mesa103-failed-render-v3-draft.patch`, SHA-256
`262cbbeeee13d14d95bf03857c61542ee81271d4857c80419c2633579f0f4532`,
also discards later batches at flush after a preparation failure and rechecks
failure after mapping a query buffer. Its changed AGX C files compiled against
the exact Gravity 103 source. A failed query write can still leave an old
availability value, and encoding before the later flush, actual buffer cleanup,
reset handling and the original unchecked allocation remain unresolved. It is
an isolated draft, not an installed or hardware-validated fix.
