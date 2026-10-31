# J773g USB binding draft

`0008-j773g-usb-bindings-draft.patch` adds the T8132 compatible strings used by
`0007-j773g-rear-usb-draft.patch` to the WIP5 SPMI, DART, DWC3 and ATC PHY
bindings. The ATC PHY string falls back to `apple,t8122-atcphy`, as in the
Gravity source; the other nodes use their existing Gravity fallback strings.
This is a draft description of device-tree compatibility, not confirmation
that the newer drivers' behavior or hardware initialization is correct.
The controllers in 0007 remain disabled.

The patch applies to the current WIP5 + 0001–0004 + 0007 source tree. It is
not included in the active kernel compilation, which started before this draft.
Standalone schema checks from a partial binding directory could not resolve
three referenced schemas and are not a validation pass. Full-tree schema and
hardware review remain open; no device or boot changes were made.
