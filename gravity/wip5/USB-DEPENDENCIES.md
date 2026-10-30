# J773g USB forward-port dependency review

This is source inventory, not a patch or a hardware qualification. Compared
`omacom/linux-aurora` WIP5 source `2f725546d6ac6afe0bd5abfa1a844971519f0076`
with Gravity's M4 source `4fc326f6c25ccceb7515e2635c22e01fde5d3bac` and
Gravity series patch 0003 (`840ac90252e2ef1962c318fbd567efcf29031661`).

- The WIP5 T8132 SoC, common board and J773g board files have no ATC PHY,
  DWC3, USB-DART or NUB SPMI controller nodes. Gravity 0003 touches all three
  files and other boards and depends on earlier platform work. Applying it
  wholesale to the newer kernel would change multiple boards and conflict.
- Gravity describes four PHY/controller groups and their DARTs; common board
  wiring supplies rear Type-C controllers 0 and 1. The mini adds a third rear
  Type-C controller at SPMI address 8 and configures controller/PHY 2 as a
  fixed host path for the front hub. These are distinct paths and cannot be
  inferred from a successful test of a single rear connector.
- The port needs the associated power domains, clock/interrupt resources,
  controller and PHY nodes, endpoint links, board-specific hub GPIOs and
  m1n1 tunable aliases. It also depends on the SMC GPIO draft for the common
  USB power-enable line. Preserve board gating and review existing newer driver
  behavior before copying a Gravity node.
- WIP5's SPMI and DART schemas include fallback families but do not enumerate
  `apple,t8132-spmi` or `apple,t8132-dart`. The exact WIP5 ATC PHY binding
  likewise needs review against Gravity's T8132 compatible and fixed-lane
  properties. Binding validation and a complete J773g DTB compile are required;
  passing a text apply check does not establish runtime controller ownership.
- The mini's existing Gravity kernel is unstable; do not test an incomplete
  WIP5 USB tree on it. The WIP5 SMC draft omits reboot cells, and the SMC GPIO
  dependency does not establish PMU layout or safe shutdown behavior.

Evidence: exact-ref source files and binding YAML fetched read-only from GitHub;
Gravity source from the checksum-verified archive. No boot, peripheral test,
full series replay, schema validation or hardware qualification is claimed.
