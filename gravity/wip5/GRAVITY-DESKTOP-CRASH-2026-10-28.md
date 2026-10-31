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
