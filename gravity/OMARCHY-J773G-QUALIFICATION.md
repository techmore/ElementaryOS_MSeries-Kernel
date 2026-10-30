# Omarchy M4 Mac mini (J773g) qualification

Goal: a reproducible Omarchy-compatible kernel for the Apple M4 Mac mini,
with the necessary Gravity-derived work integrated and tested on that machine.
Source inventory, driver binding, or a successful build alone is not approval
for upstream. The owner decides when the tested result is ready to propose.

## Current status

- Target: `apple,j773g`, T8132, M4 Mac mini. The exact Omarchy package pin
  and known base conflicts are recorded in `OMARCHY-PORT-AUDIT.md`.
- No candidate Omarchy kernel has been built, installed, or booted. The live
  observations are from Gravity and are not evidence of Omarchy behavior.
- GPU timeout rescue, the SMC reboot path and the cause of the current
  cursor-only screen remain unverified. The owner reports instability on the
  current Gravity desktop; defer GPU workloads while investigating it.
- Synchronization of local commits to GitHub remains outstanding. Record the
  actual remote branch and commit when write access is available.

## Evidence required for a candidate

1. Record exact source commits, configuration, firmware prerequisites, each
   integrated or omitted patch with rationale, and a reproducible build
   procedure. Resolve overlapping implementations rather than blindly applying
   the Gravity series to Aurora.
2. Build an independently named package containing a matching kernel, modules
   and J773g DTB. Record toolchain, build logs, checksums and configuration;
   run relevant kernel and device-tree checks. Preserve a working boot entry and
   document a recovery path before an attended hardware trial.
3. On Omarchy and this Mac mini, record boot identity and exercise CPU, memory,
   internal storage, USB, networking and HDMI. Record results and failures, not
   merely whether devices enumerate. Check thermal and frequency behavior.
4. Qualify the desktop at its actual monitor resolution, including login,
   idle, compositor, display reconnect and normal application use. Separately
   test GPU rendering and compute correctness in bounded stages, retaining
   logs and stopping on errors. Verify timeout recovery only if its trigger can
   be reproduced safely; no rescue log means that behavior remains untested.
5. Verify reboot and shutdown in attended tests with recovery available; record
   the boot IDs and observed outcome. Missing PMU cells and their effect must be
   resolved or explicitly characterized without guessing register offsets.
6. Review logs and regressions, document remaining limitations and obtain the
   owner's approval before proposing an upstream change. Re-run affected checks
   after changes; retain exact versions and evidence for review.

These are acceptance targets, not claims that the current host or any candidate
already passes them.
