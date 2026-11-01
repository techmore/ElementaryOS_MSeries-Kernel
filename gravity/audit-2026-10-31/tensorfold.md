# TensorFold Vulkan on the Mac mini M4 GPU (J773g, T8132, G16G) — audit

Date: 2026-10-31. Sources read at:

- ashhart/TensorFold PR 1544 head `b3ab9ba217a80c63fcc48f7643ddfe339a8f4bdc` ("Native Vulkan backend for Qwen3.5-2B (opt-in)"). The PR is open. It branches from main at `86e29f69`, which is after v1.1.9 (`465e48b6`) and before v1.2.0. `build.zig.zon` says version 1.1.9.
- aurora-silicon/mesa `aurora-wip` `8990cdb219b2`, the commit vulkan-aurora pins.
- techmore/ElementaryOS_MSeries `mseries/local-ai/` (the owner's M1 Pro build, package and receipts).
- `mlx.md` (this directory) for the G16G feature list.

Nothing here ran on M4 hardware or on any GPU. Every "works" below comes from reading the source or from CI, not from a measurement.

## Summary

- **Feature check: G16G has everything the TensorFold Vulkan engine needs.** It needs no cooperative matrix, no fp32 atomics, no bf16 type, no subgroup-size control and no int8 or 64-bit features. The tight spots are:
  - shared memory: 30,720 of the 32,768 bytes available;
  - subgroup size: the shaders assume exactly 32, which Honeykrisp guarantees;
  - FMA: G16G's FMA is not exact, which matters only to bit-level comparisons.
- **No driver-ID problem.** TensorFold checks no vendor or driver ID. Unlike MLX, it needs no drirc entry for Borealis (35). Only the optional `--vendor` guard on the probes pins a vendor, and that is Mesa's `0x10005`, the same as on M1.
- **Package.** New Arch package `tensorfold-vulkan` on techmore/omarchy-pkgs `elementaryos-mseries-mlx`. It is pinned to b3ab9ba, uses the Zig 0.17.0 archive pinned by sha256, and is built with ReleaseSafe and `-Dvulkan=true`. It depends on `vulkan-aurora`. Its wrappers set `VK_DRIVER_FILES` for TensorFold's own processes only. CI is green on GitHub's arm64 runner (run 41214452366). The M4 mini VM that PKG_RUNNER selects cannot build any package yet, because its docker has no buildx.
- **Benchmark.** techmore/omarchy-mlx `m4-mini-bench` gains:
  - a TensorFold engine leg (Vulkan on Linux, Metal v1.1.9 on macOS);
  - the Qwen3.5-2B work, which both engines can run;
  - an N-way `--compare`.

  13 harness tests pass with no GPU.

## 1. Feature audit: what the Qwen3.5-2B Vulkan path needs, and what G16G gives

What the engine requires, from the PR head:

**Device selection** (`zig/src/vulkan/device.zig`, `families/qwen3_5/backend/vulkan/engine.zig:105`):

- Vulkan ≥ 1.3, a device that is not a CPU, and a compute queue.
- It enables only `storageBuffer16BitAccess` and `shaderInt16`.
- It checks no vendor ID, driver ID or device name.

**Run-time guards in the operators:**

- `attention.zig:62-63`: needs `maxComputeSharedMemorySize ≥ 30,720`. The bf16 SDPA arm holds 7,168 stream floats, a 256-float q row and a 256-float tree.
- `gdn.zig:120-124`:
  - subgroup operations in the compute stage;
  - `VK_SUBGROUP_FEATURE_SHUFFLE_RELATIVE_BIT`;
  - a subgroup size divisible by 4.
- `norm_mlp.zig:62`: uses the `PRESERVE_F32` (DenormPreserve) add only if `shaderDenormPreserveFloat32` is set. Otherwise it uses the plain add.

**Shaders:**

- 22 `.comp` files in `zig/kernels/vulkan`, compiled with `glslang --target-env vulkan1.2` (SPIR-V 1.5). The server embeds the 24 stage 1–5 variants.
- Extensions:

  | Extension | Count |
  |---|---|
  | 16-bit storage | 35 |
  | int16 arithmetic | 21 |
  | fp16 arithmetic | 13 (declared; the server's variants are all bf16 through `uint16_t`) |
  | int64 | 1 (`copy_general` U64, not in the server) |
  | subgroup basic | 4 |
  | subgroup arithmetic | 3 |
  | subgroup shuffle | 1 |
  | subgroup shuffle_relative | 1 |
  | `spirv_intrinsics` | 1 (the DenormPreserve variant) |

- Workgroups are up to 1,024 invocations (`sdpa_decode_native`).
- `SIMD = 32` is hard-coded in `sdpa_decode_native` and `fast_norm_gated`.
- Atomics are integer only: `atomicAnd`/`Or`/`Min`, plus a CAS loop in the contract controls.
- `fma()` appears in `sdpa_decode_native` (×5) and `gated_delta_prefill_ash` (×1).

| Requirement | G16G on aurora-wip 8990cdb219b2 (`src/asahi/vulkan/hk_physical_device.c`) |
|---|---|
| Vulkan 1.3 | 1.4 |
| `storageBuffer16BitAccess`, `shaderInt16` | yes (406, 385) |
| shared memory ≥ 30,720 B | 32,768 (`HK_MAX_SHARED_SIZE`, `hk_private.h:52`); same as M1, 2 KiB headroom |
| 1,024 invocations | 1,024 (1249) |
| subgroup ops in compute, shuffle_relative | yes (1322-1327) |
| subgroup size 32 (hard-coded SIMD) | `subgroupSize` 32, min = max = 32 (1321, 1414-1415) |
| cooperative matrix | **not used.** G16G lacks it (M5-only); no impact |
| fp32 atomic add (`EXT_shader_atomic_float`) | **not used.** G16G lacks it; no impact |
| bf16 storage / `EXT_bfloat16` | **not used.** bf16 is handled as `uint16_t` bit patterns |
| `subgroupSizeControl` | not enabled by the engine (G16G has it) |
| DenormPreserve fp32 | G16G reports `shaderDenormPreserveFloat32 = false` (1363), so the engine picks the plain add; same as M1 |
| vendor / driver ID | vendor 0x10005 (Mesa, 1082), driver Borealis (1349-1351). TensorFold checks neither |

Verdict: functionally sufficient. The risks, in order:

1. **Unproven compute path.** This is the same as for MLX (`mlx.md` §1): G16 kernel compute submission, Borealis compute and the 25G83 firmware are all unproven on the M4. A GPU fault can stop the GPU until reboot. Run `tensorfold-vulkan-gates` first; it holds `/tmp/m1-gpu.lock` and has a 60 s fence timeout per probe.
2. **FMA on G16G.** `agx_chip_exact_fma32(G16G)` is false, because probes fail near the minimum normal. GLSL `fma()` carries no exactness requirement, and fp32 denormals are flushed on every Honeykrisp chip anyway. Expect at most last-bit differences from M1 in SDPA and the GDN prefill. Upstream's contract gates use tolerance bounds. The contract `pointwise` group's KNOWN denormal finding is expected on G16G too.
3. **Hard-coded subgroup size 32.** This is correct on every Honeykrisp chip today, but nothing guards it (there is no check in `attention.zig`). If a future Mesa varied the subgroup size, `sdpa`/`fast_norm_gated` would silently compute wrong results.
4. **Shared-memory headroom is 2 KiB.** The engine refuses the device if the limit ever drops below 30,720 bytes.
5. **Spec gap, harmless on Mesa.** The fp16 arithmetic extension is declared but `shaderFloat16` is never enabled. The server's bf16 variants should not emit the Float16 capability; not verified with `spirv-dis`.
6. **Speed.** The engine submits one dispatch per op and waits on a fence each time (`dispatch.zig` `Pipeline.run`). It measured 2.8 tok/s on the M1 Pro, against MLX's 56. Upstream's batching follow-up is still not public. Expect the M4 to be limited by submit round trips, not by the GPU.
7. **Fidelity.** Upstream's own fidelity packet fails on long documents (bf16 near-ties). The owner's M1 Pro receipts show divergence after 880 characters at a 0.089-logit near tie. Use it as an experimental engine only.

## 2. Package: techmore/omarchy-pkgs `elementaryos-mseries-mlx`

The branch was pulled first. Its head was `ab549f15` (the MLX agent's commits). Commits added:

- `152d97e1` (package, CI, inventory)
- `d8832631` (dispatch runner input, `[skip ci]`)

Only `pkgbuilds/tensorfold-vulkan/`, `.github/workflows/elementaryos-mseries-mlx.yml` and a single `tensorfold-vulkan none` line in `release/mac-inventory.txt` changed. The inventory line follows the repo rule that a new Mac recipe is listed before its first promotion.

`pkgbuilds/tensorfold-vulkan/PKGBUILD`, `1.1.9.pr1544.b3ab9ba-1`, aarch64:

**Sources:**

- GitHub archive of `b3ab9ba2…` (sha256 `66af6b1a…f465`).
- `zig-aarch64-linux-0.17.0.tar.xz` (sha256 `9e8d1166…4ff8`, the same pin as the elementary script and this repo's ghostty).
- `prepare()` checks `zig version` and the tree's `.zig-version`.

**`build()`:**

- `zig build -Dvulkan=true -Doptimize=ReleaseSafe -Dcpu=apple_m1`. `apple_m1` is the ISA every Apple Silicon Mac has, and it is what upstream's macOS release targets.
- Builds the server, the model probe, `tf-vulkan-probe`, stages 1–5 and the contract runners.
- Builds the GDN contract a second time from its own root into a separate prefix.

**`check()`:** the GPU-free host suites `vulkan-host-test`, `qwen35-model-host-test` and `contract-pointwise-host-test`.

**Installed files:**

- `/usr/lib/tensorfold-vulkan/tensorfold-native-vulkan`, plus `bin/` holding 13 probe and contract executables.
- `/usr/bin/tensorfold-vulkan`: sets `VK_DRIVER_FILES=/usr/share/vulkan/icd.d/asahi_icd.aarch64.json` and unsets `VK_ICD_FILENAMES`/`VK_ADD_DRIVER_FILES`, then execs the server. `TENSORFOLD_VK_ICD` overrides the manifest.
- `/usr/bin/tensorfold-vulkan-gates`: stages 1–5 and the six contract groups, with `--vendor 0x10005 --timeout-ms 60000`, holding `/tmp/m1-gpu.lock`.
- `/usr/share/tensorfold-vulkan/build.json`: commit, PR, Zig version and archive sha256, options, server path and sha256, and the ICD.
- Licenses: LICENSE, NOTICE, THIRD_PARTY_NOTICES.md, LICENSES/.

**Dependencies:**

- `depends`: `vulkan-aurora>=1:26.3.0_devel.20261031`, `vulkan-icd-loader`, `glibc`, `util-linux`.
- `makedepends`: `glslang`, `vulkan-headers`.

**Changes to the system:** nothing system-wide. There is no drirc entry, no vendor spoofing, and no change to other apps' driver choice.

Image: install `tensorfold-vulkan` by name on the M4 image; it is opt-in.

## 3. CI

The workflow now takes `vars.PKG_RUNNER`/`PKG_BUILD_JOBS`, as `eb93aeb3` added on `elementaryos-mseries`. It also takes a dispatch input, `runner`, that overrides PKG_RUNNER without changing the repository variable.

- Run 41214331469 (push 152d97e1, PKG_RUNNER → `m4mini-pkgs` VM `lima-kbuild`): both `tensorfold-vulkan` and `omarchy-mlx-m4` **failed before building**. The VM's docker has no buildx plugin: `bin/build`'s `docker buildx build --platform` stops with `unknown flag: --platform` (exit 125). This is a runner problem, not a package problem. The VM needs `docker-buildx`; I did not change the VM or the variable.
- Run 41214452366 (dispatch, `runner=["ubuntu-24.04-arm"]`, `packages=tensorfold-vulkan`): **success**, about 8 minutes. The steps:
  - `build()` took about 6 minutes. Zig 0.17 prints a successful glslang's file-name echo under a "failed command:" header; those lines are not failures, and every step succeeded.
  - `check()` passed the host suites.
  - Artifact: `tensorfold-vulkan-1.1.9.pr1544.b3ab9ba-1-aarch64.pkg.tar.zst`, sha256 `e43c84285eb9b2e9a7019aa1c0806e385ab78946ae3054844f543ccba7f30c7f`.
  - The server's sha256 is `d84f9d3fb0d67d1889a8252d7e0fbe878a411f5111ace4aab67aaaf204bb90d2` (in `build.json`).
  - The package installs 13 executables in `bin/`, plus the server, both wrappers and the licenses.
  - `.PKGINFO` lists the four `depends`.
  - The artifact is unsigned, like the other packages on this branch.
- CPU-target check: the runner was a Neoverse (SVE2) host. I disassembled the packaged server (942k lines, with SVE, SVE2 and SME decoding enabled) and found no SVE or SME instructions, so `-Dcpu=apple_m1` took effect. Zig shows the target as `native-native` in its step names; that label leaves out the CPU model.

## 4. Benchmark: techmore/omarchy-mlx `m4-mini-bench`

Commits `ed98cba0` and `1690652a`, on top of `3a0ee883`. `scripts/m4_mini_bench.py` sha256 is `8258e71c…7e61`.

**Engines:**

- `--engine mlx` (default, unchanged).
- `--engine tensorfold`:
  - Linux: `tensorfold-vulkan` from the package. The script refuses a package whose `build.json` commit is not b3ab9ba, or whose server no longer matches the recorded sha256.
  - macOS: the TensorFold v1.1.9 macOS arm64 release. The script downloads it into `~/.cache/m4-mini-bench`, checks the archive sha256 (`f8330102…a9d7`) and the binary sha256 (`4b4b5a5a…b8e4`), and runs `--backend mlx`, which is native Metal. v1.1.9 is the newest release that the PR head contains.
  - `--tensorfold-bin` runs any other build; the result records it as unpinned.

**Models:**

- `--model qwen3-1.7b`: unchanged; the MLX default.
- `--model qwen3.5-2b`: `mlx-community/Qwen3.5-2B-MLX-4bit` at `93760be4`. Five files are sha256-checked: weights `713fe7e5…`, tokenizer `87a7830d…`, `config.json`, `tokenizer_config.json` and `chat_template.jinja`. The small-file hashes were verified against HF's git blob IDs. This is PR 1544's only supported checkpoint. MLX runs it too, which gives the same-model triple.

**Fixed work for TensorFold:**

- Prompt: the fixed text, tokenized by the server's `/v1/tokenize` (no special tokens) and cut to 512 IDs. The IDs are sent as IDs to `/v1/completions`.
- Generation: `max_tokens` 128, `temperature` 0, `ignore_eos`, `return_token_ids`.
- Server: `--parallel 1 --no-drafts --no-thinking --context 2048`, loopback only.
- Repeats: 1 warmup, then 5 measured runs.

**Rates:**

- prompt rate: 512 / `prefill_seconds` (else / `time_to_first_token`);
- decode rate: `tokens_per_second`;
- time to first token.

All three come from the server's own `tensorfold` block.

**Refusals:**

- a wrong token count;
- runs that disagree with each other;
- cached prompt tokens;
- drafts;
- IDs that disagree with the server's `token_sha256` or with their count.

The default timeout is 2,400 s, because the unbatched Vulkan engine decodes at about 3 tok/s.

**What each result records:** the `/health` response (release, backend, device name on macOS, peak memory), the server command and log tail, `build.json`, and `vulkaninfo --summary` run with the same single ICD.

**`--compare A B [C …]`:**

- The last result is the reference.
- Each result is reported against it: prompt and generation medians, time to first token, both rates as a share of the reference, and whether its generated IDs are identical.
- It refuses results whose model or prompt-ID hashes differ.
- Schema-1 results are read as MLX qwen3-1.7b.

**Tests:** `tests/test_m4_mini_bench.py`, 13 tests passing locally (Python 3, no GPU, no mlx):

- the existing comparison tests;
- a 3-way comparison;
- a model-mismatch refusal;
- the TensorFold leg against a fake server: fixed work, planted cached and short replies, startup exit (exit 3), hang (exit 4);
- the Linux `build.json` pin and hash checks;
- download, hash check and cache of the macOS release (via a `file://` tarball).

`--self-test` was extended to cover the same.

**Owner's run on the mini (same machine, two boots):**

```bash
# Linux (Omarchy, after `tensorfold-vulkan-gates` passes)
python scripts/m4_mini_bench.py --model qwen3.5-2b --out linux-mlx-2b.json            # omarchy-mlx venv
python scripts/m4_mini_bench.py --engine tensorfold --out linux-tf-vulkan.json
# macOS
python3 scripts/m4_mini_bench.py --engine tensorfold --out macos-tf-metal.json
python3 scripts/m4_mini_bench.py --model qwen3.5-2b --out macos-mlx-2b.json            # mlx venv
python3 scripts/m4_mini_bench.py --compare linux-mlx-2b.json linux-tf-vulkan.json macos-mlx-2b.json macos-tf-metal.json
```

**Follow-up not done (outside my scope):** `pkgbuilds/omarchy-mlx-m4` still pins the bench at `0f845c99`. The packaged `omarchy-mlx-m4-bench` gets the TensorFold leg only after its `_bench_commit` is bumped to `1690652a0de099ef1fc6120c54c7f92ff39a84c0`. That needs the script sha256 `8258e71cee62b80fe516670a8b14cc770badbc35af77923d34386d2ea7a03e61` and the doc sha256 `c8bdd99b64e616a1a024e5057c4c9147d99e2ed25d9e45ae37a25837d5cb5aa5`. Until the bump, the doc says to run the script from a checkout.

## Blockers and risks

1. **No hardware run.** The whole G16G compute chain is unproven (see `mlx.md`). Run `tensorfold-vulkan-gates` before any model run.
2. **Upstream's M4 coverage.** TensorFold's Metal Qwen3.5-2B recipe says M1–M4 are untested for this model; only the M5 Max is qualified. The macOS leg is a speed number, not a correctness claim; check that the text is sensible. On Vulkan, upstream covered only M1, M1 Max and M2 Max, plus the owner's M1 Pro.
3. **The PR is open and unmerged.** If the PR head is force-pushed and the commit is garbage-collected, the GitHub archive URL in the PKGBUILD stops resolving. Mirror the tarball to a techmore release if that matters.
4. **Self-hosted runner.** `m4mini-pkgs` lacks docker buildx, so every PKG_RUNNER build fails at the image step, including omarchy-mlx-m4's.
5. **Engine comparability.** The Vulkan engine (one dispatch per op, synchronous) and the Metal engine (lane engine, simdgroup kernels) differ greatly in design. The generated IDs will differ between them and from MLX. The comparison refuses only a prompt-ID mismatch: TensorFold's tokenizer against HF's for the MLX leg. If those ever differ, that is itself a finding.
6. **Not done.** No upstream PRs, issues or comments. No settings or repository variables changed. No secrets used.
