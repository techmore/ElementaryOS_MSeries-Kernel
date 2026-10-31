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
