# Experimental direct-root initramfs

The existing direct Omarchy bundle passes no initramfs. Its matching kernel
builds Apple NVMe, EFI partition parsing, DART, SART, RTKit and Btrfs in,
but its Apple SPMI, ATC PHY and DWC3 glue are modules. Consequently, keyboard
probing on that route depends on module autoload after the root mounts; this
does not establish a working storage or USB handoff.

The rescue builder now offers a separate `--direct-root-bootstrap` experiment,
requiring its existing `--module-root` and `--release` options. This archive
loads the same experimental keyboard modules as the rescue archive, looks up
the existing boot command line's PARTUUID against sysfs, rejects duplicate
matches and invalid subvolume arguments, waits up to 60 seconds, mounts the
Btrfs subvolume and runs `switch_root`. Lookup, validation or mount failure
enters an initramfs shell, subject to actual console and keyboard availability.
It does not authenticate that shell. The archive uses local Gravity userspace
binaries, not a reproducible Omarchy initramfs.

The draft archive is local and uninstalled at
`~/.cache/m4-kernel/latest-aurora/j773g-direct-root-bootstrap-draft.cpio.gz`.
Its SHA-1 is `e72871e070cba56b6dd8a099d68d44d6a4c0eeba` and SHA-256 is
`3193e75261efbf3e60bd4fee0ca02ba55db44ba373f90f8cd561e2bd19b98c85`.
Gzip integrity, archive listing, bash syntax, argument parsing and simulated
sysfs selection and duplicate rejection were checked on the host. No actual
block discovery, device mount, module loading, `switch_root`, boot, graphical
output, keyboard or recovery path has been tested. The archive is not wired
into any installed boot bundle. The direct-root staging tool accepts it only
with explicit `--experimental-initramfs PATH`, checks this exact archive hash,
copies it into the uninstalled bundle, and records it in the manifest. The
default path still uses no initramfs. The optional path is available through
the Python staging tool; the local convenience wrapper does not enable it.

`switch_root` replaces PID 1: failure during that operation does not guarantee
a fallback shell and can end the boot. Even earlier shell availability depends
on unverified hardware. A separately established recovery route remains needed;
this draft does not make the machine safe to boot or solve GPU support.
