# MLX on the Mac mini M4 GPU (J773g, T8132, G16G) — audit

Date: 2026-10-31. Sources read at: aurora-silicon/mesa `aurora-wip` 8990cdb219b2 (the commit `mesa-aurora`/`vulkan-aurora` pins on techmore/omarchy-pkgs `elementaryos-mseries`), techmore/linux-m1pro-touchid `elementaryos-mseries` fa26b0f92ef6, joshuaswarren/omarchy-mlx main 033f6061 (techmore fork main is 8 commits behind, at be521c4b), joshuaswarren/mesa-1 `honeykrisp-omarchy` 7faf04c065c5, joshuaswarren/metal2vk main 83880cba (v0.4.2).

Nothing here ran on M4 hardware. Every "works" below is from source and CI, not from a measurement.

## Summary

- Honeykrisp in aurora-wip admits G16G for Vulkan. vulkan-aurora is built from it. No Mesa change is needed for the GPU to be visible.
- The packaged MLX driver (`omarchy-mlx-vulkan`, built from joshuaswarren/mesa-1) has no G16G support. MLX would select it and find no device.
- aurora-wip reports `VK_DRIVER_ID_AURORA_BOREALIS` (35). omarchy-mlx 0.7.28 refuses that driver ID as a non-Apple GPU, even with the right ICD. Fixed in the packaging with a drirc entry, and in the source on techmore/omarchy-mlx `m4-mini-bench` 3a0ee883.
- G16G gives MLX everything it requires. It lacks only the optional cooperative matrix and fp32 atomic-add paths, as on a stock M1. MLX runs the fallback kernels, so prefill will be slower than on M1/M2 with the fork ICD.
- metal2vk is not a build or default runtime dependency. Not packaged.
- Pushed: omarchy-pkgs `elementaryos-mseries-mlx` (new package `omarchy-mlx-m4`, CI green) and omarchy-mlx `m4-mini-bench` (benchmark, tests, Borealis fix).

## 1. Honeykrisp on G16G (aurora-silicon/mesa aurora-wip)

Admission is in place since 662048cacc83 ("asahi: enable native G16G on the shared AGX3 path", 2026-10-17):

- `src/asahi/lib/agx_chip.c` `agx_chip_from_params`: generation 16 variant `'G'` → `AGX_CHIP_G16G`.
- `agx_chip_driver_supported` (`case AGX_CHIP_G16G`): HAL200 command stream, Gen4-HAL200 sampler, classic submission.
- `agx_params_driver_supported` (`case AGX_CHIP_G16G`) needs all of: `chip_id == 0x8132`, `num_dies == 1`, `num_clusters_total == 1`, `usc_generation == AGX3` and `gpu_hal_generation == HAL_200`.
- `agx_chip.h`: G16G is in `agx_chip_native_agx3`, native indirect compute, native imageblock and the uncovered-tile MSAA workaround. `agx_chip_exact_fma32` is false for G16G.
- `agx_device.c`: `agx_open_device` refuses a chip that fails `agx_params_driver_supported` (around line 919, unless `ASAHI_M5_BRINGUP`). G16G loads `libagx_g16g`.
- `src/asahi/vulkan/hk_physical_device.c`:
  - G16G gets `robustImageAccess`/`robustImageAccess2` and `maxImageDimension3D` 2048.
  - `deviceID` is `chip_id` (0x8132).
  - `conformanceVersion` is 0.0.0.0 on every chip, because Borealis has made no CTS submission.

The kernel side matches this contract. In `drivers/gpu/drm/asahi/g16/params.rs` `fill()`, chip 0x8132 reports variant G, revision 0x10, 1 die, `num_clusters` 1 (from `g16/hw.rs` t8132 CONFIG, 10 cores per cluster), `usc_generation` 3 and `HAL_200`. It sets the features `PER_COMMAND_INPUT_SYNCS | EXACT_PRIOR_BARRIERS`, plus the generic `VM_STATUS*`/`INDEPENDENT_QUEUES`/`SOFT_FAULTS` set in `gpu.rs`. The `drm_asahi_params_global` layout and the feature bit numbers are identical in Mesa's `include/drm-uapi/asahi_drm.h` and the kernel's `include/uapi/drm/asahi_drm.h`. Mesa's header has extra command structs (`*_with_prior`, `render_program*`) that this kernel header lacks. Mesa uses them only behind feature bits.

