# J773g rear USB forward-port draft

`0006-j773g-rear-usb-draft.patch` is an initial J773g-only port adapted from
Gravity `0003` (Yureka Lilian, commit 840ac90252e2ef1962c318fbd567efcf29031661)
and the later select-IRQ correction in its `gravity-m4` pin. It follows WIP5's
five patches and local 0001–0004. It creates a board-specific include carrying
NUB SPMI, DWC3, DART and ATC PHY descriptions and connector graphs for the
three rear ports. The third rear connector uses the corrected select interrupt
65, not 64. All newly described controllers remain `status = "disabled"`;
this is wiring integration, not enabled USB functionality. The front hub and
its fixed-lane PHY handling are not included.

The exact source tree with WIP5 + 0001–0004 and this draft compiled the J773g
DTB in a local preliminary build. A full kernel build using this tree is running
in `/home/sdolbec/.cache/m4-kernel/wip5-source/j773g-kernel-build` with its
output in `build.log`. It uses `defconfig` plus `asahi.config`, not the WIP5
release recipe, and a distinct draft local version; it is a build-troubleshooting
artifact, not a package or boot candidate. The staged SPMI, DART, DWC3 and PHY
compatible strings still need binding updates and semantic review of the newer
Aurora driver, DART ranges, PHY tunables and m1n1 handoff before any node is
enabled. Do not install or boot it. No USB behavior is qualified.
