# Gravity audio observation, 2026-10-30

On the running Gravity kernel, ALSA lists `T8132Speaker` (internal playback)
and `Apple DisplayPort` playback devices. The `sdolbec` PipeWire session did
not expose either local device; it initially exposed a dummy sink, followed by
network sinks after session services initialized. No sound was played.

At inspection time logind reported the physical seat active at the
`plasmalogin` Wayland greeter. The accessible `sdolbec` session was a separate
terminal session with no seat; the ALSA control device ACL granted the greeter
access and did not grant this user access. Thus lack of local PipeWire sinks
in this session is consistent with seat access and does not establish a driver
failure or functioning audio after a desktop login. No ACL or audio policy was
changed. Recheck local sinks and an audible playback after the user logs in;
this observation does not qualify audio on the unbooted Aurora candidate.