Packaging: `pkgbuilds/mesa-aurora/PKGBUILD` (pkgbase mesa-aurora, split `vulkan-aurora`) builds `-Dvulkan-drivers=asahi` from 8990cdb219b2. vulkan-aurora installs `/usr/lib/libvulkan_asahi.so` and `/usr/share/vulkan/icd.d/asahi_icd.aarch64.json`, with an absolute `library_path`.

Gating verdict: M4 Vulkan is not gated off, and no change from GravityLinux/mesa or joshuaswarren/mesa-1 is needed. GravityLinux/mesa main (`3119a8ff6bac` "asahi: add native M4 dEQP and Piglit runner profiles", Apple9 path) is a separate Gallium/Apple9 effort. Do not mix it in. joshuaswarren/mesa-1 has unrelated history (no usable merge base) and no G16G admission.

M4-specific notes:

- **Driver identity.** `driverID` is `VK_DRIVER_ID_AURORA_BOREALIS` and `driverName` is "Borealis" (`hk_physical_device.h`, 1349-1351). `deviceName` looks like "Apple M4 (G16G 10)". vendorID is Mesa's 0x10005. The drirc option `hk_report_honeykrisp_driver_id` (fdddefe6d89, `00-hk-defaults.conf`, `hk_drirc_gen.py`) switches the ID back per engine. Aurora uses it for DXVK and vkd3d.
- **FMA.** `KHR_shader_fma` is off on G16G (exact FMA32 is unqualified; probes fail near the minimum normal).
- **Kernel firmware.** The G16 driver admits only the exact GFX firmware TEXT image of macOS build 25G83 (`g16/hw.rs` `firmware:`). A different macOS stub/firmware on the mini means no GPU at all.
- **Recovery and power.** `g16_recovery=1` and `g16_stream_gate=1` are the defaults (`asahi_core.rs`). The GFX power domain is held for the whole session (`g16/glue.c` `asahi_g16_hold_power`, J773g admitted in 5d25f5078a63). PMP cooling can throttle, so record temperatures with any number.
- **Conformance.** No CTS claim on G16G.

## 2. What omarchy-mlx's Vulkan backend needs, and what G16G gives

Requirements come from `overlay/mlx/backend/omarchy/device.cpp`: `classify_physical_device`, `collect_capabilities`, `Device::Device`, and the `#extension` lines of the 128 GLSL shaders.

Hard requirements:

| Requirement | G16G on aurora-wip |
|---|---|
| Vulkan 1.3 | yes (1.4, `hk_get_vk_version`) |
| Apple GPU identity: vendor 0x106b, or "honeykrisp" in the device name, or driver ID 26 | **no**: Borealis ID 35. Fixed with drirc or 3a0ee883 |
| `timelineSemaphore` | yes |
| One compute queue | yes |

Optional features, used when present:

| Feature | G16G on aurora-wip |
|---|---|
| `shaderFloat16`, `shaderInt16`, `shaderInt64` | yes (`hk_physical_device.c` 384-438) |
| `storageBuffer16BitAccess` | yes |
| `subgroupSizeControl` | yes |
| `EXT_global_priority` | yes |
| `KHR_cooperative_matrix` (8x8x8 f32/f16 with f32 accumulator, bf16) | **no**: gated to M5 only, extension at 2013 and compiler lowering at `hk_shader.c:3013` |
| `EXT_shader_atomic_float` (fp32 buffer atomic add) | **no** (only G17P and M5). MLX uses the FCAS compare-exchange kernels (`primitives.cpp` around 10636 and 11165) |

Shader features, from the GLSL:

