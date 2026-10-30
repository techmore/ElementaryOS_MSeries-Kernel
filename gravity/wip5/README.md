# J773g forward port onto the existing WIP kernel

The owner's direction is to carry the Gravity M4 changes forward into the
existing WIP line. The project's current recorded WIP candidate is the hub's
`mseries/aurora/unified72/series.json` revision 7 (wip5), based on
`omacom/linux-aurora` commit `2f725546d6ac6afe0bd5abfa1a844971519f0076`,
with five additional patches. The upstream integration branch has since moved
to `2dd4aab661e42eccf3eef0f4dd765bcc72e5832a`; this draft is pinned to the
project's WIP candidate, not silently rebased to the newer upstream head.

## First draft: J773g SMC

`0001-j773g-smc-forward-port.patch` adapts the mailbox, SMC and GPIO nodes from
Gravity series patch 0002, originally by Yureka Lilian
(`be925f37d4ef327166b8a94f7303aa038c40b8e5`), to the J773g board file and
adds the T8132 mailbox and SMC compatible strings to the corresponding binding
lists. It deliberately does not add the reboot child from local patch 0067:
the reboot binding requires four PMU cells, and the mini's cells and offsets
have not been established. The node remains a draft until schema and hardware
review; it does not claim working reboot, shutdown, sensors or full M4 support.

The patch passes `git apply --check` against the three affected files fetched
at the exact WIP5 pin. None of the five WIP5 patches touches those files.
The board, its include closure, binding headers and Apple DT Makefile at the
WIP5 pin have the same Git blob IDs as the checked-out Omarchy package pin
`3bdf11d3`. Applying the patch to that checkout compiled the J773g DTB with
`make O=/tmp/omarchy-j773g-build ARCH=arm64 apple/t8132-j773g.dtb`; output
SHA-256 `c732cc4e058f1494b28272ccef1a7313adff009b078c283306168482740952ad`.
This is a DT compiler check of matching source inputs, not a complete WIP5
kernel build, DT schema validation, boot or hardware test. `dtschema` was not
available in the environment.

Next: integrate and replay against the full WIP5 source and its existing five
patches, then port the remaining J773g platform and graphics work in dependency
order. Compare Aurora's existing implementations instead of stacking Gravity's
65 patches blindly; keep Mesa, firmware, boot and speaker safety contracts
matched. The Gravity-based R8 proposal remains historical reference and must
not replace the WIP base.
