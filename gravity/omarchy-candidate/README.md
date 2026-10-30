# Gravity source candidate for J773g

This is a source-preparation step toward an Omarchy-compatible M4 kernel, not
an Omarchy package or a port of Gravity's changes into Aurora. It starts from
Gravity's `gravity-m4` commit `4fc326f6c25ccceb7515e2635c22e01fde5d3bac`,
which already contains patches 0001–0065, and applies the local 0066 and 0067
patches in a separate Git worktree. It verifies all patch hashes first.

```sh
bash gravity/omarchy-candidate/prepare-source.sh /path/to/gravity-linux.git /new/candidate-worktree
```

The source checkout must already contain the pinned commit. The output path must
not exist. If worktree creation or patching fails, inspect the output and remove
it with `git -C /path/to/gravity-linux.git worktree remove /new/candidate-worktree`
before retrying. This script does not build, package, install or alter a running
kernel, configuration, bootloader, firmware or initramfs.

On 2026-10-30, the two patches independently passed `git apply --check` against
isolated files from that exact Gravity pin. The saved stock GPU sources were
byte-identical to the pin. A full worktree preparation and build remain untested:
the source fetch was still in progress. The Gravity base has not been made
compatible with the Omarchy recipe or boot chain; the [qualification plan](../OMARCHY-J773G-QUALIFICATION.md)
remains open, as does integration with Aurora and all hardware acceptance.

## Build artifact preflight

`python3 gravity/omarchy-candidate/check-build.py --build BUILD_DIR --receipt RECEIPT`
checks a separately built candidate's source pin, `-ARCH` release, 16 KiB
configuration, artifact hashes, J773g device-tree compatibles and GPU,
display and Ethernet module vermagic. It needs `fdtget` and `modinfo`. The
receipt must include hashes for the Image, J773g DTB, `asahi_m4.ko`,
`appledrm.ko` and `atlantic.ko`, plus the exact R8 timeout patch hash. The R8
proposal now has an explicit `build-kernel.py --target omarchy` option with
release `7.1.13-omarchy-m4-r8-ARCH` and a display module hash in its receipt.
The default target remains elementary; its release does not end in `-ARCH`.
The Omarchy target still uses the candidate's existing config overlays, which
must be reviewed for the Arch environment. Neither target has been built from
the proposal. An Omarchy package, boot integration and matching Mesa remain to
be implemented and tested.
This preflight does not establish provenance, completeness of all modules,
package safety, a working boot chain or hardware qualification. Five synthetic
tests exercise matching and rejected inputs; no Omarchy candidate has passed it.

## Isolated staging

After a real build passes the preflight, `stage-build.py --source SOURCE
--build BUILD --receipt RECEIPT --output NEW_DIRECTORY` runs kernel
`modules_install` into the new directory and stages the matching Image, J773g
DTB, configuration and `linux-omarchy-m4` pkgbase. It checks the installed GPU,
display and Ethernet modules against the build receipt and leaves an
`INCOMPLETE` marker if staging fails. It does not produce or install an Arch
package, change the boot chain or establish provenance. The preflight and
staging have only been exercised with synthetic inputs and a mocked module
installer; they still need a real R8 build and Omarchy package review.
