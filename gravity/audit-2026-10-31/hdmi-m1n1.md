# J773g (Mac mini M4) native HDMI: the m1n1 half

Branch `mini/hdmi-handoff` on techmore/m1n1. It is based on `elementaryos-mseries` 92f2c77, which includes the M1N1_RUNNER and arm64 fallback CI commits.
Clone: `/private/tmp/claude-501/m1n1-hdmi`. Commits `26f0f70a` (the handoff) and `6142c02f` (CI: drop macos-14).
Kernel counterpart: techmore/linux-m1pro-touchid `mini/hdmi` (see `hdmi.md`).

## What m1n1 now does on J773g

New file `src/kboot_display_j773g.c`, entry point `dt_set_j773g_hdmi_handoff(dt)`. It always returns 0.
`dt_set_display()` in kboot.c calls it from the T8132 branch, and only for an `apple,j773g` root. J713 still takes `dt_set_j713_dcp_handoff()`, unchanged.
On J773g that function only ever printed a refusal. The top-of-function `dart_lock_adt("/arm-io/dart-disp0")` is unchanged.

**Gate.** Nothing at all happens unless all three hold:
- `chip_id == T8132`;
- the root is `apple,j773g`;
- alias `dcpext0` names an `apple,t8132-dcpext` node.

Otherwise there are no register accesses and the DT is byte-identical. An older J773g DT therefore keeps the boot framebuffer only, as before.

**Checks, in order.** Any failure stops the handoff.
1. **Device tree.** These nodes must all be `disabled`:
   - dcpext0 at 0x286e00000, with 2+2 cells and no memory-region or firmware properties yet;
   - iommus `<&dart-dcpext0 23>`, with the DART at 0x286340000;
   - mailbox `apple,asc-mailbox-v4` at 0x286e08000;
   - a `piodma` child with `<&dart-dispext0 16>`;
   - alias `disp0`, an `apple,display-subsystem` node with `<&dart-dispext0 0>`, the DART at 0x286300000.

   Both DARTs must have `apple,dma-range = <1 TiB, 64 GiB>`.
2. **Firmware.** The OS firmware is 26.6.2.
3. **ADT.**
   - The dcpext0, dart-dcpext0 and dart-dispext0 reg values match.
   - Both DARTs have vm-base 1 TiB and vm-size(-23) 64 GiB, with 32 streams.
   - `iop-dcpext0-nub` has uuid `81BAF476-679D-3CC0-8C6A-E6B6FA659D5E` (pinned, as in the kernel), `pre-loaded=1` and `running=1`.
   - The nub has exactly 4 segments: `__TEXT`, `__DATA`, `__OS_LOG` and a heap.
   - TEXT, DATA, heap and `/vram` lie in DRAM, outside the OS RAM and the MCC carveouts, with remaps in the DART window and no overlaps.
   - `__OS_LOG` has remap == phys.
   - The boot framebuffer lies inside `/vram`.
4. **Power.** dcpext0's clock-gate is DISPEXT0_CPU, which is virtual and resolves to its parent DISPEXT0_FE. That power state must be on. This check reads registers only.
5. **Coprocessor.** dcpext0's ASC CPU_CONTROL RUN bit is set. Both DARTs' PROTECT values are logged. All reads are under an exception guard.
6. **DART mappings.** The tables are read only, after confirming they lie inside the ADT `pt-region-N`, which itself must be outside OS RAM. The walk covers dart-dcpext0 SID 23 and dart-dispext0 SIDs 0 and 16.
   - SID 23 must map TEXT, DATA and the heap, each exactly once, in full, at its ADT DVA. It may also map /vram.
   - SIDs 0 and 16 may map only the whole heap and /vram.
   - SID 0 must map the boot framebuffer page. This is the "iBoot lights HDMI through dispext0" check.
   - No stream may map `__OS_LOG` or anything else.

**Publish.** This is one transaction on a DT copy. The DARTs are locked just before the copy is committed.
- `/reserved-memory`, all no-map:
  - `dcpext0-text@`, `-data@`, `-heap@` (`apple,asc-mem`);
  - `framebuffer@<vram>` (compatible `framebuffer`, all of /vram);
  - `dcp-oslog@` (`apple,dcp-os-log`, with no iommu-addresses).

  Each mapping found gets one `iommu-addresses <owner 1TiB|dva size>` entry.
- `memory-region` and `-names`:
  - dcpext0: `text data heap [framebuffer]`;
  - display: `framebuffer [heap]`;
  - piodma: `[heap] [framebuffer]`.
