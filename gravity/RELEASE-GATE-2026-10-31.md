# Release gate (owner, 2026-10-31)

**From macOS on the M4 Mac mini: reclaim the disk, run our modified Omarchy installer, and get a clean
install that boots to a GPU-accelerated desktop over HDMI with AI up (Claude Code running on it).**
Booting and getting AI up is the gate. The six evidence steps in `OMARCHY-J773G-QUALIFICATION.md` remain the
supporting record.

## The path

1. **Kernel** — `techmore/linux-m1pro-touchid` `elementaryos-mseries`: Aurora `aurora-wip` plus the J773g
   commits (GPU done as step 1; display/HDMI, USB-C, Wi-Fi/BT, NVMe wiring, audio next). Built by the
   branch's CI.
2. **Boot loader** — `techmore/m1n1` `elementaryos-mseries`: Aurora m1n1 plus J773g (GPU handoff done; the
   storage handoff and anything else the m1n1 audit finds still to do).
3. **Installer** — our fork of `omacom/omarchy-mac-installer` (not yet created), which refuses M4 today
   (`scripts/supported-models.json` lists M4 as refused). It must admit `apple,j773g` and install our m1n1
   stage 2, kernel, modules and J773g DTB.
4. **Desktop** — Omarchy with Mesa that drives the M4 (G16) GPU; HDMI at the monitor's real resolution.
5. **AI up** — network, then Claude Code installed and running on the new system.

## Disk state on 2026-10-31 (before reclaiming)

| Partition | Size | What |
|---|---|---|
| disk0s2 | 148.0 GB | macOS container (Macintosh HD) |
| disk0s3 | 2.5 GB | Gravity Linux stub container (APFS) |
| disk0s4 | 524 MB | `EFI - GRAVI` |
| disk0s5 | 1.1 GB | Gravity `/boot` |
| disk0s6 | 93.0 GB | Gravity root |
| disk0s7 | 5.4 GB | Apple Recovery (keep) |

## Reclaiming (owner runs these; irreversible)

Only right before running the finished installer: this deletes Gravity, today's working Linux and rescue
path. Back up anything on Gravity first. Check identifiers with `diskutil list` on the day; they can change.

```bash
diskutil apfs deleteContainer disk0s3
diskutil eraseVolume free free disk0s4
diskutil eraseVolume free free disk0s5
diskutil eraseVolume free free disk0s6
diskutil apfs resizeContainer disk0s2 0
```

The free space then sits directly after the macOS container, so `resizeContainer … 0` gives it all back. If
Startup Disk still lists Gravity, its boot policy entry goes with the stub container.

## Gate checklist

- [ ] Installer runs from macOS on J773g and completes without manual steps
- [ ] First boot reaches the desktop with the GPU in use (not software rendering)
- [ ] HDMI output at the monitor's native resolution
- [ ] Wired keyboard and mouse; then Bluetooth
- [ ] Network (Ethernet or Wi-Fi)
- [ ] Claude Code installed and answering on the new system
- [ ] Reboot and shutdown work; macOS still boots from Startup Disk
