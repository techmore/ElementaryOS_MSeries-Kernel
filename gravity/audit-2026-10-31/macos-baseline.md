# Mac mini M4 macOS (Metal) baseline — 2026-10-31

PR: https://github.com/techmore/ElementaryOS_MSeries/pull/709 (branch m4-mini-macos-baseline -> dev, commit d99d6a7)

Machine: Mac16,10, Apple M4, 10-core GPU, 16 GB, macOS 27.0 (26A5421a), AC power, no thermal warnings.
Stack: Python 3.14.3 venv (/private/tmp/claude-501/bench/venv), mlx 0.32.3, mlx-lm 0.31.3, transformers 5.16.1;
TensorFold v1.1.9 macOS release (archive + binary sha256 match the m4-mini-bench pins). All model weights matched pinned sha256.
Load: Lima VM kbuild busy throughout (390-590% CPU, load avg 15-23, 10 GiB of 16 held); untouched. Numbers are a loaded floor.

## engine-compare.py (median of 3; decode tok/s, TTFT s)
| Model | MLX in-process (Metal) | mlx_lm.server | TensorFold Metal |
|---|---|---|---|
| Granite 4.0 1B 4-bit, 32 | 58.59, 0.22 | 43.01, 0.22 | - |
| LFM3-1.7B 8-bit, 32 | 31.53, 0.24 | - | - |
| Qwen3.5-2B 4-bit, 32 | 47.67, 0.38 | 42.36, 0.42 | 39.71, 0.07 |
| Qwen3.5-2B, 32, 4 at once (total) | - | 41.63, 1.86 | 36.84, 1.82 |
| Qwen3.5-2B, 32, 8 at once (total) | - | failed (1-2 of 8 connections reset each round) | 35.41, 3.64 |
| Qwen3.5-2B, 256 | 51.26, 0.52 | 40.64, 0.55 | 36.37, 0.12 |
| Qwen3.5-4B 4-bit, 32 | 28.99, 0.39 | 25.15, 0.38 | - |
| Qwen3.5-4B, 32, 4 at once (total) | - | 29.23, 2.29 | - |

Output vs M1 Pro (Linux Vulkan) reference text: identical everywhere except Qwen3.5-2B 256 tokens (MLX + server on Metal diverge
after 1207/1301 chars; TensorFold matches) and Qwen3.5-4B in-process (diverges after 55 chars; server matches). All fluent.

## omarchy-mlx m4_mini_bench.py macOS legs (512 prompt / 128 gen, 5 runs)
MLX Qwen3-1.7B: prompt 897 tok/s, gen 57.8 · MLX Qwen3.5-2B: 853 / 54.4 · TensorFold Metal Qwen3.5-2B: 586 / 37.9 (same token IDs as MLX).

## Changes
engine-compare.py (mlx-metal, lm-metal, tensorfold-metal arms; HF snapshot paths; --reserve-gib; env knobs for Linux-on-M4),
machine.py (macOS snapshot + host_info), scoreboard.py (separate M4 section/CSV/SVG, same-as-M1 column, Linux how-to note).
M1 Pro table regenerates unchanged. Receipts: mseries/local-ai/receipts/2026-10-31-m4-mini-macos/.
Not done: Rapid-MLX and our patched server on macOS (patched server's small-rows patch targets omarchy Vulkan kernels).
