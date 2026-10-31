# Omarchy ARM root staging

On 2026-10-30 the official [Omarchy 4.5.0-rc2 ARM release](https://github.com/omacom/omarchy/releases/tag/v4.5.0-rc2) was staged under `~/.cache/m4-omarchy-root-staging/`, without mounting or changing partitions. The downloaded ISO matched the release SHA-256 `ee885285d6cba0dfc9a9ead22cf5bcc203b9f460970721b3c0b8a1dca4c867a8` and its embedded compressed root matched `dfe0ca883c2a3c62436306fcca42661e683c2bfe9f11334ad98ccc9650af9168`. The decompressed Btrfs image is 6,502,219,776 bytes; SHA-1 `2dbd79b41ff8fd815b2e9b12ba1f656cb92b8288`, SHA-256 `4b66dcfb84cc725e8bc11f27f3ecd452608e4753d13b3abfdab7124dbdb99b4e`.

A full read-only `btrfs check --check-data-csum` found no errors. An unprivileged `btrfs restore` preview of `/etc/os-release` failed because btrfs-progs 7.1 mishandles an inline zstd frame; independent decoding of the full frame succeeded and produced the expected file. The behavior matches [btrfs-progs issue #1171](https://github.com/kdave/btrfs-progs/issues/1171). The failed preview was discarded and the verified source image remains intact. The generic ARM release-candidate root is not yet a bootable J773g system: it needs matched kernel, modules, DTB, firmware, provisioning, storage and input support, and a reviewed boot chain. Check duplicate filesystem UUID handling before any attachment; do not use the raw image as an installed root without resolving that and preparing its mini-specific configuration.

A private corrected `btrfs restore` build now restores the actual
`/etc/os-release` successfully and rejects truncated, short and oversized zstd
frames in host checks. The [btrfs-progs issue #1171](https://github.com/kdave/btrfs-progs/issues/1171)
fix draft is saved locally as `btrfs-restore-inline-zstd.patch`, SHA-1
`2acc015a27837af9a1e82035341e03d3c3d01ace` and SHA-256
`2bd28cc6af3c77a2d13fc616ec14862674cea5a7d3b2cacdae917d1d160262ee`;
`RESTORE-PATCH-TESTS.md` beside the staged image records the commands.
Unprivileged restore cannot preserve root ownership, so this is not a complete
root installation. The image uses 4 KiB sectors and the candidate uses 16 KiB
pages. Source review indicates the inspected inline frame is decoded using a
4 KiB sector buffer, but actual mount and reads remain untested. Include the
matching Btrfs module and dependencies in an initramfs when it is modular.

Read-only extraction from Btrfs root ID 256 shows the staged `/etc/fstab` and `/etc/crypttab` have no active entries. Its `/etc/mkinitcpio.conf` uses `HOOKS=(base systemd autodetect microcode modconf kms keyboard sd-vconsole block filesystems fsck)` with an empty explicit `MODULES` array. These are generic image defaults, not a configured mini installation. A future boot target needs an explicit root identity and an initramfs built for the exact candidate kernel; blindly running `autodetect` against the currently booted Gravity kernel may omit modules needed by that candidate. The latest diagnostic config has Apple NVMe, DART, SART and Btrfs built in, but its USB DT nodes remain disabled and firmware or network availability is not established. No root image, boot files or host configuration were changed by this inspection.

The same candidate is preserved here as
`btrfs-restore-inline-zstd-draft.patch` (SHA-1
`46ab7d261ce4736e129fb3fb9b7dac2fbd4ed4d7`); context formatting differs from
the cached original. It reverse-checks against the patched btrfs-progs v7.1
source with `git apply --unidiff-zero`, and needs broader review before an
upstream proposal.

A read-only comparison confirms the staged image's Btrfs filesystem UUID is
different from the currently mounted Gravity root. Cloning the image would
still duplicate its own UUID; attachment and installation must account for
that separately.

The practical metadata-correct staging path is a privileged, read-only loop
mount of the verified image followed by `rsync -aHAX --numeric-ids` into a new,
separately named Btrfs subvolume. Before any copy, recheck free space and all
mounted filesystem UUIDs; the image has about 10.16 GB referenced uncompressed
and two nested subvolumes (`portables` and `machines`) that need explicit
handling. Verify owners, setuid bits, hardlinks, ACLs, capabilities and special
files after copying. This does not provision a user, firmware or boot entry.
The detailed attended plan is in the local staging cache; no mount or target
subvolume has been created.

`stage-omarchy-root.sh` prepares that copy as an attended root operation. It
checks the image hash, available space and mounted filesystem UUIDs, then mounts
the source read-only and copies it to a new `omarchy-root-subvolume` below the
specified staging directory. It prints a checksum and metadata dry run and
leaves a partial target for inspection on failure. Nested subvolume layout and
any differences reported by rsync still need review. The script has passed
shell syntax and non-root refusal checks only; it has not been run as root.
Once the staged root is reviewed, `stage-graphics-modules.sh` can copy the
separately built graphics-draft module tree into that isolated root and run
offline depmod. It checks the subvolume and module layout, the Asahi module's
recorded SHA-256 and kernel release, and refuses an existing destination.
Its root operation has not been run or tested; the Asahi hash is only an
identity check, not proof that the GPU works or that every module is intact.
The kernel image, firmware and boot configuration still need integration.
The optional graphics-matched Atlantic module stage is at
`~/.cache/m4-kernel/latest-aurora/graphics-ethernet-stage/root`; it uses a
`usr/lib/modules` layout. The module-staging script accepts that layout as
well as `lib/modules`, and checks the extra Atlantic module's recorded hash and
release when present. Its PCI ID matches the live mini's Ethernet controller,
but the experimental PCIe/DART and loader handoffs are not qualified or
enabled, so packaging it does not establish network operation.
Read-only selective extraction from the image confirms that `/lib` points to
`usr/lib` and `/usr/lib/modules` exists, as required by this script. The root
copy script records its rsync dry-run output and exits with an error when that
comparison reports differences; an empty report is not a hardware boot test.

For a later direct-root experiment, `stage-j773g-omarchy.py` builds an
uninstalled m1n1 bundle using the graphics kernel, a supplied DTB and a staged
root with matching modules. It supplies `root=PARTUUID=...`, Btrfs subvolume
root flags and no initramfs. The graphics config builds GPT partition parsing,
Apple NVMe, SART, DART and Btrfs into the kernel; the loader's boot grammar
accepts `-` for no initramfs. A synthetic-root fixture verified generated
arguments and artifact hashes. The tool compares the supplied PARTUUID and
top-level-relative path against `findmnt` and `lsblk`; a Btrfs fixture passed,
and mismatched partition and path cases were rejected. This verifies the mount
mapping, not that the path is a complete staged subvolume. Storage handoff, init, display,
input, firmware and recovery remain untested. No real root bundle was made.

Selective read-only extraction confirms `/sbin/init` resolves through
`/usr/bin/init` to the ARM64 systemd executable, its ELF interpreter is
present, and the packaged default target is graphical. The image's passwd
file has no regular account entries (UIDs 1000–59999), so even a successful
kernel and init boot would not by itself provide a provisioned desktop login.
These observations do not verify systemd's full library dependencies or a
working display, and do not change the image.
The image includes a `sysinit.target.wants/systemd-firstboot.service` link and
an empty `/etc/machine-id`. The service prompts for initial system settings and
a root password when `ConditionFirstBoot=yes`; the local systemd machine-id
manual says an empty existing file does not count as first boot. The image has
a different systemd version, so verify that behavior there before relying on
automatic prompts. In any case this service is not evidence of regular-user
provisioning. The staged copy needs an explicit, reviewed access setup.
Selective extraction also shows the image contains ARM64 `useradd` and
`passwd`, and has a `wheel` group. Its main sudoers file comments out the
general wheel rule; the extracted sudoers drop-ins grant only named commands.
Adding a user to `wheel` alone is therefore not evidence of general sudo
access. Account creation and an intentional admin policy remain to be applied
to the staged root, with passwords entered locally rather than recorded here.

A second, dependent draft `btrfs-restore-metadata-draft.patch` (SHA-1
`87fbba2a6875cf772ec1d304c1af0f8f91800aed`) reapplies file mode after writing
and reports extended-attribute failures. Isolated checks preserved an actual
setuid file and capability and rejected an injected xattr failure. This does
not resolve special-node or hardlink preservation, so the privileged copy route
remains the practical full-root path; both drafts need broader upstream review.

The direct-root staging tool now also rejects an ordinary directory as the
root: after confirming Btrfs, it requires the root-directory inode to be 256,
the Btrfs subvolume-root inode. It rejects commas in paths used to construct
boot arguments, preventing a subvolume name from adding a separate mount
option. Host tests verify both rejections occur before output creation. This
is not a contents, provisioning or hardware boot validation.

For the direct-root path, the matching graphics config also builds devtmpfs and its automatic mount support, Unix sockets, tmpfs, cgroups, futexes and file handles in. A selective read-only restore of the image's systemd executable, interpreter and its transitive ELF `NEEDED` libraries was checked with the image's AArch64 dynamic loader in `--list` mode and an explicit library path; all listed non-vDSO dependencies resolved to extracted image files. The restored copies are unprivileged inspection artifacts, not metadata-correct root files, and the loader's list mode does not run systemd or test optional runtime loads, mount behavior or boot.

The direct-root staging tool now accepts only the two recorded DTB hashes for
the exact graphics kernel: its baseline DTB and the separate rear-keyboard trial
DTB. Both observed DTBs contain the `ans` alias used by direct m1n1 ANS
admission; the `u-boot,j773g-dtb-source` marker is for the separate U-Boot
importer and is not the direct m1n1 admission condition. Hash matching prevents
accidentally pairing an unrelated DTB, but neither candidate nor its loader,
storage or keyboard handoff is boot-qualified. New DTBs require explicit
review and an updated allowlist.

The direct-root tool also verifies the recorded unconfigured release stage-1
hash and accepts only the two recorded raw `ESP_STAGE2` m1n1 builds with the
J773g ANS and USB2 gates; it rejects the packed inline-U-Boot candidates. It
checks the staged `asahi.ko` against the matching graphics build as well as the
Image and DTB hashes. The direct-root host fixture passed a recorded-artifact
case and rejected unrelated stage 1, stage 2, DTB and Asahi module inputs before
output creation. Its filesystem identity is simulated; it does not validate a
real mount, loader execution, hardware recovery, or boot.

The direct-root staging tool now refuses to assemble its bundle when the staged
root's `/etc/passwd` has no regular local login account (UID 1000–59999 with an
absolute home and a non-`nologin`/`false` shell). The supplied image lacks such
an account, so a separately reviewed provisioning step is required first. The
check reads only the public account database: it does not create a user, read a
password hash, establish that the account can authenticate, or verify a working
login session. A host fixture covers the unprovisioned rejection before output
creation; actual provisioning and hardware boot remain untested.
The local-user check additionally requires that the declared home directory and
shell resolve to existing paths inside the staged root. It still does not read
or validate credentials or establish a working login.

`provision-omarchy-user.sh` is an attended provisioning path for an already
staged `omarchy-root-subvolume`. It prompts for a new local username and invokes
`passwd` interactively inside the staged root; no password is placed in command
arguments or a log. It validates the existing sudoers configuration and adds a
general password-required wheel rule after password setup; existing command-specific
passwordless rules remain in effect. It refuses an existing user,
home or policy, and checks that `/dev/tty` can be opened inside the chroot
before creating an account. If needed it creates a temporary character device
with major 5, minor 0 and removes only that same node on exit. A failure after
`useradd` can leave a partial account for manual inspection. The script has not
been run against the real staged root or with a real password; user-namespace
fixtures covered refusal of an incorrect existing tty and failed tty creation.

For storage-only troubleshooting, `stage-j773g-omarchy.py` now accepts the
explicit `--allow-unprovisioned` option and labels a bundle without a local user
as an unprovisioned diagnostic. The default still requires the account check.
This does not establish interactive access, recovery, a working loader, or a
bootable desktop.

Additional disposable user/mount-namespace fixtures bind a pseudo-terminal only
inside the test namespace and mock the staged chroot commands. They verified the
provisioning command order, resulting `0440` wheel rule, and removal of the
temporary policy on a simulated password failure. These fixtures do not run the
real staged `useradd`, `passwd`, PAM, `visudo`, or a real password prompt.
