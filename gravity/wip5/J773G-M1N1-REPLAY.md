# J773g m1n1 diagnostic source replay

`replay-j773g-m1n1-draft.py` reconstructs m1n1 snapshots from
Aurora m1n1 commit `cda8314d2121c0279e4ca811bc6c6293a663e5d0` and local
patches `0005`, `0006`, `0010`, `0014`, `0018`, in that order. It verifies
the archive and patch SHA-256s before creating a new source directory and uses
`git apply --unidiff-zero` for the recorded patch formatting. The source
archive is available from
`https://codeload.github.com/aurora-silicon/m1n1/tar.gz/cda8314d2121c0279e4ca811bc6c6293a663e5d0`;
its SHA-256 is `5e853caee70e56ba082f33c1d557fa30d25e92c2c571251b8ff04bbbc356e244`.

```sh
python3 gravity/wip5/replay-j773g-m1n1-draft.py \
  --archive /path/to/m1n1-cda8314d.tar.gz --output /path/to/new/source
```

The replayed tree was compared with the previously preserved local
`/tmp/j773g-mini-gpu-m1n1`: `diff -qr --no-dereference`, excluding generated
`build`, `target` and `__pycache__` directories, found no differences. The
archive has dangling artwork PNG symlinks but contains the prebuilt bootlogo
binary files used by this build. This matches the diagnostic scratch source;
it does **not** prove the original direct-bundle binaries were built from it.

On the Gravity development machine, both unconfigured loader stages built
from that replay using Fedora GCC 16.2.1, rustc 1.98.1, the
`aarch64-unknown-none-softfloat` Rust target, the lockfile's Cargo dependencies,
and these invocations from the replayed source:

```sh
M1N1_VERSION_TAG=vcda8314d2121c0279e4ca811bc6c6293a663e5d0 \
  make NO_DISPLAY=1 RELEASE=1 CHAINLOADING=1 -j4
# Save build/m1n1.bin before building stage 2.
M1N1_VERSION_TAG=vcda8314d2121c0279e4ca811bc6c6293a663e5d0 \
  make NO_DISPLAY=1 RELEASE=1 CHAINLOADING=1 ESP_STAGE2=1 -j4
```

The local build used a private matching Rust toolchain on `PATH` and Cargo
cache `/tmp/j773g-cargo` with offline mode. Cargo paths can be embedded in the
binary; a contributor needs the lockfile's pinned Git and registry dependencies
and a compatible toolchain. The version tag is set explicitly because the
upstream `version.sh` otherwise derives it from the directory name. Builds
completed with existing T8140 stack-usage warnings. The resulting uninstalled
stage 1 SHA-1 `d548ef20a1c92f44a7e03f368989f2033ed35c8f`, SHA-256
`097757ba955487da35208a8c2e640af484655ddbce0c3a8c530748af1b40ba3f`;
stage 2 SHA-1 `85587ed026d031e2241a99c3a71b4afb3279f3f4`, SHA-256
`240f2466dd47435a5eac8756b2fba062ab0deee3912cf8577d36f36f87f0aac8`.

**Neither diagnostic result matches the existing direct-bundle allowlisted
binaries.** The direct-bundle stage 2 lacks the PMP-inspection marker string
present in the diagnostic replay, so they are not interchangeable.

The replay script also offers `--profile direct-stage2` (0005, 0006, 0010,
0018) and `--profile direct-stage2-inline` (those patches followed by 0019).
The second profile's full source, excluding generated directories and comparing
symlinks themselves, matches a preserved original local build tree. That tree's
existing stage-2 binary SHA-256 is
`9ef4c475badbd2e52a59a2ad5f79c5569237b8b2021bf8f16f9178c392c02b37`,
the second allowlisted direct stage 2. In an isolated copy of that tree,
reversing 0019 and rebuilding the changed object with the same stage-2 options
reproduced the other allowlisted stage 2, SHA-256
`1b85c2945fd32b7c007506fb847f7fe8581da053f600fcd413a815f581b1cbdd`.
That reproduction reused retained build objects; it is not a clean binary
rebuild or proof of their original compilation history. A clean build of the
narrower profile did not match, even with the previously embedded Cargo cache
path and build tag. Patch 0019 changes J773g ANS initialization, live-session
checking, retention and failure cleanup; its effects on real direct and inline
boot remain untested.

The allowlisted unconfigured stage 1, SHA-256
`0597951acb4f9c6df2a3113e9e17f9814ab6e12b3cf754815224c4836a466b94`,
predates the 0018 and 0019 patches in the local build record and used
`NO_DISPLAY=1 RELEASE=1 CHAINLOADING=1`. A rebuild using 0005, 0006 and 0010
did not match it, including after reusing original build objects; its exact
build inputs remain unproven. Stage 1 needs a reviewed per-machine
configuration. None of these experiments installs, enrolls or boots a loader,
or demonstrates hardware operation or recovery.
