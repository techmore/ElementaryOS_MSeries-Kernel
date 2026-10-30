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
