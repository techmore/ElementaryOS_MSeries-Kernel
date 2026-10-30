# Gravity M4 host observation — 2026-10-30

Read-only inspection on the running Apple Mac mini J773g, compatible
`apple,j773g`, `apple,t8132`. Kernel `7.1.13-509.gravity.fc44.aarch64+16k`,
boot ID `e472ab2a-cff8-4cbd-baf1-c110fc8c1cbd`, uptime approximately 44 hours
at observation. Early journal wall-clock entries show October 17 before time
synchronization; use boot ID and uptime, not those timestamps, for identity.

- `macsmc_reboot` is loaded and bound to the platform device. The live device
  tree contains the `apple,smc-reboot` child. This boot's log reports handling
  reboot and poweroff through SMC, and reports missing `shutdown_flag`,
  `boot_stage`, `boot_error_count` and `panic_count` NVMEM cells.
- The prior boot also reported SMC handler registration. Its journal ends at
  `systemd-shutdown` after reaching `poweroff.target`; the journal stopped
  before the kernel poweroff call. This does not prove which handler executed,
  that power was removed, or that restart through SMC succeeded. The current
  boot proves a later boot occurred, not that it was an automatic reboot.
- `asahi_m4` is loaded and bound to the GPU. The installed on-disk module
  `/lib/modules/7.1.13-509.gravity.fc44.aarch64+16k/updates/asahi_m4.ko`
  has SHA-256 `28bfa14fde8a2e0056c930b7a834778acd2a53408f4e76dffd79e71cb57df951`,
  identical to the saved patched build in `~/m4-build/asahi_m4-fix/`; its
  binary contains the 0066 timeout-rescue log string. The boot log shows an
  unsigned out-of-tree module loading; an on-disk hash alone does not establish
  the exact bytes loaded at boot.
- Current-boot kernel journal inspection found no notification-rescue message,
  submission-pipeline failure, retirement watchdog timeout, double-unmap
  signature, or closed-GEM unbind failure. This is passive observation, not a
  controlled stress test or proof that timeout rescue was exercised.
- HDMI connector reports connected and advertises 3840x2160 modes. The agent's
  sandbox has no `/dev/dri` or desktop display environment: `glxinfo -B` cannot
  open a display and Vulkan cannot enumerate the DRM device. Those attempts do
  not test hardware rendering. No reboot, shutdown, kernel or boot changes were
  performed.

Commands: `uname -a`, `uptime`, `/proc/sys/kernel/random/boot_id`, live device
tree, `lsmod`, `modinfo asahi_m4`, `sha256sum`, `strings`, `journalctl -b` and
`journalctl -b -1`, and `/sys/class/drm`. Full logs are not copied here.

Still open: a deliberate hardware rendering workload with access to the GPU,
observation of timeout recovery under a reproduced condition, and attended
reboot/poweroff checks with recovery available. Investigate the mini's PMU
cells from independently verified J773g firmware data before using offsets from
another board. None of these observations qualifies an Omarchy kernel.

## Additional source and bus checks

Applying repository patch 0066 to copies of the two saved stock driver files
succeeds, and both resulting files (`g16_drm.rs` and `g16_runtime.rs`) match
`~/m4-build/asahi_m4-fix/` byte for byte. This connects the saved patch to the
saved build source; it does not independently prove the running module's bytes.
The repository's offline `bash validate.sh` passes.

The live system exposes two SPMI controllers. Three device-tree children on the
first controller are USB-PD devices; the second controller has no device-tree
children or enumerated SPMI child devices, and `/sys/class/nvmem` is empty. This
provides no PMIC address or safe register offsets; it does not prove the hardware
has no PMIC. No raw bus accesses were attempted.

## Vulkan enumeration follow-up

After network/device access became available, `vulkaninfo --summary` identified
Apple M4 (G16G B1) using Mesa Honeykrisp 26.3.0-devel. Immediately after that
19:35:54 EDT enumeration, this boot logged four `UATPageTable::unmap_pages`
"already unmapped" messages at IOVA `0x2ffff90000`. This is the same warning
signature previously observed before hangs; the temporal association does not
prove causation. The earlier statement that no such signature was present was
accurate only before this enumeration. No subsequent GPU workload was run.

The saved driver logs an error and clears the entry when an unmap finds a
non-leaf page. Several teardown and rollback paths can invoke this routine;
the log alone does not identify which one or establish a safe fix. Further
GPU tests should wait for a controlled investigation given the owner's report
of instability.

## Desktop symptom reported after enumeration

The owner reports stuttering, crashes, and a cursor with no desktop. The time
the blank screen began relative to the Vulkan enumeration is not established.
At 16:19:52 EDT, before that enumeration, `apple-drm` logged that it rejected a
plane operation that could crash DCP: a 235x2136 plane at 290x2160 on a
3840x2160 output did not satisfy its visible-area requirement. The kernel
message says the compositor should fall back to software compositing and that
failure to do so could freeze or crash it. This is a lead, not proof of the
current symptom's cause. The older `GPU-HANG-2026-10-28.md` also records a
separate cursor-only login caused by display modes arriving late.

After the report, passive checks showed all ten CPU cores online, approximately
12 GiB memory available and 56 GiB free on `/`; these do not prove CPU or
graphics stability. The sandbox could not inspect host desktop processes or
connect to the system bus. No desktop restart, reboot, or GPU workload was
performed.
