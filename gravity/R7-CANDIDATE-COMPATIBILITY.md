# Existing M4 mini candidate: GPU timeout fix compatibility

The existing elementary M4 mini candidate is
[PR 444](https://github.com/techmore/ElementaryOS_MSeries/pull/444), branch
`codex/m4-mini-readiness`, inspected at
`c6fd172c1abc1a31dbf9c70eef79c3bd7896cd8c`. Its compatibility README says R5
is the last completed package and the current source recipe targets R7; the R7
build and native qualification were pending at that revision. This Gravity-based
candidate is the existing project work to support, not the earlier isolated
Omarchy-pinned SMC experiment.

## 0066 source reconciliation

The candidate pins `GravityLinux/linux` at
`4fc326f6c25ccceb7515e2635c22e01fde5d3bac`. The two saved stock GPU files
have Git blob IDs matching that exact pin: `g16_drm.rs` is
`22a864dcbb1b57967d85b02998d9a6c88eeb0c18` and `g16_runtime.rs` is
`9d818e2a40e67183ad9f892ff4e3c1df65024f67`.

The ten R7 compatibility patches were fetched at the PR head and each
SHA-256 matched the R7 `package-versions.json`. Of those ten, only 0002,
0004 and 0005 touch either of these two GPU files. Applying their GPU-file
hunks in order produced `g16_drm.rs` SHA-256
`ea399e483c9b7372725b6888a68a58e77092101e6f8c85324a0e1cf28f353ecf`,
matching the R7 `resulting-files-by-version.json`. Then local patch 0066
passed `git apply --check` and applied without conflict. The resulting SHA-256
values are:

- `g16_drm.rs`: `b488b1520e3eae3b6e1161eec4e9dd64f4b233bd2a54c73044602a362c290554`
- `g16_runtime.rs`: `1f5c6760de0d72ea898eb66b3e2f7484b1d9c9ec838f99f7318b6894a2503f47`

This checks the relevant files, not a complete replay of R7, a build, or the
interaction of the fixes under real GPU workloads. Integrating 0066 into the
candidate needs a new immutable package revision, updated source-result hashes
and package gates, a full build, and deliberate hardware qualification. Retain
the historical R5/R6/R7 contracts. Do not change the live desktop or boot setup.

Direct Git fetch of the candidate branch failed due to DNS, and the connected
GitHub app returned 403 for branch creation. These results are local evidence;
they have not been synchronized to the candidate PR.

## Prepared R8 proposal

`R8-PR444-proposal.patch` is a draft against the exact PR head above, with paths
relative to the elementary repository. It adds 0066 as compatibility patch
0011, creates separate R8 patch and resulting-file records without changing
R3–R7, and updates the build and package checker version selection to R8. It
does not change the image profile's selected package or claim that R8 exists as
a built artifact. Apply only after checking the target branch head and resolving
any changes since that pin.

In a partial snapshot of the PR's relevant files, Python compilation passed,
the patch-manifest checksums and reconstructed GPU result hashes matched, and
the earlier version and result records remained identical. The generated patch
also reverse-applied cleanly to that modified snapshot. R8 uses the separate
package name `linux-image-elementary-m4-gravity1-r8` and kernel release
`7.1.13-elementary-m4-gravity1-r8`, avoiding the original proposal's collision
with prior module paths. The package checker retains the historical name and
release for R2–R7 and verifies R8's name, release and build receipt agree.
Four isolated identity tests passed: R7 and R8 identities reach package
extraction, while an R8 package using the old name or release is rejected.
These tests use mocked package extraction, not actual package inspection.
The embedded patch contains its original mail-format whitespace. These checks do not replace a
full checkout replay, full R8 build, package inspection, integration with the
selected image, or physical testing.

## Full patch-set source replay

At the same pinned candidate and Gravity revisions, the complete set of
source files touched by the four packaging patches and eleven proposed R8
compatibility patches was fetched into an isolated scratch tree. The two new
Apple idle files were absent from the Gravity base, as expected. All four
packaging patches and all eleven compatibility patches applied in manifest
order with `patch --batch --fuzz=0`. Every file in both resulting-file
manifests matched its SHA-256, including both 0066-modified GPU files. The
candidate's actual `source_patch_gate()` also passed its boot-CPU idle and
BCM4388 ordering checks. The four identity tests passed again.

This is a complete replay of the touched-file patch set, not a full kernel
source checkout or compile. The full Image, modules, DTBs and actual Debian
package still require building and inspection, followed by hardware testing.

## Image integration gap

The candidate PR's `package-policy.py` declares a dependency on the older
`linux-image-elementary-m4-gravity1` package. Its `build-research-image.py`
also enforces that exact package identity, and `prepare-hosted-image-inputs.py`
accepts only the older package filename prefix. The R8 proposal's distinct
package name therefore cannot yet be substituted into that image pipeline.
Do not add it to the image or mark it selected until those contracts and the
version-pinned profile are updated together, with a new policy package version
where needed and tests of both historical and explicitly selected R8 paths.
Existing R5 image selection remains unchanged.