- On dcpext0: `apple,firmware-version` and `apple,firmware-compat` = <26 6 2>, `apple,firmware-uuid`, and the marker `apple,j773g-hdmi-handoff`.
- `status = "okay"` on dcpext0, dcpext0_mbox, dcpext0_dart, dispext0_dart and the display node.
- dart-dcpext0 and then dart-dispext0 are locked (PROTECT TTBR_TCR, read back). If a lock fails, the copy is discarded.
- `/chosen/aurora,j773g-hdmi-handoff` is set to `"published"`, or to `"refused: <step>"` on a refusal. A refusal writes no register and changes nothing else in the DT.

A second call (the marker is already present) does nothing.

**Why it is not a `dcp_soc` entry in `kboot_display_handoff.c`.** That framework hard-codes `/arm-io/dcp`, `dart-dcp`, `dart-disp0` and the `dcp`/`disp0-piodma` aliases. It also needs `/vram` to be a nub segment and every non-log segment to be exactly one carveout. On J773g, dcpext0's nub has no /vram and its TEXT is not a carveout. The framework also leaves the nodes disabled behind a marker, while this kernel wants m1n1 to enable them.

Changing it would touch the code path shared by T6030, T8122, T6031 and J616s. So the new file reuses its patterns instead:
- guarded MMIO;
- page-table walks bounded by pt-region;
- run coalescing;
- all-or-nothing scratch DT;
- the T6041 dcpext text/data/heap memory contract.

## Tests

- `tests/j773g_hdmi_host.c` provides a fake ADT, PMGR, MMIO and DRAM with real T8110 two-level page tables. It uses m1n1's libfdt and a DT shaped like the kernel's `t8132-j773g.dts`. The stand-ins are `tests/t8122_display_host/` plus `tests/j773g_hdmi_host/soc.h`.
- `tests/python/test_j773g_hdmi_handoff.py` builds it with ASan/UBSan and runs **41 scenarios**. It also checks that kboot.c sends only apple,j773g to the handoff ahead of the J713 call, and that nothing happens before the gate. The scenarios are:
  - 7 publish: plain, DARTs already locked, display maps the heap, dcpext0 maps /vram, empty piodma, `__OS_LOG` inside a `/memreserve/`, repeat;
  - 4 nothing: wrong chip, J713 root, an old DT without dcpext0, a dcpext0 that is not t8132-dcpext;
  - 30 refusals covering every check above, including a DT that is full and a DART lock that does not stick.
- Locally on macOS with clang: the new tests pass (49 pytest items). The full `tests/python` suite gives 387 passed. The remaining failures and errors (8) come from missing rustc and aarch64 tools on this Mac, not from this change. The new file passes `clang --target=aarch64 -fsyntax-only` with m1n1's flags and `clang-format` 20.1.8. kboot.c's existing clang-format violations are unchanged (33 before and after).

## CI

Branch head `6142c02f`, with two commits on top of `elementaryos-mseries` 92f2c77:
- `26f0f70a`: the handoff and its tests;
- `6142c02f`: a CI-only commit that drops the macos-14 test job.

- **build.yml**: https://github.com/techmore/m1n1/actions/runs/41216283330 succeeded. It is an aarch64 gcc build with `-Wstack-usage=2048 -Os` and `CHAINLOADING=1`.
- **test.yml**: https://github.com/techmore/m1n1/actions/runs/41216281571 succeeded. All four jobs passed: ubuntu gcc, ubuntu llvm, macos-15 llvm-brew, and ubuntu-24.04-arm native. On the ubuntu gcc job: 421 passed, 12 skipped, including `test_j773g_hdmi_handoff.py`.
- The two earlier test runs (41214796967, 41216009863) had every job green except macos-14. That job was cancelled by GitHub's macOS 14 image retirement brownout (actions/runner-images#13518, image retired 2026-11-02). The same cancellation hits `elementaryos-mseries` itself (runs 41214583682, 41215937574). That is why `6142c02f` removes the macos-14 matrix entry; `elementaryos-mseries` will need the same change.

## What only hardware can confirm

