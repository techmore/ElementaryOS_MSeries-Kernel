# Generic Omarchy image desktop session, J773g draft

Selective, unprivileged extraction from the verified Omarchy 4.5.0-rc2 ARM
root image found Hyprland and UWSM session descriptors, Omarchy Hyprland
configuration under `/etc/skel`, the SDDM executable and unit, and SDDM's
Omarchy Wayland configuration. The extracted `/etc/systemd/system` has an
enabled tty1 getty but no `display-manager.service` link; the skeleton bash
profile does not start a compositor. The image's previously inspected default
target is graphical. A newly provisioned user alone therefore does not show
how the desktop manager is started. This extraction is an inspection, not a
metadata-correct root, boot or complete audit of generated systemd units.

A separate read-only extraction of the image's own
`/usr/lib/systemd/system/graphical.target` confirms it declares both
`Wants=display-manager.service` and ordering after that service. The optional
alias below therefore supplies the unit name requested by that target. This
checks the image's unit files only; it does not show that systemd reaches the
target or that SDDM, Hyprland, a display or input works on the mini.

`enable-omarchy-sddm-draft.sh` is an **optional, attended root** step on the
already prepared, isolated `omarchy-root-subvolume`. Its explicit opt-in
creates the SDDM alias only if the staged manager, configuration, and subvolume
checks pass, and refuses to replace any existing selection:

```sh
sudo bash gravity/wip5/enable-omarchy-sddm-draft.sh /absolute/path/to/omarchy-root-subvolume --enable-sddm
```

This helper is not part of the normal root-preparation command. The SDDM unit
conflicts with tty1 getty and its configuration starts a Wayland compositor,
so a failed graphics path could leave that console unavailable. The current
mini candidate deliberately disables its GPU; this helper neither enables it
nor establishes working display, input, login, recovery or boot. Keep an
independent recovery path. The real staged root and hardware have not been
tested. User-namespace fixtures with simulated subvolume checks verify the
opt-in link and refusal paths only; they do not run systemd or SDDM.