| Shader extension | Count | Driver side on G16G |
|---|---|---|
| `GL_EXT_shader_16bit_storage` | 159 | yes |
| int16 / fp16 / int64 / int8 arithmetic types | 92 / 71 / 11 / 6 | yes. The int8 shaders read packed words, so `shaderInt8` is not enabled at device creation |
| `KHR_shader_subgroup` basic, arithmetic, shuffle, shuffle_relative | 30, 20, 3, 4 | subgroup size 32 with all operations (1321-1332) |
| `KHR_memory_scope_semantics` | 11 | `vulkanMemoryModel` yes |
| `KHR_cooperative_matrix` | 11 | only on the coopmat paths, which are gated off here |
| `EXT_bfloat16` | 2 | only on the coopmat paths, which are gated off here |

Limits: `maxComputeSharedMemorySize` 32 KiB (`hk_private.h:52`, same as M1), `maxStorageBufferRange` INT32_MAX, `maxMemoryAllocationSize` 128 GiB, 1024 invocations per workgroup.

Verdict: functionally sufficient. Speed caveats:

- No cooperative matrix, so the coopmat prefill, attention and gated-delta paths (`primitives.cpp` around 683-849) are off. On M1/M2 the joshuaswarren/mesa-1 ICD exposes them.
- Enabling coopmat on G16G is not a flag flip. `agx_nir_lower_cmat` is wired only for M5 in `hk_shader.c`. It would need compiler work and CTS. Not safe as a "minimal change".
- MLX's per-chip tuning tables have no G16G entry. Split-K defaults exist only for G13G/G13C/G14C. Expect untuned defaults.

## 2b. metal2vk (joshuaswarren/metal2vk)

omarchy-mlx uses it only for `mx.fast.metal_kernel` custom kernels, the ones oMLX, mlx-lm and mlx-vlm write in MSL (`overlay/mlx/backend/omarchy/m2v_route.{h,cpp}`, `docs/custom-kernel-metal2vk.md`). MLX's own primitives use the backend's hand-written GLSL. Metal kernels are not translated wholesale.

- The route is opt-in. `MLX_OMARCHY_METAL_KERNEL_BACKEND` defaults to `translator` (the built-in MSL-to-GLSL translator). `auto` and `m2v` select metal2vk per the gate table.
- Modules come first from the ahead-of-time cache shipped in the wheel. `overlay/mlx/backend/omarchy/m2v_aot` holds 33 `.spv` with reflection JSON. They are used only through the opt-in modes.
- Only on a cache miss does the backend exec `m2v-compile` (`tools/m2v-compile` in metal2vk). That needs clang/opt 23, a patched clspv (pinned f2b01dd6 + 20 patches, LLVM built in) and spirv-tools.
- So metal2vk is neither a build dependency nor a default runtime dependency. I did not package it. Building patched clspv in CI is a multi-hour LLVM build. Package it later only if the gate turns on `auto`/`m2v` for kernels outside the AOT cache.

Output requirements: SPIR-V 1.5 for Vulkan 1.3 (`compile.sh` passes `clspv --spv-version=1.5`, checked by `spirv-val --target-env vulkan1.3`). Across the shipped AOT modules the capabilities are Shader, Int16 (32), GroupNonUniform (17), GroupNonUniformArithmetic (25), GroupNonUniformShuffle (9), VariablePointers and VariablePointersStorageBuffer (12), Int8 (9) and Int64 (1). The extension is `SPV_KHR_non_semantic_info`, and no module uses cooperative matrix.

Honeykrisp on G16G exposes all of these: `KHR_variable_pointers` with both features, `shaderInt8`, `KHR_shader_non_semantic_info`, and the subgroup operations. The opt-in 64-bit mode needs `bufferDeviceAddress`, which is also exposed. metal2vk modules should therefore run on G16G.

Caveats:

- omarchy-mlx does not enable `variablePointers`, `shaderInt8` or `VK_KHR_shader_non_semantic_info` at `vkCreateDevice`. Mesa tolerates this; it is a spec gap to fix in omarchy-mlx.
- Do not use `m2v-compile --native-builtins fma` on G16G. `KHR_shader_fma` is off because G16G's FFMA is not exact near denormals.
- The backend refuses coopmat modules (`m2v_route.cpp` `validate_dispatch`), so the `m2v_mma_f32` path is unavailable here anyway.

