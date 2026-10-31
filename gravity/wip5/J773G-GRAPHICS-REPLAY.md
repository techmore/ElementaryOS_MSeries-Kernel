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