- **That iBoot scans out HDMI through dispext0/dcpext0.** The power, SID 0 TTBR and "SID 0 maps the boot framebuffer" checks decide this at boot. If they refuse, `/chosen/aurora,j773g-hdmi-handoff` and the m1n1 log say which. In that case the kernel side must move to dcpext1 or dcp, and this file's constants (addresses, nub, DARTs) must move with it.
- **That the live mappings fit the strict rules.** This means TEXT/DATA/heap at their ADT DVAs, and the display and piodma mapping only the heap and /vram. Any other mapping, such as main-dcp heap regions or other carveouts, is refused with the DVA and PA logged. That log gives the next rule to add.
- **That the segments and /vram lie outside the OS RAM.** This is the T6041 rule. TEXT is at DRAM+0x2a8000, and phys_base is not in the ADT. If it refuses with "lies in the RAM handed to the OS", the rule needs revisiting.
- **That dcpext0's ASC CPU_CONTROL is at +0x44** on this ascwrap-v6.
- **That the kernel accepts the locked DARTs (`fw_mirror`), the PIODMA SID 16 and the 26.6 desktop start.** See hdmi.md.
- That the three `__OS_LOG` buffers sit where the ADT says, and whether they actually fall in the OS RAM. That depends on phys_base, which is not in the ADT. Either way they are now reserved on every J773g boot (see below).

## Follow-up: every display coprocessor's `__OS_LOG` is reserved on each J773g boot (commit `dbb0a0de`)

dcp, dcpext0 and dcpext1 all run from iBoot onward, and each writes its `__OS_LOG` buffer. In the J773g ADT these buffers are 0x10003f0c000, 0x10003f30000 and 0x10003f54000, each 0x24000 bytes. m1n1 used to reserve none of them; the HDMI handoff reserved dcpext0's, and only when it published.

- `kboot_display_handoff.c` now has a `dcp_soc_t8132` entry:
  - chip T8132, boards `{"apple,j773g"}`, `board_gate`;
  - explicit nubs dcp, dcpext0 and dcpext1;
  - `oslog_in_rsv`, as on J616s, with the same rule as the HDMI handoff: a buffer wholly inside a /memreserve/ still gets its node;
  - a new `oslog_only` flag.
- With `oslog_only`, `dt_set_display_handoff()` runs `dcp6_find_nubs()` and `dcp6_reserve_oslogs()` and then returns. This happens right after the board gate, before the firmware, device-tree and opt-in gates. There is no register access and no dry run, and no chosen property can reach the generic handoff.
- In `dt_set_display()` on J773g, `dt_set_j773g_hdmi_handoff(dt)` runs first, then `dt_set_display_handoff(dt)`, and the function returns the handoff's result.

  The order matters. The HDMI handoff refuses if dcpext0's buffer is already reserved. `dcp6_reserve_oslogs()`, by contrast, keeps an existing `dcp-oslog@<phys>` node with the same reg and no-map. Both use the name `dcp-oslog@%lx`, both round the size up to 16K, both set `no-map` (`add_resv()` does) and both mark the node `apple,dcp-os-log` (= `DCP6_OSLOG_PROP`).
- J713 never calls `dt_set_display_handoff()`, and the board gate stops any other T8132 board.
- Tests: the J773g host harness now links `kboot_display_handoff.c` and includes the dcp and dcpext1 nubs with their real ADT segments. It runs the `__OS_LOG` pass after the HDMI handoff in every scenario (46 scenarios, 70 pytest items). It checks that:
  - a publish ends with exactly three nodes and no duplicate;
  - a refused or absent handoff still reserves all three;
  - a buffer that overlaps a reservation or a carveout, or straddles a /memreserve/, is skipped and logged, and the boot continues;
  - nothing happens on another chip, board or SoC;
  - the pass touches no register.

  The shared host `soc.h` gains T8132.
- Locally the full suite gives 408 passed. The same 8 environment-only failures and errors remain (rustc, Homebrew llvm). The T8122 host suite (`run-t8122-display-handoff.sh`) needs `dtc`, which this Mac lacks, so it ran only in CI.
- CI on `dbb0a0de`:
  - **build.yml** https://github.com/techmore/m1n1/actions/runs/41217199760: success.
  - **test.yml** https://github.com/techmore/m1n1/actions/runs/41217201761: success on all four jobs (ubuntu gcc and llvm, macos-15, ubuntu-24.04-arm native). The ubuntu gcc job reported 442 passed and 12 skipped.
- Not verified:
  - `test_t8122_handoff_unchanged` (the T8122 host suite) is skipped in CI as well as locally, because neither has `dtc`.
  - I ran it here with a pure-Python dtc stand-in. Both the base and this branch stop at the same `contract-selftest` failures, with identical output. That points to the stand-in, not this change. The full T8122 scenario set has still not run against this branch.
  - The other SoCs' host suites that do run (T6041, T6031 runner, T8140) pass.