## 3. Packages pushed: techmore/omarchy-pkgs `elementaryos-mseries-mlx`

Based on `elementaryos-mseries` 34c27c6e. Commits 857b07fd and ab549f15. The three platform PKGBUILDs (linux-aurora, m1n1-aurora, mesa-aurora) are untouched.

New `pkgbuilds/omarchy-mlx-m4/` (pkgbase `omarchy-mlx-m4` 0.1.0-1, aarch64) has two split packages.

`omarchy-mlx-vulkan-aurora`:

- `depends=('vulkan-aurora>=1:26.3.0_devel.20261031')`.
- `provides=('omarchy-mlx-vulkan=0.7.28-5')`, the exact version `omarchy-mlx` 0.7.28-5 depends on. Bump `_omarchy_mlx_ver` with omarchy-mlx.
- `conflicts=('omarchy-mlx-vulkan' 'mesa-honeykrisp-omarchy')`.
- Installs `/usr/lib/omarchy-mlx/vulkan/honeykrisp_icd.aarch64.json` as a symlink to the vulkan-aurora manifest, so MLX and the desktop share one driver.
- Installs `/usr/share/drirc.d/60-omarchy-mlx-honeykrisp-id.conf`, which sets `hk_report_honeykrisp_driver_id` for engine `^mlx-omarchy$` only.
- Ships no `mesa-git-sha`. The tarball-built driver reports no git SHA, so omarchy-mlx records the identity without enforcing one.

`omarchy-mlx-m4-bench`:

- Installs `/usr/bin/omarchy-mlx-m4-bench`, which runs the benchmark with `/usr/lib/omarchy-mlx/venv/bin/python`.
- Installs `/usr/lib/omarchy-mlx-m4/m4_mini_bench.py` from techmore/omarchy-mlx 0f845c99, fetched by raw URL with its sha256.
- Installs `/usr/share/omarchy-mlx-m4/stack.json`, which maps the pinned versions to their commits:
  - linux-aurora 7.3.0.aurora90-1 → fa26b0f92ef6
  - m1n1-aurora 1.6.1.aurora90-1 → 9347c1818082
  - vulkan-aurora 1:26.3.0_devel.20261031.231461.8990cdb219b-1 → 8990cdb219b2
  - omarchy-mlx 0.7.28-5 → 5c15fbaead0e, the v0.7.28 tag commit
- `check()` runs the bench self-test and validates the manifest and the drirc XML.

Other changes on the branch:

- New fork-only workflow `.github/workflows/elementaryos-mseries-mlx.yml`, a copy of elementaryos-mseries.yml for this branch and `pkgbuilds/omarchy-mlx-m4/**`.
- `release/mac-inventory.txt` gains `omarchy-mlx-m4 none`.

Image: install `omarchy-mlx omarchy-mlx-vulkan-aurora omarchy-mlx-m4-bench vulkan-aurora` by name on the M4 image. Do not put `omarchy-mlx-vulkan-aurora` in `omarchy-platform-apple-silicon`, because it conflicts with `omarchy-mlx-vulkan`, which other Macs keep. Optional tools for the renderer lines: `vulkan-tools`, `mesa-utils`.

CI:

- Run 41209727448 (857b07fd): success. `self-test ok`, and both `.pkg.tar.zst` files were built and uploaded as artifacts.
- Run 41209983504 (ab549f15, drirc added): success (`self-test ok`; `omarchy-mlx-vulkan-aurora` 3573 bytes with the drirc file, sha256 5da28efd…; `omarchy-mlx-m4-bench` sha256 f8e28f03…).

The artifacts are unsigned, like elementaryos-mseries'.

## 4. Benchmark pushed: techmore/omarchy-mlx `m4-mini-bench`

Based on joshuaswarren/omarchy-mlx main 033f6061.

Commit 0f845c99 adds:

