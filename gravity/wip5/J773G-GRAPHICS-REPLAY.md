# Replaying the local J773g graphics kernel source

`replay-j773g-graphics-draft.py` reconstructs the source used for the
unbooted `7.2.11-elementary-m4-graphics-draft` build. It checks the exact
omacom `2dd4aab661e42eccf3eef0f4dd765bcc72e5832a` archive SHA-256, all
17 ordered patches across the kernel and hub repositories, and the recorded
build config. It then extracts and patches into a **new** directory; it does
not modify the live system, boot files, or either repository.

```sh
python3 gravity/wip5/replay-j773g-graphics-draft.py \
  --archive /path/to/omacom-2dd4aab.tar.gz \
  --hub /path/to/ElementaryOS_MSeries \
  --output /path/to/new/replay-directory
```

The source archive is available from
`https://codeload.github.com/omacom/linux-aurora/tar.gz/2dd4aab661e42eccf3eef0f4dd765bcc72e5832a`.
The hub input supplies the five WIP5 display patches from
`mseries/aurora/unified72/patches`. The script copies the exact generated
config into `recorded.config`; this is an input record, not a promise of
reproducible binaries across toolchains. The original build used Fedora clang
22.1.8 and the config records its compiler and Rust feature checks. Supply a
compatible build environment and review `olddefconfig` changes before using
the config in an out-of-tree kernel build.

For clean checkouts, the verified immutable kernel and hub commits are
`3ff11e05c076e57787f71dbe630625cc37fd3f36` in
`https://github.com/techmore/ElementaryOS_MSeries-Kernel.git` and
`7f24d3b4bf0ca8e3227928c3690eb865f768f91f` in
`https://github.com/techmore/ElementaryOS_MSeries.git`, respectively. A
contributor can clone both, check out those commits, download the archive above,
and run the command with those checkout paths. All 17 patches and the config
were independently fetched from GitHub using these commit IDs and matched
their recorded SHA-256 values; the pinned upstream archive URL returned HTTP
200. The local archive used for replay matched the recorded archive digest;
the remote archive was not downloaded a second time for this check.
The same replay was also run from clean `git archive` snapshots of those two
commits using the verified local upstream archive; a full `diff -qr` again
matched the cached source used for the original build. It did not consume
uncommitted files from either checkout.

On 2026-10-30 the script replayed the verified local archive and 17 patches;
`diff -qr` found no differences against the entire cached source used for the
completed graphics build. The copied config SHA-256 is
`709eb97d0118b096afc335ba8daef28a819177bb2c76e0926c59d69f18dbdb99`.
This validates source replay, not a fresh Image, modules or DTB build, and
does not establish bit-identical outputs.

The baseline replay retains the disabled mini GPU. The separate rear USB2
keyboard trial `0017-j773g-usb2-keyboard-trial.patch` applies to this replay;
it was not included in the source comparison above and requires its matching
experimental loader. The staged Ethernet module is an external build and is
not reconstructed by this script. Loader binaries and firmware inputs also
need their own reproducible, matched build. No source replay or successful
build demonstrates a boot, display, keyboard, storage ownership or recovery.
