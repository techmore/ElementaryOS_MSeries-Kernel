# J773g GPU inspection loader bundle

The independent m1n1 and U-Boot diagnostic drafts are now assembled as an
uninstalled loader pair, with separate source and destination DTBs. The m1n1
source DTB has the empty GPU inspection/handoff opt-in on a disabled GPU; the
kernel destination DTB has only the new diagnostic-only import opt-in on a
disabled GPU. The GPU admission opt-in and firmware epoch are absent from the
destination. The paired raw stage 1 is unconfigured. U-Boot must be directed
to load the separate target DTB; no such boot command or root is configured.

`build-j773g-gpu-inspection-dtb.c` creates the two DTBs from the exact
graphics rescue DTB (SHA-256
`abff43e472901a55798b0c3ad833574d13c6fc52ea07a7cf7499180ba440cbc9`),
checking board identity, GPU compatibility, disabled state and absence of
admission markers. It refuses to overwrite an output. The output source and
target SHA-256 hashes are respectively
`56a8d2613d1cdecf319607ffd13cafaba46f65d5c0c7709dc56ef50d707898ef` and
`2ba45795b6da0156a3eaef2101f2f45bacc4f77e2992474c59df107b680d5c4d`.
The checked assembler `build-j773g-gpu-inspection-bundle.py` admits only the
recorded components and writes a new directory under home.

The stage 1 was built from the same isolated m1n1 source as the early GPU
diagnostic stage 2, with `NO_DISPLAY=1 RELEASE=1 CHAINLOADING=1`; stage 2 adds
`ESP_STAGE2=1`. See `J773G-GPU-EARLY-DIAGNOSTIC.md` and
`J773G-GPU-DIAGNOSTIC-IMPORT.md` for source, U-Boot build and limits. The raw
stage 1 SHA-256 is
`78f2977b1545a38dad54b4cf0f27875d422779805102ed2d4bfb33d346eb8db0`.
The packed stage 2 is m1n1, the source DTB, then gzip-compressed diagnostic
U-Boot; its SHA-256 is
`8d8198ae8175a15717b1719320d3be869dd2e14c6c222a10d481943509087229`.
The contents were split and checked against the component bytes; decompression
matched the U-Boot binary. DTB decoding confirmed the different opt-ins and
unchanged import marker. The graphics Image and manifest are alongside them at
`~/.cache/m4-kernel/latest-aurora/gpu-early-diag/inspection-packed/`.

The bundle has no configured stage 1, installed files, boot entry, boot
command, or staged Omarchy root. It has not been booted or run on hardware.
The copied source DTB still opts in to GPU resource publication when all
resource checks succeed; the GPU remains disabled and the separate destination
does not opt in to that publication. Source-side reservation publication and
U-Boot's normal reservation import are not eliminated by this diagnostic.
Storage, firmware identity, power, graphics, keyboard and recovery remain
unverified; the prepared files are not an authorization or readiness claim for
a boot attempt.