- `scripts/m4_mini_bench.py`
- `docs/m4-mini-bench.md`
- `tests/test_m4_mini_bench.py` (unittest: 4 tests pass locally; the parent/child flow was also exercised with stub mlx modules)

The fixed work:

| Item | Value |
|---|---|
| Model | `mlx-community/Qwen3-1.7B-4bit` @ 3b1b1768f8f8 |
| Hash-checked files | `model.safetensors` 0e86d967…, `tokenizer.json` aeb13307… |
| Prompt | 512 token IDs cut from a fixed text; the ID SHA-256 is recorded |
| Generation | 128 greedy tokens, EOS masked |
| Repeats | 1 warmup, 5 measured |
| Reported | mlx-lm `prompt_tps` and `generation_tps` (median, min, max, spread), time to first token, peak memory |

Each run records:

- kernel and `/proc/version`;
- device tree;
- the pacman versions of the Aurora and MLX packages, and their commits from the stack manifest;
- the asahi module parameters;
- `mx.device_info()` (device name, driver, driverInfo, ICD path);
- the `vulkaninfo --summary` and `eglinfo -B`/`glxinfo -B` renderer lines, when those tools are installed;
- on macOS: `sw_vers`, chip, GPU cores and power mode;
- mlx, mlx-lm and transformers versions;
- the script's commit and hash;
- load average, governor and temperatures.

How it runs:

- The measurement runs in a child process with a 900 s timeout (exit 4) and holds `/tmp/m1-gpu.lock`.
- A run is refused if the token counts are wrong, the greedy runs disagree, or the default device is not the GPU.
- `--compare linux.json macos.json` refuses results with mismatched model or prompt hashes. It prints Linux as a share of macOS and whether the token IDs are identical.
- macOS setup: `pip install mlx==0.32.3 mlx-lm==0.31.3 transformers==5.16.1 huggingface_hub`. This matches `mlx.lock` and the packaged venv's mlx-lm.

Commit 3a0ee883 makes `classify_physical_device` accept `kAuroraBorealisDriverId` (35), with a doctest case for "Apple M4 (G16G 10)". A wheel built from it no longer needs the drirc entry. The backend syntax gate was dispatched on the fork (run 41209935454, head 3a0ee883): success, both the syntax and translate-tests jobs. The doctest suite `test_runtime` is not run by that workflow, so the new discovery test case has not been run.

## Blockers and risks

1. No hardware run yet. The whole chain is unproven on J773g:
   - G16 kernel compute submission;
   - Borealis compute;
   - MLX correctness on G16G.

   Run `omarchy-mlx-m4-bench` plus omarchy-mlx's correctness gates (`scripts/m3m4_kit.sh` and the collector) before quoting any number.
2. **Firmware.** The G16 kernel admits only GFX firmware 25G83. Confirm that the macOS stub/firmware the installer uses matches, or the GPU never comes up.
3. **Fault handling.** A GPU fault on G16 can stop the GPU until reboot. The bench has a timeout, but a fault still means a reboot.
4. **Prefill speed.** No cooperative matrix on G16G (M5-only in Aurora), so prefill uses the scalar and subgroup kernels. Expect a larger gap to macOS than on M1/M2 with the fork ICD.
5. **Version coupling.** `omarchy-mlx-vulkan-aurora` provides exactly `omarchy-mlx-vulkan=0.7.28-5`. Bump it whenever omarchy-mlx's pkgver or pkgrel changes. Also update `stack.json` when the platform pins move; the bench reports `commit: null` on a mismatch rather than a wrong commit.
6. **Packaged omarchy-mlx is old.** It is 0.7.28, while upstream has v0.7.35 and the Borealis fix is only on the techmore branch. A newer wheel (with 3a0ee883) would make the drirc workaround unnecessary.
7. **Validation gaps.** omarchy-mlx does not enable `shaderInt8`/`variablePointers`/`non_semantic_info` for metal2vk modules. This is harmless on Mesa but invalid per the spec.
8. **Not done.** No upstream PRs or comments were made. The techmore/omarchy-mlx fork main was not synced.
