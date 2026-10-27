# ElementaryOS_MSeries-Kernel

Kernel, firmware and boot work for the M-series port: Aurora and Fairydust kernel series, USB4 patches, m1n1/U-Boot boot assembly, Touch ID SEP driver installer, and hardware qualification evidence.

History was extracted from `techmore/ElementaryOS_MSeries` (`dev` @ 35f7f21, 2026-10-27) with `git filter-repo`; the 2018 upstream root commit is dropped and home paths are scrubbed. The hub repository stays authoritative until the cutover in its `mseries/KERNEL-SPLIT-PLAN` is complete.

| Path | Contents |
| --- | --- |
| `aurora/` | Aurora port qualification, frozen pins, unified72 series, trial staging, hardware evidence |
| `fairydust/` | PKGBUILD, Debian packaging, USB4 patches and tools |
| `aurora-sep/` | Touch ID SEP driver installer and PAM shim |
| `qualification/` | kernel smoke, dock timing, VRR and GPU probes |
| `tools/` | kernel config gate |
| `docs/` | kernel flow, report, source, reboot queue, firmware design |
| `power/` | vendored `display_status.py` (see `power/VENDORED.md`) |

Run the checks with `bash validate.sh`. The OS image consumes releases from this repository by immutable version and checksum; see `MANIFEST-SCHEMA.md`.
