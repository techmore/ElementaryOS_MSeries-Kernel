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

The separate, explicitly incomplete `mesa103-allocation-incomplete-v4.patch`
(SHA-256 `c716c6f3756ed54edf0b2b1fe05509cc1f7c607f852d7e2d9f5733876464b86e`)
adds checks and failure propagation for initial encoder allocation and mapping,
and prevents mmap ioctl errors from continuing with an invalid offset. Seven
changed C files compiled against the exact Gravity 103 source. Secondary
encoder allocations, pool continuation, other mapping callers and nested
context-loss handling remain incomplete; no fault injection or hardware run
has validated it. This is a work-in-progress artifact and must not be deployed.

The follow-up `mesa103-allocation-incomplete-v5.patch` (SHA-256
`3be3c5821ef11427665edbcd3c1a64b3ab1b14db8ab2288d7e48dd6f9c87ed78`)
adds checked handling to the six secondary encoder allocations and associated
draw, compute and temporary-resource failure paths. Its changed AGX objects
compiled against the exact Gravity 103 source. Pool continuation, other
mapping callers, full cleanup and reset propagation remain unaudited; no
fault-injection or GPU execution validated it. It is not deployable.

The follow-up `mesa103-allocation-incomplete-v6.patch` (SHA-256
`6008bb204c8acb85651cc1600b9bdef2ff3ef3af2bc2afd2e8b518c81528d64e`)
adds a checked path for encoder continuation buffer creation, mapping and
pool tracking, preserving the previous encoder link on failure. Its changed
pool and AGX state files compiled against Gravity 103. Generic pool and mapping
callers, generated nested calls, full cleanup and runtime behavior remain
unverified; it is not deployable and was not run on the GPU.

The next isolated draft, `mesa103-allocation-incomplete-v7.patch` (SHA-256
`ec3f06b7140dde91b2a1447060d26a65e0d1e304209a92e0ff04a17415942613`),
propagates encoder continuation failure through more nested draw, tessellation,
copy and query paths. Its changed state, query and blit objects compiled against
the exact Gravity 103 source. Generic pool and mapping callers, generated-call
behavior, Apple9 preparation and cleanup remain unaudited; neither fault
injection nor GPU runtime validation has been performed. It is not deployable.

The isolated `mesa103-allocation-incomplete-v8.patch` (SHA-256
`0480c373084f2e498fa1105bdd1450d1bfe0f1c49adafa2768d231d12fbbba5c`)
adds checked allocation and context-loss propagation for Apple9 compute launch
preparation. The changed objects compile against Gravity 103. Apple9 draw
preparation, generic pools, mapping callers and cleanup remain incomplete;
invalid ABI state also takes the unknown-reset path. No injected-failure or
GPU runtime validation was performed, and the patch is not deployable.

The isolated `mesa103-allocation-incomplete-v9.patch` (SHA-256
`9d4de1b1011d072022d8f7642b254134046700d40834a1b7f17944a29bd59127`)
adds checked Apple9 draw-preparation allocations and propagates preparation
failure as unknown context loss. The changed objects compile against Gravity
103. Earlier descriptor, texture and sampler allocations, generic pools,
mapping and cleanup remain incomplete. It has not been fault-injected or
tested on a GPU and must not be deployed.

`mesa103-allocation-incomplete-v10.patch` (SHA-256
`65f6000eb02cd2a2e99d33fb2ab7f7274aa9c7ec161e41e68916846deefa3eb6`)
adds checked Apple9 graphics sysval, resource-descriptor, texture and sampler
table allocation, propagating failure in draw and compute callers. The changed
AGX state object compiles against Gravity 103. Other descriptor, uniform, pool
and mapping paths and cleanup remain incomplete; no fault-injection or GPU
runtime validation has been performed. It must not be deployed.

`mesa103-allocation-incomplete-v11.patch` (SHA-256
`73e93e59d3c8cfed65c48cc6bf42812db494b3873fe5158da35436bcef667450`)
extends checked allocation to generic texture/sampler descriptors, uniform
buffers, the SSBO sink and bindless sampler heap. The changed state and uniform
objects compiled against Gravity 103. Pipeline builders, other uploads and
mapping paths, cleanup and query/fence behavior remain incomplete; no fault
injection or GPU runtime validation has been performed. It is not deployable.

`mesa103-allocation-incomplete-v12.patch` (SHA-256
`c21dee0446aa89e6ab89308acf31181f870aeddab5a6aeca7420e14aa55372a1`)
adds checked paths for pipeline USC, varying linkage, precompiled-kernel
arguments and USC uploads, indirect groups and draw parameters. The affected
state object compiles against Gravity 103. Other command uploads, scratch and
mapping allocations, and cleanup/query/fence behavior remain incomplete; it
has not been fault-injected or GPU-tested and is not deployable.

`mesa103-allocation-incomplete-v13.patch` (SHA-256
`93d8fcc5fb0990afb41edcab24cd7882261b36633a66e594005d036ebf4cb9e3`)
adds transactional scratch replacement and checked render-state, scissor,
depth, viewport and related upload paths before submission. The changed
scratch, state and pipe objects compile against Gravity 103. Geometry,
tessellation, user-index and shader-cache allocations, generic pool tracking,
global mapping, query/fence cleanup and the Vulkan scratch wrapper remain
incomplete; no fault-injection or GPU execution validated this draft. It must
not be deployed.

`mesa103-allocation-incomplete-v14.patch` (SHA-256
`e829085317ebfa36971ee18c7954a500763546f86abf46e882080a40a74fdfe5`)
extends checked allocation handling to user-index uploads, heap resources,
restart descriptors, and the direct state-file pool allocation paths including
geometry and tessellation. The changed state object compiles against Gravity
103. Shared pools, shader caches, other mapping paths, arithmetic overflow,
Vulkan scratch propagation and query/fence cleanup remain incomplete. It has
not been fault-injected or GPU-tested and must not be deployed.

`mesa103-allocation-incomplete-v15.patch` (SHA-256
`4e843d654e10c812d006388b5da21238769a649dcd3133037a191e294e4ba313`)
extends the draft to shader-cache allocation and mapping, helper-program
failure, pool preallocation tracking and checked-path arithmetic. The affected
cache, pool, pipe and state objects compile against Gravity 103. Vulkan still
uses aborting wrappers; generic pools, other allocation/mapping callers and
query/fence cleanup remain incomplete. There is no fault-injection or GPU
runtime validation, so this draft must not be deployed.

The Vulkan-focused `mesa103-allocation-incomplete-v16.patch` (SHA-256
`84eda2af64befdc7055c73268f0f6f2b616be2e18de34231412509cc132ed854`)
adds checked scratch and shader-cache access for command recording and queue
submission. The three changed Vulkan objects compiled against exact Gravity
103 source in an isolated build. Cache failures are currently classified as
out-of-memory even for some other errors; cache concurrency, in-flight scratch
lifetime, generic allocation paths and query/fence cleanup remain unvalidated.
This is not a linked build, an injected-failure or GPU runtime test, and the
draft must not be deployed.
