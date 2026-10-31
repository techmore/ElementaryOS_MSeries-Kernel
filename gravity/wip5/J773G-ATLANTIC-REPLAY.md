# J773g Atlantic module build draft

The optional `atlantic.ko` staged with the graphics candidate was built from
the `drivers/net/ethernet/aquantia/atlantic` directory in the same pinned Aurora
`2dd4aab661e42eccf3eef0f4dd765bcc72e5832a` source used by the graphics build.
The copied module sources match that directory. Reconstruct the full kernel
source using `J773G-GRAPHICS-REPLAY.md` and use a completed matching kernel build,
including its generated headers and `Module.symvers`.

`build-j773g-atlantic-draft.py` verifies the recorded 56-file driver tree,
kernel config, Image, symbol table and release, copies the driver to a new
directory, and invokes the captured external-module build with
`CONFIG_AQTION=m`. It checks the resulting release, AQC113 PCI alias and
undefined symbols against `Module.symvers`. It does not install the module.

```sh
python3 gravity/wip5/build-j773g-atlantic-draft.py \
  --kernel-source /path/to/replayed/kernel/source \
  --kernel-build /path/to/completed/kernel/build \
  --output /path/to/new/module-build-directory
```

The original used `ARCH=arm64 CC=clang LD=ld HOSTCC=clang`, clang 22.1.8 and
a completed `7.2.11-elementary-m4-graphics-draft` kernel build. The script
requires that exact recorded kernel Image SHA-256
`d7503a309985d172374c3ef1045fdab7fb1e4b370118d0f48fbe021221107de7`,
config SHA-256 `709eb97d0118b096afc335ba8daef28a819177bb2c76e0926c59d69f18dbdb99`,
and Module.symvers SHA-256
`2b6690501e605775ce33adf35958c13b745ee8194da123f5a1f6060d679a77d5`.
It verifies the driver subtree, not every kernel header; use the verified
source replay without local changes. A new kernel build with different hashes
requires independent review rather than bypassing these identity checks.

An isolated script build completed and produced an AArch64 relocatable module
with matching vermagic and AQC113 alias; all 148 undefined symbols appeared in
the matching kernel's export table. Its SHA-256 was
`5b0d9aa1b9908469ce4cdbf6be00d05a81153fc875b1e7772b096b6a6b411c2f`,
which differs from the existing staged module's
`a150dcb959bb72b2aee1d67e90b3d0d8e41d6c078fbec2fad1ce9d6f806dfbfe`.
The root-staging helper checks the latter exact hash, so this rebuild is not
accepted as a replacement. A separate clean build with another output directory
also had a different hash.

For the scripted rebuild, `llvm-objcopy --strip-debug
--remove-section=.note.gnu.build-id` produced byte-identical files from the
staged and rebuilt modules, both SHA-256
`04c2f0bf884c9400ccf30f460a31518671900aa226619db8f479e2dafa970db9`.
The original and rebuild contain their respective different module-build
directory paths in debug strings, and have different GNU build IDs
(`acae9d9250fe60c37027995fd15fd53a20bc1656` and
`67d229f05634e864e26052f53c410cc6170e303e`). This comparison establishes
equality of the remaining stripped ELF, including its code and relocation
sections; the unstripped files and build IDs remain different. It does not
establish hardware operation or justify replacing the staging hash check.

Build and symbol checks do not test module loading. The mini PCIe controller,
DART ownership, handoff and Ethernet have not been qualified on the candidate;
the module alone does not establish networking or boot readiness.
