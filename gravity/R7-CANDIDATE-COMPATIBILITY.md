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
